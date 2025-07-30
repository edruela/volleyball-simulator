"""
Flask application for Volleyball Manager
Cloud Run deployment with containerized serverless architecture
"""

import os
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields  # type: ignore
from flask_cors import CORS
from google.cloud import firestore  # type: ignore
from game_engine.match_simulation import VolleyballSimulator
from utils.firestore_helpers import FirestoreHelper
from utils.auth import require_auth

app = Flask(__name__)
CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])
api = Api(
    app,
    version="1.0",
    title="Volleyball Simulator API",
    description="A volleyball simulation and management API",
)

# Define namespaces
match_ns = api.namespace("matches", description="Match operations")
club_ns = api.namespace("clubs", description="Club operations")
league_ns = api.namespace("leagues", description="League operations")
player_ns = api.namespace("players", description="Player operations")

# Define models for request/response documentation
tactics_model = api.model(
    "Tactics",
    {
        "formation": fields.String(required=True, example="5-1"),
        "intensity": fields.Float(required=True, example=1.0),
        "style": fields.String(required=True, example="balanced"),
    },
)

match_request = api.model(
    "MatchRequest",
    {
        "homeClubId": fields.String(required=True, description="Home club ID"),
        "awayClubId": fields.String(required=True, description="Away club ID"),
        "tactics": fields.Nested(tactics_model),
    },
)

club_request = api.model(
    "ClubRequest",
    {
        "name": fields.String(required=True, description="Club name"),
        "countryId": fields.String(required=True, description="Country ID"),
        "ownerId": fields.String(required=True, description="Owner ID"),
    },
)

player_request = api.model(
    "PlayerRequest",
    {
        "clubId": fields.String(required=True, description="Club ID"),
        "countryId": fields.String(required=True, description="Country ID"),
        "position": fields.String(required=True, description="Player position"),
        "age": fields.Integer(description="Player age"),
    },
)

contract_renewal_request = api.model(
    "ContractRenewalRequest",
    {
        "offeredSalary": fields.Integer(required=True, description="Offered salary"),
        "yearsOffered": fields.Integer(required=True, description="Contract years"),
    },
)

transfer_assessment_request = api.model(
    "TransferAssessmentRequest",
    {
        "offeredSalary": fields.Integer(required=True, description="Offered salary"),
        "targetClubId": fields.String(required=True, description="Target club ID"),
    },
)

# Initialize other components
db = None
firestore_helper = None
volleyball_sim = None

try:
    db = firestore.Client()
    firestore_helper = FirestoreHelper(db)
    volleyball_sim = VolleyballSimulator()
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


@match_ns.route("/simulate")
class MatchSimulation(Resource):
    @match_ns.expect(match_request)
    @match_ns.response(200, "Match simulated successfully")
    @match_ns.response(400, "Invalid request")
    @match_ns.response(401, "Authentication required")
    @match_ns.response(404, "Club not found")
    @match_ns.response(500, "Internal server error")
    @require_auth
    def post(self):
        """Simulate a volleyball match"""
        try:
            request_json = request.get_json(silent=True)
            if not request_json:
                return {"error": "No JSON data provided"}, 400

            home_club_id = request_json.get("homeClubId")
            away_club_id = request_json.get("awayClubId")

            if not home_club_id or not away_club_id:
                return {"error": "Missing club IDs"}, 400

            if not firestore_helper or not volleyball_sim:
                return {
                    "error": ("Service unavailable - running in local testing mode")
                }, 503

            home_club_data = firestore_helper.get_club(home_club_id)
            away_club_data = firestore_helper.get_club(away_club_id)

            if not home_club_data or not away_club_data:
                return {"error": "Club not found"}, 404

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
            return {"error": f"Match simulation failed: {str(e)}"}, 500


@club_ns.route("")
class ClubOperations(Resource):
    @club_ns.param("clubId", "The club identifier")
    @club_ns.response(200, "Success")
    @club_ns.response(400, "Invalid request")
    @club_ns.response(401, "Authentication required")
    @club_ns.response(404, "Club not found")
    @require_auth
    def get(self):
        """Get club information"""
        try:
            club_id = request.args.get("clubId")
            if not club_id:
                return {"error": "Missing clubId parameter"}, 400

            if not firestore_helper:
                return {
                    "error": ("Service unavailable - running in local testing mode")
                }, 503

            club_data = firestore_helper.get_club(club_id)
            if not club_data:
                return {"error": "Club not found"}, 404

            players = firestore_helper.get_club_players(club_id)
            club_data["players"] = players

            return jsonify(club_data)

        except Exception as e:
            return {"error": f"Failed to get club: {str(e)}"}, 500

    @club_ns.expect(club_request)
    @club_ns.response(200, "Club created successfully")
    @club_ns.response(400, "Invalid request")
    @club_ns.response(401, "Authentication required")
    @club_ns.response(500, "Internal server error")
    @require_auth
    def post(self):
        """Create a new club"""
        try:
            request_json = request.get_json(silent=True)
            if not request_json:
                return {"error": "No JSON data provided"}, 400

            required_fields = ["name", "countryId", "ownerId"]
            for field in required_fields:
                if field not in request_json:
                    return {"error": f"Missing required field: {field}"}, 400

            if not firestore_helper:
                return {
                    "error": ("Service unavailable - running in local testing mode")
                }, 503

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
            return {"error": f"Failed to create club: {str(e)}"}, 500


@league_ns.route("/standings")
class LeagueStandings(Resource):
    @league_ns.param("countryId", "The country identifier")
    @league_ns.param("divisionTier", "The division tier", type=int)
    @league_ns.response(200, "Success")
    @league_ns.response(400, "Invalid request")
    @league_ns.response(401, "Authentication required")
    @league_ns.response(500, "Internal server error")
    @require_auth
    def get(self):
        """Get league standings"""
        try:
            country_id = request.args.get("countryId")
            division_tier = request.args.get("divisionTier", type=int)

            if not country_id or division_tier is None:
                return {"error": "Missing countryId or divisionTier parameters"}, 400

            if not firestore_helper:
                return {
                    "error": ("Service unavailable - running in local testing mode")
                }, 503

            standings = firestore_helper.get_league_standings(country_id, division_tier)

            return jsonify(
                {
                    "countryId": country_id,
                    "divisionTier": division_tier,
                    "standings": standings,
                }
            )

        except Exception as e:
            return {"error": f"Failed to get standings: {str(e)}"}, 500


@player_ns.route("/<string:player_id>")
class PlayerDetail(Resource):
    @player_ns.response(200, "Success")
    @player_ns.response(404, "Player not found")
    @player_ns.response(401, "Authentication required")
    @require_auth
    def get(self, player_id):
        """Get a specific player"""
        try:
            if not firestore_helper:
                return {
                    "error": "Service unavailable - running in local testing mode"
                }, 503

            player_data = firestore_helper.get_player(player_id)
            if not player_data:
                return {"error": "Player not found"}, 404

            return jsonify(player_data)

        except Exception as e:
            return {"error": f"Internal server error: {str(e)}"}, 500


@player_ns.route("")
class PlayerCreate(Resource):
    @player_ns.expect(player_request)
    @player_ns.response(200, "Success")
    @player_ns.response(400, "Invalid request")
    @player_ns.response(401, "Authentication required")
    @require_auth
    def post(self):
        """Create a new player"""
        try:
            if not request.json:
                return {"error": "No JSON data provided"}, 400

            required_fields = ["clubId", "countryId", "position"]
            for field in required_fields:
                if field not in request.json:
                    return {"error": f"Missing required field: {field}"}, 400

            club_id = request.json["clubId"]
            country_id = request.json["countryId"]
            position = request.json["position"]
            age = request.json.get("age")

            if not firestore_helper:
                return {
                    "error": "Service unavailable - running in local testing mode"
                }, 503

            club_data = firestore_helper.get_club(club_id)
            if not club_data:
                return {"error": "Club not found"}, 404

            division_tier = club_data.get("divisionTier", 10)

            from models.player import generate_random_player

            player = generate_random_player(
                club_id, country_id, position, division_tier
            )

            if age is not None:
                if age < 16 or age > 45:
                    return {"error": "Age must be between 16 and 45"}, 400
                player.age = age

            if division_tier <= 9 and not player.is_professional_eligible():
                return {
                    "error": "Player must be at least 21 years old for professional divisions"
                }, 400

            player_id = firestore_helper.save_player(player)

            return jsonify(
                {
                    "playerId": player_id,
                    "message": "Player created successfully",
                    "player": player.to_dict(),
                }
            )

        except Exception as e:
            return {"error": f"Internal server error: {str(e)}"}, 500


@player_ns.route("/<string:player_id>/renew-contract")
class PlayerContractRenewal(Resource):
    @player_ns.expect(contract_renewal_request)
    @player_ns.response(200, "Success")
    @player_ns.response(400, "Invalid request")
    @player_ns.response(404, "Player not found")
    @player_ns.response(401, "Authentication required")
    @require_auth
    def post(self, player_id):
        """Renew player contract"""
        try:
            if not request.json:
                return {"error": "No JSON data provided"}, 400

            required_fields = ["offeredSalary", "yearsOffered"]
            for field in required_fields:
                if field not in request.json:
                    return {"error": f"Missing required field: {field}"}, 400

            offered_salary = request.json["offeredSalary"]
            years_offered = request.json["yearsOffered"]

            if offered_salary <= 0 or years_offered <= 0:
                return {"error": "Salary and years must be positive"}, 400

            if not firestore_helper:
                return {
                    "error": "Service unavailable - running in local testing mode"
                }, 503

            player_data = firestore_helper.get_player(player_id)
            if not player_data:
                return {"error": "Player not found"}, 404

            from models.player import Player

            player = Player.from_dict(player_data)

            club_data = firestore_helper.get_club(player.club_id)
            if not club_data:
                return {"error": "Player's club not found"}, 404

            division_tier = club_data.get("divisionTier", 10)

            similar_players = firestore_helper.get_players_by_division_and_position(
                division_tier, player.position, player.country_id
            )

            if similar_players:
                total_salary = sum(
                    p.get("contract", {}).get("salary", 0) for p in similar_players
                )
                avg_salary = int(total_salary / len(similar_players))
            else:
                avg_salary = 0

            accepts_offer = player.evaluate_contract_offer(offered_salary, avg_salary)

            response_data = {
                "playerId": player_id,
                "offeredSalary": offered_salary,
                "yearsOffered": years_offered,
                "accepted": accepts_offer,
                "averageSimilarSalary": avg_salary,
                "similarPlayersCount": len(similar_players),
            }

            if accepts_offer:
                player.contract.salary = offered_salary
                player.contract.years_remaining = years_offered

                update_data = {
                    "contract": {
                        "salary": offered_salary,
                        "years_remaining": years_offered,
                        "bonus_clause": player.contract.bonus_clause,
                        "transfer_clause": player.contract.transfer_clause,
                    }
                }

                firestore_helper.update_player(player_id, update_data)
                response_data["message"] = "Contract renewal accepted and updated"
            else:
                response_data["message"] = "Contract renewal rejected"

            return jsonify(response_data)

        except Exception as e:
            return {"error": f"Internal server error: {str(e)}"}, 500


@player_ns.route("/<string:player_id>/retire")
class PlayerRetirement(Resource):
    @player_ns.response(200, "Success")
    @player_ns.response(404, "Player not found")
    @player_ns.response(401, "Authentication required")
    @require_auth
    def post(self, player_id):
        """Retire a player"""
        try:
            if not firestore_helper:
                return {
                    "error": "Service unavailable - running in local testing mode"
                }, 503

            player_data = firestore_helper.get_player(player_id)
            if not player_data:
                return {"error": "Player not found"}, 404

            from models.player import Player

            player = Player.from_dict(player_data)

            should_retire = player.should_retire()

            response_data = {
                "playerId": player_id,
                "playerAge": player.age,
                "retired": should_retire,
            }

            if should_retire:
                from datetime import datetime

                update_data = {
                    "retired": True,
                    "retiredAt": datetime.now().isoformat(),
                    "clubId": None,
                }

                firestore_helper.update_player(player_id, update_data)
                response_data["message"] = "Player has retired"
            else:
                response_data["message"] = "Player chooses to continue playing"

            return jsonify(response_data)

        except Exception as e:
            return {"error": f"Internal server error: {str(e)}"}, 500


@player_ns.route("/<string:player_id>/assess-transfer")
class PlayerTransferAssessment(Resource):
    @player_ns.expect(transfer_assessment_request)
    @player_ns.response(200, "Success")
    @player_ns.response(400, "Invalid request")
    @player_ns.response(404, "Player not found")
    @player_ns.response(401, "Authentication required")
    @require_auth
    def post(self, player_id):
        """Assess transfer offer for a player"""
        try:
            if not request.json:
                return {"error": "No JSON data provided"}, 400

            required_fields = ["offeredSalary", "targetClubId"]
            for field in required_fields:
                if field not in request.json:
                    return {"error": f"Missing required field: {field}"}, 400

            offered_salary = request.json["offeredSalary"]
            target_club_id = request.json["targetClubId"]

            if offered_salary <= 0:
                return {"error": "Salary must be positive"}, 400

            if not firestore_helper:
                return {
                    "error": "Service unavailable - running in local testing mode"
                }, 503

            player_data = firestore_helper.get_player(player_id)
            if not player_data:
                return {"error": "Player not found"}, 404

            from models.player import Player

            player = Player.from_dict(player_data)

            current_club_data = firestore_helper.get_club(player.club_id)
            if not current_club_data:
                return {"error": "Player's current club not found"}, 404

            target_club_data = firestore_helper.get_club(target_club_id)
            if not target_club_data:
                return {"error": "Target club not found"}, 404

            current_club_tier = current_club_data.get("divisionTier", 10)
            target_club_tier = target_club_data.get("divisionTier", 10)

            if target_club_tier <= 9 and not player.is_professional_eligible():
                return {
                    "error": "Player must be at least 21 years old for professional divisions"
                }, 400

            accepts_transfer = player.evaluate_transfer_offer(
                offered_salary, target_club_tier, current_club_tier
            )

            response_data = {
                "playerId": player_id,
                "offeredSalary": offered_salary,
                "currentSalary": player.contract.salary,
                "targetClubId": target_club_id,
                "currentClubTier": current_club_tier,
                "targetClubTier": target_club_tier,
                "accepted": accepts_transfer,
            }

            if accepts_transfer:
                response_data["message"] = "Transfer offer accepted"
            else:
                response_data["message"] = "Transfer offer rejected"

            return jsonify(response_data)

        except Exception as e:
            return {"error": f"Internal server error: {str(e)}"}, 500


@api.route("/health")
class HealthCheck(Resource):
    @api.response(200, "Service is healthy")
    def get(self):
        """Health check endpoint for Cloud Run"""
        return {"status": "healthy", "service": "volleyball-simulator"}, 200


if __name__ == "__main__":
    import os

    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
