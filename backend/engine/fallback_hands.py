"""
Fallback Hands for Convention Practice

Pre-scripted hands for each convention that are guaranteed to meet
SAYC requirements. Used when random generation times out to ensure
users always get a valid learning experience.

Each hand is stored in PBN format (Spades.Hearts.Diamonds.Clubs).
"""

import random
from engine.hand import Hand

# =============================================================================
# STRONG 2♣ - Requires 22+ HCP or 19-21 with 9+ playing tricks
# =============================================================================
STRONG_2C_HANDS = [
    # 22+ HCP hands (balanced)
    "AKQJ.AKQ.AQJ.KQ3",    # 31 HCP, 4-3-3-3, pure power
    "AKQ.AKQJ.AKJ.432",    # 27 HCP, 3-4-3-3
    "AKQ5.AK43.AKQ.K2",    # 28 HCP, 4-4-3-2
    "AK.AKQJ2.AKQ.J32",    # 27 HCP, 2-5-3-3
    "AKQJ.AK.AKQ32.K2",    # 29 HCP, 4-2-5-2

    # 22+ HCP hands (unbalanced - strong suits)
    "AKQJT98.AK.AK.32",    # 24 HCP, 7-2-2-2, spade suit
    "AK.AKQJT98.AK.32",    # 24 HCP, 2-7-2-2, heart suit
    "AKQJT9.AK.AKQ.32",    # 26 HCP, 6-2-3-2
    "AK.AKQ.AKQJT9.32",    # 26 HCP, 2-3-6-2, diamond suit
    "AKQ.AK.AKQ.QJT98",    # 28 HCP, 3-2-3-5, club suit

    # 19-21 HCP with massive playing strength (9+ playing tricks)
    "AKQJT9876.A.AK.2",   # 21 HCP, 9-card spade suit, 12.5 playing tricks
    "AKQ.AKQJT987.A.2",   # 23 HCP, 8-card heart suit, 12.5 playing tricks
    "AKQJT987.AK.AK.2",   # 24 HCP, 8-card spade suit, 12.5 playing tricks
    "AKQ.AK.AKQJT9.32",   # 25 HCP, 6-card diamond suit
    "AKQ.A.AKQJT987.2",   # 23 HCP, 8-card diamond suit, 12.5 playing tricks
]

# =============================================================================
# 1NT OPENING - Requires 15-17 HCP and balanced shape
# =============================================================================
ONE_NT_HANDS = [
    "AQ32.KJ4.QJ5.K32",    # 15 HCP, 4-3-3-3
    "KQ4.AJ32.KQ5.J32",    # 16 HCP, 3-4-3-3
    "AK32.KQ4.J32.Q54",    # 16 HCP, 4-3-3-3
    "KQJ.AQ32.K54.J32",    # 16 HCP, 3-4-3-3
    "AQ54.KJ3.KQ2.J32",    # 17 HCP, 4-3-3-3
    "KJ32.AQ4.KJ5.Q32",    # 16 HCP, 4-3-3-3
    "AK32.QJ4.KJ32.Q3",    # 16 HCP, 4-3-4-2 (5-3-3-2 variant)
    "KQJ4.AQ32.K5.J32",    # 16 HCP, 4-4-2-3
    "AQ3.KJ54.KQ32.J2",    # 16 HCP, 3-4-4-2
    "KQ32.AJ4.KQ5.432",    # 15 HCP, 4-3-3-3
]

# =============================================================================
# WEAK TWO BIDS - Requires 6-10 HCP, 6-card suit, 2 of top 3 honors (A/K/Q)
# =============================================================================
WEAK_TWO_HANDS = [
    # Weak Two Hearts (6 hearts, 6-10 HCP, 2 of A/K/Q)
    "32.KQT987.QJ2.32",    # 8 HCP, 6 hearts with KQ
    "43.AQT987.432.32",    # 6 HCP, 6 hearts with AQ
    "32.AKT987.J32.43",    # 8 HCP, 6 hearts with AK
    "J2.KQJ987.432.32",    # 7 HCP, 6 hearts with KQ
    "43.AKJ987.432.32",    # 8 HCP, 6 hearts with AK

    # Weak Two Spades (6 spades, 6-10 HCP, 2 of A/K/Q)
    "KQT987.32.QJ2.32",    # 8 HCP, 6 spades with KQ
    "AQT987.43.432.32",    # 6 HCP, 6 spades with AQ
    "AKT987.32.J32.43",    # 8 HCP, 6 spades with AK
    "KQJ987.J2.432.32",    # 7 HCP, 6 spades with KQ
    "AKJ987.43.432.32",    # 8 HCP, 6 spades with AK

    # Weak Two Diamonds (6 diamonds, 6-10 HCP, 2 of A/K/Q)
    "32.43.KQT987.QJ2",    # 8 HCP, 6 diamonds with KQ
    "43.32.AQT987.432",    # 6 HCP, 6 diamonds with AQ
    "32.43.AKT987.J32",    # 8 HCP, 6 diamonds with AK
    "J2.32.KQJ987.432",    # 7 HCP, 6 diamonds with KQ
    "43.32.AKJ987.432",    # 8 HCP, 6 diamonds with AK
]

# =============================================================================
# Registry mapping convention names to fallback hands
# =============================================================================
FALLBACK_REGISTRY = {
    "Strong2C": STRONG_2C_HANDS,
    "1NT": ONE_NT_HANDS,
    "Preempt": WEAK_TWO_HANDS,
}


def get_fallback_hand(convention_name: str) -> Hand:
    """
    Get a random pre-scripted hand for a convention.

    Args:
        convention_name: Name of the convention (e.g., "Strong2C", "1NT")

    Returns:
        Hand object or None if convention not found
    """
    hands = FALLBACK_REGISTRY.get(convention_name)
    if not hands:
        return None

    pbn = random.choice(hands)
    return Hand.from_pbn(pbn)


def get_remaining_deck(used_hand: Hand) -> list:
    """
    Generate the remaining deck after a hand is dealt.

    Args:
        used_hand: Hand object that has been dealt

    Returns:
        List of Card objects representing remaining 39 cards
    """
    from engine.hand import Card

    ranks = '23456789TJQKA'
    suits = ['♠', '♥', '♦', '♣']

    full_deck = [Card(r, s) for r in ranks for s in suits]
    used_cards = set((c.rank, c.suit) for c in used_hand.cards)

    return [c for c in full_deck if (c.rank, c.suit) not in used_cards]
