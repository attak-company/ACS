# 共享模組 - 工具函數
# 負責：共用工具函數

from flask import current_app, request
from flask_mail import Message, Mail
import os
import re
from datetime import datetime, timedelta
import secrets
import string
from urllib.parse import urljoin

# 初始化郵件服務
mail = Mail()

def init_mail(app):
    """初始化郵件服務"""
    # 配置郵件設定
    app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
    app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', '587'))
    app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True').lower() == 'true'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'attak.company@gmail.com')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'zhaagfccyxawzhos')
    app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_DEFAULT_SENDER', 'attak.company@gmail.com')
    
    # 初始化郵件擴展
    mail.init_app(app)

def send_verification_email(email: str, code: str) -> bool:
    """發送驗證碼郵件"""
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
        return True
        
    except Exception as e:
        print(f"郵件發送失敗: {e}")
        return False

def validate_email(email: str) -> bool:
    """驗證電子郵件格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone: str) -> bool:
    """驗證電話號碼格式"""
    # 移除所有非數字字符
    digits_only = re.sub(r'\D', '', phone)
    
    # 檢查長度（台灣手機號碼為10位）
    return len(digits_only) == 10 and digits_only.startswith('09')

def format_phone(phone: str) -> str:
    """格式化電話號碼"""
    # 移除所有非數字字符
    digits_only = re.sub(r'\D', '', phone)
    
    # 如果是10位數字且以09開頭，格式化為 XXXX-XXX-XXX
    if len(digits_only) == 10 and digits_only.startswith('09'):
        return f"{digits_only[:4]}-{digits_only[4:7]}-{digits_only[7:]}"
    
    return phone

def generate_random_string(length: int = 8) -> str:
    """生成隨機字符串"""
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def format_datetime(dt: datetime, format_type: str = 'short') -> str:
    """格式化日期時間"""
    if format_type == 'short':
        return dt.strftime('%Y-%m-%d %H:%M')
    elif format_type == 'long':
        return dt.strftime('%Y年%m月%d日 %H:%M')
    elif format_type == 'date':
        return dt.strftime('%Y-%m-%d')
    elif format_type == 'time':
        return dt.strftime('%H:%M')
    else:
        return dt.strftime('%Y-%m-%d %H:%M:%S')

def calculate_age(birth_date: datetime) -> int:
    """計算年齡"""
    today = datetime.now()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    return age

def sanitize_filename(filename: str) -> str:
    """清理檔案名稱"""
    # 移除或替換不安全的字符
    filename = re.sub(r'[^\w\s-]', '', filename)
    filename = re.sub(r'[-\s]+', '-', filename)
    return filename.strip('-_')

def is_valid_password(password: str) -> tuple[bool, str]:
    """驗證密碼強度"""
    if len(password) < 8:
        return False, "密碼至少需要8個字符"
    
    if not re.search(r'[a-z]', password):
        return False, "密碼需要包含至少一個小寫字母"
    
    if not re.search(r'[A-Z]', password):
        return False, "密碼需要包含至少一個大寫字母"
    
    if not re.search(r'\d', password):
        return False, "密碼需要包含至少一個數字"
    
    return True, "密碼符合要求"

def paginate_query(query, page: int, per_page: int = 20):
    """分頁查詢"""
    items = query.limit(per_page).offset((page - 1) * per_page).all()
    total = query.count()
    
    return {
        'items': items,
        'total': total,
        'pages': (total + per_page - 1) // per_page,
        'current_page': page,
        'per_page': per_page,
        'has_next': page * per_page < total,
        'has_prev': page > 1
    }

def create_response(success: bool, message: str, data=None, error=None):
    """創建標準回應格式"""
    response = {
        'success': success,
        'message': message
    }
    
    if data is not None:
        response['data'] = data
    
    if error is not None:
        response['error'] = error
    
    return response

def log_user_action(user_id: int, action: str, details: str = None):
    """記錄用戶操作"""
    try:
        # 這裡可以實現日誌記錄到資料庫或檔案
        print(f"[{datetime.now()}] User {user_id}: {action} - {details}")
    except Exception as e:
        print(f"Error logging user action: {e}")

def get_client_ip():
    """獲取客戶端 IP 地址"""
    if request.environ.get('HTTP_X_FORWARDED_FOR'):
        return request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0]
    elif request.environ.get('HTTP_X_REAL_IP'):
        return request.environ['HTTP_X_REAL_IP']
    else:
        return request.environ.get('REMOTE_ADDR')

def is_safe_url(target: str) -> bool:
    """檢查 URL 是否安全"""
    try:
        from urllib.parse import urlparse
        ref_url = urlparse(request.host_url)
        test_url = urlparse(urljoin(request.host_url, target))
        return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc
    except:
        return False
