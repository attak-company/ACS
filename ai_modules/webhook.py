# AI 模組 - Webhook 處理
# 負責：LINE Webhook 的入口

from flask import Blueprint, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from ai_modules.line_bot import LineBotHandler
from shared.database import db
from shared.models import Merchant, User

# 創建 Blueprint
webhook_bp = Blueprint('webhook', __name__)

@webhook_bp.route('/webhook/<string:username>', methods=['POST'])
def merchant_webhook(username):
    """特定商家的 Webhook 端點"""
    try:
        # 根據用戶名稱查找對應的商家
        user = User.query.filter_by(username=username).first()
        if not user:
            print(f"No user found for username: {username}")
            return 'OK', 200
        
        merchant = Merchant.query.filter_by(user_id=user.id).first()
        if not merchant or not merchant.line_channel_secret:
            print(f"No merchant {merchant.id} or LINE secret configured for user: {username}")
            return 'OK', 200
        
        # 創建 LINE Bot 處理器
        handler = WebhookHandler(merchant.line_channel_secret)
        
        # 獲取請求內容
        signature = request.headers.get('X-Line-Signature', '')
        body = request.get_data(as_text=True)
        
        # 處理 webhook 事件
        from ai_modules.line_bot import LineBotHandler
        bot_handler = LineBotHandler(merchant)
        bot_handler.handle_webhook(body, signature)
        
        print(f"Webhook processed for user {username}: merchant {merchant.id}")
        return 'OK', 200
        
    except Exception as e:
        print(f"Webhook error for user {username}: {e}")
        return 'OK', 200

@webhook_bp.route('/webhook', methods=['POST'])
def universal_webhook():
    """向後兼容的通用 webhook"""
    try:
        # 查找第一個有 LINE 配置的商家
        merchant = Merchant.query.filter(
            Merchant.line_channel_access_token.isnot(None),
            Merchant.line_channel_secret.isnot(None)
        ).first()
        
        if not merchant:
            print("No merchant with LINE configuration found")
            return 'OK', 200
        
        # 創建 LINE Bot 處理器
        handler = WebhookHandler(merchant.line_channel_secret)
        
        # 獲取請求內容
        signature = request.headers.get('X-Line-Signature', '')
        body = request.get_data(as_text=True)
        
        # 處理 webhook 事件
        from ai_modules.line_bot import LineBotHandler
        bot_handler = LineBotHandler(merchant)
        bot_handler.handle_webhook(body, signature)
        
        print(f"Universal webhook processed for merchant {merchant.id}")
        return 'OK', 200
        
    except Exception as e:
        print(f"Universal webhook error: {e}")
        return 'OK', 200
