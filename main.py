"""
Cloud Functions entry points for Volleyball Manager
"""
import json
from typing import Dict, Any
from flask import Request
from google.cloud import firestore
from game_engine.match_simulation import VolleyballSimulator
from models.club import Club
from models.player import Player
from utils.firestore_helpers import FirestoreHelper

db = firestore.Client()
firestore_helper = FirestoreHelper(db)
volleyball_sim = VolleyballSimulator()


def simulate_match(request: Request) -> Dict[str, Any]:
    """
    Cloud Function to simulate a volleyball match
    """
    try:
        request_json = request.get_json(silent=True)
        if not request_json:
            return {"error": "No JSON data provided"}, 400
        
        home_club_id = request_json.get('homeClubId')
        away_club_id = request_json.get('awayClubId')
        
        if not home_club_id or not away_club_id:
            return {"error": "Missing club IDs"}, 400
        
        home_club_data = firestore_helper.get_club(home_club_id)
        away_club_data = firestore_helper.get_club(away_club_id)
        
        if not home_club_data or not away_club_data:
            return {"error": "Club not found"}, 404
        
        home_players = firestore_helper.get_club_players(home_club_id)
        away_players = firestore_helper.get_club_players(away_club_id)
        
        home_team = {
            'id': home_club_id,
            'club': home_club_data,
            'players': home_players
        }
        
        away_team = {
            'id': away_club_id,
            'club': away_club_data,
            'players': away_players
        }
        
        tactics = request_json.get('tactics', {
            'home': {'formation': '5-1', 'intensity': 1.0, 'style': 'balanced'},
            'away': {'formation': '5-1', 'intensity': 1.0, 'style': 'balanced'}
        })
        
        match_result = volleyball_sim.simulate_match(home_team, away_team, tactics)
        
        match_id = firestore_helper.save_match(match_result)
        match_result['matchId'] = match_id
        
        return match_result
        
    except Exception as e:
        return {"error": f"Match simulation failed: {str(e)}"}, 500


def get_club(request: Request) -> Dict[str, Any]:
    """
    Cloud Function to get club information
    """
    try:
        club_id = request.args.get('clubId')
        if not club_id:
            return {"error": "Missing clubId parameter"}, 400
        
        club_data = firestore_helper.get_club(club_id)
        if not club_data:
            return {"error": "Club not found"}, 404
        
        players = firestore_helper.get_club_players(club_id)
        club_data['players'] = players
        
        return club_data
        
    except Exception as e:
        return {"error": f"Failed to get club: {str(e)}"}, 500


def create_club(request: Request) -> Dict[str, Any]:
    """
    Cloud Function to create a new club
    """
    try:
        request_json = request.get_json(silent=True)
        if not request_json:
            return {"error": "No JSON data provided"}, 400
        
        required_fields = ['name', 'countryId', 'ownerId']
        for field in required_fields:
            if field not in request_json:
                return {"error": f"Missing required field: {field}"}, 400
        
        club_id = firestore_helper.create_club(request_json)
        
        initial_players = firestore_helper.generate_initial_squad(club_id, request_json['countryId'])
        
        return {
            "clubId": club_id,
            "message": "Club created successfully",
            "playersGenerated": len(initial_players)
        }
        
    except Exception as e:
        return {"error": f"Failed to create club: {str(e)}"}, 500


def get_league_standings(request: Request) -> Dict[str, Any]:
    """
    Cloud Function to get league standings
    """
    try:
        country_id = request.args.get('countryId')
        division_tier = request.args.get('divisionTier', type=int)
        
        if not country_id or division_tier is None:
            return {"error": "Missing countryId or divisionTier parameters"}, 400
        
        standings = firestore_helper.get_league_standings(country_id, division_tier)
        
        return {
            "countryId": country_id,
            "divisionTier": division_tier,
            "standings": standings
        }
        
    except Exception as e:
        return {"error": f"Failed to get standings: {str(e)}"}, 500
