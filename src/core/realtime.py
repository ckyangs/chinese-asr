# -*- coding: utf-8 -*-
"""即時語音辨識：音訊緩衝與背景辨識"""

import queue
import threading
import tempfile
import wave
from pathlib import Path

import numpy as np

from .transcriber import transcribe_audio


TARGET_SAMPLE_RATE = 16000  # Whisper 最佳採樣率，與麥克風錄音一致


def _resample_to_16k(samples: np.ndarray, orig_sr: int) -> np.ndarray:
    """重採樣至 16kHz（與麥克風一致，有助改善辨識與修復亂碼）"""
    if orig_sr == TARGET_SAMPLE_RATE:
        s = samples.astype(np.float64) if samples.dtype != np.float64 else samples.copy()
        if samples.dtype in (np.int16, np.int32):
            s = s / 32768.0
        return s
    if samples.dtype in (np.int16, np.int32):
        samples = samples.astype(np.float64) / 32768.0
    else:
        samples = samples.astype(np.float64)
    new_len = int(len(samples) * TARGET_SAMPLE_RATE / orig_sr)
    if new_len < 1:
        return samples
    old_indices = np.arange(len(samples))
    new_indices = np.linspace(0, len(samples) - 1, new_len)
    return np.interp(new_indices, old_indices, samples)


def _samples_to_wav(samples: np.ndarray, sample_rate: int, path: Path) -> None:
    """將音訊樣本寫入 WAV 檔案（支援 float32、float64、int16），自動重採樣至 16kHz"""
    if samples.ndim > 1:
        samples = samples.mean(axis=0)
    samples = _resample_to_16k(samples, sample_rate)
    sample_rate = TARGET_SAMPLE_RATE
    if samples.dtype in (np.float32, np.float64):
        samples = np.clip(samples.astype(np.float64), -1.0, 1.0)
        samples = (samples * 32767).astype(np.int16)
    elif samples.dtype not in (np.int16,):
        if samples.dtype == np.uint8:
            samples = (samples.astype(np.int16) - 128) * 256
        else:
            samples = samples.astype(np.int16)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(samples.tobytes())


class RealtimeTranscriber:
    """即時辨識：背景執行緒處理音訊塊並辨識"""

    def __init__(
        self,
        result_queue: "queue.Queue[str]",
        model_size: str = "base",
        language: str = "zh",
        chunk_duration_sec: float = 2.5,
        sample_rate: int = 48000,
    ):
        self.result_queue = result_queue
        self.model_size = model_size
        self.language = language
        self.chunk_duration_sec = chunk_duration_sec
        self.sample_rate = sample_rate
        self.buffer: list[np.ndarray] = []
        self.buffer_lock = threading.Lock()
        self.samples_per_chunk = int(sample_rate * chunk_duration_sec)
        self._stop = threading.Event()

    def add_frame(self, samples: np.ndarray, sample_rate: int | None = None) -> None:
        """加入一幀音訊（來自 av.AudioFrame），可指定 sample_rate（首次有效）"""
        if sample_rate is not None:
            self.sample_rate = sample_rate
            self.samples_per_chunk = int(sample_rate * self.chunk_duration_sec)
        with self.buffer_lock:
            self.buffer.append(samples.copy())

    def _extract_chunk(self) -> np.ndarray | None:
        """取出足夠的樣本作為一個辨識塊，剩餘樣本保留於緩衝"""
        with self.buffer_lock:
            if not self.buffer:
                return None
            concat = np.concatenate(self.buffer)
            if len(concat) < self.samples_per_chunk:
                return None
            chunk = concat[: self.samples_per_chunk]
            remainder = concat[self.samples_per_chunk :]
            self.buffer = [remainder] if len(remainder) > 0 else []
            return chunk

    def _transcribe_chunk(self, samples: np.ndarray) -> str:
        """辨識單一音訊塊"""
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            path = Path(f.name)
        try:
            _samples_to_wav(samples, self.sample_rate, path)
            text, _ = transcribe_audio(
                str(path),
                language=self.language,
                model_size=self.model_size,
            )
            return text.strip()
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
