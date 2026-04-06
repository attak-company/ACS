#!/usr/bin/env python3
"""
ngrok 啟動腳本
自動檢測 ngrok 並更新 Webhook URL
"""

import requests
import time
import sys

def check_ngrok_status():
    """檢查 ngrok 狀態並獲取 URL"""
    try:
        # 檢查 ngrok API
        response = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            
            # 尋找 HTTP 隧道
            for tunnel in tunnels:
                if tunnel.get('proto') == 'http' and tunnel.get('public_url'):
                    url = tunnel['public_url']
                    print(f"✅ ngrok 正在運行")
                    print(f"🌐 公開 URL: {url}")
                    
                    # 提取用戶名稱（假設第一個用戶）
                    # 這裡可以改為動態獲取或從配置文件讀取
                    username = "your_username"  # 替換為實際用戶名稱
                    
                    webhook_url = f"{url}/webhook/{username}"
                    print(f"🔗 Webhook URL: {webhook_url}")
                    print(f"👤 使用用戶名稱: {username}")
                    print(f"📋 複製此 URL 到 LINE Developers Console")
                    print()
                    return url
        
        print("❌ ngrok 未運行或無法連接")
        print("🚀 請先啟動 ngrok: ngrok http 5000")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"❌ 連接 ngrok API 失敗: {e}")
        return None
    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        return None

def main():
    print("🔍 檢查 ngrok 狀態...")
    print("=" * 50)
    
    url = check_ngrok_status()
    
    if url:
        print("=" * 50)
        print("✅ ngrok 已準備就緒！")
        print()
        print("📝 下一步：")
        print("1. 複製上面的 Webhook URL")
        print("2. 到 LINE Developers Console 設定 Webhook")
        print("3. 測試你的 LINE Bot")
    else:
        print("=" * 50)
        print("🚀 啟動指令：")
        print("ngrok http 5000")
        print()
        print("然後重新運行此腳本")

if __name__ == "__main__":
    main()
