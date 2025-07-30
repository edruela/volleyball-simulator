#!/usr/bin/env python3
"""
Script to load mock data into Firestore for local testing
"""

import os
import sys
from google.cloud import firestore  # type: ignore

from utils.firestore_helpers import FirestoreHelper

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    """Load mock data into Firestore"""
    try:
        db = firestore.Client(
            project=os.getenv("GOOGLE_CLOUD_PROJECT", "invweb-lab-public-2")
        )
        helper = FirestoreHelper(db)

        print("Loading mock data into Firestore...")
        print("This will create:")

        # Retrieve country names from sample data
        country_names = (
            helper.get_sample_country_names()
            if hasattr(helper, "get_sample_country_names")
            else ["volcania", "coastalia", "forestland"]
        )
        print(f"- {len(country_names)} countries ({', '.join(country_names)})")

        # Dynamically calculate club and division info
        sample_clubs = (
            helper.get_sample_clubs() if hasattr(helper, "get_sample_clubs") else []
        )
        divisions = set(
            club.get("divisionTier") for club in sample_clubs if "divisionTier" in club
        )
        clubs_per_division = {}
        for division in divisions:
            clubs_per_division[division] = sum(
                1 for club in sample_clubs if club.get("divisionTier") == division
            )
        total_clubs = len(sample_clubs)
        divisions_str = ", ".join(str(d) for d in sorted(divisions))
        clubs_per_division_str = ", ".join(
            f"{clubs_per_division[d]} clubs in division {d}" for d in sorted(divisions)
        )
        print(
            f"- {total_clubs} clubs ({clubs_per_division_str}, "
            f"divisions {divisions_str}, across {len(country_names)} "
            f"countries)"
        )

        # Dynamically calculate player info if possible
        sample_players = (
            helper.get_sample_players() if hasattr(helper, "get_sample_players") else []
        )
        players_per_club = (
            round(len(sample_players) / total_clubs) if total_clubs > 0 else 0
        )
        print(
            f"- ~{len(sample_players)} players "
            f"({players_per_club} players per club)"
        )

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
