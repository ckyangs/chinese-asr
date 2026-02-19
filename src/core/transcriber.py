# -*- coding: utf-8 -*-
"""Faster-Whisper 語音辨識引擎封裝"""

from pathlib import Path
from typing import Optional

# 延遲載入，依 model_size 快取
_transcriber_cache: dict[str, object] = {}


def _get_transcriber(model_size: str = "base"):
    """取得 Transcriber（依 model_size 快取）"""
    if model_size not in _transcriber_cache:
        from faster_whisper import WhisperModel
        _transcriber_cache[model_size] = WhisperModel(model_size, device="cpu", compute_type="int8")
    return _transcriber_cache[model_size]


def transcribe_audio(
    audio_path: str,
    language: Optional[str] = "zh",
    model_size: str = "base",
    beam_size: int = 8,
    initial_prompt: Optional[str] = None,
) -> tuple[str, list[dict]]:
    """
    辨識音訊檔案，回傳完整文字與分段結果（含時間戳）

    Returns:
        full_text: 辨識出的完整文字
        segments: 分段列表，每段含 start, end, text
    """
    path = Path(audio_path)
    if not path.exists():
        raise FileNotFoundError(f"檔案不存在: {audio_path}")

    model = _get_transcriber(model_size)
    transcribe_kw: dict = {
        "language": language,
        "beam_size": beam_size,
        "vad_filter": True,
        "condition_on_previous_text": True,
        "no_speech_threshold": 0.4,
        "log_prob_threshold": -0.8,
    }
    if initial_prompt and initial_prompt.strip():
        transcribe_kw["initial_prompt"] = initial_prompt.strip()

    segments_iter, info = model.transcribe(str(path), **transcribe_kw)

    segments_list = []
    full_parts = []
    for seg in segments_iter:
        segments_list.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip(),
        })
        full_parts.append(seg.text.strip())

    full_text = "".join(full_parts).strip()
    return full_text, segments_list
