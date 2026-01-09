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


class TestFeedbackMessageAccuracy:
    """
    Test that feedback messages are situationally accurate.

    These tests verify that:
    - "Ruffing" is only used when actually ruffing (playing trump while void)
    - "Wins this trick" is only claimed when we know it will win
    - Leading trump is not called a "ruff"
    - Messages match the actual play situation
    """

    @pytest.fixture
    def generator(self):
        """Create feedback generator (DDS disabled for unit tests)"""
        return PlayFeedbackGenerator(use_dds=False)

    @pytest.fixture
    def spade_contract(self):
        """Create a spade contract for testing trump plays"""
        return Contract(level=4, strain='♠', declarer='S')

    @pytest.fixture
    def nt_contract(self):
        """Create a NT contract for testing non-trump plays"""
        return Contract(level=3, strain='NT', declarer='S')

    def create_play_state(self, contract, hands_dict, current_trick=None, trick_history=None):
        """Helper to create a PlayState for testing

        Note: Uses _skip_validation=True for Hand to allow partial hands in tests.
        In real play, hands start with 13 cards but diminish as cards are played.
        """
        hands = {}
        for pos, cards in hands_dict.items():
            hand_cards = [Card(rank=c[0], suit=c[1]) for c in cards]
            # Skip validation to allow partial hands for testing mid-play scenarios
            hands[pos] = Hand(cards=hand_cards, _skip_validation=True)

        return PlayState(
            contract=contract,
            hands=hands,
            current_trick=current_trick or [],
            tricks_won={'N': 0, 'E': 0, 'S': 0, 'W': 0},
            trick_history=trick_history or [],
            next_to_play='S'
        )

    # === LEADING TRUMP TESTS ===

    def test_leading_trump_not_called_ruff(self, generator, spade_contract):
        """Leading trump should NOT be called a 'ruff'"""
        # Set up state where South is leading (no current trick)
        state = self.create_play_state(
            spade_contract,
            hands_dict={
                'N': [('A', '♥'), ('K', '♥')],
                'E': [('Q', '♥'), ('J', '♥')],
                'S': [('A', '♠'), ('K', '♠')],  # Has trumps
                'W': [('T', '♥'), ('9', '♥')]
            },
            current_trick=[]  # No cards played yet - South is leading
        )

        # South leads the Ace of spades (trump)
        user_card = Card('A', '♠')
        message = generator._explain_optimal_play("A♠", PlayCategory.TRUMPING, state, 'S')

        # Should NOT say "ruff" - leading trump is not a ruff
        assert "ruff" not in message.lower(), f"Leading trump incorrectly called a ruff: {message}"
        assert "leading" in message.lower() or "correct" in message.lower(), f"Message should mention leading: {message}"

    # === ACTUAL RUFF TESTS ===

    def test_ruff_second_hand_no_win_claim(self, generator, spade_contract):
        """Ruffing in 2nd seat should NOT claim 'wins this trick' (could be overruffed)"""
        # West led a heart, East (2nd hand) is void and ruffs
        state = self.create_play_state(
            spade_contract,
            hands_dict={
                'N': [('A', '♥'), ('K', '♥')],
                'E': [('5', '♠'), ('3', '♠')],  # Void in hearts, has trumps
                'S': [('Q', '♥'), ('J', '♥')],
                'W': [('T', '♥'), ('9', '♥')]
            },
            current_trick=[
                (Card('T', '♥'), 'W')  # West led 10 of hearts
            ]
        )

        # East ruffs with 5 of spades (2nd hand)
        message = generator._explain_optimal_play("5♠", PlayCategory.TRUMPING, state, 'E')

        # Should NOT claim "wins this trick" - South or North might overruff
        assert "wins this trick" not in message.lower(), f"2nd hand ruff incorrectly claims win: {message}"
        # Should say ruff since actually ruffing (void in led suit)
        assert "ruff" in message.lower(), f"Should mention ruffing: {message}"

    def test_ruff_third_hand_no_win_claim(self, generator, spade_contract):
        """Ruffing in 3rd seat should NOT claim 'wins this trick' (4th hand could overruff)"""
        # West led heart, East followed, South (3rd hand) is void and ruffs
        state = self.create_play_state(
            spade_contract,
            hands_dict={
                'N': [('A', '♥'), ('K', '♥')],
                'E': [('Q', '♥'), ('J', '♥')],
                'S': [('5', '♠'), ('3', '♠')],  # Void in hearts, has trumps
                'W': [('T', '♥'), ('9', '♥')]
            },
            current_trick=[
                (Card('T', '♥'), 'W'),  # West led
                (Card('Q', '♥'), 'E')   # East followed
            ]
        )

        # South ruffs with 5 of spades (3rd hand)
        message = generator._explain_optimal_play("5♠", PlayCategory.TRUMPING, state, 'S')

        # Should NOT claim "wins this trick" - North might overruff
        assert "wins this trick" not in message.lower(), f"3rd hand ruff incorrectly claims win: {message}"

    def test_ruff_fourth_hand_can_claim_win(self, generator, spade_contract):
        """Ruffing in 4th seat CAN claim 'wins' since no one else can play"""
        # West led heart, East/South followed, North (4th hand) is void and ruffs
        state = self.create_play_state(
            spade_contract,
            hands_dict={
                'N': [('5', '♠'), ('3', '♠')],  # Void in hearts, has trumps
                'E': [('Q', '♥'), ('J', '♥')],
                'S': [('K', '♥'), ('9', '♥')],
                'W': [('T', '♥'), ('8', '♥')]
            },
            current_trick=[
                (Card('T', '♥'), 'W'),  # West led
                (Card('Q', '♥'), 'E'),  # East followed
                (Card('K', '♥'), 'S')   # South followed
            ]
        )

        # North ruffs with 5 of spades (4th hand) - this WILL win
        message = generator._explain_optimal_play("5♠", PlayCategory.TRUMPING, state, 'N')

        # CAN claim "wins" since 4th hand and no higher trump played
        assert "wins" in message.lower(), f"4th hand ruff should claim win: {message}"

    def test_ruff_fourth_hand_higher_trump_already_played(self, generator, spade_contract):
        """4th hand ruff with lower trump should NOT claim 'wins'"""
        # Someone already trumped higher
        state = self.create_play_state(
            spade_contract,
            hands_dict={
                'N': [('3', '♠'), ('2', '♠')],  # Only low trumps
                'E': [('Q', '♥'), ('J', '♥')],
                'S': [('K', '♥'), ('9', '♥')],
                'W': [('T', '♥'), ('8', '♥')]
            },
            current_trick=[
                (Card('T', '♥'), 'W'),  # West led heart
                (Card('A', '♠'), 'E'),  # East ruffed with Ace of spades!
                (Card('K', '♥'), 'S')   # South followed
            ]
        )

        # North plays 3 of spades (4th hand) - can't beat East's Ace
        message = generator._explain_optimal_play("3♠", PlayCategory.TRUMPING, state, 'N')

        # Should NOT claim "wins" since East's Ace of spades beats our 3
        assert "wins this trick" not in message.lower(), f"Should not claim win when outtrumped: {message}"

    # === OVERRUFF TESTS ===

    def test_overruff_message(self, generator, spade_contract):
        """Overruffing should be identified correctly"""
        # West led heart, East ruffed, South overruffs
        state = self.create_play_state(
            spade_contract,
            hands_dict={
                'N': [('A', '♥'), ('K', '♥')],
                'E': [('5', '♠')],  # East ruffed
                'S': [('K', '♠'), ('Q', '♠')],  # South has higher trumps
                'W': [('T', '♥'), ('9', '♥')]
            },
            current_trick=[
                (Card('T', '♥'), 'W'),  # West led
                (Card('5', '♠'), 'E')   # East ruffed with 5♠
            ]
        )

        # South overruffs - categorize should return OVERRUFFING
        category = generator._categorize_play(state, 'S', Card('K', '♠'))
        assert category == PlayCategory.OVERRUFFING, f"Should categorize as overruffing: {category}"

    # === CATEGORIZATION TESTS ===

    def test_categorize_opening_lead(self, generator, spade_contract):
        """Opening lead should be categorized correctly"""
        state = self.create_play_state(
            spade_contract,
            hands_dict={
                'N': [('A', '♥'), ('K', '♥')],
                'E': [('Q', '♥'), ('J', '♥')],
                'S': [('T', '♥'), ('9', '♥')],
                'W': [('8', '♥'), ('7', '♥')]
            },
            current_trick=[],
            trick_history=[]  # No tricks played yet
        )

        category = generator._categorize_play(state, 'W', Card('8', '♥'))
        assert category == PlayCategory.OPENING_LEAD

    def test_categorize_subsequent_lead_not_opening(self, generator, spade_contract):
        """Leading to 2nd+ trick should NOT be opening lead"""
        # Create a completed trick in history
        from engine.play_engine import Trick
        completed_trick = Trick(
            cards=[(Card('A', '♥'), 'W'), (Card('K', '♥'), 'N'),
                   (Card('Q', '♥'), 'E'), (Card('J', '♥'), 'S')],
            leader='W',
            winner='W'
        )

        state = self.create_play_state(
            spade_contract,
            hands_dict={
                'N': [('T', '♥')],
                'E': [('9', '♥')],
                'S': [('8', '♥')],
                'W': [('7', '♥')]
            },
            current_trick=[],  # Leading to new trick
            trick_history=[completed_trick]  # But not first trick
        )

        category = generator._categorize_play(state, 'W', Card('7', '♥'))
        # Should NOT be OPENING_LEAD since we have trick history
        assert category != PlayCategory.OPENING_LEAD, f"2nd trick lead incorrectly categorized as opening: {category}"

    def test_categorize_following_suit(self, generator, spade_contract):
        """Following suit should be categorized correctly"""
        state = self.create_play_state(
            spade_contract,
            hands_dict={
                'N': [('A', '♥'), ('K', '♥')],
                'E': [('Q', '♥'), ('J', '♥')],
                'S': [('T', '♥'), ('9', '♥')],
                'W': [('8', '♥'), ('7', '♥')]
            },
            current_trick=[
                (Card('A', '♥'), 'W')  # West led heart
            ]
        )

        # East follows with heart
        category = generator._categorize_play(state, 'E', Card('Q', '♥'))
        assert category == PlayCategory.FOLLOWING_SUIT

    def test_categorize_discarding_no_trump(self, generator, nt_contract):
        """Discarding in NT (no trump) when void"""
        state = self.create_play_state(
            nt_contract,
            hands_dict={
                'N': [('A', '♣'), ('K', '♣')],  # Only clubs
                'E': [('Q', '♥'), ('J', '♥')],
                'S': [('T', '♥'), ('9', '♥')],
                'W': [('8', '♥'), ('7', '♥')]
            },
            current_trick=[
                (Card('Q', '♥'), 'W')  # West led heart
            ]
        )

        # North is void in hearts, discards a club (NT so no trump)
        category = generator._categorize_play(state, 'N', Card('K', '♣'))
        assert category == PlayCategory.DISCARDING

    def test_categorize_sluffing_could_trump(self, generator, spade_contract):
        """Sluffing (discarding when could trump) should be categorized correctly"""
        state = self.create_play_state(
            spade_contract,
            hands_dict={
                'N': [('A', '♠'), ('K', '♣')],  # Has trump but discards club
                'E': [('Q', '♥'), ('J', '♥')],
                'S': [('T', '♥'), ('9', '♥')],
                'W': [('8', '♥'), ('7', '♥')]
            },
            current_trick=[
                (Card('Q', '♥'), 'W')  # West led heart
            ]
        )

        # North is void in hearts, has trump but discards club instead
        category = generator._categorize_play(state, 'N', Card('K', '♣'))
        assert category == PlayCategory.SLUFFING

    # === HINT ACCURACY TESTS ===

    def test_hint_for_leading_trump(self, generator, spade_contract):
        """Hint for leading trump should be about trump management, not ruffing"""
        state = self.create_play_state(
            spade_contract,
            hands_dict={
                'N': [('A', '♥')],
                'E': [('Q', '♥')],
                'S': [('A', '♠')],
                'W': [('T', '♥')]
            },
            current_trick=[]  # Leading
        )

        hint = generator._generate_hint(PlayCategory.TRUMPING, PlayCorrectnessLevel.SUBOPTIMAL,
                                        Card('A', '♠'), [Card('A', '♠')], state, 'S')

        # Should mention trump management, not ruffing
        assert "ruff" not in hint.lower() or "trump" in hint.lower(), f"Lead trump hint wrong: {hint}"

    def test_hint_for_ruffing(self, generator, spade_contract):
        """Hint for ruffing should mention ruffing"""
        state = self.create_play_state(
            spade_contract,
            hands_dict={
                'N': [('A', '♥')],
                'E': [('Q', '♥')],
                'S': [('5', '♠')],  # Void in hearts
                'W': [('T', '♥')]
            },
            current_trick=[
                (Card('T', '♥'), 'W')  # West led heart
            ]
        )

        hint = generator._generate_hint(PlayCategory.TRUMPING, PlayCorrectnessLevel.SUBOPTIMAL,
                                        Card('5', '♠'), [Card('5', '♠')], state, 'S')

        # Should mention ruffing
        assert "ruff" in hint.lower(), f"Ruff hint should mention ruffing: {hint}"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
