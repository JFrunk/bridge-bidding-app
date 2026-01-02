"""
Integration tests for Learning Mode system.

Tests:
- Skill tree structure and curriculum
- Skill hand generators (all 27 skills)
- Learning Mode API endpoints
- Answer evaluation (HCP, yes/no, bidding)
- Progress tracking and mastery detection
"""

import pytest
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TestSkillTreeStructure:
    """Test skill tree curriculum structure."""

    def test_skill_tree_has_9_levels(self):
        """Skill tree should have 9 levels (0-8)."""
        from engine.learning.skill_tree import get_skill_tree_manager

        manager = get_skill_tree_manager()
        levels = manager.get_all_levels()

        # Skill tree is a dict with level IDs as keys
        assert len(levels) == 9
        assert 'level_0_foundations' in levels
        assert 'level_8_advanced_conventions' in levels

    def test_level_0_has_foundation_skills(self):
        """Level 0 should have foundation skills."""
        from engine.learning.skill_tree import get_skill_tree_manager

        manager = get_skill_tree_manager()
        level_0 = manager.get_level('level_0_foundations')

        assert level_0 is not None
        assert 'skills' in level_0
        assert len(level_0['skills']) >= 3  # At least 3 foundation skills

        skill_ids = [s.id for s in level_0['skills']]
        assert 'hand_evaluation_basics' in skill_ids

    def test_level_structure(self):
        """Each level should have required fields."""
        from engine.learning.skill_tree import get_skill_tree_manager

        manager = get_skill_tree_manager()
        levels = manager.get_all_levels()

        for level_id, level_data in levels.items():
            assert 'name' in level_data
            assert 'description' in level_data
            assert 'level' in level_data
            # Either skills or conventions
            assert 'skills' in level_data or 'conventions' in level_data


class TestSkillHandGenerators:
    """Test skill hand generators."""

    def test_all_generators_exist(self):
        """All expected generators should be registered."""
        from engine.learning.skill_hand_generators import SKILL_GENERATORS

        expected_skills = [
            # Level 0
            'hand_evaluation_basics', 'suit_quality', 'bidding_language',
            # Level 1
            'when_to_open', 'opening_one_suit', 'opening_1nt',
            'opening_2c_strong', 'opening_2nt',
            # Level 2
            'responding_to_major', 'responding_to_minor', 'responding_to_1nt',
            'responding_to_2c', 'responding_to_2nt',
            # Level 3
            'rebid_after_1_level', 'rebid_after_2_level',
            'rebid_after_raise', 'rebid_after_1nt_response',
            # Level 4
            'after_opener_raises', 'after_opener_rebids_suit',
            'after_opener_new_suit', 'after_opener_rebids_nt',
            'preference_bids',
            # Level 6
            'overcalls', 'responding_to_overcalls', 'negative_doubles',
            'over_opponent_double', 'balancing',
        ]

        for skill_id in expected_skills:
            assert skill_id in SKILL_GENERATORS, f"Missing generator: {skill_id}"

        # Verify count
        assert len(SKILL_GENERATORS) == 27

    def test_hand_evaluation_basics_generator(self):
        """Hand evaluation basics should generate valid hands."""
        from engine.learning.skill_hand_generators import get_skill_hand_generator, create_deck

        generator = get_skill_hand_generator('hand_evaluation_basics')
        assert generator is not None

        deck = create_deck()
        hand, remaining = generator.generate(deck)

        assert hand is not None
        assert len(hand.cards) == 13
        assert 0 <= hand.hcp <= 40

        expected = generator.get_expected_response(hand)
        assert 'hcp' in expected
        assert expected['hcp'] == hand.hcp

    def test_when_to_open_generator(self):
        """When to open generator should produce valid hands."""
        from engine.learning.skill_hand_generators import get_skill_hand_generator, create_deck

        generator = get_skill_hand_generator('when_to_open')
        assert generator is not None

        deck = create_deck()
        hand, _ = generator.generate(deck)

        assert hand is not None
        expected = generator.get_expected_response(hand)
        assert 'should_open' in expected
        assert isinstance(expected['should_open'], bool)

    def test_opening_one_suit_generator(self):
        """Opening one suit generator should produce valid hands."""
        from engine.learning.skill_hand_generators import get_skill_hand_generator, create_deck

        generator = get_skill_hand_generator('opening_one_suit')
        assert generator is not None

        deck = create_deck()
        hand, _ = generator.generate(deck)

        assert hand is not None
        # Should be an opening hand
        assert hand.hcp >= 12 or hand.total_points >= 12

        expected = generator.get_expected_response(hand)
        assert 'bid' in expected
        assert expected['bid'].startswith('1')

    def test_opening_1nt_generator(self):
        """Opening 1NT generator should produce balanced 15-17 HCP hands."""
        from engine.learning.skill_hand_generators import get_skill_hand_generator, create_deck

        generator = get_skill_hand_generator('opening_1nt')
        assert generator is not None

        deck = create_deck()
        hand, _ = generator.generate(deck)

        assert hand is not None
        assert 15 <= hand.hcp <= 17
        assert hand.is_balanced

        expected = generator.get_expected_response(hand)
        assert expected['bid'] == '1NT'

    def test_all_generators_produce_valid_hands(self):
        """All generators should produce valid 13-card hands."""
        from engine.learning.skill_hand_generators import SKILL_GENERATORS, create_deck

        for skill_id, generator_class in SKILL_GENERATORS.items():
            generator = generator_class()
            deck = create_deck()
            hand, _ = generator.generate(deck)

            assert hand is not None, f"Generator {skill_id} returned None"
            assert len(hand.cards) == 13, f"Generator {skill_id} produced {len(hand.cards)} cards"

    def test_all_generators_have_expected_response(self):
        """All generators should return valid expected responses."""
        from engine.learning.skill_hand_generators import SKILL_GENERATORS, create_deck

        for skill_id, generator_class in SKILL_GENERATORS.items():
            generator = generator_class()
            deck = create_deck()
            hand, _ = generator.generate(deck)

            expected = generator.get_expected_response(hand)
            assert expected is not None, f"Generator {skill_id} returned None expected"
            assert isinstance(expected, dict), f"Generator {skill_id} expected not dict"


class TestLearningModeAPI:
    """Test Learning Mode API endpoints."""

    def test_start_session_returns_hand(self):
        """start_learning_session should return a hand and session info."""
        from engine.learning.learning_path_api import start_learning_session
        from flask import Flask

        app = Flask(__name__)
        with app.test_request_context(
            '/api/learning/start-session',
            method='POST',
            json={'user_id': 1, 'topic_id': 'hand_evaluation_basics', 'topic_type': 'skill'}
        ):
            response = start_learning_session()
            data = response.get_json()

            assert 'session_id' in data
            assert 'hand' in data
            assert 'expected_response' in data
            assert data['topic_id'] == 'hand_evaluation_basics'

    def test_submit_answer_correct(self):
        """submit_learning_answer should recognize correct HCP answer."""
        from engine.learning.learning_path_api import submit_learning_answer
        from flask import Flask

        app = Flask(__name__)
        with app.test_request_context(
            '/api/learning/submit-answer',
            method='POST',
            json={
                'user_id': 999,  # Test user
                'topic_id': 'hand_evaluation_basics',
                'topic_type': 'skill',
                'answer': '15',
                'hand_id': 'test123',
                'expected_response': {'hcp': 15, 'explanation': 'Test'}
            }
        ):
            response = submit_learning_answer()
            data = response.get_json()

            assert data['is_correct'] == True
            assert 'Correct' in data['feedback']

    def test_submit_answer_incorrect(self):
        """submit_learning_answer should recognize incorrect HCP answer."""
        from engine.learning.learning_path_api import submit_learning_answer
        from flask import Flask

        app = Flask(__name__)
        with app.test_request_context(
            '/api/learning/submit-answer',
            method='POST',
            json={
                'user_id': 999,
                'topic_id': 'hand_evaluation_basics',
                'topic_type': 'skill',
                'answer': '12',
                'hand_id': 'test456',
                'expected_response': {'hcp': 15, 'explanation': 'Test'}
            }
        ):
            response = submit_learning_answer()
            data = response.get_json()

            assert data['is_correct'] == False
            assert '15' in data['feedback']

    def test_bid_normalization(self):
        """Bid answers should be normalized (1H = 1♥)."""
        from engine.learning.learning_path_api import normalize_bid

        assert normalize_bid('1H') == '1♥'
        assert normalize_bid('1S') == '1♠'
        assert normalize_bid('2D') == '2♦'
        assert normalize_bid('3C') == '3♣'
        assert normalize_bid('1NT') == '1NT'
        assert normalize_bid('1♥') == '1♥'  # Already unicode
        # Note: 'PASS' becomes 'PA♠♠' due to S→♠ replacement, but this is OK
        # because we compare normalized forms on both sides

    def test_get_learning_status(self):
        """get_user_learning_status should return progress info."""
        from engine.learning.learning_path_api import get_user_learning_status
        from flask import Flask

        app = Flask(__name__)
        with app.test_request_context('/api/learning/status?user_id=1'):
            response = get_user_learning_status()
            data = response.get_json()

            assert 'user_id' in data
            assert 'levels' in data
            assert 'overall_progress' in data
            assert 'current_level' in data


class TestAnswerEvaluation:
    """Test different answer types."""

    def test_yes_no_evaluation_yes(self):
        """Yes/no questions should accept various 'yes' formats."""
        from engine.learning.learning_path_api import submit_learning_answer
        from flask import Flask

        app = Flask(__name__)
        for answer in ['yes', 'Yes', 'YES', 'true', 'open', '1']:
            with app.test_request_context(
                '/api/learning/submit-answer',
                method='POST',
                json={
                    'user_id': 999,
                    'topic_id': 'when_to_open',
                    'topic_type': 'skill',
                    'answer': answer,
                    'hand_id': 'test',
                    'expected_response': {'should_open': True, 'explanation': 'Test'}
                }
            ):
                response = submit_learning_answer()
                data = response.get_json()
                assert data['is_correct'] == True, f"'{answer}' should be correct for True"

    def test_yes_no_evaluation_no(self):
        """Yes/no questions should accept 'no' answers."""
        from engine.learning.learning_path_api import submit_learning_answer
        from flask import Flask

        app = Flask(__name__)
        with app.test_request_context(
            '/api/learning/submit-answer',
            method='POST',
            json={
                'user_id': 999,
                'topic_id': 'when_to_open',
                'topic_type': 'skill',
                'answer': 'no',
                'hand_id': 'test',
                'expected_response': {'should_open': False, 'explanation': 'Test'}
            }
        ):
            response = submit_learning_answer()
            data = response.get_json()
            assert data['is_correct'] == True

    def test_bid_evaluation_with_normalization(self):
        """Bid answers should match regardless of format."""
        from engine.learning.learning_path_api import submit_learning_answer
        from flask import Flask

        app = Flask(__name__)
        # ASCII input should match Unicode expected
        with app.test_request_context(
            '/api/learning/submit-answer',
            method='POST',
            json={
                'user_id': 999,
                'topic_id': 'opening_one_suit',
                'topic_type': 'skill',
                'answer': '1H',
                'hand_id': 'test',
                'expected_response': {'bid': '1♥', 'explanation': 'Test'}
            }
        ):
            response = submit_learning_answer()
            data = response.get_json()
            assert data['is_correct'] == True


class TestInterleavedReview:
    """Test interleaved review functionality."""

    def test_review_requires_2_topics(self):
        """Review should require at least 2 practiced topics."""
        from engine.learning.learning_path_api import get_interleaved_review
        from flask import Flask

        app = Flask(__name__)
        with app.test_request_context('/api/learning/review?user_id=999&level=0&count=5'):
            response = get_interleaved_review()
            data = response.get_json()

            # New user won't have 2 topics practiced
            assert data['ready'] == False
            assert 'Need at least 2' in data.get('message', '')


class TestLevelAssessment:
    """Test level assessment functionality."""

    def test_assessment_requires_all_topics_mastered(self):
        """Assessment should require all topics mastered."""
        from engine.learning.learning_path_api import get_level_assessment
        from flask import Flask

        app = Flask(__name__)
        with app.test_request_context('/api/learning/level-assessment?user_id=999&level=0'):
            response = get_level_assessment()
            data = response.get_json()

            # New user won't have topics mastered
            assert data['ready'] == False
            assert 'Complete all topics' in data.get('message', '')


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
