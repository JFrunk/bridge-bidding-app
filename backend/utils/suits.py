"""
Suit normalization utilities for bridge engine.

Establishes Unicode symbols (♠, ♥, ♦, ♣) as the ground truth format
for all internal suit representation. ASCII letters (S, H, D, C) are
accepted as input and converted to symbols; they should never persist
in engine data structures.

Usage:
    from utils.suits import normalize_suit, is_valid_suit, SUITS

    normalize_suit('S')   # -> '♠'
    normalize_suit('♠')   # -> '♠'
    normalize_suit('NT')  # -> 'NT'
    is_valid_suit('♠')    # -> True
    is_valid_suit('S')    # -> False (ASCII, not normalized)
"""

from typing import Optional, Set

# === CONSTANTS ===

# Ground truth: Unicode symbols for all internal suit representation
SUITS: list[str] = ['♠', '♥', '♦', '♣']
SUIT_SYMBOLS: Set[str] = {'♠', '♥', '♦', '♣'}

# Suit ranking (for bidding order): ♣ < ♦ < ♥ < ♠
SUIT_RANK: dict[str, int] = {'♣': 0, '♦': 1, '♥': 2, '♠': 3}

# ASCII-to-Unicode mapping (for external format ingestion)
ASCII_TO_SYMBOL: dict[str, str] = {
    'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣',
    's': '♠', 'h': '♥', 'd': '♦', 'c': '♣',
}

# Unicode-to-ASCII mapping (for DDS and external systems)
SYMBOL_TO_ASCII: dict[str, str] = {
    '♠': 'S', '♥': 'H', '♦': 'D', '♣': 'C',
}

# Suit display names
SUIT_NAMES: dict[str, str] = {
    '♠': 'Spades', '♥': 'Hearts', '♦': 'Diamonds', '♣': 'Clubs',
}


# === NORMALIZATION ===

def normalize_suit(suit: Optional[str]) -> str:
    """
    Normalize a suit identifier to the canonical Unicode symbol format.

    Accepts Unicode symbols, ASCII letters, or 'NT'. Returns the
    canonical format used throughout the engine.

    Args:
        suit: Suit identifier ('♠', 'S', 's', 'NT', etc.)

    Returns:
        Unicode symbol ('♠', '♥', '♦', '♣') or 'NT'

    Raises:
        ValueError: If suit is not a recognized identifier

    Examples:
        normalize_suit('♠')  -> '♠'
        normalize_suit('S')  -> '♠'
        normalize_suit('NT') -> 'NT'
    """
    if suit is None:
        raise ValueError("Suit cannot be None")

    # Already a valid symbol
    if suit in SUIT_SYMBOLS:
        return suit

    # NT is a special case (no trump)
    if suit.upper() == 'NT':
        return 'NT'

    # ASCII letter conversion
    if suit in ASCII_TO_SYMBOL:
        return ASCII_TO_SYMBOL[suit]

    raise ValueError(f"Unrecognized suit identifier: {suit!r}")


def is_valid_suit(suit: str) -> bool:
    """
    Check if a suit is in the canonical Unicode symbol format.

    This does NOT accept ASCII letters — use normalize_suit() first
    if you need to convert from ASCII.

    Args:
        suit: Suit string to validate

    Returns:
        True if suit is a Unicode symbol (♠, ♥, ♦, ♣)
    """
    return suit in SUIT_SYMBOLS


def to_ascii(suit: str) -> str:
    """
    Convert a Unicode suit symbol to its ASCII equivalent.

    Used when interfacing with external systems (DDS, PBN export, etc.)
    that require letter-based suit identifiers.

    Args:
        suit: Unicode suit symbol ('♠', '♥', '♦', '♣') or 'NT'

    Returns:
        ASCII letter ('S', 'H', 'D', 'C') or 'NT'

    Raises:
        ValueError: If suit is not a valid Unicode symbol
    """
    if suit == 'NT':
        return 'NT'
    if suit in SYMBOL_TO_ASCII:
        return SYMBOL_TO_ASCII[suit]
    raise ValueError(f"Cannot convert to ASCII: {suit!r} (not a Unicode suit symbol)")
