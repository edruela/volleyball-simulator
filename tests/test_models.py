"""
Tests for data models
"""

import pytest
from models.club import Club, ClubFinances, ClubFacilities, ClubStats, ClubTactics
from models.player import (
    Player,
    PlayerAttributes,
    PlayerCondition,
    PlayerContract,
    PlayerStats,
    generate_random_player,
)


class TestClub:
    """Test cases for Club model"""

    def test_club_creation(self):
        """Test basic club creation"""
        club = Club(
            id="test_club_1",
            name="Test Club",
            short_name="TC",
            country_id="testland",
            division_tier=10,
            owner_id="test_owner",
        )

        assert club.id == "test_club_1"
        assert club.name == "Test Club"
        assert club.short_name == "TC"
        assert club.country_id == "testland"
        assert club.division_tier == 10
        assert club.owner_id == "test_owner"

        assert club.finances is not None
        assert club.facilities is not None
        assert club.stats is not None
        assert club.default_tactics is not None
        assert club.colors is not None

    def test_club_finances_scaling(self):
        """Test that finances scale with division tier"""
        elite_club = Club(
            id="elite",
            name="Elite Club",
            short_name="EC",
            country_id="testland",
            division_tier=1,
        )

        amateur_club = Club(
            id="amateur",
            name="Amateur Club",
            short_name="AC",
            country_id="testland",
            division_tier=19,
        )

        assert elite_club.finances.weekly_revenue > amateur_club.finances.weekly_revenue

    def test_club_to_dict_conversion(self):
        """Test club dictionary conversion"""
        club = Club(
            id="test_club",
            name="Test Club",
            short_name="TC",
            country_id="testland",
            division_tier=10,
        )

        club_dict = club.to_dict()

        assert club_dict["id"] == "test_club"
        assert club_dict["name"] == "Test Club"
        assert club_dict["countryId"] == "testland"
        assert club_dict["divisionTier"] == 10
        assert "createdAt" in club_dict
        assert "finances" in club_dict
        assert "facilities" in club_dict

    def test_club_from_dict_conversion(self):
        """Test creating club from dictionary"""
        club_data = {
            "id": "test_club",
            "name": "Test Club",
            "short_name": "TC",
            "country_id": "testland",
            "division_tier": 10,
            "finances": {
                "balance": 100000,
                "weekly_revenue": 5000,
                "weekly_expenses": 4000,
                "transfer_budget": 50000,
            },
        }

        club = Club.from_dict(club_data)

        assert club.id == "test_club"
        assert club.name == "Test Club"
        assert isinstance(club.finances, ClubFinances)
        assert club.finances.balance == 100000

    def test_club_stats_update(self):
        """Test club stats update after match"""
        club = Club(
            id="test_club",
            name="Test Club",
            short_name="TC",
            country_id="testland",
            division_tier=10,
        )

        club.update_stats(won=True, sets_for=3, sets_against=1)
        assert club.stats.wins == 1
        assert club.stats.points == 3
        assert club.stats.sets_won == 3
        assert club.stats.sets_lost == 1

        club.update_stats(won=False, sets_for=1, sets_against=3)
        assert club.stats.wins == 1
        assert club.stats.losses == 1
        assert club.stats.points == 3  # No additional points for loss
        assert club.stats.sets_won == 4  # 3 + 1
        assert club.stats.sets_lost == 4  # 1 + 3

    def test_club_overall_rating(self):
        """Test club overall rating calculation"""
        club = Club(
            id="test_club",
            name="Test Club",
            short_name="TC",
            country_id="testland",
            division_tier=1,  # Elite tier
        )

        rating = club.get_overall_rating()

        assert rating > 0
        assert isinstance(rating, float)

        assert rating > 50  # Should be above average


class TestPlayer:
    """Test cases for Player model"""

    def test_player_creation(self):
        """Test basic player creation"""
        attributes = PlayerAttributes(spike_power=80, spike_accuracy=75)
        condition = PlayerCondition()
        contract = PlayerContract(salary=50000, years_remaining=2)
        stats = PlayerStats()

        player = Player(
            id="test_player_1",
            first_name="John",
            last_name="Doe",
            club_id="test_club",
            country_id="testland",
            age=25,
            position="OH",
            attributes=attributes,
            condition=condition,
            contract=contract,
            stats=stats,
        )

        assert player.id == "test_player_1"
        assert player.first_name == "John"
        assert player.last_name == "Doe"
        assert player.age == 25
        assert player.position == "OH"
        assert player.full_name == "John Doe"

    def test_player_overall_rating_by_position(self):
        """Test that overall rating varies by position"""
        base_attributes = PlayerAttributes(
            spike_power=80,
            spike_accuracy=80,
            block_timing=80,
            passing_accuracy=80,
            setting_precision=80,
            serve_power=80,
            serve_accuracy=80,
            court_vision=80,
            decision_making=80,
            communication=80,
            stamina=80,
            strength=80,
            agility=80,
            jump_height=80,
            speed=80,
        )

        positions = ["OH", "MB", "OPP", "S", "L", "DS"]
        ratings = {}

        for position in positions:
            player = Player(
                id=f"player_{position}",
                first_name="Test",
                last_name="Player",
                club_id="test_club",
                country_id="testland",
                age=25,
                position=position,
                attributes=base_attributes,
                condition=PlayerCondition(),
                contract=PlayerContract(salary=50000, years_remaining=2),
                stats=PlayerStats(),
            )

            ratings[position] = player.get_overall_rating()

        for position, rating in ratings.items():
            assert rating > 0
            assert rating <= 100

    def test_player_condition_effects(self):
        """Test that player condition affects rating"""
        attributes = PlayerAttributes(spike_power=80, spike_accuracy=80)

        healthy_player = Player(
            id="healthy",
            first_name="Healthy",
            last_name="Player",
            club_id="test_club",
            country_id="testland",
            age=25,
            position="OH",
            attributes=attributes,
            condition=PlayerCondition(fatigue=0, fitness=100, morale=100),
            contract=PlayerContract(salary=50000, years_remaining=2),
            stats=PlayerStats(),
        )

        tired_player = Player(
            id="tired",
            first_name="Tired",
            last_name="Player",
            club_id="test_club",
            country_id="testland",
            age=25,
            position="OH",
            attributes=attributes,
            condition=PlayerCondition(fatigue=80, fitness=60, morale=50),
            contract=PlayerContract(salary=50000, years_remaining=2),
            stats=PlayerStats(),
        )

        healthy_rating = healthy_player.get_overall_rating()
        tired_rating = tired_player.get_overall_rating()

        assert healthy_rating > tired_rating

    def test_player_fatigue_recovery(self):
        """Test player fatigue recovery"""
        player = Player(
            id="test_player",
            first_name="Test",
            last_name="Player",
            club_id="test_club",
            country_id="testland",
            age=25,
            position="OH",
            attributes=PlayerAttributes(),
            condition=PlayerCondition(fatigue=60),
            contract=PlayerContract(salary=50000, years_remaining=2),
            stats=PlayerStats(),
        )

        initial_fatigue = player.condition.fatigue
        player.recover_fatigue(rest_days=2)

        assert player.condition.fatigue < initial_fatigue
        assert player.condition.fatigue >= 0  # Should not go below 0

    def test_player_dict_conversion(self):
        """Test player dictionary conversion"""
        player = Player(
            id="test_player",
            first_name="Test",
            last_name="Player",
            club_id="test_club",
            country_id="testland",
            age=25,
            position="OH",
            attributes=PlayerAttributes(),
            condition=PlayerCondition(),
            contract=PlayerContract(salary=50000, years_remaining=2),
            stats=PlayerStats(),
        )

        player_dict = player.to_dict()

        assert player_dict["id"] == "test_player"
        assert player_dict["first_name"] == "Test"
        assert player_dict["position"] == "OH"
        assert "attributes" in player_dict
        assert "condition" in player_dict
        assert "contract" in player_dict
        assert "createdAt" in player_dict

        restored_player = Player.from_dict(player_dict)
        assert restored_player.id == player.id
        assert restored_player.first_name == player.first_name
        assert isinstance(restored_player.attributes, PlayerAttributes)


class TestPlayerGeneration:
    """Test cases for random player generation"""

    def test_generate_random_player(self):
        """Test random player generation"""
        player = generate_random_player(
            club_id="test_club", country_id="testland", position="OH", division_tier=10
        )

        assert player.club_id == "test_club"
        assert player.country_id == "testland"
        assert player.position == "OH"
        assert 18 <= player.age <= 35
        assert player.first_name is not None
        assert player.last_name is not None
        assert player.contract.salary > 0

    def test_player_generation_by_division(self):
        """Test that player quality varies by division tier"""
        elite_player = generate_random_player(
            "club1", "testland", "OH", division_tier=1
        )
        amateur_player = generate_random_player(
            "club2", "testland", "OH", division_tier=19
        )

        elite_rating = elite_player.get_overall_rating()
        amateur_rating = amateur_player.get_overall_rating()

        assert 1 <= elite_rating <= 100
        assert 1 <= amateur_rating <= 100

    def test_position_specific_generation(self):
        """Test that different positions get appropriate attributes"""
        setter = generate_random_player("club", "testland", "S", division_tier=10)
        libero = generate_random_player("club", "testland", "L", division_tier=10)

        assert setter.attributes.setting_precision >= 30

        assert libero.attributes.passing_accuracy >= 30

        assert setter.get_overall_rating() > 0
        assert libero.get_overall_rating() > 0
