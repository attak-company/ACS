# AI 模組 - Webhook 處理
# 負責：LINE Webhook 的入口

import time
import threading
from flask import Blueprint, request, jsonify, current_app
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from ai_modules.line_bot import LineBotHandler
from shared.database import db
from shared.models import Merchant, User

# 創建 Blueprint
webhook_bp = Blueprint('webhook', __name__)

def handle_webhook_async(app, body, signature, merchant_id):
    """在背景執行緒中處理 Webhook"""
    with app.app_context():
        try:
            merchant = Merchant.query.get(merchant_id)
            if not merchant:
                return
            
            bot_handler = LineBotHandler(merchant)
            bot_handler.handle_webhook(body, signature)
        except Exception as e:
            print(f"Background webhook processing error: {e}")

@webhook_bp.route('/webhook/<string:username>', methods=['POST'])
def merchant_webhook(username):
    """特定商家的 Webhook 端點"""
    try:
        # 根據用戶名稱查找對應的商家
        user = User.query.filter_by(username=username).first()
        if not user:
            return 'OK', 200
        
        merchant = Merchant.query.filter_by(user_id=user.id).first()
        if not merchant:
            return 'OK', 200
            
        # 獲取請求內容
        signature = request.headers.get('X-Line-Signature')
        body = request.get_data(as_text=True)
        
        # 立即啟動背景任務處理 AI 邏輯
        app = current_app._get_current_object()
        thread = threading.Thread(target=handle_webhook_async, args=(app, body, signature, merchant.id))
        thread.start()
        
        # 立即回傳 OK 給 LINE
        return 'OK', 200
        
    except Exception as e:
        print(f"Webhook error: {e}")
        return 'OK', 200

@webhook_bp.route('/universal', methods=['POST'])
def universal_webhook():
    """通用 Webhook 端點 (自動根據內容識別商家)"""
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    
    print(f"收到通用 Webhook 請求 - Signature: {signature[:10]}...")
    
    # 這裡可以根據 body 中的內容（例如 LINE User ID 或其他識別碼）來查找商家
    # 目前簡化處理：使用第一個配置了 LINE 的商家
    merchant = Merchant.query.filter(
        Merchant.line_channel_access_token.isnot(None),
        Merchant.line_channel_secret.isnot(None)
    ).first()
    
    if not merchant:
        print("系統中沒有配置任何 LINE Bot 商家")
        return 'No configured merchant found', 404

    print(f"使用通用模式為商家 {merchant.name} 處理 Webhook...")
    try:
        handler = LineBotHandler(merchant)
        handler.handle_webhook(body, signature)
        print(f"通用 Webhook 處理完成")
        return 'OK'
        
        # 處理 webhook 事件
        from ai_modules.line_bot import LineBotHandler
        bot_handler = LineBotHandler(merchant)
        bot_handler.handle_webhook(body, signature)
        
        print(f"Universal webhook processed for merchant {merchant.id}")
        return 'OK', 200
        
    except Exception as e:
        print(f"Universal webhook error: {e}")
        return 'OK', 200
