"""
Shared dealing utilities for bridge hand generation.

All hand/deck generation should go through these functions to ensure:
- Cards are dealt from a single 52-card deck (no duplicates)
- Consistent deck construction across the codebase
- Proper seeding for reproducibility
"""

import random
from typing import Dict, List, Optional

from engine.hand import Hand, Card
from utils.seats import SEAT_NAMES

# Standard card constants
RANKS = '23456789TJQKA'
SUITS = ['♠', '♥', '♦', '♣']


def create_deck() -> List[Card]:
    """Create a standard 52-card deck (unshuffled)."""
    return [Card(rank, suit) for suit in SUITS for rank in RANKS]


def shuffled_deck(seed: Optional[int] = None) -> List[Card]:
    """Create and shuffle a 52-card deck.

    Args:
        seed: Optional random seed for reproducibility.
              Only sets seed if provided (does not reset global state).
    """
    if seed is not None:
        random.seed(seed)
    deck = create_deck()
    random.shuffle(deck)
    return deck


def deal_four_hands(seed: Optional[int] = None) -> Dict[str, Hand]:
    """Deal 4 hands of 13 cards each from a single shuffled deck.

    This is the standard way to generate a bridge deal. Never generate
    4 independent hands — that allows duplicate cards across players.

    Args:
        seed: Optional random seed for reproducibility.

    Returns:
        Dict mapping position names to Hand objects.
    """
    deck = shuffled_deck(seed)
    return {
        'North': Hand(deck[0:13]),
        'East': Hand(deck[13:26]),
        'South': Hand(deck[26:39]),
        'West': Hand(deck[39:52])
    }


def deal_remaining_hands(
    assigned: Dict[str, Hand],
    seed: Optional[int] = None
) -> Dict[str, Hand]:
    """Deal remaining positions from cards not already assigned.

    Use when one or more hands are pre-constructed (e.g., scenario hands)
    and the remaining positions need random hands from leftover cards.

    Args:
        assigned: Dict of position -> Hand for pre-assigned hands.
        seed: Optional random seed.

    Returns:
        Complete dict with all 4 positions filled.
    """
    positions = SEAT_NAMES

    # Collect all cards already dealt
    used_cards = set()
    for hand in assigned.values():
        for card in hand.cards:
            used_cards.add((card.rank, card.suit))

    # Build remaining deck
    remaining = [
        Card(rank, suit)
        for suit in SUITS for rank in RANKS
        if (rank, suit) not in used_cards
    ]

    if seed is not None:
        random.seed(seed)
    random.shuffle(remaining)

    # Deal to unassigned positions
    result = dict(assigned)
    card_idx = 0
    for pos in positions:
        if pos not in result:
            result[pos] = Hand(remaining[card_idx:card_idx + 13])
            card_idx += 13

    return result
