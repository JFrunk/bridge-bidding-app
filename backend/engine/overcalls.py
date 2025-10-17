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
        # Need to beat the LAST bid in the auction, not just the opening bid
        auction_history = features.get('auction_history', [])
        last_bid = None
        for bid in reversed(auction_history):
            if bid != 'Pass' and bid not in ['X', 'XX']:
                last_bid = bid
                break

        # If no non-pass bid found, use opening bid as fallback
        if not last_bid:
            last_bid = features['auction_features']['opening_bid']

        # Also track the opening bid for context (e.g., to check if it's a preempt)
        opening_bid = features['auction_features']['opening_bid']

        # Try NT overcall first (passing both last_bid and opening_bid for context)
        nt_overcall = self._try_nt_overcall(hand, last_bid, opening_bid, is_balancing)
        if nt_overcall:
            return nt_overcall

        # Try suit overcalls (check majors first, then minors)
        for suit in ['♠', '♥', '♦', '♣']:
            suit_overcall = self._try_suit_overcall(hand, suit, last_bid, is_balancing)
            if suit_overcall:
                return suit_overcall

        return None

    def _try_nt_overcall(self, hand: Hand, last_bid: str, opening_bid: str, is_balancing: bool) -> Optional[Tuple[str, str]]:
        """
        Try NT overcall at appropriate level.
        1NT - Direct: 15-18 HCP, balanced, stopper
        1NT - Balancing: 12-15 HCP, balanced, stopper
        2NT - 19-20 HCP, balanced, stopper (over 1-level openings)
        3NT - 21-24 HCP, balanced, stopper OR 18-21 HCP over preempt/competitive auction

        Args:
            last_bid: The most recent non-pass bid we need to beat
            opening_bid: The original opening bid (for context on preempts)
        """
        if not hand.is_balanced:
            return None

        # Check for stopper in opponent's suit (use opening bid to identify their suit)
        if 'NT' in last_bid:
            return None  # Can't overcall NT over NT

        opponent_suit = opening_bid[1] if len(opening_bid) >= 2 else None
        if not opponent_suit or not self._has_stopper(hand, opponent_suit):
            return None

        # Determine if opponent made a preemptive opening (2-level or higher)
        try:
            opening_level = int(opening_bid[0])
            is_opponent_preempt = opening_level >= 2
        except (ValueError, IndexError):
            is_opponent_preempt = False

        # Try 3NT first (for very strong hands or over preempts/competitive auctions)
        if is_opponent_preempt or last_bid != opening_bid:
            # Over preempts OR competitive auctions: 3NT shows 18-21 HCP with stopper
            if 18 <= hand.hcp <= 21:
                if self._is_bid_higher('3NT', last_bid):
                    context = "preempt" if is_opponent_preempt else "competitive auction"
                    return ('3NT', f"3NT overcall over {context} showing {hand.hcp} HCP, balanced, with stopper in {opponent_suit}.")

        # Over 1-level openings with very strong hands
        if not is_opponent_preempt and 22 <= hand.hcp <= 24:
            if self._is_bid_higher('3NT', last_bid):
                return ('3NT', f"3NT overcall showing {hand.hcp} HCP, balanced, with stopper.")

        # Try 2NT (19-20 HCP over 1-level openings, must be direct - not after raise)
        if not is_opponent_preempt and last_bid == opening_bid and 19 <= hand.hcp <= 20:
            if self._is_bid_higher('2NT', last_bid):
                return ('2NT', f"2NT overcall showing {hand.hcp} HCP, balanced, with stopper.")

        # Try 1NT
        if is_balancing:
            if 12 <= hand.hcp <= 15:
                if self._is_bid_higher('1NT', last_bid):
                    return ('1NT', f"Balancing 1NT showing {hand.hcp} HCP, balanced, with stopper.")
        else:
            if 15 <= hand.hcp <= 18:
                if self._is_bid_higher('1NT', last_bid):
                    return ('1NT', f"1NT overcall showing {hand.hcp} HCP, balanced, with stopper.")

        return None

    def _has_stopper(self, hand: Hand, suit: str) -> bool:
        """
        Check if hand has a stopper in the given suit.

        Full stopper: A, Kx+, Qxx+, Jxxx+
        Partial stopper (acceptable with 15+ HCP): Jxx, Qx, Txx+

        With 15+ HCP, we accept marginal stoppers (Jxx, Qx) as sufficient
        for 1NT overcall, as the hand strength compensates for the weak stopper.
        """
        suit_cards = [card for card in hand.cards if card.suit == suit]
        if not suit_cards:
            return False  # Void is not a stopper for NT

        ranks = [card.rank for card in suit_cards]
        length = len(ranks)

        # Full stoppers (any HCP)
        if 'A' in ranks:
            return True
        if 'K' in ranks and length >= 2:
            return True
        if 'Q' in ranks and length >= 3:
            return True
        if 'J' in ranks and length >= 4:
            return True

        # Marginal stoppers (acceptable with 15+ HCP for competitive bidding)
        if hand.hcp >= 15:
            # Jxx is acceptable with strong hand (e.g., West's J-7-6 with 15 HCP)
            if 'J' in ranks and length >= 3:
                return True
            # Qx is acceptable with strong hand
            if 'Q' in ranks and length >= 2:
                return True
            # Txx+ is acceptable with very strong hand (16+ HCP)
            if hand.hcp >= 16 and 'T' in ranks and length >= 3:
                return True

        return False

    def _try_suit_overcall(self, hand: Hand, suit: str, opponent_bid: str, is_balancing: bool) -> Optional[Tuple[str, str]]:
        """
        Try suit overcall at the cheapest legal level (simple or jump).

        Requirements:
        - Direct 1-level: 8-16 HCP, 5+ card suit, good quality
        - Direct 2-level: 11-16 HCP, 5+ card suit, very good quality
        - Direct 3-level (over preempt): 13-16 HCP, 5+ card suit, excellent quality
        - Weak Jump: 6-10 HCP, 6-card suit, preemptive (SAYC standard)
        - Balancing: 7-16 HCP, slightly relaxed suit quality
        """
        suit_length = hand.suit_lengths.get(suit, 0)

        # Need at least 5-card suit (6 for weak jump)
        if suit_length < 5:
            return None

        # Detect if opponent made a preempt (2-level or 3-level opening)
        try:
            opponent_level = int(opponent_bid[0])
            is_preempt = opponent_level >= 2
        except (ValueError, IndexError):
            is_preempt = False

        # Evaluate suit quality
        suit_quality = self._evaluate_suit_quality(hand, suit)

        # Check for weak jump overcall first (SAYC standard)
        # Example: After opponent opens 1♥, we can jump to 2♠ with 6 spades and 6-10 HCP
        if not is_balancing and 6 <= hand.hcp <= 10 and suit_length >= 6:
            # Find the jump level (one level higher than necessary)
            try:
                opponent_level = int(opponent_bid[0])
                opponent_suit = opponent_bid[1:]
                suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}

                # Calculate minimum level needed to overcall
                if suit_rank.get(suit, 0) > suit_rank.get(opponent_suit, 0):
                    min_level = opponent_level
                else:
                    min_level = opponent_level + 1

                # Jump level is one higher
                jump_level = min_level + 1

                # Only make weak jumps at 2 or 3 level (not 4+)
                if jump_level in [2, 3]:
                    jump_bid = f"{jump_level}{suit}"

                    # Need decent suit quality for weak jump
                    if suit_quality >= self._quality_to_score('fair'):
                        suit_name = {'♠': 'Spade', '♥': 'Heart', '♦': 'Diamond', '♣': 'Club'}[suit]
                        return (jump_bid, f"Weak jump overcall showing {hand.hcp} HCP and 6-card {suit_name} suit (preemptive).")
            except (ValueError, IndexError):
                pass

        # Find cheapest legal level for simple overcalls
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
                # 3-level overcall (usually over preempts)
                # Stricter requirements when overcalling at 3-level

                if is_preempt:
                    # Over opponent's preempt: need 13-17 HCP and excellent suit
                    if hand.hcp < 13 or hand.hcp > 17:
                        continue
                    # Need excellent suit quality to compete at 3-level over preempt
                    if suit_quality < self._quality_to_score('excellent'):
                        continue
                else:
                    # 3-level simple overcall in competitive auction (not over preempt)
                    if hand.hcp < 13 or hand.hcp > 16:
                        continue
                    # Need very good suit
                    if suit_quality < self._quality_to_score('very_good'):
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