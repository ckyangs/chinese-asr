# -*- coding: utf-8 -*-
"""即時語音辨識：音訊緩衝與背景辨識"""

import queue
import threading
import tempfile
from pathlib import Path
from typing import List, Tuple

from pydub import AudioSegment
import zhconv

from .transcriber import transcribe_audio


# 音量低於此 dBFS 視為靜音，不送去辨識（避免幻覺亂碼）
SILENCE_DBFS_THRESHOLD = -42


def _frames_to_segment(frames_data: List[Tuple[bytes, int, int, int]]) -> AudioSegment:
    """將 WebRTC 音訊幀轉為 16kHz 單聲道 AudioSegment"""
    if not frames_data:
        return AudioSegment.empty()
    sound = AudioSegment.empty()
    for raw_bytes, sample_width, frame_rate, channels in frames_data:
        seg = AudioSegment(
            data=raw_bytes,
            sample_width=sample_width,
            frame_rate=frame_rate,
            channels=channels,
        )
        sound += seg
    return sound.set_channels(1).set_frame_rate(16000)


def _frames_to_wav(
    frames_data: List[Tuple[bytes, int, int, int]],
    path: Path,
) -> None:
    """將 WebRTC 音訊幀轉為 16kHz 單聲道 WAV 檔"""
    sound = _frames_to_segment(frames_data)
    if len(sound) > 0:
        sound.export(str(path), format="wav")


class RealtimeTranscriber:
    """即時辨識：使用 pydub 正確轉換 WebRTC 音訊格式"""

    def __init__(
        self,
        result_queue: "queue.Queue[str]",
        model_size: str = "base",
        language: str = "zh",
        chunk_duration_sec: float = 4.0,
        sample_rate: int = 48000,
    ):
        self.result_queue = result_queue
        self.model_size = model_size
        self.language = language
        self.chunk_duration_sec = chunk_duration_sec
        self.sample_rate = sample_rate
        self.buffer: List[Tuple[bytes, int, int, int]] = []
        self.buffer_lock = threading.Lock()
        self._bytes_per_chunk = int(sample_rate * chunk_duration_sec * 2)
        self._stop = threading.Event()
        self._last_text = ""  # 前文上下文，供下一段辨識使用

    def add_frame(self, raw_bytes: bytes, sample_width: int, frame_rate: int, channels: int) -> None:
        """加入一幀音訊（使用 frame.format 確保正確格式）"""
        if sample_width <= 0:
            sample_width = 2
        if frame_rate <= 0:
            frame_rate = 48000
        if channels <= 0:
            channels = 1
        with self.buffer_lock:
            self.buffer.append((raw_bytes, sample_width, frame_rate, channels))

    def _extract_chunk(self) -> List[Tuple[bytes, int, int, int]] | None:
        """取出足夠音訊作為一個辨識塊"""
        with self.buffer_lock:
            if not self.buffer:
                return None
            total_bytes = sum(len(b[0]) for b in self.buffer)
            if total_bytes < self._bytes_per_chunk:
                return None
            accumulated = 0
            chunk_frames = []
            for item in self.buffer:
                chunk_frames.append(item)
                accumulated += len(item[0])
                if accumulated >= self._bytes_per_chunk:
                    break
            self.buffer = self.buffer[len(chunk_frames) :]
            return chunk_frames

    def _transcribe_chunk(self, frames_data: List[Tuple[bytes, int, int, int]]) -> str:
        """辨識音訊塊（pydub 轉 16kHz 單聲道，靜音時跳過以減少亂碼）"""
        sound = _frames_to_segment(frames_data)
        if len(sound) == 0:
            return ""
        # 靜音檢測：音量過低時跳過辨識，避免 Whisper 在靜音時產生幻覺亂碼
        try:
            dbfs = sound.dBFS
            if dbfs < SILENCE_DBFS_THRESHOLD or dbfs == float("-inf"):
                return ""
        except Exception:
            pass
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = Path(f.name)
        try:
            sound.export(str(path), format="wav")
            # 前文上下文可提升連貫辨識（取最後約 40 字）
            prompt = "以下是繁體中文："
            if self._last_text:
                prompt += self._last_text[-40:]
            text, _ = transcribe_audio(
                str(path),
                language=self.language,
                model_size=self.model_size,
                beam_size=8,
                vad_filter=False,
                no_speech_threshold=0.6,
                log_prob_threshold=-0.5,
                repetition_penalty=1.1,
                initial_prompt=prompt,
            )
            text = text.strip()
            if text:
                text = zhconv.convert(text, "zh-hant")
                self._last_text = (self._last_text + text)[-200:]  # 累積前文，保留最後 200 字
            return text
        finally:
            path.unlink(missing_ok=True)

    def run_worker(self) -> None:
        """背景工作：定期取出緩衝並辨識"""
        while not self._stop.is_set():
            chunk = self._extract_chunk()
            if chunk is not None:
                try:
                    text = self._transcribe_chunk(chunk)
                    if text:
                        self.result_queue.put(text)
                except Exception as e:
                    self.result_queue.put(f"[錯誤] {e!s}")
            else:
                self._stop.wait(timeout=0.2)

    def stop(self) -> None:
        self._stop.set()
