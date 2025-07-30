from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class CompetitionType(Enum):
    DOMESTIC_LEAGUE = "domestic_league"
    DOMESTIC_CUP = "domestic_cup"
    CONTINENTAL_CHAMPIONS = "continental_champions"
    CONTINENTAL_CUP = "continental_cup"
    WORLD_CHAMPIONSHIP = "world_championship"


class CompetitionStatus(Enum):
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"


class CompetitionFormat(Enum):
    LEAGUE = "league"
    KNOCKOUT = "knockout"
    GROUP_THEN_KNOCKOUT = "group_then_knockout"


@dataclass
class CompetitionFormatDetails:
    type: CompetitionFormat
    teams_count: int
    group_size: Optional[int] = None
    playoffs_teams: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.type.value,
            "teamsCount": self.teams_count,
            "groupSize": self.group_size,
            "playoffsTeams": self.playoffs_teams,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompetitionFormatDetails":
        return cls(
            type=CompetitionFormat(data["type"]),
            teams_count=data["teamsCount"],
            group_size=data.get("groupSize"),
            playoffs_teams=data.get("playoffsTeams"),
        )


@dataclass
class CompetitionParticipant:
    club_id: str
    seeded: bool = False
    group_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clubId": self.club_id,
            "seeded": self.seeded,
            "groupId": self.group_id,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompetitionParticipant":
        return cls(
            club_id=data["clubId"],
            seeded=data.get("seeded", False),
            group_id=data.get("groupId"),
        )


@dataclass
class CompetitionPrizes:
    winner: float
    runner_up: float
    third_place: float
    participation: float
    per_win: float = 0.0
    per_goal: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "winner": self.winner,
            "runnerUp": self.runner_up,
            "thirdPlace": self.third_place,
            "participation": self.participation,
            "performanceBonus": {
                "perWin": self.per_win,
                "perGoal": self.per_goal,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompetitionPrizes":
        performance_bonus = data.get("performanceBonus", {})
        return cls(
            winner=data["winner"],
            runner_up=data["runnerUp"],
            third_place=data["thirdPlace"],
            participation=data["participation"],
            per_win=performance_bonus.get("perWin", 0.0),
            per_goal=performance_bonus.get("perGoal", 0.0),
        )


@dataclass
class CompetitionStanding:
    club_id: str
    position: int
    points: int
    wins: int
    losses: int
    sets_for: int
    sets_against: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "clubId": self.club_id,
            "position": self.position,
            "points": self.points,
            "wins": self.wins,
            "losses": self.losses,
            "setsFor": self.sets_for,
            "setsAgainst": self.sets_against,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompetitionStanding":
        return cls(
            club_id=data["clubId"],
            position=data["position"],
            points=data["points"],
            wins=data["wins"],
            losses=data["losses"],
            sets_for=data["setsFor"],
            sets_against=data["setsAgainst"],
        )


@dataclass
class CompetitionResults:
    winner: Optional[str] = None
    runner_up: Optional[str] = None
    standings: List[CompetitionStanding] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "winner": self.winner,
            "runnerUp": self.runner_up,
            "standings": [standing.to_dict() for standing in self.standings],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CompetitionResults":
        standings = [
            CompetitionStanding.from_dict(s) for s in data.get("standings", [])
        ]
        return cls(
            winner=data.get("winner"),
            runner_up=data.get("runnerUp"),
            standings=standings,
        )


@dataclass
class Competition:
    id: str
    name: str
    type: CompetitionType
    continent: str
    season_id: str
    country_id: Optional[str] = None
    division_tier: Optional[int] = None
    format: Optional[CompetitionFormatDetails] = None
    participants: List[CompetitionParticipant] = field(default_factory=list)
    prizes: Optional[CompetitionPrizes] = None
    status: CompetitionStatus = CompetitionStatus.UPCOMING
    current_round: Optional[str] = None
    results: Optional[CompetitionResults] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert Competition to dictionary for Firestore storage"""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "continent": self.continent,
            "seasonId": self.season_id,
            "countryId": self.country_id,
            "divisionTier": self.division_tier,
            "format": self.format.to_dict() if self.format else None,
            "participants": [p.to_dict() for p in self.participants],
            "prizes": self.prizes.to_dict() if self.prizes else None,
            "status": self.status.value,
            "currentRound": self.current_round,
            "results": self.results.to_dict() if self.results else None,
            "createdAt": (self.created_at.isoformat() if self.created_at else None),
            "updatedAt": (self.updated_at.isoformat() if self.updated_at else None),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Competition":
        """Create Competition from Firestore dictionary"""
        format_details = None
        if data.get("format"):
            format_details = CompetitionFormatDetails.from_dict(data["format"])

        participants = [
            CompetitionParticipant.from_dict(p) for p in data.get("participants", [])
        ]

        prizes = None
        if data.get("prizes"):
            prizes = CompetitionPrizes.from_dict(data["prizes"])

        results = None
        if data.get("results"):
            results = CompetitionResults.from_dict(data["results"])

        return cls(
            id=data["id"],
            name=data["name"],
            type=CompetitionType(data["type"]),
            continent=data["continent"],
            season_id=data["seasonId"],
            country_id=data.get("countryId"),
            division_tier=data.get("divisionTier"),
            format=format_details,
            participants=participants,
            prizes=prizes,
            status=CompetitionStatus(data.get("status", "upcoming")),
            current_round=data.get("currentRound"),
            results=results,
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
