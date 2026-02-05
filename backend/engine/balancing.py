"""
V3 Logic Stack: Balancing Module

Implements the "Borrowed King" principle for pass-out seat bidding.
In balancing position, we can bid with ~3 HCP less than direct seat because
partner has already shown values by passing (they couldn't act themselves).

The key insight: When opponents bid and two passes follow, partner has ~8-10 HCP
trapped behind the opener. We "borrow" from partner to protect them.

SAYC Standards for Balancing:
- Balancing 1NT: 11-14 HCP (vs 15-18 direct)
- Balancing Double: 8+ HCP (vs 12+ direct)
- Balancing Suit: 8+ HCP (vs 10+ direct at 1-level)

Date: 2026-01-07
"""

from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict


class BalancingModule(ConventionModule):
    """
    Handles competitive bidding in the pass-out (balancing) seat.

    Uses Actual HCP + Virtual Offset (+3) for decision thresholds.
    This is the "Borrowed King" principle - we're borrowing values
    from partner who has already shown strength by passing.
    """

    # The Virtual HCP Offset (Borrowed King)
    VIRTUAL_OFFSET = 3

    def get_constraints(self) -> Dict:
        """Return constraints for hand generation (testing)."""
        return {
            'hcp_min': 8,
            'hcp_max': 14,
        }

    def _estimate_partner_hcp(self, hand: Hand, features: Dict) -> int:
        """
        Estimate partner's HCP using BiddingState beliefs about all seats.

        In balancing position (opener bid, responder passed, partner passed),
        we can compute partner's likely HCP as:
            40 - my_hcp - opener_midpoint - responder_midpoint

        Falls back to VIRTUAL_OFFSET when BiddingState unavailable.
        """
        bidding_state = features.get('bidding_state')
        if bidding_state is not None:
            positions = features.get('positions', [])
            my_index = features.get('my_index')
            if positions and my_index is not None:
                from utils.seats import normalize, lho, rho
                my_seat = normalize(positions[my_index])
                # In balancing: LHO is opener, RHO is responder who passed
                lho_belief = bidding_state.seat(lho(my_seat))
                rho_belief = bidding_state.seat(rho(my_seat))
                lho_mid = (lho_belief.hcp[0] + lho_belief.hcp[1]) // 2
                rho_mid = (rho_belief.hcp[0] + rho_belief.hcp[1]) // 2
                partner_est = max(0, 40 - hand.hcp - lho_mid - rho_mid)
                return partner_est
        return self.VIRTUAL_OFFSET

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Evaluate balancing action in pass-out seat.

        Returns (bid, explanation) or None if no balancing action appropriate.
        """
        # Check if we're actually in balancing seat
        if not self._is_applicable(features):
            return None

        # Get the opponent's opening bid
        auction_features = features.get('auction_features', {})
        opening_bid = auction_features.get('opening_bid', '')

        if not opening_bid or opening_bid in ['Pass', 'X', 'XX']:
            return None

        # Estimate partner's HCP using BiddingState (or fall back to +3 offset)
        partner_est = self._estimate_partner_hcp(hand, features)
        adjusted_hcp = hand.hcp + partner_est

        # Try each action in priority order
        # Priority: 1NT > Double > Suit bid > Pass

        # 1. Try Balancing 1NT (11-14 actual HCP, balanced, stopper)
        nt_bid = self._try_balancing_1nt(hand, features, opening_bid)
        if nt_bid:
            return nt_bid

        # 2. Try Balancing Takeout Double (9+ actual HCP, support for unbid)
        double_bid = self._try_balancing_double(hand, features, opening_bid, adjusted_hcp)
        if double_bid:
            return double_bid

        # 3. Try Balancing Suit Bid (8+ actual HCP, 5+ card suit)
        suit_bid = self._try_balancing_suit(hand, features, opening_bid, adjusted_hcp)
        if suit_bid:
            return suit_bid

        # 4. Pass with weak hand (< 8 HCP) or unsuitable shape
        if hand.hcp < 5:
            return ("Pass", f"Too weak to balance with only {hand.hcp} HCP.")

        # Check if we have defensive values in opponent's suit (trap pass)
        opponent_suit = opening_bid[1] if len(opening_bid) >= 2 else None
        if opponent_suit and self._has_trap_hand(hand, opponent_suit):
            return ("Pass", f"Trap pass with {hand.hcp} HCP and defensive values in {opponent_suit}.")

        # Default: Pass without suitable action
        return ("Pass", f"No suitable balancing action with {hand.hcp} HCP.")

    def _is_applicable(self, features: Dict) -> bool:
        """
        Check if balancing module applies.

        Applicable when:
        1. Opponent opened
        2. Partner passed
        3. RHO passed
        4. Our pass would end the auction (passout seat)
        """
        auction_features = features.get('auction_features', {})
        balancing_info = auction_features.get('balancing', {})

        # Use pre-calculated balancing detection from feature_extractor
        if balancing_info.get('is_balancing', False):
            return True

        # Fallback: manual detection
        opener_relationship = auction_features.get('opener_relationship')
        if opener_relationship != 'Opponent':
            return False

        auction_history = features.get('auction_history', [])
        if len(auction_history) < 3:
            return False

        # Check if last two bids were passes
        if auction_history[-1] != 'Pass' or auction_history[-2] != 'Pass':
            return False

        # Check that there's exactly one non-pass bid (the opening)
        non_pass_bids = [b for b in auction_history if b not in ['Pass', 'X', 'XX']]
        if len(non_pass_bids) != 1:
            return False

        return True

    def _try_balancing_1nt(self, hand: Hand, features: Dict, opening_bid: str) -> Optional[Tuple[str, str]]:
        """
        Try Balancing 1NT: 11-14 HCP (vs 15-18 direct), balanced, stopper.

        The Borrowed King: With 11-14 HCP in balancing seat, we effectively
        show 14-17 combined with partner's trapped ~3 HCP.
        """
        # Must be balanced
        if not hand.is_balanced:
            return None

        # HCP range for balancing 1NT: 11-14 (SAYC)
        if hand.hcp < 11 or hand.hcp > 14:
            return None

        # Must have stopper in opponent's suit
        opponent_suit = opening_bid[1] if len(opening_bid) >= 2 else None
        if not opponent_suit or not self._has_stopper(hand, opponent_suit):
            return None

        # Check if 1NT is a legal bid (higher than opening)
        if not self._is_bid_legal('1NT', opening_bid):
            return None

        return (
            '1NT',
            f"Balancing 1NT with {hand.hcp} HCP, balanced, stopper in {opponent_suit}. "
            f"(Borrowed King: shows 11-14 vs direct 15-18)"
        )

    def _try_balancing_double(self, hand: Hand, features: Dict, opening_bid: str, adjusted_hcp: int) -> Optional[Tuple[str, str]]:
        """
        Try Balancing Takeout Double: 8+ actual HCP (vs 12+ direct).

        Requirements:
        - 8+ actual HCP (11+ adjusted with +3 offset)
        - Shortness in opponent's suit (0-2 cards)
        - Support for unbid suits (3+ cards in each)
        """
        # Minimum 8 actual HCP for balancing double
        if hand.hcp < 8:
            return None

        # Get opponent's suit
        opponent_suit = opening_bid[1] if len(opening_bid) >= 2 and opening_bid[1] in '♣♦♥♠' else None
        if not opponent_suit:
            return None

        # Must have shortness in opponent's suit (0-2 cards)
        opp_suit_length = hand.suit_lengths.get(opponent_suit, 0)
        if opp_suit_length > 2:
            return None

        # Must have support for unbid suits (3+ cards in each)
        unbid_suits = [s for s in '♠♥♦♣' if s != opponent_suit]
        for suit in unbid_suits:
            if hand.suit_lengths.get(suit, 0) < 3:
                return None

        # STRONG HAND EXCEPTION: 15+ HCP balanced without stopper
        # These hands are too strong for 1NT but can still double
        if hand.hcp >= 15:
            return (
                'X',
                f"Strong balancing double with {hand.hcp} HCP. "
                f"Will bid NT next to show 15+ HCP."
            )

        return (
            'X',
            f"Balancing takeout double with {hand.hcp} HCP (Borrowed King: 8+ vs direct 12+), "
            f"short in {opponent_suit}, support for unbid suits."
        )

    def _try_balancing_suit(self, hand: Hand, features: Dict, opening_bid: str, adjusted_hcp: int) -> Optional[Tuple[str, str]]:
        """
        Try Balancing Suit Bid: 8+ actual HCP (vs 10+ direct), 5+ card suit.

        Priority: Majors > Minors (we want to find a fit for game potential)
        """
        # Minimum 8 actual HCP for suit bid
        if hand.hcp < 8:
            return None

        # Get opponent's suit for legality check
        opponent_suit = opening_bid[1] if len(opening_bid) >= 2 else None
        opponent_level = int(opening_bid[0]) if opening_bid[0].isdigit() else 1

        # Find our longest suit (prefer majors)
        best_suit = None
        best_length = 0

        # Check majors first
        for suit in ['♠', '♥']:
            length = hand.suit_lengths.get(suit, 0)
            if length >= 5 and length > best_length:
                best_suit = suit
                best_length = length

        # Then check minors
        if best_suit is None:
            for suit in ['♦', '♣']:
                length = hand.suit_lengths.get(suit, 0)
                if length >= 5 and length > best_length:
                    best_suit = suit
                    best_length = length

        if best_suit is None:
            return None

        # Determine bid level
        suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}
        opp_suit_rank = suit_rank.get(opponent_suit, 0)
        my_suit_rank = suit_rank.get(best_suit, 0)

        if my_suit_rank > opp_suit_rank:
            bid_level = opponent_level
        else:
            bid_level = opponent_level + 1

        # Check suit quality for 2-level bids (need better suit)
        if bid_level >= 2:
            suit_hcp = hand.suit_hcp.get(best_suit, 0)
            # Need at least 4 HCP in suit for 2-level balance (e.g., KQ, AJ)
            if suit_hcp < 4 and best_length < 6:
                return None

        bid = f"{bid_level}{best_suit}"
        suit_name = {'♠': 'spades', '♥': 'hearts', '♦': 'diamonds', '♣': 'clubs'}[best_suit]

        return (
            bid,
            f"Balancing {bid_level}-level bid in {suit_name} with {hand.hcp} HCP and "
            f"{best_length}-card suit (Borrowed King: need 8+ vs direct 10+)."
        )

    def _has_stopper(self, hand: Hand, suit: str) -> bool:
        """
        Check if hand has a stopper in the given suit.

        Full stoppers: A, Kx, Qxx, Jxxx
        Partial stoppers (OK for balancing): Kx, Qx, Jxx
        """
        suit_cards = [c for c in hand.cards if c.suit == suit]
        if not suit_cards:
            return False  # Void is not a stopper for NT

        ranks = [c.rank for c in suit_cards]
        length = len(ranks)

        # Full stoppers
        if 'A' in ranks:
            return True
        if 'K' in ranks and length >= 2:
            return True
        if 'Q' in ranks and length >= 3:
            return True
        if 'J' in ranks and length >= 4:
            return True

        # Partial stoppers (acceptable for balancing)
        if 'K' in ranks and length >= 1:  # Kx is partial
            return True
        if 'Q' in ranks and length >= 2:  # Qx is partial
            return True
        if 'J' in ranks and length >= 3:  # Jxx is partial
            return True

        return False

    def _has_trap_hand(self, hand: Hand, opponent_suit: str) -> bool:
        """
        Check if hand has "trap" values in opponent's suit.

        A trap pass is when we have strong holdings in opponent's suit
        (e.g., QJTx, KQJx) and expect to beat their contract.
        """
        suit_length = hand.suit_lengths.get(opponent_suit, 0)
        suit_hcp = hand.suit_hcp.get(opponent_suit, 0)

        # Trap: 4+ cards with 6+ HCP in opponent's suit (e.g., KQJx)
        if suit_length >= 4 and suit_hcp >= 6:
            return True

        # Also trap if we have 5+ cards with 4+ HCP (length strength)
        if suit_length >= 5 and suit_hcp >= 4:
            return True

        return False

    def _is_bid_legal(self, bid: str, last_bid: str) -> bool:
        """Check if bid is legally higher than last_bid."""
        suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4, 'NT': 5}

        try:
            my_level = int(bid[0])
            my_suit = bid[1:] if len(bid) > 1 else 'NT'
            last_level = int(last_bid[0])
            last_suit = last_bid[1:] if len(last_bid) > 1 else 'NT'

            if my_level > last_level:
                return True
            if my_level == last_level and suit_rank.get(my_suit, 0) > suit_rank.get(last_suit, 0):
                return True
        except (ValueError, IndexError):
            return False

        return False


# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("balancing", BalancingModule())
