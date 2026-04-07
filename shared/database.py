# 共享模組 - 資料庫連線
# 負責：資料庫連線配置

from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# 初始化資料庫
db = SQLAlchemy()

# 初始化登入管理器
login_manager = LoginManager()

def init_database(app):
    """初始化資料庫"""
    # 配置資料庫 - 暫時使用 SQLite 進行測試
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///acs_dev.db'
    print("使用 SQLite 資料庫 (開發模式)")
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # 初始化擴展
    db.init_app(app)
    login_manager.init_app(app)
    
    # 設定登入視圖
    login_manager.login_view = 'auth.login'
    login_manager.login_message = '請先登入以訪問此頁面。'
    login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    """載入用戶"""
    from .models import User
    return User.query.get(int(user_id))
