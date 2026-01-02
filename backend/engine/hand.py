from collections import namedtuple
from typing import Optional

Card = namedtuple('Card', ['rank', 'suit'])

# PBN rank mapping (T = 10)
PBN_RANK_MAP = {'A': 'A', 'K': 'K', 'Q': 'Q', 'J': 'J', 'T': 'T',
                '10': 'T', '9': '9', '8': '8', '7': '7', '6': '6',
                '5': '5', '4': '4', '3': '3', '2': '2'}

# Suit order for PBN (Spades.Hearts.Diamonds.Clubs)
PBN_SUITS = ['♠', '♥', '♦', '♣']


class Hand:
    """Represents a 13-card bridge hand and evaluates its properties."""

    def __init__(self, cards):
        if len(cards) != 13:
            raise ValueError("A hand must contain exactly 13 cards.")

        suit_order = {'♠': 0, '♥': 1, '♦': 2, '♣': 3}
        rank_order_map = {rank: i for i, rank in enumerate('23456789TJQKA')}
        self.cards = sorted(cards, key=lambda card: (suit_order[card.suit], -rank_order_map[card.rank]))

        # Store original suit lengths and points (immutable after initialization)
        self.suit_lengths = self._get_suit_lengths()
        self.hcp = self._calculate_hcp()
        self.suit_hcp = self._calculate_suit_hcp()
        self.dist_points = self._calculate_distribution_points()
        self.total_points = self.hcp + self.dist_points
        self.is_balanced = self._check_is_balanced()

    def __str__(self):
        hand_str = ""
        for suit in ['♠', '♥', '♦', '♣']:
            cards_in_suit = [c.rank for c in self.cards if c.suit == suit]
            hand_str += f"{suit} {' '.join(cards_in_suit)}\n"
        return hand_str.strip()

    def _calculate_hcp(self):
        points = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
        return sum(points.get(card.rank, 0) for card in self.cards)

    def _calculate_suit_hcp(self):
        points = {'A': 4, 'K': 3, 'Q': 2, 'J': 1}
        suit_points = {'♠': 0, '♥': 0, '♦': 0, '♣': 0}
        for card in self.cards:
            suit_points[card.suit] += points.get(card.rank, 0)
        return suit_points

    def _calculate_distribution_points(self):
        points = 0
        for length in self.suit_lengths.values():
            if length == 5: points += 1
            elif length == 6: points += 2
            elif length >= 7: points += 3
        return points

    def _get_suit_lengths(self):
        lengths = {'♠': 0, '♥': 0, '♦': 0, '♣': 0}
        for card in self.cards:
            lengths[card.suit] += 1
        return lengths

    def _check_is_balanced(self):
        counts = list(self.suit_lengths.values())
        return 0 not in counts and 1 not in counts and counts.count(2) <= 1

    # =========================================================================
    # PBN (Portable Bridge Notation) Support
    # =========================================================================

    @classmethod
    def from_pbn(cls, pbn_string: str) -> 'Hand':
        """
        Create a Hand from a PBN-formatted string.

        PBN format: "AKQJ.T987.654.32" where:
        - Suits are separated by periods
        - Order is always Spades.Hearts.Diamonds.Clubs
        - T represents 10
        - Empty suits use no characters (e.g., "AK..QJT98.76543")
        """
        # Handle optional direction prefix (e.g., "N:AK97543.K.T3.AK7")
        if len(pbn_string) >= 2 and pbn_string[1] == ':':
            pbn_string = pbn_string[2:]

        suit_parts = pbn_string.split('.')

        if len(suit_parts) != 4:
            raise ValueError(
                f"PBN string must have exactly 4 suits separated by periods. "
                f"Got {len(suit_parts)} parts: '{pbn_string}'"
            )

        cards = []
        for i, part in enumerate(suit_parts):
            suit = PBN_SUITS[i]
            for char in part:
                rank = PBN_RANK_MAP.get(char.upper())
                if rank is None:
                    raise ValueError(f"Invalid rank character '{char}' in PBN string")
                cards.append(Card(rank, suit))

        if len(cards) != 13:
            raise ValueError(
                f"PBN string must produce exactly 13 cards. "
                f"Got {len(cards)} cards from '{pbn_string}'"
            )

        return cls(cards)

    def to_pbn(self) -> str:
        """Export the hand to a PBN-formatted string."""
        parts = []
        for suit in PBN_SUITS:
            cards_in_suit = [c.rank for c in self.cards if c.suit == suit]
            parts.append("".join(cards_in_suit))
        return ".".join(parts)

    def to_pbn_with_direction(self, direction: str = 'S') -> str:
        """Export the hand to a PBN-formatted string with direction prefix."""
        return f"{direction}:{self.to_pbn()}"

    @classmethod
    def from_lin(cls, lin_string: str) -> 'Hand':
        """
        Create a Hand from a LIN-formatted string (Bridge Base Online format).

        LIN format uses S, H, D, C as suit prefixes:
        "SAKQ7543HKT3CAKD7" or "S AKQ7543 H K T3 C AK D 7"
        """
        lin_string = lin_string.replace(' ', '')
        lin_suit_map = {'S': '♠', 'H': '♥', 'D': '♦', 'C': '♣'}

        cards = []
        current_suit = None

        for char in lin_string.upper():
            if char in lin_suit_map:
                current_suit = lin_suit_map[char]
            elif current_suit:
                rank = PBN_RANK_MAP.get(char)
                if rank:
                    cards.append(Card(rank, current_suit))

        if len(cards) != 13:
            raise ValueError(
                f"LIN string must produce exactly 13 cards. "
                f"Got {len(cards)} cards from '{lin_string}'"
            )

        return cls(cards)

    def __repr__(self):
        """Return a detailed representation for debugging."""
        return f"Hand(pbn='{self.to_pbn()}', hcp={self.hcp}, shape={self.shape_string})"

    @property
    def shape_string(self) -> str:
        """Return shape as a string like '5-4-3-1'."""
        lengths = [self.suit_lengths[s] for s in PBN_SUITS]
        return '-'.join(str(l) for l in lengths)

    @property
    def sorted_shape(self) -> str:
        """Return shape sorted by length like '5431'."""
        lengths = sorted(self.suit_lengths.values(), reverse=True)
        return ''.join(str(l) for l in lengths)
