"""
Firestore database helper functions
"""

from typing import Dict, List, Optional, Any
from google.cloud import firestore
from models.club import Club
from models.player import Player, generate_random_player
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

    def create_sample_data(self):
        """Create sample clubs and players for testing"""
        try:
            countries = [
                {
                    "id": "volcania",
                    "name": "Volcania",
                    "modifiers": {"blockTiming": 15, "strength": 10, "agility": -5},
                },
                {
                    "id": "coastalia",
                    "name": "Coastalia",
                    "modifiers": {"agility": 10, "serveAccuracy": 10, "strength": -5},
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
                    "modifiers": country_data["modifiers"]
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
    
    def create_season(self, season) -> bool:
        """Create a new season in Firestore"""
        try:
            season_ref = self.db.collection("seasons").document(season.id)
            season_ref.set(season.to_dict())
            return True
        except Exception as e:
            print(f"Error creating season: {e}")
            return False
    
    def create_competition(self, competition) -> bool:
        """Create a new competition in Firestore"""
        try:
            competition_ref = self.db.collection("competitions").document(competition.id)
            competition_ref.set(competition.to_dict())
            return True
        except Exception as e:
            print(f"Error creating competition: {e}")
            return False
    
    def get_clubs_by_country_and_tier(self, country_id: str, tier: int) -> List[Dict[str, Any]]:
        """Get all clubs for a specific country and division tier"""
        try:
            clubs_ref = self.db.collection("clubs")
            query = clubs_ref.where("countryId", "==", country_id).where("divisionTier", "==", tier)
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
