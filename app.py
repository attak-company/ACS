from flask import Flask, render_template, request, jsonify, redirect, url_for, flash

from flask_sqlalchemy import SQLAlchemy

from flask_cors import CORS

from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user

from flask_mail import Mail, Message

from werkzeug.security import generate_password_hash, check_password_hash

from linebot import LineBotApi, WebhookHandler

from linebot.exceptions import InvalidSignatureError

from linebot.models import MessageEvent, TextMessage, TextSendMessage

import google.generativeai as genai

import os

import re

from datetime import datetime, timedelta

import json

import random

import string

from dotenv import load_dotenv



load_dotenv()



app = Flask(__name__)

CORS(app)



app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://username:password@localhost:5432/line_ai_appointment')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False



# Email configuration

app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')

app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '587'))

app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'

app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'attak.company@gmail.com')

app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'zhaagfccyxawzhos')

app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'attak.company@gmail.com')



# Initialize mail

mail = Mail(app)



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



class VerificationCode(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(120), nullable=False)

    code = db.Column(db.String(6), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    expires_at = db.Column(db.DateTime, nullable=False)

    is_used = db.Column(db.Boolean, default=False)

    

    def __init__(self, email, code):

        self.email = email

        self.code = code

        self.expires_at = datetime.utcnow() + timedelta(minutes=10)  # 10分鐘後過期

    

    @staticmethod

    def generate_code():

        """生成6位數驗證碼"""

        return ''.join(random.choices(string.digits, k=6))

    

    @staticmethod

    def is_valid(email, code):

        """檢查驗證碼是否有效"""

        verification = VerificationCode.query.filter_by(

            email=email, 

            code=code, 

            is_used=False

        ).first()

        

        if verification and verification.expires_at > datetime.utcnow():

            return verification

        return None



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

    return render_template('landing.html')


@app.route('/test-forgot-password')
def test_forgot_password():
    """忘記密碼測試頁面"""
    return render_template('test_forgot_password.html')


@app.route('/test-login')
def test_login():
    """登入測試頁面"""
    return render_template('test_login.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('merchant_dashboard'))
    
    if request.method == 'POST':
        username_or_email = request.form.get('username')
        password = request.form.get('password')
        
        # 調試信息
        print(f"DEBUG: 嘗試登入 - 用戶名/郵件: {username_or_email}")
        
        # 嘗試用用戶名查找
        user = User.query.filter_by(username=username_or_email).first()
        
        # 如果用如果用戶名找不到，嘗試用郵件查找
        if not user:
            user = User.query.filter_by(email=username_or_email).first()
        
        if user:
            print(f"DEBUG: 找到用戶 - ID: {user.id}, 用戶名: {user.username}, 郵件: {user.email}")
            if user.check_password(password):
                print(f"DEBUG: 密碼驗證成功")
                login_user(user)
                flash('登入成功！', 'success')
                return redirect(url_for('merchant_dashboard'))
            else:
                print(f"DEBUG: 密碼驗證失敗")
                flash('密碼錯誤，請檢查您的密碼。', 'error')
        else:
            print(f"DEBUG: 找不到用戶")
            flash('找不到該用戶名或郵件，請檢查您的輸入。', 'error')
    
    return render_template('login_unified.html')


@app.route('/pricing')
def pricing():

    return render_template('pricing.html')



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

            return render_template('login_unified.html')

        

        if User.query.filter_by(username=username).first():

            flash('使用者名稱已存在', 'error')

            return render_template('login_unified.html')

        

        if User.query.filter_by(email=email).first():

            flash('電子郵件已存在', 'error')

            return render_template('login_unified.html')

        

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

    

    return render_template('login_unified.html')



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



# 服務項目管理路由

@app.route('/services')

@login_required

def services_page():

    """服務項目管理頁面"""

    # 獲取當前用戶的商家

    merchant = Merchant.query.filter_by(user_id=current_user.id).first()

    if not merchant:

        flash('請先設定店家資訊', 'warning')

        return redirect(url_for('merchant_dashboard'))

    

    # 獲取該商家的所有服務項目

    services = Service.query.filter_by(merchant_id=merchant.id).all()

    return render_template('services.html', services=services)



@app.route('/api/services', methods=['GET', 'POST'])

@login_required

def api_services():

    """服務項目 API"""

    # 獲取當前用戶的商家

    merchant = Merchant.query.filter_by(user_id=current_user.id).first()

    if not merchant:

        return jsonify({'error': '請先設定店家資訊'}), 400

    

    if request.method == 'GET':

        # 獲取所有服務項目

        services = Service.query.filter_by(merchant_id=merchant.id).all()

        return jsonify([{

            'id': s.id,

            'name': s.name,

            'description': s.description,

            'duration': s.duration,

            'price': s.price,

            'merchant_id': s.merchant_id

        } for s in services])

    

    elif request.method == 'POST':

        # 新增服務項目

        try:

            data = request.get_json()

            

            # 驗證必填欄位

            if not data.get('name') or not data.get('duration') or not data.get('price'):

                return jsonify({'error': '請填寫所有必填欄位'}), 400

            

            # 創建新服務

            service = Service(

                merchant_id=merchant.id,

                name=data['name'],

                description=data.get('description', ''),

                duration=data['duration'],

                price=data['price']

            )

            

            db.session.add(service)

            db.session.commit()

            

            return jsonify({

                'message': '服務項目創建成功',

                'service': {

                    'id': service.id,

                    'name': service.name,

                    'description': service.description,

                    'duration': service.duration,

                    'price': service.price

                }

            }), 201

            

        except Exception as e:

            db.session.rollback()

            return jsonify({'error': f'創建失敗: {str(e)}'}), 500



@app.route('/api/services/<int:service_id>', methods=['GET', 'PUT', 'DELETE'])

@login_required

def api_service_detail(service_id):

    """單個服務項目 API"""

    # 獲取當前用戶的商家

    merchant = Merchant.query.filter_by(user_id=current_user.id).first()

    if not merchant:

        return jsonify({'error': '請先設定店家資訊'}), 400

    

    # 查找服務項目

    service = Service.query.filter_by(id=service_id, merchant_id=merchant.id).first()

    if not service:

        return jsonify({'error': '服務項目不存在'}), 404

    

    if request.method == 'GET':

        # 獲取單個服務項目

        return jsonify({

            'id': service.id,

            'name': service.name,

            'description': service.description,

            'duration': service.duration,

            'price': service.price,

            'merchant_id': service.merchant_id

        })

    

    elif request.method == 'PUT':

        # 更新服務項目

        try:

            data = request.get_json()

            

            # 更新欄位

            if 'name' in data:

                service.name = data['name']

            if 'description' in data:

                service.description = data['description']

            if 'duration' in data:

                service.duration = data['duration']

            if 'price' in data:

                service.price = data['price']

            

            db.session.commit()

            

            return jsonify({

                'message': '服務項目更新成功',

                'service': {

                    'id': service.id,

                    'name': service.name,

                    'description': service.description,

                    'duration': service.duration,

                    'price': service.price

                }

            })

            

        except Exception as e:

            db.session.rollback()

            return jsonify({'error': f'更新失敗: {str(e)}'}), 500

    

    elif request.method == 'DELETE':

        # 刪除服務項目

        try:

            # 檢查是否有相關的預約

            appointments = Appointment.query.filter_by(service_id=service_id).first()

            if appointments:

                return jsonify({'error': '無法刪除，該服務項目已有相關預約'}), 400

            

            db.session.delete(service)

            db.session.commit()

            

            return jsonify({'message': '服務項目刪除成功'})

            

        except Exception as e:

            db.session.rollback()

            return jsonify({'error': f'刪除失敗: {str(e)}'}), 500



# 預約管理路由

@app.route('/api/appointments', methods=['GET', 'POST', 'PUT', 'DELETE'])

@login_required

def api_appointments():

    """預約管理 API"""

    # 獲取當前用戶的商家

    merchant = Merchant.query.filter_by(user_id=current_user.id).first()

    if not merchant:

        return jsonify({'error': '請先設定店家資訊'}), 400

    

    if request.method == 'GET':

        # 獲取所有預約

        appointments = Appointment.query.filter_by(merchant_id=merchant.id).all()

        return jsonify([{

            'id': a.id,

            'customer_name': a.customer_name,

            'customer_phone': a.customer_phone,

            'service_id': a.service_id,

            'service_name': a.service.name if a.service else None,

            'date': a.date.isoformat() if a.date else None,

            'time': a.time,

            'status': a.status,

            'line_user_id': a.line_user_id,

            'created_at': a.created_at.isoformat() if a.created_at else None

        } for a in appointments])

    

    elif request.method == 'POST':

        # 新增預約

        try:

            data = request.get_json()

            

            # 驗證必填欄位

            if not data.get('customer_name') or not data.get('date') or not data.get('time'):

                return jsonify({'error': '請填寫所有必填欄位'}), 400

            

            appointment = Appointment(

                merchant_id=merchant.id,

                customer_name=data['customer_name'],

                customer_phone=data.get('customer_phone', ''),

                service_id=data.get('service_id'),

                date=datetime.strptime(data['date'], '%Y-%m-%d').date(),

                time=data['time'],

                status=data.get('status', 'confirmed'),

                line_user_id=data.get('line_user_id')

            )

            

            db.session.add(appointment)

            db.session.commit()

            

            return jsonify({

                'message': '預約創建成功',

                'appointment': {

                    'id': appointment.id,

                    'customer_name': appointment.customer_name,

                    'customer_phone': appointment.customer_phone,

                    'service_id': appointment.service_id,

                    'service_name': appointment.service.name if appointment.service else None,

                    'date': appointment.date.isoformat(),

                    'time': appointment.time,

                    'status': appointment.status,

                    'line_user_id': appointment.line_user_id

                }

            }), 201

            

        except Exception as e:

            db.session.rollback()

            return jsonify({'error': f'創建失敗: {str(e)}'}), 500

    

    elif request.method == 'PUT':

        # 更新預約

        try:

            data = request.get_json()

            appointment_id = data.get('id')

            

            appointment = Appointment.query.filter_by(

                id=appointment_id, 

                merchant_id=merchant.id

            ).first()

            

            if not appointment:

                return jsonify({'error': '預約不存在'}), 404

            

            # 更新欄位

            if 'customer_name' in data:

                appointment.customer_name = data['customer_name']

            if 'customer_phone' in data:

                appointment.customer_phone = data['customer_phone']

            if 'service_id' in data:

                appointment.service_id = data['service_id']

            if 'date' in data:

                appointment.date = datetime.strptime(data['date'], '%Y-%m-%d').date()

            if 'time' in data:

                appointment.time = data['time']

            if 'status' in data:

                appointment.status = data['status']

            if 'line_user_id' in data:

                appointment.line_user_id = data['line_user_id']

            

            db.session.commit()

            

            return jsonify({

                'message': '預約更新成功',

                'appointment': {

                    'id': appointment.id,

                    'customer_name': appointment.customer_name,

                    'customer_phone': appointment.customer_phone,

                    'service_id': appointment.service_id,

                    'service_name': appointment.service.name if appointment.service else None,

                    'date': appointment.date.isoformat(),

                    'time': appointment.time,

                    'status': appointment.status,

                    'line_user_id': appointment.line_user_id

                }

            })

            

        except Exception as e:

            db.session.rollback()

            return jsonify({'error': f'更新失敗: {str(e)}'}), 500

    

    elif request.method == 'DELETE':

        # 刪除預約

        try:

            appointment_id = request.args.get('id')

            

            appointment = Appointment.query.filter_by(

                id=appointment_id, 

                merchant_id=merchant.id

            ).first()

            

            if not appointment:

                return jsonify({'error': '預約不存在'}), 404

            

            db.session.delete(appointment)

            db.session.commit()

            

            return jsonify({'message': '預約刪除成功'})

            

        except Exception as e:

            db.session.rollback()

            return jsonify({'error': f'刪除失敗: {str(e)}'}), 500



# 用戶設定管理路由

@app.route('/api/user/profile', methods=['GET', 'PUT'])

@login_required

def api_user_profile():

    """用戶資料管理 API"""

    if request.method == 'GET':

        # 獲取用戶資料

        return jsonify({

            'username': current_user.username,

            'email': current_user.email,

            'created_at': current_user.created_at.isoformat() if current_user.created_at else None

        })

    

    elif request.method == 'PUT':

        # 更新用戶資料

        try:

            data = request.get_json()

            

            # 驗證必填欄位

            if not data.get('username') or not data.get('email'):

                return jsonify({'error': '用戶名和電子郵件為必填欄位'}), 400

            

            # 檢查用戶名是否已被使用

            if data['username'] != current_user.username:

                existing_user = User.query.filter(

                    User.username == data['username'],

                    User.id != current_user.id

                ).first()

                if existing_user:

                    return jsonify({'error': '用戶名已被使用'}), 400

            

            # 檢查電子郵件是否已被使用

            if data['email'] != current_user.email:

                existing_user = User.query.filter(

                    User.email == data['email'],

                    User.id != current_user.id

                ).first()

                if existing_user:

                    return jsonify({'error': '電子郵件已被使用'}), 400

            

            # 更新用戶資料

            current_user.username = data['username']

            current_user.email = data['email']

            

            db.session.commit()

            

            return jsonify({

                'message': '用戶資料更新成功',

                'user': {

                    'username': current_user.username,

                    'email': current_user.email

                }

            })

            

        except Exception as e:

            db.session.rollback()

            return jsonify({'error': f'更新失敗: {str(e)}'}), 500



@app.route('/api/send-verification-code', methods=['POST'])
def api_send_verification_code():

    """發送驗證碼 API"""

    try:

        data = request.get_json()

        email = data.get('email')

        

        if not email:

            return jsonify({'error': '電子郵件為必填'}), 400

        

        # 檢查電子郵件是否存在

        user = User.query.filter_by(email=email).first()

        if not user:

            return jsonify({'error': '此電子郵件未註冊'}), 404

        

        # 生成驗證碼

        code = VerificationCode.generate_code()

        

        # 將舊的驗證碼標記為已使用

        old_codes = VerificationCode.query.filter_by(email=email, is_used=False).all()

        for old_code in old_codes:

            old_code.is_used = True

        

        # 創建新的驗證碼

        verification = VerificationCode(email=email, code=code)

        db.session.add(verification)

        db.session.commit()

        

        # 嘗試發送郵件

        try:

            msg = Message(

                subject='數位店長 - 密碼修改驗證碼',

                recipients=[email],

                html=f'''

                <html>

                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">

                    <div style="background-color: #f8f9fa; padding: 30px; border-radius: 10px; text-align: center;">

                        <h2 style="color: #333; margin-bottom: 20px;">數位店長 - 密碼修改驗證碼</h2>

                        <p style="color: #666; font-size: 16px; margin-bottom: 30px;">您正在申請修改密碼，請使用以下驗證碼：</p>

                        <div style="background-color: #007bff; color: white; font-size: 32px; font-weight: bold; padding: 20px; border-radius: 8px; margin: 20px 0; letter-spacing: 5px;">

                            {code}

                        </div>

                        <p style="color: #666; font-size: 14px; margin-bottom: 20px;">驗證碼有效期限為 10 分鐘</p>

                        <p style="color: #999; font-size: 12px;">如果這不是您本人的操作，請忽略此郵件。</p>

                    </div>

                </body>

                </html>

                '''

            )

            mail.send(msg)

            print(f"驗證碼已發送到 {email}: {code}")

            

            return jsonify({

                'success': True,

                'message': '驗證碼已發送至您的電子郵件'

            })

            

        except Exception as mail_error:

            print(f"郵件發送失敗: {mail_error}")

            # 如果郵件發送失敗，仍然返回成功，但在控制台顯示驗證碼

            return jsonify({

                'success': True,

                'message': '驗證碼已生成（郵件發送失敗，請查看控制台）'

            })

        

    except Exception as e:

        db.session.rollback()

        print(f"發送驗證碼錯誤: {e}")

        return jsonify({'error': f'發送失敗: {str(e)}'}), 500



@app.route('/api/change-password-with-code', methods=['POST'])
def api_change_password_with_code():

    """使用驗證碼修改密碼 API"""

    try:

        data = request.get_json()

        

        # 驗證必填欄位

        if not data.get('email') or not data.get('new_password') or not data.get('verification_code'):

            return jsonify({'error': '所有欄位為必填'}), 400

        

        email = data['email']

        new_password = data['new_password']

        verification_code = data['verification_code']

        

        # 驗證驗證碼

        verification = VerificationCode.is_valid(email, verification_code)

        if not verification:

            return jsonify({'error': '驗證碼無效或已過期'}), 400

        

        # 獲取用戶

        user = User.query.filter_by(email=email).first()

        if not user:

            return jsonify({'error': '電子郵件未註冊'}), 404

        

        # 驗證新密碼長度

        if len(new_password) < 8:

            return jsonify({'error': '新密碼至少需要8個字元'}), 400

        

        # 標記驗證碼為已使用

        verification.is_used = True

        

        # 更新密碼

        user.set_password(new_password)

        db.session.commit()

        

        return jsonify({

            'success': True,

            'message': '密碼修改成功'

        })

        

    except Exception as e:

        db.session.rollback()

        print(f"使用驗證碼修改密碼錯誤: {e}")

        return jsonify({'error': f'修改失敗: {str(e)}'}), 500



@app.route('/api/user/change-password', methods=['POST'])

@login_required

def api_change_password():

    """修改密碼 API"""

    try:

        data = request.get_json()

        

        # 驗證必填欄位

        if not data.get('current_password') or not data.get('new_password') or not data.get('confirm_password'):

            return jsonify({'error': '所有欄位為必填'}), 400

        

        current_password = data['current_password']

        new_password = data['new_password']

        confirm_password = data['confirm_password']

        

        # 驗證舊密碼

        if not current_user.check_password(current_password):

            return jsonify({'error': '舊密碼不正確'}), 400

        

        # 驗證新密碼長度

        if len(new_password) < 8:

            return jsonify({'error': '新密碼至少需要8個字元'}), 400

        

        # 驗證密碼強度

        if not re.search(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)', new_password):

            return jsonify({'error': '密碼需要包含大小寫字母和數字'}), 400

        

        # 驗證新密碼確認

        if new_password != confirm_password:

            return jsonify({'error': '新密碼確認不一致'}), 400

        

        # 更新密碼

        current_user.set_password(new_password)

        db.session.commit()

        

        return jsonify({

            'success': True,

            'message': '密碼修改成功'

        })

        

    except Exception as e:

        db.session.rollback()

        print(f"修改密碼錯誤: {e}")

        return jsonify({'error': f'修改失敗: {str(e)}'}), 500



# 營業時間管理路由

@app.route('/api/schedule', methods=['GET', 'POST'])

@login_required

def api_schedule():

    """營業時間 API"""

    try:

        # 獲取當前用戶的商家

        merchant = Merchant.query.filter_by(user_id=current_user.id).first()

        if not merchant:

            return jsonify({'error': '請先設定店家資訊'}), 400

        

        if request.method == 'GET':

            # 獲取所有營業時間

            try:

                schedules = Schedule.query.filter_by(merchant_id=merchant.id).all()

                return jsonify([{

                    'id': s.id,

                    'day_of_week': s.day_of_week,

                    'start_time': s.start_time,

                    'end_time': s.end_time,

                    'is_available': s.is_available,

                    'schedule_type': 'regular'  # 暫時固定值

                } for s in schedules])

            except Exception as e:

                print(f"Error fetching schedules: {e}")

                # 如果沒有營業時間，返回空數組

                return jsonify([])

        

        elif request.method == 'POST':

            # 保存營業時間

            try:

                data = request.get_json()

                print(f"Received schedule data: {data}")  # Debug log

                

                # 檢查數據類型

                if not isinstance(data, list):

                    return jsonify({'error': '數據格式錯誤，需要數組格式'}), 400

                

                # 刪除舊的營業時間

                Schedule.query.filter_by(merchant_id=merchant.id).delete()

                

                # 新增營業時間

                for schedule_item in data:

                    # 驗證必填欄位

                    if not all(key in schedule_item for key in ['day_of_week', 'start_time', 'end_time']):

                        return jsonify({'error': '缺少必填欄位'}), 400

                    

                    schedule = Schedule(

                        merchant_id=merchant.id,

                        day_of_week=schedule_item['day_of_week'],

                        start_time=schedule_item['start_time'],

                        end_time=schedule_item['end_time'],

                        is_available=schedule_item.get('is_available', True)

                    )

                    db.session.add(schedule)

                

                db.session.commit()

                return jsonify({'message': '營業時間更新成功'})

                

            except Exception as e:

                db.session.rollback()

                print(f"Error saving schedule: {e}")  # Debug log

                return jsonify({'error': f'更新失敗: {str(e)}'}), 500

    

    except Exception as e:

        print(f"General error in schedule API: {e}")

        return jsonify({'error': f'系統錯誤: {str(e)}'}), 500



@app.route('/api/special-schedule', methods=['GET', 'POST', 'PUT', 'DELETE'])

@login_required

def api_special_schedule():

    """特殊營業時間 API"""

    # 獲取當前用戶的商家

    merchant = Merchant.query.filter_by(user_id=current_user.id).first()

    if not merchant:

        return jsonify({'error': '請先設定店家資訊'}), 400

    

    if request.method == 'GET':

        # 獲取所有特殊營業時間

        special_schedules = SpecialSchedule.query.filter_by(merchant_id=merchant.id).all()

        return jsonify([{

            'id': s.id,

            'date': s.date.isoformat() if s.date else None,

            'is_closed': s.is_closed,

            'open_time': s.open_time,

            'close_time': s.close_time,

            'reason': s.reason

        } for s in special_schedules])

    

    elif request.method == 'POST':

        # 新增特殊營業時間

        try:

            data = request.get_json()

            

            special_schedule = SpecialSchedule(

                merchant_id=merchant.id,

                date=datetime.strptime(data['date'], '%Y-%m-%d').date(),

                is_closed=data.get('is_closed', False),

                open_time=data.get('open_time'),

                close_time=data.get('close_time'),

                reason=data.get('reason', '')

            )

            

            db.session.add(special_schedule)

            db.session.commit()

            

            return jsonify({

                'message': '特殊營業時間創建成功',

                'special_schedule': {

                    'id': special_schedule.id,

                    'date': special_schedule.date.isoformat(),

                    'is_closed': special_schedule.is_closed,

                    'open_time': special_schedule.open_time,

                    'close_time': special_schedule.close_time,

                    'reason': special_schedule.reason

                }

            }), 201

            

        except Exception as e:

            db.session.rollback()

            return jsonify({'error': f'創建失敗: {str(e)}'}), 500

    

    elif request.method == 'PUT':

        # 更新特殊營業時間

        try:

            data = request.get_json()

            schedule_id = data.get('id')

            

            special_schedule = SpecialSchedule.query.filter_by(

                id=schedule_id, 

                merchant_id=merchant.id

            ).first()

            

            if not special_schedule:

                return jsonify({'error': '特殊營業時間不存在'}), 404

            

            # 更新欄位

            if 'date' in data:

                special_schedule.date = datetime.strptime(data['date'], '%Y-%m-%d').date()

            if 'is_closed' in data:

                special_schedule.is_closed = data['is_closed']

            if 'open_time' in data:

                special_schedule.open_time = data['open_time']

            if 'close_time' in data:

                special_schedule.close_time = data['close_time']

            if 'reason' in data:

                special_schedule.reason = data['reason']

            

            db.session.commit()

            

            return jsonify({

                'message': '特殊營業時間更新成功',

                'special_schedule': {

                    'id': special_schedule.id,

                    'date': special_schedule.date.isoformat(),

                    'is_closed': special_schedule.is_closed,

                    'open_time': special_schedule.open_time,

                    'close_time': special_schedule.close_time,

                    'reason': special_schedule.reason

                }

            })

            

        except Exception as e:

            db.session.rollback()

            return jsonify({'error': f'更新失敗: {str(e)}'}), 500

    

    elif request.method == 'DELETE':

        # 刪除特殊營業時間

        try:

            schedule_id = request.args.get('id')

            

            special_schedule = SpecialSchedule.query.filter_by(

                id=schedule_id, 

                merchant_id=merchant.id

            ).first()

            

            if not special_schedule:

                return jsonify({'error': '特殊營業時間不存在'}), 404

            

            db.session.delete(special_schedule)

            db.session.commit()

            

            return jsonify({'message': '特殊營業時間刪除成功'})

            

        except Exception as e:

            db.session.rollback()

            return jsonify({'error': f'刪除失敗: {str(e)}'}), 500



if __name__ == '__main__':

    with app.app_context():

        db.create_all()

    app.run(host='0.0.0.0', port=5000, debug=True)

