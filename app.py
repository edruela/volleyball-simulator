"""
Flask application for Volleyball Manager
Converted from Cloud Functions to Cloud Run deployment
"""

import json
from typing import Dict, Any, Union, Tuple
from flask import Flask, request, jsonify
from flask_restx import Api, Resource, fields
from google.cloud import firestore
from game_engine.match_simulation import VolleyballSimulator
from models.club import Club
from models.player import Player
from utils.firestore_helpers import FirestoreHelper

app = Flask(__name__)
api = Api(app, version='1.0', title='Volleyball Simulator API',
          description='A volleyball simulation and management API')

# Define namespaces
match_ns = api.namespace('matches', description='Match operations')
club_ns = api.namespace('clubs', description='Club operations')
league_ns = api.namespace('leagues', description='League operations')

# Define models for request/response documentation
tactics_model = api.model('Tactics', {
    'formation': fields.String(required=True, example='5-1'),
    'intensity': fields.Float(required=True, example=1.0),
    'style': fields.String(required=True, example='balanced')
})

match_request = api.model('MatchRequest', {
    'homeClubId': fields.String(required=True, description='Home club ID'),
    'awayClubId': fields.String(required=True, description='Away club ID'),
    'tactics': fields.Nested(tactics_model)
})

club_request = api.model('ClubRequest', {
    'name': fields.String(required=True, description='Club name'),
    'countryId': fields.String(required=True, description='Country ID'),
    'ownerId': fields.String(required=True, description='Owner ID')
})

# Initialize other components
db = firestore.Client()
firestore_helper = FirestoreHelper(db)
volleyball_sim = VolleyballSimulator()


@match_ns.route('/simulate')
class MatchSimulation(Resource):
    @match_ns.expect(match_request)
    @match_ns.response(200, 'Match simulated successfully')
    @match_ns.response(400, 'Invalid request')
    @match_ns.response(404, 'Club not found')
    @match_ns.response(500, 'Internal server error')
    def post(self):
        """Simulate a volleyball match"""
        try:
            request_json = request.get_json(silent=True)
            if not request_json:
                return jsonify({"error": "No JSON data provided"}), 400

            home_club_id = request_json.get("homeClubId")
            away_club_id = request_json.get("awayClubId")

            if not home_club_id or not away_club_id:
                return jsonify({"error": "Missing club IDs"}), 400

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
                    "home": {"formation": "5-1", "intensity": 1.0, "style": "balanced"},
                    "away": {"formation": "5-1", "intensity": 1.0, "style": "balanced"},
                },
            )

            match_result = volleyball_sim.simulate_match(home_team, away_team, tactics)

            match_id = firestore_helper.save_match(match_result)
            match_result["matchId"] = match_id

            return jsonify(match_result)

        except Exception as e:
            return jsonify({"error": f"Match simulation failed: {str(e)}"}), 500


@club_ns.route('')
class ClubOperations(Resource):
    @club_ns.param('clubId', 'The club identifier')
    @club_ns.response(200, 'Success')
    @club_ns.response(400, 'Invalid request')
    @club_ns.response(404, 'Club not found')
    def get(self):
        """Get club information"""
        try:
            club_id = request.args.get("clubId")
            if not club_id:
                return jsonify({"error": "Missing clubId parameter"}), 400

            club_data = firestore_helper.get_club(club_id)
            if not club_data:
                return jsonify({"error": "Club not found"}), 404

            players = firestore_helper.get_club_players(club_id)
            club_data["players"] = players

            return jsonify(club_data)

        except Exception as e:
            return jsonify({"error": f"Failed to get club: {str(e)}"}), 500

    @club_ns.expect(club_request)
    @club_ns.response(200, 'Club created successfully')
    @club_ns.response(400, 'Invalid request')
    @club_ns.response(500, 'Internal server error')
    def post(self):
        """Create a new club"""
        try:
            request_json = request.get_json(silent=True)
            if not request_json:
                return jsonify({"error": "No JSON data provided"}), 400

            required_fields = ["name", "countryId", "ownerId"]
            for field in required_fields:
                if field not in request_json:
                    return jsonify({"error": f"Missing required field: {field}"}), 400

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


@league_ns.route('/standings')
class LeagueStandings(Resource):
    @league_ns.param('countryId', 'The country identifier')
    @league_ns.param('divisionTier', 'The division tier', type=int)
    @league_ns.response(200, 'Success')
    @league_ns.response(400, 'Invalid request')
    @league_ns.response(500, 'Internal server error')
    def get(self):
        """Get league standings"""
        try:
            country_id = request.args.get("countryId")
            division_tier = request.args.get("divisionTier", type=int)

            if not country_id or division_tier is None:
                return (
                    jsonify({"error": "Missing countryId or divisionTier parameters"}),
                    400,
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


@api.route('/health')
class HealthCheck(Resource):
    @api.response(200, 'Service is healthy')
    def get(self):
        """Health check endpoint for Cloud Run"""
        return {"status": "healthy", "service": "volleyball-simulator"}, 200


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=False)
