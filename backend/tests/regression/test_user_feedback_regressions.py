"""
User Feedback Regression Tests

This file contains regression tests created from user feedback.
Each test represents a bug reported by users that has been fixed.

WORKFLOW for adding new regression tests:
1. User reports bug via feedback
2. Create minimal reproduction test (should FAIL before fix)
3. Implement fix
4. Verify test passes
5. Keep test permanently to prevent regression

Run with: pytest tests/regression/test_user_feedback_regressions.py -v
"""
import pytest
from datetime import datetime
from dataclasses import dataclass
from typing import List, Optional

from engine.hand import Hand, Card
from engine.bidding_engine import BiddingEngine


# =============================================================================
# Helper Classes
# =============================================================================

@dataclass
class UserFeedbackBug:
    """Represents a bug reported via user feedback."""
    bug_id: str
    reported_date: str
    user_description: str
    hand_spec: dict  # spades, hearts, diamonds, clubs
    auction_before: List[str]
    expected_bid: str
    incorrect_bid: str  # What the engine incorrectly produced
    fix_description: str

    def make_hand(self) -> Hand:
        """Create a Hand from the specification."""
        cards = []
        for suit, holding in [
            ('♠', self.hand_spec.get('spades', '')),
            ('♥', self.hand_spec.get('hearts', '')),
            ('♦', self.hand_spec.get('diamonds', '')),
            ('♣', self.hand_spec.get('clubs', ''))
        ]:
            for rank in holding:
                cards.append(Card(rank, suit))
        return Hand(cards)


def get_bid(hand: Hand, auction: List[str] = None, dealer: str = "South") -> str:
    """Get bid from the bidding engine."""
    engine = BiddingEngine()
    auction_history = [{"bid": b} for b in (auction or [])]

    # Determine position based on auction length
    positions = ["North", "East", "South", "West"]
    my_position = positions[len(auction_history) % 4] if auction_history else "South"

    result = engine.get_next_bid(
        hand=hand,
        auction_history=auction_history,
        my_position=my_position,
        vulnerability="None",
        dealer=dealer
    )
    return result[0]


# =============================================================================
# User Feedback Bug Registry
# =============================================================================

USER_FEEDBACK_BUGS = [
    UserFeedbackBug(
        bug_id="UFB-2026-02-05-001",
        reported_date="2026-02-05",
        user_description="Why did partner not bid 2C to indicate 22 points?",
        hand_spec={'spades': 'AKQJ', 'hearts': 'AK53', 'diamonds': 'KQ7', 'clubs': '64'},
        auction_before=[],
        expected_bid="2♣",
        incorrect_bid="2NT",
        fix_description="2♣ rule required 22+ HCP AND (4+ quick tricks OR 24+ HCP). "
                       "Fixed to require only 22+ HCP."
    ),
    # Template for future bugs:
    # UserFeedbackBug(
    #     bug_id="UFB-YYYY-MM-DD-NNN",
    #     reported_date="YYYY-MM-DD",
    #     user_description="User's description of the issue",
    #     hand_spec={'spades': 'XXX', 'hearts': 'XXX', 'diamonds': 'XXX', 'clubs': 'XXX'},
    #     auction_before=["1♣", "Pass"],  # Auction before user's bid
    #     expected_bid="1♥",
    #     incorrect_bid="Pass",
    #     fix_description="Brief description of the fix"
    # ),
]


# =============================================================================
# Regression Tests
# =============================================================================

class TestUserFeedbackRegressions:
    """Test all bugs reported via user feedback."""

    @pytest.mark.parametrize("bug", USER_FEEDBACK_BUGS, ids=lambda b: b.bug_id)
    def test_user_feedback_bug(self, bug: UserFeedbackBug):
        """Test that the reported bug is fixed and stays fixed."""
        hand = bug.make_hand()
        actual_bid = get_bid(hand, bug.auction_before)

        assert actual_bid == bug.expected_bid, (
            f"\n"
            f"Bug ID: {bug.bug_id}\n"
            f"Reported: {bug.reported_date}\n"
            f"Description: {bug.user_description}\n"
            f"Expected: {bug.expected_bid}\n"
            f"Got: {actual_bid} (was incorrectly: {bug.incorrect_bid})\n"
            f"Fix: {bug.fix_description}\n"
            f"Hand HCP: {hand.hcp}\n"
            f"REGRESSION DETECTED - Bug has reappeared!"
        )


class TestUserFeedbackDocumentation:
    """Generate documentation of all user feedback bugs."""

    def test_generate_bug_report(self):
        """Print summary of all user feedback bugs (always passes)."""
        print("\n" + "="*70)
        print("USER FEEDBACK BUG REGISTRY")
        print("="*70)

        for bug in USER_FEEDBACK_BUGS:
            print(f"\n[{bug.bug_id}] Reported: {bug.reported_date}")
            print(f"  Issue: {bug.user_description[:60]}...")
            print(f"  Fixed: {bug.incorrect_bid} -> {bug.expected_bid}")

        print("\n" + "="*70)
        print(f"Total bugs tracked: {len(USER_FEEDBACK_BUGS)}")
        print("="*70)

        assert True  # Always passes


# =============================================================================
# Quick Add Template
# =============================================================================

def create_regression_test_template(
    bug_id: str,
    user_description: str,
    spades: str,
    hearts: str,
    diamonds: str,
    clubs: str,
    auction_before: List[str],
    expected_bid: str,
    incorrect_bid: str,
    fix_description: str
) -> str:
    """Generate code template for a new regression test.

    Usage:
        print(create_regression_test_template(
            bug_id="UFB-2026-02-05-002",
            user_description="Partner passed my takeout double",
            spades="A72",
            hearts="QJ76",
            diamonds="Q73",
            clubs="A72",
            auction_before=["Pass", "1♣", "X", "Pass"],
            expected_bid="1♥",
            incorrect_bid="Pass",
            fix_description="Advancer pass rule had too low HCP threshold"
        ))
    """
    return f'''
    UserFeedbackBug(
        bug_id="{bug_id}",
        reported_date="{datetime.now().strftime('%Y-%m-%d')}",
        user_description="{user_description}",
        hand_spec={{'spades': '{spades}', 'hearts': '{hearts}', 'diamonds': '{diamonds}', 'clubs': '{clubs}'}},
        auction_before={auction_before},
        expected_bid="{expected_bid}",
        incorrect_bid="{incorrect_bid}",
        fix_description="{fix_description}"
    ),
'''


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
