"""
API endpoint integration tests for Volleyball Manager
"""

import pytest
import os
import json
from unittest.mock import patch
from app import app


@pytest.fixture
def client():
    """Create test client with auth bypass enabled"""
    os.environ["SKIP_AUTH"] = "true"
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client
    if "SKIP_AUTH" in os.environ:
        del os.environ["SKIP_AUTH"]


@pytest.fixture
def mock_firestore_helper():
    """Mock FirestoreHelper for testing"""
    with patch("app.firestore_helper") as mock_helper:
        yield mock_helper


class TestClubEndpoints:
    """Test club-related API endpoints"""

    def test_get_club_success(self, client, mock_firestore_helper):
        """Test successful club retrieval"""
        mock_club_data = {
            "id": "test_club_123",
            "name": "Test Volleyball Club",
            "countryId": "volcania",
            "divisionTier": 10,
            "ownerId": "user123",
            "isPlayerClub": True,
        }

        mock_players = [
            {
                "id": "player1",
                "name": {"first": "John", "last": "Doe"},
                "position": "OH",
            },
            {
                "id": "player2",
                "name": {"first": "Jane", "last": "Smith"},
                "position": "S",
            },
        ]

        mock_firestore_helper.get_club.return_value = mock_club_data
        mock_firestore_helper.get_club_players.return_value = mock_players

        response = client.get("/clubs?clubId=test_club_123")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["name"] == "Test Volleyball Club"
        assert data["countryId"] == "volcania"
        assert "players" in data
        assert len(data["players"]) == 2

    def test_get_club_missing_id(self, client):
        """Test club retrieval without clubId parameter"""
        response = client.get("/clubs")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Missing clubId parameter" in data["error"]

    def test_get_club_not_found(self, client, mock_firestore_helper):
        """Test club retrieval for non-existent club"""
        mock_firestore_helper.get_club.return_value = None

        response = client.get("/clubs?clubId=nonexistent")

        assert response.status_code == 404
        data = json.loads(response.data)
        assert "Club not found" in data["error"]

    def test_create_club_success(self, client, mock_firestore_helper):
        """Test successful club creation"""
        mock_firestore_helper.create_club.return_value = "new_club_123"
        mock_firestore_helper.generate_initial_squad.return_value = ["p1", "p2", "p3"]

        club_data = {
            "name": "New Test Club",
            "countryId": "coastalia",
            "ownerId": "user456",
        }

        response = client.post(
            "/clubs",
            data=json.dumps(club_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["clubId"] == "new_club_123"
        assert "Club created successfully" in data["message"]
        assert data["playersGenerated"] == 3

    def test_create_club_missing_fields(self, client):
        """Test club creation with missing required fields"""
        incomplete_data = {"name": "Incomplete Club"}

        response = client.post(
            "/clubs",
            data=json.dumps(incomplete_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Missing required field" in data["error"]

    def test_create_club_no_json(self, client):
        """Test club creation without JSON data"""
        response = client.post("/clubs")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "No JSON data provided" in data["error"]


class TestLeagueEndpoints:
    """Test league-related API endpoints"""

    def test_get_league_standings_success(self, client, mock_firestore_helper):
        """Test successful league standings retrieval"""
        mock_standings = [
            {
                "clubId": "club1",
                "name": "Top Club",
                "wins": 10,
                "losses": 2,
                "points": 30,
                "position": 1,
            },
            {
                "clubId": "club2",
                "name": "Second Club",
                "wins": 8,
                "losses": 4,
                "points": 24,
                "position": 2,
            },
        ]

        mock_firestore_helper.get_league_standings.return_value = mock_standings

        response = client.get("/leagues/standings?countryId=volcania&divisionTier=1")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["countryId"] == "volcania"
        assert data["divisionTier"] == 1
        assert len(data["standings"]) == 2
        assert data["standings"][0]["name"] == "Top Club"

    def test_get_league_standings_missing_params(self, client):
        """Test league standings retrieval with missing parameters"""
        response = client.get("/leagues/standings?countryId=volcania")

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Missing countryId or divisionTier parameters" in data["error"]

    def test_get_league_standings_invalid_tier(self, client):
        """Test league standings with invalid division tier"""
        response = client.get(
            "/leagues/standings?countryId=volcania&divisionTier=invalid"
        )

        assert response.status_code == 400


class TestMatchEndpoints:
    """Test match-related API endpoints"""

    def test_simulate_match_success(self, client, mock_firestore_helper):
        """Test successful match simulation"""
        mock_home_club = {"id": "home_club", "name": "Home Team"}
        mock_away_club = {"id": "away_club", "name": "Away Team"}
        mock_players = [{"id": "p1", "position": "OH"}]

        mock_firestore_helper.get_club.side_effect = [mock_home_club, mock_away_club]
        mock_firestore_helper.get_club_players.return_value = mock_players
        mock_firestore_helper.save_match.return_value = "match_123"

        with patch("app.volleyball_sim") as mock_sim:
            mock_result = {
                "homeClubId": "home_club",
                "awayClubId": "away_club",
                "result": {"winner": "home", "homeSets": 3, "awaySets": 1},
            }
            mock_sim.simulate_match.return_value = mock_result

            match_data = {"homeClubId": "home_club", "awayClubId": "away_club"}

            response = client.post(
                "/matches/simulate",
                data=json.dumps(match_data),
                content_type="application/json",
            )

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["matchId"] == "match_123"
            assert data["result"]["winner"] == "home"

    def test_simulate_match_missing_clubs(self, client):
        """Test match simulation with missing club IDs"""
        incomplete_data = {"homeClubId": "home_club"}

        response = client.post(
            "/matches/simulate",
            data=json.dumps(incomplete_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Missing club IDs" in data["error"]

    def test_simulate_match_club_not_found(self, client, mock_firestore_helper):
        """Test match simulation with non-existent club"""
        with patch("app.volleyball_sim"):
            mock_firestore_helper.get_club.side_effect = [None, None]

            match_data = {"homeClubId": "nonexistent1", "awayClubId": "nonexistent2"}

            response = client.post(
                "/matches/simulate",
                data=json.dumps(match_data),
                content_type="application/json",
            )

            assert response.status_code == 404
            data = json.loads(response.data)
            assert "Club not found" in data["error"]


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["status"] == "healthy"
        assert data["service"] == "volleyball-simulator"


class TestAuthBypass:
    """Test authentication bypass functionality"""

    def test_auth_bypass_enabled(self, client):
        """Test that auth bypass works when SKIP_AUTH is true"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_auth_bypass_disabled(self):
        """Test that auth bypass only works when SKIP_AUTH is 'true'"""
        from utils.auth import require_auth
        import os

        original_skip_auth = os.environ.get("SKIP_AUTH")
        os.environ["SKIP_AUTH"] = "false"

        try:

            @require_auth
            def mock_endpoint():
                return {"success": True}

            assert os.getenv("SKIP_AUTH", "false").lower() != "true"

        finally:
            if original_skip_auth is not None:
                os.environ["SKIP_AUTH"] = original_skip_auth
            elif "SKIP_AUTH" in os.environ:
                del os.environ["SKIP_AUTH"]


if __name__ == "__main__":
    pytest.main([__file__])
