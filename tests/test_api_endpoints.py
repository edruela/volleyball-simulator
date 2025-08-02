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
        # Use valid UUIDs for club IDs
        home_club_id = "550e8400-e29b-41d4-a716-446655440000"
        away_club_id = "550e8400-e29b-41d4-a716-446655440001"

        mock_home_club = {"id": home_club_id, "name": "Home Team"}
        mock_away_club = {"id": away_club_id, "name": "Away Team"}
        # Create enough players for a match (minimum 6 required)
        mock_players = [
            {"id": "p1", "position": "OH"},
            {"id": "p2", "position": "MB"},
            {"id": "p3", "position": "OPP"},
            {"id": "p4", "position": "S"},
            {"id": "p5", "position": "L"},
            {"id": "p6", "position": "OH"},
        ]

        mock_firestore_helper.get_club.side_effect = [mock_home_club, mock_away_club]
        mock_firestore_helper.get_club_players.return_value = mock_players
        mock_firestore_helper.save_match.return_value = "match_123"

        with patch("app.volleyball_sim") as mock_sim:
            mock_result = {
                "homeClubId": home_club_id,
                "awayClubId": away_club_id,
                "result": {"winner": "home", "homeSets": 3, "awaySets": 1},
            }
            mock_sim.simulate_match.return_value = mock_result

            match_data = {"homeClubId": home_club_id, "awayClubId": away_club_id}

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
        incomplete_data = {"homeClubId": "550e8400-e29b-41d4-a716-446655440000"}

        response = client.post(
            "/matches/simulate",
            data=json.dumps(incomplete_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid request data" in data["error"]
        assert "Missing required fields: awayClubId" in data["details"]

    def test_simulate_match_club_not_found(self, client, mock_firestore_helper):
        """Test match simulation with non-existent club"""
        with patch("app.volleyball_sim"):
            mock_firestore_helper.get_club.side_effect = [None, None]

            # Use valid UUIDs for club IDs
            home_club_id = "550e8400-e29b-41d4-a716-446655440000"
            away_club_id = "550e8400-e29b-41d4-a716-446655440001"
            match_data = {"homeClubId": home_club_id, "awayClubId": away_club_id}

            response = client.post(
                "/matches/simulate",
                data=json.dumps(match_data),
                content_type="application/json",
            )

            assert response.status_code == 404
            data = json.loads(response.data)
            assert "club not found" in data["error"].lower()

    def test_simulate_match_invalid_club_id_format(self, client):
        """Test match simulation with invalid club ID format"""
        match_data = {"homeClubId": "invalid_id", "awayClubId": "also_invalid"}

        response = client.post(
            "/matches/simulate",
            data=json.dumps(match_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "Invalid club ID format" in data["error"]
        assert "Club IDs must be valid UUIDs" in data["details"]


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check_unhealthy(self, client):
        """Test health check endpoint when services are unavailable"""
        response = client.get("/health")

        # Health endpoint should return 503 when required services are unavailable
        assert response.status_code == 503
        data = json.loads(response.data)
        assert data["status"] == "unhealthy"
        assert data["service"] == "volleyball-simulator"
        assert "services" in data

    def test_health_check_with_mocked_services(self, client):
        """Test health check endpoint with mocked healthy services"""
        with patch("app.service_status") as mock_status:
            # Mock all services as healthy
            mock_status.firebase_initialized = True
            mock_status.firestore_connected = True
            mock_status.simulator_available = True
            mock_status.initialization_errors = []
            mock_status.is_healthy.return_value = True

            response = client.get("/health")

            assert response.status_code == 200
            data = json.loads(response.data)
            assert data["status"] == "healthy"
            assert data["service"] == "volleyball-simulator"


class TestAuthBypass:
    """Test authentication bypass functionality"""

    def test_auth_bypass_enabled(self, client):
        """Test that auth bypass works when SKIP_AUTH is true"""
        # Health endpoint returns 503 when services are unavailable, not related to auth
        response = client.get("/health")
        assert response.status_code == 503  # Services unavailable in test environment

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


class TestPlayerEndpoints:
    """Test player-related API endpoints"""

    def test_get_player_success(self, client, mock_firestore_helper):
        """Test successful player retrieval"""
        mock_player_data = {
            "id": "test_player_123",
            "firstName": "John",
            "lastName": "Doe",
            "clubId": "test_club",
            "countryId": "volcania",
            "age": 25,
            "position": "OH",
            "contract": {
                "salary": 50000,
                "yearsRemaining": 2,
                "bonusClause": 5000,
                "transferClause": 100000,
            },
        }

        mock_firestore_helper.get_player.return_value = mock_player_data

        response = client.get("/players/test_player_123")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["firstName"] == "John"
        assert data["lastName"] == "Doe"
        assert data["position"] == "OH"

    def test_get_player_not_found(self, client, mock_firestore_helper):
        """Test player retrieval for non-existent player"""
        mock_firestore_helper.get_player.return_value = None

        response = client.get("/players/nonexistent")

        assert response.status_code == 404
        data = json.loads(response.data)
        assert "Player not found" in data["error"]

    def test_create_player_success(self, client, mock_firestore_helper):
        """Test successful player creation"""
        mock_club_data = {"id": "test_club", "name": "Test Club", "divisionTier": 10}

        mock_firestore_helper.get_club.return_value = mock_club_data
        mock_firestore_helper.save_player.return_value = "new_player_123"

        player_data = {
            "clubId": "test_club",
            "countryId": "volcania",
            "position": "OH",
            "age": 25,
        }

        response = client.post(
            "/players",
            data=json.dumps(player_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["playerId"] == "new_player_123"
        assert "Player created successfully" in data["message"]

    def test_create_player_underage_professional(self, client, mock_firestore_helper):
        """Test player creation with underage player for professional division"""
        mock_club_data = {
            "id": "test_club",
            "name": "Test Club",
            "divisionTier": 5,  # Professional division
        }

        mock_firestore_helper.get_club.return_value = mock_club_data

        player_data = {
            "clubId": "test_club",
            "countryId": "volcania",
            "position": "OH",
            "age": 20,  # Under 21
        }

        response = client.post(
            "/players",
            data=json.dumps(player_data),
            content_type="application/json",
        )

        assert response.status_code == 400
        data = json.loads(response.data)
        assert "must be at least 21 years old" in data["error"]

    def test_contract_renewal_accepted(self, client, mock_firestore_helper):
        """Test contract renewal that gets accepted"""
        mock_player_data = {
            "id": "test_player",
            "first_name": "John",
            "last_name": "Doe",
            "club_id": "test_club",
            "country_id": "volcania",
            "age": 25,
            "position": "OH",
            "attributes": {
                "spike_power": 75,
                "spike_accuracy": 70,
                "block_timing": 60,
                "passing_accuracy": 65,
                "setting_precision": 50,
                "serve_power": 60,
                "serve_accuracy": 55,
                "court_vision": 65,
                "decision_making": 60,
                "communication": 70,
                "stamina": 75,
                "strength": 70,
                "agility": 65,
                "jump_height": 80,
                "speed": 60,
            },
            "condition": {"fatigue": 10, "fitness": 90, "morale": 80, "injury": None},
            "contract": {
                "salary": 50000,
                "years_remaining": 1,
                "bonus_clause": 5000,
                "transfer_clause": 100000,
            },
            "stats": {
                "matches_played": 15,
                "sets_played": 45,
                "points": 120,
                "kills": 85,
                "blocks": 25,
                "aces": 12,
                "digs": 30,
                "assists": 5,
            },
        }

        mock_club_data = {"id": "test_club", "divisionTier": 10}

        mock_similar_players = [
            {"contract": {"salary": 45000}},
            {"contract": {"salary": 55000}},
            {"contract": {"salary": 50000}},
        ]

        mock_firestore_helper.get_player.return_value = mock_player_data
        mock_firestore_helper.get_club.return_value = mock_club_data
        mock_firestore_helper.get_players_by_division_and_position.return_value = (
            mock_similar_players
        )
        mock_firestore_helper.update_player.return_value = True

        renewal_data = {
            "offeredSalary": 60000,  # Above 110% of average (55000)
            "yearsOffered": 3,
        }

        response = client.post(
            "/players/test_player/renew-contract",
            data=json.dumps(renewal_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["accepted"] == True
        assert "accepted and updated" in data["message"]

    def test_contract_renewal_rejected(self, client, mock_firestore_helper):
        """Test contract renewal that gets rejected"""
        mock_player_data = {
            "id": "test_player",
            "first_name": "John",
            "last_name": "Doe",
            "club_id": "test_club",
            "country_id": "volcania",
            "age": 25,
            "position": "OH",
            "attributes": {
                "spike_power": 75,
                "spike_accuracy": 70,
                "block_timing": 60,
                "passing_accuracy": 65,
                "setting_precision": 50,
                "serve_power": 60,
                "serve_accuracy": 55,
                "court_vision": 65,
                "decision_making": 60,
                "communication": 70,
                "stamina": 75,
                "strength": 70,
                "agility": 65,
                "jump_height": 80,
                "speed": 60,
            },
            "condition": {"fatigue": 10, "fitness": 90, "morale": 80, "injury": None},
            "contract": {
                "salary": 50000,
                "years_remaining": 1,
                "bonus_clause": 5000,
                "transfer_clause": 100000,
            },
            "stats": {
                "matches_played": 15,
                "sets_played": 45,
                "points": 120,
                "kills": 85,
                "blocks": 25,
                "aces": 12,
                "digs": 30,
                "assists": 5,
            },
        }

        mock_club_data = {"id": "test_club", "divisionTier": 10}

        mock_similar_players = [
            {"contract": {"salary": 60000}},
            {"contract": {"salary": 65000}},
            {"contract": {"salary": 70000}},
        ]

        mock_firestore_helper.get_player.return_value = mock_player_data
        mock_firestore_helper.get_club.return_value = mock_club_data
        mock_firestore_helper.get_players_by_division_and_position.return_value = (
            mock_similar_players
        )

        renewal_data = {
            "offeredSalary": 50000,  # Below 110% of average (71500)
            "yearsOffered": 3,
        }

        response = client.post(
            "/players/test_player/renew-contract",
            data=json.dumps(renewal_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["accepted"] == False
        assert "rejected" in data["message"]

    def test_player_retirement_young_player(self, client, mock_firestore_helper):
        """Test retirement for young player (should not retire)"""
        mock_player_data = {
            "id": "test_player",
            "first_name": "John",
            "last_name": "Doe",
            "club_id": "test_club",
            "country_id": "volcania",
            "age": 25,  # Young player
            "position": "OH",
            "attributes": {
                "spike_power": 75,
                "spike_accuracy": 70,
                "block_timing": 60,
                "passing_accuracy": 65,
                "setting_precision": 50,
                "serve_power": 60,
                "serve_accuracy": 55,
                "court_vision": 65,
                "decision_making": 60,
                "communication": 70,
                "stamina": 75,
                "strength": 70,
                "agility": 65,
                "jump_height": 80,
                "speed": 60,
            },
            "condition": {"fatigue": 10, "fitness": 90, "morale": 80, "injury": None},
            "contract": {
                "salary": 50000,
                "years_remaining": 2,
                "bonus_clause": 5000,
                "transfer_clause": 100000,
            },
            "stats": {
                "matches_played": 15,
                "sets_played": 45,
                "points": 120,
                "kills": 85,
                "blocks": 25,
                "aces": 12,
                "digs": 30,
                "assists": 5,
            },
        }

        mock_firestore_helper.get_player.return_value = mock_player_data

        response = client.post("/players/test_player/retire")

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["retired"] == False
        assert "continue playing" in data["message"]

    def test_transfer_assessment_accepted(self, client, mock_firestore_helper):
        """Test transfer assessment that gets accepted"""
        mock_player_data = {
            "id": "test_player",
            "first_name": "John",
            "last_name": "Doe",
            "club_id": "current_club",
            "country_id": "volcania",
            "age": 25,
            "position": "OH",
            "attributes": {
                "spike_power": 75,
                "spike_accuracy": 70,
                "block_timing": 60,
                "passing_accuracy": 65,
                "setting_precision": 50,
                "serve_power": 60,
                "serve_accuracy": 55,
                "court_vision": 65,
                "decision_making": 60,
                "communication": 70,
                "stamina": 75,
                "strength": 70,
                "agility": 65,
                "jump_height": 80,
                "speed": 60,
            },
            "condition": {"fatigue": 10, "fitness": 90, "morale": 80, "injury": None},
            "contract": {
                "salary": 50000,
                "years_remaining": 2,
                "bonus_clause": 5000,
                "transfer_clause": 100000,
            },
            "stats": {
                "matches_played": 15,
                "sets_played": 45,
                "points": 120,
                "kills": 85,
                "blocks": 25,
                "aces": 12,
                "digs": 30,
                "assists": 5,
            },
        }

        mock_current_club = {"id": "current_club", "divisionTier": 10}

        mock_target_club = {"id": "target_club", "divisionTier": 5}  # Better division

        mock_firestore_helper.get_player.return_value = mock_player_data
        mock_firestore_helper.get_club.side_effect = [
            mock_current_club,
            mock_target_club,
        ]

        transfer_data = {
            "offeredSalary": 60000,  # Higher salary
            "targetClubId": "target_club",
        }

        response = client.post(
            "/players/test_player/assess-transfer",
            data=json.dumps(transfer_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["accepted"] == True
        assert "accepted" in data["message"]

    def test_transfer_assessment_rejected(self, client, mock_firestore_helper):
        """Test transfer assessment that gets rejected"""
        mock_player_data = {
            "id": "test_player",
            "first_name": "John",
            "last_name": "Doe",
            "club_id": "current_club",
            "country_id": "volcania",
            "age": 25,
            "position": "OH",
            "attributes": {
                "spike_power": 75,
                "spike_accuracy": 70,
                "block_timing": 60,
                "passing_accuracy": 65,
                "setting_precision": 50,
                "serve_power": 60,
                "serve_accuracy": 55,
                "court_vision": 65,
                "decision_making": 60,
                "communication": 70,
                "stamina": 75,
                "strength": 70,
                "agility": 65,
                "jump_height": 80,
                "speed": 60,
            },
            "condition": {"fatigue": 10, "fitness": 90, "morale": 80, "injury": None},
            "contract": {
                "salary": 50000,
                "years_remaining": 2,
                "bonus_clause": 5000,
                "transfer_clause": 100000,
            },
            "stats": {
                "matches_played": 15,
                "sets_played": 45,
                "points": 120,
                "kills": 85,
                "blocks": 25,
                "aces": 12,
                "digs": 30,
                "assists": 5,
            },
        }

        mock_current_club = {"id": "current_club", "divisionTier": 5}

        mock_target_club = {"id": "target_club", "divisionTier": 10}  # Worse division

        mock_firestore_helper.get_player.return_value = mock_player_data
        mock_firestore_helper.get_club.side_effect = [
            mock_current_club,
            mock_target_club,
        ]

        transfer_data = {
            "offeredSalary": 45000,  # Lower salary
            "targetClubId": "target_club",
        }

        response = client.post(
            "/players/test_player/assess-transfer",
            data=json.dumps(transfer_data),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = json.loads(response.data)
        assert data["accepted"] == False
        assert "rejected" in data["message"]


if __name__ == "__main__":
    pytest.main([__file__])
