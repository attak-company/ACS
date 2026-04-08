# AI 模組 - Webhook 處理
# 負責：LINE Webhook 的入口

import time
import threading
import json
from urllib.request import Request, urlopen
from urllib.error import URLError
from urllib.parse import urlencode
from flask import Blueprint, request, jsonify, current_app
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from ai_modules.line_bot import LineBotHandler
from ai_modules.ai_service import AIService
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


def _send_instagram_text_reply(access_token: str, recipient_id: str, text: str):
    """透過 Instagram Messaging API 回覆文字訊息"""
    url = f"https://graph.facebook.com/v23.0/me/messages?access_token={access_token}"
    payload = {
        "messaging_type": "RESPONSE",
        "recipient": {"id": recipient_id},
        "message": {"text": text[:1000]}
    }
    data = json.dumps(payload).encode("utf-8")
    req = Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
    with urlopen(req, timeout=10) as resp:
        return resp.read()


@webhook_bp.route('/webhook/instagram/<string:username>', methods=['GET'])
def instagram_webhook_verify(username):
    """Instagram Webhook 驗證端點"""
    mode = request.args.get('hub.mode')
    verify_token = request.args.get('hub.verify_token')
    challenge = request.args.get('hub.challenge')

    user = User.query.filter_by(username=username).first()
    if not user:
        return 'forbidden', 403

    merchant = Merchant.query.filter_by(user_id=user.id).first()
    if not merchant:
        return 'forbidden', 403

    expected_token = merchant.instagram_verify_token
    if mode == 'subscribe' and expected_token and verify_token == expected_token:
        return challenge or 'ok', 200

    return 'forbidden', 403


@webhook_bp.route('/webhook/instagram/<string:username>', methods=['POST'])
def instagram_webhook_message(username):
    """Instagram 訊息 Webhook 入口"""
    try:
        user = User.query.filter_by(username=username).first()
        if not user:
            return 'OK', 200

        merchant = Merchant.query.filter_by(user_id=user.id).first()
        if not merchant:
            return 'OK', 200

        if not merchant.instagram_page_access_token:
            return 'OK', 200

        payload = request.get_json(silent=True) or {}
        entries = payload.get('entry', [])

        for entry in entries:
            for messaging in entry.get('messaging', []):
                sender = messaging.get('sender', {}) or {}
                sender_id = sender.get('id')
                message = messaging.get('message', {}) or {}
                text = message.get('text', '')

                if not sender_id or not text:
                    continue

                ai_service = AIService(merchant.google_gemini_api_key)
                reply_text = ai_service.generate_response(
                    text,
                    merchant.name,
                    merchant.ai_tone or "友善專業"
                )

                try:
                    _send_instagram_text_reply(
                        merchant.instagram_page_access_token,
                        sender_id,
                        reply_text
                    )
                except URLError as e:
                    print(f"Instagram reply network error: {e}")
                except Exception as e:
                    print(f"Instagram reply error: {e}")

        return 'OK', 200
    except Exception as e:
        print(f"Instagram webhook error: {e}")
        return 'OK', 200
