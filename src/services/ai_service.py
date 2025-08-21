"""
AI Service for Muni-Info Phase 3
Provides intelligent complaint analysis, categorization, and routing
"""

import re
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class AIAnalysisResult:
    """Result of AI analysis on a complaint"""
    category: str
    confidence: float
    priority: str
    priority_confidence: float
    department: str
    suggested_response: str
    keywords: List[str]
    urgency_indicators: List[str]

class AIService:
    """AI-powered complaint analysis and categorization service"""
    
    def __init__(self):
        self.category_keywords = {
            'Water': [
                'water', 'tap', 'pipe', 'leak', 'burst', 'pressure', 'supply', 'outage',
                'draining', 'flooding', 'sewage', 'drainage', 'blockage', 'smell',
                'contaminated', 'dirty', 'brown', 'chlorine'
            ],
            'Electricity': [
                'power', 'electricity', 'outage', 'blackout', 'transformer', 'cable',
                'pole', 'meter', 'billing', 'streetlight', 'lighting', 'voltage',
                'electrical', 'spark', 'wire', 'connection'
            ],
            'Roads': [
                'road', 'street', 'pothole', 'tar', 'asphalt', 'traffic', 'sign',
                'marking', 'intersection', 'sidewalk', 'pavement', 'crossing',
                'bridge', 'surface', 'crack', 'repair'
            ],
            'Sanitation': [
                'garbage', 'trash', 'refuse', 'collection', 'bin', 'dump', 'litter',
                'cleaning', 'sweep', 'toilet', 'public', 'hygiene', 'waste',
                'recycling', 'landfill'
            ],
            'Housing': [
                'housing', 'rdp', 'house', 'building', 'construction', 'maintenance',
                'repair', 'roof', 'window', 'door', 'structure', 'property'
            ],
            'Parks': [
                'park', 'garden', 'playground', 'grass', 'tree', 'maintenance',
                'recreation', 'facility', 'sport', 'field', 'bench'
            ]
        }
        
        self.urgency_keywords = {
            'urgent': [
                'emergency', 'urgent', 'immediate', 'dangerous', 'hazard', 'risk',
                'injury', 'accident', 'fire', 'explosion', 'gas', 'toxic',
                'flooding', 'burst', 'collapse'
            ],
            'high': [
                'major', 'serious', 'important', 'critical', 'affecting many',
                'whole area', 'community', 'health', 'safety', 'children'
            ],
            'medium': [
                'issue', 'problem', 'concern', 'request', 'help', 'fix',
                'repair', 'maintenance', 'service'
            ],
            'low': [
                'minor', 'small', 'cosmetic', 'aesthetic', 'suggestion',
                'improvement', 'enhancement', 'when possible'
            ]
        }
        
        self.department_mapping = {
            'Water': 'Water and Sanitation Department',
            'Electricity': 'Electrical Services Department', 
            'Roads': 'Roads and Infrastructure Department',
            'Sanitation': 'Waste Management Department',
            'Housing': 'Human Settlements Department',
            'Parks': 'Parks and Recreation Department',
            'Other': 'General Services Department'
        }
        
        self.response_templates = {
            'Water': {
                'urgent': "Thank you for reporting this urgent water issue. We have escalated this to our emergency response team and will dispatch a technician within 2 hours.",
                'high': "We have received your water service complaint and assigned it high priority. Our team will investigate within 24 hours.",
                'medium': "Thank you for your water service report. We will address this issue within 48-72 hours.",
                'low': "We have logged your water service concern and will include it in our scheduled maintenance program."
            },
            'Electricity': {
                'urgent': "This electrical issue has been marked as urgent for safety reasons. Our emergency electrical team has been notified and will respond immediately.",
                'high': "Your electrical service complaint has been prioritized. We will dispatch a technician within 4 hours.",
                'medium': "Thank you for reporting this electrical issue. We will schedule a repair within 24-48 hours.",
                'low': "We have noted your electrical service concern and will address it during routine maintenance."
            },
            'Roads': {
                'urgent': "This road hazard has been flagged as urgent. Our emergency road crew will respond within 4 hours to make the area safe.",
                'high': "Your road infrastructure complaint has been given high priority. We will assess and begin repairs within 48 hours.",
                'medium': "Thank you for reporting this road issue. It has been added to our maintenance schedule for completion within 1-2 weeks.",
                'low': "We have logged your road maintenance request for inclusion in our next scheduled road works."
            },
            'Sanitation': {
                'urgent': "This sanitation issue poses a health risk and has been escalated immediately. Our team will respond within 4 hours.",
                'high': "We have prioritized your sanitation complaint. Our waste management team will address this within 24 hours.",
                'medium': "Thank you for your sanitation service report. We will resolve this issue within 48 hours.",
                'low': "Your sanitation concern has been logged and will be addressed during our next scheduled service."
            }
        }

    def analyze_complaint(self, description: str, location: str = "", complaint_type: str = "") -> AIAnalysisResult:
        """
        Analyze complaint text using AI-like algorithms
        Returns comprehensive analysis including category, priority, and routing
        """
        description_lower = description.lower()
        location_lower = location.lower() if location else ""
        full_text = f"{description_lower} {location_lower}"
        
        # 1. Smart Categorization
        category, category_confidence = self._categorize_complaint(full_text)
        
        # 2. Intelligent Priority Detection
        priority, priority_confidence = self._determine_priority(full_text)
        
        # 3. Department Routing
        department = self.department_mapping.get(category, 'General Services Department')
        
        # 4. Extract Keywords
        keywords = self._extract_keywords(full_text, category)
        
        # 5. Identify Urgency Indicators
        urgency_indicators = self._identify_urgency_indicators(full_text)
        
        # 6. Generate Response Suggestion
        suggested_response = self._generate_response(category, priority)
        
        return AIAnalysisResult(
            category=category,
            confidence=category_confidence,
            priority=priority,
            priority_confidence=priority_confidence,
            department=department,
            suggested_response=suggested_response,
            keywords=keywords,
            urgency_indicators=urgency_indicators
        )

    def _categorize_complaint(self, text: str) -> Tuple[str, float]:
        """Categorize complaint using keyword matching and patterns"""
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                # Count occurrences with weight for exact matches
                count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
                score += count * (1.5 if len(keyword) > 4 else 1.0)
            
            category_scores[category] = score
        
        if not category_scores or max(category_scores.values()) == 0:
            return 'Other', 0.5
        
        best_category = max(category_scores, key=category_scores.get)
        max_score = category_scores[best_category]
        
        # Calculate confidence based on score distribution
        total_score = sum(category_scores.values())
        confidence = min(0.95, max_score / total_score) if total_score > 0 else 0.5
        
        return best_category, confidence

    def _determine_priority(self, text: str) -> Tuple[str, float]:
        """Determine priority level using urgency indicators"""
        priority_scores = {}
        
        for priority, keywords in self.urgency_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    # Weight longer, more specific keywords higher
                    weight = len(keyword) / 5.0
                    count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', text))
                    score += count * weight
            
            priority_scores[priority] = score
        
        # Additional pattern-based priority detection
        if re.search(r'(can\'t|cannot|no|not|stop|broken|burst|leak)', text):
            priority_scores['high'] = priority_scores.get('high', 0) + 2
        
        if re.search(r'(days?|weeks?|months?).*ago', text):
            priority_scores['medium'] = priority_scores.get('medium', 0) + 1
        
        if not priority_scores or max(priority_scores.values()) == 0:
            return 'medium', 0.6
        
        best_priority = max(priority_scores, key=priority_scores.get)
        max_score = priority_scores[best_priority]
        
        # Calculate confidence
        total_score = sum(priority_scores.values())
        confidence = min(0.9, max_score / total_score) if total_score > 0 else 0.6
        
        return best_priority, confidence

    def _extract_keywords(self, text: str, category: str) -> List[str]:
        """Extract relevant keywords from complaint text"""
        keywords = []
        category_words = self.category_keywords.get(category, [])
        
        for keyword in category_words:
            if keyword in text:
                keywords.append(keyword)
        
        # Extract additional meaningful words
        words = re.findall(r'\b\w{4,}\b', text)
        for word in words[:5]:  # Limit to 5 additional keywords
            if word not in keywords and len(word) > 3:
                keywords.append(word)
        
        return keywords[:10]  # Limit total keywords

    def _identify_urgency_indicators(self, text: str) -> List[str]:
        """Identify specific urgency indicators in the text"""
        indicators = []
        
        for priority, keywords in self.urgency_keywords.items():
            for keyword in keywords:
                if keyword in text and keyword not in indicators:
                    indicators.append(keyword)
        
        return indicators[:5]  # Limit to 5 indicators

    def _generate_response(self, category: str, priority: str) -> str:
        """Generate contextual response based on category and priority"""
        templates = self.response_templates.get(category, {})
        
        if priority in templates:
            return templates[priority]
        
        # Fallback generic responses
        fallback_responses = {
            'urgent': "Thank you for your urgent report. We are treating this as high priority and will respond immediately.",
            'high': "We have received your complaint and assigned it high priority. Our team will address this within 24 hours.",
            'medium': "Thank you for your report. We will investigate and respond within 48-72 hours.",
            'low': "We have logged your concern and will address it as part of our routine maintenance schedule."
        }
        
        return fallback_responses.get(priority, "Thank you for your complaint. We will investigate and respond appropriately.")

    def get_trending_issues(self, complaints: List[Dict]) -> Dict[str, int]:
        """Analyze trending issues from complaint data"""
        trending = {}
        
        for complaint in complaints:
            description = complaint.get('description', '')
            analysis = self.analyze_complaint(description)
            
            category = analysis.category
            trending[category] = trending.get(category, 0) + 1
        
        # Sort by frequency
        return dict(sorted(trending.items(), key=lambda x: x[1], reverse=True))

    def predict_resolution_time(self, category: str, priority: str) -> str:
        """Predict resolution time based on category and priority"""
        time_matrix = {
            'Water': {
                'urgent': '2-4 hours',
                'high': '4-24 hours', 
                'medium': '1-3 days',
                'low': '3-7 days'
            },
            'Electricity': {
                'urgent': '1-2 hours',
                'high': '4-8 hours',
                'medium': '1-2 days', 
                'low': '2-5 days'
            },
            'Roads': {
                'urgent': '4-8 hours',
                'high': '1-2 days',
                'medium': '1-2 weeks',
                'low': '2-4 weeks'
            },
            'Sanitation': {
                'urgent': '2-4 hours',
                'high': '8-24 hours',
                'medium': '1-2 days',
                'low': '2-7 days'
            }
        }
        
        return time_matrix.get(category, {}).get(priority, '2-7 days')

# Global AI service instance
ai_service = AIService()