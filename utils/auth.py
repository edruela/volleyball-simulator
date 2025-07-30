"""
Firebase Authentication utilities for Volleyball Manager API
"""

from functools import wraps
from flask import request, jsonify
import firebase_admin
from firebase_admin import auth, credentials
import os
import json
import base64


def initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized"""
    if not firebase_admin._apps:
        firebase_key = os.getenv("FIREBASE_ADMIN_KEY")
        if not firebase_key:
            raise ValueError("FIREBASE_ADMIN_KEY environment variable not set")

        try:
            # Decode base64 string to JSON
            decoded_key = base64.b64decode(firebase_key).decode("utf-8")
            cred_dict = json.loads(decoded_key)
            cred = credentials.Certificate(cred_dict)
            firebase_admin.initialize_app(cred)
        except json.JSONDecodeError:
            raise ValueError("Invalid FIREBASE_ADMIN_KEY format - must be valid JSON")
        except Exception as e:
            raise ValueError(f"Failed to initialize Firebase: {str(e)}")


def require_auth(f):
    """
    Decorator to require Firebase Authentication for API endpoints

    Expects Authorization header with format: Bearer <firebase_id_token>
    Adds user_id, user_email and user_roles to request context if token is valid
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if os.getenv("SKIP_AUTH", "false").lower() == "true":
            return f(*args, **kwargs)

        if not firebase_admin._apps:
            initialize_firebase()

        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return jsonify({"error": "Authorization header is required"}), 401

        try:
            token = auth_header.split(" ")[1]
        except IndexError:
            return (
                jsonify(
                    {
                        "error": (
                            "Invalid authorization header format. "
                            "Use: Bearer <token>"
                        )
                    }
                ),
                401,
            )

        try:
            decoded_token = auth.verify_id_token(token)
            request.user_id = decoded_token["uid"]
            request.user_email = decoded_token.get("email")
            request.user_roles = decoded_token.get("roles", [])
            return f(*args, **kwargs)
        except auth.ExpiredIdTokenError:
            return jsonify({"error": "Token has expired"}), 401
        except auth.RevokedIdTokenError:
            return jsonify({"error": "Token has been revoked"}), 401
        except auth.InvalidIdTokenError:
            return jsonify({"error": "Invalid token"}), 401
        except Exception as e:
            return (
                jsonify({"error": f"Authentication failed: {str(e)}"}),
                401,
            )

    return decorated_function
