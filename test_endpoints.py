#!/usr/bin/env python3
"""Test the health endpoints of the improved application"""

import os

os.environ["SKIP_AUTH"] = "true"

from app import app


def test_endpoints():
    print("=== Testing Health Endpoints ===")

    with app.test_client() as client:
        # Test health endpoint
        response = client.get("/health")
        print(f"Health endpoint: {response.status_code}")
        if response.status_code != 200:
            data = response.get_json()
            print(f"Health response: {data}")

        # Test ready endpoint
        response = client.get("/ready")
        print(f"Ready endpoint: {response.status_code}")

        # Test status endpoint
        response = client.get("/status")
        print(f"Status endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.get_json()
            print(f"Status data keys: {list(data.keys())}")


if __name__ == "__main__":
    test_endpoints()
