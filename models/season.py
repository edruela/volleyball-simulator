from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class SeasonStatus(Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"


@dataclass
class Season:
    id: str
    name: str
    duration_minutes: int
    start_date: datetime
    status: SeasonStatus = SeasonStatus.UPCOMING
    participating_countries: List[str] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Season to dictionary for Firestore storage"""
        return {
            "id": self.id,
            "name": self.name,
            "durationMinutes": self.duration_minutes,
            "startDate": self.start_date.isoformat(),
            "status": self.status.value,
            "participatingCountries": self.participating_countries,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "updatedAt": self.updated_at.isoformat() if self.updated_at else None,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Season":
        """Create Season from Firestore dictionary"""
        return cls(
            id=data["id"],
            name=data["name"],
            duration_minutes=data["durationMinutes"],
            start_date=datetime.fromisoformat(data["startDate"]),
            status=SeasonStatus(data["status"]),
            participating_countries=data.get("participatingCountries", []),
            created_at=datetime.fromisoformat(data["createdAt"]) if data.get("createdAt") else None,
            updated_at=datetime.fromisoformat(data["updatedAt"]) if data.get("updatedAt") else None,
        )
