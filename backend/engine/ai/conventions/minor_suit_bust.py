from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict


class MinorSuitBustConvention(ConventionModule):
    """
    Minor Suit Bust (2♠ relay) over 1NT.

    SAYC Standard:
    - 2♠ over 1NT forces opener to bid 3♣
    - Responder then:
      * Passes with a club bust (weak hand, 6+ clubs)
      * Bids 3♦ with a diamond bust (weak hand, 6+ diamonds) - opener passes

    This convention is for very weak hands (0-7 HCP) with a long minor
    that don't want to play 1NT.
    """

    def get_constraints(self) -> Dict:
        """Defines requirements for minor suit bust."""
        return {'hcp_range': (0, 7)}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Main evaluation for Minor Suit Bust convention."""
        # Check for opener's forced 3♣ response
        if self._is_opener_response_applicable(features):
            return self._get_opener_response(hand, features)

        # Check for responder's correction to 3♦
        if self._is_responder_correction_applicable(features):
            return self._get_responder_correction(hand, features)

        # Check for initiating 2♠ bust
        if self._should_bid_minor_bust(hand, features):
            return self._initiate_minor_bust(hand, features)

        return None

    def _should_bid_minor_bust(self, hand: Hand, features: Dict) -> bool:
        """
        Check if responder should bid 2♠ minor suit bust.

        Requirements:
        - Partner opened 1NT
        - Weak hand (0-7 HCP)
        - 6+ card minor suit (clubs or diamonds)
        - No 4-card major (would use Stayman instead)
        - No 5-card major (would use Jacoby instead)
        """
        auction_features = features.get('auction_features', {})

        # Partner must have opened 1NT
        if auction_features.get('opening_bid') != '1NT':
            return False
        if auction_features.get('opener_relationship') != 'Partner':
            return False

        # Must be our first bid
        non_pass_bids = [bid for bid in features.get('auction_history', []) if bid != 'Pass']
        if len(non_pass_bids) != 1:  # Only partner's 1NT
            return False

        # Weak hand (0-7 HCP)
        if hand.hcp > 7:
            return False

        # Need 6+ card minor
        has_long_club = hand.suit_lengths['♣'] >= 6
        has_long_diamond = hand.suit_lengths['♦'] >= 6
        if not (has_long_club or has_long_diamond):
            return False

        # No 4+ card major (would use Stayman or Jacoby)
        if hand.suit_lengths['♥'] >= 4 or hand.suit_lengths['♠'] >= 4:
            return False

        return True

    def _initiate_minor_bust(self, hand: Hand, features: Dict) -> Tuple[str, str, dict]:
        """Bid 2♠ to force opener to 3♣."""
        metadata = {'bypass_suit_length': True}  # 2♠ is artificial, not showing spades

        if hand.suit_lengths['♣'] >= 6:
            return ("2♠", f"Minor suit bust relay. Will pass 3♣ with weak hand ({hand.hcp} HCP) and 6+ clubs.", metadata)
        else:
            return ("2♠", f"Minor suit bust relay. Will correct to 3♦ with weak hand ({hand.hcp} HCP) and 6+ diamonds.", metadata)

    def _is_opener_response_applicable(self, features: Dict) -> bool:
        """
        Check if opener should respond 3♣ to responder's 2♠ bust relay.
        """
        auction_features = features.get('auction_features', {})

        # I must be the 1NT opener
        if auction_features.get('opening_bid') != '1NT':
            return False
        if auction_features.get('opener_relationship') != 'Me':
            return False

        # Partner must have bid 2♠
        partner_last_bid = auction_features.get('partner_last_bid', '')
        return partner_last_bid == '2♠'

    def _get_opener_response(self, hand: Hand, features: Dict) -> Tuple[str, str, dict]:
        """
        Opener's forced response to 2♠ minor bust relay.
        Always bid 3♣ (forced).
        """
        metadata = {'bypass_suit_length': True}
        return ("3♣", "Forced response to 2♠ minor suit bust relay.", metadata)

    def _is_responder_correction_applicable(self, features: Dict) -> bool:
        """
        Check if responder should correct 3♣ to 3♦.
        """
        auction_features = features.get('auction_features', {})

        # Partner opened 1NT
        if auction_features.get('opening_bid') != '1NT':
            return False
        if auction_features.get('opener_relationship') != 'Partner':
            return False

        # I must have bid 2♠ earlier
        auction_history = features.get('auction_history', [])
        my_index = features.get('my_index', -1)
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if features['positions'][i % 4] == features['positions'][my_index]]

        if '2♠' not in my_bids:
            return False

        # Partner must have bid 3♣
        partner_last_bid = auction_features.get('partner_last_bid', '')
        return partner_last_bid == '3♣'

    def _get_responder_correction(self, hand: Hand, features: Dict) -> Tuple[str, str]:
        """
        Responder's follow-up after opener bids 3♣.
        - Pass with 6+ clubs
        - Bid 3♦ with 6+ diamonds
        """
        if hand.suit_lengths['♣'] >= 6:
            return ("Pass", f"Signing off in 3♣ with weak hand ({hand.hcp} HCP) and {hand.suit_lengths['♣']}-card club suit.")
        else:
            return ("3♦", f"Correcting to 3♦ with weak hand ({hand.hcp} HCP) and {hand.suit_lengths['♦']}-card diamond suit.")


# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("minor_suit_bust", MinorSuitBustConvention())
