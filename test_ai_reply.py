#!/usr/bin/env python3
"""
AI 回覆測試腳本
模擬 LINE 用戶發送訊息並檢查 AI 回覆
"""

import sys
import os
sys.path.insert(0, '.')

from app import create_app
from shared.database import db
from shared.models import Merchant
from ai_modules.line_bot import LineBotHandler
from ai_modules.ai_service import AIService

def test_ai_reply():
    """測試 AI 回覆功能"""
    print("🧪 開始測試 AI 回覆功能...")
    
    app = create_app()
    
    with app.app_context():
        # 獲取測試商家
        merchant = Merchant.query.first()
        
        if not merchant:
            print("❌ 找不到商家資料")
            return
        
        if not merchant.line_channel_access_token or not merchant.line_channel_secret or not merchant.google_gemini_api_key:
            print("❌ 商家缺少必要的金鑰配置")
            return
        
        print(f"✅ 找到商家: {merchant.name}")
        print(f"✅ LINE Token: {'已配置' if merchant.line_channel_access_token else '未配置'}")
        print(f"✅ LINE Secret: {'已配置' if merchant.line_channel_secret else '未配置'}")
        print(f"✅ Gemini Key: {'已配置' if merchant.google_gemini_api_key else '未配置'}")
        
        # 創建 LINE Bot 處理器
        try:
            bot_handler = LineBotHandler(merchant)
            ai_service = AIService(merchant.google_gemini_api_key)
            
            # 測試訊息列表
            test_messages = [
                "你好",
                "我想預約",
                "你們的營業時間是什麼？",
                "剪髮多少錢？",
                "明天下午3點可以預約嗎？"
            ]
            
            print("\n📝 測試訊息:")
            for i, message in enumerate(test_messages, 1):
                print(f"  {i}. {message}")
                
                # 模擬處理訊息
                print(f"  🤖 AI 分析中...")
                intent = ai_service.analyze_intent(message)
                print(f"  🎯 意圖: {list(intent.keys())[list(intent.values()).index(True) + 1]}")
                
                if intent['appointment_request']:
                    print("  📅 處理預約請求...")
                    # 這裡會觸發服務選擇邏輯
                else:
                    print("  💬 生成 AI 回覆...")
                    response = ai_service.generate_response(
                        message,
                        merchant.name,
                        merchant.ai_tone or "友善專業"
                    )
                    print(f"  📤 AI 回覆: {response[:100]}..." if len(response) > 100 else response)
                    print("  ✅ 回覆成功！")
                
                print("-" * 50)
                
        except Exception as e:
            print(f"❌ 測試過程中發生錯誤: {e}")

if __name__ == '__main__':
    test_ai_reply()
