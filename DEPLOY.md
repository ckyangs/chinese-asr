# 部署指南：即時麥克風辨識

本專案已加入 **STUN 伺服器** 設定，讓 WebRTC 在雲端部署環境能建立麥克風連線。

## 建議部署平台

| 平台 | 即時辨識 | 說明 |
|------|----------|------|
| **Hugging Face Spaces** | ✅ 支援較佳 | 與 streamlit-webrtc 相容性好 |
| **Streamlit Cloud** | ⚠️ 視環境而定 | 部分情況可能需 TURN 伺服器 |

## Hugging Face Spaces 部署步驟

1. 註冊 [Hugging Face](https://huggingface.co/) 帳號
2. 點選 **Create new Space**
3. 設定：
   - **Space name**：例如 `chinese-asr`
   - **SDK**：選擇 **Streamlit**
   - **License**：選 MIT 或 Apache-2.0
4. 上傳檔案或連結 GitHub：
   - `app.py`（主程式）
   - `requirements.txt`
   - `src/` 資料夾
   - `README.md`（含 Spaces 描述）
5. 建置完成後，開啟 Space 連結即可使用即時辨識

## Streamlit Cloud 部署步驟

> 詳細圖文說明請參考 [STREAMLIT_CLOUD_DEPLOY.md](STREAMLIT_CLOUD_DEPLOY.md)

1. **推送到 GitHub**：將專案 `git push` 至 GitHub 倉庫
2. **前往** [share.streamlit.io](https://share.streamlit.io)，用 GitHub 登入
3. 點選 **New app**
4. 設定 **Repository**、**Branch**（main）、**Main file path**（`app.py`）
5. 建議使用 **Standard** 方案（記憶體較大，適合 Whisper）
6. 點 **Deploy!** 等待建置完成

## 若即時辨識無法連線

可能原因：

1. **瀏覽器**：建議使用 Chrome 或 Edge
2. **防火牆**：部分企業網路可能封鎖 WebRTC
3. **HTTPS**：部署必須使用 HTTPS（Streamlit Cloud / HF Spaces 預設已啟用）

備用方案：使用「上傳檔案」或「麥克風錄音」分頁進行辨識。
