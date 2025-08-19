from dataclasses import dataclass
from typing import Optional

@dataclass
class Location:
    latitude: float
    longitude: float
    province: Optional[str] = None
    district: Optional[str] = None
    municipality: Optional[str] = None
    
    def to_dict(self):
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "province": self.province,
            "district": self.district,
            "municipality": self.municipality
        }