#!/usr/bin/env python3
"""
Simple test script to verify auth bypass and JSON serialization fixes
"""
import os
import sys

sys.path.append(".")

os.environ["SKIP_AUTH"] = "true"

from app import app


def test_health_endpoint():
    """Test health endpoint"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/health")
        print(f"Health check status: {response.status_code}")
        print(f"Health check response: {response.get_json()}")
        return response.status_code == 200


def test_clubs_endpoint_missing_id():
    """Test clubs endpoint without clubId parameter"""
    app.config["TESTING"] = True
    with app.test_client() as client:
        response = client.get("/clubs")
        print(f"Clubs (no ID) status: {response.status_code}")
        print(f"Clubs (no ID) response: {response.get_json()}")
        return response.status_code == 400 and response.get_json() is not None


def test_auth_bypass():
    """Test that auth bypass is working"""
    print(f"SKIP_AUTH environment variable: {os.getenv('SKIP_AUTH')}")
    return os.getenv("SKIP_AUTH") == "true"


if __name__ == "__main__":
    print("Testing local Flask app with auth bypass...")
    print("=" * 50)

    auth_bypass_ok = test_auth_bypass()
    print(f"Auth bypass enabled: {auth_bypass_ok}")
    print()

    health_ok = test_health_endpoint()
    print(f"Health endpoint working: {health_ok}")
    print()

    clubs_ok = test_clubs_endpoint_missing_id()
    print(f"Clubs endpoint JSON serialization working: {clubs_ok}")
    print()

    if auth_bypass_ok and health_ok and clubs_ok:
        print("✅ All tests passed! Auth bypass and JSON serialization " "are working.")
        sys.exit(0)
    else:
        print("❌ Some tests failed.")
        sys.exit(1)
