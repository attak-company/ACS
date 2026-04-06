# LINE AI 智能客服自動預約系統

一套面向小型商户的 LINE AI 智能客服自動預約系統，整合 Google Gemini AI 和 LINE Bot，提供完整的自動化預約解決方案。

## 系統特色

- 🤖 **AI 智能客服**：使用 Google Gemini Flash API 提供自然對話體驗
- 📱 **LINE 整合**：無縫整合 LINE 平台，客戶透過熟悉介面預約
- 🗓️ **智能排程**：自動檢查時間衝突，推薦可用時段
- 🏪 **商家管理**：完整的後台管理系統，零代碼配置
- 📊 **數據分析**：提供預約統計和商業洞察

## 功能模組

### 商家後台功能
- **基本設定**：店家資訊、到店須知、AI 語氣風格
- **服務管理**：新增/編輯/刪除服務項目
- **營業時間**：設定每週營業時間
- **行事曆檢視**：可視化預約狀況
- **預約管理**：查看、確認、取消預約
- **LINE 設定**：配置 LINE Bot API

### AI 客服功能
- 自動識別預約意圖
- 智能推薦可用時段
- 自動創建預約記錄
- 個性化對話風格

## 技術架構

- **後端框架**：Flask (Python)
- **資料庫**：PostgreSQL
- **AI 服務**：Google Gemini Flash API
- **通訊平台**：LINE Bot API
- **前端框架**：Bootstrap 5 + JavaScript
- **行事曆**：FullCalendar

## 快速開始

### 1. 環境準備

```bash
# 複製專案
git clone <repository-url>
cd line-ai-appointment-system

# 安裝依賴
pip install -r requirements.txt
```

### 2. 環境設定

```bash
# 複製環境變數檔案
cp .env.example .env

# 編輯 .env 檔案，填入必要的 API 金鑰和 PostgreSQL 設定
```

### 3. PostgreSQL 設定

```bash
# 確保 PostgreSQL 已安裝並運行
# Windows: 下載並安裝 PostgreSQL
# macOS: brew install postgresql
# Ubuntu: sudo apt-get install postgresql postgresql-contrib

# 創建資料庫和設定連接
python setup_postgresql.py
```

### 4. 資料庫初始化

```bash
# 啟動 Flask 應用（會自動創建資料表）
python app.py
```

### 5. LINE Bot 設定

1. 前往 [LINE Developers Console](https://developers.line.biz/)
2. 創建新的 Provider 和 Channel (Messaging API)
3. 取得 Channel Access Token 和 Channel Secret
4. 在商家後台的「LINE 設定」頁面填入金鑰
5. 設定 Webhook URL：`http://your-domain.com/webhook`

## 使用指南

### 商家設定流程

1. **基本資訊設定**
   - 訪問 `/merchant` 進入後台
   - 填寫店家名稱、地址、電話等基本資訊
   - 設定到店須知和 AI 語氣風格

2. **服務項目管理**
   - 新增店家提供的服務項目
   - 設定每項服務的時長和價格

3. **營業時間設定**
   - 設定每週的營業時間
   - 可設定休息日或特殊時段

4. **LINE Bot 配置**
   - 填入 LINE Channel Access Token 和 Channel Secret
   - 測試 LINE Bot 連接

### 客戶預約流程

1. 客戶透過 LINE 發送訊息
2. AI 自動識別預約需求
3. 系統推薦可用時段
4. 客戶確認後自動創建預約
5. 系統發送確認訊息

## API 文件

### 主要端點

- `GET /` - 系統首頁
- `GET /merchant` - 商家後台
- `GET/POST /api/merchant` - 商家資訊 API
- `GET/POST /api/services` - 服務項目 API
- `GET/POST /api/schedule` - 營業時間 API
- `GET/POST /api/appointments` - 預約管理 API
- `GET /api/calendar/<date>` - 行事曆資料 API
- `POST /webhook` - LINE Bot Webhook

### 資料庫結構

#### Merchant（商家）
- id, name, description, address, phone
- line_channel_access_token, line_channel_secret
- ai_tone, arrival_info, created_at

#### Service（服務）
- id, merchant_id, name, description
- duration（分鐘）, price, created_at

#### Schedule（營業時間）
- id, merchant_id, day_of_week（0-6）
- start_time, end_time, is_available

#### Appointment（預約）
- id, merchant_id, customer_name, customer_phone
- service_id, date, time, status
- line_user_id, created_at

#### BlockedTime（封鎖時間）
- id, merchant_id, date, start_time, end_time, reason

## 部署說明

### 本地開發

```bash
python app.py
```

### 生產環境

建議使用 Gunicorn + Nginx：

```bash
# 安裝 Gunicorn
pip install gunicorn

# 啟動應用
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### Docker 部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app.py"]
```

## 安全注意事項

1. **API 金鑰保護**：確保 LINE Channel Access Token 和 Channel Secret 安全存放
2. **Webhook 驗證**：系統已實作 LINE Webhook 簽名驗證
3. **資料庫安全**：生產環境建議使用 PostgreSQL 取代 SQLite
4. **HTTPS**：生產環境必須使用 HTTPS

## 故障排除

### 常見問題

1. **LINE Bot 無回應**
   - 檢查 Webhook URL 是否正確
   - 確認 Channel Access Token 和 Channel Secret
   - 檢查伺服器防火牆設定

2. **AI 回應異常**
   - 檢查 Google Gemini API 金鑰
   - 確認 API 配額是否用盡

3. **預約時間衝突**
   - 檢查營業時間設定
   - 確認服務時長配置正確

## 授權條款

MIT License

## 貢獻指南

歡迎提交 Issue 和 Pull Request！

## 聯絡方式

如有問題，請透過 GitHub Issues 聯繫。

---

**注意**：本系統為開源專案，使用者需自行承擔使用風險。建議在正式上線前進行充分測試。
