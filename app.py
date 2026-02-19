# -*- coding: utf-8 -*-
"""
中文語音辨識工具 - Streamlit 版本
支援 .mp3, .wav, .m4a 上傳，或麥克風即時錄音，使用 Faster-Whisper 辨識
"""

import html
import queue
import threading
import time
from pathlib import Path

import streamlit as st
from streamlit_webrtc import WebRtcMode, webrtc_streamer

from src.core.realtime import RealtimeTranscriber
from src.core.transcriber import transcribe_audio


def _escape_html(text: str) -> str:
    """跳脫 HTML 特殊字元，確保正確顯示"""
    return html.escape(text)


def _format_ts(seconds: float) -> str:
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _build_srt_content(segments: list) -> str:
    """產生 SRT 檔案內容"""
    lines = []
    for i, seg in enumerate(segments, 1):
        start = _format_ts(seg["start"])
        end = _format_ts(seg["end"])
        lines.append(f"{i}\n{start} --> {end}\n{seg.get('text', '').strip()}\n")
    return "\n".join(lines)


# 頁面設定
st.set_page_config(
    page_title="中文語音辨識工具",
    page_icon="🎤",
    layout="centered",
)

# 標題
st.title("🎤 中文語音辨識工具")
st.caption("上傳音訊檔、麥克風錄音，或即時邊講邊辨識，使用 Faster-Whisper 引擎")

# 側邊欄：辨識設定（全域共用）
with st.sidebar:
    st.subheader("辨識設定")
    model_size = st.selectbox(
        "模型大小",
        ["tiny", "base", "small", "medium", "large-v2", "XA9/faster-whisper-large-v2-zh-TW"],
        index=2,
        help="zh-TW 為繁體中文專用模型，輸出較正確",
        key="model_size",
    )
    language = st.text_input("語言代碼", value="zh", help="zh=中文, en=英文", key="language")
    initial_prompt = st.text_area(
        "提示詞（選填）",
        value="",
        height=60,
        help="輸入可能會出現的專有名詞、術語，可提升辨識準確度",
        key="initial_prompt",
    )

# 輸入方式選項
tab_upload, tab_mic, tab_realtime = st.tabs(["📁 上傳檔案", "🎙️ 麥克風錄音", "⚡ 即時辨識"])

with tab_upload:
    uploaded_file = st.file_uploader(
        "上傳音訊檔案",
        type=["mp3", "wav", "m4a"],
        help="請選擇 .mp3、.wav 或 .m4a 檔案",
    )

with tab_mic:
    st.caption("點擊麥克風按鈕開始錄音，錄完後即可辨識")
    audio_input = st.audio_input("使用麥克風錄音", sample_rate=16000, key="mic_recording")

# 決定音訊來源（優先使用上傳檔案）
audio_source = None
source_name = None
if uploaded_file is not None:
    audio_source = uploaded_file.getvalue()
    source_name = uploaded_file.name
elif audio_input is not None:
    audio_source = audio_input.read()
    source_name = f"錄音_{int(time.time())}.wav"

if audio_source is not None and source_name:
    # 儲存音訊到暫存檔（上傳或麥克風錄音）
    temp_dir = Path("./.streamlit_temp")
    temp_dir.mkdir(exist_ok=True)
    temp_path = temp_dir / source_name
    temp_path.write_bytes(audio_source)

    st.success(f"已準備：{source_name}")

    # 辨識按鈕
    if st.button("▶ 開始辨識", type="primary", key="btn_transcribe"):
        result_holder = [None]
        error_holder = [None]

        with st.spinner("辨識中，請稍候..."):
            try:
                text, segments = transcribe_audio(
                    str(temp_path),
                    language=language,
                    model_size=model_size,
                    initial_prompt=initial_prompt or None,
                )
                result_holder[0] = (text, segments)
            except Exception as e:
                error_holder[0] = str(e) or repr(e)

        # 清除暫存檔
        try:
            temp_path.unlink(missing_ok=True)
        except Exception:
            pass

        if error_holder[0]:
            st.error(f"辨識失敗：{error_holder[0]}")
        elif result_holder[0] is None:
            st.error("辨識失敗，請重試")
        else:
            text, segments = result_holder[0]  # 已確認非 None
            st.session_state.last_result = {"text": text, "segments": segments, "name": source_name}
            st.success("辨識完成！")

    # 顯示辨識結果（存於 session，避免 rerun 後消失）
    if "last_result" in st.session_state:
        r = st.session_state.last_result
        st.subheader("辨識結果")
        st.text_area("辨識文字", value=r["text"], height=200, disabled=True, key="result_text")
        st.subheader("匯出")
        default_name = Path(r["name"]).stem
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                "📄 下載 TXT",
                data=r["text"],
                file_name=f"{default_name}.txt",
                mime="text/plain",
                key="dl_txt",
            )
        with dl_col2:
            srt_content = _build_srt_content(r["segments"])
            st.download_button(
                "📄 下載 SRT",
                data=srt_content,
                file_name=f"{default_name}.srt",
                mime="application/x-subrip",
                key="dl_srt",
            )

else:
    st.info("請上傳音訊檔案或使用麥克風錄音以開始辨識")

# ========== 即時辨識分頁 ==========
with tab_realtime:
    st.subheader("⚡ 即時辨識")
    st.caption("開啟麥克風後，邊講邊輸出辨識文字（每 5 秒輸出一次，音訊重採樣至 16kHz）")
    st.info(
        "即時辨識需瀏覽器麥克風權限。建議使用 Chrome 或 Edge。"
        "若連線失敗，請改用「上傳檔案」或「麥克風錄音」分頁。"
    )

    # 初始化即時辨識資源
    if "realtime_init" not in st.session_state:
        st.session_state.realtime_queue = queue.Queue()
        st.session_state.realtime_transcript = []
        st.session_state.realtime_init = True

    rt_queue = st.session_state.realtime_queue
    rt_transcript = st.session_state.realtime_transcript

    # 即時辨識使用較小模型以提升速度（tiny 最快、亂碼較少）
    rt_model = st.selectbox("即時辨識模型", ["small", "base", "tiny"], index=0, key="rt_model", help="small 辨識最準，tiny 最快")

    # 建立即時辨識器（模型變更時重建）
    need_new_transcriber = (
        "realtime_transcriber" not in st.session_state
        or st.session_state.realtime_transcriber.model_size != rt_model
    )
    if need_new_transcriber:
        if "realtime_transcriber" in st.session_state:
            del st.session_state["realtime_transcriber"]
        st.session_state.realtime_transcriber = RealtimeTranscriber(
            result_queue=rt_queue,
            model_size=rt_model,
            language=language,
            chunk_duration_sec=5.0,
            sample_rate=48000,
        )
        worker = threading.Thread(
            target=st.session_state.realtime_transcriber.run_worker,
            daemon=True,
        )
        worker.start()

    rt_transcriber = st.session_state.realtime_transcriber

    # SENDONLY 模式使用 audio_receiver 接收音訊
    # frontend_rtc_configuration 提供 STUN 伺服器，改善部署環境（Streamlit Cloud / HF Spaces）的 WebRTC 連線
    rtc_config = {
        "iceServers": [
            {"urls": "stun:stun.l.google.com:19302"},
            {"urls": "stun:stun1.l.google.com:19302"},
        ]
    }
    webrtc_ctx = webrtc_streamer(
        key="realtime_asr",
        mode=WebRtcMode.SENDONLY,
        media_stream_constraints={"video": False, "audio": True},
        audio_receiver_size=256,
        rtc_configuration=rtc_config,
    )

    # 有 audio_receiver 時：收取音訊 → 送入辨識 → 顯示結果
    if webrtc_ctx.audio_receiver:
        transcript_placeholder = st.empty()
        try:
            while True:
                try:
                    audio_frames = webrtc_ctx.audio_receiver.get_frames(timeout=1)
                except queue.Empty:
                    break
                for frame in audio_frames:
                    arr = frame.to_ndarray()
                    # PyAV 回傳 (channels, samples)，tobytes() 為 planar；
                    # pydub 需 interleaved (L,R,L,R...)，故需 transpose
                    if arr.ndim == 2 and arr.shape[0] > 1:
                        arr = arr.T.flatten()  # (ch,s) -> (s,ch) flatten -> interleaved
                    raw = arr.tobytes()
                    sw = getattr(frame.format, "bytes", 2) or 2
                    sr = getattr(frame, "sample_rate", None) or 48000
                    ch = len(getattr(frame.layout, "channels", [0])) or 1
                    rt_transcriber.add_frame(raw, sw, sr, ch)
                # 收取辨識結果
                while True:
                    try:
                        new_text = rt_queue.get_nowait()
                        rt_transcript.append(new_text)
                    except queue.Empty:
                        break
                full_text = "".join(rt_transcript)
                with transcript_placeholder.container():
                    st.markdown("**即時辨識結果**")
                    if full_text:
                        st.markdown(f"<div style='white-space: pre-wrap; font-size: 1rem; line-height: 1.6;'>{_escape_html(full_text)}</div>", unsafe_allow_html=True)
                    else:
                        st.info("（辨識中...）")
        except Exception as e:
            st.error(f"即時辨識錯誤：{e}")

        if rt_transcript:
            st.markdown("---")
            full_text = "".join(rt_transcript)
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📄 下載 TXT", data=full_text, file_name="即時辨識.txt", mime="text/plain", key="rt_dl")
            with col2:
                if st.button("清除", key="rt_clear"):
                    rt_transcript.clear()
                    st.rerun()
    else:
        # 尚未開始串流時顯示空結果區
        st.markdown("**即時辨識結果**")
        full_text = "".join(rt_transcript)
        st.text_area("辨識文字", value=full_text or "（點擊 START 開始）", height=250, disabled=True, key="rt_wait")
        if rt_transcript:
            col1, col2 = st.columns(2)
            with col1:
                st.download_button("📄 下載 TXT", data=full_text, file_name="即時辨識.txt", mime="text/plain", key="rt_dl2")
            with col2:
                if st.button("清除", key="rt_clear2"):
                    rt_transcript.clear()
                    st.rerun()
