from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage
import google.generativeai as genai
import os
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/line_ai_appointment')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Conversation memory storage
conversation_history = {}  # user_id -> list of messages

# User session management
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with merchant
    merchant = db.relationship('Merchant', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Merchant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    line_channel_access_token = db.Column(db.String(200))
    line_channel_secret = db.Column(db.String(200))
    ai_tone = db.Column(db.Text, default='friendly')
    arrival_info = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer, nullable=False)  # minutes
    price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Schedule(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.String(5), nullable=False)  # HH:MM
    end_time = db.Column(db.String(5), nullable=False)    # HH:MM
    is_available = db.Column(db.Boolean, default=True)
    schedule_type = db.Column(db.String(20), default='regular')  # regular, break, special

class SpecialSchedule(db.Model):
    """特殊營業時間（臨時調休、節假日等）"""
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)  # 特定日期
    is_closed = db.Column(db.Boolean, default=False)  # 是否休息
    open_time = db.Column(db.String(5))  # HH:MM，特殊開店時間
    close_time = db.Column(db.String(5))  # HH:MM，特殊關店時間
    reason = db.Column(db.String(200))  # 調休原因
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id'), nullable=False)
    customer_name = db.Column(db.String(100))
    customer_phone = db.Column(db.String(20))
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.String(5), nullable=False)  # HH:MM
    status = db.Column(db.String(20), default='confirmed')
    line_user_id = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    service = db.relationship('Service', backref='appointments')

class BlockedTime(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchant.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    start_time = db.Column(db.String(5), nullable=False)
    end_time = db.Column(db.String(5), nullable=False)
    reason = db.Column(db.String(200))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('merchant_dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('merchant_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('登入成功！', 'success')
            return redirect(url_for('merchant_dashboard'))
        else:
            flash('使用者名稱或密碼錯誤', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('merchant_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 驗證
        if password != confirm_password:
            flash('密碼不匹配', 'error')
            return render_template('login.html')
        
        if User.query.filter_by(username=username).first():
            flash('使用者名稱已存在', 'error')
            return render_template('login.html')
        
        if User.query.filter_by(email=email).first():
            flash('電子郵件已存在', 'error')
            return render_template('login.html')
        
        # 創建用戶
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # 創建對應的商家記錄
        merchant = Merchant(
            user_id=user.id,
            name='新店家',
            phone='',
            address='',
            description='',
            arrival_info='',
            ai_tone='friendly'
        )
        db.session.add(merchant)
        db.session.commit()
        
        flash('註冊成功！請登入', 'success')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已成功登出', 'info')
    return redirect(url_for('login'))

@app.route('/merchant')
@login_required
def merchant_dashboard():
    return render_template('merchant.html')

@app.route('/api/merchant', methods=['GET', 'POST'])
@login_required
def api_merchant():
    if request.method == 'POST':
        data = request.json
        merchant = Merchant.query.filter_by(user_id=current_user.id).first()
        if not merchant:
            merchant = Merchant(user_id=current_user.id, name='新店家')
            db.session.add(merchant)
        
        merchant.name = data.get('name', merchant.name)
        merchant.description = data.get('description', merchant.description)
        merchant.address = data.get('address', merchant.address)
        merchant.phone = data.get('phone', merchant.phone)
        merchant.arrival_info = data.get('arrival_info', merchant.arrival_info)
        merchant.ai_tone = data.get('ai_tone', merchant.ai_tone)
        merchant.line_channel_access_token = data.get('line_channel_access_token', merchant.line_channel_access_token)
        merchant.line_channel_secret = data.get('line_channel_secret', merchant.line_channel_secret)
        
        db.session.commit()
        return jsonify({'success': True})
    
    merchant = Merchant.query.filter_by(user_id=current_user.id).first()
    if not merchant:
        merchant = Merchant(user_id=current_user.id, name='新店家')
        db.session.add(merchant)
        db.session.commit()
    
    return jsonify({
        'name': merchant.name,
        'description': merchant.description,
        'address': merchant.address,
        'phone': merchant.phone,
        'arrival_info': merchant.arrival_info,
        'ai_tone': merchant.ai_tone,
        'line_channel_access_token': merchant.line_channel_access_token,
        'line_channel_secret': merchant.line_channel_secret
    })

@app.route('/webhook/<int:merchant_id>', methods=['POST'])
def merchant_webhook(merchant_id):
    """特定商家的 Webhook 端點"""
    merchant = Merchant.query.filter_by(id=merchant_id).first()
    
    if not merchant or not merchant.line_channel_secret:
        print(f"No merchant {merchant_id} or LINE secret configured")
        return 'OK', 200
    
    line_bot_api = LineBotApi(merchant.line_channel_access_token)
    handler = WebhookHandler(merchant.line_channel_secret)
    
    body = request.get_data(as_text=True)
    signature = request.headers['X-Line-Signature']
    
    print(f"Webhook received for merchant {merchant_id}: {body}")  # Debug log
    
    @handler.add(MessageEvent, message=TextMessage)
    def handle_message(event):
        try:
            user_message = event.message.text
            user_id = event.source.user_id
            
            # Initialize conversation history
            if user_id not in conversation_history:
                conversation_history[user_id] = []
            
            # Add user message to history
            conversation_history[user_id].append({
                'role': 'user',
                'content': user_message,
                'timestamp': datetime.now().isoformat()
            })
            
            # Keep only last 10 messages
            if len(conversation_history[user_id]) > 10:
                conversation_history[user_id] = conversation_history[user_id][-10:]
            
            # Initialize AI
            genai.configure(api_key=os.getenv('GOOGLE_GEMINI_API_KEY'))
            model = genai.GenerativeModel('gemini-1.5-flash-exp-0827')
            
            # Get merchant info
            services = Service.query.filter_by(merchant_id=merchant.id).all()
            services_text = '\n'.join([f"- {s.name} ({s.duration}分鐘, ${s.price})" for s in services])
            
            # Build conversation history
            history_text = ""
            if len(conversation_history[user_id]) > 1:
                history_text = "\n\n對話歷史：\n"
                for msg in conversation_history[user_id][-5:]:
                    if msg['role'] == 'user':
                        history_text += f"用戶：{msg['content']}\n"
                    else:
                        history_text += f"助手：{msg['content']}\n"
            
            # Build prompt
            prompt = f"""
            你是{merchant.name}的AI客服助手。請用{merchant.ai_tone}的語氣回覆。
            
            店家服務項目：
            {services_text}
            
            到店須知：
            {merchant.arrival_info or '無特別須知'}
            
            {history_text}
            
            當前用戶訊息：{user_message}
            
            請用繁體中文回覆，語氣要友善自然。
            """
            
            try:
                response = model.generate_content(prompt)
                reply_text = response.text
                
                # Add AI reply to conversation history
                conversation_history[user_id].append({
                    'role': 'assistant',
                    'content': reply_text,
                    'timestamp': datetime.now().isoformat()
                })
                
                # Check for appointment request
                appointment_keywords = ['預約', '約', '訂位', '預訂']
                if any(keyword in user_message for keyword in appointment_keywords):
                    handle_appointment_request(user_message, user_id, merchant, services)
                
                # Send reply
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
                
            except Exception as ai_error:
                print(f"AI error: {ai_error}")
                # Fallback to rule-based replies
                reply_text = get_fallback_reply(user_message, merchant)
                
                # Add fallback reply to conversation history
                conversation_history[user_id].append({
                    'role': 'assistant',
                    'content': reply_text,
                    'timestamp': datetime.now().isoformat()
                })
                
                line_bot_api.reply_message(
                    event.reply_token,
                    TextSendMessage(text=reply_text)
                )
                
        except Exception as e:
            print(f"Error handling message: {e}")
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage(text="抱歉，系統暫時出現問題，請稍後再試。")
            )
    
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print("Invalid signature")
        return 'Invalid signature', 400
    except Exception as e:
        print(f"Webhook error: {e}")
        return 'OK', 200
    
    return 'OK', 200

@app.route('/webhook', methods=['POST'])
def webhook():
    # 向後兼容的通用 webhook
    merchant = Merchant.query.filter(
        Merchant.line_channel_access_token.isnot(None),
        Merchant.line_channel_secret.isnot(None)
    ).first()
    
    if not merchant:
        print("No merchant with LINE configuration found")
        return 'OK', 200
    
    # 重定向到特定商家的 webhook
    return merchant_webhook(merchant.id)

def handle_appointment_request(user_message, user_id, merchant, services):
    """處理預約請求"""
    try:
        print(f"Processing appointment request: {user_message}")
        # 實現預約邏輯...
    except Exception as e:
        print(f"Error processing appointment: {e}")

def get_fallback_reply(user_message, merchant):
    """預設回覆規則"""
    user_message_lower = user_message.lower()
    
    # 問候語
    greetings = ['你好', '您好', 'hi', 'hello', '嗨']
    if any(greeting in user_message_lower for greeting in greetings):
        return f"你好！歡迎來到{merchant.name}，我是AI客服助手。有什麼可以幫助您的嗎？"
    
    # 營業時間查詢
    if '營業時間' in user_message or '開門時間' in user_message or '營業' in user_message:
        return "我們的營業時間請參考店家資訊，或直接詢問特定日期的營業時間。"
    
    # 服務項目查詢
    if '服務' in user_message or '項目' in user_message:
        services = Service.query.filter_by(merchant_id=merchant.id).all()
        if services:
            service_list = '\n'.join([f"• {s.name} ({s.duration}分鐘, ${s.price})" for s in services])
            return f"我們的服務項目：\n{service_list}\n\n請問您想預約哪個服務呢？"
        else:
            return "目前還沒有設定服務項目，請稍後再試。"
    
    # 預約相關
    if '預約' in user_message or '約' in user_message:
        return "好的，我來幫您安排預約。請告訴我您想要的服務項目、日期和時間。"
    
    # 預設回覆
    return f"感謝您的來信！我是{merchant.name}的AI客服助手。有什麼可以幫助您的嗎？您可以詢問營業時間、服務項目或直接預約。"

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
