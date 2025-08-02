"""
Flask application for Volleyball Manager
Cloud Run deployment with containerized serverless architecture
Enhanced with comprehensive error handling, logging, and resilience features
"""

import os
import sys
import logging
import traceback
import time
from typing import Optional, Dict, Any, Type
from flask import Flask, request, jsonify, g
from flask_restx import Api, Resource, fields  # type: ignore
from flask_cors import CORS
from google.cloud import firestore  # type: ignore
from google.cloud.logging import Client as LoggingClient
import firebase_admin
from firebase_admin import credentials
import json
import base64


# Configure structured logging for Cloud Run
def setup_logging():
    """Configure structured logging for Cloud Run deployment"""
    # Use Cloud Logging in production, stdout in development
    if os.getenv("GOOGLE_CLOUD_PROJECT"):
        try:
            client = LoggingClient()
            client.setup_logging()
        except Exception as e:
            # Fallback to basic logging if Cloud Logging fails
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            )
            logging.warning(f"Failed to setup Cloud Logging, using basic logging: {e}")
    else:
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )

    return logging.getLogger(__name__)


logger = setup_logging()

# Import application modules with error handling
VolleyballSimulator: Optional[Type[Any]] = None
FirestoreHelper: Optional[Type[Any]] = None

try:
    from game_engine.match_simulation import VolleyballSimulator as _VolleyballSimulator

    VolleyballSimulator = _VolleyballSimulator
    logger.info("Successfully imported VolleyballSimulator")
except ImportError as e:
    logger.error(f"Failed to import VolleyballSimulator: {e}")
    VolleyballSimulator = None

try:
    from utils.firestore_helpers import FirestoreHelper as _FirestoreHelper

    FirestoreHelper = _FirestoreHelper
    logger.info("Successfully imported FirestoreHelper")
except ImportError as e:
    logger.error(f"Failed to import FirestoreHelper: {e}")
    FirestoreHelper = None

try:
    from utils.auth import require_auth

    logger.info("Successfully imported auth utilities")
except ImportError as e:
    logger.error(f"Failed to import auth utilities: {e}")

    # Create a dummy auth decorator if import fails
    def require_auth(f):
        return f


# Environment validation
def validate_environment():
    """Validate required environment variables and configuration"""
    required_vars = []
    optional_vars = {
        "GOOGLE_CLOUD_PROJECT": "Cloud project ID for logging and Firestore",
        "FIREBASE_ADMIN_KEY": "Firebase admin service account key (base64 encoded)",
        "PORT": "Server port (defaults to 8080)",
        "SKIP_AUTH": "Skip authentication for development (defaults to false)",
    }

    missing_critical = []
    warnings = []

    # Check for Firebase credentials if authentication is required
    if os.getenv("SKIP_AUTH", "false").lower() != "true":
        if not os.getenv("FIREBASE_ADMIN_KEY"):
            missing_critical.append("FIREBASE_ADMIN_KEY (required for authentication)")

    # Log environment status
    for var, description in optional_vars.items():
        value = os.getenv(var)
        if value:
            logger.info(f"Environment variable {var}: configured")
        else:
            warnings.append(f"{var}: not set - {description}")

    if warnings:
        logger.warning("Optional environment variables not set:")
        for warning in warnings:
            logger.warning(f"  - {warning}")

    if missing_critical:
        logger.error("Critical environment variables missing:")
        for missing in missing_critical:
            logger.error(f"  - {missing}")
        return False

    return True


# Service status tracking
class ServiceStatus:
    def __init__(self):
        self.firebase_initialized = False
        self.firestore_connected = False
        self.simulator_available = False
        self.initialization_errors = []

    def add_error(self, service: str, error: str):
        self.initialization_errors.append(f"{service}: {error}")
        logger.error(f"Service {service} failed: {error}")

    def is_healthy(self):
        return (
            self.firebase_initialized
            or os.getenv("SKIP_AUTH", "false").lower() == "true"
        ) and (self.firestore_connected and self.simulator_available)


service_status = ServiceStatus()

# Initialize Flask app with error handling
try:
    app = Flask(__name__)
    CORS(app, origins="*", allow_headers=["Content-Type", "Authorization"])

    # Configure app settings
    app.config["JSON_SORT_KEYS"] = False
    app.config["JSONIFY_PRETTYPRINT_REGULAR"] = True

    # Initialize API with error handling
    api = Api(
        app,
        version="1.0",
        title="Volleyball Simulator API",
        description="A volleyball simulation and management API with enhanced error handling",
        doc=(
            "/swagger-ui"
            if os.getenv("ENVIRONMENT", "production") != "production"
            else False
        ),
        catch_all_404s=True,
    )

    logger.info("Flask application initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Flask application: {e}")
    sys.exit(1)

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


# Firebase initialization with retry logic
def initialize_firebase_with_retry(max_retries: int = 3) -> bool:
    """Initialize Firebase with retry logic and comprehensive error handling"""
    if os.getenv("SKIP_AUTH", "false").lower() == "true":
        logger.info("Authentication disabled via SKIP_AUTH environment variable")
        service_status.firebase_initialized = True
        return True

    if firebase_admin._apps:
        logger.info("Firebase already initialized")
        service_status.firebase_initialized = True
        return True

    firebase_key = os.getenv("FIREBASE_ADMIN_KEY")
    if not firebase_key:
        error_msg = "FIREBASE_ADMIN_KEY environment variable not set"
        service_status.add_error("Firebase", error_msg)
        return False

    for attempt in range(max_retries):
        try:
            logger.info(f"Initializing Firebase (attempt {attempt + 1}/{max_retries})")

            # Decode base64 string to JSON
            decoded_key = base64.b64decode(firebase_key).decode("utf-8")
            cred_dict = json.loads(decoded_key)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)

            logger.info("Firebase initialized successfully")
            service_status.firebase_initialized = True
            return True

        except json.JSONDecodeError as e:
            error_msg = f"Invalid FIREBASE_ADMIN_KEY format - must be valid base64 encoded JSON: {e}"
            service_status.add_error("Firebase", error_msg)
            return False  # Don't retry for invalid format

        except ValueError as e:
            error_msg = f"Invalid Firebase credentials: {e}"
            service_status.add_error("Firebase", error_msg)
            return False  # Don't retry for invalid credentials

        except Exception as e:
            error_msg = f"Firebase initialization failed (attempt {attempt + 1}): {e}"
            logger.warning(error_msg)
            if attempt == max_retries - 1:
                service_status.add_error("Firebase", error_msg)
                return False
            time.sleep(2**attempt)  # Exponential backoff

    return False


# Firestore initialization with retry logic
def initialize_firestore_with_retry(max_retries: int = 3) -> Optional[firestore.Client]:
    """Initialize Firestore with retry logic and comprehensive error handling"""

    for attempt in range(max_retries):
        try:
            logger.info(f"Initializing Firestore (attempt {attempt + 1}/{max_retries})")

            # Try to create Firestore client
            db = firestore.Client()

            # Test connection with a simple operation
            test_doc_ref = db.collection("_health_check").document("test")
            test_doc_ref.get()  # This will raise an exception if connection fails

            logger.info("Firestore connected successfully")
            service_status.firestore_connected = True
            return db

        except Exception as e:
            error_msg = f"Firestore initialization failed (attempt {attempt + 1}): {e}"
            logger.warning(error_msg)
            if attempt == max_retries - 1:
                service_status.add_error("Firestore", error_msg)
                return None
            time.sleep(2**attempt)  # Exponential backoff

    return None


# Initialize services with comprehensive error handling
logger.info("Starting service initialization...")

# Validate environment first
if not validate_environment():
    logger.error(
        "Environment validation failed, but continuing with limited functionality"
    )

# Initialize Firebase
firebase_initialized = initialize_firebase_with_retry()

# Initialize Firestore
db = initialize_firestore_with_retry()

# Initialize Firestore helper
firestore_helper = None
if db and FirestoreHelper is not None:
    try:
        firestore_helper = FirestoreHelper(db)
        logger.info("FirestoreHelper initialized successfully")
    except Exception as e:
        error_msg = f"FirestoreHelper initialization failed: {e}"
        service_status.add_error("FirestoreHelper", error_msg)

# Initialize volleyball simulator
volleyball_sim = None
if VolleyballSimulator is not None:
    try:
        volleyball_sim = VolleyballSimulator()
        service_status.simulator_available = True
        logger.info("VolleyballSimulator initialized successfully")
    except Exception as e:
        error_msg = f"VolleyballSimulator initialization failed: {e}"
        service_status.add_error("VolleyballSimulator", error_msg)

# Log final initialization status
if service_status.is_healthy():
    logger.info("All critical services initialized successfully")
else:
    logger.warning("Some services failed to initialize:")
    for error in service_status.initialization_errors:
        logger.warning(f"  - {error}")
    logger.warning("Application will run with limited functionality")


# Global error handlers
@app.errorhandler(404)
def not_found(error):
    logger.warning(f"404 error: {request.url}")
    return jsonify({"error": "Resource not found", "path": request.path}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    logger.warning(f"405 error: {request.method} {request.url}")
    return (
        jsonify(
            {
                "error": "Method not allowed",
                "method": request.method,
                "path": request.path,
            }
        ),
        405,
    )


@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error: {error}")
    logger.error(f"Request: {request.method} {request.url}")
    logger.error(f"Traceback: {traceback.format_exc()}")
    return (
        jsonify(
            {
                "error": "Internal server error",
                "message": "An unexpected error occurred. Please try again later.",
                "request_id": getattr(g, "request_id", "unknown"),
            }
        ),
        500,
    )


@app.before_request
def before_request():
    """Log request details and add request ID for tracking"""
    import uuid

    g.request_id = str(uuid.uuid4())[:8]
    g.start_time = time.time()

    # Log request details (but not for health checks to reduce noise)
    if not request.path.endswith("/health"):
        logger.info(f"Request {g.request_id}: {request.method} {request.path}")


@app.after_request
def after_request(response):
    """Log response details and timing"""
    if hasattr(g, "start_time") and not request.path.endswith("/health"):
        duration = time.time() - g.start_time
        logger.info(
            f"Response {getattr(g, 'request_id', 'unknown')}: {response.status_code} ({duration:.3f}s)"
        )
    return response


# Utility function for safe service access
def safe_service_access(service_name: str, service_obj, fallback_response):
    """Safely access a service with fallback handling"""
    if service_obj is None:
        logger.warning(f"Service {service_name} is not available")
        return fallback_response
    return service_obj


# Input validation utilities
def validate_json_input(
    required_fields: list, optional_fields: Optional[dict] = None
) -> tuple:
    """Validate JSON input with detailed error reporting"""
    request_json = request.get_json(silent=True)
    if not request_json:
        return (
            None,
            {
                "error": "No JSON data provided",
                "details": "Request body must contain valid JSON",
            },
            400,
        )

    missing_fields = []
    invalid_fields = []

    # Check required fields
    for field in required_fields:
        if field not in request_json:
            missing_fields.append(field)
        elif not request_json[field] or (
            isinstance(request_json[field], str) and not request_json[field].strip()
        ):
            invalid_fields.append(f"{field} (empty or whitespace)")

    # Validate optional fields if provided
    if optional_fields:
        for field, validator in optional_fields.items():
            if field in request_json:
                try:
                    if not validator(request_json[field]):
                        invalid_fields.append(f"{field} (invalid format)")
                except Exception:
                    invalid_fields.append(f"{field} (validation error)")

    errors = []
    if missing_fields:
        errors.append(f"Missing required fields: {', '.join(missing_fields)}")
    if invalid_fields:
        errors.append(f"Invalid fields: {', '.join(invalid_fields)}")

    if errors:
        return (
            None,
            {
                "error": "Invalid request data",
                "details": "; ".join(errors),
                "required_fields": required_fields,
            },
            400,
        )

    return request_json, None, None


def safe_firestore_operation(operation_name: str, operation_func, *args, **kwargs):
    """Safely execute Firestore operations with error handling"""
    try:
        logger.debug(f"Executing Firestore operation: {operation_name}")
        result = operation_func(*args, **kwargs)
        logger.debug(f"Firestore operation {operation_name} completed successfully")
        return result, None
    except Exception as e:
        error_msg = f"Firestore operation {operation_name} failed: {str(e)}"
        logger.error(error_msg)
        logger.error(f"Traceback: {traceback.format_exc()}")
        return None, error_msg


@match_ns.route("/simulate")
class MatchSimulation(Resource):
    @match_ns.expect(match_request)
    @match_ns.response(200, "Match simulated successfully")
    @match_ns.response(400, "Invalid request")
    @match_ns.response(401, "Authentication required")
    @match_ns.response(404, "Club not found")
    @match_ns.response(500, "Internal server error")
    @match_ns.response(503, "Service unavailable")
    @require_auth
    def post(self):
        """Simulate a volleyball match with comprehensive error handling"""
        request_id = getattr(g, "request_id", "unknown")
        logger.info(f"Match simulation request {request_id} started")

        try:
            # Validate input
            request_json, error_response, status_code = validate_json_input(
                required_fields=["homeClubId", "awayClubId"],
                optional_fields={"tactics": lambda x: isinstance(x, dict)},
            )

            if error_response:
                logger.warning(
                    f"Request {request_id}: Input validation failed - {error_response}"
                )
                return error_response, status_code

            home_club_id = request_json["homeClubId"]
            away_club_id = request_json["awayClubId"]

            # Validate club IDs format (basic UUID check)
            import re

            uuid_pattern = re.compile(
                r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$",
                re.IGNORECASE,
            )
            if not uuid_pattern.match(home_club_id) or not uuid_pattern.match(
                away_club_id
            ):
                logger.warning(f"Request {request_id}: Invalid club ID format")
                return {
                    "error": "Invalid club ID format",
                    "details": "Club IDs must be valid UUIDs",
                }, 400

            # Check service availability
            if not firestore_helper:
                logger.error(f"Request {request_id}: Firestore service unavailable")
                return {
                    "error": "Service unavailable",
                    "details": "Database service is not available",
                    "retry_after": 30,
                }, 503

            if not volleyball_sim:
                logger.error(f"Request {request_id}: Volleyball simulator unavailable")
                return {
                    "error": "Service unavailable",
                    "details": "Match simulation service is not available",
                    "retry_after": 30,
                }, 503

            # Fetch club data with error handling
            home_club_data, error = safe_firestore_operation(
                "get_home_club", firestore_helper.get_club, home_club_id
            )
            if error:
                logger.error(
                    f"Request {request_id}: Failed to fetch home club - {error}"
                )
                return {
                    "error": "Database error",
                    "details": "Failed to retrieve home club data",
                }, 500

            away_club_data, error = safe_firestore_operation(
                "get_away_club", firestore_helper.get_club, away_club_id
            )
            if error:
                logger.error(
                    f"Request {request_id}: Failed to fetch away club - {error}"
                )
                return {
                    "error": "Database error",
                    "details": "Failed to retrieve away club data",
                }, 500

            # Check if clubs exist
            if not home_club_data:
                logger.warning(
                    f"Request {request_id}: Home club {home_club_id} not found"
                )
                return {"error": "Home club not found", "clubId": home_club_id}, 404

            if not away_club_data:
                logger.warning(
                    f"Request {request_id}: Away club {away_club_id} not found"
                )
                return {"error": "Away club not found", "clubId": away_club_id}, 404

            # Fetch players with error handling
            home_players, error = safe_firestore_operation(
                "get_home_players", firestore_helper.get_club_players, home_club_id
            )
            if error:
                logger.error(
                    f"Request {request_id}: Failed to fetch home players - {error}"
                )
                return {
                    "error": "Database error",
                    "details": "Failed to retrieve home team players",
                }, 500

            away_players, error = safe_firestore_operation(
                "get_away_players", firestore_helper.get_club_players, away_club_id
            )
            if error:
                logger.error(
                    f"Request {request_id}: Failed to fetch away players - {error}"
                )
                return {
                    "error": "Database error",
                    "details": "Failed to retrieve away team players",
                }, 500

            # Check if teams have enough players
            if len(home_players) < 6:
                logger.warning(
                    f"Request {request_id}: Home team has insufficient players ({len(home_players)})"
                )
                return {
                    "error": "Insufficient players",
                    "details": f"Home team needs at least 6 players, has {len(home_players)}",
                    "clubId": home_club_id,
                }, 400

            if len(away_players) < 6:
                logger.warning(
                    f"Request {request_id}: Away team has insufficient players ({len(away_players)})"
                )
                return {
                    "error": "Insufficient players",
                    "details": f"Away team needs at least 6 players, has {len(away_players)}",
                    "clubId": away_club_id,
                }, 400

            # Prepare team data
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

            # Process tactics with defaults
            tactics = request_json.get("tactics", {})
            default_tactics = {
                "home": {"formation": "5-1", "intensity": 1.0, "style": "balanced"},
                "away": {"formation": "5-1", "intensity": 1.0, "style": "balanced"},
            }

            # Merge with defaults
            for team in ["home", "away"]:
                if team not in tactics:
                    tactics[team] = default_tactics[team]
                else:
                    for key, default_value in default_tactics[team].items():
                        if key not in tactics[team]:
                            tactics[team][key] = default_value

            # Simulate match
            logger.info(f"Request {request_id}: Starting match simulation")
            try:
                match_result = volleyball_sim.simulate_match(
                    home_team, away_team, tactics
                )
                logger.info(f"Request {request_id}: Match simulation completed")
            except Exception as e:
                logger.error(
                    f"Request {request_id}: Match simulation failed - {str(e)}"
                )
                logger.error(f"Traceback: {traceback.format_exc()}")
                return {
                    "error": "Simulation error",
                    "details": "Failed to simulate match",
                    "retry_after": 5,
                }, 500

            # Save match result
            match_id, error = safe_firestore_operation(
                "save_match", firestore_helper.save_match, match_result
            )
            if error:
                logger.error(f"Request {request_id}: Failed to save match - {error}")
                # Return simulation result even if save fails
                logger.warning(
                    f"Request {request_id}: Returning simulation result without saving"
                )
                return jsonify(
                    {
                        **match_result,
                        "warning": "Match simulated successfully but not saved to database",
                        "matchId": None,
                    }
                )

            match_result["matchId"] = match_id
            logger.info(
                f"Request {request_id}: Match simulation completed successfully, saved as {match_id}"
            )

            return jsonify(match_result)

        except Exception as e:
            logger.error(
                f"Request {request_id}: Unexpected error in match simulation - {str(e)}"
            )
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "error": "Internal server error",
                "details": "An unexpected error occurred during match simulation",
                "request_id": request_id,
            }, 500


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
    @api.response(503, "Service is unhealthy")
    def get(self):
        """Comprehensive health check endpoint for Cloud Run and monitoring"""
        try:
            health_status = {
                "status": "unknown",
                "service": "volleyball-simulator",
                "timestamp": time.time(),
                "version": "1.0.0",
                "environment": os.getenv("ENVIRONMENT", "unknown"),
                "services": {
                    "firebase": {
                        "status": (
                            "healthy"
                            if service_status.firebase_initialized
                            else "unhealthy"
                        ),
                        "required": os.getenv("SKIP_AUTH", "false").lower() != "true",
                    },
                    "firestore": {
                        "status": (
                            "healthy"
                            if service_status.firestore_connected
                            else "unhealthy"
                        ),
                        "required": True,
                    },
                    "simulator": {
                        "status": (
                            "healthy"
                            if service_status.simulator_available
                            else "unhealthy"
                        ),
                        "required": True,
                    },
                },
                "initialization_errors": (
                    service_status.initialization_errors
                    if service_status.initialization_errors
                    else None
                ),
            }

            # Check if all required services are healthy
            all_required_healthy = True
            for service_name, service_info in health_status["services"].items():
                if service_info["required"] and service_info["status"] != "healthy":
                    all_required_healthy = False
                    break

            if all_required_healthy:
                health_status["status"] = "healthy"
                return health_status, 200
            else:
                health_status["status"] = "unhealthy"
                return health_status, 503

        except Exception as e:
            logger.error(f"Health check failed: {str(e)}")
            return {
                "status": "error",
                "service": "volleyball-simulator",
                "timestamp": time.time(),
                "error": f"Health check failed: {str(e)}",
            }, 503


@api.route("/ready")
class ReadinessCheck(Resource):
    @api.response(200, "Service is ready")
    @api.response(503, "Service is not ready")
    def get(self):
        """Readiness check for Kubernetes/Cloud Run probes"""
        if service_status.is_healthy():
            return {"status": "ready", "timestamp": time.time()}, 200
        else:
            return {
                "status": "not ready",
                "timestamp": time.time(),
                "details": "One or more required services are unavailable",
            }, 503


@api.route("/status")
class ServiceStatusEndpoint(Resource):
    @api.response(200, "Service status")
    def get(self):
        """Detailed service status for debugging"""
        return {
            "service": "volleyball-simulator",
            "timestamp": time.time(),
            "uptime": time.time() - app.config.get("START_TIME", time.time()),
            "environment": {
                "python_version": sys.version,
                "platform": sys.platform,
                "google_cloud_project": os.getenv("GOOGLE_CLOUD_PROJECT"),
                "port": os.getenv("PORT", "8080"),
                "skip_auth": os.getenv("SKIP_AUTH", "false"),
            },
            "services": {
                "firebase_initialized": service_status.firebase_initialized,
                "firestore_connected": service_status.firestore_connected,
                "simulator_available": service_status.simulator_available,
                "errors": service_status.initialization_errors,
            },
            "memory_usage": {
                "available": True  # Could add psutil for detailed memory info
            },
        }, 200


# Record startup time for uptime tracking
app.config["START_TIME"] = time.time()

# Log final startup status
logger.info(f"Volleyball Simulator API starting up...")
logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'unknown')}")
logger.info(f"Python version: {sys.version}")
logger.info(
    f"Services status: Firebase={service_status.firebase_initialized}, "
    f"Firestore={service_status.firestore_connected}, "
    f"Simulator={service_status.simulator_available}"
)

if service_status.initialization_errors:
    logger.warning(
        f"Startup completed with {len(service_status.initialization_errors)} errors"
    )
else:
    logger.info("Startup completed successfully")

if __name__ == "__main__":
    try:
        port = int(os.environ.get("PORT", 8080))
        debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"

        logger.info(f"Starting Flask development server on port {port}")
        logger.info(f"Debug mode: {debug_mode}")

        app.run(host="0.0.0.0", port=port, debug=debug_mode)
    except Exception as e:
        logger.error(f"Failed to start Flask application: {e}")
        sys.exit(1)
