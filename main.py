"""
Legacy Cloud Functions entry points for Volleyball Manager (deprecated)
This file contains compatibility wrappers for the original Cloud Functions deployment.
The current deployment uses app.py with Flask on Cloud Run.
"""

from typing import Dict, Any, Union, Tuple, Optional
import os
from flask import Flask, Request, jsonify
from flask_restx import Api, Resource, fields  # type: ignore
from google.cloud import firestore  # type: ignore
from game_engine.match_simulation import VolleyballSimulator
from game_engine.season_management import SeasonManager
from utils.firestore_helpers import FirestoreHelper
from utils.auth import require_auth

db = None
firestore_helper: Optional[FirestoreHelper] = None
volleyball_sim: Optional[VolleyballSimulator] = None
season_manager: Optional[SeasonManager] = None

try:
    db = firestore.Client(
        project=os.getenv("GOOGLE_CLOUD_PROJECT", "invweb-lab-public-2")
    )
    firestore_helper = FirestoreHelper(db)
    volleyball_sim = VolleyballSimulator()
    season_manager = SeasonManager(firestore_helper)
except Exception as e:
    print(
        f"Warning: Firestore initialization failed (likely missing "
        f"credentials): {e}"
    )
    print(
        "Running in local testing mode - Swagger UI will be available "
        "but API endpoints may not work"
    )
    db = None
    firestore_helper = None
    volleyball_sim = None
    season_manager = None

app = Flask(__name__)
api = Api(
    app,
    version="1.0",
    title="Volleyball Manager API",
    description=("API for managing volleyball clubs, players, matches, and seasons"),
    doc="/swagger/",
)

match_request_model = api.model(
    "MatchRequest",
    {
        "homeClubId": fields.String(required=True, description="ID of the home club"),
        "awayClubId": fields.String(required=True, description="ID of the away club"),
        "tactics": fields.Raw(description="Match tactics configuration"),
    },
)

club_request_model = api.model(
    "ClubRequest",
    {
        "name": fields.String(required=True, description="Club name"),
        "countryId": fields.String(required=True, description="Country ID"),
        "ownerId": fields.String(required=True, description="Owner ID"),
    },
)

season_request_model = api.model(
    "SeasonRequest",
    {
        "seasonName": fields.String(required=True, description="Name of the season"),
        "durationMinutes": fields.Integer(
            required=True, description="Duration in minutes"
        ),
        "participatingCountries": fields.List(
            fields.String, description="List of country IDs"
        ),
    },
)


@api.route("/simulate-match")
class SimulateMatch(Resource):
    @api.expect(match_request_model)
    @api.doc(
        "simulate_match",
        description="Simulate a volleyball match between two clubs",
    )
    @require_auth
    def post(self):
        """
        Simulate a volleyball match between two clubs
        """
        try:
            request_json = api.payload
            if not request_json:
                return jsonify({"error": "No JSON data provided"}), 400

            home_club_id = request_json.get("homeClubId")
            away_club_id = request_json.get("awayClubId")

            if not home_club_id or not away_club_id:
                return jsonify({"error": "Missing club IDs"}), 400

            if not firestore_helper or not volleyball_sim:
                return (
                    jsonify(
                        {
                            "error": (
                                "Service unavailable - running in local testing mode"
                            )
                        }
                    ),
                    503,
                )

            home_club_data = firestore_helper.get_club(home_club_id)
            away_club_data = firestore_helper.get_club(away_club_id)

            if not home_club_data or not away_club_data:
                return jsonify({"error": "Club not found"}), 404

            home_players = firestore_helper.get_club_players(home_club_id)
            away_players = firestore_helper.get_club_players(away_club_id)

            home_team = {
                "id": home_club_id,
                "club": home_club_data,
                "players": home_players,
            }

            away_team = {
                "id": away_club_id,
                "club": away_club_data,
                "players": away_players,
            }

            tactics = request_json.get(
                "tactics",
                {
                    "home": {
                        "formation": "5-1",
                        "intensity": 1.0,
                        "style": "balanced",
                    },
                    "away": {
                        "formation": "5-1",
                        "intensity": 1.0,
                        "style": "balanced",
                    },
                },
            )

            match_result = volleyball_sim.simulate_match(home_team, away_team, tactics)

            match_id = firestore_helper.save_match(match_result)
            match_result["matchId"] = match_id

            return jsonify(match_result)

        except Exception as e:
            return jsonify({"error": f"Match simulation failed: {str(e)}"}), 500


@api.route("/club")
class GetClub(Resource):
    @api.doc("get_club", description="Get club information by ID")
    @api.param("clubId", "Club ID", required=True)
    @require_auth
    def get(self):
        """
        Get club information by ID
        """
        try:
            from flask import request

            club_id = request.args.get("clubId")
            if not club_id:
                return jsonify({"error": "Missing clubId parameter"}), 400

            if not firestore_helper:
                return (
                    jsonify(
                        {
                            "error": (
                                "Service unavailable - running in local testing mode"
                            )
                        }
                    ),
                    503,
                )

            club_data = firestore_helper.get_club(club_id)
            if not club_data:
                return jsonify({"error": "Club not found"}), 404

            players = firestore_helper.get_club_players(club_id)
            club_data["players"] = players

            return jsonify(club_data)

        except Exception as e:
            return jsonify({"error": f"Failed to get club: {str(e)}"}), 500


@api.route("/club")
class CreateClub(Resource):
    @api.expect(club_request_model)
    @api.doc("create_club", description="Create a new club")
    @require_auth
    def post(self):
        """
        Create a new club
        """
        try:
            request_json = api.payload
            if not request_json:
                return jsonify({"error": "No JSON data provided"}), 400

            required_fields = ["name", "countryId", "ownerId"]
            for field in required_fields:
                if field not in request_json:
                    return jsonify({"error": f"Missing required field: {field}"}), 400

            if not firestore_helper:
                return (
                    jsonify(
                        {
                            "error": (
                                "Service unavailable - running in local testing mode"
                            )
                        }
                    ),
                    503,
                )

            club_id = firestore_helper.create_club(request_json)

            initial_players = firestore_helper.generate_initial_squad(
                club_id, request_json["countryId"]
            )

            return jsonify(
                {
                    "clubId": club_id,
                    "message": "Club created successfully",
                    "playersGenerated": len(initial_players),
                }
            )

        except Exception as e:
            return jsonify({"error": f"Failed to create club: {str(e)}"}), 500


@api.route("/league-standings")
class GetLeagueStandings(Resource):
    @api.doc(
        "get_league_standings",
        description="Get league standings for a specific country and division",
    )
    @api.param("countryId", "Country ID", required=True)
    @api.param("divisionTier", "Division tier number", type=int, required=True)
    @require_auth
    def get(self):
        """
        Get league standings for a specific country and division
        """
        try:
            from flask import request

            country_id = request.args.get("countryId")
            division_tier = request.args.get("divisionTier", type=int)

            if not country_id or division_tier is None:
                return (
                    jsonify({"error": "Missing countryId or divisionTier parameters"}),
                    400,
                )

            if not firestore_helper:
                return (
                    jsonify(
                        {
                            "error": (
                                "Service unavailable - running in local testing mode"
                            )
                        }
                    ),
                    503,
                )

            standings = firestore_helper.get_league_standings(country_id, division_tier)

            return jsonify(
                {
                    "countryId": country_id,
                    "divisionTier": division_tier,
                    "standings": standings,
                }
            )

        except Exception as e:
            return jsonify({"error": f"Failed to get standings: {str(e)}"}), 500


@api.route("/start-season")
class StartSeason(Resource):
    @api.expect(season_request_model)
    @api.doc(
        "start_season",
        description="Start a new season with competitions for all countries",
    )
    @require_auth
    def post(self):
        """
        Start a new season with competitions for all countries
        """
        try:
            request_json = api.payload
            if not request_json:
                return jsonify({"error": "No JSON data provided"}), 400

            season_name = request_json.get("seasonName")
            duration_minutes = request_json.get("durationMinutes")
            participating_countries = request_json.get("participatingCountries")

            if not season_name:
                return jsonify({"error": "Missing seasonName parameter"}), 400

            if duration_minutes is None:
                return jsonify({"error": "Missing durationMinutes parameter"}), 400

            if not isinstance(duration_minutes, int) or duration_minutes <= 0:
                return (
                    jsonify({"error": "durationMinutes must be a positive integer"}),
                    400,
                )

            if participating_countries is not None:
                if not isinstance(participating_countries, list):
                    return (
                        jsonify({"error": "participatingCountries must be a list"}),
                        400,
                    )

                from utils.constants import COUNTRIES

                invalid_countries = [
                    c for c in participating_countries if c not in COUNTRIES
                ]
                if invalid_countries:
                    return (
                        jsonify({"error": f"Invalid countries: {invalid_countries}"}),
                        400,
                    )

            if not season_manager:
                return (
                    jsonify(
                        {
                            "error": (
                                "Service unavailable - running in local testing mode"
                            )
                        }
                    ),
                    503,
                )

            result = season_manager.create_season(
                season_name=season_name,
                duration_minutes=duration_minutes,
                participating_countries=participating_countries,
            )

            if result.success:
                return jsonify(
                    {
                        "seasonId": result.season_id,
                        "message": result.message,
                        "competitionsCreated": result.competitions_created,
                        "participatingCountries": result.participating_countries,
                        "durationMinutes": duration_minutes,
                    }
                )
            else:
                return jsonify({"error": result.message}), 400

        except Exception as e:
            return jsonify({"error": f"Failed to start season: {str(e)}"}), 500


def simulate_match(
    request: Request,
) -> Union[Dict[str, Any], Tuple[Dict[str, str], int]]:
    """Legacy Cloud Function wrapper for simulate_match (deprecated)"""
    with app.test_request_context(json=request.get_json(silent=True)):
        return SimulateMatch().post()


def get_club(
    request: Request,
) -> Union[Dict[str, Any], Tuple[Dict[str, str], int]]:
    """Legacy Cloud Function wrapper for get_club (deprecated)"""
    with app.test_request_context(query_string=request.query_string):
        return GetClub().get()


def create_club(
    request: Request,
) -> Union[Dict[str, Any], Tuple[Dict[str, str], int]]:
    """Legacy Cloud Function wrapper for create_club (deprecated)"""
    with app.test_request_context(json=request.get_json(silent=True)):
        return CreateClub().post()


def get_league_standings(
    request: Request,
) -> Union[Dict[str, Any], Tuple[Dict[str, str], int]]:
    """Legacy Cloud Function wrapper for get_league_standings (deprecated)"""
    with app.test_request_context(query_string=request.query_string):
        return GetLeagueStandings().get()


def start_season(
    request: Request,
) -> Union[Dict[str, Any], Tuple[Dict[str, str], int]]:
    """Legacy Cloud Function wrapper for start_season (deprecated)"""
    with app.test_request_context(json=request.get_json(silent=True)):
        return StartSeason().post()


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080)
