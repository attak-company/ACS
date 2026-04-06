# 📁 LINE AI 系統文件結構整理

## 🎯 當前文件狀況

### ✅ 核心文件 (保留)
```
ACS/
├── 📄 app.py                    # 主應用程式
├── 📄 requirements.txt           # Python 依賴
├── 📄 .env.example             # 環境變數範例
├── 📄 .gitignore              # Git 忽略文件
├── 📁 templates/              # HTML 模板
│   ├── 📄 index.html         # 首頁
│   ├── 📄 login.html         # 登入頁面
│   └── 📄 merchant.html      # 商家後台
├── 📁 instance/               # Flask 實例文件
└── 📁 __pycache__/           # Python 緩存
```

### 📚 協作文檔 (保留但整理)
```
ACS/
├── 📖 README.md               # 項目說明
├── 📖 GITHUB_SETUP.md         # GitHub 設置指南
├── 📖 LIVE_COLLABORATION.md  # Live 協作指南
├── 📖 LIVE_SHARE_AI_RULES.md # Live Share AI 規範
└── 📖 QUICK_START.md         # 快速開始指南
```

### 🛠️ 工具腳本 (保留但整理)
```
ACS/
├── 🔧 setup_collaboration.sh  # 協作設置腳本
├── 🔧 start_ngrok.py         # ngrok 啟動腳本
├── 🔧 setup_postgresql.py    # 資料庫設置
└── 🔧 migrate_to_multiuser.py # 多用戶遷移
```

### 🗑️ 需要清理的文件
```
ACS/
├── ❌ app_clean.py           # 舊版本，可刪除
├── ❌ QUICK_START.md         # 與其他文檔重複
└── ❌ .venv/               # 虛擬環境 (可選保留)
```

## 🎯 整理後的文件結構

### 📁 建議的最終結構
```
ACS/
├── 📄 app.py                    # 主應用程式
├── 📄 requirements.txt           # Python 依賴
├── 📄 .env.example             # 環境變數範例
├── 📄 .gitignore              # Git 忽略文件
├── 📁 templates/              # HTML 模板
│   ├── 📄 index.html         # 首頁
│   ├── 📄 login.html         # 登入頁面
│   └── 📄 merchant.html      # 商家後台
├── 📁 instance/               # Flask 實例文件
├── 📁 __pycache__/           # Python 緩存
├── 📁 docs/                  # 📚 文檔目錄
│   ├── 📖 README.md           # 項目說明
│   ├── 📖 SETUP.md           # 設置指南
│   ├── 📖 COLLABORATION.md   # 協作指南
│   └── 📖 AI_RULES.md        # AI 規範
├── 📁 scripts/               # 🛠️ 工具腳本
│   ├── 🔧 setup_collaboration.sh
│   ├── 🔧 start_ngrok.py
│   ├── 🔧 setup_postgresql.py
│   └── 🔧 migrate_to_multiuser.py
└── 📁 backup/               # 🗂️ 備份目錄
    └── 📄 old_versions/      # 舊版本備份
```

## 🔄 整理步驟

### 步驟 1: 創建目錄結構
```bash
# 創建整理後的目錄
mkdir -p docs
mkdir -p scripts  
mkdir -p backup/old_versions
```

### 步驟 2: 移動文檔
```bash
# 移動文檔到 docs 目錄
mv README.md docs/
mv GITHUB_SETUP.md docs/SETUP.md
mv LIVE_COLLABORATION.md docs/COLLABORATION.md
mv LIVE_SHARE_AI_RULES.md docs/AI_RULES.md
```

### 步驟 3: 移動腳本
```bash
# 移動腳本到 scripts 目錄
mv setup_collaboration.sh scripts/
mv start_ngrok.py scripts/
mv setup_postgresql.py scripts/
mv migrate_to_multiuser.py scripts/
```

### 步驟 4: 清理舊文件
```bash
# 移動舊文件到備份
mv app_clean.py backup/old_versions/
mv QUICK_START.md backup/old_versions/
```

### 步驟 5: 更新引用
```bash
# 更新腳本中的路徑引用
# 更新文檔中的相對路徑
# 更新 README 中的文件引用
```

## 🎯 整理後的優勢

### ✅ 清晰的結構
- **核心文件** 在根目錄，易於找到
- **文檔** 統一在 `docs/` 目錄
- **腳本** 統一在 `scripts/` 目錄
- **備份** 統一在 `backup/` 目錄

### ✅ 易於維護
- **新文檔** 添加到 `docs/`
- **新腳本** 添加到 `scripts/`
- **舊文件** 移動到 `backup/`
- **清理** 只需清理特定目錄

### ✅ 專業外觀
- **符合標準** 的 Python 項目結構
- **易於部署** 的目錄佈局
- **版本控制** 友好的文件組織
- **團隊協作** 清晰的文件分工

## 🚀 執行整理

讓我開始執行整理步驟...
