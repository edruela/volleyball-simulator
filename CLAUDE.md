# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a comprehensive volleyball team management simulation game built with Python Flask backend and designed for Cloud Run deployment. The project simulates volleyball matches, manages clubs and players, and handles league structures across multiple fictional countries.

## Key Commands

### Development and Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run all tests
pytest

# Run tests with coverage
pytest --cov=. --cov-report=html --cov-report=term-missing

# Code formatting and linting
black .
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
mypy . --ignore-missing-imports

# Run all quality checks (CI pipeline)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics && \
black --check --diff . && \
mypy . --ignore-missing-imports && \
pytest --cov=. --cov-report=term-missing
```

### Local Development
```bash
# Run Flask development server
python app.py

# Run with Docker
docker build -t volleyball-simulator .
docker run -p 8080:8080 volleyball-simulator

# Load mock data for testing (requires Firestore emulator)
export FIRESTORE_EMULATOR_HOST=localhost:8080
python scripts/load_mock_data.py
```

### Testing Specific Components
```bash
# Test specific file
pytest tests/test_models.py

# Test with verbose output
pytest -v

# Run match simulation benchmark
python -c "from game_engine.match_simulation import VolleyballSimulator; print('Simulator loaded')"
```

## Architecture Overview

### Core Components
- **Flask Application** (`app.py`): Main API server with RESTful endpoints
- **Game Engine** (`game_engine/`): Match simulation and league management logic
- **Models** (`models/`): Data structures for clubs, players, competitions
- **Utils** (`utils/`): Database helpers, authentication, constants

### Tech Stack
- **Backend**: Python 3.12+ with Flask and Flask-RESTX
- **Database**: Google Cloud Firestore (NoSQL document store)
- **Deployment**: Google Cloud Run (containerized serverless)
- **Testing**: pytest with coverage reporting
- **Code Quality**: black, flake8, mypy

### Key Features
- Advanced volleyball match simulation with realistic rally mechanics
- 19-tier league system with promotion/relegation
- Player development system with age-based progression
- Financial management and transfer market
- Multi-country support with unique player modifiers

## Data Models

### Core Entities
- **Club**: Team with finances, facilities, tactics, and player roster
- **Player**: Individual with attributes, contract, condition, and career stats  
- **Match**: Game simulation with detailed events and statistics
- **Competition**: Leagues and tournaments with participants and results
- **Season**: Time-bound container for all competitions

### Database Collections
- `clubs`: Club data with financial and tactical information
- `players`: Player attributes, contracts, and career statistics
- `matches`: Match results with detailed simulation events
- `competitions`: Tournament structures and standings
- `seasons`: Season metadata and scheduling

## Game Logic

### Match Simulation
The volleyball simulator (`game_engine/match_simulation.py`) implements:
- Realistic rally mechanics with serve, attack, defense phases
- Team strength calculation based on player attributes and tactics
- Home advantage, fatigue, and momentum factors
- Event-driven simulation with detailed statistics

### Player Development
- Age-based attribute progression with peak and decline phases
- Position-specific attribute importance and development rates
- Injury system affecting performance and availability
- Contract negotiations and transfer mechanics

### Competition Structure
- **Domestic**: 19-tier leagues (Elite → Professional → Semi-Pro → Amateur)
- **Continental**: Champions League, Professional Cup, Amateur Championship
- **Scheduling**: Automated season creation with configurable duration

## Testing Strategy

### Test Categories
- **Unit Tests**: Individual component functionality
- **Integration Tests**: API endpoints with mocked database
- **Simulation Tests**: Match engine accuracy and performance
- **Mock Data**: Comprehensive test fixtures for all entities

### Coverage Requirements
- Maintain >80% test coverage across all modules
- Critical game logic (simulation engine) requires >95% coverage
- All API endpoints must have integration tests

## Firebase Integration

### Authentication
- All API endpoints (except `/health`) require Firebase ID tokens
- Use `@require_auth` decorator for protected routes
- Token validation through Firebase Admin SDK

### Firestore Operations
- Use `FirestoreHelper` class for database operations
- Implement proper error handling and transaction support
- Mock Firestore operations in tests using dependency injection

## API Endpoints

### Core Operations
- `POST /matches/simulate`: Run volleyball match simulations
- `GET /clubs`: Retrieve club information and player rosters
- `POST /clubs`: Create new player-controlled clubs
- `GET /leagues/standings`: Get league tables and standings
- `POST /start_season`: Initialize new seasons with competitions

### Development Endpoints
- `GET /health`: Application health check (no auth required)
- Mock data endpoints for testing with Firestore emulator

## Development Guidelines

### Code Style
- Follow black formatting (line length: 88 characters)
- Use type hints for all function parameters and returns
- Implement dataclasses for structured data models
- Add docstrings for all public methods and classes

### Error Handling
- Use proper HTTP status codes for API responses
- Implement comprehensive logging for debugging
- Handle Firestore exceptions gracefully
- Validate input data using Flask-RESTX models

### Performance Considerations
- Optimize match simulation for batch processing
- Use Firestore transactions for data consistency
- Implement caching for frequently accessed game data
- Monitor Cloud Run memory and CPU usage

## Deployment

### Cloud Run Configuration
- Container runs on port 8080 with gunicorn WSGI server
- Uses non-root user for security
- Environment variables: `PORT`, `FIREBASE_ADMIN_KEY`
- Auto-scaling based on request volume

### CI/CD Pipeline
- Automated testing on pull requests
- Code quality checks (linting, type checking, formatting)
- Security scanning for dependencies
- Deployment to Cloud Run on main branch merges

## Country System

The game features 12 fictional countries with unique player modifiers:
- **Volcania**: Mountain terrain (+Block Timing, +Strength)
- **Coastalia**: Coastal region (+Agility, +Serve Accuracy)  
- **Forestland**: Balanced temperate climate
- **Desertia**: Hot climate (+Stamina, +Mental Toughness)
- And 8 others with specific regional characteristics

Each country affects player generation and development patterns, creating strategic depth in team building and transfers.