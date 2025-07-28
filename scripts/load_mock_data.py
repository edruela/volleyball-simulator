#!/usr/bin/env python3
"""
Script to load mock data into Firestore for local testing
"""

import os
import sys
from google.cloud import firestore

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.firestore_helpers import FirestoreHelper


def main():
    """Load mock data into Firestore"""
    try:
        db = firestore.Client()
        helper = FirestoreHelper(db)

        print("Loading mock data into Firestore...")
        print("This will create:")
        print("- 3 countries (volcania, coastalia, forestland)")
        print("- 60 clubs (4 clubs per division, divisions 15-19, across 3 countries)")
        print("- ~720 players (12 players per club)")

        helper.create_sample_data()

        print("\n✅ Mock data loaded successfully!")
        print("\nYou can now test the API with club IDs from the created clubs.")
        print("Use the get_league_standings endpoint to see available clubs:")
        print("GET /get_league_standings?countryId=volcania&divisionTier=15")

    except Exception as e:
        print(f"❌ Error loading mock data: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
