#!/usr/bin/env python3
"""
PostgreSQL 資料庫設定腳本
請先確保 PostgreSQL 已安裝並運行
"""

import psycopg2
from psycopg2 import OperationalError
import os
from dotenv import load_dotenv

load_dotenv()

def create_database():
    """創建資料庫"""
    try:
        # 連接到 PostgreSQL 預設資料庫
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            user=os.getenv('DB_USER', 'username'),
            password=os.getenv('DB_PASSWORD', 'password'),
            database='postgres'  # 預設資料庫
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # 檢查資料庫是否存在
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'line_ai_appointment'")
        exists = cursor.fetchone()
        
        if not exists:
            # 創建資料庫
            cursor.execute('CREATE DATABASE line_ai_appointment')
            print("✅ 資料庫 'line_ai_appointment' 創建成功")
        else:
            print("✅ 資料庫 'line_ai_appointment' 已存在")
            
        cursor.close()
        conn.close()
        return True
        
    except OperationalError as e:
        print(f"❌ 連接 PostgreSQL 失敗: {e}")
        print("請檢查：")
        print("1. PostgreSQL 是否已安裝並運行")
        print("2. 使用者名稱和密碼是否正確")
        print("3. .env 文件中的設定是否正確")
        return False

def test_connection():
    """測試資料庫連接"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            user=os.getenv('DB_USER', 'username'),
            password=os.getenv('DB_PASSWORD', 'password'),
            database=os.getenv('DB_NAME', 'line_ai_appointment')
        )
        cursor = conn.cursor()
        cursor.execute('SELECT version()')
        version = cursor.fetchone()[0]
        print(f"✅ 連接成功！PostgreSQL 版本: {version}")
        cursor.close()
        conn.close()
        return True
    except OperationalError as e:
        print(f"❌ 連接失敗: {e}")
        return False

if __name__ == "__main__":
    print("🔧 設定 PostgreSQL 資料庫...")
    print("=" * 50)
    
    # 顯示當前設定
    print(f"主機: {os.getenv('DB_HOST', 'localhost')}")
    print(f"端口: {os.getenv('DB_PORT', '5432')}")
    print(f"資料庫: {os.getenv('DB_NAME', 'line_ai_appointment')}")
    print(f"使用者: {os.getenv('DB_USER', 'username')}")
    print("=" * 50)
    
    # 創建資料庫
    if create_database():
        print("\n🔗 測試連接...")
        if test_connection():
            print("\n🎉 PostgreSQL 設定完成！")
            print("現在可以運行 'python app.py' 啟動應用程式")
        else:
            print("\n❌ 連接測試失敗")
    else:
        print("\n❌ 資料庫創建失敗")
