#!/usr/bin/env python3
"""
Comprehensive test script for diagnosing Cloud Run 500 errors
This script tests all potential failure points in the application startup
"""

import os
import sys
import traceback
import json
from unittest.mock import patch, MagicMock


def test_environment_variables():
    """Test if required environment variables are set"""
    print("=== Testing Environment Variables ===")
    
    # Check PORT
    port = os.environ.get("PORT", "8080")
    print(f"✓ PORT: {port}")
    
    # Check Firebase config
    firebase_key = os.environ.get("FIREBASE_ADMIN_KEY")
    if firebase_key:
        print("✓ FIREBASE_ADMIN_KEY is set")
        try:
            # Try to parse as JSON
            import base64
            decoded = base64.b64decode(firebase_key).decode('utf-8')
            parsed = json.loads(decoded)
            print("✓ FIREBASE_ADMIN_KEY is valid base64-encoded JSON")
        except Exception as e:
            print(f"⚠ FIREBASE_ADMIN_KEY format issue: {e}")
            try:
                # Try parsing directly as JSON
                parsed = json.loads(firebase_key)
                print("✓ FIREBASE_ADMIN_KEY is valid JSON (not base64)")
            except Exception as e2:
                print(f"✗ FIREBASE_ADMIN_KEY is not valid JSON: {e2}")
    else:
        print("⚠ FIREBASE_ADMIN_KEY not set (will run in local testing mode)")
    
    print()


def test_imports():
    """Test all critical imports"""
    print("=== Testing Imports ===")
    
    imports_to_test = [
        ("flask", "Flask"),
        ("flask_restx", "Api, Resource, fields"),
        ("flask_cors", "CORS"),
        ("google.cloud.firestore", "firestore"),
        ("game_engine.match_simulation", "VolleyballSimulator"),
        ("utils.firestore_helpers", "FirestoreHelper"),
        ("utils.auth", "require_auth"),
        ("models.club", "Club"),
        ("models.player", "Player, generate_random_player"),
    ]
    
    for module_name, import_items in imports_to_test:
        try:
            if module_name == "flask":
                from flask import Flask
            elif module_name == "flask_restx":
                from flask_restx import Api, Resource, fields
            elif module_name == "flask_cors":
                from flask_cors import CORS
            elif module_name == "google.cloud.firestore":
                from google.cloud import firestore
            elif module_name == "game_engine.match_simulation":
                from game_engine.match_simulation import VolleyballSimulator
            elif module_name == "utils.firestore_helpers":
                from utils.firestore_helpers import FirestoreHelper
            elif module_name == "utils.auth":
                from utils.auth import require_auth
            elif module_name == "models.club":
                from models.club import Club
            elif module_name == "models.player":
                from models.player import Player, generate_random_player
            
            print(f"✓ {module_name} ({import_items})")
        except Exception as e:
            print(f"✗ {module_name}: {e}")
            traceback.print_exc()
    
    print()


def test_firestore_initialization():
    """Test Firestore client initialization"""
    print("=== Testing Firestore Initialization ===")
    
    try:
        from google.cloud import firestore
        
        # Test without credentials (should fail gracefully)
        try:
            db = firestore.Client()
            print("✓ Firestore Client created (with credentials)")
        except Exception as e:
            print(f"⚠ Firestore Client creation failed: {e}")
            print("  This is expected in local testing without credentials")
        
        # Test FirestoreHelper with mock
        try:
            from utils.firestore_helpers import FirestoreHelper
            mock_db = MagicMock()
            helper = FirestoreHelper(mock_db)
            print("✓ FirestoreHelper instantiated with mock database")
        except Exception as e:
            print(f"✗ FirestoreHelper instantiation failed: {e}")
            traceback.print_exc()
            
    except Exception as e:
        print(f"✗ Firestore module import failed: {e}")
        traceback.print_exc()
    
    print()


def test_firebase_auth_initialization():
    """Test Firebase Auth initialization"""
    print("=== Testing Firebase Auth Initialization ===")
    
    try:
        from utils.auth import initialize_firebase
        import firebase_admin
        
        # Clear any existing Firebase apps
        if firebase_admin._apps:
            for app in firebase_admin._apps.values():
                firebase_admin.delete_app(app)
        
        firebase_key = os.environ.get("FIREBASE_ADMIN_KEY")
        if firebase_key:
            try:
                initialize_firebase()
                print("✓ Firebase initialized successfully")
            except Exception as e:
                print(f"⚠ Firebase initialization failed: {e}")
                print("  This may indicate invalid credentials")
        else:
            print("⚠ Skipping Firebase init (no credentials)")
            
    except Exception as e:
        print(f"✗ Firebase auth module error: {e}")
        traceback.print_exc()
    
    print()


def test_flask_app_creation():
    """Test Flask application creation"""
    print("=== Testing Flask App Creation ===")
    
    try:
        # Set environment to skip auth for testing
        os.environ["SKIP_AUTH"] = "true"
        
        # Import and test app creation
        from app import app
        print("✓ Flask app imported successfully")
        
        # Test app configuration
        print(f"✓ App debug mode: {app.debug}")
        print(f"✓ App testing mode: {app.testing}")
        
        # Test that routes are registered
        rules = [str(rule) for rule in app.url_map.iter_rules()]
        print(f"✓ Registered routes: {len(rules)}")
        
        # Key routes to check
        critical_routes = ["/health", "/matches/simulate", "/clubs"]
        for route in critical_routes:
            if any(route in rule for rule in rules):
                print(f"  ✓ {route} route found")
            else:
                print(f"  ⚠ {route} route not found")
                
    except Exception as e:
        print(f"✗ Flask app creation failed: {e}")
        traceback.print_exc()
    
    print()


def test_health_endpoint():
    """Test the health endpoint"""
    print("=== Testing Health Endpoint ===")
    
    try:
        os.environ["SKIP_AUTH"] = "true"
        from app import app
        
        with app.test_client() as client:
            response = client.get('/health')
            print(f"✓ Health endpoint status: {response.status_code}")
            
            if response.status_code == 200:
                data = response.get_json()
                print(f"✓ Health response: {data}")
            else:
                print(f"⚠ Health endpoint returned: {response.data}")
                
    except Exception as e:
        print(f"✗ Health endpoint test failed: {e}")
        traceback.print_exc()
    
    print()


def test_gunicorn_compatibility():
    """Test gunicorn WSGI server compatibility"""
    print("=== Testing Gunicorn Compatibility ===")
    
    try:
        import gunicorn
        print(f"✓ Gunicorn version: {gunicorn.__version__}")
        
        # Test WSGI application object
        os.environ["SKIP_AUTH"] = "true"
        from app import app
        
        # Test that app is WSGI callable
        if callable(app):
            print("✓ App is WSGI callable")
        else:
            print("✗ App is not WSGI callable")
            
        # Test with dummy WSGI environ
        try:
            environ = {
                'REQUEST_METHOD': 'GET',
                'PATH_INFO': '/health',
                'SERVER_NAME': 'localhost',
                'SERVER_PORT': '8080',
                'wsgi.version': (1, 0),
                'wsgi.url_scheme': 'http',
                'wsgi.input': None,
                'wsgi.errors': sys.stderr,
                'wsgi.multithread': False,
                'wsgi.multiprocess': True,
                'wsgi.run_once': False
            }
            
            start_response = MagicMock()
            response = app(environ, start_response)
            print("✓ WSGI interface test successful")
            
        except Exception as e:
            print(f"⚠ WSGI interface test failed: {e}")
            
    except Exception as e:
        print(f"✗ Gunicorn compatibility test failed: {e}")
        traceback.print_exc()
    
    print()


def test_docker_port_configuration():
    """Test Docker port configuration"""
    print("=== Testing Docker Port Configuration ===")
    
    # Test port parsing
    test_ports = ["8080", "80", "3000", "invalid"]
    
    for test_port in test_ports:
        try:
            port = int(test_port)
            print(f"✓ Port {test_port} is valid integer")
        except ValueError:
            print(f"⚠ Port {test_port} is invalid")
    
    # Test environment port
    env_port = os.environ.get("PORT", "8080")
    try:
        port = int(env_port)
        print(f"✓ Environment PORT={env_port} is valid")
    except ValueError:
        print(f"✗ Environment PORT={env_port} is invalid")
    
    print()


def test_memory_and_performance():
    """Test memory usage and performance"""
    print("=== Testing Memory and Performance ===")
    
    try:
        import psutil
        process = psutil.Process()
        
        # Memory before import
        mem_before = process.memory_info().rss / 1024 / 1024
        print(f"Memory before app import: {mem_before:.1f} MB")
        
        # Import app
        os.environ["SKIP_AUTH"] = "true"
        from app import app
        
        # Memory after import
        mem_after = process.memory_info().rss / 1024 / 1024
        print(f"Memory after app import: {mem_after:.1f} MB")
        print(f"Memory increase: {mem_after - mem_before:.1f} MB")
        
        if mem_after > 500:  # Cloud Run default memory limit check
            print("⚠ High memory usage detected")
        else:
            print("✓ Memory usage within reasonable limits")
            
    except ImportError:
        print("⚠ psutil not available, skipping memory test")
    except Exception as e:
        print(f"⚠ Memory test failed: {e}")
    
    print()


def test_cloud_run_specific_issues():
    """Test for Cloud Run specific issues"""
    print("=== Testing Cloud Run Specific Issues ===")
    
    # Test for Cloud Run metadata server access
    try:
        import requests
        # This should fail in local testing but shows what Cloud Run tries
        metadata_url = "http://metadata.google.internal/computeMetadata/v1/instance/service-accounts/default/token"
        headers = {"Metadata-Flavor": "Google"}
        
        try:
            response = requests.get(metadata_url, headers=headers, timeout=1)
            print("✓ Cloud Run metadata server accessible")
        except:
            print("⚠ Cloud Run metadata server not accessible (expected locally)")
            
    except ImportError:
        print("⚠ requests not available for metadata test")
    
    # Test for proper signal handling
    try:
        import signal
        print("✓ Signal module available for graceful shutdown")
    except:
        print("⚠ Signal module not available")
    
    # Test timezone (Cloud Run uses UTC)
    import datetime
    now = datetime.datetime.now()
    utc_now = datetime.datetime.utcnow()
    print(f"Local time: {now}")
    print(f"UTC time: {utc_now}")
    
    print()


def create_minimal_test_server():
    """Create a minimal test server for debugging"""
    print("=== Creating Minimal Test Server ===")
    
    try:
        from flask import Flask, jsonify
        
        minimal_app = Flask(__name__)
        
        @minimal_app.route('/health')
        def health():
            return jsonify({"status": "ok", "test": "minimal"})
        
        @minimal_app.route('/test-error')
        def test_error():
            raise Exception("Test error for debugging")
        
        print("✓ Minimal Flask app created")
        print("  Routes: /health, /test-error")
        
        # Test the minimal app
        with minimal_app.test_client() as client:
            response = client.get('/health')
            print(f"✓ Minimal app health check: {response.status_code}")
            
        return minimal_app
        
    except Exception as e:
        print(f"✗ Minimal app creation failed: {e}")
        return None


def main():
    """Run all diagnostic tests"""
    print("Cloud Run Deployment Diagnostic Tool")
    print("=" * 50)
    print()
    
    # Set testing environment
    os.environ["SKIP_AUTH"] = "true"
    
    test_functions = [
        test_environment_variables,
        test_imports,
        test_firestore_initialization,
        test_firebase_auth_initialization,
        test_flask_app_creation,
        test_health_endpoint,
        test_gunicorn_compatibility,
        test_docker_port_configuration,
        test_memory_and_performance,
        test_cloud_run_specific_issues,
        create_minimal_test_server,
    ]
    
    passed = 0
    failed = 0
    
    for test_func in test_functions:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ Test {test_func.__name__} failed: {e}")
            traceback.print_exc()
            failed += 1
        print()
    
    print("=" * 50)
    print(f"SUMMARY: {passed} tests passed, {failed} tests failed")
    
    if failed > 0:
        print("\nPOTENTIAL CLOUD RUN ISSUES:")
        print("1. Check Cloud Run environment variables (FIREBASE_ADMIN_KEY)")
        print("2. Verify Firebase service account key format")
        print("3. Check Cloud Run memory limits (512MB default)")
        print("4. Verify port configuration (must use $PORT)")
        print("5. Check startup timeout (Cloud Run has 240s limit)")
        print("6. Review application logs in Cloud Run console")
    else:
        print("\nAll tests passed! The issue might be:")
        print("1. Cloud Run specific environment differences")
        print("2. Network connectivity issues")
        print("3. Authentication/authorization problems")
        print("4. Cold start timeout issues")


if __name__ == "__main__":
    main()