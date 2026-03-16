from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.bidding_validation import BidValidator
from typing import Optional, Tuple, Dict


class SmolenConvention(ConventionModule):
    """
    Smolen Convention — 5-4 major suit inversion after Stayman denial.

    After 1NT → 2♣ → 2♦ (denial), responder with 5-4 in majors and game
    values (10+ HCP) jumps to 3-level in their 4-CARD major:
      - 3♥ = 4 hearts, 5 spades (inverted — shows shorter suit)
      - 3♠ = 4 spades, 5 hearts (inverted — shows shorter suit)

    Purpose: Keeps the strong NT hand (opener) as declarer when a 5-3
    major fit is found.

    Opener's response:
      - 4M (partner's 5-card suit) with 3+ card support
      - 3NT without 3-card support for partner's long major
      - 4NT (RKCB) with fit and slam interest (17 HCP max end)
    """

    def get_constraints(self) -> Dict:
        return {'suit_length_req': (['♥', '♠'], 4, 'any_of')}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Main evaluation with bid validation."""
        # Check opener responding to Smolen jump
        if self._is_opener_response_applicable(features):
            return self._get_opener_response(hand, features)
        # Check responder making Smolen jump
        if self._is_smolen_applicable(hand, features):
            return self._get_smolen_bid(hand, features)
        return None

    def _is_smolen_applicable(self, hand: Hand, features: Dict) -> bool:
        """Check if responder should make a Smolen jump.

        Requirements:
        - Partner opened 1NT
        - We bid Stayman (2♣)
        - Partner denied 4-card major (2♦)
        - We have exactly 5-4 in majors (5 in one, 4 in the other)
        - 10+ HCP (game values)
        """
        auction_features = features.get('auction_features', {})
        opening_bid = auction_features.get('opening_bid')
        partner_last_bid = auction_features.get('partner_last_bid')

        if opening_bid != '1NT':
            return False
        if auction_features.get('opener_relationship') != 'Partner':
            return False
        if partner_last_bid != '2♦':
            return False

        # Verify we bid Stayman
        my_index = features.get('my_index', -1)
        positions = features.get('positions', [])
        auction_history = features.get('auction_history', [])
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if positions[i % 4] == positions[my_index]
                   and auction_history[i] not in ['Pass', 'X', 'XX']]

        if not my_bids or my_bids[0] != '2♣':
            return False

        # Must have exactly 5-4 in majors
        h_len = hand.suit_lengths['♥']
        s_len = hand.suit_lengths['♠']
        has_5_4 = (h_len == 5 and s_len == 4) or (h_len == 4 and s_len == 5)
        if not has_5_4:
            return False

        # Game values required (10+ HCP opposite 15-17)
        if hand.hcp < 10:
            return False

        return True

    def _get_smolen_bid(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str, dict]]:
        """Return the Smolen jump bid.

        INVERSION: Bid the 4-card major, showing 5 in the OTHER major.
        - 3♥ = 4 hearts, 5 spades
        - 3♠ = 4 spades, 5 hearts
        """
        metadata = {'bypass_suit_length': True, 'bypass_hcp': True,
                    'bypass_sanity_check': True, 'convention': 'smolen'}

        auction_history = features.get('auction_history', [])

        if hand.suit_lengths['♥'] == 4 and hand.suit_lengths['♠'] >= 5:
            bid = '3♥'
            explanation = (f"Smolen: shows 4 hearts and 5 spades ({hand.hcp} HCP). "
                          f"Inverted jump to keep opener as declarer.")
        elif hand.suit_lengths['♠'] == 4 and hand.suit_lengths['♥'] >= 5:
            bid = '3♠'
            explanation = (f"Smolen: shows 4 spades and 5 hearts ({hand.hcp} HCP). "
                          f"Inverted jump to keep opener as declarer.")
        else:
            return None

        if BidValidator.is_legal_bid(bid, auction_history):
            return (bid, explanation, metadata)
        return None

    def _is_opener_response_applicable(self, features: Dict) -> bool:
        """Check if opener should respond to partner's Smolen jump.

        Opener position: I opened 1NT, partner bid 2♣, I bid 2♦, partner
        jumped to 3♥ or 3♠ (Smolen).
        """
        auction_features = features.get('auction_features', {})
        partner_last_bid = auction_features.get('partner_last_bid')

        if auction_features.get('opener_relationship') != 'Me':
            return False
        if auction_features.get('opening_bid') != '1NT':
            return False
        if partner_last_bid not in ['3♥', '3♠']:
            return False

        # Verify Stayman sequence: I bid 1NT, then 2♦ (denial)
        my_index = features.get('my_index', -1)
        positions = features.get('positions', [])
        auction_history = features.get('auction_history', [])
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if positions[i % 4] == positions[my_index]
                   and auction_history[i] not in ['Pass', 'X', 'XX']]

        if len(my_bids) < 2:
            return False
        if my_bids[0] != '1NT' or my_bids[1] != '2♦':
            return False

        return True

    def _get_opener_response(self, hand: Hand, features: Dict) -> Tuple[str, str, dict]:
        """Opener responds to partner's Smolen jump.

        Partner's Smolen bid shows their 4-card major; their 5-card major
        is the OTHER suit.
        - Partner bid 3♥ → 5 spades, 4 hearts → check for 3+ spades
        - Partner bid 3♠ → 5 hearts, 4 spades → check for 3+ hearts
        """
        partner_last_bid = features['auction_features']['partner_last_bid']
        metadata = {'bypass_suit_length': True, 'bypass_hcp': True,
                    'bypass_sanity_check': True, 'convention': 'smolen_response'}

        if partner_last_bid == '3♥':
            # Partner has 5 spades, 4 hearts
            if hand.suit_lengths['♠'] >= 3:
                return ("4♠", f"Accepting Smolen: 3+ spade support for partner's 5-card suit.", metadata)
            else:
                return ("3NT", f"Declining Smolen: only {hand.suit_lengths['♠']} spades, no 5-3 fit.", metadata)
        elif partner_last_bid == '3♠':
            # Partner has 5 hearts, 4 spades
            if hand.suit_lengths['♥'] >= 3:
                return ("4♥", f"Accepting Smolen: 3+ heart support for partner's 5-card suit.", metadata)
            else:
                return ("3NT", f"Declining Smolen: only {hand.suit_lengths['♥']} hearts, no 5-3 fit.", metadata)

        return ("3NT", "Smolen response fallthrough.", metadata)


# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("smolen", SmolenConvention())
