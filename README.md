# Volleyball Manager - Complete Implementation Specification

## Table of Contents

1. [Project Overview](#project-overview)
1. [Game Design Specification](#game-design-specification)
1. [Technical Architecture](#technical-architecture)
1. [Database Schema](#database-schema)
1. [Backend Implementation (Python)](#backend-implementation-python)
1. [Frontend Implementation (React.js)](#frontend-implementation-reactjs)
1. [Monetization Strategy](#monetization-strategy)
1. [Deployment Guide](#deployment-guide)
1. [Testing Strategy](#testing-strategy)
1. [Implementation Roadmap](#implementation-roadmap)

## Project Overview

### Vision Statement

Create a comprehensive volleyball team management simulation game where players build clubs from amateur divisions to elite professional leagues across multiple continents, focusing on strategy, player development, and financial management.

### Core Principles

- **Fair Play**: No pay-to-win mechanics - all players compete on equal terms
- **Depth**: 19-tier league system with 3,648+ clubs per continent
- **Accessibility**: Mobile-first responsive web application
- **Scalability**: Cloud-native architecture supporting global expansion
- **Sustainability**: Ethical monetization through convenience and cosmetic features

### Target Audience

- Sports management game enthusiasts
- Volleyball fans and players
- Strategy game players
- Mobile and web gamers aged 16-45

## Game Design Specification

### World Structure

#### Continental System (Expandable)

```yaml
Phase 1 Launch - Euralia Continent:
  Countries: 12 fictional countries
  Total Clubs: 3,648 (304 per country)
  League Structure: 19-tier pyramid per country
  
Phase 2+ Expansion:
  - Ameritas Continent (+3,648 clubs)
  - Afrosia Continent (+3,648 clubs)
  - Oceanus Continent (+3,648 clubs)
  Total Potential: 14,592 clubs across 4 continents
```

#### League Pyramid Structure (Per Country)

```yaml
Tier 1: Elite League (16 clubs)
Tier 2-4: Professional Divisions 1-3 (48 clubs total)
Tier 5-9: Semi-Professional Divisions 1-5 (80 clubs total)
Tier 10-19: Amateur Divisions 1-10 (160 clubs total)

Total per country: 304 clubs
Promotion/Relegation: Top 2 automatic, 3rd-6th playoffs
```

#### Fictional Countries (Euralia)

```yaml
1. Volcania: Mountainous, +15 Block Timing, +10 Strength, -5 Agility
2. Coastalia: Coastal, +10 Agility, +10 Serve Accuracy, -5 Strength
3. Forestland: Temperate, Balanced (+5 all technical skills)
4. Desertia: Hot climate, +15 Stamina, +5 Mental Toughness, -10 Speed
5. Northlands: Cold climate, +15 Spike Power, +10 Strength, -10 Agility
6. Islandia: Tropical, +15 Speed, +10 Court Vision, -5 Strength
7. Plainscountry: Agricultural, +10 Passing Accuracy, +5 Decision Making
8. Stonehills: Rocky terrain, +10 Injury Resistance, +10 Mental Toughness
9. Riverside: River valleys, +10 Adaptability, +5 all physical attributes
10. Windlands: Windy, +15 Ball Control, +10 Serve Accuracy
11. Sunlands: Sunny, +10 Stamina, +10 Jump Height, -5 night performance
12. Mistcountry: Foggy, +15 Court Vision, +10 Communication, -5 reaction time
```

### Player System

#### Positions and Roles

```yaml
OH (Outside Hitter): Primary attackers, balanced skills
MB (Middle Blocker): Net defense and quick attacks, blocking specialists
OPP (Opposite Hitter): Secondary attackers, power focus
S (Setter): Playmaker, ball distribution specialist
L (Libero): Defensive specialist, cannot attack or serve
DS (Defensive Specialist): Back-row defense, flexible role
```

#### Player Attributes (0-100 scale)

```yaml
Technical Attributes:
  - Spike Power: Attacking strength
  - Spike Accuracy: Attack precision
  - Block Timing: Defensive blocking ability
  - Passing Accuracy: Receive and dig quality
  - Setting Precision: Ball distribution (setters)
  - Serve Power: Service strength
  - Serve Accuracy: Service precision
  - Court Vision: Reading the game
  - Decision Making: Tactical choices
  - Communication: Team coordination

Physical Attributes:
  - Stamina: Affects all skills when low (0-100)
  - Strength: Affects spike power and blocking (0-100)
  - Agility: Movement and reaction time (0-100)
  - Jump Height: Attacking and blocking reach (0-100)
  - Speed: Court coverage ability (0-100)

Condition Modifiers:
  - Fitness Level: 0-100%, affects all physical attributes
  - Fatigue: 0-100, accumulates with games
  - Injury Status: Reduces specific attributes
```

#### Performance Interaction System

```python
# Technical skills affected by physical condition
def apply_physical_impact(technical_skill, physical_attributes, fatigue):
    fitness_factor = physical_attributes['fitness'] / 100
    fatigue_factor = (100 - fatigue) / 100
    
    # Physical attributes below 70% start affecting technical skills
    physical_penalty = max(0, (70 - physical_attributes['stamina']) * 0.02)
    
    return technical_skill * fitness_factor * fatigue_factor * (1 - physical_penalty)
```

### Strategy System

#### Formation Options

```yaml
6-2 Formation: 
  - 2 setters, balanced attack
  - Bonuses: +10% attack variety, -5% defense consistency
  
5-1 Formation:
  - 1 setter, specialized roles  
  - Bonuses: Balanced, no penalties
  
4-2 Formation:
  - Amateur level, simple setup
  - Bonuses: +5% serve consistency, -10% attack power
```

#### Tactical Intensity Levels

```yaml
Conservative (Low Intensity):
  - Effect: +5 stamina preservation per game, -10% performance
  - Usage: Rest key players, injury prevention
  
Balanced (Medium Intensity):
  - Effect: Standard performance and fatigue
  - Usage: Default tactical approach
  
Aggressive (High Intensity):
  - Effect: +15% performance, -10 stamina per game
  - Usage: Important matches, short-term boost
```

### Financial System

#### Revenue Streams by Division

```yaml
Elite League (Tier 1):
  Base Revenue: $25M-$50M annually
  Ticket Sales: $2M per home game (15 games)
  Marketing Contracts: $15M-$35M
  Continental Competition Bonus: $10M+ potential

Professional Divisions (Tiers 2-4):
  Base Revenue: $2M-$15M annually
  Scaling factor: 0.6x per tier down

Semi-Professional Divisions (Tiers 5-9):
  Base Revenue: $200K-$1.5M annually
  Part-time to full-time transition point

Amateur Divisions (Tiers 10-19):
  Base Revenue: $5K-$200K annually
  Grassroots to serious amateur levels
```

#### Starting Conditions

```yaml
All Players Start With:
  - Money: $500,000
  - Starting Division: Amateur Division 7-10 (random)
  - Initial Squad: 12 amateur-level players
  - Stadium Capacity: 500-2,000 seats
  - Basic facilities
```

### Competition Structure

#### Domestic Competitions

```yaml
Regular Season:
  - 15 games per season (single round-robin)
  - 30-week season with rest periods
  - Promotion/relegation playoffs: weeks 28-30

Cup Competitions:
  - National Cup: All divisions participate
  - Format: Single elimination
  - Prize money scales with division tier
```

#### Continental Competitions

```yaml
Continental Champions League:
  - Participants: All Elite League clubs (192 teams)
  - Format: Group stage → Knockout rounds
  - Prize Pool: $200M total, $50M winner
  - Timeline: Weeks 32-42

Continental Professional Cup:
  - Participants: Professional Division 1 clubs (192 teams)  
  - Prize Pool: $75M total, $20M winner

Continental Amateur Championship:
  - Participants: Semi-Pro Division 1 champions (12 teams)
  - Prize Pool: $10M total, $3M winner
```

#### World Competitions (Phase 2+)

```yaml
World Club Championship:
  - Participants: Continental Champions League winners
  - Format: Round-robin + Finals
  - Prize Pool: $100M+ (scales with continents)
  - Timeline: Weeks 44-48
```

## Technical Architecture

### GCP Cloud Architecture

#### Overview

```
Frontend (React.js) → Firebase Hosting → Cloud Run (Flask App) → Firestore Database
                   ↓
            Cloud Storage (Assets) + Cloud Scheduler (Cron Jobs)
```

#### Cost-Optimized MVP Stack

```yaml
Frontend:
  - Firebase Hosting: FREE (10GB storage, custom domain, SSL)
  - React.js 18+ with Tailwind CSS
  - Progressive Web App capabilities

Backend:
  - Cloud Run (Flask App): FREE (2M requests/month, 180,000 vCPU-seconds)
  - Containerized serverless architecture, auto-scaling
  - Request timeout: 300 seconds, 512MB memory, 1 vCPU

Database:
  - Firestore: FREE (50K reads, 20K writes daily)
  - NoSQL document database
  - Real-time synchronization

Storage:
  - Cloud Storage: FREE (5GB for game assets)
  - CDN distribution included

Estimated Cost: $0-$15/month for MVP (slightly higher than Cloud Functions due to container overhead)
```

## Database Schema

### Firestore Collections

#### Users Collection

```javascript
users/{userId} {
  email: string,
  displayName: string,
  clubId: string,
  preferences: {
    theme: 'light' | 'dark',
    notifications: boolean,
    autoSave: boolean,
    language: string
  },
  subscription: {
    tier: 'free' | 'supporter' | 'analytics' | 'creator',
    expiresAt: timestamp,
    features: string[]
  },
  gameStats: {
    totalPlayTime: number,
    clubsManaged: number,
    matchesSimulated: number,
    achievementsUnlocked: string[]
  },
  createdAt: timestamp,
  lastLogin: timestamp
}
```

#### Clubs Collection

```javascript
clubs/{clubId} {
  name: string,
  shortName: string, // 3-4 letter abbreviation
  countryId: string,
  divisionTier: number, // 1-19
  ownerId: string, // userId for player-controlled clubs
  isPlayerClub: boolean,
  
  // Basic Info
  foundedYear: number,
  colors: {
    primary: string,
    secondary: string,
    accent: string
  },
  badge: {
    type: string,
    customUrl?: string // For premium users
  },
  
  // Finances
  finances: {
    balance: number,
    weeklyRevenue: number,
    weeklyExpenses: number,
    transferBudget: number,
    debtLevel: number
  },
  
  // Performance Stats
  stats: {
    currentSeason: {
      wins: number,
      losses: number,
      setsWon: number,
      setsLost: number,
      position: number,
      points: number
    },
    historical: {
      totalSeasons: number,
      promotions: number,
      relegations: number,
      trophiesWon: string[]
    }
  },
  
  // Facilities
  facilities: {
    stadiumCapacity: number,
    stadiumName: string,
    trainingLevel: number, // 1-10
    youthAcademy: number, // 0-10
    medicalFacilities: number // 1-10
  },
  
  // Tactics
  defaultTactics: {
    formation: string, // '6-2', '5-1', '4-2'
    intensity: number, // 0.8-1.2
    style: string, // 'balanced', 'aggressive', 'defensive'
  },
  
  // AI Behavior (for computer-controlled clubs)
  aiPersonality: {
    spending: number, // 1-10 (conservative to aggressive)
    tactics: number, // 1-10 (defensive to attacking)
    transfers: number, // 1-10 (local to international focus)
    development: number // 1-10 (short-term to long-term)
  }
}
```

#### Players Collection

```javascript
players/{playerId} {
  // Basic Info
  name: {
    first: string,
    last: string,
    nickname?: string
  },
  clubId: string,
  countryId: string,
  age: number,
  position: 'OH' | 'MB' | 'OPP' | 'S' | 'L' | 'DS',
  
  // Contract
  contract: {
    salary: number,
    yearsRemaining: number,
    bonusClause: number,
    transferClause: number
  },
  
  // Attributes
  attributes: {
    // Technical (0-100)
    spikePower: number,
    spikeAccuracy: number,
    blockTiming: number,
    passingAccuracy: number,
    settingPrecision: number,
    servePower: number,
    serveAccuracy: number,
    courtVision: number,
    decisionMaking: number,
    communication: number,
    
    // Physical (0-100)  
    stamina: number,
    strength: number,
    agility: number,
    jumpHeight: number,
    speed: number
  },
  
  // Development
  potential: {
    maxAge: number, // Age at which decline starts
    peakAge: number, // Age of peak performance
    growthRate: number, // How fast they develop
    ceiling: { // Maximum possible attributes
      spikePower: number,
      // ... other attributes
    }
  },
  
  // Current Condition
  condition: {
    fatigue: number, // 0-100
    fitness: number, // 0-100
    morale: number, // 0-100
    injury: null | {
      type: string,
      severity: number,
      daysRemaining: number,
      affectedAttributes: string[]
    }
  },
  
  // Career Stats
  careerStats: {
    matchesPlayed: number,
    setsPlayed: number,
    points: number,
    kills: number,
    blocks: number,
    aces: number,
    digs: number,
    assists: number
  },
  
  // Personality
  personality: {
    leadership: number, // 1-10
    workEthic: number, // 1-10
    temperament: number, // 1-10 (calm to volatile)
    ambition: number, // 1-10
    loyalty: number // 1-10
  }
}
```

#### Matches Collection

```javascript
matches/{matchId} {
  // Basic Info
  homeClubId: string,
  awayClubId: string,
  competition: string, // 'domestic_league', 'continental_champions', etc.
  season: string,
  matchDay: number,
  date: timestamp,
  
  // Tactics Used
  tactics: {
    home: {
      formation: string,
      intensity: number,
      style: string
    },
    away: {
      formation: string,
      intensity: number,
      style: string
    }
  },
  
  // Result
  result: {
    homeSets: number,
    awaySets: number,
    sets: [
      { homePoints: number, awayPoints: number },
      // ... up to 5 sets
    ],
    winner: 'home' | 'away',
    duration: number // minutes
  },
  
  // Match Events (for detailed analysis)
  events: [
    {
      type: string, // 'serve_ace', 'attack_kill', 'block_point', etc.
      playerId: string,
      team: 'home' | 'away',
      set: number,
      timestamp: number,
      effectiveness: number
    }
  ],
  
  // Statistics
  stats: {
    home: {
      kills: number,
      blocks: number,
      aces: number,
      errors: number,
      possession: number // percentage
    },
    away: {
      kills: number,
      blocks: number,
      aces: number,
      errors: number,
      possession: number
    }
  },
  
  // Financial Impact
  attendance: number,
  revenue: {
    tickets: number,
    concessions: number,
    merchandise: number,
    total: number
  }
}
```

#### Competitions Collection

```javascript
competitions/{competitionId} {
  name: string,
  type: 'domestic_league' | 'domestic_cup' | 'continental_champions' | 'continental_cup' | 'world_championship',
  continent: string,
  season: string,
  
  // Structure
  format: {
    type: 'league' | 'knockout' | 'group_then_knockout',
    teamsCount: number,
    groupSize?: number,
    playoffsTeams?: number
  },
  
  // Participating Clubs
  participants: [
    {
      clubId: string,
      seeded: boolean,
      groupId?: string
    }
  ],
  
  // Prize Structure
  prizes: {
    winner: number,
    runnerUp: number,
    thirdPlace: number,
    participation: number,
    performanceBonus: {
      perWin: number,
      perGoal: number
    }
  },
  
  // Current Status
  status: 'upcoming' | 'active' | 'completed',
  currentRound: string,
  
  // Final Results
  results: {
    winner: string,
    runnerUp: string,
    standings: [
      {
        clubId: string,
        position: number,
        points: number,
        wins: number,
        losses: number,
        setsFor: number,
        setsAgainst: number
      }
    ]
  }
}
```

#### Game Configuration

```javascript
gameConfig/settings {
  // World Data
  continents: [
    {
      id: string,
      name: string,
      unlocked: boolean,
      countries: [
        {
          id: string,
          name: string,
          playerModifiers: {
            spikePower: number,
            blockTiming: number,
            // ... other attribute modifiers
          }
        }
      ]
    }
  ],
  
  // Economic Settings
  economy: {
    inflationRate: number,
    transferMarketActivity: number,
    salaryCapMultipliers: {
      1: number, // Elite League multiplier
      2: number, // Professional 1 multiplier
      // ... for each tier
    }
  },
  
  // Game Balance
  simulation: {
    homeAdvantage: number, // 1.05 = 5% advantage
    fatigueImpact: number,
    injuryProbability: number,
    developmentRates: {
      young: number, // <20 years
      prime: number, // 20-30 years  
      veteran: number // >30 years
    }
  },
  
  // Pregenerated Data
  playerNames: {
    male: {
      first: string[],
      last: string[]
    },
    female: {
      first: string[],
      last: string[]
    }
  }
}
```

## Backend Implementation (Python)

### Project Structure

```
volleyball_manager/
├── main.py                    # Cloud Functions entry points
├── requirements.txt           # Python dependencies
├── game_engine/
│   ├── __init__.py
│   ├── match_simulation.py    # Core match simulation
│   ├── player_development.py  # Player growth algorithms
│   ├── economy.py            # Financial calculations
│   ├── ai_decisions.py       # AI club management
│   ├── league_management.py  # Season progression
│   └── competitions.py       # Tournament management
├── models/
│   ├── __init__.py
│   ├── club.py               # Club data model
│   ├── player.py             # Player data model
│   ├── match.py              # Match data model
│   └── competition.py        # Competition data model
├── utils/
│   ├── __init__.py
│   ├── firestore_helpers.py  # Database utilities
│   ├── validators.py         # Input validation
│   ├── constants.py          # Game constants
│   └── random_generators.py  # Random data generation
└── tests/
    ├── test_match_simulation.py
    ├── test_player_development.py
    └── test_economy.py
```

### Core Game Engine (Python)

#### Match Simulation Engine

```python
# game_engine/match_simulation.py
import random
import numpy as np
from typing import Dict, List, Tuple
from dataclasses import dataclass
from enum import Enum

class MatchEvent(Enum):
    SERVE_ACE = "serve_ace"
    SERVE_ERROR = "serve_error"
    ATTACK_KILL = "attack_kill"
    ATTACK_ERROR = "attack_error"
    BLOCK_POINT = "block_point"
    DIG_SAVE = "dig_save"

@dataclass
class RallyResult:
    winner: str
    events: List[Dict]
    duration: float

class VolleyballSimulator:
    """Advanced volleyball match simulation engine"""
    
    def __init__(self):
        self.HOME_ADVANTAGE = 1.05
        self.FATIGUE_IMPACT = 0.02
        self.MOMENTUM_FACTOR = 0.0
    
    def simulate_match(self, home_team: Dict, away_team: Dict, tactics: Dict) -> Dict:
        """Simulate complete volleyball match"""
        
        # Calculate team strengths
        home_strength = self._calculate_team_strength(home_team, tactics['home'])
        away_strength = self._calculate_team_strength(away_team, tactics['away'])
        
        # Apply home advantage
        home_strength['overall'] *= self.HOME_ADVANTAGE
        
        # Simulate sets (best of 5)
        sets_results = []
        home_sets = 0
        away_sets = 0
        total_rallies = 0
        
        for set_num in range(5):
            if home_sets == 3 or away_sets == 3:
                break
                
            is_fifth_set = set_num == 4
            set_result = self._simulate_set(home_strength, away_strength, is_fifth_set)
            
            sets_results.append({
                'homePoints': set_result.home_points,
                'awayPoints': set_result.away_points,
                'winner': set_result.winner,
                'duration': set_result.duration,
                'events': set_result.events
            })
            
            if set_result.winner == 'home':
                home_sets += 1
            else:
                away_sets += 1
                
            total_rallies += len(set_result.events)
            
            # Apply fatigue between sets
            self._apply_fatigue(home_team, away_team, set_result.duration)
        
        # Calculate match statistics
        attendance = self._calculate_attendance(home_team, away_team)
        revenue = self._calculate_revenue(home_team, attendance)
        
        return {
            'homeClubId': home_team['id'],
            'awayClubId': away_team['id'],
            'date': datetime.now().isoformat(),
            'result': {
                'homeSets': home_sets,
                'awaySets': away_sets,
                'sets': sets_results,
                'winner': 'home' if home_sets > away_sets else 'away'
            },
            'stats': self._compile_match_stats(sets_results),
            'attendance': attendance,
            'revenue': revenue,
            'totalRallies': total_rallies
        }
    
    def _simulate_set(self, home_strength: Dict, away_strength: Dict, is_fifth_set: bool):
        """Simulate individual volleyball set"""
        target_points = 15 if is_fifth_set else 25
        home_points = 0
        away_points = 0
        events = []
        
        serving_team = random.choice(['home', 'away'])
        start_time = 0.0
        
        while not self._is_set_complete(home_points, away_points, target_points):
            rally_result = self._simulate_rally(home_strength, away_strength, serving_team)
            
            events.extend(rally_result.events)
            
            if rally_result.winner == 'home':
                home_points += 1
                serving_team = 'home'
            else:
                away_points += 1
                serving_team = 'away'
            
            # Update momentum based on score
            self._update_momentum(home_points, away_points)
        
        return SetResult(
            home_points=home_points,
            away_points=away_points,
            winner='home' if home_points > away_points else 'away',
            duration=len(events) * 0.5,  # ~30 seconds per rally
            events=events
        )
    
    def _simulate_rally(self, home_strength: Dict, away_strength: Dict, serving_team: str) -> RallyResult:
        """Simulate individual rally with realistic volleyball mechanics"""
        
        events = []
        rally_active = True
        touches = 0
        
        # Determine serving and receiving teams
        if serving_team == 'home':
            serve_str = home_strength
            receive_str = away_strength
        else:
            serve_str = away_strength
            receive_str = home_strength
        
        # PHASE 1: Service
        serve_outcome = self._simulate_serve(serve_str, receive_str)
        events.append(serve_outcome['event'])
        
        if serve_outcome['rally_ends']:
            return RallyResult(
                winner=serve_outcome['winner'],
                events=events,
                duration=random.uniform(2, 5)
            )
        
        # PHASE 2: Rally continuation
        attacking_team = 'away' if serving_team == 'home' else 'home'
        
        while rally_active and touches < 20:  # Max 20 touches to prevent infinite rallies
            if attacking_team == 'home':
                attack_str = home_strength
                defense_str = away_strength
            else:
                attack_str = away_strength
                defense_str = home_strength
            
            attack_outcome = self._simulate_attack(attack_str, defense_str, attacking_team)
            events.append(attack_outcome['event'])
            
            if attack_outcome['rally_ends']:
                return RallyResult(
                    winner=attack_outcome['winner'],
                    events=events,
                    duration=random.uniform(5, 30)
                )
            
            # Switch sides
            attacking_team = 'away' if attacking_team == 'home' else 'home'
            touches += 1
        
        # Fallback: random winner if rally goes too long
        return RallyResult(
            winner=random.choice(['home', 'away']),
            events=events,
            duration=random.uniform(15, 45)
        )
    
    def _simulate_serve(self, serving_strength: Dict, receiving_strength: Dict) -> Dict:
        """Simulate service phase"""
        serve_power = serving_strength['serve']
        receive_skill = receiving_strength['receive']
        
        # Calculate probabilities
        ace_prob = max(0.01, min(0.15, (serve_power - receive_skill) / 500 + 0.05))
        error_prob = max(0.02, min(0.12, (100 - serve_power) / 800 + 0.03))
        
        outcome = random.random()
        
        if outcome < ace_prob:
            return {
                'rally_ends': True,
                'winner': 'serving',
                'event': {
                    'type': MatchEvent.SERVE_ACE.value,
                    'team': 'serving',
                    'effectiveness': min(1.0, serve_power / 100)
                }
            }
        elif outcome < ace_prob + error_prob:
            return {
                'rally_ends': True,
                'winner': 'receiving',
                'event': {
                    'type': MatchEvent.SERVE_ERROR.value,
                    'team': 'serving',
                    'effectiveness': 0.0
                }
            }
        else:
            return {
                'rally_ends': False,
                'winner': None,
                'event': {
                    'type': MatchEvent.DIG_SAVE.value,
                    'team': 'receiving',
                    'effectiveness': min(1.0, receive_skill / 100)
                }
            }
    
    def _simulate_attack(self, attacking_strength: Dict, defending_strength: Dict, team: str) -> Dict:
        """Simulate attack phase"""
        attack_power = attacking_strength['attack']
        defense_power = defending_strength['defense']
        
        # Factor in momentum
        momentum_bonus = self.MOMENTUM_FACTOR * 0.1 if team == 'home' else -self.MOMENTUM_FACTOR * 0.1
        
        # Calculate success probability
        success_prob = (attack_power + momentum_bonus) / (attack_power + defense_power + momentum_bonus)
        success_prob = max(0.1, min(0.9, success_prob))  # Clamp between 10-90%
        
        outcome = random.random()
        
        if outcome < success_prob * 0.8:  # 80% of successful attacks are kills
            return {
                'rally_ends': True,
                'winner': team,
                'event': {
                    'type': MatchEvent.ATTACK_KILL.value,
                    'team': team,
                    'effectiveness': min(1.0, attack_power / 100)
                }
            }
        elif outcome < success_prob:  # 20% continue rally
            return {
                'rally_ends': False,
                'winner': None,
                'event': {
                    'type': MatchEvent.DIG_SAVE.value,
                    'team': 'away' if team == 'home' else 'home',
                    'effectiveness': min(1.0, defense_power / 100)
                }
            }
        else:  # Attack unsuccessful
            if random.random() < 0.3:  # 30% blocked
                return {
                    'rally_ends': True,
                    'winner': 'away' if team == 'home' else 'home',
                    'event': {
                        'type': MatchEvent.BLOCK_POINT.value,
                        'team': 'away' if team == 'home' else 'home',
                        'effectiveness': min(1.0, defense_power / 100)
                    }
                }
            else:  # 70% attack error
                return {
                    'rally_ends': True,
                    'winner': 'away' if team == 'home' else 'home',
```
