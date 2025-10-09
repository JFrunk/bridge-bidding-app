from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict

class OvercallModule(ConventionModule):
    """
    Playbook for making overcalls (suit and 1NT) in both direct and balancing seats.

    SAYC Standards:
    - Direct seat: 8-16 HCP (1-level), 11-16 HCP (2-level)
    - Balancing seat: 7-16 HCP (can be lighter)
    - 1NT overcall: 15-18 HCP direct, 12-15 HCP balancing
    - Suit quality crucial, especially for minimum hands
    """

    def get_constraints(self) -> Dict:
        return {}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        if not self._is_applicable(features):
            return None

        # Determine if we're in balancing seat
        is_balancing = self._is_balancing_seat(features)

        return self._get_overcall_bid(hand, features, is_balancing)

    def _is_applicable(self, features: Dict) -> bool:
        """
        Overcall is applicable if:
        1. An opponent has opened
        2. We haven't bid yet
        3. We're either in direct seat OR balancing seat
        """
        auction_features = features.get('auction_features', {})
        opener_relationship = auction_features.get('opener_relationship')

        # Must be a competitive situation (opponent opened)
        if opener_relationship != 'Opponent':
            return None

        my_index = features.get('my_index', -1)
        my_bids = [bid for i, bid in enumerate(features['auction_history'])
                   if features['positions'][i % 4] == features['positions'][my_index]]

        # Haven't bid yet (or only passed)
        return len([b for b in my_bids if b != 'Pass']) == 0

    def _is_balancing_seat(self, features: Dict) -> bool:
        """
        Check if we're in balancing (pass-out) seat.
        True if last 2 bids were Pass and our Pass would end auction.
        """
        auction_history = features['auction_history']
        if len(auction_history) >= 2:
            return auction_history[-1] == 'Pass' and auction_history[-2] == 'Pass'
        return False

    def _get_overcall_bid(self, hand: Hand, features: Dict, is_balancing: bool) -> Optional[Tuple[str, str]]:
        """
        Determine the best overcall bid (suit or NT).
        Priority: 1NT overcall, then suit overcalls (majors before minors).
        """
        opponent_bid = features['auction_features']['opening_bid']

        # Try 1NT overcall first
        nt_overcall = self._try_nt_overcall(hand, opponent_bid, is_balancing)
        if nt_overcall:
            return nt_overcall

        # Try suit overcalls (check majors first, then minors)
        for suit in ['♠', '♥', '♦', '♣']:
            suit_overcall = self._try_suit_overcall(hand, suit, opponent_bid, is_balancing)
            if suit_overcall:
                return suit_overcall

        return None

    def _try_nt_overcall(self, hand: Hand, opponent_bid: str, is_balancing: bool) -> Optional[Tuple[str, str]]:
        """
        Try 1NT overcall.
        Direct: 15-18 HCP, balanced, stopper
        Balancing: 12-15 HCP, balanced, stopper
        """
        if not hand.is_balanced:
            return None

        # Check HCP requirements
        if is_balancing:
            if not (12 <= hand.hcp <= 15):
                return None
            description = "Balancing 1NT showing 12-15 HCP, balanced, with stopper."
        else:
            if not (15 <= hand.hcp <= 18):
                return None
            description = "1NT overcall showing 15-18 HCP, balanced, with stopper."

        # Check for stopper in opponent's suit
        if 'NT' in opponent_bid:
            return None  # Can't overcall 1NT over 1NT

        opponent_suit = opponent_bid[1] if len(opponent_bid) >= 2 else None
        if opponent_suit and self._has_stopper(hand, opponent_suit):
            if self._is_bid_higher('1NT', opponent_bid):
                return ('1NT', description)

        return None

    def _has_stopper(self, hand: Hand, suit: str) -> bool:
        """
        Check if hand has a stopper in the given suit.
        Stopper: A, Kx+, Qxx+, or Jxxx+
        """
        suit_cards = [card for card in hand.cards if card.suit == suit]
        if not suit_cards:
            return False  # Void is not a stopper for NT

        ranks = [card.rank for card in suit_cards]
        length = len(ranks)

        if 'A' in ranks:
            return True
        if 'K' in ranks and length >= 2:
            return True
        if 'Q' in ranks and length >= 3:
            return True
        if 'J' in ranks and length >= 4:
            return True

        return False

    def _try_suit_overcall(self, hand: Hand, suit: str, opponent_bid: str, is_balancing: bool) -> Optional[Tuple[str, str]]:
        """
        Try suit overcall at the cheapest legal level.

        Requirements:
        - Direct 1-level: 8-16 HCP, 5+ card suit, good quality
        - Direct 2-level: 11-16 HCP, 5+ card suit, very good quality
        - Balancing: 7-16 HCP, slightly relaxed suit quality
        """
        suit_length = hand.suit_lengths.get(suit, 0)

        # Need at least 5-card suit
        if suit_length < 5:
            return None

        # Evaluate suit quality
        suit_quality = self._evaluate_suit_quality(hand, suit)

        # Find cheapest legal level
        for bid_level in [1, 2, 3]:
            potential_bid = f"{bid_level}{suit}"

            if not self._is_bid_higher(potential_bid, opponent_bid):
                continue

            # Check HCP and suit quality requirements for this level
            if bid_level == 1:
                # 1-level overcall
                min_hcp = 7 if is_balancing else 8
                if hand.hcp < min_hcp or hand.hcp > 16:
                    continue

                # Suit quality: need "good" for 5-card, "fair" for 6+
                required_quality = 'fair' if suit_length >= 6 else 'good'
                if suit_quality < self._quality_to_score(required_quality):
                    continue

            elif bid_level == 2:
                # 2-level overcall (more dangerous)
                min_hcp = 10 if is_balancing else 11
                if hand.hcp < min_hcp or hand.hcp > 16:
                    continue

                # Suit quality: need "very_good" for 5-card, "good" for 6+
                required_quality = 'good' if suit_length >= 6 else 'very_good'
                if suit_quality < self._quality_to_score(required_quality):
                    continue
            else:
                # 3-level overcall (weak jump or very strong)
                # For now, skip 3-level overcalls (can add weak jump logic later)
                continue

            # We have a valid overcall!
            seat_desc = "Balancing overcall" if is_balancing else "Overcall"
            suit_name = {'♠': 'Spade', '♥': 'Heart', '♦': 'Diamond', '♣': 'Club'}[suit]
            return (potential_bid, f"{seat_desc} showing {hand.hcp} HCP and {suit_length}-card {suit_name} suit.")

        return None

    def _evaluate_suit_quality(self, hand: Hand, suit: str) -> int:
        """
        Evaluate suit quality on a scale of 0-10.

        Scoring:
        - Top honors (A, K, Q): 3 points each
        - Secondary honors (J, T): 1 point each
        - Bonus for concentrated honors (AK=+1, KQ=+1, QJ=+1, JT=+1)

        Returns: 0-10 score
        """
        suit_cards = [card for card in hand.cards if card.suit == suit]
        ranks = [card.rank for card in suit_cards]

        score = 0

        # Top honors
        if 'A' in ranks:
            score += 3
        if 'K' in ranks:
            score += 3
        if 'Q' in ranks:
            score += 3

        # Secondary honors
        if 'J' in ranks:
            score += 1
        if 'T' in ranks:
            score += 1

        # Bonus for combinations
        if 'A' in ranks and 'K' in ranks:
            score += 1
        elif 'K' in ranks and 'Q' in ranks:
            score += 1
        elif 'Q' in ranks and 'J' in ranks:
            score += 1
        elif 'J' in ranks and 'T' in ranks:
            score += 1

        return score

    def _quality_to_score(self, quality: str) -> int:
        """Convert quality descriptor to numeric score."""
        quality_map = {
            'poor': 2,      # One honor
            'fair': 4,      # Two honors or good combination
            'good': 6,      # Two top honors or strong combination
            'very_good': 8, # Three honors or AK/KQ
            'excellent': 10 # AKQ or similar
        }
        return quality_map.get(quality, 0)

    def _is_bid_higher(self, my_bid: str, other_bid: str) -> bool:
        """Check if my_bid is legally higher than other_bid."""
        suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4, 'NT': 5}
        try:
            my_level, my_suit = int(my_bid[0]), my_bid[1:]
            other_level, other_suit = int(other_bid[0]), other_bid[1:]
            if my_level > other_level:
                return True
            if my_level == other_level and suit_rank.get(my_suit, 0) > suit_rank.get(other_suit, 0):
                return True
        except (ValueError, IndexError):
            return False
        return False