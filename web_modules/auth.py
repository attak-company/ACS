# Web 模組 - 認證相關功能
# 負責：登入、註冊、忘記密碼

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
import re
from shared.database import db
from shared.models import User, VerificationCode, Merchant
from shared.utils import send_verification_email

# 創建 Blueprint
auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """登入路由"""
    if current_user and current_user.is_authenticated:
        return redirect(url_for('dashboard.merchant_dashboard'))
    
    if request.method == 'POST':
        username_or_email = request.form.get('username')
        password = request.form.get('password')
        
        print(f"DEBUG: 登入嘗試 - username_or_email: {username_or_email}")
        
        if not username_or_email or not password:
            flash('請填寫所有必填欄位', 'error')
            return render_template('login_unified.html')
        
        # 嘗試通過用戶名或電子郵件查找用戶
        user = User.query.filter(
            (User.username == username_or_email) | 
            (User.email == username_or_email)
        ).first()
        
        print(f"DEBUG: 找到的用戶: {user}")
        
        if user and user.check_password(password):
            print(f"DEBUG: 密碼驗證成功")
            if login_user(user, remember=True):
                flash('登入成功！', 'success')
                return redirect(url_for('dashboard.merchant_dashboard'))
        else:
            print(f"DEBUG: 密碼驗證失敗")
            flash('密碼錯誤，請檢查您的密碼。', 'error')
    
    return render_template('login_unified.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """註冊路由"""
    if current_user and current_user.is_authenticated:
        return redirect(url_for('dashboard.merchant_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # 基本驗證
        if not all([username, email, password, confirm_password]):
            flash('請填寫所有必填欄位', 'error')
            return render_template('login_unified.html')
        
        if password != confirm_password:
            flash('密碼確認不一致', 'error')
            return render_template('login_unified.html')
        
        if len(password) < 8:
            flash('密碼至少需要8個字元', 'error')
            return render_template('login_unified.html')
        
        # 檢查用戶名和電子郵件是否已存在
        if User.query.filter_by(username=username).first():
            flash('用戶名稱已被使用', 'error')
            return render_template('login_unified.html')
        
        if User.query.filter_by(email=email).first():
            flash('電子郵件已被使用', 'error')
            return render_template('login_unified.html')
        
        # 創建新用戶
        user = User(username=username, email=email)
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # 創建對應的商家記錄
        from shared.models import Merchant
        merchant = Merchant(
            user_id=user.id,
            name='新店家'
        )
        db.session.add(merchant)
        db.session.commit()
        
        flash('註冊成功！請登入。', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('login_unified.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """登出路由"""
    logout_user()
    flash('已成功登出', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/api/send-verification-code', methods=['POST'])
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
        
        # 發送郵件
        email_sent = send_verification_email(email, code)
        
        if email_sent:
            return jsonify({
                'success': True,
                'message': '驗證碼已發送至您的電子郵件'
            })
        else:
            return jsonify({
                'success': True,
                'message': '驗證碼已生成（郵件發送失敗，請查看控制台）'
            })
        
    except Exception as e:
        db.session.rollback()
        print(f"發送驗證碼錯誤: {e}")
        return jsonify({'error': f'發送失敗: {str(e)}'}), 500

@auth_bp.route('/api/change-password-with-code', methods=['POST'])
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
