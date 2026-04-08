
# ACS 應用程序主入口
# 總入口（只負責啟動與掛載路由）

import os
from flask import Flask
from flask_login import LoginManager
from flask_mail import Mail

# 導入共享模組
from shared.database import init_database, db, login_manager
from shared.utils import init_mail, mail

# 導入 Web 模組
from web_modules.auth import auth_bp
from web_modules.dashboard import dashboard_bp
from web_modules.routes import web_bp

# 導入 AI 模組
from ai_modules.webhook import webhook_bp
from ai_modules.ai_routes import ai_bp

def create_app():
    """創建 Flask 應用"""
    app = Flask(__name__, 
                template_folder='web_modules/templates',
                static_folder='web_modules/static')
    
    # 基本配置
    app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
    app.config['DEBUG'] = os.getenv('FLASK_ENV', 'development') == 'development'
    
    # URL and Session Configuration
    # app.config['SERVER_NAME'] = 'localhost' # ngrok needs this to be flexible
    app.config['APPLICATION_ROOT'] = '/'
    app.config['PREFERRED_URL_SCHEME'] = 'https'  # ngrok uses https
    
    # Session configuration for ngrok
    app.config['SESSION_COOKIE_SECURE'] = False  # Set to True if using HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Allow cross-origin for ngrok
    
    # 初始化資料庫
    init_database(app)
    
    # 初始化郵件服務
    init_mail(app)
    
    # 註冊 Blueprint
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(web_bp)
    app.register_blueprint(webhook_bp)
    app.register_blueprint(ai_bp)
    
    # 創建資料表
    with app.app_context():
        from shared.models import User, Merchant, Service, Schedule, Appointment, VerificationCode, UserToken
        db.create_all()
    
    return app

def create_tables():
    """創建資料表（獨立函數）"""
    app = create_app()
    with app.app_context():
        from shared.models import User, Merchant, Service, Schedule, Appointment, VerificationCode, UserToken
        db.create_all()
        print("資料表創建完成")

if __name__ == '__main__':
    app = create_app()
    
    # 開發模式
    if app.config.get('DEBUG'):
        # 使用 0.0.0.0 以允許外部存取，或保持 127.0.0.1
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        app.run(host='0.0.0.0', port=5000)
