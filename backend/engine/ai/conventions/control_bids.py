from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.bidding_validation import BidValidator
from utils.seats import partner as partner_seat_fn, seat_from_index
from typing import Optional, Tuple, Dict


class ControlBidsConvention(ConventionModule):
    """
    Control Bidding (Cue-Bidding) for Slam Exploration.

    After a major suit is agreed at the 3-level in a game-forcing auction,
    control bids show first-round (Ace/void) or second-round (King/singleton)
    controls in side suits, ascending from the cheapest suit.

    The sequence:
    1. Agreed major at 3-level + GF values → initiate control bidding
    2. Bid cheapest side suit where you hold a control
    3. If no control to show → sign off in 4M
    4. If all suits controlled → Blackwood 4NT takes over
    """

    SUIT_ORDER = ['♣', '♦', '♥', '♠']
    SUIT_RANK = {'♣': 0, '♦': 1, '♥': 2, '♠': 3}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Return (bid, explanation) for a control bid, or None."""
        auction = features.get('auction_features', {})
        auction_history = features.get('auction_history', [])

        # Need agreed suit info
        agreed_info = auction.get('agreed_suit', {})
        if not agreed_info:
            return None

        agreed_suit = agreed_info.get('agreed_suit')
        fit_known = agreed_info.get('fit_known', False)

        # Only control-bid with agreed major
        if agreed_suit not in ['♥', '♠'] or not fit_known:
            return None

        # Need game-forcing values (14+ HCP or strong total points)
        if hand.hcp < 14:
            return None

        # Check current auction level — control bids happen at 3-4 level
        current_level = self._get_current_level(auction_history)
        if current_level < 3 or current_level > 4:
            return None

        # Don't initiate if partner already bid 4NT (Blackwood takes over)
        partner_last = auction.get('partner_last_bid', '')
        if partner_last == '4NT':
            return None

        # Don't control-bid if partner signed off in 4M
        if partner_last and partner_last[0] == '4' and len(partner_last) >= 2:
            if partner_last[1] == agreed_suit:
                # Partner signed off — only continue with very strong hand
                if hand.hcp < 17:
                    return None

        # Find controls in each side suit
        controls = {}
        for suit in self.SUIT_ORDER:
            if suit == agreed_suit:
                continue
            control_level = self._get_control_level(hand, suit)
            if control_level > 0:
                controls[suit] = control_level

        # Find the cheapest unbid control
        cheapest_control = self._find_cheapest_control(
            controls, agreed_suit, auction_history, features
        )

        if cheapest_control:
            suit, control_level = cheapest_control
            bid_level = self._calculate_bid_level(suit, agreed_suit, current_level)

            # Don't go past 4-level for control bids (except 4♥ when spades is trump)
            if bid_level > 4:
                return None
            if bid_level == 4 and self.SUIT_RANK[suit] > self.SUIT_RANK[agreed_suit]:
                return None  # Would bypass game level

            bid = f"{bid_level}{suit}"

            # Validate legality
            if not BidValidator.is_legal_bid(bid, auction_history):
                return None

            control_type = "Ace or void" if control_level == 1 else "King or singleton"
            suit_name = {'♣': 'clubs', '♦': 'diamonds', '♥': 'hearts', '♠': 'spades'}[suit]
            explanation = f"Control bid showing {control_type} in {suit_name}"

            # Return 3-tuple with metadata to bypass validation
            metadata = {
                'bypass_hcp': True,
                'bypass_suit_length': True,
                'convention': 'control_bid'
            }
            return (bid, explanation, metadata)

        # No control to show — check if we should sign off or if all controlled
        uncontrolled = self._find_uncontrolled_suits(controls, agreed_suit)
        if not uncontrolled:
            # All side suits controlled — don't sign off, let Blackwood handle
            return None

        # Sign off in 4M (no control to show in a needed suit)
        sign_off_bid = f"4{agreed_suit}"
        if BidValidator.is_legal_bid(sign_off_bid, auction_history):
            uncontrolled_names = [
                {'♣': 'clubs', '♦': 'diamonds', '♥': 'hearts', '♠': 'spades'}[s]
                for s in uncontrolled
            ]
            return (
                sign_off_bid,
                f"Signing off — no control in {', '.join(uncontrolled_names)}"
            )

        return None

    def _get_control_level(self, hand: Hand, suit: str) -> int:
        """
        Determine control level in a suit.
        Returns: 1 = first-round (Ace or void), 2 = second-round (King or singleton), 0 = none
        """
        suit_cards = [c for c in hand.cards if c.suit == suit]
        suit_length = len(suit_cards)

        # Void = first-round control
        if suit_length == 0:
            return 1

        # Ace = first-round control
        if any(c.rank == 'A' for c in suit_cards):
            return 1

        # Singleton = second-round control
        if suit_length == 1:
            return 2

        # King = second-round control
        if any(c.rank == 'K' for c in suit_cards):
            return 2

        return 0

    def _find_cheapest_control(
        self, controls: Dict, agreed_suit: str,
        auction_history: list, features: Dict
    ) -> Optional[Tuple[str, int]]:
        """Find the cheapest side-suit control not yet shown."""
        my_index = features.get('my_index', 0)
        positions = features.get('positions', [])

        # Collect suits already control-bid by our side
        already_shown = set()
        my_pos = positions[my_index] if my_index < len(positions) else None
        partner_pos = partner_seat_fn(my_pos) if my_pos else None
        for i, bid in enumerate(auction_history):
            if not positions:
                break
            bidder = positions[i % 4] if i < len(positions) * 4 else None

            if bidder in [my_pos, partner_pos] and len(bid) >= 2 and bid[0].isdigit():
                bid_suit = bid[1] if bid[1] in '♣♦♥♠' else None
                bid_level = int(bid[0])
                # A 4-level bid in a side suit (not the agreed suit) is likely a control bid
                if bid_suit and bid_suit != agreed_suit and bid_level >= 4:
                    already_shown.add(bid_suit)

        # Iterate through suits in order, find cheapest unshown control
        # First-round controls (Ace/void) have priority
        for control_priority in [1, 2]:
            for suit in self.SUIT_ORDER:
                if suit == agreed_suit:
                    continue
                if suit in already_shown:
                    continue
                if controls.get(suit) == control_priority:
                    return (suit, control_priority)

        return None

    def _calculate_bid_level(self, suit: str, agreed_suit: str, current_level: int) -> int:
        """Calculate the minimum level for a control bid in the given suit."""
        # Control bids go up from the current level
        # If the suit ranks below the agreed suit at the current level, bid at current level
        # If the suit ranks above, need to go to next level
        if self.SUIT_RANK[suit] > self.SUIT_RANK.get(agreed_suit, 4):
            # Suit is higher than trump — same level only if we haven't passed it
            return current_level
        else:
            # Suit is lower than trump — could be same or next level
            return current_level + 1

    def _find_uncontrolled_suits(self, controls: Dict, agreed_suit: str) -> list:
        """Find side suits with no control."""
        uncontrolled = []
        for suit in self.SUIT_ORDER:
            if suit == agreed_suit:
                continue
            if suit not in controls:
                uncontrolled.append(suit)
        return uncontrolled

    def _get_current_level(self, auction_history: list) -> int:
        """Get the current highest bid level in the auction."""
        current_level = 0
        for bid in auction_history:
            if bid and bid[0].isdigit():
                level = int(bid[0])
                if level > current_level:
                    current_level = level
        return current_level


# Auto-register on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("control_bids", ControlBidsConvention())
