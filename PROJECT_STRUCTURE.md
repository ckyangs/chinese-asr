# 中文語音辨識工具 - 專案目錄結構

## 建議專案結構

```
ASR/
├── main.py                 # 應用程式主入口
├── requirements.txt        # Python 套件依賴
├── README.md               # 專案說明文件
│
├── src/                    # 主要程式碼目錄
│   ├── __init__.py
│   ├── app.py              # PyQt6 主應用程式視窗
│   ├── ui/                 # 介面相關
│   │   ├── __init__.py
│   │   ├── main_window.py  # 主視窗 UI 與事件綁定
│   │   └── styles.py      # 樣式定義（可選）
│   │
│   ├── core/               # 核心辨識邏輯
│   │   ├── __init__.py
│   │   ├── transcriber.py  # Whisper/Faster-Whisper 辨識引擎封裝
│   │   └── audio_utils.py  # 音訊格式處理（轉換、驗證）
│   │
│   └── utils/              # 工具函式
│       ├── __init__.py
│       ├── export.py       # 匯出為 .txt / .srt
│       └── progress.py    # 進度追蹤輔助
│
└── assets/                 # 靜態資源（可選）
    └── icons/             # 圖示檔案
```

## 模組職責說明

| 模組 | 職責 |
|------|------|
| `main.py` | 程式進入點，啟動 PyQt6 應用程式 |
| `app.py` | 建立主視窗、整合各模組 |
| `main_window.py` | 上傳按鈕、辨識按鈕、進度條、文字框等 UI 元件與事件 |
| `transcriber.py` | 載入 Faster-Whisper 模型、執行辨識、回傳辨識結果 |
| `audio_utils.py` | 驗證副檔名、必要時做格式轉換（如 m4a → wav） |
| `export.py` | 將辨識文字匯出為 .txt 或 .srt |
| `progress.py` | 配合辨識流程提供進度回報給 UI |

## 執行方式

```bash
# 安裝依賴
pip install -r requirements.txt

# 啟動應用程式
python main.py
```

## 系統需求

- **Python**: 3.9 或以上
- **FFmpeg**（建議安裝）：用於處理 .mp3、.m4a 等格式，可透過 `brew install ffmpeg`（macOS）安裝
