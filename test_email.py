#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
郵件功能測試腳本
用於測試忘記密碼的郵件發送功能
"""

import os
import sys
from flask_mail import Message

# 添加項目根目錄到 Python 路徑
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, mail

def test_email_config():
    """測試郵件配置"""
    with app.app_context():
        print("=== 郵件配置檢查 ===")
        print(f"MAIL_SERVER: {app.config.get('MAIL_SERVER')}")
        print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
        print(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
        print(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
        print(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
        print(f"MAIL_PASSWORD: {'*' * len(app.config.get('MAIL_PASSWORD', '')) if app.config.get('MAIL_PASSWORD') else 'None'}")

def test_send_email():
    """測試發送郵件"""
    with app.app_context():
        print("\n=== 測試郵件發送 ===")
        
        try:
            # 創建測試郵件
            msg = Message(
                subject='數位店長 - 郵件功能測試',
                recipients=['attak.company@gmail.com'],  # 修改為你的測試郵件
                html=f'''
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
                    <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px; text-align: center;">
                        <h2 style="color: #333; margin-bottom: 20px;">數位店長 - 郵件功能測試</h2>
                        <p style="color: #666; font-size: 16px; margin-bottom: 30px;">這是一封測試郵件，用於驗證郵件發送功能是否正常。</p>
                        <div style="background-color: #28a745; color: white; font-size: 24px; font-weight: bold; padding: 20px; border-radius: 8px; margin: 20px 0;">
                            ✅ 郵件功能正常
                        </div>
                        <p style="color: #999; font-size: 12px;">如果收到這封郵件，表示郵件發送功能正常運作。</p>
                    </div>
                </body>
                </html>
                '''
            )
            
            # 發送郵件
            mail.send(msg)
            print("✅ 郵件發送成功！")
            print("請檢查您的收件箱（包括垃圾郵件）")
            
        except Exception as e:
            print(f"❌ 郵件發送失敗：{e}")
            print("可能的原因：")
            print("1. Gmail 密碼錯誤或已過期")
            print("2. Gmail 安全設定問題")
            print("3. 網路連線問題")
            print("4. SMTP 伺服器設定錯誤")

def test_verification_code():
    """測試驗證碼生成"""
    from app import VerificationCode
    
    with app.app_context():
        print("\n=== 測試驗證碼生成 ===")
        
        try:
            # 生成測試驗證碼
            code = VerificationCode.generate_code()
            print(f"✅ 驗證碼生成成功：{code}")
            
            # 創建驗證碼記錄
            verification = VerificationCode(email='test@example.com', code=code)
            print(f"✅ 驗證碼記錄創建成功")
            print(f"   郵件：{verification.email}")
            print(f"   驗證碼：{verification.code}")
            print(f"   創建時間：{verification.created_at}")
            print(f"   過期時間：{verification.expires_at}")
            print(f"   是否已使用：{verification.is_used}")
            
        except Exception as e:
            print(f"❌ 驗證碼生成失敗：{e}")

def check_env_file():
    """檢查環境變數檔案"""
    print("\n=== 環境變數檔案檢查 ===")
    
    env_files = ['.env', '.env.example', '.env.template']
    
    for env_file in env_files:
        file_path = os.path.join(os.path.dirname(__file__), env_file)
        if os.path.exists(file_path):
            print(f"✅ {env_file} 存在")
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'MAIL_' in content:
                    print(f"   {env_file} 包含郵件配置")
                else:
                    print(f"   {env_file} 不包含郵件配置")
        else:
            print(f"❌ {env_file} 不存在")

if __name__ == "__main__":
    print("開始測試郵件功能...")
    
    try:
        # 檢查環境變數檔案
        check_env_file()
        
        # 檢查郵件配置
        test_email_config()
        
        # 測試驗證碼生成
        test_verification_code()
        
        # 詢問是否測試郵件發送
        response = input("\n是否測試郵件發送？(y/n): ")
        if response.lower() == 'y':
            test_send_email()
        
        print("\n=== 測試完成 ===")
        print("如果郵件發送失敗，請檢查：")
        print("1. Gmail 密碼是否正確")
        print("2. Gmail 是否啟用了兩步驟驗證")
        print("3. 是否需要使用應用程式密碼")
        print("4. 防火牆是否阻擋 SMTP 連線")
        
    except Exception as e:
        print(f"測試過程中發生錯誤：{e}")
        import traceback
        traceback.print_exc()
