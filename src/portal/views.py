from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from src.services.complaint_service import complaint_service
from src.services.community_service import community_service
from src.services.location_service import location_service
from src.models.complaint import ComplaintPriority

portal_bp = Blueprint('portal', __name__, url_prefix='/portal')

@portal_bp.route('/')
def index():
    """Public portal homepage"""
    recent_announcements = community_service.repository.get_active_announcements(limit=5)
    
    # Get some basic stats for display
    stats = complaint_service.repository.get_statistics()
    
    return render_template('portal/index.html', 
                         announcements=recent_announcements,
                         stats=stats)

@portal_bp.route('/complaints/submit', methods=['GET', 'POST'])
def submit_complaint():
    """Public complaint submission form"""
    if request.method == 'POST':
        phone_number = request.form.get('phone_number')
        complaint_type = request.form.get('complaint_type')
        description = request.form.get('description')
        priority = request.form.get('priority', 'medium')
        
        # Basic validation
        if not all([phone_number, complaint_type, description]):
            flash('All fields are required', 'error')
            return render_template('portal/submit_complaint.html')
        
        try:
            priority_enum = ComplaintPriority(priority)
            
            complaint = complaint_service.create_complaint(
                sender=phone_number,
                complaint_type=complaint_type,
                description=description,
                priority=priority_enum
            )
            
            flash(f'Complaint submitted successfully! Reference: {complaint.reference_id}', 'success')
            return redirect(url_for('portal.complaint_status', reference_id=complaint.reference_id))
            
        except Exception as e:
            flash(f'Error submitting complaint: {str(e)}', 'error')
    
    return render_template('portal/submit_complaint.html')

@portal_bp.route('/complaints/status')
@portal_bp.route('/complaints/status/<reference_id>')
def complaint_status(reference_id=None):
    """Check complaint status"""
    complaint = None
    
    if reference_id:
        complaint = complaint_service.get_complaint_by_reference(reference_id)
        if not complaint:
            flash('Complaint not found', 'error')
    
    elif request.args.get('reference_id'):
        reference_id = request.args.get('reference_id')
        complaint = complaint_service.get_complaint_by_reference(reference_id)
        if not complaint:
            flash('Complaint not found', 'error')
    
    return render_template('portal/complaint_status.html', 
                         complaint=complaint,
                         reference_id=reference_id)

@portal_bp.route('/services')
def services():
    """Municipal services information"""
    return render_template('portal/services.html')

@portal_bp.route('/services/rate', methods=['GET', 'POST'])
def rate_service():
    """Rate municipal services"""
    if request.method == 'POST':
        service_type = request.form.get('service_type')
        rating = request.form.get('rating')
        municipality = request.form.get('municipality')
        phone_number = request.form.get('phone_number')
        comment = request.form.get('comment')
        
        if not all([service_type, rating, municipality, phone_number]):
            flash('All required fields must be filled', 'error')
            return render_template('portal/rate_service.html')
        
        try:
            rating_value = int(rating)
            if rating_value < 1 or rating_value > 5:
                raise ValueError()
        except (TypeError, ValueError):
            flash('Rating must be between 1 and 5', 'error')
            return render_template('portal/rate_service.html')
        
        try:
            community_service.submit_rating(
                service_type=service_type,
                rating=rating_value,
                municipality=municipality,
                user_phone=phone_number,
                comment=comment
            )
            
            flash('Thank you for your rating!', 'success')
            return redirect(url_for('portal.services'))
            
        except Exception as e:
            flash(f'Error submitting rating: {str(e)}', 'error')
    
    return render_template('portal/rate_service.html')

@portal_bp.route('/announcements')
def announcements():
    """View community announcements"""
    municipality = request.args.get('municipality')
    announcements = community_service.repository.get_active_announcements(
        municipality=municipality, 
        limit=50
    )
    
    return render_template('portal/announcements.html', 
                         announcements=announcements,
                         selected_municipality=municipality)

@portal_bp.route('/location')
def location_lookup():
    """Location identification tool"""
    result = None
    
    if request.args.get('lat') and request.args.get('lon'):
        try:
            lat = float(request.args.get('lat'))
            lon = float(request.args.get('lon'))
            
            location = location_service.get_location_from_coordinates(lat, lon)
            result = location
            
        except (TypeError, ValueError):
            flash('Invalid coordinates provided', 'error')
    
    return render_template('portal/location.html', location=result)

@portal_bp.route('/emergency')
def emergency_services():
    """Emergency services information"""
    return render_template('portal/emergency.html')

@portal_bp.route('/about')
def about():
    """About Muni-Info"""
    return render_template('portal/about.html')

@portal_bp.route('/api-docs')
def api_docs():
    """API Documentation for developers"""
    return render_template('portal/api_docs.html')