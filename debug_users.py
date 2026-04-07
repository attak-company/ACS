#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
用戶數據調試腳本
用於檢查現有用戶和驗證密碼
"""

import os
import sys
from werkzeug.security import generate_password_hash, check_password_hash

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User

def debug_users():
    """調試用戶數據"""
    with app.app_context():
        print("=== 用戶數據調試 ===")
        
        # 查詢所有用戶
        users = User.query.all()
        print(f"總用戶數: {len(users)}")
        
        for user in users:
            print(f"\n--- 用戶 ID: {user.id} ---")
            print(f"用戶名: '{user.username}'")
            print(f"郵件: '{user.email}'")
            print(f"密碼哈希: '{user.password_hash}'")
            print(f"創建時間: {user.created_at}")
        
        # 測試特定用戶的密碼驗證
        print("\n=== 密碼測試 ===")
        test_password = "123456"  # 修改為你要測試的密碼
        
        for user in users:
            is_valid = user.check_password(test_password)
            print(f"用戶 '{user.username}' 密碼 '{test_password}' 驗證結果: {is_valid}")
        
        # 測試手動密碼哈希
        print("\n=== 手動密碼哈希測試 ===")
        test_password = "123456"
        manual_hash = generate_password_hash(test_password)
        print(f"密碼 '{test_password}' 的哈希值: {manual_hash}")
        print(f"手動哈希驗證: {check_password_hash(manual_hash, test_password)}")

def create_test_user():
    """創建測試用戶"""
    with app.app_context():
        print("\n=== 創建測試用戶 ===")
        
        # 檢查是否已存在
        existing_user = User.query.filter_by(username="testuser").first()
        if existing_user:
            print("測試用戶已存在")
            return
        
        # 創建新用戶
        test_user = User(
            username="testuser",
            email="test@example.com"
        )
        test_user.set_password("123456")
        
        db.session.add(test_user)
        db.session.commit()
        
        print("測試用戶創建成功")
        print(f"用戶名: testuser")
        print(f"郵件: test@example.com")
        print(f"密碼: 123456")

if __name__ == "__main__":
    print("開始調試用戶數據...")
    
    try:
        debug_users()
        
        # 詢問是否創建測試用戶
        response = input("\n是否創建測試用戶 (testuser/123456)? (y/n): ")
        if response.lower() == 'y':
            create_test_user()
        
    except Exception as e:
        print(f"錯誤: {e}")
        import traceback
        traceback.print_exc()
