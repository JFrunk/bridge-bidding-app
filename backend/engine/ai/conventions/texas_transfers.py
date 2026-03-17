from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.bidding_validation import BidValidator, get_next_legal_bid
from utils.seats import seat_index, seat_from_index
from typing import Optional, Tuple, Dict


class TexasTransferConvention(ConventionModule):
    """
    Texas Transfers (4-level transfers) over 1NT or 2NT.

    SAYC Standard:
    - 4♦ = transfer to 4♥ (shows 6+ hearts, game values 10+ HCP)
    - 4♥ = transfer to 4♠ (shows 6+ spades, game values 10+ HCP)

    Key Benefits:
    - Puts the strong hand (NT opener) as declarer
    - Disambiguates 4NT after transfer completion as strictly RKCB (not quantitative)

    Opener MUST complete the transfer (no super-accepts at 4-level).

    Post-Transfer:
    - Pass = to play in 4M
    - 4NT = RKCB (never quantitative after Texas Transfer)
    - New suit at 5-level = cue-bid (slam try)
    """

    def get_constraints(self) -> Dict:
        return {'suit_length_req': (['♥', '♠'], 6, 'any_of')}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Main evaluation with bid validation."""
        result = self._evaluate_texas(hand, features)
        if not result:
            return None

        bid = result[0]
        if bid == "Pass":
            return result

        auction_history = features.get('auction_history', [])
        if BidValidator.is_legal_bid(bid, auction_history):
            return result

        # Texas transfers are fixed bids — if illegal, something is wrong
        return None

    def _evaluate_texas(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Internal dispatch for Texas Transfer actions."""
        # Check for opener completing the transfer
        if self._is_completion_applicable(features):
            return self._get_completion_bid(features)
        # Check for responder initiating the transfer
        if self._is_initiation_applicable(hand, features):
            return self._get_transfer_bid(hand)
        return None

    def _is_initiation_applicable(self, hand: Hand, features: Dict) -> bool:
        """Check if responder should use Texas Transfer.

        Requirements:
        - Partner opened 1NT or 2NT
        - 6+ card major
        - Game values (10+ HCP over 1NT, 4+ HCP over 2NT)
        - No intervening bids (uncontested)
        - NOT slam-interested (15+ HCP uses Jacoby + Blackwood instead)
        """
        auction_features = features.get('auction_features', {})
        opening_bid = auction_features.get('opening_bid')

        if opening_bid not in ['1NT', '2NT']:
            return False
        if auction_features.get('opener_relationship') != 'Partner':
            return False

        # Must be first response (no prior bids except passes)
        non_pass_bids = [bid for bid in features.get('auction_history', []) if bid != 'Pass']
        if len(non_pass_bids) != 1:
            return False

        # Must have 6+ card major
        has_6_hearts = hand.suit_lengths['♥'] >= 6
        has_6_spades = hand.suit_lengths['♠'] >= 6
        if not has_6_hearts and not has_6_spades:
            return False

        # HCP requirements
        if opening_bid == '1NT':
            # Over 1NT: 10-14 HCP (game values, not slam)
            # With 15+, use Jacoby transfer + Blackwood for slam exploration
            if hand.hcp < 10 or hand.hcp >= 15:
                return False
        else:  # 2NT
            # Over 2NT: 4-9 HCP (combined ~24-30, game values)
            # With 10+, use Jacoby transfer + Blackwood
            if hand.hcp < 4 or hand.hcp >= 10:
                return False

        return True

    def _get_transfer_bid(self, hand: Hand) -> Optional[Tuple[str, str, dict]]:
        """Return the Texas Transfer bid."""
        metadata = {'bypass_suit_length': True, 'bypass_hcp': True,
                    'bypass_sanity_check': True, 'convention': 'texas_transfer'}

        # Prefer spades if both are 6+
        if hand.suit_lengths['♠'] >= 6:
            return ("4♥", f"Texas Transfer showing 6+ spades ({hand.hcp} HCP).", metadata)
        if hand.suit_lengths['♥'] >= 6:
            return ("4♦", f"Texas Transfer showing 6+ hearts ({hand.hcp} HCP).", metadata)
        return None

    def _is_completion_applicable(self, features: Dict) -> bool:
        """Check if opener should complete a Texas Transfer.

        Opener MUST complete (no choice) when partner bids 4♦ or 4♥ over 1NT/2NT.
        """
        auction_features = features.get('auction_features', {})
        partner_last_bid = auction_features.get('partner_last_bid')

        if auction_features.get('opener_relationship') != 'Me':
            return False
        if auction_features.get('opening_bid') not in ['1NT', '2NT']:
            return False
        if partner_last_bid not in ['4♦', '4♥']:
            return False

        # Verify this is indeed a Texas Transfer context (not a natural bid)
        # 4♦ and 4♥ directly over 1NT/2NT are always Texas
        auction_history = features.get('auction_history', [])
        my_index = features.get('my_index', -1)
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if features['positions'][i % 4] == features['positions'][my_index]
                   and auction_history[i] not in ['Pass', 'X', 'XX']]

        # Our last non-pass bid should be 1NT or 2NT
        if not my_bids or my_bids[-1] not in ['1NT', '2NT']:
            return False

        return True

    def _get_completion_bid(self, features: Dict) -> Tuple[str, str, dict]:
        """Complete the Texas Transfer."""
        partner_last_bid = features['auction_features']['partner_last_bid']
        metadata = {'bypass_suit_length': True, 'bypass_hcp': True,
                    'bypass_sanity_check': True, 'convention': 'texas_transfer_completion'}

        if partner_last_bid == '4♦':
            return ("4♥", "Completing Texas Transfer to hearts.", metadata)
        if partner_last_bid == '4♥':
            return ("4♠", "Completing Texas Transfer to spades.", metadata)
        return ("Pass", "Error: fall-through in Texas Transfer completion.", {})


# Utility function for other modules to check Texas Transfer context
def is_texas_transfer_sequence(auction_history: list, positions: list,
                                my_index: int) -> bool:
    """Check if the auction contains a completed Texas Transfer.

    Returns True if partner bid 4♦/4♥ over 1NT/2NT and we completed it,
    OR if we bid 4♦/4♥ over partner's 1NT/2NT and they completed it.
    """
    if len(auction_history) < 4:
        return False

    my_pos = positions[my_index]
    partner_pos = positions[seat_index(seat_from_index(my_index + 2))]

    my_bids = []
    partner_bids = []
    for i, bid in enumerate(auction_history):
        pos = positions[i % 4]
        if pos == my_pos:
            my_bids.append((i, bid))
        elif pos == partner_pos:
            partner_bids.append((i, bid))

    # Pattern 1: Partner opened NT, I transferred, partner completed
    # Partner: 1NT → I: 4♦/4♥ → Partner: 4♥/4♠
    for pi, pbid in partner_bids:
        if pbid in ['1NT', '2NT']:
            for mi, mbid in my_bids:
                if mi > pi and mbid in ['4♦', '4♥']:
                    for pi2, pbid2 in partner_bids:
                        if pi2 > mi:
                            if (mbid == '4♦' and pbid2 == '4♥') or \
                               (mbid == '4♥' and pbid2 == '4♠'):
                                return True

    # Pattern 2: I opened NT, partner transferred, I completed
    for mi, mbid in my_bids:
        if mbid in ['1NT', '2NT']:
            for pi, pbid in partner_bids:
                if pi > mi and pbid in ['4♦', '4♥']:
                    for mi2, mbid2 in my_bids:
                        if mi2 > pi:
                            if (pbid == '4♦' and mbid2 == '4♥') or \
                               (pbid == '4♥' and mbid2 == '4♠'):
                                return True

    return False


# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("texas_transfers", TexasTransferConvention())
