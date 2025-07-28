#!/usr/bin/env python3
"""
Test script for the Season Management API
"""

from utils.constants import COUNTRIES
from game_engine.season_management import SeasonManager
from utils.firestore_helpers import FirestoreHelper

def test_imports():
    """Test that all imports work correctly"""
    print('✓ All imports successful')
    print(f'✓ Found {len(COUNTRIES)} countries: {list(COUNTRIES.keys())}')
    print('✓ Season management system ready')
    return True

def test_countries():
    """Test that all 12 countries are properly configured"""
    expected_countries = [
        'volcania', 'coastalia', 'forestland', 'desertia', 'northlands', 
        'islandia', 'plainscountry', 'stonehills', 'riverside', 'windlands', 
        'sunlands', 'mistcountry'
    ]
    
    print(f"Expected {len(expected_countries)} countries")
    print(f"Found {len(COUNTRIES)} countries")
    
    missing = set(expected_countries) - set(COUNTRIES.keys())
    extra = set(COUNTRIES.keys()) - set(expected_countries)
    
    if missing:
        print(f"✗ Missing countries: {missing}")
        return False
    
    if extra:
        print(f"✗ Extra countries: {extra}")
        return False
    
    print("✓ All 12 countries properly configured")
    
    for country_id, country_data in COUNTRIES.items():
        if 'name' not in country_data or 'modifiers' not in country_data:
            print(f"✗ Country {country_id} missing name or modifiers")
            return False
    
    print("✓ All countries have proper structure")
    return True

def test_season_config():
    """Test season configuration"""
    from utils.constants import GAME_CONFIG
    
    if 'SEASON' not in GAME_CONFIG:
        print("✗ SEASON config missing from GAME_CONFIG")
        return False
    
    season_config = GAME_CONFIG['SEASON']
    required_keys = ['DEFAULT_DURATION_MINUTES', 'CLUBS_PER_DIVISION', 'TOTAL_DIVISIONS']
    
    for key in required_keys:
        if key not in season_config:
            print(f"✗ Missing {key} in SEASON config")
            return False
    
    print("✓ Season configuration properly set up")
    return True

if __name__ == "__main__":
    print("Testing Season Management API Implementation...")
    print("=" * 50)
    
    tests = [
        test_imports,
        test_countries, 
        test_season_config
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with error: {e}")
            print()
    
    print(f"Results: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! Season API is ready.")
    else:
        print("❌ Some tests failed. Please check the implementation.")
