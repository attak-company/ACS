# API 規格文檔

## 📋 **總覽**

本文檔定義了 ACS 系統中各模組之間的 API 介面規格，確保夥伴 A 和夥伴 B 能夠正確協作。

---

## 🔐 **Web 模組 API (夥伴 A 提供)**

### **認證相關 API**

#### **POST /api/send-verification-code**
發送驗證碼到用戶郵件

**請求格式：**
```json
{
    "email": "user@example.com"
}
```

**回應格式：**
```json
{
    "success": true,
    "message": "驗證碼已發送至您的電子郵件"
}
```

**錯誤回應：**
```json
{
    "error": "此電子郵件未註冊"
}
```

#### **POST /api/change-password-with-code**
使用驗證碼修改密碼

**請求格式：**
```json
{
    "email": "user@example.com",
    "verification_code": "123456",
    "new_password": "newpassword123"
}
```

**回應格式：**
```json
{
    "success": true,
    "message": "密碼修改成功"
}
```

### **店家資料 API**

#### **GET /api/merchant**
獲取當前用戶的店家資料

**回應格式：**
```json
{
    "name": "店家名稱",
    "description": "店家描述",
    "address": "店家地址",
    "phone": "店家電話",
    "arrival_info": "到店須知",
    "ai_tone": "友善專業",
    "line_channel_access_token": "token_here",
    "line_channel_secret": "secret_here"
}
```

#### **POST /api/merchant**
更新店家資料

**請求格式：**
```json
{
    "name": "店家名稱",
    "description": "店家描述",
    "address": "店家地址",
    "phone": "店家電話",
    "arrival_info": "到店須知",
    "ai_tone": "友善專業",
    "line_channel_access_token": "token_here",
    "line_channel_secret": "secret_here"
}
```

**回應格式：**
```json
{
    "success": true
}
```

### **服務項目 API**

#### **GET /api/services**
獲取服務項目列表

**回應格式：**
```json
[
    {
        "id": 1,
        "name": "剪髮",
        "description": "基本剪髮服務",
        "duration": 30,
        "price": 500
    }
]
```

#### **POST /api/services**
新增服務項目

**請求格式：**
```json
{
    "name": "剪髮",
    "description": "基本剪髮服務",
    "duration": 30,
    "price": 500
}
```

#### **PUT /api/services/{id}**
更新服務項目

#### **DELETE /api/services/{id}**
刪除服務項目

### **營業時間 API**

#### **GET /api/schedule**
獲取營業時間

**回應格式：**
```json
[
    {
        "id": 1,
        "day_of_week": 0,
        "start_time": "09:00",
        "end_time": "18:00",
        "is_available": true,
        "schedule_type": "regular"
    }
]
```

#### **POST /api/schedule**
更新營業時間

**請求格式：**
```json
[
    {
        "day_of_week": 0,
        "start_time": "09:00",
        "end_time": "18:00",
        "is_available": true
    }
]
```

### **預約管理 API**

#### **GET /api/appointments**
獲取預約列表

**回應格式：**
```json
[
    {
        "id": 1,
        "customer_name": "張三",
        "customer_phone": "0912345678",
        "service_id": 1,
        "service_name": "剪髮",
        "appointment_time": "2024-12-25T14:00:00",
        "notes": "備註",
        "status": "pending"
    }
]
```

#### **POST /api/appointments**
新增預約

#### **PUT /api/appointments/{id}**
更新預約

#### **DELETE /api/appointments/{id}**
刪除預約

---

## 🤖 **AI 模組 API (夥伴 B 提供)**

### **AI 聊天 API**

#### **POST /api/ai/chat**
AI 聊天回覆

**請求格式：**
```json
{
    "message": "你好，我想預約剪髮"
}
```

**回應格式：**
```json
{
    "success": true,
    "response": "你好！歡迎來到店家名稱，我可以幫您預約剪髮服務..."
}
```

### **AI 意圖分析 API**

#### **POST /api/ai/intent**
分析用戶意圖

**請求格式：**
```json
{
    "message": "我想預約明天下午3點"
}
```

**回應格式：**
```json
{
    "success": true,
    "intent": {
        "greeting": false,
        "appointment_request": true,
        "service_inquiry": false,
        "price_inquiry": false,
        "hours_inquiry": false,
        "contact_info": false
    }
}
```

### **AI 預約資訊提取 API**

#### **POST /api/ai/extract-appointment**
提取預約資訊

**請求格式：**
```json
{
    "message": "我想預約剪髮，明天下午3點"
}
```

**回應格式：**
```json
{
    "success": true,
    "appointment_info": {
        "service": "剪髮",
        "date": null,
        "time": "下午 3 點",
        "name": null,
        "phone": null
    }
}
```

---

## 🔗 **LINE Bot Webhook API**

### **POST /webhook/{username}**
特定用戶的 LINE Bot Webhook

**請求標頭：**
- `Content-Type: application/json`
- `X-Line-Signature: {signature}`

**請求格式：**
```json
{
    "events": [
        {
            "type": "message",
            "message": {
                "type": "text",
                "text": "用戶訊息"
            },
            "source": {
                "type": "user",
                "userId": "user_id"
            },
            "replyToken": "reply_token"
        }
    ]
}
```

**回應格式：**
```
HTTP 200 OK
```

### **POST /webhook**
通用 LINE Bot Webhook (向後兼容)

---

## 📊 **資料模型**

### **User 模型**
```json
{
    "id": 1,
    "username": "testuser",
    "email": "test@example.com",
    "created_at": "2024-01-01T00:00:00Z"
}
```

### **Merchant 模型**
```json
{
    "id": 1,
    "user_id": 1,
    "name": "店家名稱",
    "description": "店家描述",
    "address": "店家地址",
    "phone": "0912345678",
    "arrival_info": "到店須知",
    "ai_tone": "友善專業",
    "line_channel_access_token": "token_here",
    "line_channel_secret": "secret_here",
    "google_gemini_api_key": "api_key_here"
}
```

---

## 🔧 **錯誤處理**

### **標準錯誤回應格式**
```json
{
    "success": false,
    "error": "錯誤訊息"
}
```

### **常見錯誤代碼**
- `400` - 請求格式錯誤
- `401` - 未授權
- `403` - 禁止訪問
- `404` - 資源不存在
- `500` - 伺服器內部錯誤

---

## 🔄 **版本控制**

### **API 版本**
- 當前版本：v1.0
- 版本格式：`/api/v1/...`

### **變更日誌**
- v1.0 - 初始版本
- 包含所有基本功能

---

## 📝 **更新說明**

### **如何更新 API 規格**
1. 在此文件中新增或修改 API 定義
2. 更新對應的實現代碼
3. 通知另一個夥伴進行相應調整
4. 更新版本號和變更日誌

### **相容性說明**
- 所有 API 都需要向后兼容
- 重大變更需要提前通知
- 廢棄的 API 需要標註清楚
