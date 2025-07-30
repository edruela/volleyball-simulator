"""
Tests for match simulation engine
"""

from game_engine.match_simulation import VolleyballSimulator, MatchEvent
from models.club import Club
from models.player import (
    Player,
    PlayerAttributes,
    PlayerCondition,
    PlayerContract,
    PlayerStats,
)


class TestVolleyballSimulator:
    """Test cases for volleyball match simulation"""

    def setup_method(self):
        """Set up test fixtures"""
        self.simulator = VolleyballSimulator()

        self.home_club = Club(
            id="home_club_1",
            name="Home Team FC",
            short_name="HTF",
            country_id="testland",
            division_tier=10,
            owner_id="test_owner",
        )

        self.away_club = Club(
            id="away_club_1",
            name="Away Team FC",
            short_name="ATF",
            country_id="testland",
            division_tier=10,
            owner_id="test_owner",
        )

        self.home_players = self._create_test_players("home_club_1")
        self.away_players = self._create_test_players("away_club_1")

        self.home_team = {
            "id": "home_club_1",
            "club": self.home_club.to_dict(),
            "players": [p.to_dict() for p in self.home_players],
        }

        self.away_team = {
            "id": "away_club_1",
            "club": self.away_club.to_dict(),
            "players": [p.to_dict() for p in self.away_players],
        }

        self.tactics = {
            "home": {"formation": "5-1", "intensity": 1.0, "style": "balanced"},
            "away": {"formation": "5-1", "intensity": 1.0, "style": "balanced"},
        }

    def _create_test_players(self, club_id: str) -> list:
        """Create test players for a club"""
        players = []
        positions = ["OH", "OH", "MB", "MB", "OPP", "S", "L"]

        for i, position in enumerate(positions):
            player = Player(
                id=f"player_{club_id}_{i}",
                first_name=f"Player{i}",
                last_name="Test",
                club_id=club_id,
                country_id="testland",
                age=25,
                position=position,
                attributes=PlayerAttributes(
                    spike_power=70,
                    spike_accuracy=70,
                    block_timing=70,
                    passing_accuracy=70,
                    setting_precision=70,
                    serve_power=70,
                    serve_accuracy=70,
                    court_vision=70,
                    decision_making=70,
                    communication=70,
                    stamina=80,
                    strength=70,
                    agility=70,
                    jump_height=70,
                    speed=70,
                ),
                condition=PlayerCondition(),
                contract=PlayerContract(salary=50000, years_remaining=2),
                stats=PlayerStats(),
            )
            players.append(player)

        return players

    def test_simulate_match_basic(self):
        """Test basic match simulation"""
        result = self.simulator.simulate_match(
            self.home_team, self.away_team, self.tactics
        )

        assert "homeClubId" in result
        assert "awayClubId" in result
        assert "result" in result
        assert "stats" in result
        assert "attendance" in result
        assert "revenue" in result

        match_result = result["result"]
        assert "homeSets" in match_result
        assert "awaySets" in match_result
        assert "winner" in match_result
        assert "sets" in match_result

        home_sets = match_result["homeSets"]
        away_sets = match_result["awaySets"]

        assert max(home_sets, away_sets) == 3
        assert min(home_sets, away_sets) <= 2

        if home_sets > away_sets:
            assert match_result["winner"] == "home"
        else:
            assert match_result["winner"] == "away"

    def test_set_scoring_rules(self):
        """Test that sets follow volleyball scoring rules"""
        result = self.simulator.simulate_match(
            self.home_team, self.away_team, self.tactics
        )
        sets = result["result"]["sets"]

        for i, set_result in enumerate(sets):
            home_points = set_result["homePoints"]
            away_points = set_result["awayPoints"]

            if i == 4:  # Fifth set (if it exists)
                assert max(home_points, away_points) >= 15
            else:
                assert max(home_points, away_points) >= 25

            assert abs(home_points - away_points) >= 2

    def test_team_strength_calculation(self):
        """Test team strength calculation"""
        home_strength = self.simulator._calculate_team_strength(
            self.home_team, self.tactics["home"]
        )

        assert "overall" in home_strength
        assert "attack" in home_strength
        assert "defense" in home_strength
        assert "serve" in home_strength
        assert "receive" in home_strength

        for key, value in home_strength.items():
            assert value > 0
            assert isinstance(value, (int, float))

    def test_formation_bonuses(self):
        """Test that different formations provide different bonuses"""
        tactics_62 = {"formation": "6-2", "intensity": 1.0, "style": "balanced"}
        tactics_51 = {"formation": "5-1", "intensity": 1.0, "style": "balanced"}
        tactics_42 = {"formation": "4-2", "intensity": 1.0, "style": "balanced"}

        strength_62 = self.simulator._calculate_team_strength(
            self.home_team, tactics_62
        )
        strength_51 = self.simulator._calculate_team_strength(
            self.home_team, tactics_51
        )
        strength_42 = self.simulator._calculate_team_strength(
            self.home_team, tactics_42
        )

        assert strength_62["attack"] > strength_51["attack"]

        assert strength_42["attack"] < strength_51["attack"]

    def test_match_events_generation(self):
        """Test that match generates realistic events"""
        result = self.simulator.simulate_match(
            self.home_team, self.away_team, self.tactics
        )

        sets = result["result"]["sets"]
        total_events = 0

        for set_result in sets:
            events = set_result.get("events", [])
            total_events += len(events)

            for event in events:
                assert "type" in event
                assert "team" in event
                assert "effectiveness" in event

                assert event["type"] in [e.value for e in MatchEvent]

                assert event["team"] in ["home", "away"]

                assert 0 <= event["effectiveness"] <= 1

        assert total_events > 0

    def test_attendance_calculation(self):
        """Test attendance calculation"""
        attendance = self.simulator._calculate_attendance(
            self.home_team, self.away_team
        )

        assert attendance > 0

        stadium_capacity = self.home_team["club"]["facilities"]["stadiumCapacity"]
        assert attendance <= stadium_capacity

    def test_revenue_calculation(self):
        """Test revenue calculation"""
        attendance = 1000
        revenue = self.simulator._calculate_revenue(self.home_team, attendance)

        assert "tickets" in revenue
        assert "concessions" in revenue
        assert "merchandise" in revenue
        assert "total" in revenue

        for key, value in revenue.items():
            assert value >= 0

        expected_total = (
            revenue["tickets"] + revenue["concessions"] + revenue["merchandise"]
        )
        assert revenue["total"] == expected_total

    def test_match_stats_compilation(self):
        """Test match statistics compilation"""
        result = self.simulator.simulate_match(
            self.home_team, self.away_team, self.tactics
        )
        stats = result["stats"]

        assert "home" in stats
        assert "away" in stats

        for team_stats in [stats["home"], stats["away"]]:
            assert "kills" in team_stats
            assert "blocks" in team_stats
            assert "aces" in team_stats
            assert "errors" in team_stats

            for stat_value in team_stats.values():
                assert stat_value >= 0
                assert isinstance(stat_value, int)
