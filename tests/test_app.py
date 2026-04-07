#!/usr/bin/env python3
"""
應用程式測試腳本
"""

import os
import sys

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from flask import render_template, request
from shared.database import db
from shared.models import User

def test_app():
    """完整測試應用程式"""
    print("🧪 開始測試應用程式...")
    
    try:
        # 1. 測試應用程式創建
        print("\n1️⃣ 測試應用程式創建...")
        app = create_app()
        print("✅ 應用程式創建成功")
        
        # 2. 測試模板載入（在請求上下文中）
        print("\n2️⃣ 測試模板載入...")
        with app.test_request_context('/'):
            try:
                render_template('login_unified.html')
                print("✅ 模板載入成功")
            except Exception as e:
                print(f"❌ 模板載入失敗: {e}")
                return False
        
        # 3. 測試資料庫連接
        print("\n3️⃣ 測試資料庫連接...")
        with app.app_context():
            try:
                # 測試資料庫連接
                from sqlalchemy import text
                db.session.execute(text('SELECT 1'))
                print("✅ 資料庫連接成功")
                
                # 測試 User 模型
                test_user = User.query.filter_by(username='testuser').first()
                if test_user:
                    print("✅ 測試用戶存在")
                    print(f"   用戶名: {test_user.username}")
                    print(f"   郵箱: {test_user.email}")
                    print(f"   是否活躍: {test_user.is_active}")
                    print(f"   認證狀態: {test_user.is_authenticated}")
                else:
                    print("❌ 測試用戶不存在")
                
            except Exception as e:
                print(f"❌ 資料庫測試失敗: {e}")
                return False
        
        # 4. 測試路由註冊
        print("\n4️⃣ 測試路由註冊...")
        with app.test_client() as client:
            try:
                # 測試登入頁面
                response = client.get('/login')
                if response.status_code == 200:
                    print("✅ 登入路由正常")
                else:
                    print(f"❌ 登入路由異常: {response.status_code}")
                
                # 測試註冊頁面
                response = client.get('/register')
                if response.status_code == 200:
                    print("✅ 註冊路由正常")
                else:
                    print(f"❌ 註冊路由異常: {response.status_code}")
                
            except Exception as e:
                print(f"❌ 路由測試失敗: {e}")
                return False
        
        print("\n🎉 所有測試通過！應用程式可以正常啟動")
        return True
        
    except Exception as e:
        print(f"\n❌ 應用程式測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_app()
    if success:
        print("\n🚀 現在可以安全啟動應用程式:")
        print("   python app.py")
    else:
        print("\n⚠️  請修復上述問題後再啟動應用程式")
