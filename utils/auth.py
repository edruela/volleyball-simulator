"""
Firebase Authentication utilities for Volleyball Manager API
"""

from functools import wraps
from flask import request, jsonify
import firebase_admin
from firebase_admin import auth, credentials
import os
import json


def initialize_firebase():
    """Initialize Firebase Admin SDK if not already initialized"""
    if not firebase_admin._apps:
        firebase_key = os.getenv("FIREBASE_ADMIN_KEY")
        if firebase_key:
            try:
                cred_dict = json.loads(firebase_key)
                cred = credentials.Certificate(cred_dict)
            except json.JSONDecodeError:
                raise ValueError(
                    "Invalid FIREBASE_ADMIN_KEY format - must be valid JSON"
                )
        else:
            cred = credentials.ApplicationDefault()

        firebase_admin.initialize_app(cred)


def require_auth(f):
    """
    Decorator to require Firebase Authentication for API endpoints

    Expects Authorization header with format: Bearer <firebase_id_token>
    Adds user_id and user_email to request context if token is valid
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
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
            return f(*args, **kwargs)
        except Exception as e:
            return (
                jsonify({"error": f"Invalid token: {str(e)}"}),
                401,
            )

    return decorated_function
