"""
Club data model and operations
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ClubFinances:
    balance: float
    weekly_revenue: float
    weekly_expenses: float
    transfer_budget: float
    debt_level: float = 0.0


@dataclass
class ClubFacilities:
    stadium_capacity: int
    stadium_name: str
    training_level: int = 1
    youth_academy: int = 0
    medical_facilities: int = 1


@dataclass
class ClubStats:
    wins: int = 0
    losses: int = 0
    sets_won: int = 0
    sets_lost: int = 0
    position: int = 0
    points: int = 0


@dataclass
class ClubTactics:
    formation: str = "5-1"
    intensity: float = 1.0
    style: str = "balanced"


@dataclass
class Club:
    id: str
    name: str
    short_name: str
    country_id: str
    division_tier: int
    owner_id: Optional[str] = None
    is_player_club: bool = False
    founded_year: int = 2024
    colors: Optional[Dict[str, str]] = None
    finances: Optional[ClubFinances] = None
    facilities: Optional[ClubFacilities] = None
    stats: Optional[ClubStats] = None
    default_tactics: Optional[ClubTactics] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.colors is None:
            self.colors = {
                "primary": "#FF0000",
                "secondary": "#FFFFFF",
                "accent": "#000000",
            }

        if self.finances is None:
            base_revenue = max(5000, 500000 - (self.division_tier * 25000))
            self.finances = ClubFinances(
                balance=500000,  # Starting balance
                weekly_revenue=base_revenue / 52,
                weekly_expenses=base_revenue * 0.8 / 52,
                transfer_budget=100000,
            )

        if self.facilities is None:
            capacity = max(500, 10000 - (self.division_tier * 400))
            self.facilities = ClubFacilities(
                stadium_capacity=capacity,
                stadium_name=f"{self.name} Arena",
                training_level=max(1, 6 - (self.division_tier // 3)),
                youth_academy=max(0, 5 - (self.division_tier // 4)),
                medical_facilities=max(1, 6 - (self.division_tier // 3)),
            )

        if self.stats is None:
            self.stats = ClubStats()

        if self.default_tactics is None:
            self.default_tactics = ClubTactics()

        if self.created_at is None:
            self.created_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert club to dictionary for Firestore storage"""
        assert self.created_at is not None
        data = asdict(self)
        data["countryId"] = data.pop("country_id")
        data["divisionTier"] = data.pop("division_tier")
        data["ownerId"] = data.pop("owner_id")
        data["isPlayerClub"] = data.pop("is_player_club")
        data["foundedYear"] = data.pop("founded_year")
        data["defaultTactics"] = data.pop("default_tactics")
        data["createdAt"] = self.created_at.isoformat()

        if "facilities" in data and isinstance(data["facilities"], dict):
            facilities = data["facilities"]
            facilities["stadiumCapacity"] = facilities.pop("stadium_capacity")
            facilities["stadiumName"] = facilities.pop("stadium_name")
            facilities["trainingLevel"] = facilities.pop("training_level")
            facilities["youthAcademy"] = facilities.pop("youth_academy")
            facilities["medicalFacilities"] = facilities.pop("medical_facilities")
            data["facilities"] = facilities

        if "finances" in data and isinstance(data["finances"], dict):
            finances = data["finances"]
            finances["weeklyRevenue"] = finances.pop("weekly_revenue")
            finances["weeklyExpenses"] = finances.pop("weekly_expenses")
            finances["transferBudget"] = finances.pop("transfer_budget")
            finances["debtLevel"] = finances.pop("debt_level")
            data["finances"] = finances

        if "stats" in data and isinstance(data["stats"], dict):
            stats = data["stats"]
            stats["setsWon"] = stats.pop("sets_won")
            stats["setsLost"] = stats.pop("sets_lost")
            data["stats"] = stats

        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Club":
        """Create club from Firestore dictionary"""
        if "finances" in data and isinstance(data["finances"], dict):
            data["finances"] = ClubFinances(**data["finances"])

        if "facilities" in data and isinstance(data["facilities"], dict):
            data["facilities"] = ClubFacilities(**data["facilities"])

        if "stats" in data and isinstance(data["stats"], dict):
            data["stats"] = ClubStats(**data["stats"])

        if "default_tactics" in data and isinstance(data["default_tactics"], dict):
            data["default_tactics"] = ClubTactics(**data["default_tactics"])

        if "created_at" in data:
            data["created_at"] = datetime.fromisoformat(data["created_at"])
        elif "createdAt" in data:
            data["created_at"] = datetime.fromisoformat(data["createdAt"])
            del data["createdAt"]

        return cls(**data)

    def update_stats(self, won: bool, sets_for: int, sets_against: int):
        """Update club stats after a match"""
        assert self.stats is not None
        if won:
            self.stats.wins += 1
            self.stats.points += 3
        else:
            self.stats.losses += 1

        self.stats.sets_won += sets_for
        self.stats.sets_lost += sets_against

    def get_overall_rating(self) -> float:
        """Calculate overall club rating based on facilities and finances"""
        assert self.facilities is not None
        assert self.finances is not None
        facility_rating = (
            self.facilities.training_level * 10
            + self.facilities.youth_academy * 5
            + self.facilities.medical_facilities * 5
        ) / 3

        financial_rating = min(100, self.finances.balance / 10000)

        tier_bonus = max(0, 100 - (self.division_tier * 5))

        return (facility_rating + financial_rating + tier_bonus) / 3
