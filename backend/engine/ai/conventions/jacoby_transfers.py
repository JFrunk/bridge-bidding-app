from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.bidding_validation import BidValidator, get_next_legal_bid
from typing import Optional, Tuple, Dict

class JacobyConvention(ConventionModule):
    """Complete playbook for the Jacoby Transfer convention."""

    def get_constraints(self) -> Dict:
        return {'suit_length_req': (['♥', '♠'], 5, 'any_of')}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Main evaluation function with bid validation."""
        auction_history = features.get('auction_history', [])

        # Get the raw jacoby bid
        result = self._evaluate_jacoby(hand, features)

        if not result:
            return None

        bid, explanation = result

        # Always pass Pass bids through
        if bid == "Pass":
            return result

        # Validate the bid is legal
        if BidValidator.is_legal_bid(bid, auction_history):
            return result

        # Bid is illegal - try to find next legal bid of same strain
        next_legal = get_next_legal_bid(bid, auction_history)
        if next_legal:
            # SANITY CHECK: If adjustment is more than 2 levels, something is wrong
            # Prevents transfer sequences from escalating to unreasonable levels
            try:
                original_level = int(bid[0])
                adjusted_level = int(next_legal[0])

                if adjusted_level - original_level > 2:
                    # The suggested bid is way off - pass instead of making unreasonable bid
                    return ("Pass", f"Cannot make reasonable bid at current auction level (suggested {bid}, would need {next_legal}).")
            except (ValueError, IndexError):
                # Not a level bid (e.g., Pass, X, XX) - allow adjustment
                pass

            adjusted_explanation = f"{explanation} [Adjusted from {bid} to {next_legal} for legality]"
            return (next_legal, adjusted_explanation)

        # No legal bid possible - pass
        return None

    def _evaluate_jacoby(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Internal method that calculates jacoby bid without validation."""
        # Check for responder's continuation after transfer completion
        if self._is_responder_continuation_applicable(features):
            return self._get_responder_continuation(hand, features)
        # Check for opener completing the transfer
        if self._is_completion_applicable(features):
            return self._get_completion_bid(hand, features)
        # Check for responder initiating the transfer
        if self._is_initiation_applicable(hand, features):
            return self._get_transfer_bid(hand)
        return None

    def _is_completion_applicable(self, features: Dict) -> bool:
        auction_features = features.get('auction_features', {})
        partner_last_bid = auction_features.get('partner_last_bid')
        return (auction_features.get('opener_relationship') == 'Me' and
                auction_features.get('opening_bid') == '1NT' and
                partner_last_bid in ['2♦', '2♥'])

    def _get_completion_bid(self, hand: Hand, features: Dict) -> Tuple[str, str]:
        partner_last_bid = features['auction_features']['partner_last_bid']
        if partner_last_bid == "2♦":
            # Super-accept with maximum (17 HCP) and 4-card support
            if hand.hcp == 17 and hand.suit_lengths['♥'] >= 4:
                return ("3♥", "Super-accept showing maximum 1NT (17 HCP) with 4-card heart support.")
            return ("2♥", "Completing the transfer to Hearts.")
        if partner_last_bid == "2♥":
            # Super-accept with maximum (17 HCP) and 4-card support
            if hand.hcp == 17 and hand.suit_lengths['♠'] >= 4:
                return ("3♠", "Super-accept showing maximum 1NT (17 HCP) with 4-card spade support.")
            return ("2♠", "Completing the transfer to Spades.")
        return ("Pass", "Error: Fall-through in transfer completion.")

    def _is_initiation_applicable(self, hand: Hand, features: Dict) -> bool:
        auction_features = features.get('auction_features', {})
        non_pass_bids = [bid for bid in features.get('auction_history', []) if bid != 'Pass']
        return (auction_features.get('opening_bid') == '1NT' and
                auction_features.get('opener_relationship') == 'Partner' and
                len(non_pass_bids) == 1 and
                (hand.suit_lengths['♥'] >= 5 or hand.suit_lengths['♠'] >= 5))
    
    def _get_transfer_bid(self, hand: Hand) -> Optional[Tuple[str, str]]:
        if hand.suit_lengths['♥'] >= 5:
            return ("2♦", "Jacoby Transfer showing 5+ Hearts.")
        if hand.suit_lengths['♠'] >= 5:
            return ("2♥", "Jacoby Transfer showing 5+ Spades.")
        return None

    def _is_responder_continuation_applicable(self, features: Dict) -> bool:
        """Check if responder should continue after opener completes transfer."""
        auction_features = features.get('auction_features', {})
        auction_history = features.get('auction_history', [])

        # Must be responder (partner opened 1NT)
        if auction_features.get('opener_relationship') != 'Partner':
            return False
        if auction_features.get('opening_bid') != '1NT':
            return False

        # Check if we initiated Jacoby and partner has completed
        # Auction should be: 1NT - 2♦ - 2♥ or 1NT - 2♥ - 2♠ (or super-accepts)
        if len(auction_history) < 3:
            return False

        my_index = features.get('my_index', -1)
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if features['positions'][i % 4] == features['positions'][my_index]]

        # Check if we transferred (bid 2♦ or 2♥ after 1NT)
        if len(my_bids) < 1:
            return False
        if my_bids[0] not in ['2♦', '2♥']:
            return False

        # Partner must have completed (or super-accepted)
        partner_last_bid = auction_features.get('partner_last_bid', '')
        if my_bids[0] == '2♦':
            # Expect 2♥ or 3♥ (super-accept)
            return partner_last_bid in ['2♥', '3♥']
        if my_bids[0] == '2♥':
            # Expect 2♠ or 3♠ (super-accept)
            return partner_last_bid in ['2♠', '3♠']

        return False

    def _get_responder_continuation(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Responder's action after opener completes the transfer."""
        auction_history = features.get('auction_history', [])
        partner_last_bid = features['auction_features'].get('partner_last_bid', '')

        # Determine which major we transferred to
        my_index = features.get('my_index', -1)
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if features['positions'][i % 4] == features['positions'][my_index]]

        my_transfer_bid = my_bids[0]
        if my_transfer_bid == '2♦':
            my_suit = '♥'
        elif my_transfer_bid == '2♥':
            my_suit = '♠'
        else:
            return None

        # Partner super-accepted (3♥ or 3♠)
        super_accepted = partner_last_bid[0] == '3'

        # Decide continuation based on strength and suit length
        if hand.hcp <= 7:
            # Weak hand (0-7 HCP): Pass
            return ("Pass", f"Weak hand ({hand.hcp} HCP), passing after transfer completion.")

        elif 8 <= hand.hcp <= 9:
            # Invitational (8-9 HCP)
            if super_accepted:
                # Partner showed maximum with fit, bid game
                return (f"4{my_suit}", f"Accepting super-accept with {hand.hcp} HCP.")
            else:
                # Invite game
                if hand.suit_lengths[my_suit] == 5:
                    return ("2NT", f"Invitational ({hand.hcp} HCP) with 5-card {my_suit}.")
                else:
                    return (f"3{my_suit}", f"Invitational ({hand.hcp} HCP) with 6+ card {my_suit}.")

        else:  # 10+ HCP
            # Game-forcing values
            if hand.suit_lengths[my_suit] == 5:
                # With 5-card suit, might prefer 3NT
                return ("3NT", f"Game-forcing ({hand.hcp} HCP) with 5-card {my_suit}, bidding 3NT.")
            elif hand.suit_lengths[my_suit] == 6:
                # With 6-card suit, bid game in the major
                return (f"4{my_suit}", f"Game-forcing ({hand.hcp} HCP) with 6-card {my_suit}.")
            else:
                # With 7+ cards, always bid game in the major
                return (f"4{my_suit}", f"Game-forcing ({hand.hcp} HCP) with {hand.suit_lengths[my_suit]}-card {my_suit}.")

# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("jacoby", JacobyConvention())
