"""
Smart Complaint Routing Service for Muni-Info Phase 3
Intelligently routes complaints to appropriate departments and personnel
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import json

from src.models.complaint import Complaint, ComplaintPriority, ComplaintStatus
from src.models.user import UserRole
from src.services.ai_service import ai_service

class RoutingPriority(Enum):
    """Routing priority levels"""
    IMMEDIATE = "immediate"  # < 1 hour
    HIGH = "high"           # < 4 hours  
    NORMAL = "normal"       # < 24 hours
    LOW = "low"            # < 72 hours

@dataclass
class Department:
    """Department information"""
    name: str
    code: str
    capacity: int  # Current capacity (complaints they can handle)
    specialties: List[str]
    current_load: int = 0
    response_time_avg: float = 0.0  # Average response time in hours
    resolution_rate: float = 0.0   # Percentage of complaints resolved

@dataclass
class Staff:
    """Staff member information"""
    user_id: str
    name: str
    department: str
    skills: List[str]
    current_load: int = 0
    max_capacity: int = 10
    performance_score: float = 1.0  # Performance multiplier
    availability: bool = True

@dataclass
class RoutingDecision:
    """Routing decision result"""
    department: str
    assigned_staff: Optional[str]
    priority: RoutingPriority
    estimated_response_time: str
    confidence: float
    reasoning: List[str]

class SmartRoutingService:
    """Intelligent complaint routing service"""
    
    def __init__(self):
        # Initialize departments
        self.departments = {
            'water_sanitation': Department(
                name='Water and Sanitation Department',
                code='WSD',
                capacity=50,
                specialties=['water', 'sanitation', 'sewage', 'drainage', 'plumbing']
            ),
            'electrical': Department(
                name='Electrical Services Department', 
                code='ESD',
                capacity=30,
                specialties=['electricity', 'power', 'streetlights', 'transformer', 'outage']
            ),
            'roads_infrastructure': Department(
                name='Roads and Infrastructure Department',
                code='RID', 
                capacity=40,
                specialties=['roads', 'potholes', 'traffic', 'bridges', 'sidewalks']
            ),
            'waste_management': Department(
                name='Waste Management Department',
                code='WMD',
                capacity=25,
                specialties=['garbage', 'refuse', 'recycling', 'bins', 'collection']
            ),
            'housing': Department(
                name='Human Settlements Department',
                code='HSD',
                capacity=20,
                specialties=['housing', 'rdp', 'maintenance', 'repairs', 'construction']
            ),
            'parks_recreation': Department(
                name='Parks and Recreation Department',
                code='PRD',
                capacity=15,
                specialties=['parks', 'gardens', 'playgrounds', 'sports', 'recreation']
            ),
            'emergency_services': Department(
                name='Emergency Services Department',
                code='ESD',
                capacity=20,
                specialties=['emergency', 'fire', 'rescue', 'disaster', 'safety'],
            )
        }
        
        # Staff database (simplified - in real implementation would come from user management)
        self.staff = {}
        self.load_staff_data()
        
        # Routing rules
        self.category_to_department = {
            'Water': 'water_sanitation',
            'Electricity': 'electrical',
            'Roads': 'roads_infrastructure', 
            'Sanitation': 'waste_management',
            'Housing': 'housing',
            'Parks': 'parks_recreation',
            'Emergency': 'emergency_services',
            'Other': 'water_sanitation'  # Default fallback
        }
        
        # Priority to routing priority mapping
        self.priority_mapping = {
            ComplaintPriority.URGENT: RoutingPriority.IMMEDIATE,
            ComplaintPriority.HIGH: RoutingPriority.HIGH,
            ComplaintPriority.MEDIUM: RoutingPriority.NORMAL,
            ComplaintPriority.LOW: RoutingPriority.LOW
        }
    
    def route_complaint(self, complaint: Complaint) -> RoutingDecision:
        """
        Intelligently route complaint to appropriate department and staff
        """
        reasoning = []
        
        # Step 1: Determine department using AI analysis + category mapping
        department_code = self.determine_department(complaint, reasoning)
        
        # Step 2: Determine routing priority
        routing_priority = self.determine_routing_priority(complaint, reasoning)
        
        # Step 3: Find best available staff member
        assigned_staff = self.find_best_staff(department_code, complaint, reasoning)
        
        # Step 4: Calculate estimated response time
        estimated_time = self.calculate_response_time(department_code, routing_priority)
        
        # Step 5: Calculate confidence score
        confidence = self.calculate_confidence(complaint, department_code, assigned_staff)
        
        return RoutingDecision(
            department=self.departments[department_code].name,
            assigned_staff=assigned_staff,
            priority=routing_priority,
            estimated_response_time=estimated_time,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def determine_department(self, complaint: Complaint, reasoning: List[str]) -> str:
        """Determine the best department for the complaint"""
        # Start with category-based routing
        base_department = self.category_to_department.get(complaint.complaint_type, 'water_sanitation')
        
        # Use AI analysis if available for better routing
        if hasattr(complaint, 'ai_analysis') and complaint.ai_analysis:
            ai_category = complaint.ai_analysis.get('category')
            ai_confidence = complaint.ai_analysis.get('category_confidence', 0)
            
            if ai_category and ai_confidence > 0.8:
                ai_department = self.category_to_department.get(ai_category, base_department)
                if ai_department != base_department:
                    reasoning.append(f"AI suggested {ai_category} category with {ai_confidence:.1%} confidence")
                    base_department = ai_department
        
        # Check for emergency keywords that should go to emergency services
        emergency_keywords = ['emergency', 'fire', 'gas leak', 'explosion', 'danger', 'life threatening']
        description_lower = complaint.description.lower()
        
        for keyword in emergency_keywords:
            if keyword in description_lower:
                reasoning.append(f"Emergency keyword '{keyword}' detected - routing to emergency services")
                return 'emergency_services'
        
        # Check department capacity and suggest alternatives if overloaded
        department = self.departments[base_department]
        if department.current_load >= department.capacity * 0.9:  # 90% capacity
            alternative = self.find_alternative_department(base_department, complaint.complaint_type)
            if alternative:
                reasoning.append(f"Primary department at 90% capacity - routing to alternative")
                return alternative
        
        reasoning.append(f"Routed to {department.name} based on complaint type: {complaint.complaint_type}")
        return base_department
    
    def determine_routing_priority(self, complaint: Complaint, reasoning: List[str]) -> RoutingPriority:
        """Determine routing priority based on complaint analysis"""
        base_priority = self.priority_mapping.get(complaint.priority, RoutingPriority.NORMAL)
        
        # AI can upgrade priority based on analysis
        if hasattr(complaint, 'ai_analysis') and complaint.ai_analysis:
            urgency_indicators = complaint.ai_analysis.get('urgency_indicators', [])
            if urgency_indicators:
                critical_indicators = ['emergency', 'urgent', 'dangerous', 'burst', 'fire', 'leak']
                critical_found = any(indicator in critical_indicators for indicator in urgency_indicators)
                
                if critical_found and base_priority != RoutingPriority.IMMEDIATE:
                    reasoning.append(f"AI detected critical urgency indicators: {urgency_indicators[:3]}")
                    return RoutingPriority.IMMEDIATE
        
        # Time-based priority adjustment
        complaint_age = datetime.now() - complaint.timestamp
        if complaint_age > timedelta(hours=24) and base_priority == RoutingPriority.LOW:
            reasoning.append("Complaint is over 24 hours old - upgrading priority")
            return RoutingPriority.NORMAL
        
        return base_priority
    
    def find_best_staff(self, department_code: str, complaint: Complaint, reasoning: List[str]) -> Optional[str]:
        """Find the best available staff member for the complaint"""
        department_staff = [s for s in self.staff.values() if s.department == department_code and s.availability]
        
        if not department_staff:
            reasoning.append("No available staff in department - will assign when available")
            return None
        
        # Score each staff member
        best_staff = None
        best_score = 0
        
        for staff in department_staff:
            score = self.calculate_staff_score(staff, complaint)
            if score > best_score and staff.current_load < staff.max_capacity:
                best_score = score
                best_staff = staff
        
        if best_staff:
            reasoning.append(f"Assigned to {best_staff.name} (score: {best_score:.2f})")
            # Update staff load (simplified - in real system would be persisted)
            best_staff.current_load += 1
            return best_staff.user_id
        else:
            reasoning.append("All staff at capacity - will assign when available")
            return None
    
    def calculate_staff_score(self, staff: Staff, complaint: Complaint) -> float:
        """Calculate staff suitability score for complaint"""
        score = staff.performance_score
        
        # Skill matching bonus
        complaint_text = complaint.description.lower()
        skill_matches = sum(1 for skill in staff.skills if skill.lower() in complaint_text)
        score += skill_matches * 0.3
        
        # Load penalty (prefer less loaded staff)
        load_ratio = staff.current_load / staff.max_capacity
        score *= (1.0 - load_ratio * 0.5)
        
        return score
    
    def calculate_response_time(self, department_code: str, priority: RoutingPriority) -> str:
        """Calculate estimated response time"""
        department = self.departments[department_code]
        base_time = department.response_time_avg if department.response_time_avg > 0 else 4.0
        
        # Adjust based on priority
        priority_multipliers = {
            RoutingPriority.IMMEDIATE: 0.25,
            RoutingPriority.HIGH: 0.5,
            RoutingPriority.NORMAL: 1.0,
            RoutingPriority.LOW: 2.0
        }
        
        multiplier = priority_multipliers[priority]
        estimated_hours = base_time * multiplier
        
        # Adjust for current department load
        load_factor = department.current_load / department.capacity
        if load_factor > 0.8:
            estimated_hours *= 1.5
        elif load_factor < 0.3:
            estimated_hours *= 0.8
        
        # Format response time
        if estimated_hours < 1:
            return f"{int(estimated_hours * 60)} minutes"
        elif estimated_hours < 24:
            return f"{int(estimated_hours)} hours"
        else:
            return f"{int(estimated_hours / 24)} days"
    
    def calculate_confidence(self, complaint: Complaint, department_code: str, assigned_staff: Optional[str]) -> float:
        """Calculate confidence in routing decision"""
        confidence = 0.8  # Base confidence
        
        # AI analysis boosts confidence
        if hasattr(complaint, 'ai_analysis') and complaint.ai_analysis:
            ai_confidence = complaint.ai_analysis.get('category_confidence', 0)
            confidence += ai_confidence * 0.2
        
        # Staff assignment boosts confidence
        if assigned_staff:
            confidence += 0.1
        
        # Department capacity affects confidence
        department = self.departments[department_code]
        load_ratio = department.current_load / department.capacity
        if load_ratio > 0.8:
            confidence -= 0.2  # Overloaded department reduces confidence
        
        return min(1.0, confidence)
    
    def find_alternative_department(self, overloaded_dept: str, complaint_type: str) -> Optional[str]:
        """Find alternative department when primary is overloaded"""
        # Define department alternatives
        alternatives = {
            'water_sanitation': ['waste_management', 'roads_infrastructure'],
            'electrical': ['roads_infrastructure'],
            'roads_infrastructure': ['water_sanitation'],
            'waste_management': ['water_sanitation'],
            'housing': ['water_sanitation'],
            'parks_recreation': ['roads_infrastructure']
        }
        
        alt_depts = alternatives.get(overloaded_dept, [])
        for alt_dept in alt_depts:
            department = self.departments[alt_dept]
            if department.current_load < department.capacity * 0.7:  # Less than 70% capacity
                return alt_dept
        
        return None
    
    def update_department_metrics(self, department_code: str, resolved_complaint: Complaint):
        """Update department performance metrics after complaint resolution"""
        if department_code not in self.departments:
            return
        
        department = self.departments[department_code]
        department.current_load = max(0, department.current_load - 1)
        
        # Update response time (simplified calculation)
        if resolved_complaint.status == ComplaintStatus.RESOLVED:
            resolution_hours = (resolved_complaint.updated_at - resolved_complaint.timestamp).total_seconds() / 3600
            
            # Update rolling average
            if department.response_time_avg == 0:
                department.response_time_avg = resolution_hours
            else:
                department.response_time_avg = (department.response_time_avg * 0.8) + (resolution_hours * 0.2)
    
    def get_department_status(self) -> Dict[str, Dict]:
        """Get current status of all departments"""
        status = {}
        for code, dept in self.departments.items():
            load_percentage = (dept.current_load / dept.capacity * 100) if dept.capacity > 0 else 0
            
            status[code] = {
                'name': dept.name,
                'current_load': dept.current_load,
                'capacity': dept.capacity,
                'load_percentage': round(load_percentage, 1),
                'avg_response_time': round(dept.response_time_avg, 2),
                'resolution_rate': round(dept.resolution_rate, 1),
                'status': self.get_load_status(load_percentage)
            }
        
        return status
    
    def get_load_status(self, load_percentage: float) -> str:
        """Get load status description"""
        if load_percentage >= 90:
            return 'critical'
        elif load_percentage >= 70:
            return 'high'
        elif load_percentage >= 40:
            return 'normal'
        else:
            return 'low'
    
    def load_staff_data(self):
        """Load staff data (simplified - would come from user management in real system)"""
        # Sample staff data
        sample_staff = [
            Staff('staff_001', 'John Mbeki', 'water_sanitation', ['plumbing', 'water', 'pipes'], 2, 8, 1.2),
            Staff('staff_002', 'Sarah van der Merwe', 'electrical', ['electrical', 'power', 'wiring'], 1, 10, 1.1),
            Staff('staff_003', 'David Nkomo', 'roads_infrastructure', ['roads', 'asphalt', 'maintenance'], 3, 6, 0.9),
            Staff('staff_004', 'Lisa Patel', 'waste_management', ['waste', 'recycling', 'collection'], 1, 8, 1.3),
            Staff('staff_005', 'Mike Johnson', 'housing', ['construction', 'maintenance', 'repairs'], 0, 5, 1.0),
            Staff('staff_006', 'Thabo Mthembu', 'parks_recreation', ['landscaping', 'maintenance', 'sports'], 2, 7, 1.1),
            Staff('staff_007', 'Anna Koekemoer', 'emergency_services', ['emergency', 'fire', 'rescue'], 0, 12, 1.4)
        ]
        
        self.staff = {s.user_id: s for s in sample_staff}
    
    def get_routing_analytics(self) -> Dict[str, any]:
        """Get routing performance analytics"""
        total_staff = len(self.staff)
        available_staff = sum(1 for s in self.staff.values() if s.availability)
        total_load = sum(s.current_load for s in self.staff.values())
        total_capacity = sum(s.max_capacity for s in self.staff.values())
        
        return {
            'departments': len(self.departments),
            'total_staff': total_staff,
            'available_staff': available_staff,
            'utilization_rate': (total_load / total_capacity * 100) if total_capacity > 0 else 0,
            'department_status': self.get_department_status(),
            'recommendations': self.generate_routing_recommendations()
        }
    
    def generate_routing_recommendations(self) -> List[str]:
        """Generate recommendations for routing optimization"""
        recommendations = []
        
        # Check for overloaded departments
        for code, dept in self.departments.items():
            load_percentage = (dept.current_load / dept.capacity * 100)
            if load_percentage > 90:
                recommendations.append(f"{dept.name} is critically overloaded ({load_percentage:.1f}%) - consider reassigning staff")
            elif load_percentage > 80:
                recommendations.append(f"{dept.name} is highly loaded ({load_percentage:.1f}%) - monitor closely")
        
        # Check for underutilized departments
        underutilized = [dept for code, dept in self.departments.items() 
                        if (dept.current_load / dept.capacity * 100) < 20]
        if underutilized:
            recommendations.append(f"Consider temporary staff reassignment from underutilized departments")
        
        # Check staff utilization
        overloaded_staff = [s for s in self.staff.values() if s.current_load >= s.max_capacity]
        if overloaded_staff:
            recommendations.append(f"{len(overloaded_staff)} staff members are at maximum capacity")
        
        return recommendations[:5]  # Return top 5 recommendations

# Global routing service instance
routing_service = SmartRoutingService()