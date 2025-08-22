from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime

@dataclass
class ServiceCenter:
    name: str
    address: str
    phone: Optional[str] = None
    email: Optional[str] = None
    services: List[str] = field(default_factory=list)
    distance_km: Optional[float] = None
    coordinates: Optional[Dict[str, float]] = None
    operating_hours: Optional[str] = None
    rating: Optional[float] = None

@dataclass
class WardInfo:
    ward_number: Optional[str] = None
    councillor_name: Optional[str] = None
    councillor_party: Optional[str] = None
    councillor_contact: Optional[str] = None
    councillor_email: Optional[str] = None
    ward_office_address: Optional[str] = None
    ward_office_phone: Optional[str] = None
    ward_office_email: Optional[str] = None
    office_hours: Optional[str] = None

@dataclass
class Location:
    latitude: float
    longitude: float
    province: Optional[str] = None
    district: Optional[str] = None
    municipality: Optional[str] = None
    
    # Enhanced address information
    formatted_address: Optional[str] = None
    street_number: Optional[str] = None
    street_name: Optional[str] = None
    suburb: Optional[str] = None
    city: Optional[str] = None
    postal_code: Optional[str] = None
    
    # Administrative information
    ward_info: Optional[WardInfo] = None
    nearest_service_centers: List[ServiceCenter] = field(default_factory=list)
    
    # Metadata
    geocoding_source: Optional[str] = None
    last_updated: Optional[datetime] = None
    accuracy_radius_m: Optional[float] = None
    
    def to_dict(self):
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "province": self.province,
            "district": self.district,
            "municipality": self.municipality,
            "formatted_address": self.formatted_address,
            "street_number": self.street_number,
            "street_name": self.street_name,
            "suburb": self.suburb,
            "city": self.city,
            "postal_code": self.postal_code,
            "ward_info": self.ward_info.__dict__ if self.ward_info else None,
            "nearest_service_centers": [sc.__dict__ for sc in self.nearest_service_centers],
            "geocoding_source": self.geocoding_source,
            "last_updated": self.last_updated.isoformat() if self.last_updated else None,
            "accuracy_radius_m": self.accuracy_radius_m
        }
    
    def get_full_address(self) -> str:
        """Get a formatted full address"""
        if self.formatted_address:
            return self.formatted_address
        
        parts = []
        if self.street_number and self.street_name:
            parts.append(f"{self.street_number} {self.street_name}")
        elif self.street_name:
            parts.append(self.street_name)
        
        if self.suburb:
            parts.append(self.suburb)
        if self.city:
            parts.append(self.city)
        if self.province:
            parts.append(self.province)
        if self.postal_code:
            parts.append(self.postal_code)
        
        return ", ".join(parts) if parts else f"{self.latitude}, {self.longitude}"