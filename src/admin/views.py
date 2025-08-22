from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from datetime import datetime, timedelta
from src.services.user_service import user_service
from src.services.complaint_service import complaint_service
from src.services.community_service import community_service
from src.models.user import UserRole
from src.models.complaint import ComplaintStatus, ComplaintPriority
from src.models.community import AnnouncementType, AnnouncementPriority

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def require_dashboard_access(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.can_access_dashboard():
            flash('Access denied. Insufficient privileges.', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = user_service.authenticate_user(username, password)
        if user and user.can_access_dashboard():
            login_user(user, remember=True)
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid credentials or insufficient privileges', 'error')
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out successfully', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@login_required
@require_dashboard_access
def dashboard():
    # Get dashboard statistics
    complaint_stats = complaint_service.repository.get_statistics()
    user_stats = user_service.get_dashboard_stats()
    
    # Get recent complaints
    recent_complaints = complaint_service.repository.get_recent_complaints(days=7)
    
    # Get complaints by status for charts
    status_data = []
    for status in ComplaintStatus:
        count = complaint_stats['by_status'].get(status.value, 0)
        status_data.append({
            'status': status.value.title(),
            'count': count,
            'color': _get_status_color(status)
        })
    
    # Get complaints by priority
    priority_data = []
    for priority in ComplaintPriority:
        count = complaint_stats['by_priority'].get(priority.value, 0)
        priority_data.append({
            'priority': priority.value.title(),
            'count': count,
            'color': _get_priority_color(priority)
        })
    
    return render_template('admin/dashboard.html',
                         complaint_stats=complaint_stats,
                         user_stats=user_stats,
                         recent_complaints=recent_complaints[:10],
                         status_data=status_data,
                         priority_data=priority_data)

@admin_bp.route('/complaints')
@login_required
@require_dashboard_access
def complaints():
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status')
    priority_filter = request.args.get('priority')
    
    # Get all complaints
    all_complaints = complaint_service.repository.get_all_complaints()
    
    # Apply filters
    filtered_complaints = all_complaints
    if status_filter and status_filter != 'all':
        filtered_complaints = [c for c in filtered_complaints if c.status.value == status_filter]
    if priority_filter and priority_filter != 'all':
        filtered_complaints = [c for c in filtered_complaints if c.priority.value == priority_filter]
    
    # Pagination
    per_page = 20
    total = len(filtered_complaints)
    start = (page - 1) * per_page
    end = start + per_page
    complaints_page = filtered_complaints[start:end]
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': (total + per_page - 1) // per_page,
        'has_prev': page > 1,
        'has_next': page * per_page < total,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page * per_page < total else None
    }
    
    return render_template('admin/complaints.html',
                         complaints=complaints_page,
                         pagination=pagination,
                         status_filter=status_filter,
                         priority_filter=priority_filter,
                         statuses=ComplaintStatus,
                         priorities=ComplaintPriority)

@admin_bp.route('/complaints/<reference_id>')
@login_required
@require_dashboard_access
def complaint_detail(reference_id):
    complaint = complaint_service.get_complaint_by_reference(reference_id)
    if not complaint:
        flash('Complaint not found', 'error')
        return redirect(url_for('admin.complaints'))
    
    return render_template('admin/complaint_detail.html', complaint=complaint)

@admin_bp.route('/complaints/<reference_id>/update', methods=['POST'])
@login_required
@require_dashboard_access
def update_complaint(reference_id):
    complaint = complaint_service.get_complaint_by_reference(reference_id)
    if not complaint:
        return jsonify({'error': 'Complaint not found'}), 404
    
    new_status = request.json.get('status')
    notes = request.json.get('notes', '')
    
    try:
        status_enum = ComplaintStatus(new_status)
        updated_complaint = complaint_service.update_complaint_status(
            reference_id, status_enum, notes
        )
        
        if updated_complaint:
            # Send notification to user
            from src.services.notification_service import notification_service
            if status_enum == ComplaintStatus.RESOLVED:
                notification_service.notify_complaint_resolved(updated_complaint)
            else:
                notification_service.notify_status_update(updated_complaint, notes)
            
            return jsonify({
                'success': True,
                'message': f'Complaint updated to {status_enum.value}',
                'status': status_enum.value
            })
        else:
            return jsonify({'error': 'Failed to update complaint'}), 500
            
    except ValueError as e:
        return jsonify({'error': f'Invalid status: {new_status}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users')
@login_required
@require_dashboard_access
def users():
    if not current_user.can_manage_users():
        flash('Access denied. Insufficient privileges.', 'error')
        return redirect(url_for('admin.dashboard'))
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '')
    role_filter = request.args.get('role')
    
    all_users = user_service.repository.get_all_users()
    
    # Apply search filter
    if search:
        all_users = [u for u in all_users if 
                    search.lower() in u.full_name.lower() or 
                    search.lower() in u.username.lower() or 
                    search.lower() in (u.email or '').lower()]
    
    # Apply role filter
    if role_filter and role_filter != 'all':
        all_users = [u for u in all_users if u.role.value == role_filter]
    
    # Pagination
    per_page = 15
    total = len(all_users)
    start = (page - 1) * per_page
    end = start + per_page
    users_page = all_users[start:end]
    
    pagination = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': (total + per_page - 1) // per_page,
        'has_prev': page > 1,
        'has_next': page * per_page < total,
        'prev_num': page - 1 if page > 1 else None,
        'next_num': page + 1 if page * per_page < total else None
    }
    
    return render_template('admin/users.html', 
                         users=users_page,
                         all_users=all_users,
                         pagination=pagination,
                         search=search,
                         role_filter=role_filter,
                         user_roles=UserRole)

@admin_bp.route('/analytics')
@login_required
@require_dashboard_access
def analytics():
    # Get analytics data for the last 30 days
    complaints = complaint_service.repository.get_recent_complaints(days=30)
    
    # Group complaints by date
    daily_counts = {}
    for complaint in complaints:
        date_str = complaint.timestamp.strftime('%Y-%m-%d')
        daily_counts[date_str] = daily_counts.get(date_str, 0) + 1
    
    # Create timeline data
    timeline_data = []
    for i in range(30):
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        timeline_data.insert(0, {
            'date': date_str,
            'count': daily_counts.get(date_str, 0)
        })
    
    # Get type distribution
    complaint_stats = complaint_service.repository.get_statistics()
    type_data = [
        {'type': k, 'count': v} 
        for k, v in complaint_stats['by_type'].items()
    ]
    
    return render_template('admin/analytics.html',
                         timeline_data=timeline_data,
                         type_data=type_data,
                         complaint_stats=complaint_stats)

@admin_bp.route('/api/complaints/stats')
@login_required
@require_dashboard_access
def api_complaint_stats():
    stats = complaint_service.repository.get_statistics()
    return jsonify(stats)

@admin_bp.route('/api/complaints/recent')
@login_required
@require_dashboard_access
def api_recent_complaints():
    days = request.args.get('days', 7, type=int)
    complaints = complaint_service.repository.get_recent_complaints(days=days)
    
    complaint_data = []
    for complaint in complaints[:20]:  # Limit to 20 most recent
        complaint_data.append({
            'reference_id': complaint.reference_id,
            'complaint_type': complaint.complaint_type,
            'status': complaint.status.value,
            'priority': complaint.priority.value,
            'timestamp': complaint.timestamp.isoformat(),
            'description': complaint.description[:100] + '...' if len(complaint.description) > 100 else complaint.description
        })
    
    return jsonify(complaint_data)

# User management routes
@admin_bp.route('/users/create', methods=['POST'])
@login_required
@require_dashboard_access
def create_user():
    if not current_user.can_manage_users():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['username', 'full_name', 'email', 'password', 'role']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if username already exists
        if user_service.repository.get_user_by_username(data['username']):
            return jsonify({'error': 'Username already exists'}), 400
        
        # Check if email already exists
        if data['email'] and user_service.repository.get_user_by_email(data['email']):
            return jsonify({'error': 'Email already exists'}), 400
        
        # Create user
        user = user_service.create_admin_user(
            username=data['username'],
            full_name=data['full_name'],
            email=data['email'],
            password=data['password'],
            role=UserRole(data['role']),
            municipality=data.get('municipality'),
            department=data.get('department')
        )
        
        return jsonify({
            'success': True,
            'message': f'User {user.username} created successfully',
            'user': user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<user_id>', methods=['GET'])
@login_required
@require_dashboard_access
def get_user(user_id):
    if not current_user.can_manage_users():
        return jsonify({'error': 'Access denied'}), 403
    
    user = user_service.repository.get_user_by_id(user_id)
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify(user.to_dict())

@admin_bp.route('/users/<user_id>/update', methods=['POST'])
@login_required
@require_dashboard_access
def update_user(user_id):
    if not current_user.can_manage_users():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        user = user_service.repository.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        data = request.get_json()
        
        # Update user fields
        if 'full_name' in data:
            user.full_name = data['full_name']
        if 'email' in data:
            # Check if email already exists for another user
            existing_user = user_service.repository.get_user_by_email(data['email'])
            if existing_user and existing_user.user_id != user_id:
                return jsonify({'error': 'Email already exists'}), 400
            user.email = data['email']
        if 'role' in data:
            user.role = UserRole(data['role'])
        if 'municipality' in data:
            user.municipality = data['municipality']
        if 'department' in data:
            user.department = data['department']
        if 'is_active' in data:
            user.is_active = data['is_active']
        
        # Update password if provided
        if data.get('password'):
            user.set_password(data['password'])
        
        updated_user = user_service.repository.update_user(user)
        
        return jsonify({
            'success': True,
            'message': f'User {user.username} updated successfully',
            'user': updated_user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<user_id>/toggle-status', methods=['POST'])
@login_required
@require_dashboard_access
def toggle_user_status(user_id):
    if not current_user.can_manage_users():
        return jsonify({'error': 'Access denied'}), 403
    
    # Prevent users from deactivating themselves
    if user_id == current_user.user_id:
        return jsonify({'error': 'Cannot deactivate your own account'}), 400
    
    try:
        user = user_service.repository.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        user.is_active = not user.is_active
        updated_user = user_service.repository.update_user(user)
        
        status = 'activated' if user.is_active else 'deactivated'
        return jsonify({
            'success': True,
            'message': f'User {user.username} {status} successfully',
            'is_active': user.is_active
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/users/<user_id>/delete', methods=['DELETE'])
@login_required
@require_dashboard_access
def delete_user(user_id):
    if not current_user.can_manage_users():
        return jsonify({'error': 'Access denied'}), 403
    
    # Prevent users from deleting themselves
    if user_id == current_user.user_id:
        return jsonify({'error': 'Cannot delete your own account'}), 400
    
    try:
        user = user_service.repository.get_user_by_id(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        success = user_service.repository.delete_user(user_id)
        if success:
            return jsonify({
                'success': True,
                'message': f'User {user.username} deleted successfully'
            })
        else:
            return jsonify({'error': 'Failed to delete user'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Profile and Settings routes
@admin_bp.route('/profile')
@login_required
def profile():
    return render_template('admin/profile.html', user=current_user)

@admin_bp.route('/profile/update', methods=['POST'])
@login_required
def update_profile():
    try:
        data = request.get_json()
        
        # Update current user's profile
        if 'full_name' in data:
            current_user.full_name = data['full_name']
        if 'email' in data:
            # Check if email already exists for another user
            existing_user = user_service.repository.get_user_by_email(data['email'])
            if existing_user and existing_user.user_id != current_user.user_id:
                return jsonify({'error': 'Email already exists'}), 400
            current_user.email = data['email']
        if 'phone_number' in data:
            current_user.phone_number = data['phone_number']
        
        updated_user = user_service.repository.update_user(current_user)
        
        return jsonify({
            'success': True,
            'message': 'Profile updated successfully',
            'user': updated_user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/profile/change-password', methods=['POST'])
@login_required
def change_password():
    try:
        data = request.get_json()
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        # Validate input
        if not all([current_password, new_password, confirm_password]):
            return jsonify({'error': 'All password fields are required'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': 'New passwords do not match'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': 'Password must be at least 6 characters long'}), 400
        
        # Verify current password
        if not current_user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 400
        
        # Update password
        current_user.set_password(new_password)
        user_service.repository.update_user(current_user)
        
        return jsonify({
            'success': True,
            'message': 'Password changed successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/settings')
@login_required
@require_dashboard_access
def settings():
    if not current_user.can_manage_users():
        flash('Access denied. Insufficient privileges.', 'error')
        return redirect(url_for('admin.dashboard'))
    
    # Get system settings/statistics
    system_stats = {
        'total_users': len(user_service.repository.get_all_users()),
        'total_complaints': complaint_service.repository.get_statistics()['total'],
        'active_users': len([u for u in user_service.repository.get_all_users() if u.is_active]),
        'system_uptime': 'Available in production'
    }
    
    return render_template('admin/settings.html', system_stats=system_stats)

@admin_bp.route('/settings/system', methods=['POST'])
@login_required
@require_dashboard_access
def update_system_settings():
    if not current_user.can_manage_users():
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        
        # In a real implementation, you would update system configuration
        # For now, just acknowledge the request
        return jsonify({
            'success': True,
            'message': 'System settings updated successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def _get_status_color(status: ComplaintStatus) -> str:
    colors = {
        ComplaintStatus.SUBMITTED: '#17a2b8',  # info
        ComplaintStatus.IN_PROGRESS: '#ffc107',  # warning
        ComplaintStatus.UNDER_REVIEW: '#6f42c1',  # purple
        ComplaintStatus.RESOLVED: '#28a745',  # success
        ComplaintStatus.CLOSED: '#6c757d'  # secondary
    }
    return colors.get(status, '#6c757d')

def _get_priority_color(priority: ComplaintPriority) -> str:
    colors = {
        ComplaintPriority.LOW: '#28a745',  # green
        ComplaintPriority.MEDIUM: '#ffc107',  # yellow
        ComplaintPriority.HIGH: '#fd7e14',  # orange
        ComplaintPriority.URGENT: '#dc3545'  # red
    }
    return colors.get(priority, '#6c757d')

# Announcement Management Routes
@admin_bp.route('/announcements')
@login_required
@require_dashboard_access
def announcements():
    """Announcements management page"""
    # Get filter parameters
    municipality_filter = request.args.get('municipality', '')
    type_filter = request.args.get('type', '')
    priority_filter = request.args.get('priority', '')
    status_filter = request.args.get('status', '')
    
    # Get all announcements
    all_announcements = community_service.repository._load_data(community_service.repository.announcements_file)
    announcements = []
    
    # Convert to announcement objects and apply filters
    for item in all_announcements:
        announcement = community_service.repository._dict_to_announcement(item)
        
        # Apply filters
        if municipality_filter and announcement.municipality != municipality_filter:
            continue
        if type_filter and announcement.announcement_type.value != type_filter:
            continue
        if priority_filter and announcement.priority.value != priority_filter:
            continue
        if status_filter:
            if status_filter == 'active' and not announcement.is_active:
                continue
            elif status_filter == 'inactive' and announcement.is_active:
                continue
            elif status_filter == 'expired' and not announcement.is_expired():
                continue
        
        announcements.append(announcement)
    
    # Sort by priority then by creation date
    priority_order = {
        AnnouncementPriority.URGENT: 0,
        AnnouncementPriority.HIGH: 1,
        AnnouncementPriority.MEDIUM: 2,
        AnnouncementPriority.LOW: 3
    }
    announcements.sort(key=lambda x: (priority_order.get(x.priority, 4), -x.created_at.timestamp()))
    
    # Calculate statistics
    total_announcements = len(all_announcements)
    active_announcements = sum(1 for a in announcements if a.is_active and not a.is_expired())
    urgent_announcements = sum(1 for a in announcements if a.priority == AnnouncementPriority.URGENT and a.is_active)
    emergency_announcements = sum(1 for a in announcements if a.announcement_type == AnnouncementType.EMERGENCY and a.is_active)
    
    announcement_stats = {
        'total': total_announcements,
        'active': active_announcements,
        'urgent': urgent_announcements,
        'emergency': emergency_announcements
    }
    
    return render_template('admin/announcements.html',
                         announcements=announcements,
                         announcement_stats=announcement_stats,
                         municipality_filter=municipality_filter,
                         type_filter=type_filter,
                         priority_filter=priority_filter,
                         status_filter=status_filter)

@admin_bp.route('/announcements', methods=['POST'])
@login_required
@require_dashboard_access
def create_announcement():
    """Create new announcement"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['title', 'content', 'municipality', 'announcement_type', 'priority']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Parse announcement type and priority
        try:
            announcement_type = AnnouncementType(data['announcement_type'])
            priority = AnnouncementPriority(data['priority'])
        except ValueError as e:
            return jsonify({'error': f'Invalid type or priority: {str(e)}'}), 400
        
        # Create announcement
        announcement = community_service.create_announcement(
            title=data['title'],
            content=data['content'],
            municipality=data['municipality'],
            author=current_user.full_name,
            announcement_type=announcement_type,
            priority=priority,
            expires_in_days=data.get('expires_in_days'),
            areas_affected=data.get('areas_affected', []),
            contact_info=data.get('contact_info')
        )
        
        return jsonify({
            'success': True,
            'message': 'Announcement created successfully',
            'announcement': announcement.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/announcements/<announcement_id>')
@login_required  
@require_dashboard_access
def get_announcement(announcement_id):
    """Get announcement details"""
    try:
        announcement = community_service.repository.get_announcement_by_id(announcement_id)
        
        if not announcement:
            return jsonify({'error': 'Announcement not found'}), 404
        
        return jsonify({
            'success': True,
            'announcement': announcement.to_dict()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/announcements/<announcement_id>/toggle', methods=['POST'])
@login_required
@require_dashboard_access
def toggle_announcement_status(announcement_id):
    """Toggle announcement active status"""
    try:
        announcement = community_service.repository.get_announcement_by_id(announcement_id)
        
        if not announcement:
            return jsonify({'error': 'Announcement not found'}), 404
        
        # Toggle status
        announcement.is_active = not announcement.is_active
        community_service.repository.save_announcement(announcement)
        
        return jsonify({
            'success': True,
            'message': f'Announcement {"activated" if announcement.is_active else "deactivated"}',
            'is_active': announcement.is_active
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/announcements/<announcement_id>', methods=['DELETE'])
@login_required
@require_dashboard_access  
def delete_announcement(announcement_id):
    """Delete announcement"""
    try:
        # Load all announcements
        data = community_service.repository._load_data(community_service.repository.announcements_file)
        
        # Find and remove the announcement
        original_count = len(data)
        data = [item for item in data if item.get('announcement_id') != announcement_id]
        
        if len(data) == original_count:
            return jsonify({'error': 'Announcement not found'}), 404
        
        # Save updated data
        community_service.repository._save_data(community_service.repository.announcements_file, data)
        
        return jsonify({
            'success': True,
            'message': 'Announcement deleted successfully'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500