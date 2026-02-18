"""匯出辨識結果為 .txt 或 .srt 格式"""

from pathlib import Path


def _format_srt_timestamp(seconds: float) -> str:
    """將秒數轉換為 SRT 時間格式 HH:MM:SS,mmm"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def export_to_txt(text: str, output_path: str) -> Path:
    """將文字匯出為 .txt 檔"""
    path = Path(output_path)
    if path.suffix.lower() != ".txt":
        path = path.with_suffix(".txt")
    path.write_text(text, encoding="utf-8")
    return path


def export_to_srt(segments: list[dict], output_path: str) -> Path:
    """
    將分段結果匯出為 .srt 字幕檔

    segments: [{"start": float, "end": float, "text": str}, ...]
    """
    path = Path(output_path)
    if path.suffix.lower() != ".srt":
        path = path.with_suffix(".srt")

    lines = []
    for i, seg in enumerate(segments, 1):
        start = _format_srt_timestamp(seg["start"])
        end = _format_srt_timestamp(seg["end"])
        text = seg.get("text", "").strip()
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")

    path.write_text("\n".join(lines), encoding="utf-8")
    return path
