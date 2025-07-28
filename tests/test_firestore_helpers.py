"""
Tests for Firestore helper functions
"""
import pytest
from unittest.mock import Mock, MagicMock
from utils.firestore_helpers import FirestoreHelper


class TestFirestoreHelper:
    """Test cases for Firestore helper functions"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_db = Mock()
        self.firestore_helper = FirestoreHelper(self.mock_db)
    
    def test_create_club(self):
        """Test club creation"""
        mock_doc_ref = Mock()
        self.mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        club_data = {
            'name': 'Test Club',
            'countryId': 'testland',
            'ownerId': 'test_owner'
        }
        
        club_id = self.firestore_helper.create_club(club_data)
        
        assert club_id is not None
        assert isinstance(club_id, str)
        
        self.mock_db.collection.assert_called_with('clubs')
        mock_doc_ref.set.assert_called_once()
    
    def test_get_club_existing(self):
        """Test getting existing club"""
        mock_doc = Mock()
        mock_doc.exists = True
        mock_doc.to_dict.return_value = {
            'id': 'test_club',
            'name': 'Test Club',
            'countryId': 'testland'
        }
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        self.mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        result = self.firestore_helper.get_club('test_club')
        
        assert result is not None
        assert result['name'] == 'Test Club'
        
        self.mock_db.collection.assert_called_with('clubs')
        self.mock_db.collection.return_value.document.assert_called_with('test_club')
    
    def test_get_club_nonexistent(self):
        """Test getting non-existent club"""
        mock_doc = Mock()
        mock_doc.exists = False
        
        mock_doc_ref = Mock()
        mock_doc_ref.get.return_value = mock_doc
        self.mock_db.collection.return_value.document.return_value = mock_doc_ref
        
        result = self.firestore_helper.get_club('nonexistent_club')
        
        assert result is None
    
    def test_get_club_players(self):
        """Test getting club players"""
        mock_player_docs = []
        for i in range(3):
            mock_doc = Mock()
            mock_doc.id = f'player_{i}'
            mock_doc.to_dict.return_value = {
                'name': f'Player {i}',
                'position': 'OH',
                'clubId': 'test_club'
            }
            mock_player_docs.append(mock_doc)
        
        mock_query = Mock()
        mock_query.stream.return_value = mock_player_docs
        self.mock_db.collection.return_value.where.return_value = mock_query
        
        players = self.firestore_helper.get_club_players('test_club')
        
        assert len(players) == 3
        assert all('id' in player for player in players)
        assert all(player['clubId'] == 'test_club' for player in players)
        
        self.mock_db.collection.assert_called_with('players')
        self.mock_db.collection.return_value.where.assert_called_with('clubId', '==', 'test_club')
    
    def test_save_match(self):
        """Test saving match result"""
        mock_match_doc_ref = Mock()
        mock_home_club_doc_ref = Mock()
        mock_away_club_doc_ref = Mock()
        
        mock_home_doc = Mock()
        mock_home_doc.exists = True
        mock_home_doc.to_dict.return_value = {'stats': {'wins': 0, 'losses': 0}}
        mock_home_club_doc_ref.get.return_value = mock_home_doc
        
        mock_away_doc = Mock()
        mock_away_doc.exists = True
        mock_away_doc.to_dict.return_value = {'stats': {'wins': 0, 'losses': 0}}
        mock_away_club_doc_ref.get.return_value = mock_away_doc
        
        def mock_collection_document(collection_name):
            if collection_name == 'matches':
                return Mock(document=Mock(return_value=mock_match_doc_ref))
            elif collection_name == 'clubs':
                mock_clubs_collection = Mock()
                def mock_document(doc_id):
                    if doc_id == 'home_club':
                        return mock_home_club_doc_ref
                    elif doc_id == 'away_club':
                        return mock_away_club_doc_ref
                mock_clubs_collection.document = mock_document
                return mock_clubs_collection
        
        self.mock_db.collection.side_effect = mock_collection_document
        
        match_data = {
            'homeClubId': 'home_club',
            'awayClubId': 'away_club',
            'result': {
                'winner': 'home',
                'homeSets': 3,
                'awaySets': 1
            }
        }
        
        match_id = self.firestore_helper.save_match(match_data)
        
        assert match_id is not None
        assert isinstance(match_id, str)
        
        mock_match_doc_ref.set.assert_called_once()
        
        mock_home_club_doc_ref.update.assert_called_once()
        mock_away_club_doc_ref.update.assert_called_once()
    
    def test_get_league_standings(self):
        """Test getting league standings"""
        mock_club_docs = []
        for i in range(3):
            mock_doc = Mock()
            mock_doc.id = f'club_{i}'
            mock_doc.to_dict.return_value = {
                'name': f'Club {i}',
                'stats': {
                    'wins': i + 1,
                    'losses': 3 - i,
                    'points': (i + 1) * 3,
                    'setsWon': (i + 1) * 3,
                    'setsLost': (3 - i) * 2
                }
            }
            mock_club_docs.append(mock_doc)
        
        mock_query = Mock()
        mock_query.stream.return_value = mock_club_docs
        
        mock_collection = Mock()
        mock_first_where = Mock()
        mock_first_where.where.return_value = mock_query
        mock_collection.where.return_value = mock_first_where
        self.mock_db.collection.return_value = mock_collection
        
        standings = self.firestore_helper.get_league_standings('testland', 10)
        
        assert len(standings) == 3
        
        for i in range(len(standings) - 1):
            assert standings[i]['points'] >= standings[i + 1]['points']
        
        for i, club in enumerate(standings):
            assert club['position'] == i + 1
        
        self.mock_db.collection.assert_called_with('clubs')
        mock_collection.where.assert_called_with('countryId', '==', 'testland')
        mock_first_where.where.assert_called_with('divisionTier', '==', 10)
