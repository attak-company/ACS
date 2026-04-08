# AI 模組 - AI 服務
# 負責：串接 Gemini AI、處理 Prompt

try:
    import google.generativeai as genai
except ImportError:
    print("Warning: google-generativeai not installed. Please run: pip install google-generativeai")
    genai = None

from typing import Optional
import re
import os

class AIService:
    """AI 服務類別"""
    
    def __init__(self, api_key: str = None):
        """Initialize AI service"""
        if genai is None:
            raise ImportError("google-generativeai is not installed. Please run: pip install google-generativeai")
        
        # Use provided API key or fallback to environment variable
        self.api_key = api_key or os.getenv('GOOGLE_GEMINI_API_KEY')
        
        if not self.api_key:
            print("Warning: No Gemini API key provided. AI responses will use fallback rules only.")
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            # Use available flash version for ultra-fast responses
            self.model = genai.GenerativeModel('models/gemini-2.5-flash')
        else:
            self.model = None
    
    def generate_response(self, prompt: str, merchant_name: str, ai_tone: str = "friendly professional") -> str:
        """Generate AI response"""
        try:
            # Ensure API key is configured
            if not self.api_key or not self.model:
                return self._get_fallback_response(prompt, merchant_name)
                
            # Simplify prompt and limit output length for minimal thinking time
            full_prompt = f"You are {merchant_name} customer service, reply in {ai_tone} tone: {prompt}"
            
            # Reconfigure with explicit api_key to avoid authentication loss
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('models/gemini-2.5-flash')
            
            response = model.generate_content(
                full_prompt,
                generation_config={
                    "temperature": 0.4,
                    "top_p": 1,
                    "top_k": 32,
                    "max_output_tokens": 100,
                }
            )
            return response.text.strip()
        except Exception as e:
            print(f"DEBUG SPEED: AI generation error: {e}")
            return self._get_fallback_response(prompt, merchant_name)
    
    def _get_fallback_response(self, user_message: str, merchant_name: str) -> str:
        """預設回覆規則"""
        user_message_lower = user_message.lower()
        
        # 問候語
        greetings = ['你好', '您好', 'hi', 'hello']
        if any(greeting in user_message_lower for greeting in greetings):
            return f"你好！歡迎來到{merchant_name}，我是AI客服助手。有什麼可以幫助您的嗎？"
        
        # 服務查詢
        if '服務' in user_message or '項目' in user_message:
            return f"感謝您對{merchant_name}的興趣！我們提供多種專業服務，請告訴我您需要的具體服務，我會為您提供詳細資訊。"
        
        # 營業時間
        if '營業時間' in user_message or '開門時間' in user_message:
            return f"關於{merchant_name}的營業時間，請查看我們的官方資訊或直接致電詢問。"
        
        # 預約相關
        appointment_keywords = ['預約', '約', '訂位', '預定']
        if any(keyword in user_message for keyword in appointment_keywords):
            return f"好的！我可以幫您預約{merchant_name}的服務。請告訴我您想要的服務項目和希望的時間。"
        
        # 價格查詢
        if '價格' in user_message or '多少錢' in user_message or '費用' in user_message:
            return f"關於{merchant_name}的服務價格，請告訴我您感興趣的具體服務項目，我會為您提供詳細的價格資訊。"
        
        # 預設回覆
        return f"感謝您的來信！我是{merchant_name}的AI客服助手。有什麼可以幫助您的嗎？您可以詢問營業時間、服務項目或直接預約。"
    
    def analyze_intent(self, message: str) -> dict:
        """優化意圖分析：優先使用關鍵字匹配，完全移除 AI 呼叫以達成秒回"""
        message_lower = message.lower()
        
        intent = {
            'greeting': False,
            'appointment_request': False,
            'service_inquiry': False,
            'price_inquiry': False,
            'hours_inquiry': False,
            'contact_info': False
        }
        
        # 預約請求 (最優先判定)
        appointment_keywords = ['預約', '約', '訂位', '預定', '想約', '有空嗎', 'booking', 'appointment']
        if any(keyword in message_lower for keyword in appointment_keywords):
            intent['appointment_request'] = True
            return intent
            
        # 營業時間查詢
        hours_keywords = ['營業時間', '幾點', '開門', '關門', '營業', 'hours', 'open', 'close']
        if any(keyword in message_lower for keyword in hours_keywords):
            intent['hours_inquiry'] = True
            return intent

        # 價格查詢
        price_keywords = ['價格', '多少錢', '費用', '價錢', 'price', 'cost', '錢']
        if any(keyword in message_lower for keyword in price_keywords):
            intent['price_inquiry'] = True
            return intent
            
        # 服務查詢
        service_keywords = ['服務', '項目', 'service', 'treatment', '內容']
        if any(keyword in message_lower for keyword in service_keywords):
            intent['service_inquiry'] = True
            return intent
            
        # 聯絡資訊
        contact_keywords = ['電話', '地址', '位置', '聯絡', 'phone', 'address', 'location', '在哪']
        if any(keyword in message_lower for keyword in contact_keywords):
            intent['contact_info'] = True
            return intent

        # 問候語
        greetings = ['你好', '您好', 'hi', 'hello', '哈囉', '有人嗎']
        intent['greeting'] = any(greeting in message_lower for greeting in greetings)
        
        return intent
    
    def extract_appointment_info(self, message: str) -> dict:
        """提取預約資訊"""
        appointment_info = {
            'service': None,
            'date': None,
            'time': None,
            'name': None,
            'phone': None
        }
        
        # 提取服務項目（簡化版本）
        services = ['剪髮', '染髮', '燙髮', '護髮', '造型', '洗髮']
        for service in services:
            if service in message:
                appointment_info['service'] = service
                break
        
        # 提取時間資訊（簡化版本）
        time_patterns = [
            r'(\d{1,2})[點時](\d{1,2})?[分鐘]?',  # 點時分
            r'(\d{1,2})[：:](\d{1,2})',  # 冒號分隔
            r'上午|下午|早上|晚上',  # 時段
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, message)
            if match:
                appointment_info['time'] = match.group()
                break
        
        return appointment_info
