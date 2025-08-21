"""
Advanced Analytics Service for Muni-Info Phase 3
Provides predictive insights, trend analysis, and performance metrics
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from dataclasses import dataclass
import json
import statistics

from src.models.complaint import Complaint, ComplaintStatus, ComplaintPriority
from src.services.complaint_repository import complaint_repository
from src.services.ai_service import ai_service

@dataclass
class AnalyticsInsight:
    """A single analytics insight with metadata"""
    title: str
    description: str
    value: Any
    trend: str  # 'up', 'down', 'stable'
    importance: str  # 'critical', 'high', 'medium', 'low'
    category: str
    timestamp: datetime

@dataclass
class PredictiveModel:
    """Predictive model results"""
    prediction: str
    confidence: float
    factors: List[str]
    recommended_actions: List[str]

class AdvancedAnalyticsService:
    """Advanced analytics and predictive insights service"""
    
    def __init__(self):
        self.repository = complaint_repository
        
    def get_comprehensive_dashboard(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive analytics dashboard data"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        complaints = self.repository.get_complaints_by_date_range(start_date, end_date)
        
        dashboard = {
            'overview': self._generate_overview_metrics(complaints),
            'trends': self._analyze_trends(complaints, days),
            'predictions': self._generate_predictions(complaints),
            'insights': self._generate_insights(complaints),
            'performance_metrics': self._calculate_performance_metrics(complaints),
            'geographic_analysis': self._analyze_geographic_patterns(complaints),
            'ai_effectiveness': self._analyze_ai_effectiveness(complaints),
            'recommendations': self._generate_recommendations(complaints)
        }
        
        return dashboard
    
    def _generate_overview_metrics(self, complaints: List[Complaint]) -> Dict[str, Any]:
        """Generate high-level overview metrics"""
        if not complaints:
            return {
                'total_complaints': 0,
                'resolution_rate': 0,
                'average_resolution_time': 0,
                'satisfaction_score': 0
            }
        
        resolved_complaints = [c for c in complaints if c.status == ComplaintStatus.RESOLVED]
        urgent_complaints = [c for c in complaints if c.priority == ComplaintPriority.URGENT]
        
        # Calculate average resolution time for resolved complaints
        resolution_times = []
        for complaint in resolved_complaints:
            if hasattr(complaint, 'updated_at') and complaint.updated_at:
                hours = (complaint.updated_at - complaint.timestamp).total_seconds() / 3600
                resolution_times.append(hours)
        
        avg_resolution_time = statistics.mean(resolution_times) if resolution_times else 0
        
        return {
            'total_complaints': len(complaints),
            'resolved_complaints': len(resolved_complaints),
            'resolution_rate': (len(resolved_complaints) / len(complaints) * 100) if complaints else 0,
            'urgent_complaints': len(urgent_complaints),
            'average_resolution_time': round(avg_resolution_time, 2),
            'categories': self._count_by_category(complaints),
            'status_distribution': self._count_by_status(complaints),
            'priority_distribution': self._count_by_priority(complaints)
        }
    
    def _analyze_trends(self, complaints: List[Complaint], days: int) -> Dict[str, Any]:
        """Analyze complaint trends over time"""
        if not complaints:
            return {'daily_counts': {}, 'trend_direction': 'stable', 'growth_rate': 0}
        
        # Group complaints by day
        daily_counts = defaultdict(int)
        for complaint in complaints:
            date_key = complaint.timestamp.strftime('%Y-%m-%d')
            daily_counts[date_key] += 1
        
        # Calculate trend direction
        sorted_dates = sorted(daily_counts.keys())
        if len(sorted_dates) >= 2:
            recent_avg = statistics.mean([daily_counts[d] for d in sorted_dates[-7:]])
            earlier_avg = statistics.mean([daily_counts[d] for d in sorted_dates[:-7]]) if len(sorted_dates) > 7 else recent_avg
            
            if recent_avg > earlier_avg * 1.1:
                trend_direction = 'up'
                growth_rate = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
            elif recent_avg < earlier_avg * 0.9:
                trend_direction = 'down'
                growth_rate = ((recent_avg - earlier_avg) / earlier_avg * 100) if earlier_avg > 0 else 0
            else:
                trend_direction = 'stable'
                growth_rate = 0
        else:
            trend_direction = 'stable'
            growth_rate = 0
        
        return {
            'daily_counts': dict(daily_counts),
            'trend_direction': trend_direction,
            'growth_rate': round(growth_rate, 2),
            'peak_day': max(daily_counts.keys(), key=lambda x: daily_counts[x]) if daily_counts else None,
            'category_trends': self._analyze_category_trends(complaints)
        }
    
    def _generate_predictions(self, complaints: List[Complaint]) -> Dict[str, PredictiveModel]:
        """Generate predictive insights"""
        predictions = {}
        
        # Predict volume for next 7 days
        if complaints:
            recent_complaints = [c for c in complaints if (datetime.now() - c.timestamp).days <= 7]
            avg_daily = len(recent_complaints) / 7
            predicted_volume = int(avg_daily * 7)
            
            predictions['volume'] = PredictiveModel(
                prediction=f"Expected {predicted_volume} complaints in next 7 days",
                confidence=0.75,
                factors=["Historical averages", "Recent trends"],
                recommended_actions=["Ensure adequate staffing", "Prepare resources for peak categories"]
            )
        
        # Predict category trends
        category_counts = self._count_by_category(complaints)
        if category_counts:
            trending_category = max(category_counts, key=category_counts.get)
            predictions['trending_category'] = PredictiveModel(
                prediction=f"{trending_category} complaints likely to increase",
                confidence=0.68,
                factors=[f"Current volume: {category_counts[trending_category]} complaints"],
                recommended_actions=[f"Allocate additional resources to {trending_category} department", "Proactive maintenance planning"]
            )
        
        return predictions
    
    def _generate_insights(self, complaints: List[Complaint]) -> List[AnalyticsInsight]:
        """Generate actionable insights from complaint data"""
        insights = []
        
        if not complaints:
            return insights
        
        # Resolution rate insight
        resolved = len([c for c in complaints if c.status == ComplaintStatus.RESOLVED])
        total = len(complaints)
        resolution_rate = (resolved / total * 100) if total > 0 else 0
        
        if resolution_rate < 70:
            insights.append(AnalyticsInsight(
                title="Low Resolution Rate",
                description=f"Only {resolution_rate:.1f}% of complaints are being resolved",
                value=f"{resolution_rate:.1f}%",
                trend="down",
                importance="critical",
                category="performance",
                timestamp=datetime.now()
            ))
        
        # High priority complaints insight
        urgent_count = len([c for c in complaints if c.priority == ComplaintPriority.URGENT])
        if urgent_count > total * 0.15:  # More than 15% urgent
            insights.append(AnalyticsInsight(
                title="High Urgency Rate",
                description=f"{urgent_count} urgent complaints require immediate attention",
                value=urgent_count,
                trend="up",
                importance="high",
                category="urgency",
                timestamp=datetime.now()
            ))
        
        # Category concentration insight
        category_counts = self._count_by_category(complaints)
        if category_counts:
            max_category = max(category_counts, key=category_counts.get)
            max_count = category_counts[max_category]
            if max_count > total * 0.4:  # One category dominates
                insights.append(AnalyticsInsight(
                    title="Category Concentration",
                    description=f"{max_category} complaints represent {max_count/total*100:.1f}% of all issues",
                    value=f"{max_category}: {max_count}",
                    trend="stable",
                    importance="medium",
                    category="distribution",
                    timestamp=datetime.now()
                ))
        
        return insights
    
    def _calculate_performance_metrics(self, complaints: List[Complaint]) -> Dict[str, Any]:
        """Calculate detailed performance metrics"""
        if not complaints:
            return {}
        
        metrics = {}
        
        # Resolution time by category
        resolution_times = defaultdict(list)
        for complaint in complaints:
            if complaint.status == ComplaintStatus.RESOLVED and hasattr(complaint, 'updated_at'):
                hours = (complaint.updated_at - complaint.timestamp).total_seconds() / 3600
                resolution_times[complaint.complaint_type].append(hours)
        
        metrics['resolution_times_by_category'] = {
            category: {
                'average': round(statistics.mean(times), 2),
                'median': round(statistics.median(times), 2),
                'count': len(times)
            }
            for category, times in resolution_times.items() if times
        }
        
        # SLA compliance (assuming 24h for urgent, 72h for others)
        sla_compliance = {}
        for priority in [ComplaintPriority.URGENT, ComplaintPriority.HIGH, ComplaintPriority.MEDIUM, ComplaintPriority.LOW]:
            priority_complaints = [c for c in complaints if c.priority == priority and c.status == ComplaintStatus.RESOLVED]
            if priority_complaints:
                sla_hours = 24 if priority == ComplaintPriority.URGENT else 72
                compliant = 0
                for complaint in priority_complaints:
                    if hasattr(complaint, 'updated_at'):
                        hours = (complaint.updated_at - complaint.timestamp).total_seconds() / 3600
                        if hours <= sla_hours:
                            compliant += 1
                
                sla_compliance[priority.value] = {
                    'compliance_rate': (compliant / len(priority_complaints) * 100),
                    'total': len(priority_complaints),
                    'compliant': compliant
                }
        
        metrics['sla_compliance'] = sla_compliance
        
        return metrics
    
    def _analyze_geographic_patterns(self, complaints: List[Complaint]) -> Dict[str, Any]:
        """Analyze geographic patterns in complaints"""
        geographic_data = {}
        
        # Group by municipality/area
        area_counts = defaultdict(int)
        category_by_area = defaultdict(lambda: defaultdict(int))
        
        for complaint in complaints:
            if complaint.location_info:
                area = complaint.location_info.get('municipality', 'Unknown')
                area_counts[area] += 1
                category_by_area[area][complaint.complaint_type] += 1
        
        geographic_data = {
            'complaints_by_area': dict(area_counts),
            'category_by_area': {area: dict(categories) for area, categories in category_by_area.items()},
            'hotspots': sorted(area_counts.keys(), key=lambda x: area_counts[x], reverse=True)[:5]
        }
        
        return geographic_data
    
    def _analyze_ai_effectiveness(self, complaints: List[Complaint]) -> Dict[str, Any]:
        """Analyze the effectiveness of AI categorization and prioritization"""
        ai_stats = {
            'total_analyzed': 0,
            'category_accuracy': 0,
            'priority_accuracy': 0,
            'high_confidence_predictions': 0,
            'category_corrections': []
        }
        
        analyzed_complaints = [c for c in complaints if hasattr(c, 'ai_analysis') and c.ai_analysis]
        ai_stats['total_analyzed'] = len(analyzed_complaints)
        
        if analyzed_complaints:
            high_confidence = len([c for c in analyzed_complaints 
                                 if c.ai_analysis.get('category_confidence', 0) > 0.8])
            ai_stats['high_confidence_predictions'] = (high_confidence / len(analyzed_complaints) * 100)
            
            # Track category corrections (simplified)
            corrections = []
            for complaint in analyzed_complaints:
                ai_category = complaint.ai_analysis.get('category')
                actual_category = complaint.complaint_type
                if ai_category and ai_category != actual_category:
                    corrections.append({
                        'ai_suggested': ai_category,
                        'actual': actual_category,
                        'confidence': complaint.ai_analysis.get('category_confidence', 0)
                    })
            
            ai_stats['category_corrections'] = corrections[:10]  # Limit to 10 examples
        
        return ai_stats
    
    def _generate_recommendations(self, complaints: List[Complaint]) -> List[str]:
        """Generate actionable recommendations based on analysis"""
        recommendations = []
        
        if not complaints:
            return ["No complaints to analyze - ensure reporting systems are functioning"]
        
        # Category-based recommendations
        category_counts = self._count_by_category(complaints)
        if category_counts:
            top_category = max(category_counts, key=category_counts.get)
            count = category_counts[top_category]
            
            if count > len(complaints) * 0.3:
                recommendations.append(
                    f"Focus on {top_category} department - {count} complaints ({count/len(complaints)*100:.1f}% of total)"
                )
        
        # Urgency recommendations
        urgent_count = len([c for c in complaints if c.priority == ComplaintPriority.URGENT])
        if urgent_count > len(complaints) * 0.1:
            recommendations.append(
                f"Review emergency response procedures - {urgent_count} urgent complaints need immediate attention"
            )
        
        # Resolution rate recommendations
        resolved = len([c for c in complaints if c.status == ComplaintStatus.RESOLVED])
        resolution_rate = (resolved / len(complaints) * 100)
        if resolution_rate < 60:
            recommendations.append(
                f"Improve resolution processes - current rate is {resolution_rate:.1f}% (target: >80%)"
            )
        
        # AI recommendations
        analyzed_count = len([c for c in complaints if hasattr(c, 'ai_analysis') and c.ai_analysis])
        if analyzed_count < len(complaints) * 0.8:
            recommendations.append(
                "Increase AI analysis coverage for better insights and automated routing"
            )
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _count_by_category(self, complaints: List[Complaint]) -> Dict[str, int]:
        """Count complaints by category"""
        return dict(Counter(c.complaint_type for c in complaints))
    
    def _count_by_status(self, complaints: List[Complaint]) -> Dict[str, int]:
        """Count complaints by status"""
        return dict(Counter(c.status.value for c in complaints))
    
    def _count_by_priority(self, complaints: List[Complaint]) -> Dict[str, int]:
        """Count complaints by priority"""
        return dict(Counter(c.priority.value for c in complaints))
    
    def _analyze_category_trends(self, complaints: List[Complaint]) -> Dict[str, str]:
        """Analyze trends for each category"""
        category_trends = {}
        
        # Group complaints by category and week
        end_date = datetime.now()
        mid_date = end_date - timedelta(weeks=2)
        
        recent_counts = defaultdict(int)
        older_counts = defaultdict(int)
        
        for complaint in complaints:
            category = complaint.complaint_type
            if complaint.timestamp > mid_date:
                recent_counts[category] += 1
            else:
                older_counts[category] += 1
        
        for category in set(list(recent_counts.keys()) + list(older_counts.keys())):
            recent = recent_counts[category]
            older = older_counts[category]
            
            if older == 0:
                trend = 'new' if recent > 0 else 'stable'
            elif recent > older * 1.2:
                trend = 'increasing'
            elif recent < older * 0.8:
                trend = 'decreasing'
            else:
                trend = 'stable'
            
            category_trends[category] = trend
        
        return category_trends

# Global analytics service instance
analytics_service = AdvancedAnalyticsService()