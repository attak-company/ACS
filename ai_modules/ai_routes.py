# AI 模組 - AI 相關路由
# 負責：AI 相關的 API 路由

from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required, current_user
from ai_modules.ai_service import AIService
from shared.database import db
from shared.models import Merchant

# 創建 Blueprint
ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/ai-test')
@login_required
def ai_test():
    """AI 測試頁面"""
    return render_template('ai_test.html')

@ai_bp.route('/api/ai/chat', methods=['POST'])
@login_required
def api_ai_chat():
    """AI 聊天 API"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': '訊息不能為空'}), 400
        
        # 獲取商家資訊
        merchant = Merchant.query.filter_by(user_id=current_user.id).first()
        if not merchant:
            return jsonify({'error': '請先設定店家資訊'}), 400
        
        # 檢查 AI 配置
        if not merchant.google_gemini_api_key:
            return jsonify({'error': '請先設定 Google Gemini API Key'}), 400
        
        # 初始化 AI 服務
        ai_service = AIService(merchant.google_gemini_api_key)
        
        # 生成回覆
        response = ai_service.generate_response(
            message,
            merchant.name,
            merchant.ai_tone or "友善專業"
        )
        
        return jsonify({
            'success': True,
            'response': response
        })
        
    except Exception as e:
        print(f"AI Chat API error: {e}")
        return jsonify({'error': 'AI 服務暫時無法使用'}), 500

@ai_bp.route('/api/ai/intent', methods=['POST'])
@login_required
def api_ai_intent():
    """AI 意圖分析 API"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': '訊息不能為空'}), 400
        
        # 獲取商家資訊
        merchant = Merchant.query.filter_by(user_id=current_user.id).first()
        if not merchant:
            return jsonify({'error': '請先設定店家資訊'}), 400
        
        # 檢查 AI 配置
        if not merchant.google_gemini_api_key:
            return jsonify({'error': '請先設定 Google Gemini API Key'}), 400
        
        # 初始化 AI 服務
        ai_service = AIService(merchant.google_gemini_api_key)
        
        # 分析意圖
        intent = ai_service.analyze_intent(message)
        
        return jsonify({
            'success': True,
            'intent': intent
        })
        
    except Exception as e:
        print(f"AI Intent API error: {e}")
        return jsonify({'error': 'AI 服務暫時無法使用'}), 500

@ai_bp.route('/api/ai/extract-appointment', methods=['POST'])
@login_required
def api_ai_extract_appointment():
    """AI 預約資訊提取 API"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        
        if not message:
            return jsonify({'error': '訊息不能為空'}), 400
        
        # 獲取商家資訊
        merchant = Merchant.query.filter_by(user_id=current_user.id).first()
        if not merchant:
            return jsonify({'error': '請先設定店家資訊'}), 400
        
        # 檢查 AI 配置
        if not merchant.google_gemini_api_key:
            return jsonify({'error': '請先設定 Google Gemini API Key'}), 400
        
        # 初始化 AI 服務
        ai_service = AIService(merchant.google_gemini_api_key)
        
        # 提取預約資訊
        appointment_info = ai_service.extract_appointment_info(message)
        
        return jsonify({
            'success': True,
            'appointment_info': appointment_info
        })
        
    except Exception as e:
        print(f"AI Appointment Extraction API error: {e}")
        return jsonify({'error': 'AI 服務暫時無法使用'}), 500
