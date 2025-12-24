from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.bidding_validation import BidValidator, get_next_legal_bid
from typing import Optional, Tuple, Dict


class GerberConvention(ConventionModule):
    """
    Gerber Convention (4♣) - Ace-asking over NT bids.

    SAYC Standard:
    - 4♣ IS GERBER OVER ANY 1NT OR 2NT BY PARTNER, INCLUDING A REBID OF 1NT OR 2NT
    - Used instead of Blackwood when clubs might be trump or after NT opening/rebid
    - Responses show aces by steps:
      * 4♦ = 0 or 4 aces
      * 4♥ = 1 ace
      * 4♠ = 2 aces
      * 4NT = 3 aces
    - 5♣ asks for kings (same step responses at 5-level)
    - Any bid other than 5♣ after ace response is to play (including 4NT)
    """

    def get_constraints(self) -> Dict:
        """Defines requirements for a hand that might use Gerber."""
        return {'hcp_range': (15, 40)}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Main evaluation function with bid validation."""
        auction_history = features.get('auction_history', [])

        # Get the raw Gerber bid
        result = self._evaluate_gerber(hand, features)

        if not result:
            return None

        bid, explanation = result[:2]
        metadata = result[2] if len(result) > 2 else {}

        # Always pass Pass bids through
        if bid == "Pass":
            return result

        # Validate the bid is legal
        if BidValidator.is_legal_bid(bid, auction_history):
            return result

        # Bid is illegal - try to find next legal bid
        next_legal = get_next_legal_bid(bid, auction_history)
        if next_legal:
            try:
                original_level = int(bid[0])
                adjusted_level = int(next_legal[0])
                if adjusted_level - original_level > 2:
                    return ("Pass", f"Cannot make reasonable Gerber bid (suggested {bid}, would need {next_legal}).")
            except (ValueError, IndexError):
                pass
            adjusted_explanation = f"{explanation} [Adjusted from {bid} to {next_legal} for legality]"
            if metadata:
                return (next_legal, adjusted_explanation, metadata)
            return (next_legal, adjusted_explanation)

        return None

    def _evaluate_gerber(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Internal method that calculates Gerber bid."""
        # Check for signoff after receiving ace response
        if self._is_signoff_applicable(features):
            return self._get_signoff_bid(hand, features)
        # Check for answering Gerber (4♣)
        if self._is_ace_answering_applicable(features):
            return self._get_ace_answer_bid(hand)
        # Check for king-asking (5♣)
        if self._is_king_asking_applicable(hand, features):
            return self._get_king_ask_bid()
        # Check for answering king ask
        if self._is_king_answering_applicable(features):
            return self._get_king_answer_bid(hand)
        # Check for asking aces (4♣)
        if self._is_gerber_applicable(hand, features):
            return self._get_gerber_bid()
        return None

    def _is_gerber_applicable(self, hand: Hand, features: Dict) -> bool:
        """
        Determines if 4♣ Gerber should be used.

        SAYC Rule: 4♣ IS GERBER OVER ANY 1NT OR 2NT BY PARTNER,
        INCLUDING A REBID OF 1NT OR 2NT.
        """
        partner_last_bid = features['auction_features'].get('partner_last_bid')
        if not partner_last_bid:
            return False

        # Gerber is used when partner's last bid was NT
        if partner_last_bid not in ['1NT', '2NT', '3NT']:
            return False

        # Need slam-going values (typically 15+ HCP when partner opens NT)
        # With 1NT (15-17) + 15 = 30+, slam is possible
        # With 2NT (20-21) + 12 = 32+, slam is possible
        if partner_last_bid == '1NT' and hand.hcp < 15:
            return False
        if partner_last_bid == '2NT' and hand.hcp < 12:
            return False
        if partner_last_bid == '3NT' and hand.hcp < 12:
            return False

        # Check we haven't already asked Gerber
        auction_history = features.get('auction_history', [])
        my_index = features.get('my_index', -1)
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if features['positions'][i % 4] == features['positions'][my_index]]
        if '4♣' in my_bids:
            return False

        return True

    def _get_gerber_bid(self) -> Tuple[str, str, dict]:
        """Returns the 4♣ Gerber ace-asking bid."""
        metadata = {'bypass_suit_length': True}
        return ("4♣", "Gerber convention, asking for aces over NT.", metadata)

    def _is_ace_answering_applicable(self, features: Dict) -> bool:
        """
        Determines if we are responding to 4♣ Gerber.

        4♣ is Gerber (not natural) if our last bid was NT.
        """
        partner_last_bid = features['auction_features'].get('partner_last_bid')
        if partner_last_bid != '4♣':
            return False

        # Check if our last bid was NT (which would make partner's 4♣ Gerber)
        auction_history = features.get('auction_history', [])
        my_index = features.get('my_index', 0)

        my_bids = [
            bid for i, bid in enumerate(auction_history)
            if (i % 4) == my_index and bid not in ['Pass', 'X', 'XX']
        ]

        # If our last bid was NT, partner's 4♣ is Gerber
        if my_bids and my_bids[-1] in ['1NT', '2NT', '3NT']:
            return True

        return False

    def _get_ace_answer_bid(self, hand: Hand) -> Tuple[str, str, dict]:
        """
        Counts aces and returns Gerber response.

        Responses:
        - 4♦ = 0 or 4 aces
        - 4♥ = 1 ace
        - 4♠ = 2 aces
        - 4NT = 3 aces
        """
        num_aces = sum(1 for card in hand.cards if card.rank == 'A')
        metadata = {'bypass_suit_length': True}

        if num_aces == 0 or num_aces == 4:
            return ("4♦", "Gerber response: 0 or 4 aces.", metadata)
        if num_aces == 1:
            return ("4♥", "Gerber response: 1 ace.", metadata)
        if num_aces == 2:
            return ("4♠", "Gerber response: 2 aces.", metadata)
        if num_aces == 3:
            return ("4NT", "Gerber response: 3 aces.", metadata)

        return ("Pass", "Error: Could not count aces.", {})

    def _is_signoff_applicable(self, features: Dict) -> bool:
        """Check if we asked Gerber and partner responded."""
        auction_history = features.get('auction_history', [])
        my_index = features.get('my_index', -1)

        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if features['positions'][i % 4] == features['positions'][my_index]]

        # Did we ask Gerber?
        if '4♣' not in my_bids:
            return False

        # Did partner respond with ace count?
        partner_last_bid = features['auction_features'].get('partner_last_bid', '')
        return partner_last_bid in ['4♦', '4♥', '4♠', '4NT']

    def _get_signoff_bid(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Signoff after receiving ace response to Gerber."""
        partner_last_bid = features['auction_features'].get('partner_last_bid', '')

        # Decode partner's ace count
        ace_responses = {'4♦': [0, 4], '4♥': [1], '4♠': [2], '4NT': [3]}
        partner_aces = ace_responses.get(partner_last_bid, [0])

        my_aces = sum(1 for card in hand.cards if card.rank == 'A')

        # Determine total aces
        if len(partner_aces) > 1:
            # Partner has 0 or 4 - assume 0 for safety unless we have 0
            if my_aces == 4:
                total_aces = 4  # Partner must have 0
            elif my_aces == 0:
                total_aces = 4  # Partner must have 4
            else:
                total_aces = my_aces  # Assume partner has 0
        else:
            total_aces = my_aces + partner_aces[0]

        # Decide slam level based on aces
        if total_aces <= 2:
            # Missing 2+ aces, sign off at 4NT or 5NT
            return ("4NT", f"Signing off, only {total_aces} aces between us.")
        elif total_aces == 3:
            # Missing 1 ace, bid small slam
            return ("6NT", f"Bidding small slam with {total_aces} aces.")
        else:
            # All 4 aces - consider grand slam
            return ("6NT", f"Bidding slam with all 4 aces (consider 7NT with kings).")

    def _is_king_asking_applicable(self, hand: Hand, features: Dict) -> bool:
        """Check if we should ask for kings (5♣) after receiving all aces."""
        auction_history = features.get('auction_history', [])
        my_index = features.get('my_index', -1)
        partner_last_bid = features['auction_features'].get('partner_last_bid', '')

        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if features['positions'][i % 4] == features['positions'][my_index]]

        # Must have asked Gerber
        if '4♣' not in my_bids:
            return False

        # Partner must have responded with ace count
        if partner_last_bid not in ['4♦', '4♥', '4♠', '4NT']:
            return False

        # Decode partner's aces
        ace_responses = {'4♦': [0, 4], '4♥': [1], '4♠': [2], '4NT': [3]}
        partner_aces = ace_responses.get(partner_last_bid, [0])
        my_aces = sum(1 for card in hand.cards if card.rank == 'A')

        # Only ask for kings if we have all 4 aces
        if len(partner_aces) > 1:
            # 0 or 4 - check if combined could be 4
            if my_aces == 0 or my_aces == 4:
                return True
        elif my_aces + partner_aces[0] == 4:
            return True

        return False

    def _get_king_ask_bid(self) -> Tuple[str, str, dict]:
        """Returns the 5♣ king-asking bid."""
        metadata = {'bypass_suit_length': True}
        return ("5♣", "Gerber 5♣, asking for kings (all aces present).", metadata)

    def _is_king_answering_applicable(self, features: Dict) -> bool:
        """Determines if we are responding to 5♣ king ask."""
        partner_last_bid = features['auction_features'].get('partner_last_bid')
        if partner_last_bid != '5♣':
            return False

        # Check if this is a Gerber king-ask context
        # (we responded to 4♣ Gerber earlier)
        auction_history = features.get('auction_history', [])
        my_index = features.get('my_index', 0)

        my_bids = [
            bid for i, bid in enumerate(auction_history)
            if (i % 4) == my_index and bid not in ['Pass', 'X', 'XX']
        ]

        # If we responded to Gerber (4♦/4♥/4♠/4NT), this 5♣ is king-ask
        gerber_responses = ['4♦', '4♥', '4♠', '4NT']
        return any(bid in gerber_responses for bid in my_bids)

    def _get_king_answer_bid(self, hand: Hand) -> Tuple[str, str, dict]:
        """
        Counts kings and returns Gerber king response.

        Responses:
        - 5♦ = 0 or 4 kings
        - 5♥ = 1 king
        - 5♠ = 2 kings
        - 5NT = 3 kings
        """
        num_kings = sum(1 for card in hand.cards if card.rank == 'K')
        metadata = {'bypass_suit_length': True}

        if num_kings == 0 or num_kings == 4:
            return ("5♦", "Gerber response: 0 or 4 kings.", metadata)
        if num_kings == 1:
            return ("5♥", "Gerber response: 1 king.", metadata)
        if num_kings == 2:
            return ("5♠", "Gerber response: 2 kings.", metadata)
        if num_kings == 3:
            return ("5NT", "Gerber response: 3 kings.", metadata)

        return ("Pass", "Error: Could not count kings.", {})


# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("gerber", GerberConvention())
