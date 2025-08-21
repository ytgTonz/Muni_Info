from flask import Blueprint, request, jsonify
from functools import wraps
from datetime import datetime
from src.services.complaint_service import complaint_service
from src.services.community_service import community_service
from src.services.location_service import location_service
from src.services.user_service import user_service
from src.services.analytics_service import analytics_service
from src.services.monitoring_service import monitoring_service
from src.services.routing_service import routing_service
from src.models.complaint import ComplaintStatus, ComplaintPriority
from src.models.community import AnnouncementType, AnnouncementPriority
from src.models.user import UserRole

api_v1 = Blueprint('api_v1', __name__, url_prefix='/api/v1')

def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # In production, validate API key against database
        # For demo, accept any non-empty key
        if api_key != 'demo-api-key':
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

def paginate_results(query_results, page=1, per_page=20):
    """Helper function to paginate results"""
    total = len(query_results)
    start = (page - 1) * per_page
    end = start + per_page
    items = query_results[start:end]
    
    return {
        'items': items,
        'pagination': {
            'page': page,
            'per_page': per_page,
            'total': total,
            'pages': (total + per_page - 1) // per_page,
            'has_prev': page > 1,
            'has_next': page * per_page < total
        }
    }

# Authentication endpoint
@api_v1.route('/auth/token', methods=['POST'])
def get_auth_token():
    """Get API token for authenticated access"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    
    user = user_service.authenticate_user(username, password)
    if not user:
        return jsonify({'error': 'Invalid credentials'}), 401
    
    # In production, generate a real JWT token
    token = f"token-{user.user_id}-{datetime.now().timestamp()}"
    
    return jsonify({
        'token': token,
        'user': {
            'id': user.user_id,
            'username': user.username,
            'role': user.role.value,
            'municipality': user.municipality
        }
    })

# Complaints API
@api_v1.route('/complaints', methods=['GET'])
@require_api_key
def list_complaints():
    """List all complaints with filtering and pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    status = request.args.get('status')
    priority = request.args.get('priority')
    municipality = request.args.get('municipality')
    
    # Get all complaints
    complaints = complaint_service.repository.get_all_complaints()
    
    # Apply filters
    if status:
        complaints = [c for c in complaints if c.status.value == status]
    if priority:
        complaints = [c for c in complaints if c.priority.value == priority]
    if municipality:
        complaints = [c for c in complaints if c.location_info and c.location_info.get('municipality') == municipality]
    
    # Convert to dict
    complaint_dicts = [c.to_dict() for c in complaints]
    
    # Paginate
    result = paginate_results(complaint_dicts, page, per_page)
    
    return jsonify(result)

@api_v1.route('/complaints/<reference_id>', methods=['GET'])
@require_api_key
def get_complaint(reference_id):
    """Get specific complaint by reference ID"""
    complaint = complaint_service.get_complaint_by_reference(reference_id)
    if not complaint:
        return jsonify({'error': 'Complaint not found'}), 404
    
    return jsonify(complaint.to_dict())

@api_v1.route('/complaints/<reference_id>/status', methods=['PUT'])
@require_api_key
def update_complaint_status(reference_id):
    """Update complaint status"""
    data = request.get_json()
    new_status = data.get('status')
    notes = data.get('notes', '')
    
    if not new_status:
        return jsonify({'error': 'Status is required'}), 400
    
    try:
        status_enum = ComplaintStatus(new_status)
    except ValueError:
        return jsonify({'error': f'Invalid status: {new_status}'}), 400
    
    complaint = complaint_service.update_complaint_status(reference_id, status_enum, notes)
    if not complaint:
        return jsonify({'error': 'Complaint not found'}), 404
    
    return jsonify({
        'message': 'Status updated successfully',
        'complaint': complaint.to_dict()
    })

@api_v1.route('/complaints', methods=['POST'])
@require_api_key
def create_complaint():
    """Create new complaint via API"""
    data = request.get_json()
    
    required_fields = ['sender', 'complaint_type', 'description']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    priority = None
    if data.get('priority'):
        try:
            priority = ComplaintPriority(data['priority'])
        except ValueError:
            return jsonify({'error': f'Invalid priority: {data["priority"]}'}), 400
    
    complaint = complaint_service.create_complaint(
        sender=data['sender'],
        complaint_type=data['complaint_type'],
        description=data['description'],
        priority=priority,
        location_info=data.get('location_info')
    )
    
    return jsonify({
        'message': 'Complaint created successfully',
        'complaint': complaint.to_dict()
    }), 201

# Statistics API
@api_v1.route('/complaints/stats', methods=['GET'])
@require_api_key
def get_complaint_stats():
    """Get complaint statistics"""
    municipality = request.args.get('municipality')
    days = request.args.get('days', 30, type=int)
    
    stats = complaint_service.repository.get_statistics()
    
    # Get recent complaints for timeline
    recent_complaints = complaint_service.repository.get_recent_complaints(days=days)
    
    # Filter by municipality if specified
    if municipality:
        recent_complaints = [c for c in recent_complaints 
                           if c.location_info and c.location_info.get('municipality') == municipality]
    
    # Create daily timeline
    daily_counts = {}
    for complaint in recent_complaints:
        date_str = complaint.timestamp.strftime('%Y-%m-%d')
        daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
    
    return jsonify({
        'overview': stats,
        'recent_days': days,
        'daily_timeline': daily_counts,
        'total_recent': len(recent_complaints)
    })

# Location API
@api_v1.route('/location/identify', methods=['POST'])
@require_api_key
def identify_location():
    """Identify municipality from coordinates"""
    data = request.get_json()
    lat = data.get('latitude')
    lon = data.get('longitude')
    
    if lat is None or lon is None:
        return jsonify({'error': 'Latitude and longitude are required'}), 400
    
    try:
        lat = float(lat)
        lon = float(lon)
    except (TypeError, ValueError):
        return jsonify({'error': 'Invalid coordinate format'}), 400
    
    location = location_service.get_location_from_coordinates(lat, lon)
    if not location:
        return jsonify({'error': 'Location not found'}), 404
    
    return jsonify(location.to_dict())

# Community API
@api_v1.route('/announcements', methods=['GET'])
@require_api_key
def list_announcements():
    """List active announcements"""
    municipality = request.args.get('municipality')
    limit = min(request.args.get('limit', 50, type=int), 100)
    
    announcements = community_service.get_announcements_for_user(municipality)
    announcement_dicts = [a.to_dict() for a in announcements[:limit]]
    
    return jsonify({
        'announcements': announcement_dicts,
        'total': len(announcement_dicts)
    })

@api_v1.route('/announcements', methods=['POST'])
@require_api_key
def create_announcement():
    """Create new announcement"""
    data = request.get_json()
    
    required_fields = ['title', 'content', 'municipality', 'author']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    announcement_type = AnnouncementType.GENERAL
    if data.get('type'):
        try:
            announcement_type = AnnouncementType(data['type'])
        except ValueError:
            return jsonify({'error': f'Invalid announcement type: {data["type"]}'}), 400
    
    priority = AnnouncementPriority.MEDIUM
    if data.get('priority'):
        try:
            priority = AnnouncementPriority(data['priority'])
        except ValueError:
            return jsonify({'error': f'Invalid priority: {data["priority"]}'}), 400
    
    announcement = community_service.create_announcement(
        title=data['title'],
        content=data['content'],
        municipality=data['municipality'],
        author=data['author'],
        announcement_type=announcement_type,
        priority=priority,
        expires_in_days=data.get('expires_in_days'),
        areas_affected=data.get('areas_affected'),
        contact_info=data.get('contact_info')
    )
    
    return jsonify({
        'message': 'Announcement created successfully',
        'announcement': announcement.to_dict()
    }), 201

@api_v1.route('/ratings', methods=['POST'])
@require_api_key
def submit_rating():
    """Submit service rating"""
    data = request.get_json()
    
    required_fields = ['service_type', 'rating', 'municipality', 'user_phone']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'error': f'{field} is required'}), 400
    
    try:
        rating_value = int(data['rating'])
        if rating_value < 1 or rating_value > 5:
            raise ValueError()
    except (TypeError, ValueError):
        return jsonify({'error': 'Rating must be an integer between 1 and 5'}), 400
    
    rating = community_service.submit_rating(
        service_type=data['service_type'],
        rating=rating_value,
        municipality=data['municipality'],
        user_phone=data['user_phone'],
        comment=data.get('comment'),
        is_anonymous=data.get('is_anonymous', False)
    )
    
    return jsonify({
        'message': 'Rating submitted successfully',
        'rating': rating.to_dict()
    }), 201

@api_v1.route('/ratings/summary', methods=['GET'])
@require_api_key
def get_rating_summary():
    """Get service rating summary"""
    municipality = request.args.get('municipality')
    if not municipality:
        return jsonify({'error': 'Municipality parameter is required'}), 400
    
    summary = community_service.get_service_rating_summary(municipality)
    return jsonify({
        'municipality': municipality,
        'service_ratings': summary
    })

# Webhook endpoints for external systems
@api_v1.route('/webhooks/complaint-update', methods=['POST'])
@require_api_key
def webhook_complaint_update():
    """Webhook for external systems to update complaint status"""
    data = request.get_json()
    
    reference_id = data.get('reference_id')
    status = data.get('status')
    notes = data.get('notes', '')
    external_system = data.get('system', 'External System')
    
    if not reference_id or not status:
        return jsonify({'error': 'reference_id and status are required'}), 400
    
    try:
        status_enum = ComplaintStatus(status)
    except ValueError:
        return jsonify({'error': f'Invalid status: {status}'}), 400
    
    # Add external system info to notes
    if notes:
        notes = f"[{external_system}] {notes}"
    else:
        notes = f"Status updated by {external_system}"
    
    complaint = complaint_service.update_complaint_status(reference_id, status_enum, notes)
    if not complaint:
        return jsonify({'error': 'Complaint not found'}), 404
    
    return jsonify({
        'message': 'Complaint updated successfully',
        'reference_id': reference_id,
        'status': status
    })

# Health check endpoint
@api_v1.route('/health', methods=['GET'])
def health_check():
    """API health check"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'service': 'Muni-Info API'
    })

# API documentation endpoint
@api_v1.route('/docs', methods=['GET'])
def api_documentation():
    """API documentation"""
    docs = {
        'version': '1.0.0',
        'title': 'Muni-Info Municipal Integration API',
        'description': 'RESTful API for municipal systems integration',
        'base_url': '/api/v1',
        'authentication': 'API Key required in X-API-Key header',
        'endpoints': {
            'GET /health': 'Health check',
            'POST /auth/token': 'Get authentication token',
            'GET /complaints': 'List complaints with filtering',
            'GET /complaints/{id}': 'Get specific complaint',
            'POST /complaints': 'Create new complaint',
            'PUT /complaints/{id}/status': 'Update complaint status',
            'GET /complaints/stats': 'Get complaint statistics',
            'POST /location/identify': 'Identify location from coordinates',
            'GET /announcements': 'List active announcements',
            'POST /announcements': 'Create announcement',
            'POST /ratings': 'Submit service rating',
            'GET /ratings/summary': 'Get rating summary',
            'POST /webhooks/complaint-update': 'Webhook for external updates'
        },
        'status_codes': {
            '200': 'Success',
            '201': 'Created',
            '400': 'Bad Request',
            '401': 'Unauthorized',
            '404': 'Not Found',
            '500': 'Internal Server Error'
        }
    }
    
    return jsonify(docs)

# Phase 3: Advanced Analytics and Monitoring Endpoints

@api_v1.route('/analytics/dashboard', methods=['GET'])
@require_api_key
def get_analytics_dashboard():
    """Get comprehensive analytics dashboard data"""
    try:
        days = request.args.get('days', 30, type=int)
        dashboard_data = analytics_service.get_comprehensive_dashboard(days)
        
        return jsonify({
            'status': 'success',
            'data': dashboard_data
        })
    except Exception as e:
        return jsonify({'error': f'Analytics error: {str(e)}'}), 500

@api_v1.route('/monitoring/health', methods=['GET'])
@require_api_key
def get_system_health():
    """Get system health status"""
    try:
        health_data = monitoring_service.check_system_health()
        
        return jsonify({
            'status': 'success',
            'health_checks': {
                component: {
                    'status': health.status.value,
                    'response_time': health.response_time,
                    'message': health.message,
                    'timestamp': health.timestamp.isoformat()
                }
                for component, health in health_data.items()
            }
        })
    except Exception as e:
        return jsonify({'error': f'Health check error: {str(e)}'}), 500

@api_v1.route('/monitoring/metrics', methods=['GET'])
@require_api_key 
def get_performance_metrics():
    """Get real-time performance metrics"""
    try:
        metrics = monitoring_service.collect_system_metrics()
        
        return jsonify({
            'status': 'success',
            'metrics': [
                {
                    'name': metric.name,
                    'value': metric.value,
                    'unit': metric.unit,
                    'timestamp': metric.timestamp.isoformat()
                }
                for metric in metrics
            ]
        })
    except Exception as e:
        return jsonify({'error': f'Metrics error: {str(e)}'}), 500

@api_v1.route('/monitoring/alerts', methods=['GET'])
@require_api_key
def get_active_alerts():
    """Get active system alerts"""
    try:
        dashboard_data = monitoring_service.get_dashboard_data()
        
        return jsonify({
            'status': 'success',
            'active_alerts': dashboard_data['active_alerts'],
            'total_alerts': len(dashboard_data['active_alerts'])
        })
    except Exception as e:
        return jsonify({'error': f'Alerts error: {str(e)}'}), 500

@api_v1.route('/routing/status', methods=['GET'])
@require_api_key
def get_routing_status():
    """Get intelligent routing system status"""
    try:
        department_status = routing_service.get_department_status()
        analytics = routing_service.get_routing_analytics()
        
        return jsonify({
            'status': 'success',
            'departments': department_status,
            'analytics': analytics
        })
    except Exception as e:
        return jsonify({'error': f'Routing status error: {str(e)}'}), 500

@api_v1.route('/ai/analysis/<reference_id>', methods=['GET'])
@require_api_key
def get_ai_analysis(reference_id):
    """Get AI analysis results for a specific complaint"""
    try:
        complaint = complaint_service.get_complaint_by_reference(reference_id)
        if not complaint:
            return jsonify({'error': 'Complaint not found'}), 404
        
        if not hasattr(complaint, 'ai_analysis') or not complaint.ai_analysis:
            return jsonify({'error': 'No AI analysis available for this complaint'}), 404
        
        return jsonify({
            'status': 'success',
            'reference_id': reference_id,
            'ai_analysis': complaint.ai_analysis
        })
    except Exception as e:
        return jsonify({'error': f'AI analysis error: {str(e)}'}), 500

@api_v1.route('/ai/trends', methods=['GET'])
@require_api_key
def get_ai_trends():
    """Get AI-powered trend analysis"""
    try:
        # Get recent complaints for trend analysis
        recent_complaints = complaint_service.repository.get_recent_complaints(30)
        
        # Use AI service to analyze trends
        complaints_data = [
            {
                'description': c.description,
                'category': c.complaint_type,
                'priority': c.priority.value,
                'timestamp': c.timestamp.isoformat()
            }
            for c in recent_complaints
        ]
        
        trending_issues = analytics_service.ai_service.get_trending_issues(
            [{'description': c['description']} for c in complaints_data]
        )
        
        return jsonify({
            'status': 'success',
            'trending_issues': trending_issues,
            'analysis_period': '30 days',
            'total_analyzed': len(recent_complaints)
        })
    except Exception as e:
        return jsonify({'error': f'Trend analysis error: {str(e)}'}), 500

@api_v1.route('/predictions/resolution-time', methods=['POST'])
@require_api_key
def predict_resolution_time():
    """Predict resolution time for a complaint"""
    try:
        data = request.get_json()
        category = data.get('category', 'Other')
        priority = data.get('priority', 'medium')
        description = data.get('description', '')
        
        # Use AI to analyze and predict
        if description:
            ai_analysis = analytics_service.ai_service.analyze_complaint(description)
            category = ai_analysis.category
            priority = ai_analysis.priority
        
        predicted_time = analytics_service.ai_service.predict_resolution_time(category, priority)
        
        return jsonify({
            'status': 'success',
            'category': category,
            'priority': priority,
            'predicted_resolution_time': predicted_time,
            'confidence': 0.75  # Simplified confidence score
        })
    except Exception as e:
        return jsonify({'error': f'Prediction error: {str(e)}'}), 500