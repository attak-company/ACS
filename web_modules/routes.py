# Web 模組 - 其他路由
# 負責：其他網站路由

from flask import Blueprint, render_template

# 創建 Blueprint
web_bp = Blueprint('web', __name__)

@web_bp.route('/test-login')
def test_login():
    """登入測試頁面"""
    return render_template('test_login.html')

@web_bp.route('/test-forgot-password')
def test_forgot_password():
    """忘記密碼測試頁面"""
    return render_template('test_forgot_password.html')
