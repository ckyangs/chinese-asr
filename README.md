---
title: 中文語音辨識工具
emoji: 🎤
sdk: streamlit
sdk_version: "1.54.0"
app_file: app.py
pinned: false
---

# 中文語音辨識工具

支援 .mp3、.wav、.m4a 上傳，麥克風錄音，以及**即時邊講邊辨識**。使用 Faster-Whisper 引擎。

## 功能

- **上傳檔案**：上傳音訊後辨識
- **麥克風錄音**：錄製後辨識
- **即時辨識**：開啟麥克風後邊講邊輸出文字
- **匯出**：下載為 .txt 或 .srt 字幕檔

## 部署方式

### Hugging Face Spaces（推薦，即時辨識支援較佳）

1. 前往 [huggingface.co/spaces](https://huggingface.co/spaces)
2. 建立 New Space，選擇 **Streamlit** SDK
3. 將本專案檔案上傳或連結 Git 倉庫
4. 等待建置完成即可使用

### Streamlit Cloud

1. 將專案推送到 GitHub
2. 前往 [share.streamlit.io](https://share.streamlit.io)
3. 連結倉庫，主檔案設為 `app.py`
4. 部署完成後即可使用

## 本地執行

```bash
pip install -r requirements.txt
streamlit run app.py
```
