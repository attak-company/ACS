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
        'id': merchant.id,
        'name': merchant.name,
        'description': merchant.description,
        'address': merchant.address,
        'phone': merchant.phone,
        'arrival_info': merchant.arrival_info,
        'ai_tone': merchant.ai_tone,
        'line_channel_access_token': merchant.line_channel_access_token,
        'line_channel_secret': merchant.line_channel_secret
    })

@app.route('/api/services', methods=['GET', 'POST'])
@login_required
def api_services():
    """服務項目管理 API - 完全重寫"""
    merchant = Merchant.query.filter_by(user_id=current_user.id).first()
    if not merchant:
        return jsonify({'error': 'Merchant not found'}), 400
    
    if request.method == 'POST':
        try:
            data = request.json
            print(f"Creating new service: {data}")  # Debug
            
            # 驗證必填欄位
            if not data.get('name') or not data.get('duration'):
                return jsonify({'error': '服務名稱和時長為必填項目'}), 400
            
            service = Service(
                merchant_id=merchant.id,
                name=data.get('name', '').strip(),
                description=data.get('description', '').strip(),
                duration=int(data.get('duration', 0)),
                price=float(data.get('price', 0))
            )
            
            db.session.add(service)
            db.session.commit()
            
            print(f"Service created with ID: {service.id}")  # Debug
            return jsonify({
                'success': True, 
                'id': service.id,
                'message': '服務項目已成功新增'
            })
            
        except Exception as e:
            print(f"Error creating service: {e}")  # Debug
            db.session.rollback()
            return jsonify({'error': f'新增服務失敗: {str(e)}'}), 500
    
    # GET 請求 - 獲取所有服務
    try:
        services = Service.query.filter_by(merchant_id=merchant.id).order_by(Service.name).all()
        return jsonify([{
            'id': s.id,
            'name': s.name,
            'description': s.description or '',
            'duration': s.duration,
            'price': s.price
        } for s in services])
    except Exception as e:
        print(f"Error loading services: {e}")  # Debug
        return jsonify({'error': f'載入服務失敗: {str(e)}'}), 500

@app.route('/api/services/<int:service_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_service_detail(service_id):
    """單一服務項目操作 API - 完全重寫"""
    merchant = Merchant.query.filter_by(user_id=current_user.id).first()
    if not merchant:
        return jsonify({'error': 'Merchant not found'}), 400
    
    service = Service.query.filter_by(id=service_id, merchant_id=merchant.id).first()
    if not service:
        print(f"Service {service_id} not found for merchant {merchant.id}")  # Debug
        return jsonify({'error': '服務項目不存在'}), 404
    
    if request.method == 'GET':
        # 獲取單一服務詳情
        return jsonify({
            'id': service.id,
            'name': service.name,
            'description': service.description or '',
            'duration': service.duration,
            'price': service.price
        })
    
    elif request.method == 'PUT':
        try:
            data = request.json
            print(f"Updating service {service_id} with data: {data}")  # Debug
            
            # 驗證必填欄位
            if not data.get('name') or not data.get('duration'):
                return jsonify({'error': '服務名稱和時長為必填項目'}), 400
            
            # 更新服務
            service.name = data.get('name', service.name).strip()
            service.description = data.get('description', service.description).strip()
            service.duration = int(data.get('duration', service.duration))
            service.price = float(data.get('price', service.price))
            
            db.session.commit()
            
            print(f"Service {service_id} updated successfully")  # Debug
            return jsonify({
                'success': True,
                'message': '服務項目已成功更新'
            })
            
        except Exception as e:
            print(f"Error updating service {service_id}: {e}")  # Debug
            db.session.rollback()
            return jsonify({'error': f'更新服務失敗: {str(e)}'}), 500
    
    elif request.method == 'DELETE':
        try:
            print(f"Deleting service {service_id}")  # Debug
            
            # 檢查是否有相關預約
            appointments = Appointment.query.filter_by(service_id=service_id).first()
            if appointments:
                return jsonify({
                    'error': '無法刪除已有預約的服務項目',
                    'code': 'HAS_APPOINTMENTS'
                }), 400
            
            # 刪除服務
            db.session.delete(service)
            db.session.commit()
            
            print(f"Service {service_id} deleted successfully")  # Debug
            return jsonify({
                'success': True,
                'message': '服務項目已成功刪除'
            })
            
        except Exception as e:
            print(f"Error deleting service {service_id}: {e}")  # Debug
            db.session.rollback()
            return jsonify({'error': f'刪除服務失敗: {str(e)}'}), 500

@app.route('/api/schedule', methods=['GET', 'POST'])
@login_required
def api_schedule():
    merchant = Merchant.query.filter_by(user_id=current_user.id).first()
    if not merchant:
        return jsonify({'error': 'Merchant not found'}), 400
    
    if request.method == 'POST':
        data = request.json
        print(f"Received schedule data: {data}")  # Debug
        
        # 清除現有營業時間
        Schedule.query.filter_by(merchant_id=merchant.id).delete()
        
        # 添加新的營業時間（支持多時段）
        for day_data in data:
            schedule = Schedule(
                merchant_id=merchant.id,
                day_of_week=day_data.get('day_of_week'),
                start_time=day_data.get('start_time'),
                end_time=day_data.get('end_time'),
                is_available=day_data.get('is_available', True),
                schedule_type=day_data.get('schedule_type', 'regular')
            )
            db.session.add(schedule)
        
        try:
            db.session.commit()
            print("Schedule saved successfully")  # Debug
            return jsonify({'success': True})
        except Exception as e:
            print(f"Error saving schedule: {e}")  # Debug
            db.session.rollback()
            return jsonify({'error': str(e)}), 500
    
    schedules = Schedule.query.filter_by(merchant_id=merchant.id).all()
    # 按星期幾和時間排序
    schedules.sort(key=lambda s: (s.day_of_week, s.start_time))
    return jsonify([{
        'id': s.id,
        'day_of_week': s.day_of_week,
        'start_time': s.start_time,
        'end_time': s.end_time,
        'is_available': s.is_available,
        'schedule_type': s.schedule_type
    } for s in schedules])

@app.route('/api/special-schedule', methods=['GET', 'POST'])
@login_required
def api_special_schedule():
    """特殊營業時間 API（臨時調休、節假日等）"""
    merchant = Merchant.query.filter_by(user_id=current_user.id).first()
    if not merchant:
        return jsonify({'error': 'Merchant not found'}), 400
    
    if request.method == 'POST':
        data = request.json
        
        special = SpecialSchedule(
            merchant_id=merchant.id,
            date=datetime.strptime(data.get('date'), '%Y-%m-%d').date(),
            is_closed=data.get('is_closed', False),
            open_time=data.get('open_time'),
            close_time=data.get('close_time'),
            reason=data.get('reason', '')
        )
        
        db.session.add(special)
        db.session.commit()
        return jsonify({'success': True, 'id': special.id})
    
    specials = SpecialSchedule.query.filter_by(merchant_id=merchant.id).order_by(SpecialSchedule.date).all()
    return jsonify([{
        'id': s.id,
        'date': s.date.strftime('%Y-%m-%d'),
        'is_closed': s.is_closed,
        'open_time': s.open_time,
        'close_time': s.close_time,
        'reason': s.reason
    } for s in specials])

@app.route('/api/special-schedule/<int:special_id>', methods=['DELETE'])
@login_required
def api_delete_special_schedule(special_id):
    """刪除特殊營業時間"""
    merchant = Merchant.query.filter_by(user_id=current_user.id).first()
    if not merchant:
        return jsonify({'error': 'Merchant not found'}), 400
    
    special = SpecialSchedule.query.filter_by(id=special_id, merchant_id=merchant.id).first()
    if not special:
        return jsonify({'error': 'Special schedule not found'}), 404
    
    db.session.delete(special)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/appointments', methods=['GET', 'POST'])
@login_required
def api_appointments():
    merchant = Merchant.query.filter_by(user_id=current_user.id).first()
    if not merchant:
        return jsonify({'error': 'Merchant not found'}), 400
    
    if request.method == 'POST':
        data = request.json
        appointment = Appointment(
            merchant_id=merchant.id,
            customer_name=data.get('customer_name'),
            customer_phone=data.get('customer_phone'),
            service_id=data.get('service_id'),
            date=datetime.strptime(data.get('date'), '%Y-%m-%d').date(),
            time=data.get('time'),
            status='confirmed'
        )
        db.session.add(appointment)
        db.session.commit()
        return jsonify({'success': True})
    
    appointments = Appointment.query.filter_by(merchant_id=merchant.id).all()
    return jsonify([{
        'id': a.id,
        'customer_name': a.customer_name,
        'customer_phone': a.customer_phone,
        'service_name': a.service.name if a.service else None,
        'date': a.date.strftime('%Y-%m-%d'),
        'time': a.time,
        'status': a.status
    } for a in appointments])

@app.route('/api/appointments/<int:appointment_id>', methods=['DELETE'])
@login_required
def api_delete_appointment(appointment_id):
    merchant = Merchant.query.filter_by(user_id=current_user.id).first()
    if not merchant:
        return jsonify({'error': 'Merchant not found'}), 400
    
    appointment = Appointment.query.filter_by(id=appointment_id, merchant_id=merchant.id).first()
    if not appointment:
        return jsonify({'error': 'Appointment not found'}), 404
    
    db.session.delete(appointment)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/api/calendar/<date>')
@login_required
def api_calendar(date):
    merchant = Merchant.query.filter_by(user_id=current_user.id).first()
    if not merchant:
        return jsonify({'error': 'Merchant not found'}), 400
    
    try:
        target_date = datetime.strptime(date, '%Y-%m-%d').date()
        day_of_week = target_date.weekday()
        
        # Get schedule for this day
        schedule = Schedule.query.filter_by(
            merchant_id=merchant.id,
            day_of_week=day_of_week,
            is_available=True
        ).first()
        
        # Get appointments for this day
        appointments = Appointment.query.filter_by(
            merchant_id=merchant.id,
            date=target_date
        ).all()
        
        # Get blocked times for this day
        blocked_times = BlockedTime.query.filter_by(
            merchant_id=merchant.id,
            date=target_date
        ).all()
        
        return jsonify({
            'available': schedule is not None,
            'schedule': {
                'start_time': schedule.start_time,
                'end_time': schedule.end_time
            } if schedule else None,
            'appointments': [{'time': a.time, 'customer': a.customer_name} for a in appointments],
            'blocked_times': [{'start_time': bt.start_time, 'end_time': bt.end_time} for bt in blocked_times]
        })
        
    except ValueError:
        return jsonify({'error': 'Invalid date format'}), 400

@app.route('/api/ngrok-url', methods=['GET'])
@login_required
def get_ngrok_url():
    """獲取 ngrok URL（如果 ngrok 正在運行）"""
    try:
        import requests
        import re
        
        # 嘗試從 ngrok API 獲取 URL
        response = requests.get('http://127.0.0.1:4040/api/tunnels', timeout=2)
        if response.status_code == 200:
            data = response.json()
            tunnels = data.get('tunnels', [])
            
            # 尋找 HTTP 隧道
            for tunnel in tunnels:
                if tunnel.get('proto') == 'http' and tunnel.get('public_url'):
                    return jsonify({
                        'url': tunnel['public_url'],
                        'status': 'active'
                    })
        
        return jsonify({
            'url': None,
            'status': 'inactive'
        })
        
    except Exception as e:
        print(f"Error getting ngrok URL: {e}")
        return jsonify({
            'url': None,
            'status': 'error',
            'error': str(e)
        })

@app.route('/webhook/<string:identifier>', methods=['POST'])
def merchant_webhook(identifier):
    """特定商家的 Webhook 端點 - 支援 Merchant ID 或用戶名稱"""
    
    # 首先嘗試通過 Merchant ID 查找
    try:
        merchant_id = int(identifier)
        merchant = Merchant.query.filter_by(id=merchant_id).first()
    except ValueError:
        # 如果不是數字，嘗試通過用戶名稱查找
        merchant = Merchant.query.join(User).filter(User.username == identifier).first()
    
    if not merchant or not merchant.line_channel_secret:
        print(f"No merchant found for identifier: {identifier} or LINE secret not configured")
        return 'OK', 200
    
    line_bot_api = LineBotApi(merchant.line_channel_access_token)
    handler = WebhookHandler(merchant.line_channel_secret)
    
    body = request.get_data(as_text=True)
    signature = request.headers['X-Line-Signature']
    
    print(f"Webhook received for merchant {merchant.name} (ID: {merchant.id}): {body}")  # Debug log
    
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
