# AI 模組 - LINE Bot 處理
# 負責：LINE Messaging API 的傳送回覆

try:
    from linebot import LineBotApi, WebhookHandler
    from linebot.exceptions import InvalidSignatureError
    from linebot.models import (
        MessageEvent, TextMessage, PostbackEvent,
        QuickReply, QuickReplyButton, MessageAction, TextSendMessage
    )
except ImportError:
    print("Warning: line-bot-sdk not installed. Please run: pip install line-bot-sdk")
    LineBotApi = None
    WebhookHandler = None
    InvalidSignatureError = None
    MessageEvent = None
    TextMessage = None
    PostbackEvent = None
    QuickReply = None
    QuickReplyButton = None
    MessageAction = None
    TextSendMessage = None

from ai_modules.ai_service import AIService
from shared.database import db
from shared.models import Merchant, Service, Appointment
from datetime import datetime, timedelta
import re

class LineBotHandler:
    """LINE Bot 處理器"""
    
    def __init__(self, merchant: Merchant):
        """初始化 LINE Bot 處理器"""
        if LineBotApi is None:
            raise ImportError("line-bot-sdk is not installed. Please run: pip install line-bot-sdk")
        
        self.merchant = merchant
        self.line_bot_api = LineBotApi(merchant.line_channel_access_token)
        self.handler = WebhookHandler(merchant.line_channel_secret)
        
        # 註冊事件處理器
        self.handler.add(MessageEvent, message=TextMessage)(self.handle_message)
        self.handler.add(PostbackEvent)(self.handle_postback)
        
        # 初始化 AI 服務
        self.ai_service = AIService(merchant.google_gemini_api_key)
    
    def handle_webhook(self, body: str, signature: str):
        """處理 webhook 請求"""
        try:
            if self.handler is None:
                print("LINE Bot SDK not available")
                return
            
            self.handler.handle(body, signature)
        except Exception as e:
            print(f"Webhook handling error: {e}")
    
    def handle_message(self, event: MessageEvent):
        """處理文字訊息"""
        if MessageEvent is None:
            return
            
        user_message = event.message.text
        user_id = event.source.user_id
        
        try:
            # 分析用戶意圖
            intent = self.ai_service.analyze_intent(user_message)
            
            # 根據意圖處理
            if intent['appointment_request']:
                self._handle_appointment_request(user_message, user_id)
            else:
                # 使用 AI 生成回覆
                response = self.ai_service.generate_response(
                    user_message, 
                    self.merchant.name, 
                    self.merchant.ai_tone or "友善專業"
                )
                self._reply_message(event.reply_token, response)
                
        except Exception as e:
            print(f"Message handling error: {e}")
            self._reply_message(event.reply_token, "抱歉，系統發生錯誤，請稍後再試。")
    
    def handle_postback(self, event: PostbackEvent):
        """處理 Postback 事件"""
        if PostbackEvent is None:
            return
            
        user_id = event.source.user_id
        data = event.postback.data
        
        try:
            if data.startswith('service_'):
                # 處理服務選擇
                service_id = data.replace('service_', '')
                self._handle_service_selection(user_id, service_id)
            elif data.startswith('book_'):
                # 處理預約確認
                self._handle_booking_confirmation(user_id, data)
            else:
                # 其他 Postback 處理
                self._reply_message(event.reply_token, "感謝您的操作！")
                
        except Exception as e:
            print(f"Postback handling error: {e}")
            self._reply_message(event.reply_token, "抱歉，系統發生錯誤，請稍後再試。")
    
    def _handle_appointment_request(self, user_message: str, user_id: str):
        """處理預約請求"""
        try:
            # 獲取服務列表
            services = Service.query.filter_by(merchant_id=self.merchant.id).all()
            
            if not services:
                self._reply_message(user_id, "目前沒有可預約的服務項目。")
                return
            
            # 生成服務選單
            service_items = []
            for service in services:
                service_items.append(
                    QuickReplyButton(
                        action=MessageAction(
                            label=f"{service.name} ({service.duration}分鐘, ${service.price})",
                            text=f"我想預約{service.name}"
                        )
                    )
                )
            
            # 發送服務選單
            quick_reply = QuickReply(items=service_items)
            self._reply_message(
                user_id, 
                "請選擇您想預約的服務項目：",
                quick_reply=quick_reply
            )
            
        except Exception as e:
            print(f"Appointment request handling error: {e}")
            self._reply_message(user_id, "抱歉，無法處理預約請求，請稍後再試。")
    
    def _handle_service_selection(self, user_id: str, service_name: str):
        """處理服務選擇"""
        try:
            # 查找對應的服務
            service = Service.query.filter_by(
                merchant_id=self.merchant.id, 
                name=service_name
            ).first()
            
            if not service:
                self._reply_message(user_id, "找不到指定的服務項目。")
                return
            
            # 詢問預約時間
            message = f"""
您選擇了 {service.name} ({service.duration}分鐘, ${service.price})

請告訴我您希望的預約日期和時間，例如：
- 明天下午 3 點
- 2024/12/25 14:00
- 這週六早上 10 點
"""
            
            self._reply_message(user_id, message)
            
        except Exception as e:
            print(f"Service selection handling error: {e}")
            self._reply_message(user_id, "抱歉，無法處理服務選擇，請稍後再試。")
    
    def _handle_booking_confirmation(self, user_id: str, data: str):
        """處理預約確認"""
        try:
            # 解析預約資訊
            booking_info = self._parse_booking_data(data)
            
            # 創建預約記錄
            appointment = Appointment(
                merchant_id=self.merchant.id,
                customer_name=booking_info.get('name', 'LINE用戶'),
                customer_phone=booking_info.get('phone', ''),
                service_id=booking_info.get('service_id'),
                appointment_time=booking_info.get('time'),
                notes=booking_info.get('notes', ''),
                status='pending'
            )
            
            db.session.add(appointment)
            db.session.commit()
            
            # 發送確認訊息
            confirmation_message = f"""
預約成功！🎉

服務：{booking_info.get('service_name', '未知服務')}
時間：{booking_info.get('time_str', '未知時間')}
狀態：待確認

我們會盡快確認您的預約，如有需要會與您聯絡。
"""
            
            self._reply_message(user_id, confirmation_message)
            
        except Exception as e:
            print(f"Booking confirmation handling error: {e}")
            self._reply_message(user_id, "抱歉，無法確認預約，請稍後再試。")
    
    def _parse_booking_data(self, data: str) -> dict:
        """解析預約資料"""
        # 簡化的資料解析
        return {
            'name': 'LINE用戶',
            'phone': '',
            'service_id': None,
            'service_name': '未知服務',
            'time': datetime.now() + timedelta(days=1),
            'time_str': '明天',
            'notes': ''
        }
    
    def _reply_message(self, reply_token: str, message: str, quick_reply=None):
        """回覆訊息"""
        try:
            if TextSendMessage is None:
                print("LINE Bot SDK not available for sending messages")
                return
                
            text_message = TextSendMessage(text=message)
            
            if quick_reply:
                text_message.quick_reply = quick_reply
            
            self.line_bot_api.reply_message(reply_token, text_message)
            
        except Exception as e:
            print(f"Reply message error: {e}")
    
    def _push_message(self, to: str, message: str):
        """推送訊息"""
        try:
            if TextSendMessage is None:
                print("LINE Bot SDK not available for pushing messages")
                return
                
            text_message = TextSendMessage(text=message)
            self.line_bot_api.push_message(to, text_message)
            
        except Exception as e:
            print(f"Push message error: {e}")
