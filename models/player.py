"""
Player data model and operations
"""

from typing import Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import random


@dataclass
class PlayerAttributes:
    spike_power: int = 50
    spike_accuracy: int = 50
    block_timing: int = 50
    passing_accuracy: int = 50
    setting_precision: int = 50
    serve_power: int = 50
    serve_accuracy: int = 50
    court_vision: int = 50
    decision_making: int = 50
    communication: int = 50

    stamina: int = 50
    strength: int = 50
    agility: int = 50
    jump_height: int = 50
    speed: int = 50


@dataclass
class PlayerCondition:
    fatigue: int = 0  # 0-100
    fitness: int = 100  # 0-100
    morale: int = 75  # 0-100
    injury: Optional[Dict[str, Any]] = None


@dataclass
class PlayerContract:
    salary: int
    years_remaining: int
    bonus_clause: int = 0
    transfer_clause: int = 0


@dataclass
class PlayerStats:
    matches_played: int = 0
    sets_played: int = 0
    points: int = 0
    kills: int = 0
    blocks: int = 0
    aces: int = 0
    digs: int = 0
    assists: int = 0


@dataclass
class Player:
    id: str
    first_name: str
    last_name: str
    club_id: str
    country_id: str
    age: int
    position: str  # 'OH', 'MB', 'OPP', 'S', 'L', 'DS'
    attributes: PlayerAttributes
    condition: PlayerCondition
    contract: PlayerContract
    stats: PlayerStats
    nickname: Optional[str] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def full_name(self) -> str:
        """Get player's full name"""
        if self.nickname:
            return f"{self.first_name} '{self.nickname}' {self.last_name}"
        return f"{self.first_name} {self.last_name}"

    @property
    def display_name(self) -> str:
        """Get player's display name"""
        return self.nickname if self.nickname else f"{self.first_name} {self.last_name}"

    def get_overall_rating(self) -> int:
        """Calculate overall player rating based on position and attributes"""
        attrs = self.attributes

        if self.position == "OH":  # Outside Hitter
            rating = (
                attrs.spike_power * 0.25
                + attrs.spike_accuracy * 0.20
                + attrs.passing_accuracy * 0.15
                + attrs.agility * 0.15
                + attrs.jump_height * 0.15
                + attrs.stamina * 0.10
            )
        elif self.position == "MB":  # Middle Blocker
            rating = (
                attrs.block_timing * 0.30
                + attrs.spike_power * 0.20
                + attrs.jump_height * 0.20
                + attrs.strength * 0.15
                + attrs.court_vision * 0.15
            )
        elif self.position == "OPP":  # Opposite Hitter
            rating = (
                attrs.spike_power * 0.30
                + attrs.spike_accuracy * 0.25
                + attrs.block_timing * 0.20
                + attrs.jump_height * 0.15
                + attrs.strength * 0.10
            )
        elif self.position == "S":  # Setter
            rating = (
                attrs.setting_precision * 0.35
                + attrs.court_vision * 0.25
                + attrs.decision_making * 0.20
                + attrs.communication * 0.15
                + attrs.agility * 0.05
            )
        elif self.position == "L":  # Libero
            rating = (
                attrs.passing_accuracy * 0.40
                + attrs.agility * 0.25
                + attrs.speed * 0.20
                + attrs.court_vision * 0.15
            )
        else:  # DS - Defensive Specialist
            rating = (
                attrs.passing_accuracy * 0.35
                + attrs.agility * 0.25
                + attrs.speed * 0.20
                + attrs.court_vision * 0.20
            )

        fitness_factor = self.condition.fitness / 100
        fatigue_factor = (100 - self.condition.fatigue) / 100
        morale_factor = self.condition.morale / 100

        final_rating = rating * fitness_factor * fatigue_factor * morale_factor

        return int(max(1, min(100, final_rating)))

    def apply_country_modifiers(self, country_modifiers: Dict[str, int]):
        """Apply country-specific attribute modifiers"""
        for attr_name, modifier in country_modifiers.items():
            if hasattr(self.attributes, attr_name):
                current_value = getattr(self.attributes, attr_name)
                new_value = max(1, min(100, current_value + modifier))
                setattr(self.attributes, attr_name, new_value)

    def develop_attributes(self, training_level: int = 1):
        """Develop player attributes based on age and training"""
        if self.age > 30:
            decline_rate = (self.age - 30) * 0.5
            for attr_name in ["stamina", "speed", "agility", "jump_height"]:
                current_value = getattr(self.attributes, attr_name)
                new_value = max(1, current_value - random.uniform(0, decline_rate))
                setattr(self.attributes, attr_name, int(new_value))
        elif self.age < 25:
            growth_rate = training_level * 0.5
            for attr_name in vars(self.attributes):
                if random.random() < 0.3:  # 30% chance to improve
                    current_value = getattr(self.attributes, attr_name)
                    improvement = random.uniform(0, growth_rate)
                    new_value = min(100, current_value + improvement)
                    setattr(self.attributes, attr_name, int(new_value))

    def recover_fatigue(self, rest_days: int = 1):
        """Recover fatigue over time"""
        recovery_rate = 15 * rest_days  # 15 points per day
        self.condition.fatigue = max(0, self.condition.fatigue - recovery_rate)

    def to_dict(self) -> Dict[str, Any]:
        """Convert player to dictionary for Firestore storage"""
        assert self.created_at is not None
        data = asdict(self)
        data["createdAt"] = self.created_at.isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Player":
        """Create player from Firestore dictionary"""
        data = data.copy()

        if "attributes" in data and isinstance(data["attributes"], dict):
            data["attributes"] = PlayerAttributes(**data["attributes"])

        if "condition" in data and isinstance(data["condition"], dict):
            data["condition"] = PlayerCondition(**data["condition"])

        if "contract" in data and isinstance(data["contract"], dict):
            data["contract"] = PlayerContract(**data["contract"])

        if "stats" in data and isinstance(data["stats"], dict):
            data["stats"] = PlayerStats(**data["stats"])

        if "created_at" in data:
            if isinstance(data["created_at"], str):
                data["created_at"] = datetime.fromisoformat(data["created_at"])
        elif "createdAt" in data:
            if isinstance(data["createdAt"], str):
                data["created_at"] = datetime.fromisoformat(data["createdAt"])
            else:
                data["created_at"] = data["createdAt"]
            del data["createdAt"]

        data.pop("createdAt", None)

        return cls(**data)

    def should_retire(self) -> bool:
        """Determine if player should retire based on age"""
        if self.age < 35:
            return False
        elif self.age >= 42:
            return True
        else:
            retirement_chance = (self.age - 35) * 0.15  # 15% per year after 35
            return random.random() < retirement_chance

    def evaluate_contract_offer(self, offered_salary: int, similar_players_avg_salary: int) -> bool:
        """Evaluate if player accepts contract renewal offer"""
        if similar_players_avg_salary == 0:
            return offered_salary >= self.contract.salary * 0.9
        
        minimum_acceptable = similar_players_avg_salary * 1.1  # 110% of average
        return offered_salary >= minimum_acceptable

    def evaluate_transfer_offer(self, offered_salary: int, target_club_tier: int, current_club_tier: int) -> bool:
        """Evaluate if player accepts transfer offer"""
        salary_improvement = offered_salary > self.contract.salary * 1.05  # At least 5% salary increase
        club_improvement = target_club_tier < current_club_tier  # Lower tier number = better division
        
        if club_improvement and salary_improvement:
            return True
        elif club_improvement:
            return target_club_tier <= current_club_tier - 2 or offered_salary >= self.contract.salary * 0.95
        elif salary_improvement:
            return offered_salary >= self.contract.salary * 1.2
        else:
            return False

    def increment_age(self):
        """Increment player age for season progression"""
        self.age += 1

    def is_professional_eligible(self) -> bool:
        """Check if player meets minimum age for professional play"""
        return self.age >= 21


def generate_random_player(
    club_id: str, country_id: str, position: str, division_tier: int = 10
) -> Player:
    """Generate a random player for a club"""

    first_names = [
        "Alex",
        "Jordan",
        "Casey",
        "Taylor",
        "Morgan",
        "Riley",
        "Avery",
        "Quinn",
        "Blake",
        "Cameron",
        "Drew",
        "Emery",
        "Finley",
        "Harper",
        "Hayden",
        "Jamie",
    ]

    last_names = [
        "Smith",
        "Johnson",
        "Williams",
        "Brown",
        "Jones",
        "Garcia",
        "Miller",
        "Davis",
        "Rodriguez",
        "Martinez",
        "Hernandez",
        "Lopez",
        "Gonzalez",
        "Wilson",
        "Anderson",
        "Thomas",
    ]

    first_name = random.choice(first_names)
    last_name = random.choice(last_names)
    age = random.randint(18, 35)

    base_skill = max(30, 80 - (division_tier * 3))  # Higher tier better
    skill_variance = 15

    attributes = PlayerAttributes()

    if position == "OH":  # Outside Hitter
        attributes.spike_power = random.randint(
            base_skill, min(100, base_skill + skill_variance)
        )
        attributes.spike_accuracy = random.randint(
            base_skill, min(100, base_skill + skill_variance)
        )
        attributes.passing_accuracy = random.randint(
            base_skill - 5, min(100, base_skill + skill_variance - 5)
        )
    elif position == "MB":  # Middle Blocker
        attributes.block_timing = random.randint(
            base_skill, min(100, base_skill + skill_variance)
        )
        attributes.spike_power = random.randint(
            base_skill - 5, min(100, base_skill + skill_variance - 5)
        )
        attributes.jump_height = random.randint(
            base_skill, min(100, base_skill + skill_variance)
        )
    elif position == "S":  # Setter
        attributes.setting_precision = random.randint(
            base_skill, min(100, base_skill + skill_variance)
        )
        attributes.court_vision = random.randint(
            base_skill, min(100, base_skill + skill_variance)
        )
        attributes.decision_making = random.randint(
            base_skill, min(100, base_skill + skill_variance)
        )
    elif position == "L":  # Libero
        attributes.passing_accuracy = random.randint(
            base_skill, min(100, base_skill + skill_variance)
        )
        attributes.agility = random.randint(
            base_skill, min(100, base_skill + skill_variance)
        )
        attributes.speed = random.randint(
            base_skill, min(100, base_skill + skill_variance)
        )

    for attr_name in vars(attributes):
        if getattr(attributes, attr_name) == 50:  # Default value
            setattr(
                attributes,
                attr_name,
                random.randint(base_skill - 10, min(100, base_skill + 5)),
            )

    base_salary = max(10000, 200000 - (division_tier * 8000))
    salary = random.randint(int(base_salary * 0.7), int(base_salary * 1.3))

    contract = PlayerContract(
        salary=salary,
        years_remaining=random.randint(1, 4),
        bonus_clause=salary // 10,
        transfer_clause=salary * 2,
    )

    return Player(
        id=f"player_{random.randint(100000, 999999)}",
        first_name=first_name,
        last_name=last_name,
        club_id=club_id,
        country_id=country_id,
        age=age,
        position=position,
        attributes=attributes,
        condition=PlayerCondition(),
        contract=contract,
        stats=PlayerStats(),
    )
