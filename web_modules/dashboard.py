# Web 模組 - 儀表板相關功能
# 負負責：儀表板路徑與邏輯

from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from shared.database import db
from shared.models import Merchant, Service, Schedule, Appointment

# 創建 Blueprint
dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/')
def index():
    """首頁路由"""
    if current_user and current_user.is_authenticated:
        return redirect(url_for('dashboard.merchant_dashboard'))
    return render_template('landing.html')

@dashboard_bp.route('/merchant')
@login_required
def merchant_dashboard():
    """商家儀表板"""
    return render_template('merchant.html')

@dashboard_bp.route('/api/merchant', methods=['GET', 'POST'])
@login_required
def api_merchant():
    """店家資料 API"""
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
        merchant.instagram_username = data.get('instagram_username', merchant.instagram_username)
        merchant.instagram_url = data.get('instagram_url', merchant.instagram_url)
        merchant.instagram_page_access_token = data.get('instagram_page_access_token', merchant.instagram_page_access_token)
        merchant.instagram_verify_token = data.get('instagram_verify_token', merchant.instagram_verify_token)
        
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
        'line_channel_secret': merchant.line_channel_secret,
        'instagram_username': merchant.instagram_username,
        'instagram_url': merchant.instagram_url,
        'instagram_page_access_token': merchant.instagram_page_access_token,
        'instagram_verify_token': merchant.instagram_verify_token
    })

@dashboard_bp.route('/api/services', methods=['GET', 'POST'])
@login_required
def api_services():
    """服務項目 API"""
    merchant = Merchant.query.filter_by(user_id=current_user.id).first()
    if not merchant:
        return jsonify({'error': '請先設定店家資訊'}), 400
    
    if request.method == 'POST':
        data = request.json
        try:
            service = Service(
                merchant_id=merchant.id,
                name=data['name'],
                description=data.get('description', ''),
                duration=int(data['duration']),
                price=int(float(data['price'])),
                color=data.get('color', '#007bff')
            )
            db.session.add(service)
            db.session.commit()
            return jsonify({'success': True, 'id': service.id})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
    
    services = Service.query.filter_by(merchant_id=merchant.id).all()
    return jsonify([{
        'id': s.id,
        'name': s.name,
        'description': s.description,
        'duration': s.duration,
        'price': s.price,
        'color': getattr(s, 'color', '#007bff')
    } for s in services])

@dashboard_bp.route('/api/services/<int:service_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_service_detail(service_id):
    """服務項目詳情 API"""
    merchant = Merchant.query.filter_by(user_id=current_user.id).first()
    if not merchant:
        return jsonify({'error': '請先設定店家資訊'}), 400
    
    service = Service.query.filter_by(id=service_id, merchant_id=merchant.id).first()
    if not service:
        return jsonify({'error': '服務項目不存在'}), 404
    
    if request.method == 'GET':
        return jsonify({
            'id': service.id,
            'name': service.name,
            'description': service.description,
            'duration': service.duration,
            'price': service.price,
            'color': getattr(service, 'color', '#007bff')
        })
    
    elif request.method == 'PUT':
        data = request.json
        try:
            service.name = data.get('name', service.name)
            service.description = data.get('description', service.description)
            if 'duration' in data:
                service.duration = int(data['duration'])
            if 'price' in data:
                service.price = int(float(data['price']))
            if 'color' in data:
                service.color = data['color']
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400
    
    elif request.method == 'DELETE':
        try:
            db.session.delete(service)
            db.session.commit()
            return jsonify({'success': True})
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 400

@dashboard_bp.route('/api/schedule', methods=['GET', 'POST'])
@login_required
def api_schedule():
    """營業時間 API"""
    merchant = Merchant.query.filter_by(user_id=current_user.id).first()
    if not merchant:
        return jsonify({'error': '請先設定店家資訊'}), 400
    
    if request.method == 'POST':
        data = request.json
        # 刪除舊的營業時間
        Schedule.query.filter_by(merchant_id=merchant.id).delete()
        
        # 新增營業時間
        for schedule_item in data:
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
    
    schedules = Schedule.query.filter_by(merchant_id=merchant.id).all()
    return jsonify([{
        'id': s.id,
        'day_of_week': s.day_of_week,
        'start_time': s.start_time,
        'end_time': s.end_time,
        'is_available': s.is_available,
        'schedule_type': 'regular'
    } for s in schedules])

@dashboard_bp.route('/api/appointments', methods=['GET', 'POST'])
@login_required
def api_appointments():
    """預約管理 API"""
    merchant = Merchant.query.filter_by(user_id=current_user.id).first()
    if not merchant:
        return jsonify({'error': '請先設定店家資訊'}), 400
    
    if request.method == 'POST':
        data = request.json
        appointment = Appointment(
            merchant_id=merchant.id,
            customer_name=data['customer_name'],
            customer_phone=data.get('customer_phone', ''),
            service_id=data['service_id'],
            appointment_time=data['appointment_time'],
            notes=data.get('notes', ''),
            status='pending'
        )
        db.session.add(appointment)
        db.session.commit()
        return jsonify({'success': True, 'id': appointment.id})
    
    appointments = Appointment.query.filter_by(merchant_id=merchant.id).all()
    return jsonify([{
        'id': a.id,
        'customer_name': a.customer_name,
        'customer_phone': a.customer_phone,
        'service_id': a.service_id,
        'service_name': Service.query.get(a.service_id).name if a.service_id else '',
        'appointment_time': a.appointment_time.isoformat() if a.appointment_time else '',
        'notes': a.notes,
        'status': a.status
    } for a in appointments])

@dashboard_bp.route('/api/appointments/<int:appointment_id>', methods=['PUT', 'DELETE'])
@login_required
def api_appointment_detail(appointment_id):
    """預約詳情 API"""
    merchant = Merchant.query.filter_by(user_id=current_user.id).first()
    if not merchant:
        return jsonify({'error': '請先設定店家資訊'}), 400
    
    appointment = Appointment.query.filter_by(id=appointment_id, merchant_id=merchant.id).first()
    if not appointment:
        return jsonify({'error': '預約不存在'}), 404
    
    if request.method == 'PUT':
        data = request.json
        appointment.status = data.get('status', appointment.status)
        appointment.notes = data.get('notes', appointment.notes)
        db.session.commit()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        db.session.delete(appointment)
        db.session.commit()
        return jsonify({'success': True})
