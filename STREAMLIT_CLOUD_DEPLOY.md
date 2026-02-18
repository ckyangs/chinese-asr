# Streamlit Community Cloud 部署指南

完整步驟協助將「中文語音辨識工具」部署至 Streamlit Cloud。

---

## 前置準備

### 1. 確認專案結構

部署前請確認專案包含以下檔案與資料夾：

```
ASR/
├── app.py              ← 主程式（必要）
├── requirements.txt    ← 依賴套件（必要）
├── src/
│   ├── __init__.py
│   ├── core/
│   │   ├── transcriber.py
│   │   ├── realtime.py
│   │   └── ...
│   └── utils/
├── .streamlit/
│   └── config.toml
└── README.md
```

### 2. 初始化 Git 並推送到 GitHub

若專案尚未使用 Git：

```bash
cd /Users/ckyang/ASR

# 初始化 Git 倉庫
git init

# 建立 .gitignore（若尚未建立）
# 確保已排除 venv/、__pycache__/ 等

# 加入檔案
git add app.py requirements.txt src/ .streamlit/ README.md DEPLOY.md
git add .gitignore

# 提交
git commit -m "Initial commit: 中文語音辨識工具"

# 在 GitHub 建立新倉庫後，設定遠端並推送
git remote add origin https://github.com/你的帳號/你的倉庫名稱.git
git branch -M main
git push -u origin main
```

若專案已在 Git 管理中，直接推送即可：

```bash
git add .
git commit -m "部署設定"
git push origin main
```

---

## 部署步驟

### Step 1：前往 Streamlit Community Cloud

1. 開啟瀏覽器，前往 **[share.streamlit.io](https://share.streamlit.io)**
2. 使用 **GitHub** 帳號登入
3. 首次使用需授權 Streamlit 存取你的 GitHub 倉庫

### Step 2：新增 App

1. 點選 **「New app」** 或 **「Deploy an app」**
2. 填寫下列設定：

| 欄位 | 建議值 | 說明 |
|------|--------|------|
| **Repository** | `你的帳號/ASR` | 選擇已推送專案的 GitHub 倉庫 |
| **Branch** | `main` | 預設分支 |
| **Main file path** | `app.py` | 主程式檔名，若在子資料夾則填 `app.py` 或 `ASR/app.py`（依倉庫根目錄結構） |
| **App URL** | 自動產生 | 例如 `你的app名稱.streamlit.app` |

### Step 3：選擇資源方案

- **Community**（免費）：記憶體較少，載入 Whisper 可能較慢或失敗  
- **Standard**（付費）：記憶體較大，較適合載入 Whisper 模型  

若使用免費方案時出現記憶體不足，可考慮：

1. 改用較小的模型：側邊欄選擇 **tiny** 或 **base**
2. 升級為 Standard 方案

### Step 4：部署

1. 點選 **「Deploy!」**
2. 等候約 2–5 分鐘建置
3. 建置完成後會顯示 App 網址
4. 第一次開啟時，Whisper 會下載模型，可能需要多等數十秒

---

## 常見問題

### 專案在子資料夾時，Main file path 如何填？

若倉庫結構為：

```
我的倉庫/
└── ASR/
    ├── app.py
    └── requirements.txt
```

則 **Main file path** 填：`ASR/app.py`  

若 `app.py` 就在倉庫根目錄，填：`app.py`

### 建置失敗怎麼辦？

1. 檢查 `requirements.txt` 套件是否正確
2. 在 Cloud 介面查看 **Logs** 錯誤訊息
3. 確認 Python 版本相容（預設為 3.12）

### 即時辨識無法連線？

- 使用 Chrome 或 Edge
- 允許麥克風權限
- 可先使用「上傳檔案」或「麥克風錄音」分頁測試

---

## 部署完成後

- App 網址格式：`https://你的app名稱.streamlit.app`
- 推送到 GitHub 後，Streamlit Cloud 會自動重新部署
- 可在 Streamlit Cloud 後台檢視 Logs 與資源使用情形
