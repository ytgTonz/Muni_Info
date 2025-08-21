"""
Performance Monitoring and Alerting Service for Muni-Info Phase 3
Real-time monitoring, alerting, and system health tracking
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import time
import json
import os

from src.models.complaint import Complaint, ComplaintStatus, ComplaintPriority
from src.services.complaint_repository import complaint_repository
from src.services.analytics_service import analytics_service
from src.services.routing_service import routing_service

class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning" 
    ERROR = "error"
    CRITICAL = "critical"

class HealthStatus(Enum):
    """System health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"

@dataclass
class Metric:
    """Performance metric data point"""
    name: str
    value: float
    unit: str
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class Alert:
    """Alert notification"""
    id: str
    level: AlertLevel
    title: str
    message: str
    source: str
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class HealthCheck:
    """System health check result"""
    component: str
    status: HealthStatus
    response_time: float
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)

class PerformanceMonitor:
    """Real-time performance monitoring and alerting system"""
    
    def __init__(self):
        self.metrics_history: List[Metric] = []
        self.active_alerts: Dict[str, Alert] = {}
        self.resolved_alerts: List[Alert] = []
        self.health_checks: Dict[str, HealthCheck] = {}
        
        # Monitoring thresholds
        self.thresholds = {
            'complaint_volume_spike': {'threshold': 50, 'window_minutes': 60},
            'resolution_rate_drop': {'threshold': 60, 'window_hours': 24},
            'response_time_high': {'threshold': 2000, 'unit': 'ms'},
            'urgent_complaints_high': {'threshold': 10, 'window_hours': 1},
            'system_cpu_high': {'threshold': 80, 'unit': 'percent'},
            'memory_usage_high': {'threshold': 85, 'unit': 'percent'},
            'disk_usage_high': {'threshold': 90, 'unit': 'percent'},
            'failed_requests': {'threshold': 5, 'window_minutes': 10}
        }
        
        # Performance targets
        self.sla_targets = {
            'urgent_response_time': 1,    # 1 hour
            'high_response_time': 4,      # 4 hours
            'medium_response_time': 24,   # 24 hours
            'resolution_rate': 85,        # 85%
            'uptime': 99.5,              # 99.5%
            'api_response_time': 500      # 500ms
        }
        
        self.monitoring_start_time = datetime.now()
        
    def collect_system_metrics(self) -> List[Metric]:
        """Collect system performance metrics"""
        current_time = datetime.now()
        metrics = []
        
        # Complaint metrics
        complaints_last_hour = self.get_complaints_in_timeframe(timedelta(hours=1))
        complaints_last_day = self.get_complaints_in_timeframe(timedelta(days=1))
        
        metrics.extend([
            Metric("complaints_per_hour", len(complaints_last_hour), "count"),
            Metric("complaints_per_day", len(complaints_last_day), "count"),
            Metric("active_complaints", self.get_active_complaints_count(), "count"),
            Metric("urgent_complaints", self.get_urgent_complaints_count(), "count")
        ])
        
        # Resolution metrics
        resolution_rate = self.calculate_resolution_rate()
        avg_resolution_time = self.calculate_avg_resolution_time()
        
        metrics.extend([
            Metric("resolution_rate", resolution_rate, "percent"),
            Metric("avg_resolution_time", avg_resolution_time, "hours")
        ])
        
        # System health metrics (simulated - in real system would use actual monitoring)
        metrics.extend([
            Metric("api_response_time", self.simulate_api_response_time(), "ms"),
            Metric("system_uptime", self.calculate_uptime(), "percent"),
            Metric("memory_usage", self.simulate_memory_usage(), "percent"),
            Metric("cpu_usage", self.simulate_cpu_usage(), "percent"),
            Metric("active_sessions", len(getattr(routing_service, 'staff', {})), "count")
        ])
        
        # AI service metrics
        ai_metrics = self.collect_ai_metrics()
        metrics.extend(ai_metrics)
        
        # Store metrics
        self.metrics_history.extend(metrics)
        
        # Clean old metrics (keep last 24 hours)
        cutoff_time = current_time - timedelta(hours=24)
        self.metrics_history = [m for m in self.metrics_history if m.timestamp > cutoff_time]
        
        return metrics
    
    def collect_ai_metrics(self) -> List[Metric]:
        """Collect AI service performance metrics"""
        # Get recent complaints with AI analysis
        recent_complaints = complaint_repository.get_recent_complaints(1)  # Last day
        ai_analyzed = [c for c in recent_complaints if hasattr(c, 'ai_analysis') and c.ai_analysis]
        
        if not recent_complaints:
            return []
        
        ai_coverage = len(ai_analyzed) / len(recent_complaints) * 100
        
        # Calculate average confidence
        confidence_scores = []
        for complaint in ai_analyzed:
            if 'category_confidence' in complaint.ai_analysis:
                confidence_scores.append(complaint.ai_analysis['category_confidence'])
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0
        
        return [
            Metric("ai_analysis_coverage", ai_coverage, "percent"),
            Metric("ai_avg_confidence", avg_confidence * 100, "percent"),
            Metric("ai_analyzed_complaints", len(ai_analyzed), "count")
        ]
    
    def check_system_health(self) -> Dict[str, HealthCheck]:
        """Perform comprehensive system health checks"""
        health_checks = {}
        
        # Database health
        db_health = self.check_database_health()
        health_checks['database'] = db_health
        
        # API health
        api_health = self.check_api_health()
        health_checks['api'] = api_health
        
        # AI service health
        ai_health = self.check_ai_service_health()
        health_checks['ai_service'] = ai_health
        
        # Routing service health
        routing_health = self.check_routing_service_health()
        health_checks['routing_service'] = routing_health
        
        # Overall system health
        overall_health = self.determine_overall_health(health_checks)
        health_checks['overall'] = overall_health
        
        self.health_checks = health_checks
        return health_checks
    
    def detect_anomalies_and_alert(self, metrics: List[Metric]):
        """Detect anomalies in metrics and generate alerts"""
        for metric in metrics:
            self.check_metric_thresholds(metric)
        
        # Complex anomaly detection
        self.check_complaint_volume_spikes()
        self.check_resolution_rate_drops()
        self.check_urgent_complaint_accumulation()
        self.check_system_degradation()
    
    def check_metric_thresholds(self, metric: Metric):
        """Check if metric exceeds thresholds"""
        threshold_key = None
        threshold_config = None
        
        # Map metric to threshold
        if metric.name == "api_response_time" and metric.value > self.thresholds['response_time_high']['threshold']:
            self.create_alert(
                "api_response_time_high",
                AlertLevel.WARNING,
                "High API Response Time",
                f"API response time is {metric.value:.0f}ms (threshold: {self.thresholds['response_time_high']['threshold']}ms)",
                "performance_monitor",
                {'metric': metric.name, 'value': metric.value}
            )
        
        elif metric.name == "memory_usage" and metric.value > self.thresholds['memory_usage_high']['threshold']:
            level = AlertLevel.CRITICAL if metric.value > 95 else AlertLevel.WARNING
            self.create_alert(
                "memory_usage_high",
                level,
                "High Memory Usage",
                f"Memory usage is {metric.value:.1f}% (threshold: {self.thresholds['memory_usage_high']['threshold']}%)",
                "performance_monitor",
                {'metric': metric.name, 'value': metric.value}
            )
        
        elif metric.name == "cpu_usage" and metric.value > self.thresholds['system_cpu_high']['threshold']:
            level = AlertLevel.CRITICAL if metric.value > 95 else AlertLevel.WARNING
            self.create_alert(
                "cpu_usage_high",
                level,
                "High CPU Usage",
                f"CPU usage is {metric.value:.1f}% (threshold: {self.thresholds['system_cpu_high']['threshold']}%)",
                "performance_monitor",
                {'metric': metric.name, 'value': metric.value}
            )
    
    def check_complaint_volume_spikes(self):
        """Check for sudden spikes in complaint volume"""
        current_hour_complaints = self.get_complaints_in_timeframe(timedelta(hours=1))
        threshold = self.thresholds['complaint_volume_spike']['threshold']
        
        if len(current_hour_complaints) > threshold:
            self.create_alert(
                "complaint_volume_spike",
                AlertLevel.WARNING,
                "Complaint Volume Spike Detected",
                f"Received {len(current_hour_complaints)} complaints in the last hour (threshold: {threshold})",
                "performance_monitor",
                {'count': len(current_hour_complaints), 'threshold': threshold}
            )
    
    def check_resolution_rate_drops(self):
        """Check for drops in resolution rate"""
        complaints_24h = self.get_complaints_in_timeframe(timedelta(hours=24))
        if not complaints_24h:
            return
        
        resolved_count = len([c for c in complaints_24h if c.status == ComplaintStatus.RESOLVED])
        resolution_rate = (resolved_count / len(complaints_24h)) * 100
        threshold = self.thresholds['resolution_rate_drop']['threshold']
        
        if resolution_rate < threshold:
            self.create_alert(
                "resolution_rate_drop",
                AlertLevel.ERROR,
                "Low Resolution Rate",
                f"Resolution rate is {resolution_rate:.1f}% in last 24h (threshold: {threshold}%)",
                "performance_monitor",
                {'rate': resolution_rate, 'threshold': threshold}
            )
    
    def check_urgent_complaint_accumulation(self):
        """Check for accumulation of urgent complaints"""
        urgent_complaints = self.get_complaints_by_priority(ComplaintPriority.URGENT, timedelta(hours=1))
        threshold = self.thresholds['urgent_complaints_high']['threshold']
        
        if len(urgent_complaints) > threshold:
            self.create_alert(
                "urgent_complaints_accumulation",
                AlertLevel.CRITICAL,
                "High Urgent Complaints",
                f"{len(urgent_complaints)} urgent complaints in the last hour (threshold: {threshold})",
                "performance_monitor",
                {'count': len(urgent_complaints), 'threshold': threshold}
            )
    
    def check_system_degradation(self):
        """Check for overall system performance degradation"""
        recent_metrics = [m for m in self.metrics_history if 
                         (datetime.now() - m.timestamp).total_seconds() < 300]  # Last 5 minutes
        
        # Check multiple degradation indicators
        degradation_indicators = 0
        
        for metric in recent_metrics:
            if metric.name == "api_response_time" and metric.value > 1000:
                degradation_indicators += 1
            elif metric.name == "memory_usage" and metric.value > 90:
                degradation_indicators += 1
            elif metric.name == "cpu_usage" and metric.value > 90:
                degradation_indicators += 1
        
        if degradation_indicators >= 2:
            self.create_alert(
                "system_degradation",
                AlertLevel.ERROR,
                "System Performance Degradation",
                f"Multiple performance indicators suggest system degradation",
                "performance_monitor",
                {'indicators': degradation_indicators}
            )
    
    def create_alert(self, alert_id: str, level: AlertLevel, title: str, message: str, 
                    source: str, metadata: Dict[str, Any] = None):
        """Create and store an alert"""
        if alert_id in self.active_alerts:
            # Update existing alert
            self.active_alerts[alert_id].timestamp = datetime.now()
            self.active_alerts[alert_id].metadata.update(metadata or {})
        else:
            # Create new alert
            alert = Alert(
                id=alert_id,
                level=level,
                title=title,
                message=message,
                source=source,
                metadata=metadata or {}
            )
            self.active_alerts[alert_id] = alert
            
            # Log alert (in real system would also send notifications)
            print(f"[{level.value.upper()}] {title}: {message}")
    
    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an active alert"""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolution_time = datetime.now()
            
            # Move to resolved alerts
            self.resolved_alerts.append(alert)
            del self.active_alerts[alert_id]
            
            print(f"[RESOLVED] {alert.title}")
            return True
        return False
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        current_metrics = self.collect_system_metrics()
        health_status = self.check_system_health()
        
        # Calculate SLA compliance
        sla_compliance = self.calculate_sla_compliance()
        
        # Get recent trends
        trends = self.calculate_trends()
        
        return {
            'current_metrics': {m.name: {'value': m.value, 'unit': m.unit} for m in current_metrics},
            'health_status': {k: {'status': v.status.value, 'message': v.message} for k, v in health_status.items()},
            'active_alerts': [
                {
                    'id': alert.id,
                    'level': alert.level.value,
                    'title': alert.title,
                    'message': alert.message,
                    'timestamp': alert.timestamp.isoformat()
                }
                for alert in self.active_alerts.values()
            ],
            'sla_compliance': sla_compliance,
            'trends': trends,
            'recommendations': self.generate_recommendations()
        }
    
    def calculate_sla_compliance(self) -> Dict[str, float]:
        """Calculate SLA compliance metrics"""
        compliance = {}
        
        # Response time compliance
        recent_complaints = complaint_repository.get_recent_complaints(7)  # Last week
        
        for priority in [ComplaintPriority.URGENT, ComplaintPriority.HIGH, ComplaintPriority.MEDIUM]:
            priority_complaints = [c for c in recent_complaints if c.priority == priority]
            if not priority_complaints:
                compliance[f"{priority.value}_response_sla"] = 100.0
                continue
            
            target_hours = self.sla_targets.get(f"{priority.value}_response_time", 24)
            compliant_count = 0
            
            for complaint in priority_complaints:
                if complaint.status != ComplaintStatus.SUBMITTED:
                    response_hours = (complaint.updated_at - complaint.timestamp).total_seconds() / 3600
                    if response_hours <= target_hours:
                        compliant_count += 1
            
            compliance[f"{priority.value}_response_sla"] = (compliant_count / len(priority_complaints)) * 100
        
        # Resolution rate compliance
        resolved_complaints = [c for c in recent_complaints if c.status == ComplaintStatus.RESOLVED]
        resolution_rate = (len(resolved_complaints) / len(recent_complaints)) * 100 if recent_complaints else 0
        compliance['resolution_rate_sla'] = min(100, (resolution_rate / self.sla_targets['resolution_rate']) * 100)
        
        # System uptime compliance
        uptime = self.calculate_uptime()
        compliance['uptime_sla'] = min(100, (uptime / self.sla_targets['uptime']) * 100)
        
        return compliance
    
    def calculate_trends(self) -> Dict[str, str]:
        """Calculate trends for key metrics"""
        trends = {}
        
        # Get metrics from last 2 hours vs previous 2 hours
        now = datetime.now()
        recent_window = now - timedelta(hours=2)
        previous_window = recent_window - timedelta(hours=2)
        
        recent_metrics = [m for m in self.metrics_history if m.timestamp > recent_window]
        previous_metrics = [m for m in self.metrics_history if previous_window < m.timestamp <= recent_window]
        
        for metric_name in ['complaints_per_hour', 'resolution_rate', 'api_response_time']:
            recent_values = [m.value for m in recent_metrics if m.name == metric_name]
            previous_values = [m.value for m in previous_metrics if m.name == metric_name]
            
            if recent_values and previous_values:
                recent_avg = sum(recent_values) / len(recent_values)
                previous_avg = sum(previous_values) / len(previous_values)
                
                if recent_avg > previous_avg * 1.1:
                    trends[metric_name] = 'up'
                elif recent_avg < previous_avg * 0.9:
                    trends[metric_name] = 'down'
                else:
                    trends[metric_name] = 'stable'
            else:
                trends[metric_name] = 'stable'
        
        return trends
    
    def generate_recommendations(self) -> List[str]:
        """Generate operational recommendations based on monitoring data"""
        recommendations = []
        
        # Check active alerts for recommendations
        if any(alert.level == AlertLevel.CRITICAL for alert in self.active_alerts.values()):
            recommendations.append("🔴 Critical alerts active - immediate attention required")
        
        # Check system health
        unhealthy_components = [name for name, health in self.health_checks.items() 
                              if health.status in [HealthStatus.UNHEALTHY, HealthStatus.CRITICAL]]
        if unhealthy_components:
            recommendations.append(f"⚠️ Unhealthy components: {', '.join(unhealthy_components)}")
        
        # Check complaint volume
        recent_complaints = self.get_complaints_in_timeframe(timedelta(hours=1))
        if len(recent_complaints) > 30:
            recommendations.append("📈 High complaint volume - consider additional staff allocation")
        
        # Check urgent complaints
        urgent_complaints = [c for c in recent_complaints if c.priority == ComplaintPriority.URGENT]
        if len(urgent_complaints) > 5:
            recommendations.append("🚨 High number of urgent complaints - prioritize emergency response")
        
        # Check resolution rate
        resolution_rate = self.calculate_resolution_rate()
        if resolution_rate < 70:
            recommendations.append("📉 Low resolution rate - review complaint handling processes")
        
        return recommendations[:5]  # Top 5 recommendations
    
    # Helper methods
    def get_complaints_in_timeframe(self, timeframe: timedelta) -> List[Complaint]:
        """Get complaints within timeframe"""
        cutoff = datetime.now() - timeframe
        return complaint_repository.get_recent_complaints(timeframe.days + 1)
    
    def get_active_complaints_count(self) -> int:
        """Get count of active complaints"""
        active_statuses = [ComplaintStatus.SUBMITTED, ComplaintStatus.IN_PROGRESS, ComplaintStatus.UNDER_REVIEW]
        # Simplified - in real system would query database
        return 25  # Mock value
    
    def get_urgent_complaints_count(self) -> int:
        """Get count of urgent complaints"""
        recent_complaints = self.get_complaints_in_timeframe(timedelta(hours=24))
        return len([c for c in recent_complaints if c.priority == ComplaintPriority.URGENT])
    
    def get_complaints_by_priority(self, priority: ComplaintPriority, timeframe: timedelta) -> List[Complaint]:
        """Get complaints by priority within timeframe"""
        complaints = self.get_complaints_in_timeframe(timeframe)
        return [c for c in complaints if c.priority == priority]
    
    def calculate_resolution_rate(self) -> float:
        """Calculate resolution rate for recent complaints"""
        recent_complaints = self.get_complaints_in_timeframe(timedelta(days=7))
        if not recent_complaints:
            return 0.0
        
        resolved_count = len([c for c in recent_complaints if c.status == ComplaintStatus.RESOLVED])
        return (resolved_count / len(recent_complaints)) * 100
    
    def calculate_avg_resolution_time(self) -> float:
        """Calculate average resolution time in hours"""
        recent_resolved = complaint_repository.get_recent_complaints(7)
        resolved_complaints = [c for c in recent_resolved if c.status == ComplaintStatus.RESOLVED]
        
        if not resolved_complaints:
            return 0.0
        
        total_hours = 0
        for complaint in resolved_complaints:
            if hasattr(complaint, 'updated_at'):
                hours = (complaint.updated_at - complaint.timestamp).total_seconds() / 3600
                total_hours += hours
        
        return total_hours / len(resolved_complaints)
    
    def calculate_uptime(self) -> float:
        """Calculate system uptime percentage"""
        # Simplified calculation - in real system would track actual downtime
        running_time = (datetime.now() - self.monitoring_start_time).total_seconds()
        # Assume 99.9% uptime for simulation
        return 99.9
    
    def simulate_api_response_time(self) -> float:
        """Simulate API response time"""
        import random
        # Simulate realistic response times with occasional spikes
        base_time = random.normalvariate(300, 50)  # Normal 300ms ± 50ms
        if random.random() < 0.05:  # 5% chance of spike
            base_time += random.uniform(500, 2000)
        return max(50, base_time)
    
    def simulate_memory_usage(self) -> float:
        """Simulate memory usage"""
        import random
        return random.uniform(45, 75)  # 45-75% usage
    
    def simulate_cpu_usage(self) -> float:
        """Simulate CPU usage"""
        import random
        return random.uniform(25, 60)  # 25-60% usage
    
    def check_database_health(self) -> HealthCheck:
        """Check database health"""
        start_time = time.time()
        try:
            # Test database connectivity
            complaints = complaint_repository.get_recent_complaints(1)
            response_time = (time.time() - start_time) * 1000
            
            return HealthCheck(
                component="database",
                status=HealthStatus.HEALTHY,
                response_time=response_time,
                message="Database is responding normally",
                details={'query_time_ms': response_time}
            )
        except Exception as e:
            return HealthCheck(
                component="database",
                status=HealthStatus.CRITICAL,
                response_time=(time.time() - start_time) * 1000,
                message=f"Database error: {str(e)}",
                details={'error': str(e)}
            )
    
    def check_api_health(self) -> HealthCheck:
        """Check API health"""
        # Simulate API health check
        response_time = self.simulate_api_response_time()
        
        if response_time < 1000:
            status = HealthStatus.HEALTHY
            message = "API is responding normally"
        elif response_time < 2000:
            status = HealthStatus.DEGRADED
            message = "API response time is elevated"
        else:
            status = HealthStatus.UNHEALTHY
            message = "API response time is critically high"
        
        return HealthCheck(
            component="api",
            status=status,
            response_time=response_time,
            message=message,
            details={'avg_response_time_ms': response_time}
        )
    
    def check_ai_service_health(self) -> HealthCheck:
        """Check AI service health"""
        try:
            # Test AI service by analyzing a sample complaint
            test_analysis = analytics_service.ai_service.analyze_complaint("Test complaint about water")
            
            return HealthCheck(
                component="ai_service",
                status=HealthStatus.HEALTHY,
                response_time=50,  # Simulated
                message="AI service is functioning normally",
                details={'confidence': test_analysis.confidence}
            )
        except Exception as e:
            return HealthCheck(
                component="ai_service",
                status=HealthStatus.UNHEALTHY,
                response_time=0,
                message=f"AI service error: {str(e)}",
                details={'error': str(e)}
            )
    
    def check_routing_service_health(self) -> HealthCheck:
        """Check routing service health"""
        try:
            # Test routing service
            status = routing_service.get_department_status()
            
            return HealthCheck(
                component="routing_service",
                status=HealthStatus.HEALTHY,
                response_time=25,  # Simulated
                message="Routing service is functioning normally",
                details={'departments': len(status)}
            )
        except Exception as e:
            return HealthCheck(
                component="routing_service",
                status=HealthStatus.UNHEALTHY,
                response_time=0,
                message=f"Routing service error: {str(e)}",
                details={'error': str(e)}
            )
    
    def determine_overall_health(self, health_checks: Dict[str, HealthCheck]) -> HealthCheck:
        """Determine overall system health"""
        component_statuses = [hc.status for name, hc in health_checks.items() if name != 'overall']
        
        if any(status == HealthStatus.CRITICAL for status in component_statuses):
            overall_status = HealthStatus.CRITICAL
            message = "One or more critical components are unhealthy"
        elif any(status == HealthStatus.UNHEALTHY for status in component_statuses):
            overall_status = HealthStatus.UNHEALTHY
            message = "Some components are unhealthy"
        elif any(status == HealthStatus.DEGRADED for status in component_statuses):
            overall_status = HealthStatus.DEGRADED
            message = "Some components are experiencing degraded performance"
        else:
            overall_status = HealthStatus.HEALTHY
            message = "All systems are healthy"
        
        return HealthCheck(
            component="overall",
            status=overall_status,
            response_time=0,
            message=message,
            details={'components_checked': len(component_statuses)}
        )

# Global monitoring service instance
monitoring_service = PerformanceMonitor()