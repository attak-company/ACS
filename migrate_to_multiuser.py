#!/usr/bin/env python3
"""
多用戶系統資料庫遷移腳本
將現有的單用戶資料遷移到多用戶系統
"""

import os
from dotenv import load_dotenv
from app import app, db, User, Merchant, Service, Schedule, Appointment, BlockedTime
from werkzeug.security import generate_password_hash

load_dotenv()

def migrate_database():
    """遷移資料庫到多用戶系統"""
    with app.app_context():
        print("🔧 開始遷移到多用戶系統...")
        
        # 檢查是否已經有用戶
        existing_users = User.query.all()
        if existing_users:
            print("⚠️  資料庫已經有用戶，跳過遷移")
            return
        
        # 檢查是否有現有的商家資料
        existing_merchant = Merchant.query.filter_by(user_id=None).first()
        if not existing_merchant:
            print("📝 沒有現有商家資料，創建預設用戶...")
            create_default_user()
            return
        
        print(f"📋 找到現有商家: {existing_merchant.name}")
        
        # 創建預設用戶
        default_user = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123')
        )
        
        db.session.add(default_user)
        db.session.commit()
        
        # 將現有商家關聯到預設用戶
        existing_merchant.user_id = default_user.id
        db.session.commit()
        
        print(f"✅ 已將商家 {existing_merchant.name} 關聯到用戶 {default_user.username}")
        print("🎉 遷移完成！")
        print("📱 預設登入資訊：")
        print("   使用者名稱: admin")
        print("   密碼: admin123")

def create_default_user():
    """創建預設用戶和商家"""
    with app.app_context():
        # 創建預設用戶
        default_user = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('admin123')
        )
        
        db.session.add(default_user)
        db.session.commit()
        
        # 創建對應的商家
        merchant = Merchant(
            user_id=default_user.id,
            name='Attak穿刺店',
            phone='0908929623',
            address='嘉義市東區圓福街118巷2弄106號',
            description='',
            arrival_info='車庫有兩個停車位',
            ai_tone='formal',
            line_channel_access_token='aWtDznSW83O0f/ltXA8IK/0P8FFYYOu7mk9MhxYiv1cHlRHEcEb80BQlKPzK4j8DfJyept9dxW0D1YjHqHteLXxRc8BDGfZ3hbV+S0YhPwOWpjGj9tuRPt/PzhRet5GZOANZrvZJj2HRRUTeQ/NP9gdB04t89/1O/w1cDnyilFU=',
            line_channel_secret='39db8362d4e52a80794034e3965ac8dc'
        )
        
        db.session.add(merchant)
        db.session.commit()
        
        print("✅ 創建預設用戶和商家完成")
        print("📱 預設登入資訊：")
        print("   使用者名稱: admin")
        print("   密碼: admin123")

if __name__ == "__main__":
    migrate_database()
