import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from dataclasses import dataclass

from models.season import Season, SeasonStatus
from models.competition import (
    Competition,
    CompetitionType,
    CompetitionStatus,
    CompetitionFormatDetails,
    CompetitionFormat,
    CompetitionPrizes,
    CompetitionParticipant,
)
from utils.constants import COUNTRIES, GAME_CONFIG
from utils.firestore_helpers import FirestoreHelper


@dataclass
class SeasonCreationResult:
    season_id: str
    competitions_created: int
    participating_countries: List[str]
    success: bool
    message: str


class SeasonManager:
    """Manages season creation and competition scheduling"""

    def __init__(self, firestore_helper: FirestoreHelper):
        self.firestore_helper = firestore_helper
        self.season_config = cast(Dict[str, Any], GAME_CONFIG["SEASON"])

    def create_season(
        self,
        season_name: str,
        duration_minutes: int,
        participating_countries: Optional[List[str]] = None,
    ) -> SeasonCreationResult:
        """
        Create a new season with all competitions scheduled

        Args:
            season_name: Name of the season
            duration_minutes: Duration of the season in minutes
            participating_countries: List of country IDs to include
                (defaults to all)

        Returns:
            SeasonCreationResult with creation details
        """
        try:
            if participating_countries is None:
                participating_countries = list(COUNTRIES.keys())

            invalid_countries = [
                c for c in participating_countries if c not in COUNTRIES
            ]
            if invalid_countries:
                return SeasonCreationResult(
                    season_id="",
                    competitions_created=0,
                    participating_countries=[],
                    success=False,
                    message=f"Invalid countries: {invalid_countries}",
                )

            season_id = str(uuid.uuid4())
            season = Season(
                id=season_id,
                name=season_name,
                duration_minutes=duration_minutes,
                start_date=datetime.now(),
                status=SeasonStatus.UPCOMING,
                participating_countries=participating_countries,
            )

            season_saved = self.firestore_helper.create_season_object(season)
            if not season_saved:
                return SeasonCreationResult(
                    season_id="",
                    competitions_created=0,
                    participating_countries=[],
                    success=False,
                    message="Failed to create season in database",
                )

            competitions_created = 0

            for country_id in participating_countries:
                domestic_competitions = self._schedule_domestic_competitions(
                    season_id, country_id
                )
                competitions_created += len(domestic_competitions)

            continental_competitions = self._schedule_continental_competitions(
                season_id, participating_countries
            )
            competitions_created += len(continental_competitions)

            self._schedule_matches_for_season(season_id, participating_countries)
            
            return SeasonCreationResult(
                season_id=season_id,
                competitions_created=competitions_created,
                participating_countries=participating_countries,
                success=True,
                message=f"Season '{season_name}' created successfully with "
                f"{competitions_created} competitions",
            )

        except Exception as e:
            return SeasonCreationResult(
                season_id="",
                competitions_created=0,
                participating_countries=[],
                success=False,
                message=f"Error creating season: {str(e)}",
            )

    def _schedule_matches_for_season(self, season_id: str, participating_countries: List[str]):
        """Schedule matches for all competitions in the season"""
        try:
            competitions = self.firestore_helper.get_all_competitions()
            season_competitions = [c for c in competitions if c.get("seasonId") == season_id]
            
            for competition in season_competitions:
                if competition.get("type") == "domestic_league":
                    self._schedule_league_matches(competition, season_id)
                    
        except Exception as e:
            print(f"Error scheduling matches for season: {e}")

    def _schedule_league_matches(self, competition: Dict[str, Any], season_id: str):
        """Schedule matches for a league competition using round-robin format"""
        try:
            participants = competition.get("participants", [])
            if len(participants) < 2:
                return
                
            club_ids = [p["clubId"] for p in participants]
            competition_id = competition["id"]
            
            match_day = 1
            matches_per_round = len(club_ids) // 2
            total_rounds = (len(club_ids) - 1) * 2
            
            for round_num in range(total_rounds):
                for match_num in range(matches_per_round):
                    home_idx = match_num
                    away_idx = len(club_ids) - 1 - match_num
                    
                    if round_num % 2 == 0:
                        home_club_id = club_ids[home_idx]
                        away_club_id = club_ids[away_idx]
                    else:
                        home_club_id = club_ids[away_idx]
                        away_club_id = club_ids[home_idx]
                    
                    if home_club_id != away_club_id:
                        match_data = {
                            "homeClubId": home_club_id,
                            "awayClubId": away_club_id,
                            "competitionId": competition_id,
                            "seasonId": season_id,
                            "matchDay": match_day,
                            "scheduledDate": datetime.now().isoformat(),
                            "status": "scheduled"
                        }
                        
                        self.firestore_helper.save_scheduled_match(match_data)
                
                club_ids = [club_ids[0]] + [club_ids[-1]] + club_ids[1:-1]
                match_day += 1
                
        except Exception as e:
            print(f"Error scheduling league matches: {e}")

    def _schedule_domestic_competitions(
        self, season_id: str, country_id: str
    ) -> List[Competition]:
        """Schedule domestic league and cup competitions for a country"""
        competitions = []
        country_name = COUNTRIES[country_id]["name"]

        for tier in range(1, self.season_config["TOTAL_DIVISIONS"] + 1):
            clubs = self.firestore_helper.get_clubs_by_country_and_tier(
                country_id, tier
            )

            if not clubs:
                continue

            competition_id = str(uuid.uuid4())
            league_name = f"{country_name} Division {tier} League"

            participants = [
                CompetitionParticipant(club_id=club["id"]) for club in clubs
            ]

            base_prize = max(10000, 1000000 - (tier * 50000))
            prizes = CompetitionPrizes(
                winner=base_prize,
                runner_up=base_prize * 0.6,
                third_place=base_prize * 0.3,
                participation=base_prize * 0.1,
                per_win=base_prize * 0.05,
            )

            competition = Competition(
                id=competition_id,
                name=league_name,
                type=CompetitionType.DOMESTIC_LEAGUE,
                continent="euralia",
                season_id=season_id,
                country_id=country_id,
                division_tier=tier,
                format=CompetitionFormatDetails(
                    type=CompetitionFormat.LEAGUE,
                    teams_count=len(participants),
                ),
                participants=participants,
                prizes=prizes,
                status=CompetitionStatus.UPCOMING,
            )

            if self.firestore_helper.create_competition_object(competition):
                competitions.append(competition)

        cup_competition = self._create_national_cup(season_id, country_id)
        if cup_competition:
            competitions.append(cup_competition)

        return competitions

    def _create_national_cup(
        self, season_id: str, country_id: str
    ) -> Optional[Competition]:
        """Create national cup competition for a country"""
        country_name = COUNTRIES[country_id]["name"]

        all_clubs = []
        for tier in range(1, self.season_config["TOTAL_DIVISIONS"] + 1):
            clubs = self.firestore_helper.get_clubs_by_country_and_tier(
                country_id, tier
            )
            all_clubs.extend(clubs)

        if not all_clubs:
            return None

        competition_id = str(uuid.uuid4())
        cup_name = f"{country_name} National Cup"

        participants = [
            CompetitionParticipant(
                club_id=club["id"],
                seeded=(
                    club.get("divisionTier", 19) <= 5
                ),  # Top 5 divisions are seeded
            )
            for club in all_clubs
        ]

        prizes = CompetitionPrizes(
            winner=5000000,
            runner_up=2000000,
            third_place=1000000,
            participation=50000,
            per_win=100000,
        )

        competition = Competition(
            id=competition_id,
            name=cup_name,
            type=CompetitionType.DOMESTIC_CUP,
            continent="euralia",
            season_id=season_id,
            country_id=country_id,
            format=CompetitionFormatDetails(
                type=CompetitionFormat.KNOCKOUT, teams_count=len(participants)
            ),
            participants=participants,
            prizes=prizes,
            status=CompetitionStatus.UPCOMING,
        )

        if self.firestore_helper.create_competition_object(competition):
            return competition

        return None

    def _schedule_continental_competitions(
        self, season_id: str, participating_countries: List[str]
    ) -> List[Competition]:
        """Schedule continental competitions"""
        competitions = []

        champions_league = self._create_continental_champions_league(
            season_id, participating_countries
        )
        if champions_league:
            competitions.append(champions_league)

        professional_cup = self._create_continental_professional_cup(
            season_id, participating_countries
        )
        if professional_cup:
            competitions.append(professional_cup)

        amateur_championship = self._create_continental_amateur_championship(
            season_id, participating_countries
        )
        if amateur_championship:
            competitions.append(amateur_championship)

        return competitions

    def _create_continental_champions_league(
        self, season_id: str, participating_countries: List[str]
    ) -> Optional[Competition]:
        """Create Continental Champions League"""
        elite_clubs = []
        for country_id in participating_countries:
            clubs = self.firestore_helper.get_clubs_by_country_and_tier(country_id, 1)
            elite_clubs.extend(clubs)

        if not elite_clubs:
            return None

        competition_id = str(uuid.uuid4())
        participants = [
            CompetitionParticipant(club_id=club["id"], seeded=True)
            for club in elite_clubs
        ]

        config = self.season_config["CONTINENTAL_COMPETITIONS"]["CHAMPIONS_LEAGUE"]

        competition = Competition(
            id=competition_id,
            name="Continental Champions League",
            type=CompetitionType.CONTINENTAL_CHAMPIONS,
            continent="euralia",
            season_id=season_id,
            format=CompetitionFormatDetails(
                type=CompetitionFormat.GROUP_THEN_KNOCKOUT,
                teams_count=len(participants),
                group_size=4,
                playoffs_teams=16,
            ),
            participants=participants,
            prizes=CompetitionPrizes(
                winner=config["WINNER_PRIZE"],
                runner_up=config["WINNER_PRIZE"] * 0.5,
                third_place=config["WINNER_PRIZE"] * 0.25,
                participation=config["PRIZE_POOL"] * 0.1 / len(participants),
                per_win=1000000,
            ),
            status=CompetitionStatus.UPCOMING,
        )

        if self.firestore_helper.create_competition_object(competition):
            return competition

        return None

    def _create_continental_professional_cup(
        self, season_id: str, participating_countries: List[str]
    ) -> Optional[Competition]:
        """Create Continental Professional Cup"""
        professional_clubs = []
        for country_id in participating_countries:
            clubs = self.firestore_helper.get_clubs_by_country_and_tier(country_id, 2)
            professional_clubs.extend(clubs)

        if not professional_clubs:
            return None

        competition_id = str(uuid.uuid4())
        participants = [
            CompetitionParticipant(club_id=club["id"]) for club in professional_clubs
        ]

        config = self.season_config["CONTINENTAL_COMPETITIONS"]["PROFESSIONAL_CUP"]

        competition = Competition(
            id=competition_id,
            name="Continental Professional Cup",
            type=CompetitionType.CONTINENTAL_CUP,
            continent="euralia",
            season_id=season_id,
            format=CompetitionFormatDetails(
                type=CompetitionFormat.GROUP_THEN_KNOCKOUT,
                teams_count=len(participants),
                group_size=4,
                playoffs_teams=8,
            ),
            participants=participants,
            prizes=CompetitionPrizes(
                winner=config["WINNER_PRIZE"],
                runner_up=config["WINNER_PRIZE"] * 0.5,
                third_place=config["WINNER_PRIZE"] * 0.25,
                participation=config["PRIZE_POOL"] * 0.1 / len(participants),
                per_win=500000,
            ),
            status=CompetitionStatus.UPCOMING,
        )

        if self.firestore_helper.create_competition_object(competition):
            return competition

        return None

    def _create_continental_amateur_championship(
        self, season_id: str, participating_countries: List[str]
    ) -> Optional[Competition]:
        """Create Continental Amateur Championship"""
        amateur_clubs = []
        for country_id in participating_countries:
            clubs = self.firestore_helper.get_clubs_by_country_and_tier(country_id, 10)
            if clubs:
                amateur_clubs.append(clubs[0])

        if not amateur_clubs:
            return None

        competition_id = str(uuid.uuid4())
        participants = [
            CompetitionParticipant(club_id=club["id"]) for club in amateur_clubs
        ]

        config = self.season_config["CONTINENTAL_COMPETITIONS"]["AMATEUR_CHAMPIONSHIP"]

        competition = Competition(
            id=competition_id,
            name="Continental Amateur Championship",
            type=CompetitionType.CONTINENTAL_CUP,
            continent="euralia",
            season_id=season_id,
            format=CompetitionFormatDetails(
                type=CompetitionFormat.KNOCKOUT, teams_count=len(participants)
            ),
            participants=participants,
            prizes=CompetitionPrizes(
                winner=config["WINNER_PRIZE"],
                runner_up=config["WINNER_PRIZE"] * 0.4,
                third_place=config["WINNER_PRIZE"] * 0.2,
                participation=config["PRIZE_POOL"] * 0.05 / len(participants),
            ),
            status=CompetitionStatus.UPCOMING,
        )

        if self.firestore_helper.create_competition_object(competition):
            return competition

        return None
