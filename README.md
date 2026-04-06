# 🤖 LINE AI 智能預約系統

## 📋 項目概述

LINE AI 智能預約系統是一個基於 Flask 的智能客服預約管理系統，整合 LINE Bot 和 Google Gemini AI，提供自動化的客服和預約管理功能。

## ✨ 主要功能

### 🎯 核心功能
- **🤖 AI 智能客服** - Google Gemini 驅動的對話系統
- **📅 預約管理** - 完整的預約創建和管理
- **🏪 商家後台** - 蘋果風格的管理介面
- **👥 多用戶支援** - 安全的多商家系統
- **🔗 Webhook 整合** - LINE Bot 即時回應

### 🎨 設計特色
- **🍎 Apple 風格** - 精緻的黑白設計
- **📱 響應式設計** - 完美支援各種設備
- **✨ 流暢動畫** - 優雅的用戶體驗
- **🎯 直觀操作** - 簡單易用的介面

## 🚀 快速開始

### 📋 系統需求
- Python 3.8+
- PostgreSQL 資料庫
- LINE Developers 帳號
- Google Gemini API 金鑰

### ⚡ 安裝步驟

1. **克隆專案**
   ```bash
   git clone https://github.com/你的用戶名/line-ai-appointment-system.git
   cd line-ai-appointment-system
   ```

2. **設置環境**
   ```bash
   # 創建虛擬環境
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   
   # 安裝依賴
   pip install -r requirements.txt
   
   # 設置環境變數
   cp .env.example .env
   # 編輯 .env 文件填入你的 API 金鑰
   ```

3. **初始化資料庫**
   ```bash
   # 設置 PostgreSQL
   python scripts/setup_postgresql.py
   
   # 遷移到多用戶系統
   python scripts/migrate_to_multiuser.py
   ```

4. **啟動應用**
   ```bash
   python app.py
   ```

5. **訪問系統**
   - 本地: http://localhost:5000
   - 登入: 創建管理員帳號

## 📁 項目結構

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
├── 📁 docs/                  # 📚 文檔目錄
│   ├── 📖 README.md           # 項目說明
│   ├── 📖 SETUP.md           # 設置指南
│   ├── 📖 COLLABORATION.md   # 協作指南
│   ├── 📖 AI_RULES.md        # AI 規範
│   └── 📖 FILE_STRUCTURE.md  # 文件結構
├── 📁 scripts/               # 🛠️ 工具腳本
│   ├── 🔧 setup_collaboration.sh
│   ├── 🔧 start_ngrok.py
│   ├── 🔧 setup_postgresql.py
│   └── 🔧 migrate_to_multiuser.py
└── 📁 backup/               # 🗂️ 備份目錄
```

## 📖 文檔

### 🚀 設置指南
- **[SETUP.md](docs/SETUP.md)** - 完整的設置指南
- **[COLLABORATION.md](docs/COLLABORATION.md)** - 團隊協作指南
- **[AI_RULES.md](docs/AI_RULES.md)** - Live Share AI 協作規範

### 🛠️ 工具腳本
- **setup_collaboration.sh** - 協作環境設置
- **start_ngrok.py** - ngrok 隧道啟動
- **setup_postgresql.py** - 資料庫初始化
- **migrate_to_multiuser.py** - 多用戶系統遷移

## 🎯 使用指南

### 👥 商家管理
1. **註冊帳號** - 創建商家帳號
2. **設定服務** - 添加服務項目和價格
3. **設定時間** - 配置營業時間
4. **設定 LINE** - 配置 LINE Bot
5. **開始營業** - 接收客戶預約

### 🤖 AI 客服
1. **客戶發送訊息** - 通過 LINE 發送
2. **AI 自動回應** - Gemini 生成智能回覆
3. **預約確認** - 自動創建預約記錄
4. **提醒通知** - 自動發送提醒

## 🔧 開發指南

### 🌿 本地開發
```bash
# 啟動開發服務器
python app.py

# 啟動 ngrok (本地測試)
python scripts/start_ngrok.py
```

### 🤝 協作開發
```bash
# 設置協作環境
./scripts/setup_collaboration.sh

# 開始協作
./scripts/start_collaboration.sh
```

## 🚨 故障排除

### 常見問題
1. **資料庫連接失敗**
   - 檢查 PostgreSQL 服務狀態
   - 確認 .env 中的資料庫設定

2. **LINE Bot 無回應**
   - 檢查 Webhook URL 設定
   - 確認 LINE Channel Access Token

3. **AI 回應失敗**
   - 檢查 Google Gemini API 金鑰
   - 確認 API 配額

### 📞 獲取幫助
- 📖 查看 [文檔](docs/)
- 🐛 報告 [Issues](https://github.com/你的用戶名/line-ai-appointment-system/issues)
- 💬 討論 [Discord](你的 Discord 連結)

## 📄 授權

MIT License - 詳見 [LICENSE](LICENSE) 文件

## 🤝 貢獻

歡迎貢獻！請查看 [貢獻指南](docs/CONTRIBUTING.md)

## 🎉 致謝

- Google Gemini AI
- LINE Messaging API
- Flask 框架
- Bootstrap UI 框架

---

**🚀 讓 AI 客服更智能，讓預約管理更簡單！**
