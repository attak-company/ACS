# 共享模組 - 資料模型
# 負責：定義資料表 (User, Token, Settings)

from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from shared.database import db
import secrets
import string

class User(db.Model):
    """用戶模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 關聯關係
    merchant = db.relationship('Merchant', backref='user', uselist=False, cascade='all, delete-orphan')
    
    def set_password(self, password):
        """設定密碼"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """檢查密碼"""
        return check_password_hash(self.password_hash, password)
    
    # Flask-Login 需要的屬性
    @property
    def is_authenticated(self):
        """Flask-Login 需要的屬性"""
        return True
    
    @property
    def is_anonymous(self):
        """Flask-Login 需要的屬性"""
        return False
    
    def get_id(self):
        """Flask-Login 需要的方法"""
        return str(self.id)
    
    def __repr__(self):
        return f'<User {self.username}>'

class Merchant(db.Model):
    """商家模型"""
    __tablename__ = 'merchants'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    arrival_info = db.Column(db.Text)
    ai_tone = db.Column(db.String(50), default='友善專業')
    
    # LINE Bot Configuration
    line_channel_access_token = db.Column(db.String(200))
    line_channel_secret = db.Column(db.String(200))
    
    # AI Configuration
    google_gemini_api_key = db.Column(db.String(200))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 關聯關係
    services = db.relationship('Service', backref='merchant', cascade='all, delete-orphan')
    schedules = db.relationship('Schedule', backref='merchant', cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', backref='merchant', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Merchant {self.name}>'

class Service(db.Model):
    """服務項目模型"""
    __tablename__ = 'services'
    
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchants.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer, nullable=False)  # 分鐘
    price = db.Column(db.Integer, nullable=False)  # 金額
    color = db.Column(db.String(20), default='#007bff')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Service {self.name}>'

class Schedule(db.Model):
    """營業時間模型"""
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchants.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Monday, 6=Sunday
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_available = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Schedule Day {self.day_of_week}>'

class SpecialSchedule(db.Model):
    """特別營業時間模型"""
    __tablename__ = 'special_schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchants.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)  # 特定日期
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_closed = db.Column(db.Boolean, default=False)
    reason = db.Column(db.String(200))
    
    def __repr__(self):
        return f'<SpecialSchedule {self.date}>'

class Appointment(db.Model):
    """預約模型"""
    __tablename__ = 'appointments'
    
    id = db.Column(db.Integer, primary_key=True)
    merchant_id = db.Column(db.Integer, db.ForeignKey('merchants.id'), nullable=False)
    customer_name = db.Column(db.String(100), nullable=False)
    customer_phone = db.Column(db.String(20))
    customer_email = db.Column(db.String(120))
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    appointment_time = db.Column(db.DateTime, nullable=False)
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled, completed
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Appointment {self.customer_name}>'

class VerificationCode(db.Model):
    """驗證碼模型"""
    __tablename__ = 'verification_codes'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def generate_code():
        """生成6位數驗證碼"""
        return ''.join(secrets.choice(string.digits) for _ in range(6))
    
    @staticmethod
    def is_valid(email: str, code: str):
        """驗證碼是否有效"""
        verification = VerificationCode.query.filter_by(
            email=email,
            code=code,
            is_used=False
        ).filter(
            VerificationCode.expires_at > datetime.utcnow()
        ).first()
        
        return verification
    
    def __repr__(self):
        return f'<VerificationCode {self.email}>'

class UserToken(db.Model):
    """用戶令牌模型"""
    __tablename__ = 'user_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(255), nullable=False, unique=True)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_revoked = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    @staticmethod
    def generate_token():
        """生成隨機令牌"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def is_valid(token: str):
        """驗證令牌是否有效"""
        user_token = UserToken.query.filter_by(
            token=token,
            is_revoked=False
        ).filter(
            UserToken.expires_at > datetime.utcnow()
        ).first()
        
        return user_token
    
    def __repr__(self):
        return f'<UserToken {self.token[:8]}...>'
