"""
Regression test for forcing bid enforcement.

Bug: Feb 17, 2026 - Partner's forcing bid (takeout double) was not enforced,
allowing responder to pass when they should have bid.

Test ensures:
1. Pass is rejected when partner's bid is forcing for one round
2. Pass is rejected when auction is game-forced
3. Alternative bids are selected when Pass is illegal
"""

import pytest
from engine.hand import Hand, Card
from engine.v2.interpreters.schema_interpreter import SchemaInterpreter, ForcingLevel


def test_forcing_one_round_prevents_pass():
    """Test that FORCING_1_ROUND prevents passing on partner's next turn."""
    interpreter = SchemaInterpreter()

    # Set forcing level to FORCING_1_ROUND (simulating partner's takeout double)
    interpreter.auction_state.forcing_level = ForcingLevel.FORCING_1_ROUND

    # Create features for a weak hand (would normally pass)
    features = {
        'hcp': 6,
        'is_balanced': True,
        'longest_suit_length': 3,
        'spade_length': 3,
        'heart_length': 3,
        'diamond_length': 4,
        'club_length': 3,
        'auction_level': 3,
        'is_contested': True,
        'partner_last_bid': 'X',
        'opponent_last_bid': '3♦',
    }

    # Validate that Pass is rejected
    validation = interpreter.validate_bid_against_forcing("Pass", features['auction_level'], '')

    assert validation.is_valid is False, "Pass should be rejected when forcing for one round"
    assert "forcing for one round" in validation.reason.lower(), \
        f"Validation reason should mention forcing, got: {validation.reason}"
    assert validation.violation_type == "ONE_ROUND_VIOLATION"


def test_game_force_prevents_pass():
    """Test that GAME_FORCE prevents passing until game is reached."""
    interpreter = SchemaInterpreter()

    # Set game forcing
    interpreter.auction_state.is_game_forced = True
    interpreter.auction_state.forcing_level = ForcingLevel.GAME_FORCE

    # Create features at 2-level (below game)
    features = {
        'hcp': 12,
        'auction_level': 2,
        'is_contested': False,
        'partner_last_bid': '2♥',
    }

    # Validate that Pass is rejected
    validation = interpreter.validate_bid_against_forcing("Pass", features['auction_level'], '♥')

    assert validation.is_valid is False, "Pass should be rejected when game-forced below game"
    assert "game forced" in validation.reason.lower(), \
        f"Validation reason should mention game force, got: {validation.reason}"
    assert validation.violation_type == "GAME_FORCE_VIOLATION"


def test_game_force_allows_pass_at_game():
    """Test that GAME_FORCE allows passing once game is reached."""
    interpreter = SchemaInterpreter()

    # Set game forcing
    interpreter.auction_state.is_game_forced = True
    interpreter.auction_state.forcing_level = ForcingLevel.GAME_FORCE

    # Create features at 4-level (game reached)
    features = {
        'hcp': 12,
        'auction_level': 4,
        'is_contested': False,
        'partner_last_bid': '4♥',
    }

    # Validate that Pass is allowed
    validation = interpreter.validate_bid_against_forcing("Pass", features['auction_level'], '♥')

    assert validation.is_valid is True, "Pass should be allowed when game is reached"


def test_evaluate_rejects_illegal_pass():
    """Test that evaluate() method rejects Pass and selects alternative bid."""
    interpreter = SchemaInterpreter()

    # Set forcing level
    interpreter.auction_state.forcing_level = ForcingLevel.FORCING_1_ROUND

    # Create features that would normally generate a Pass bid
    # but also have alternatives available
    features = {
        'hcp': 8,
        'is_balanced': True,
        'longest_suit_length': 4,
        'spade_length': 4,
        'heart_length': 3,
        'diamond_length': 3,
        'club_length': 3,
        'auction_level': 3,
        'is_contested': True,
        'partner_last_bid': 'X',
        'opponent_last_bid': '3♦',
        'opener_relationship': 'Partner',
        'opening_bid': None,
    }

    # Evaluate - should NOT return Pass
    result = interpreter.evaluate(features)

    if result is not None:
        bid, explanation = result
        assert bid != "Pass", \
            f"evaluate() should not return Pass when forcing, got: {bid}"
        # Should return some alternative bid (likely a suit bid or NT)
        assert bid in ['3♥', '3♠', '3NT', '4♣', '4♦', '4♥', '4♠'], \
            f"Expected a valid alternative bid, got: {bid}"


def test_non_forcing_allows_pass():
    """Test that NON_FORCING allows passing normally."""
    interpreter = SchemaInterpreter()

    # Set non-forcing (default state)
    interpreter.auction_state.forcing_level = ForcingLevel.NON_FORCING

    # Create features for a weak hand
    features = {
        'hcp': 5,
        'auction_level': 3,
        'is_contested': True,
    }

    # Validate that Pass is allowed
    validation = interpreter.validate_bid_against_forcing("Pass", features['auction_level'], '')

    assert validation.is_valid is True, "Pass should be allowed when non-forcing"
