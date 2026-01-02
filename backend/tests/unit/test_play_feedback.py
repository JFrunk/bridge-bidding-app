"""
Unit tests for PlayFeedbackGenerator

Tests the play feedback system including:
- PlayFeedback dataclass
- PlayCorrectnessLevel enum
- PlayCategory enum
- PlayFeedbackGenerator class
- Scoring logic
- Feedback generation
"""

import pytest
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from engine.feedback.play_feedback import (
    PlayFeedback,
    PlayCorrectnessLevel,
    PlayCategory,
    PlayFeedbackGenerator,
    get_play_feedback_generator
)
from engine.hand import Hand, Card
from engine.play_engine import PlayState, Contract


class TestPlayCorrectnessLevel:
    """Test PlayCorrectnessLevel enum"""

    def test_enum_values(self):
        """Test all correctness levels have expected values"""
        assert PlayCorrectnessLevel.OPTIMAL.value == "optimal"
        assert PlayCorrectnessLevel.GOOD.value == "good"
        assert PlayCorrectnessLevel.SUBOPTIMAL.value == "suboptimal"
        assert PlayCorrectnessLevel.BLUNDER.value == "blunder"
        assert PlayCorrectnessLevel.ILLEGAL.value == "illegal"

    def test_enum_count(self):
        """Test we have expected number of levels"""
        assert len(PlayCorrectnessLevel) == 5


class TestPlayCategory:
    """Test PlayCategory enum"""

    def test_enum_values(self):
        """Test all play categories have expected values"""
        assert PlayCategory.OPENING_LEAD.value == "opening_lead"
        assert PlayCategory.FOLLOWING_SUIT.value == "following_suit"
        assert PlayCategory.DISCARDING.value == "discarding"
        assert PlayCategory.TRUMPING.value == "trumping"
        assert PlayCategory.FINESSING.value == "finessing"
        assert PlayCategory.CASHING.value == "cashing"

    def test_enum_count(self):
        """Test we have expected number of categories"""
        assert len(PlayCategory) == 10  # All categories


class TestPlayFeedback:
    """Test PlayFeedback dataclass"""

    def create_sample_feedback(self, correctness=PlayCorrectnessLevel.OPTIMAL, score=10.0):
        """Create a sample feedback object for testing"""
        return PlayFeedback(
            trick_number=1,
            position="S",
            user_card="A♠",
            correctness=correctness,
            score=score,
            optimal_cards=["A♠", "K♠"],
            tricks_with_user_card=10,
            tricks_with_optimal=10,
            tricks_cost=0,
            play_category=PlayCategory.CASHING,
            contract="4♠ by S",
            is_declarer_side=True,
            led_suit=None,
            reasoning="Cashing the ace is correct",
            helpful_hint="",
            key_concept="Cashing winners",
            difficulty="beginner"
        )

    def test_to_dict(self):
        """Test conversion to dictionary"""
        feedback = self.create_sample_feedback()
        d = feedback.to_dict()

        assert d['trick_number'] == 1
        assert d['position'] == "S"
        assert d['user_card'] == "A♠"
        assert d['correctness'] == "optimal"
        assert d['score'] == 10.0
        assert d['play_category'] == "cashing"

    def test_to_user_message_optimal(self):
        """Test user message for optimal play"""
        feedback = self.create_sample_feedback(PlayCorrectnessLevel.OPTIMAL, 10.0)
        message = feedback.to_user_message()

        assert "Excellent" in message or "best" in message
        assert "A♠" in message

    def test_to_user_message_good(self):
        """Test user message for good play"""
        feedback = self.create_sample_feedback(PlayCorrectnessLevel.GOOD, 7.5)
        feedback.tricks_cost = 1
        message = feedback.to_user_message()

        assert "reasonable" in message.lower() or "acceptable" in message.lower()

    def test_to_user_message_suboptimal(self):
        """Test user message for suboptimal play"""
        feedback = self.create_sample_feedback(PlayCorrectnessLevel.SUBOPTIMAL, 5.0)
        feedback.tricks_cost = 2
        message = feedback.to_user_message()

        assert "better" in message.lower()

    def test_to_user_message_blunder(self):
        """Test user message for blunder"""
        feedback = self.create_sample_feedback(PlayCorrectnessLevel.BLUNDER, 2.0)
        feedback.tricks_cost = 3
        message = feedback.to_user_message()

        assert "mistake" in message.lower() or "significant" in message.lower()

    def test_to_user_message_illegal(self):
        """Test user message for illegal play"""
        feedback = self.create_sample_feedback(PlayCorrectnessLevel.ILLEGAL, 0.0)
        message = feedback.to_user_message()

        assert "Illegal" in message or "follow suit" in message.lower()


class TestPlayFeedbackGenerator:
    """Test PlayFeedbackGenerator class"""

    @pytest.fixture
    def generator(self):
        """Create feedback generator (with DDS disabled for unit tests)"""
        gen = PlayFeedbackGenerator(use_dds=False)
        return gen

    def test_dds_availability_check(self, generator):
        """Test DDS availability is detected correctly"""
        # On macOS, DDS should be unavailable
        import platform
        if platform.system() != 'Linux':
            assert not generator.dds_available
        # On Linux with endplay, it might be available

    def test_get_correctness_and_score_optimal(self, generator):
        """Test scoring for optimal plays (0 tricks cost)"""
        correctness, score = generator._get_correctness_and_score(0)
        assert correctness == PlayCorrectnessLevel.OPTIMAL
        assert score == 10.0

    def test_get_correctness_and_score_good(self, generator):
        """Test scoring for good plays (1 trick cost)"""
        correctness, score = generator._get_correctness_and_score(1)
        assert correctness == PlayCorrectnessLevel.GOOD
        assert score == 7.5

    def test_get_correctness_and_score_suboptimal(self, generator):
        """Test scoring for suboptimal plays (2 tricks cost)"""
        correctness, score = generator._get_correctness_and_score(2)
        assert correctness == PlayCorrectnessLevel.SUBOPTIMAL
        assert score == 5.0

    def test_get_correctness_and_score_blunder(self, generator):
        """Test scoring for blunders (3+ tricks cost)"""
        correctness, score = generator._get_correctness_and_score(3)
        assert correctness == PlayCorrectnessLevel.BLUNDER
        assert score <= 3.0

    def test_get_correctness_and_score_severe_blunder(self, generator):
        """Test scoring for severe blunders (5+ tricks cost)"""
        correctness, score = generator._get_correctness_and_score(5)
        assert correctness == PlayCorrectnessLevel.BLUNDER
        assert score >= 0  # Score should not go negative

    def test_get_key_concept(self, generator):
        """Test key concept extraction for different play categories"""
        assert "Opening leads" in generator._get_key_concept(PlayCategory.OPENING_LEAD)
        assert "Trump" in generator._get_key_concept(PlayCategory.TRUMPING)
        assert "Cashing" in generator._get_key_concept(PlayCategory.CASHING)
        assert "Finessing" in generator._get_key_concept(PlayCategory.FINESSING)

    def test_is_declarer_side_ns(self, generator):
        """Test declarer side detection for N/S"""
        contract = Contract(level=4, strain='♠', declarer='S')
        assert generator._is_declarer_side('S', contract)
        assert generator._is_declarer_side('N', contract)
        assert not generator._is_declarer_side('E', contract)
        assert not generator._is_declarer_side('W', contract)

    def test_is_declarer_side_ew(self, generator):
        """Test declarer side detection for E/W"""
        contract = Contract(level=3, strain='NT', declarer='E')
        assert generator._is_declarer_side('E', contract)
        assert generator._is_declarer_side('W', contract)
        assert not generator._is_declarer_side('N', contract)
        assert not generator._is_declarer_side('S', contract)


class TestPlayFeedbackGeneratorScoring:
    """Test scoring edge cases"""

    def test_score_range_valid(self):
        """Test that all scores are in valid 0-10 range"""
        generator = PlayFeedbackGenerator(use_dds=False)

        for tricks_cost in range(0, 10):
            correctness, score = generator._get_correctness_and_score(tricks_cost)
            assert 0 <= score <= 10, f"Score {score} out of range for {tricks_cost} tricks cost"

    def test_correctness_ordering(self):
        """Test that correctness levels are in expected order"""
        generator = PlayFeedbackGenerator(use_dds=False)

        scores = []
        for tricks_cost in [0, 1, 2, 3]:
            correctness, score = generator._get_correctness_and_score(tricks_cost)
            scores.append(score)

        # Scores should be decreasing (or equal) as tricks cost increases
        for i in range(len(scores) - 1):
            assert scores[i] >= scores[i + 1], f"Score ordering violated: {scores}"


class TestSingletonPattern:
    """Test singleton pattern for feedback generator"""

    def test_get_play_feedback_generator(self):
        """Test singleton returns same instance"""
        gen1 = get_play_feedback_generator(use_dds=False)
        gen2 = get_play_feedback_generator(use_dds=False)

        # Should be same instance
        assert gen1 is gen2


class TestFeedbackTextGeneration:
    """Test feedback text generation"""

    @pytest.fixture
    def generator(self):
        return PlayFeedbackGenerator(use_dds=False)

    def test_generate_feedback_optimal(self, generator):
        """Test feedback text for optimal plays"""
        # Mock parameters
        from engine.play_engine import PlayState, Contract
        from engine.hand import Hand, Card

        reasoning, hint = generator._generate_feedback_text(
            play_state=None,  # Not used in text generation
            user_card=Card('A', '♠'),
            position='S',
            optimal_cards=['A♠'],
            tricks_cost=0,
            play_category=PlayCategory.CASHING
        )

        assert len(reasoning) > 0
        assert "winner" in reasoning.lower() or "good" in reasoning.lower() or "correct" in reasoning.lower()

    def test_generate_feedback_blunder(self, generator):
        """Test feedback text for blunders"""
        reasoning, hint = generator._generate_feedback_text(
            play_state=None,
            user_card=Card('2', '♠'),
            position='S',
            optimal_cards=['A♠', 'K♠'],
            tricks_cost=3,
            play_category=PlayCategory.FOLLOWING_SUIT
        )

        assert "mistake" in reasoning.lower() or "cost" in reasoning.lower()
        assert len(hint) > 0  # Should have helpful hint for mistakes


class TestRatingToScoreMapping:
    """Test mapping between ratings and score ranges"""

    def test_rating_score_consistency(self):
        """Test that ratings correspond to expected score ranges"""
        rating_ranges = {
            'optimal': (9, 10),
            'good': (7, 9),
            'suboptimal': (4, 7),
            'blunder': (0, 4),
        }

        generator = PlayFeedbackGenerator(use_dds=False)

        # Optimal (0 tricks cost)
        correctness, score = generator._get_correctness_and_score(0)
        min_score, max_score = rating_ranges['optimal']
        assert min_score <= score <= max_score + 1, f"Optimal score {score} not in range"

        # Good (1 trick cost)
        correctness, score = generator._get_correctness_and_score(1)
        min_score, max_score = rating_ranges['good']
        assert min_score <= score <= max_score + 1, f"Good score {score} not in range"

        # Suboptimal (2 tricks cost)
        correctness, score = generator._get_correctness_and_score(2)
        min_score, max_score = rating_ranges['suboptimal']
        assert min_score <= score <= max_score + 1, f"Suboptimal score {score} not in range"

        # Blunder (3+ tricks cost)
        correctness, score = generator._get_correctness_and_score(3)
        min_score, max_score = rating_ranges['blunder']
        assert min_score <= score <= max_score + 1, f"Blunder score {score} not in range"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
