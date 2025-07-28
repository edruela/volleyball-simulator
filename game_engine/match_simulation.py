"""
Advanced volleyball match simulation engine
"""
import random
import numpy as np
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


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


@dataclass
class SetResult:
    home_points: int
    away_points: int
    winner: str
    duration: float
    events: List[Dict]


class VolleyballSimulator:
    """Advanced volleyball match simulation engine"""
    
    def __init__(self):
        self.HOME_ADVANTAGE = 1.05
        self.FATIGUE_IMPACT = 0.02
        self.MOMENTUM_FACTOR = 0.0
    
    def simulate_match(self, home_team: Dict, away_team: Dict, tactics: Dict) -> Dict:
        """Simulate complete volleyball match"""
        
        home_strength = self._calculate_team_strength(home_team, tactics['home'])
        away_strength = self._calculate_team_strength(away_team, tactics['away'])
        
        home_strength['overall'] *= self.HOME_ADVANTAGE
        
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
            
            self._apply_fatigue(home_team, away_team, set_result.duration)
        
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
                'winner': 'home' if home_sets > away_sets else 'away',
                'duration': sum(s['duration'] for s in sets_results)
            },
            'stats': self._compile_match_stats(sets_results),
            'attendance': attendance,
            'revenue': revenue,
            'totalRallies': total_rallies,
            'tactics': tactics
        }
    
    def _calculate_team_strength(self, team: Dict, tactics: Dict) -> Dict:
        """Calculate overall team strength based on players and tactics"""
        players = team.get('players', [])
        if not players:
            return {
                'overall': 50.0,
                'attack': 50.0,
                'defense': 50.0,
                'serve': 50.0,
                'receive': 50.0
            }
        
        total_attack = sum(p.get('attributes', {}).get('spikePower', 50) + 
                          p.get('attributes', {}).get('spikeAccuracy', 50) for p in players) / (2 * len(players))
        total_defense = sum(p.get('attributes', {}).get('blockTiming', 50) + 
                           p.get('attributes', {}).get('passingAccuracy', 50) for p in players) / (2 * len(players))
        total_serve = sum(p.get('attributes', {}).get('servePower', 50) + 
                         p.get('attributes', {}).get('serveAccuracy', 50) for p in players) / (2 * len(players))
        total_receive = sum(p.get('attributes', {}).get('passingAccuracy', 50) for p in players) / len(players)
        
        formation_bonus = self._get_formation_bonus(tactics.get('formation', '5-1'))
        intensity = tactics.get('intensity', 1.0)
        
        return {
            'overall': (total_attack + total_defense + total_serve + total_receive) / 4 * intensity,
            'attack': total_attack * formation_bonus.get('attack', 1.0) * intensity,
            'defense': total_defense * formation_bonus.get('defense', 1.0) * intensity,
            'serve': total_serve * intensity,
            'receive': total_receive * intensity
        }
    
    def _get_formation_bonus(self, formation: str) -> Dict[str, float]:
        """Get tactical bonuses for different formations"""
        bonuses = {
            '6-2': {'attack': 1.1, 'defense': 0.95},
            '5-1': {'attack': 1.0, 'defense': 1.0},
            '4-2': {'attack': 0.9, 'defense': 1.05}
        }
        return bonuses.get(formation, {'attack': 1.0, 'defense': 1.0})
    
    def _simulate_set(self, home_strength: Dict, away_strength: Dict, is_fifth_set: bool) -> SetResult:
        """Simulate individual volleyball set"""
        target_points = 15 if is_fifth_set else 25
        home_points = 0
        away_points = 0
        events = []
        
        serving_team = random.choice(['home', 'away'])
        
        while not self._is_set_complete(home_points, away_points, target_points):
            rally_result = self._simulate_rally(home_strength, away_strength, serving_team)
            
            events.extend(rally_result.events)
            
            if rally_result.winner == 'home':
                home_points += 1
                serving_team = 'home'
            else:
                away_points += 1
                serving_team = 'away'
            
            self._update_momentum(home_points, away_points)
        
        return SetResult(
            home_points=home_points,
            away_points=away_points,
            winner='home' if home_points > away_points else 'away',
            duration=len(events) * 0.5,  # ~30 seconds per rally
            events=events
        )
    
    def _is_set_complete(self, home_points: int, away_points: int, target_points: int) -> bool:
        """Check if set is complete"""
        if home_points >= target_points and home_points - away_points >= 2:
            return True
        if away_points >= target_points and away_points - home_points >= 2:
            return True
        return False
    
    def _simulate_rally(self, home_strength: Dict, away_strength: Dict, serving_team: str) -> RallyResult:
        """Simulate individual rally with realistic volleyball mechanics"""
        
        events = []
        rally_active = True
        touches = 0
        
        if serving_team == 'home':
            serve_str = home_strength
            receive_str = away_strength
        else:
            serve_str = away_strength
            receive_str = home_strength
        
        serve_outcome = self._simulate_serve(serve_str, receive_str, serving_team)
        events.append(serve_outcome['event'])
        
        if serve_outcome['rally_ends']:
            return RallyResult(
                winner=serve_outcome['winner'],
                events=events,
                duration=random.uniform(2, 5)
            )
        
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
            
            attacking_team = 'away' if attacking_team == 'home' else 'home'
            touches += 1
        
        return RallyResult(
            winner=random.choice(['home', 'away']),
            events=events,
            duration=random.uniform(15, 45)
        )
    
    def _simulate_serve(self, serving_strength: Dict, receiving_strength: Dict, serving_team: str) -> Dict:
        """Simulate service phase"""
        serve_power = serving_strength['serve']
        receive_skill = receiving_strength['receive']
        
        ace_prob = max(0.01, min(0.15, (serve_power - receive_skill) / 500 + 0.05))
        error_prob = max(0.02, min(0.12, (100 - serve_power) / 800 + 0.03))
        
        outcome = random.random()
        
        if outcome < ace_prob:
            return {
                'rally_ends': True,
                'winner': serving_team,
                'event': {
                    'type': MatchEvent.SERVE_ACE.value,
                    'team': serving_team,
                    'effectiveness': min(1.0, serve_power / 100)
                }
            }
        elif outcome < ace_prob + error_prob:
            return {
                'rally_ends': True,
                'winner': 'away' if serving_team == 'home' else 'home',
                'event': {
                    'type': MatchEvent.SERVE_ERROR.value,
                    'team': serving_team,
                    'effectiveness': 0.0
                }
            }
        else:
            return {
                'rally_ends': False,
                'winner': None,
                'event': {
                    'type': MatchEvent.DIG_SAVE.value,
                    'team': 'away' if serving_team == 'home' else 'home',
                    'effectiveness': min(1.0, receive_skill / 100)
                }
            }
    
    def _simulate_attack(self, attacking_strength: Dict, defending_strength: Dict, team: str) -> Dict:
        """Simulate attack phase"""
        attack_power = attacking_strength['attack']
        defense_power = defending_strength['defense']
        
        momentum_bonus = self.MOMENTUM_FACTOR * 0.1 if team == 'home' else -self.MOMENTUM_FACTOR * 0.1
        
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
                    'event': {
                        'type': MatchEvent.ATTACK_ERROR.value,
                        'team': team,
                        'effectiveness': 0.0
                    }
                }
    
    def _apply_fatigue(self, home_team: Dict, away_team: Dict, set_duration: float):
        """Apply fatigue effects to players after a set"""
        fatigue_amount = set_duration * self.FATIGUE_IMPACT
        
        for team in [home_team, away_team]:
            for player in team.get('players', []):
                current_fatigue = player.get('condition', {}).get('fatigue', 0)
                player.setdefault('condition', {})['fatigue'] = min(100, current_fatigue + fatigue_amount)
    
    def _update_momentum(self, home_points: int, away_points: int):
        """Update momentum based on current score"""
        point_diff = home_points - away_points
        self.MOMENTUM_FACTOR = max(-1.0, min(1.0, point_diff * 0.1))
    
    def _calculate_attendance(self, home_team: Dict, away_team: Dict) -> int:
        """Calculate match attendance"""
        home_club = home_team.get('club', {})
        stadium_capacity = home_club.get('facilities', {}).get('stadiumCapacity', 1000)
        
        base_attendance = stadium_capacity * 0.6  # 60% base attendance
        
        attendance_factor = random.uniform(0.7, 1.3)
        
        return int(min(stadium_capacity, base_attendance * attendance_factor))
    
    def _calculate_revenue(self, home_team: Dict, attendance: int) -> Dict[str, int]:
        """Calculate match revenue"""
        home_club = home_team.get('club', {})
        division_tier = home_club.get('divisionTier', 10)
        
        base_ticket_price = max(5, 50 - (division_tier * 3))
        
        tickets = attendance * base_ticket_price
        concessions = int(tickets * 0.3)
        merchandise = int(tickets * 0.1)
        
        return {
            'tickets': tickets,
            'concessions': concessions,
            'merchandise': merchandise,
            'total': tickets + concessions + merchandise
        }
    
    def _compile_match_stats(self, sets_results: List[Dict]) -> Dict:
        """Compile overall match statistics"""
        home_stats = {'kills': 0, 'blocks': 0, 'aces': 0, 'errors': 0}
        away_stats = {'kills': 0, 'blocks': 0, 'aces': 0, 'errors': 0}
        
        for set_result in sets_results:
            for event in set_result.get('events', []):
                team = event.get('team')
                event_type = event.get('type')
                
                if team == 'home':
                    stats = home_stats
                else:
                    stats = away_stats
                
                if event_type == MatchEvent.ATTACK_KILL.value:
                    stats['kills'] += 1
                elif event_type == MatchEvent.BLOCK_POINT.value:
                    stats['blocks'] += 1
                elif event_type == MatchEvent.SERVE_ACE.value:
                    stats['aces'] += 1
                elif event_type in [MatchEvent.SERVE_ERROR.value, MatchEvent.ATTACK_ERROR.value]:
                    stats['errors'] += 1
        
        return {
            'home': home_stats,
            'away': away_stats
        }
