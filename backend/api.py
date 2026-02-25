"""
BizIT Analytics - Business API Routes
"""
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from sqlalchemy import func, extract
from models import db, BusinessData, Alert, UploadHistory, User
from utils import (
    process_upload_file, calculate_kpis, generate_alerts,
    generate_pdf_report, generate_excel_report
)
import os

api_bp = Blueprint('api', __name__)


# Helper function to check if user is admin
def is_admin():
    """Check if current user is admin"""
    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)
    return user and user.role == 'Admin'


def apply_user_filter(query):
    """Apply user filter - non-admins see only their data"""
    if not is_admin():
        user_id = int(get_jwt_identity())
        query = query.filter(BusinessData.created_by == user_id)
    return query


# ==================== DASHBOARD DATA ====================

@api_bp.route('/dashboard/kpis', methods=['GET'])
@jwt_required()
def get_dashboard_kpis():
    """Get KPI summary for dashboard"""
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    department = request.args.get('department')
    
    query = BusinessData.query
    
    # Apply user filter (non-admins see only their data)
    query = apply_user_filter(query)
    
    # Apply filters
    if start_date:
        query = query.filter(BusinessData.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(BusinessData.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    if department and department != 'all':
        query = query.filter(BusinessData.department == department)
    
    data = query.all()
    kpis = calculate_kpis(data)
    
    return jsonify(kpis), 200


@api_bp.route('/dashboard/revenue-trend', methods=['GET'])
@jwt_required()
def get_revenue_trend():
    """Get monthly revenue trend data"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    department = request.args.get('department')
    
    query = db.session.query(
        func.strftime('%Y-%m', BusinessData.date).label('month'),
        func.sum(BusinessData.revenue).label('total_revenue'),
        func.sum(BusinessData.profit).label('total_profit'),
        func.sum(BusinessData.cost).label('total_cost')
    )
    
    # Apply user filter
    if not is_admin():
        user_id = int(get_jwt_identity())
        query = query.filter(BusinessData.created_by == user_id)
    
    if start_date:
        query = query.filter(BusinessData.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(BusinessData.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    if department and department != 'all':
        query = query.filter(BusinessData.department == department)
    
    results = query.group_by(func.strftime('%Y-%m', BusinessData.date)).order_by('month').all()
    
    trend_data = {
        'labels': [r.month for r in results],
        'revenue': [round(r.total_revenue, 2) for r in results],
        'profit': [round(r.total_profit, 2) for r in results],
        'cost': [round(r.total_cost, 2) for r in results]
    }
    
    return jsonify(trend_data), 200


@api_bp.route('/dashboard/department-distribution', methods=['GET'])
@jwt_required()
def get_department_distribution():
    """Get revenue distribution by department"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = db.session.query(
        BusinessData.department,
        func.sum(BusinessData.revenue).label('total_revenue'),
        func.sum(BusinessData.profit).label('total_profit'),
        func.sum(BusinessData.cost).label('total_cost'),
        func.sum(BusinessData.sales_volume).label('total_sales')
    )
    
    # Apply user filter
    if not is_admin():
        user_id = int(get_jwt_identity())
        query = query.filter(BusinessData.created_by == user_id)
    
    if start_date:
        query = query.filter(BusinessData.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(BusinessData.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    results = query.group_by(BusinessData.department).all()
    
    distribution_data = {
        'labels': [r.department for r in results],
        'revenue': [round(r.total_revenue, 2) for r in results],
        'profit': [round(r.total_profit, 2) for r in results],
        'cost': [round(r.total_cost, 2) for r in results],
        'sales': [r.total_sales for r in results]
    }
    
    return jsonify(distribution_data), 200


@api_bp.route('/dashboard/profit-margin-trend', methods=['GET'])
@jwt_required()
def get_profit_margin_trend():
    """Get profit margin trend data"""
    department = request.args.get('department')
    
    query = db.session.query(
        func.strftime('%Y-%m', BusinessData.date).label('month'),
        func.sum(BusinessData.revenue).label('total_revenue'),
        func.sum(BusinessData.profit).label('total_profit')
    )
    
    # Apply user filter
    if not is_admin():
        user_id = int(get_jwt_identity())
        query = query.filter(BusinessData.created_by == user_id)
    
    if department and department != 'all':
        query = query.filter(BusinessData.department == department)
    
    results = query.group_by(func.strftime('%Y-%m', BusinessData.date)).order_by('month').all()
    
    margin_data = {
        'labels': [r.month for r in results],
        'margins': [round((r.total_profit / r.total_revenue * 100) if r.total_revenue > 0 else 0, 2) for r in results]
    }
    
    return jsonify(margin_data), 200


@api_bp.route('/dashboard/sales-trend', methods=['GET'])
@jwt_required()
def get_sales_trend():
    """Get sales volume trend"""
    department = request.args.get('department')
    
    query = db.session.query(
        func.strftime('%Y-%m', BusinessData.date).label('month'),
        func.sum(BusinessData.sales_volume).label('total_sales')
    )
    
    # Apply user filter
    if not is_admin():
        user_id = int(get_jwt_identity())
        query = query.filter(BusinessData.created_by == user_id)
    
    if department and department != 'all':
        query = query.filter(BusinessData.department == department)
    
    results = query.group_by(func.strftime('%Y-%m', BusinessData.date)).order_by('month').all()
    
    return jsonify({
        'labels': [r.month for r in results],
        'sales': [r.total_sales for r in results]
    }), 200


# ==================== DATA MANAGEMENT ====================

@api_bp.route('/data', methods=['GET'])
@jwt_required()
def get_business_data():
    """Get paginated business data"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    department = request.args.get('department')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = BusinessData.query
    
    # Apply user filter
    query = apply_user_filter(query)
    
    if department and department != 'all':
        query = query.filter(BusinessData.department == department)
    if start_date:
        query = query.filter(BusinessData.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(BusinessData.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    pagination = query.order_by(BusinessData.date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return jsonify({
        'data': [item.to_dict() for item in pagination.items],
        'total': pagination.total,
        'pages': pagination.pages,
        'current_page': page
    }), 200


@api_bp.route('/data/<int:data_id>', methods=['GET'])
@jwt_required()
def get_single_data(data_id):
    """Get single business data record"""
    data = BusinessData.query.get(data_id)
    if not data:
        return jsonify({'error': 'Record not found'}), 404
    return jsonify({'data': data.to_dict()}), 200


@api_bp.route('/data/<int:data_id>', methods=['PUT'])
@jwt_required()
def update_data(data_id):
    """Update business data record"""
    data = BusinessData.query.get(data_id)
    if not data:
        return jsonify({'error': 'Record not found'}), 404
    
    update_data = request.get_json()
    
    if 'date' in update_data:
        data.date = datetime.strptime(update_data['date'], '%Y-%m-%d').date()
    if 'revenue' in update_data:
        data.revenue = float(update_data['revenue'])
    if 'cost' in update_data:
        data.cost = float(update_data['cost'])
    if 'expenses' in update_data:
        data.expenses = float(update_data['expenses'])
    if 'profit' in update_data:
        data.profit = float(update_data['profit'])
    if 'department' in update_data:
        data.department = update_data['department']
    if 'sales_volume' in update_data:
        data.sales_volume = int(update_data['sales_volume'])
    
    db.session.commit()
    
    # Generate alerts if needed
    generate_alerts([data])
    
    return jsonify({'message': 'Record updated', 'data': data.to_dict()}), 200


@api_bp.route('/data/<int:data_id>', methods=['DELETE'])
@jwt_required()
def delete_data(data_id):
    """Delete business data record"""
    data = BusinessData.query.get(data_id)
    if not data:
        return jsonify({'error': 'Record not found'}), 404
    
    db.session.delete(data)
    db.session.commit()
    
    return jsonify({'message': 'Record deleted'}), 200


@api_bp.route('/departments', methods=['GET'])
@jwt_required()
def get_departments():
    """Get list of departments (filtered by user unless admin)"""
    query = db.session.query(BusinessData.department).distinct()
    
    # Apply user filter
    if not is_admin():
        user_id = int(get_jwt_identity())
        query = query.filter(BusinessData.created_by == user_id)
    
    departments = query.all()
    return jsonify({'departments': [d[0] for d in departments]}), 200


# ==================== FILE UPLOAD ====================

@api_bp.route('/upload', methods=['POST'])
@jwt_required()
def upload_file():
    """Upload CSV/Excel file with business data"""
    user_id = int(get_jwt_identity())
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # Process file
    result = process_upload_file(file, user_id)
    
    if result['status'] == 'error':
        return jsonify(result), 400
    
    return jsonify(result), 201


@api_bp.route('/upload/history', methods=['GET'])
@jwt_required()
def get_upload_history():
    """Get file upload history (user's own uploads, or all for admin)"""
    query = UploadHistory.query
    
    # Non-admins see only their own uploads
    if not is_admin():
        user_id = int(get_jwt_identity())
        query = query.filter(UploadHistory.uploaded_by == user_id)
    
    history = query.order_by(UploadHistory.created_at.desc()).limit(50).all()
    return jsonify({'history': [h.to_dict() for h in history]}), 200


# ==================== ALERTS ====================

@api_bp.route('/alerts', methods=['GET'])
@jwt_required()
def get_alerts():
    """Get all alerts"""
    unread_only = request.args.get('unread_only', 'false').lower() == 'true'
    
    query = Alert.query
    if unread_only:
        query = query.filter(Alert.is_read == False)
    
    alerts = query.order_by(Alert.created_at.desc()).limit(100).all()
    return jsonify({'alerts': [a.to_dict() for a in alerts]}), 200


@api_bp.route('/alerts/<int:alert_id>/read', methods=['PUT'])
@jwt_required()
def mark_alert_read(alert_id):
    """Mark alert as read"""
    alert = Alert.query.get(alert_id)
    if not alert:
        return jsonify({'error': 'Alert not found'}), 404
    
    alert.is_read = True
    db.session.commit()
    
    return jsonify({'message': 'Alert marked as read'}), 200


@api_bp.route('/alerts/read-all', methods=['PUT'])
@jwt_required()
def mark_all_alerts_read():
    """Mark all alerts as read"""
    Alert.query.update({'is_read': True})
    db.session.commit()
    return jsonify({'message': 'All alerts marked as read'}), 200


@api_bp.route('/alerts/generate', methods=['POST'])
@jwt_required()
def trigger_alert_generation():
    """Manually trigger alert generation"""
    data = BusinessData.query.all()
    generate_alerts(data)
    return jsonify({'message': 'Alerts generated'}), 200


# ==================== PROFITABILITY ANALYSIS ====================

@api_bp.route('/analysis/profitability', methods=['GET'])
@jwt_required()
def get_profitability_analysis():
    """Get comprehensive profitability analysis"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = BusinessData.query
    
    if start_date:
        query = query.filter(BusinessData.date >= datetime.strptime(start_date, '%Y-%m-%d').date())
    if end_date:
        query = query.filter(BusinessData.date <= datetime.strptime(end_date, '%Y-%m-%d').date())
    
    # Department-wise analysis
    dept_analysis = db.session.query(
        BusinessData.department,
        func.sum(BusinessData.revenue).label('revenue'),
        func.sum(BusinessData.cost).label('cost'),
        func.sum(BusinessData.profit).label('profit'),
        func.sum(BusinessData.expenses).label('expenses'),
        func.avg(BusinessData.profit / BusinessData.revenue * 100).label('avg_margin')
    ).group_by(BusinessData.department).all()
    
    departments = []
    for dept in dept_analysis:
        departments.append({
            'department': dept.department,
            'revenue': round(dept.revenue, 2),
            'cost': round(dept.cost, 2),
            'profit': round(dept.profit, 2),
            'expenses': round(dept.expenses, 2),
            'profit_margin': round(dept.avg_margin if dept.avg_margin else 0, 2)
        })
    
    # Sort by profit to find top/worst performers
    sorted_depts = sorted(departments, key=lambda x: x['profit'], reverse=True)
    
    # Monthly growth calculation
    monthly_data = db.session.query(
        func.strftime('%Y-%m', BusinessData.date).label('month'),
        func.sum(BusinessData.revenue).label('revenue'),
        func.sum(BusinessData.profit).label('profit')
    ).group_by(func.strftime('%Y-%m', BusinessData.date)).order_by('month').all()
    
    growth_rates = []
    for i in range(1, len(monthly_data)):
        prev_revenue = monthly_data[i-1].revenue
        curr_revenue = monthly_data[i].revenue
        if prev_revenue > 0:
            growth = ((curr_revenue - prev_revenue) / prev_revenue) * 100
            growth_rates.append({
                'month': monthly_data[i].month,
                'growth_rate': round(growth, 2)
            })
    
    return jsonify({
        'departments': departments,
        'top_performer': sorted_depts[0] if sorted_depts else None,
        'worst_performer': sorted_depts[-1] if sorted_depts else None,
        'monthly_growth': growth_rates
    }), 200


# ==================== REPORTS ====================

@api_bp.route('/reports/pdf', methods=['GET'])
@jwt_required()
def download_pdf_report():
    """Generate and download PDF report"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    department = request.args.get('department')
    
    pdf_path = generate_pdf_report(start_date, end_date, department)
    
    if pdf_path:
        return send_file(pdf_path, as_attachment=True, download_name='business_report.pdf')
    return jsonify({'error': 'Failed to generate PDF report'}), 500


@api_bp.route('/reports/excel', methods=['GET'])
@jwt_required()
def download_excel_report():
    """Generate and download Excel report"""
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    department = request.args.get('department')
    
    excel_path = generate_excel_report(start_date, end_date, department)
    
    if excel_path:
        return send_file(excel_path, as_attachment=True, 
                        download_name='business_report.xlsx',
                        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    return jsonify({'error': 'Failed to generate Excel report'}), 500


@api_bp.route('/reports/summary', methods=['GET'])
@jwt_required()
def get_monthly_summary():
    """Get monthly business summary"""
    month = request.args.get('month')  # Format: YYYY-MM
    
    if not month:
        # Default to current month
        month = datetime.now().strftime('%Y-%m')
    
    year, mon = month.split('-')
    
    data = BusinessData.query.filter(
        func.strftime('%Y', BusinessData.date) == year,
        func.strftime('%m', BusinessData.date) == mon
    ).all()
    
    kpis = calculate_kpis(data)
    
    # Get department breakdown for the month
    dept_breakdown = db.session.query(
        BusinessData.department,
        func.sum(BusinessData.revenue).label('revenue'),
        func.sum(BusinessData.profit).label('profit')
    ).filter(
        func.strftime('%Y', BusinessData.date) == year,
        func.strftime('%m', BusinessData.date) == mon
    ).group_by(BusinessData.department).all()
    
    return jsonify({
        'month': month,
        'kpis': kpis,
        'department_breakdown': [
            {'department': d.department, 'revenue': round(d.revenue, 2), 'profit': round(d.profit, 2)}
            for d in dept_breakdown
        ]
    }), 200


# ==================== ADMIN ENDPOINTS ====================

@api_bp.route('/admin/users', methods=['GET'])
@jwt_required()
def get_all_users():
    """Get all users (Admin only)"""
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    users = User.query.all()
    return jsonify({
        'users': [{
            'id': u.id,
            'name': u.name,
            'email': u.email,
            'role': u.role,
            'is_active': u.is_active,
            'created_at': u.created_at.isoformat() if u.created_at else None,
            'last_login': u.last_login.isoformat() if u.last_login else None
        } for u in users]
    }), 200


@api_bp.route('/admin/user-activity', methods=['GET'])
@jwt_required()
def get_user_activity():
    """Get user activity summary (Admin only)"""
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    # Get all users with their upload counts and data counts
    users = db.session.query(
        User.id,
        User.name,
        User.email,
        User.role,
        User.last_login,
        func.count(UploadHistory.id).label('upload_count'),
        func.count(BusinessData.id).label('data_count')
    ).outerjoin(UploadHistory, User.id == UploadHistory.uploaded_by)\
     .outerjoin(BusinessData, User.id == BusinessData.created_by)\
     .group_by(User.id).all()
    
    activity = [{
        'user_id': u.id,
        'name': u.name,
        'email': u.email,
        'role': u.role,
        'last_login': u.last_login.isoformat() if u.last_login else None,
        'upload_count': u.upload_count,
        'data_records': u.data_count
    } for u in users]
    
    return jsonify({'activity': activity}), 200


@api_bp.route('/admin/user/<int:user_id>/data', methods=['GET'])
@jwt_required()
def get_user_data(user_id):
    """Get specific user's data (Admin only)"""
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    # Check if user exists
    user = User.query.get(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    # Get user's business data
    data = BusinessData.query.filter_by(created_by=user_id)\
                             .order_by(BusinessData.date.desc())\
                             .limit(100).all()
    
    # Get user's upload history
    uploads = UploadHistory.query.filter_by(uploaded_by=user_id)\
                                 .order_by(UploadHistory.created_at.desc())\
                                 .limit(20).all()
    
    return jsonify({
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'role': user.role
        },
        'data': [d.to_dict() for d in data],
        'uploads': [u.to_dict() for u in uploads]
    }), 200


@api_bp.route('/admin/statistics', methods=['GET'])
@jwt_required()
def get_admin_statistics():
    """Get overall system statistics (Admin only)"""
    if not is_admin():
        return jsonify({'error': 'Admin access required'}), 403
    
    total_users = User.query.count()
    active_users = User.query.filter_by(is_active=True).count()
    total_records = BusinessData.query.count()
    total_uploads = UploadHistory.query.count()
    
    # Recent activity (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    recent_uploads = UploadHistory.query.filter(UploadHistory.created_at >= week_ago).count()
    
    # Get user login activity
    recent_logins = User.query.filter(User.last_login >= week_ago).count()
    
    return jsonify({
        'statistics': {
            'total_users': total_users,
            'active_users': active_users,
            'total_data_records': total_records,
            'total_uploads': total_uploads,
            'recent_uploads_7days': recent_uploads,
            'recent_logins_7days': recent_logins
        }
    }), 200
