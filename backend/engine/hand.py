from collections import namedtuple

Card = namedtuple('Card', ['rank', 'suit'])

class Hand:
    """Represents a 13-card bridge hand and evaluates its properties."""
    def __init__(self, cards):
        if len(cards) != 13:
            raise ValueError("A hand must contain exactly 13 cards.")
        
        suit_order = {'♠': 0, '♥': 1, '♦': 2, '♣': 3}
        rank_order_map = {rank: i for i, rank in enumerate('23456789TJQKA')}
        self.cards = sorted(cards, key=lambda card: (suit_order[card.suit], -rank_order_map[card.rank]))
        
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