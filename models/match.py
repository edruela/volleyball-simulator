from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class MatchStatus(Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class MatchResult:
    winner: Optional[str] = None
    home_sets: int = 0
    away_sets: int = 0
    sets_details: List[Dict[str, int]] = field(default_factory=list)
    duration_minutes: int = 0
    attendance: int = 0
    revenue: Optional[Dict[str, float]] = None
    home_stats: Optional[Dict[str, Any]] = None
    away_stats: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "winner": self.winner,
            "homeSets": self.home_sets,
            "awaySets": self.away_sets,
            "setsDetails": self.sets_details,
            "durationMinutes": self.duration_minutes,
            "attendance": self.attendance,
            "revenue": self.revenue,
            "homeStats": self.home_stats,
            "awayStats": self.away_stats,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MatchResult":
        return cls(
            winner=data.get("winner"),
            home_sets=data.get("homeSets", 0),
            away_sets=data.get("awaySets", 0),
            sets_details=data.get("setsDetails", []),
            duration_minutes=data.get("durationMinutes", 0),
            attendance=data.get("attendance", 0),
            revenue=data.get("revenue"),
            home_stats=data.get("homeStats"),
            away_stats=data.get("awayStats"),
        )


@dataclass
class Match:
    id: str
    home_club_id: str
    away_club_id: str
    competition_id: str
    season_id: str
    match_day: int
    scheduled_date: datetime
    status: MatchStatus = MatchStatus.SCHEDULED
    result: Optional[MatchResult] = None
    home_tactics: Optional[Dict[str, Any]] = None
    away_tactics: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert Match to dictionary for Firestore storage"""
        return {
            "id": self.id,
            "homeClubId": self.home_club_id,
            "awayClubId": self.away_club_id,
            "competitionId": self.competition_id,
            "seasonId": self.season_id,
            "matchDay": self.match_day,
            "scheduledDate": self.scheduled_date.isoformat(),
            "status": self.status.value,
            "result": self.result.to_dict() if self.result else None,
            "homeTactics": self.home_tactics,
            "awayTactics": self.away_tactics,
            "createdAt": (self.created_at.isoformat() if self.created_at else None),
            "updatedAt": (self.updated_at.isoformat() if self.updated_at else None),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Match":
        """Create Match from Firestore dictionary"""
        result = None
        if data.get("result"):
            result = MatchResult.from_dict(data["result"])

        return cls(
            id=data["id"],
            home_club_id=data["homeClubId"],
            away_club_id=data["awayClubId"],
            competition_id=data["competitionId"],
            season_id=data["seasonId"],
            match_day=data["matchDay"],
            scheduled_date=datetime.fromisoformat(data["scheduledDate"]),
            status=MatchStatus(data.get("status", "scheduled")),
            result=result,
            home_tactics=data.get("homeTactics"),
            away_tactics=data.get("awayTactics"),
            created_at=(
                datetime.fromisoformat(data["createdAt"])
                if data.get("createdAt")
                else None
            ),
            updated_at=(
                datetime.fromisoformat(data["updatedAt"])
                if data.get("updatedAt")
                else None
            ),
        )
