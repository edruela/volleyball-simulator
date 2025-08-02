"""
Firestore database helper functions
"""

from typing import Dict, List, Optional, Any
from datetime import datetime
from google.cloud import firestore  # type: ignore
from models.club import Club
from models.player import generate_random_player, Player
import random
import uuid


class FirestoreHelper:
    """Helper class for Firestore operations"""

    def __init__(self, db: firestore.Client):
        self.db = db

    def get_club(self, club_id: str) -> Optional[Dict[str, Any]]:
        """Get club data from Firestore"""
        try:
            doc_ref = self.db.collection("clubs").document(club_id)
            doc = doc_ref.get()

            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting club {club_id}: {e}")
            return None

    def create_club(self, club_data: Dict[str, Any]) -> str:
        """Create a new club in Firestore"""
        try:
            club_id = str(uuid.uuid4())

            club = Club(
                id=club_id,
                name=club_data["name"],
                short_name=club_data.get("shortName", club_data["name"][:3].upper()),
                country_id=club_data["countryId"],
                division_tier=club_data.get(
                    "divisionTier", random.randint(10, 19)
                ),  # Start in amateur
                owner_id=club_data["ownerId"],
                is_player_club=True,
            )

            doc_ref = self.db.collection("clubs").document(club_id)
            doc_ref.set(club.to_dict())

            return club_id
        except Exception as e:
            print(f"Error creating club: {e}")
            raise

    def get_club_players(self, club_id: str) -> List[Dict[str, Any]]:
        """Get all players for a club"""
        try:
            players_ref = self.db.collection("players").where("clubId", "==", club_id)
            players = []

            for doc in players_ref.stream():
                player_data = doc.to_dict()
                player_data["id"] = doc.id
                players.append(player_data)

            return players
        except Exception as e:
            print(f"Error getting players for club {club_id}: {e}")
            return []

    def generate_initial_squad(
        self, club_id: str, country_id: str, division_tier: int = 10
    ) -> List[str]:
        """Generate initial squad of players for a new club"""
        try:
            positions = [
                "OH",
                "OH",
                "OH",  # 3 Outside Hitters
                "MB",
                "MB",  # 2 Middle Blockers
                "OPP",
                "OPP",  # 2 Opposite Hitters
                "S",
                "S",  # 2 Setters
                "L",  # 1 Libero
                "DS",
                "DS",  # 2 Defensive Specialists
            ]

            player_ids = []

            for position in positions:
                player = generate_random_player(
                    club_id, country_id, position, division_tier
                )

                doc_ref = self.db.collection("players").document(player.id)
                doc_ref.set(player.to_dict())

                player_ids.append(player.id)

            return player_ids
        except Exception as e:
            print(f"Error generating initial squad: {e}")
            raise

    def save_match(self, match_data: Dict[str, Any]) -> str:
        """Save match result to Firestore"""
        try:
            match_id = str(uuid.uuid4())
            match_data["id"] = match_id

            doc_ref = self.db.collection("matches").document(match_id)
            doc_ref.set(match_data)

            self._update_club_stats_after_match(match_data)

            return match_id
        except Exception as e:
            print(f"Error saving match: {e}")
            raise

    def _update_club_stats_after_match(self, match_data: Dict[str, Any]):
        """Update club statistics after a match"""
        try:
            home_club_id = match_data["homeClubId"]
            away_club_id = match_data["awayClubId"]
            result = match_data["result"]

            home_won = result["winner"] == "home"
            home_sets = result["homeSets"]
            away_sets = result["awaySets"]

            home_doc_ref = self.db.collection("clubs").document(home_club_id)
            home_doc = home_doc_ref.get()
            if home_doc.exists:
                home_data = home_doc.to_dict()
                stats = home_data.get("stats", {})

                if home_won:
                    stats["wins"] = stats.get("wins", 0) + 1
                    stats["points"] = stats.get("points", 0) + 3
                else:
                    stats["losses"] = stats.get("losses", 0) + 1

                stats["setsWon"] = stats.get("setsWon", 0) + home_sets
                stats["setsLost"] = stats.get("setsLost", 0) + away_sets

                home_doc_ref.update({"stats": stats})

            away_doc_ref = self.db.collection("clubs").document(away_club_id)
            away_doc = away_doc_ref.get()
            if away_doc.exists:
                away_data = away_doc.to_dict()
                stats = away_data.get("stats", {})

                if not home_won:
                    stats["wins"] = stats.get("wins", 0) + 1
                    stats["points"] = stats.get("points", 0) + 3
                else:
                    stats["losses"] = stats.get("losses", 0) + 1

                stats["setsWon"] = stats.get("setsWon", 0) + away_sets
                stats["setsLost"] = stats.get("setsLost", 0) + home_sets

                away_doc_ref.update({"stats": stats})

        except Exception as e:
            print(f"Error updating club stats: {e}")

    def get_league_standings(
        self, country_id: str, division_tier: int
    ) -> List[Dict[str, Any]]:
        """Get league standings for a specific division"""
        try:
            clubs_ref = (
                self.db.collection("clubs")
                .where("countryId", "==", country_id)
                .where("divisionTier", "==", division_tier)
            )
            standings = []

            for doc in clubs_ref.stream():
                club_data = doc.to_dict()
                club_data["id"] = doc.id

                stats = club_data.get("stats", {})
                standings.append(
                    {
                        "clubId": doc.id,
                        "name": club_data.get("name", "Unknown Club"),
                        "wins": stats.get("wins", 0),
                        "losses": stats.get("losses", 0),
                        "setsWon": stats.get("setsWon", 0),
                        "setsLost": stats.get("setsLost", 0),
                        "points": stats.get("points", 0),
                    }
                )

            standings.sort(
                key=lambda x: (x["points"], x["setsWon"] - x["setsLost"]), reverse=True
            )

            for i, club in enumerate(standings):
                club["position"] = i + 1

            return standings
        except Exception as e:
            print(f"Error getting league standings: {e}")
            return []

    def get_player(self, player_id: str) -> Optional[Dict[str, Any]]:
        """Get a single player by ID"""
        try:
            player_ref = self.db.collection("players").document(player_id)
            player_doc = player_ref.get()

            if player_doc.exists:
                player_data = player_doc.to_dict()
                player_data["id"] = player_doc.id
                return player_data
            return None
        except Exception as e:
            print(f"Error getting player: {e}")
            return None

    def update_player(self, player_id: str, player_data: Dict[str, Any]) -> bool:
        """Update a player's data"""
        try:
            player_ref = self.db.collection("players").document(player_id)
            player_ref.update(player_data)
            return True
        except Exception as e:
            print(f"Error updating player: {e}")
            return False

    def save_player(self, player: Player) -> str:
        """Save a new player to Firestore"""
        try:
            player_data = player.to_dict()
            player_ref = self.db.collection("players").document()
            player_ref.set(player_data)
            return player_ref.id
        except Exception as e:
            print(f"Error saving player: {e}")
            raise

    def get_players_by_division_and_position(
        self, division_tier: int, position: str, country_id: str
    ) -> List[Dict[str, Any]]:
        """Get players by division tier and position for salary comparison"""
        try:
            players = []

            tiers_to_check = [division_tier]
            if division_tier > 1:
                tiers_to_check.append(division_tier - 1)
            if division_tier > 2:
                tiers_to_check.append(division_tier - 2)

            for tier in tiers_to_check:
                clubs_ref = (
                    self.db.collection("clubs")
                    .where("divisionTier", "==", tier)
                    .where("countryId", "==", country_id)
                )
                clubs = clubs_ref.stream()

                club_ids = [club.id for club in clubs]

                for club_id in club_ids:
                    players_ref = (
                        self.db.collection("players")
                        .where("clubId", "==", club_id)
                        .where("position", "==", position)
                    )
                    club_players = players_ref.stream()

                    for player_doc in club_players:
                        player_data = player_doc.to_dict()
                        player_data["id"] = player_doc.id
                        players.append(player_data)

            return players
        except Exception as e:
            print(f"Error getting players by division and position: {e}")
            return []

    def create_sample_data(self):
        """Create sample clubs and players for testing"""
        try:
            countries = [
                {
                    "id": "volcania",
                    "name": "Volcania",
                    "modifiers": {
                        "blockTiming": 15,
                        "strength": 10,
                        "agility": -5,
                    },
                },
                {
                    "id": "coastalia",
                    "name": "Coastalia",
                    "modifiers": {
                        "agility": 10,
                        "serveAccuracy": 10,
                        "strength": -5,
                    },
                },
                {
                    "id": "forestland",
                    "name": "Forestland",
                    "modifiers": {
                        "spikePower": 5,
                        "blockTiming": 5,
                        "passingAccuracy": 5,
                    },
                },
            ]

            for country in countries:
                country_ref = self.db.collection("countries").document(country["id"])
                country_ref.set(country)

            from utils.constants import COUNTRIES

            for country_id, country_data in COUNTRIES.items():
                country_doc = {
                    "id": country_id,
                    "name": country_data["name"],
                    "modifiers": country_data["modifiers"],
                }
                country_ref = self.db.collection("countries").document(country_id)
                country_ref.set(country_doc)

            for country_id, country_data in COUNTRIES.items():
                for tier in range(1, 20):  # All 19 divisions
                    clubs_per_tier = 16  # Standard 16 clubs per division
                    for i in range(clubs_per_tier):
                        club_data = {
                            "name": f"{country_data['name']} {tier}-{i+1} FC",
                            "countryId": country_id,
                            "divisionTier": tier,
                            "ownerId": None,
                            "isPlayerClub": False,
                        }

                        club_id = self.create_club(club_data)
                        self.generate_initial_squad(club_id, country_id, tier)

            print("Sample data created successfully")

        except Exception as e:
            print(f"Error creating sample data: {e}")
            raise

    def create_season_object(self, season) -> bool:
        """Create a new season object in Firestore"""
        try:
            season_ref = self.db.collection("seasons").document(season.id)
            season_ref.set(season.to_dict())
            return True
        except Exception as e:
            print(f"Error creating season: {e}")
            return False

    def create_competition_object(self, competition) -> bool:
        """Create a new competition object in Firestore"""
        try:
            competition_ref = self.db.collection("competitions").document(
                competition.id
            )
            competition_ref.set(competition.to_dict())
            return True
        except Exception as e:
            print(f"Error creating competition: {e}")
            return False

    def get_clubs_by_country_and_tier(
        self, country_id: str, tier: int
    ) -> List[Dict[str, Any]]:
        """Get all clubs for a specific country and division tier"""
        try:
            clubs_ref = self.db.collection("clubs")
            query = clubs_ref.where("countryId", "==", country_id).where(
                "divisionTier", "==", tier
            )
            docs = query.stream()

            clubs = []
            for doc in docs:
                club_data = doc.to_dict()
                club_data["id"] = doc.id
                clubs.append(club_data)

            return clubs
        except Exception as e:
            print(f"Error getting clubs by country and tier: {e}")
            return []

    def get_all_clubs(self) -> List[Dict[str, Any]]:
        """Get all clubs"""
        try:
            clubs_ref = self.db.collection("clubs")
            docs = clubs_ref.stream()

            clubs = []
            for doc in docs:
                club_data = doc.to_dict()
                club_data["id"] = doc.id
                clubs.append(club_data)

            return clubs
        except Exception as e:
            print(f"Error getting all clubs: {e}")
            return []

    def get_all_players(self) -> List[Dict[str, Any]]:
        """Get all players"""
        try:
            players_ref = self.db.collection("players")
            docs = players_ref.stream()

            players = []
            for doc in docs:
                player_data = doc.to_dict()
                player_data["id"] = doc.id
                players.append(player_data)

            return players
        except Exception as e:
            print(f"Error getting all players: {e}")
            return []

    def get_all_matches(self) -> List[Dict[str, Any]]:
        """Get all matches"""
        try:
            matches_ref = self.db.collection("matches")
            docs = matches_ref.stream()

            matches = []
            for doc in docs:
                match_data = doc.to_dict()
                match_data["id"] = doc.id
                matches.append(match_data)

            return matches
        except Exception as e:
            print(f"Error getting all matches: {e}")
            return []

    def get_all_competitions(self) -> List[Dict[str, Any]]:
        """Get all competitions"""
        try:
            competitions_ref = self.db.collection("competitions")
            docs = competitions_ref.stream()

            competitions = []
            for doc in docs:
                competition_data = doc.to_dict()
                competition_data["id"] = doc.id
                competitions.append(competition_data)

            return competitions
        except Exception as e:
            print(f"Error getting all competitions: {e}")
            return []

    def get_all_seasons(self) -> List[Dict[str, Any]]:
        """Get all seasons"""
        try:
            seasons_ref = self.db.collection("seasons")
            docs = seasons_ref.stream()

            seasons = []
            for doc in docs:
                season_data = doc.to_dict()
                season_data["id"] = doc.id
                seasons.append(season_data)

            return seasons
        except Exception as e:
            print(f"Error getting all seasons: {e}")
            return []

    def get_matches_by_status(self, status: str) -> List[Dict[str, Any]]:
        """Get matches by status"""
        try:
            matches_ref = self.db.collection("matches").where("status", "==", status)
            docs = matches_ref.stream()

            matches = []
            for doc in docs:
                match_data = doc.to_dict()
                match_data["id"] = doc.id
                matches.append(match_data)

            return matches
        except Exception as e:
            print(f"Error getting matches by status: {e}")
            return []

    def get_matches_by_match_day(self, match_day: int) -> List[Dict[str, Any]]:
        """Get matches by match day"""
        try:
            matches_ref = self.db.collection("matches").where(
                "matchDay", "==", match_day
            )
            docs = matches_ref.stream()

            matches = []
            for doc in docs:
                match_data = doc.to_dict()
                match_data["id"] = doc.id
                matches.append(match_data)

            return matches
        except Exception as e:
            print(f"Error getting matches by match day: {e}")
            return []

    def get_scheduled_matches_up_to_day(
        self, max_match_day: int
    ) -> List[Dict[str, Any]]:
        """Get scheduled matches up to a specific match day"""
        try:
            matches_ref = (
                self.db.collection("matches")
                .where("status", "==", "scheduled")
                .where("matchDay", "<=", max_match_day)
            )
            docs = matches_ref.stream()

            matches = []
            for doc in docs:
                match_data = doc.to_dict()
                match_data["id"] = doc.id
                matches.append(match_data)

            return matches
        except Exception as e:
            print(f"Error getting scheduled matches up to day: {e}")
            return []

    def update_match_status(
        self, match_id: str, status: str, result: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Update match status and result"""
        try:
            match_ref = self.db.collection("matches").document(match_id)
            update_data = {"status": status, "updatedAt": datetime.now().isoformat()}

            if result:
                update_data["result"] = result

            match_ref.update(update_data)
            return True
        except Exception as e:
            print(f"Error updating match status: {e}")
            return False

    def save_scheduled_match(self, match_data: Dict[str, Any]) -> str:
        """Save a scheduled match to Firestore"""
        try:
            match_id = str(uuid.uuid4())
            match_data["id"] = match_id
            match_data["createdAt"] = datetime.now().isoformat()
            match_data["updatedAt"] = datetime.now().isoformat()

            doc_ref = self.db.collection("matches").document(match_id)
            doc_ref.set(match_data)

            return match_id
        except Exception as e:
            print(f"Error saving scheduled match: {e}")
            raise

    def create_competition(self, competition_data: Dict[str, Any]) -> bool:
        """Create a new competition"""
        try:
            competition_id = competition_data.get("id", str(uuid.uuid4()))
            competition_data["id"] = competition_id
            competition_data["createdAt"] = datetime.now().isoformat()
            competition_data["updatedAt"] = datetime.now().isoformat()

            doc_ref = self.db.collection("competitions").document(competition_id)
            doc_ref.set(competition_data)

            return True
        except Exception as e:
            print(f"Error creating competition: {e}")
            return False

    def create_season(self, season_data: Dict[str, Any]) -> bool:
        """Create a new season"""
        try:
            season_id = season_data.get("id", str(uuid.uuid4()))
            season_data["id"] = season_id
            season_data["createdAt"] = datetime.now().isoformat()
            season_data["updatedAt"] = datetime.now().isoformat()

            doc_ref = self.db.collection("seasons").document(season_id)
            doc_ref.set(season_data)

            return True
        except Exception as e:
            print(f"Error creating season: {e}")
            return False
