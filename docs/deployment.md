# 部署說明

## 🚀 **部署概述**

本文檔說明如何部署 ACS 系統到生產環境，包括環境配置、依賴安裝和系統啟動。

---

## 📋 **部署前準備**

### **1. 系統需求**
#### **硬體需求**
- **CPU**: 2核心以上
- **記憶體**: 4GB 以上
- **硬碟**: 20GB 以上可用空間
- **網路**: 穩定的網路連接

#### **軟體需求**
- **作業系統**: Ubuntu 20.04+ / CentOS 8+ / Windows Server
- **Python**: 3.9+
- **資料庫**: PostgreSQL 12+
- **Web 伺服器**: Nginx / Apache

### **2. 依賴服務**
#### **外部服務**
- **Google Gemini API**: AI 服務
- **LINE Messaging API**: LINE Bot 功能
- **SMTP 服務**: 郵件發送功能

#### **資料庫服務**
- **PostgreSQL**: 主資料庫
- **Redis**: 快取和會話存儲（可選）

---

## 🔧 **環境配置**

### **1. 創建虛擬環境**
```bash
# 創建虛擬環境
python -m venv venv

# 啟動虛擬環境
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### **2. 安裝依賴**
```bash
# 安裝 Python 依賴
pip install -r requirements.txt

# 安裝 PostgreSQL 驅動（如需要）
pip install psycopg2-binary
```

### **3. 環境變數配置**
創建 `.env` 檔案：
```bash
# LINE Bot Configuration
LINE_CHANNEL_ACCESS_TOKEN=your_line_channel_access_token
LINE_CHANNEL_SECRET=your_line_channel_secret

# Google Gemini API
GOOGLE_GEMINI_API_KEY=your_google_gemini_api_key

# Flask Configuration
FLASK_SECRET_KEY=your_flask_secret_key
FLASK_ENV=production

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/line_ai_appointment

# Email Configuration
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_email_password
MAIL_DEFAULT_SENDER=your_email@gmail.com
```

---

## 🗄️ **資料庫設置**

### **1. PostgreSQL 安裝**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib

# CentOS/RHEL
sudo yum install postgresql-server postgresql-contrib
sudo postgresql-setup initdb
```

### **2. 資料庫配置**
```bash
# 切換到 postgres 用戶
sudo -u postgres psql

# 創建資料庫
CREATE DATABASE line_ai_appointment;

# 創建用戶
CREATE USER app_user WITH PASSWORD 'your_password';

# 授權
GRANT ALL PRIVILEGES ON DATABASE line_ai_appointment TO app_user;

# 退出
\q
```

### **3. 資料庫遷移**
```bash
# 初始化資料庫
python -c "
from app import create_tables
create_tables()
print('資料庫表創建完成')
"
```

---

## 🌐 **Web 服務器配置**

### **1. Nginx 配置**
創建 `/etc/nginx/sites-available/acs`：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/ACS/web_modules/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

### **2. 啟用站點**
```bash
# 創建軟連結
sudo ln -s /etc/nginx/sites-available/acs /etc/nginx/sites-enabled/

# 測試配置
sudo nginx -t

# 重啟 Nginx
sudo systemctl restart nginx
```

### **3. SSL 配置（可選）**
```bash
# 使用 Let's Encrypt
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

---

## 🚀 **應用部署**

### **1. 代碼部署**
```bash
# 克隆代碼
git clone https://github.com/your-repo/ACS.git
cd ACS

# 安裝依賴
pip install -r requirements.txt
```

### **2. 應用配置**
```bash
# 設置環境變數
export FLASK_ENV=production
export FLASK_APP=app.py

# 創建實例文件夾
mkdir -p instance
```

### **3. 啟動應用**
#### **開發模式**
```bash
python app.py
```

#### **生產模式**
```bash
# 使用 Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app

# 使用 uWSGI
pip install uwsgi
uwsgi --http :5000 --wsgi-file app.py --callable app
```

### **4. 進程管理**
#### **Systemd 服務**
創建 `/etc/systemd/system/acs.service`：
```ini
[Unit]
Description=ACS Application
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/ACS
Environment=PATH=/path/to/ACS/venv/bin
ExecStart=/path/to/ACS/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

啟動服務：
```bash
sudo systemctl daemon-reload
sudo systemctl enable acs
sudo systemctl start acs
```

---

## 🔍 **健康檢查**

### **1. 應用健康檢查**
```bash
# 檢查應用狀態
curl -f http://localhost:5000/health || exit 1

# 檢查資料庫連接
python -c "
from shared.database import db
try:
    db.engine.execute('SELECT 1')
    print('資料庫連接正常')
except Exception as e:
    print(f'資料庫連接失敗: {e}')
"
```

### **2. 服務監控**
```bash
# 檢查服務狀態
sudo systemctl status acs
sudo systemctl status nginx
sudo systemctl status postgresql

# 查看日誌
sudo journalctl -u acs -f
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/postgresql/postgresql-*.log
```

---

## 🔄 **更新部署**

### **1. 代碼更新**
```bash
# 拉取最新代碼
git pull origin main

# 安裝新依賴
pip install -r requirements.txt

# 運行資料庫遷移（如需要）
python migrate.py
```

### **2. 服務重啟**
```bash
# 重啟應用
sudo systemctl restart acs

# 重啟 Web 服務器
sudo systemctl restart nginx
```

### **3. 回滾機制**
```bash
# 回滾到上一個版本
git checkout HEAD~1

# 重啟服務
sudo systemctl restart acs
```

---

## 🔒 **安全配置**

### **1. 防火牆設置**
```bash
# UFW 防火牆
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable

# iptables 防火牆
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

### **2. 應用安全**
```bash
# 設置文件權限
sudo chown -R www-data:www-data /path/to/ACS
sudo chmod -R 755 /path/to/ACS
sudo chmod -R 644 /path/to/ACS/.env

# 配置 HTTPS
sudo certbot --nginx -d your-domain.com --email admin@your-domain.com --agree-tos --non-interactive
```

---

## 📊 **監控和日誌**

### **1. 應用監控**
```bash
# 安裝監控工具
pip install prometheus-client

# 配置監控端點
# 在 app.py 中添加監控代碼
```

### **2. 日誌配置**
```python
# 在 app.py 中配置日誌
import logging
from logging.handlers import RotatingFileHandler

# 配置日誌
handler = RotatingFileHandler('logs/app.log', maxBytes=10000, backupCount=3)
handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)
```

---

## 🚨 **故障排除**

### **1. 常見問題**
#### **應用無法啟動**
- **檢查**: 環境變數是否正確設置
- **檢查**: 依賴是否完整安裝
- **檢查**: 資料庫連接是否正常

#### **資料庫連接失敗**
- **檢查**: 資料庫服務是否運行
- **檢查**: 連接字符串是否正確
- **檢查**: 防火牆是否阻擋連接

#### **靜態文件無法載入**
- **檢查**: Nginx 配置是否正確
- **檢查**: 文件權限是否正確
- **檢查**: 路徑是否正確

### **2. 性能優化**
#### **資料庫優化**
```sql
-- 創建索引
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_merchants_user_id ON merchants(user_id);
```

#### **應用優化**
```python
# 配置連接池
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_size': 10,
    'pool_recycle': 120,
    'pool_pre_ping': True
}
```

---

## 📋 **部署檢查清單**

### **部署前檢查**
- [ ] 環境變數已配置
- [ ] 資料庫已創建
- [ ] 依賴已安裝
- [ ] 配置文件已準備
- [ ] 備份策略已制定

### **部署後檢查**
- [ ] 應用正常啟動
- [ ] 資料庫連接正常
- [ ] Web 服務器配置正確
- [ ] SSL 證書有效
- [ ] 監控系統正常
- [ ] 日誌記錄正常
- [ ] 性能指標正常

---

## 📞 **技術支持**

### **聯繫方式**
- **技術文檔**: `/docs/`
- **API 規格**: `/docs/api_specs.md`
- **協作指南**: `/docs/collaboration.md`

### **緊急聯繫**
- **系統故障**: 立即聯繫技術團隊
- **安全問題**: 立即隔離受影響的系統
- **數據問題**: 立即停止相關服務並備份

---

**🎯 部署成功關鍵：準備、配置、測試、監控**
