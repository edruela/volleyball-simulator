"""
Game constants and configuration
"""

GAME_CONFIG = {
    'MATCH_SIMULATION': {
        'HOME_ADVANTAGE': 1.05,
        'FATIGUE_IMPACT': 0.02,
        'MAX_RALLY_TOUCHES': 20,
        'SET_TARGET_POINTS': 25,
        'FIFTH_SET_POINTS': 15,
        'MIN_WIN_MARGIN': 2
    },
    
    'PLAYER_DEVELOPMENT': {
        'GROWTH_AGE_LIMIT': 25,
        'DECLINE_AGE_START': 30,
        'TRAINING_IMPACT': 0.5,
        'FATIGUE_RECOVERY_RATE': 15  # points per day
    },
    
    'FINANCIAL': {
        'STARTING_BALANCE': 500000,
        'BASE_REVENUE_ELITE': 25000000,
        'BASE_REVENUE_AMATEUR': 5000,
        'SALARY_CAP_MULTIPLIER': {
            1: 10.0,   # Elite League
            10: 1.0,   # Mid-tier
            19: 0.1    # Lowest amateur
        }
    },
    
    'LEAGUE_STRUCTURE': {
        'TIERS_PER_COUNTRY': 19,
        'CLUBS_PER_TIER': {
            1: 16,      # Elite League
            2: 16,      # Professional 1
            3: 16,      # Professional 2
            4: 16,      # Professional 3
            5: 16,      # Semi-Pro 1
            19: 16      # Amateur 10
        },
        'PROMOTION_SPOTS': 2,
        'PLAYOFF_SPOTS': 4
    }
}

COUNTRIES = {
    'volcania': {
        'name': 'Volcania',
        'modifiers': {
            'blockTiming': 15,
            'strength': 10,
            'agility': -5
        }
    },
    'coastalia': {
        'name': 'Coastalia', 
        'modifiers': {
            'agility': 10,
            'serveAccuracy': 10,
            'strength': -5
        }
    },
    'forestland': {
        'name': 'Forestland',
        'modifiers': {
            'spikePower': 5,
            'blockTiming': 5,
            'passingAccuracy': 5,
            'settingPrecision': 5,
            'courtVision': 5
        }
    }
}

POSITIONS = {
    'OH': {
        'name': 'Outside Hitter',
        'description': 'Primary attackers, balanced skills',
        'key_attributes': ['spikePower', 'spikeAccuracy', 'passingAccuracy']
    },
    'MB': {
        'name': 'Middle Blocker', 
        'description': 'Net defense and quick attacks',
        'key_attributes': ['blockTiming', 'spikePower', 'jumpHeight']
    },
    'OPP': {
        'name': 'Opposite Hitter',
        'description': 'Secondary attackers, power focus', 
        'key_attributes': ['spikePower', 'spikeAccuracy', 'blockTiming']
    },
    'S': {
        'name': 'Setter',
        'description': 'Playmaker, ball distribution specialist',
        'key_attributes': ['settingPrecision', 'courtVision', 'decisionMaking']
    },
    'L': {
        'name': 'Libero',
        'description': 'Defensive specialist, cannot attack or serve',
        'key_attributes': ['passingAccuracy', 'agility', 'speed']
    },
    'DS': {
        'name': 'Defensive Specialist',
        'description': 'Back-row defense, flexible role',
        'key_attributes': ['passingAccuracy', 'agility', 'courtVision']
    }
}

FORMATIONS = {
    '6-2': {
        'name': '6-2 Formation',
        'description': '2 setters, balanced attack',
        'bonuses': {'attack': 1.1, 'defense': 0.95}
    },
    '5-1': {
        'name': '5-1 Formation', 
        'description': '1 setter, specialized roles',
        'bonuses': {'attack': 1.0, 'defense': 1.0}
    },
    '4-2': {
        'name': '4-2 Formation',
        'description': 'Amateur level, simple setup',
        'bonuses': {'attack': 0.9, 'defense': 1.05}
    }
}

MATCH_EVENTS = {
    'SERVE_ACE': 'serve_ace',
    'SERVE_ERROR': 'serve_error', 
    'ATTACK_KILL': 'attack_kill',
    'ATTACK_ERROR': 'attack_error',
    'BLOCK_POINT': 'block_point',
    'DIG_SAVE': 'dig_save'
}
