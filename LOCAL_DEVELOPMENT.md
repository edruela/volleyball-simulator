# Local Development Guide

This guide provides detailed instructions for setting up and running the Volleyball Simulator locally for development.

## Prerequisites

- **Python 3.12+** (recommended to use pyenv for version management)
- **Git** for version control
- **Google Cloud SDK** (optional, for Firestore integration)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/edruela/volleyball-simulator.git
cd volleyball-simulator

# Install dependencies
pip install -r requirements.txt

# Run tests to verify setup
pytest

# Run with coverage
pytest --cov=. --cov-report=html --cov-report=term-missing
```

## Detailed Setup

### 1. Environment Setup

#### Using pyenv (Recommended)
```bash
# Install Python 3.12
pyenv install 3.12.8
pyenv local 3.12.8

# Verify Python version
python --version  # Should show Python 3.12.x
```

#### Using system Python
```bash
# Ensure you have Python 3.12+
python3 --version
```

### 2. Virtual Environment (Recommended)

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt
```

## Running Tests

### Basic Test Execution
```bash
# Run all tests
pytest

# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/test_models.py

# Run specific test class
pytest tests/test_models.py::TestClub

# Run specific test method
pytest tests/test_models.py::TestClub::test_club_creation
```

### Coverage Reports

```bash
# Generate coverage report (HTML + terminal)
pytest --cov=. --cov-report=html --cov-report=term-missing --cov-report=xml

# View HTML coverage report locally
python -m http.server 8000 --directory htmlcov
# Then open http://localhost:8000 in your browser

# View coverage in terminal only
pytest --cov=. --cov-report=term-missing
```

## Code Quality Checks

### Linting with flake8
```bash
# Check for syntax errors and undefined names
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics

# Full linting check (warnings as info)
flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
```

### Code Formatting with black
```bash
# Check formatting
black --check --diff .

# Auto-format code
black .
```

### Type Checking with mypy
```bash
# Run type checking
mypy . --ignore-missing-imports
```

### Run All Quality Checks
```bash
# Run the same checks as CI
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics && \
black --check --diff . && \
mypy . --ignore-missing-imports && \
pytest --cov=. --cov-report=term-missing
```

## Running the Application

### Local Match Simulation
```python
# Example: Run a match simulation locally
from game_engine.match_simulation import VolleyballSimulator
from models.club import Club
from models.player import generate_random_player

# Create simulator
simulator = VolleyballSimulator()

# Create test clubs
home_club = Club(
    id="home_club",
    name="Home Team",
    short_name="HOME",
    country_id="test_country",
    division_tier=10
)

away_club = Club(
    id="away_club", 
    name="Away Team",
    short_name="AWAY",
    country_id="test_country",
    division_tier=10
)

# Generate players for each club
home_players = [
    generate_random_player("home_club", "test_country", pos, 10)
    for pos in ["OH", "OH", "MB", "MB", "OPP", "S", "L"]
]

away_players = [
    generate_random_player("away_club", "test_country", pos, 10) 
    for pos in ["OH", "OH", "MB", "MB", "OPP", "S", "L"]
]

# Simulate match
result = simulator.simulate_match(
    home_club=home_club,
    away_club=away_club,
    home_players=home_players,
    away_players=away_players
)

print(f"Final Score: {result['home_sets']} - {result['away_sets']}")
print(f"Winner: {result['winner']}")
```

### Testing Cloud Functions Locally

```bash
# Install Functions Framework
pip install functions-framework

# Run simulate_match function locally
functions-framework --target=simulate_match --source=main.py --port=8080

# Test with curl
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{
    "home_club_id": "test_home",
    "away_club_id": "test_away"
  }'
```

## Database Setup (Optional)

### Using Firestore Emulator
```bash
# Install Google Cloud SDK
# Follow: https://cloud.google.com/sdk/docs/install

# Install Firestore emulator
gcloud components install cloud-firestore-emulator

# Start emulator
gcloud beta emulators firestore start --host-port=localhost:8080

# Set environment variable
export FIRESTORE_EMULATOR_HOST=localhost:8080
```

### Using Mock Data
The test suite includes comprehensive mocks for Firestore operations, so you can develop and test without a real database connection.

## Project Structure

```
volleyball-simulator/
├── .github/workflows/     # CI/CD pipeline
├── game_engine/          # Match simulation logic
├── models/               # Data models (Club, Player)
├── utils/                # Helper functions and constants
├── tests/                # Test suite
├── main.py              # Cloud Functions entry points
├── requirements.txt     # Python dependencies
└── LOCAL_DEVELOPMENT.md # This file
```

## Development Workflow

### 1. Making Changes
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...

# Run quality checks
black . && flake8 . --count --select=E9,F63,F7,F82 && mypy . --ignore-missing-imports

# Run tests
pytest --cov=. --cov-report=term-missing

# Commit changes
git add <changed-files>
git commit -m "Description of changes"
```

### 2. Testing Your Changes
```bash
# Run full test suite
pytest -v

# Test specific functionality
python -c "
from models.club import Club
club = Club('test', 'Test Club', 'TC', 'country', 10)
print(f'Club created: {club.name}')
print(f'Overall rating: {club.get_overall_rating()}')
"
```

### 3. Before Submitting
```bash
# Ensure all checks pass (same as CI)
flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics && \
black --check --diff . && \
mypy . --ignore-missing-imports && \
pytest --cov=. --cov-report=html --cov-report=term-missing
```

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure you're in the project root directory
pwd  # Should end with /volleyball-simulator

# Ensure dependencies are installed
pip install -r requirements.txt

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

#### Test Failures
```bash
# Run tests with more verbose output
pytest -v -s

# Run specific failing test
pytest tests/test_models.py::TestClub::test_club_creation -v -s

# Check for missing dependencies
pip check
```

#### Coverage Issues
```bash
# Ensure pytest-cov is installed
pip install pytest-cov

# Generate coverage with debug info
pytest --cov=. --cov-report=term-missing --cov-config=.coveragerc -v
```

#### Type Checking Issues
```bash
# Run mypy with more verbose output
mypy . --ignore-missing-imports --show-error-codes --show-error-context

# Check specific file
mypy models/club.py --ignore-missing-imports
```

### Performance Tips

- Use `pytest -x` to stop on first failure during development
- Use `pytest --lf` to run only last failed tests
- Use `pytest -k "test_name"` to run tests matching a pattern
- Generate coverage only when needed (it slows down test execution)

## IDE Setup

### VS Code
Recommended extensions:
- Python
- Pylance
- Black Formatter
- autoDocstring

### PyCharm
- Enable pytest as test runner
- Configure black as code formatter
- Enable mypy type checking

## Contributing

1. Follow the existing code style (enforced by black)
2. Add tests for new functionality
3. Ensure all quality checks pass
4. Update documentation as needed
5. Test locally before submitting PR

## Performance Benchmarks

```bash
# Benchmark match simulation
python -c "
import time
from game_engine.match_simulation import VolleyballSimulator
from models.club import Club
from models.player import generate_random_player

simulator = VolleyballSimulator()
# ... setup clubs and players ...

start = time.time()
for i in range(100):
    result = simulator.simulate_match(home_club, away_club, home_players, away_players)
end = time.time()

print(f'100 matches simulated in {end-start:.2f} seconds')
print(f'Average: {(end-start)/100*1000:.1f}ms per match')
"
```

## Additional Resources

- [Volleyball Rules](https://www.fivb.org/en/volleyball/thegame_volleyball_glossary/officialrulesofthegames) - For understanding game mechanics
- [Google Cloud Functions](https://cloud.google.com/functions/docs) - For deployment
- [Firestore Documentation](https://cloud.google.com/firestore/docs) - For database operations
- [pytest Documentation](https://docs.pytest.org/) - For testing
