from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.bidding_validation import BidValidator, get_next_legal_bid
from typing import Optional, Tuple, Dict

class BlackwoodConvention(ConventionModule):
    """
    Playbook for Blackwood, including 4NT (aces) and 5NT (kings).
    """
    def get_constraints(self) -> Dict:
        """Defines requirements for a hand that might ask for aces."""
        return {'hcp_range': (18, 40)}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Main evaluation function with bid validation."""
        auction_history = features.get('auction_history', [])

        # Get the raw blackwood bid
        result = self._evaluate_blackwood(hand, features)

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
            # This is especially critical for Blackwood where 5NT→7NT could happen
            try:
                original_level = int(bid[0])
                adjusted_level = int(next_legal[0])

                if adjusted_level - original_level > 2:
                    # The suggested bid is way off - pass instead of bidding unreasonable slam
                    return ("Pass", f"Cannot make reasonable bid at current auction level (suggested {bid}, would need {next_legal}).")
            except (ValueError, IndexError):
                # Not a level bid (e.g., Pass, X, XX) - allow adjustment
                pass

            adjusted_explanation = f"{explanation} [Adjusted from {bid} to {next_legal} for legality]"
            return (next_legal, adjusted_explanation)

        # No legal bid possible - pass
        return None

    def _evaluate_blackwood(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Internal method that calculates blackwood bid without validation."""
        # Check for signoff after receiving ace response
        if self._is_signoff_applicable(features):
            return self._get_signoff_bid(hand, features)
        # Check for answering Blackwood
        if self._is_ace_answering_applicable(features):
            return self._get_ace_answer_bid(hand)
        # Check for king-asking (5NT)
        if self._is_king_asking_applicable(hand, features):
            return self._get_king_ask_bid()
        # Check for answering king ask
        if self._is_king_answering_applicable(features):
            return self._get_king_answer_bid(hand)
        # Check for asking aces
        if self._is_ace_asking_applicable(hand, features):
            return self._get_ace_ask_bid()
        return None

    def _is_ace_asking_applicable(self, hand: Hand, features: Dict) -> bool:
        """Determines if this hand should ask for aces."""
        partner_last_bid = features['auction_features'].get('partner_last_bid')
        if not partner_last_bid: return False

        auction_history = features.get('auction_history', [])
        my_position = features['positions'][features['my_index']]

        # Get my previous bids to understand auction context
        my_previous_bids = [bid for i, bid in enumerate(auction_history)
                           if features['positions'][i % 4] == my_position
                           and bid not in ['Pass', 'X', 'XX']]

        # Don't trigger Blackwood after 2NT rebid + partner's 3-level preference
        # Example: 1♥-1♠-2NT-3♥ is just preference, not a slam try
        if '2NT' in my_previous_bids and partner_last_bid[0] == '3':
            return False

        # Don't trigger after 1NT rebid + partner's invitational bid
        # Example: 1♥-1♠-1NT-2♦ is invitational, not slam interest
        if '1NT' in my_previous_bids and partner_last_bid[0] in ['2', '3']:
            return False

        # Strong direct jump raises (e.g., 1♥ - 4♥) indicate slam interest
        # This is a jump to 4-level showing strong support
        if len(my_previous_bids) == 1 and partner_last_bid[0] == '4' and len(partner_last_bid) == 2:
            # Partner jumped to 4-level (e.g., 1♥ - 4♥)
            if hand.total_points >= 18:
                return True

        # After game-forcing sequence, 3-level bid might show slam interest
        # But we need to be conservative - only if combined strength is very high
        partner_total_points = features['auction_features'].get('partner_total_points', 0)
        if hand.total_points + partner_total_points >= 30:
            # Clear slam zone - but still only if partner raised our suit
            is_raise = len(my_previous_bids) >= 1 and partner_last_bid.endswith(my_previous_bids[0][1:])
            if is_raise and partner_last_bid[0] in ['3', '4']:
                return True

        return False

    def _get_ace_ask_bid(self) -> Tuple[str, str]:
        """Returns the 4NT ace-asking bid."""
        return ("4NT", "Blackwood convention, asking for aces.")

    def _is_ace_answering_applicable(self, features: Dict) -> bool:
        """
        Determines if we are responding to a 4NT Blackwood bid.

        4NT is Blackwood (not quantitative) if:
        1. There's a clear suit agreement (opener showed a suit), OR
        2. The auction suggests slam interest (strong hand shown)

        4NT is quantitative (NOT Blackwood) if:
        - Partner opened NT and later bid 4NT with no suit shown
        - No clear suit agreement anywhere in the auction
        """
        partner_last_bid = features['auction_features'].get('partner_last_bid')
        if partner_last_bid != '4NT':
            return False

        auction_history = features.get('auction_history', [])
        if not auction_history:
            return False

        # Find partner's bids in the auction
        my_index = features.get('my_index', 0)
        partner_index = (my_index + 2) % 4

        partner_bids = [
            bid for i, bid in enumerate(auction_history)
            if (i % 4) == partner_index and bid not in ['Pass', 'X', 'XX']
        ]

        # Check if partner actually opened the bidding (was the first non-Pass bid)
        # Find the first non-Pass bid in the auction
        first_bid_index = next((i for i, bid in enumerate(auction_history) if bid != 'Pass'), None)
        partner_actually_opened = first_bid_index is not None and (first_bid_index % 4) == partner_index

        # If partner OPENED with NT, then 4NT is quantitative
        # Pattern: 1NT - ... - 4NT → quantitative (inviting 6NT)
        if partner_actually_opened and partner_bids and partner_bids[0] in ['1NT', '2NT', '3NT']:
            return False

        # Check for suit agreement: ANY suit bid by me (opener) can be trump
        # This handles cases like: 1♠-2NT-3NT-4NT where spades could be trump
        my_suits = [bid[1] for bid in auction_history if (auction_history.index(bid) % 4) == my_index
                    and len(bid) >= 2 and bid[1] in '♣♦♥♠']
        partner_suits = [bid[1] for bid in partner_bids if len(bid) >= 2 and bid[1] in '♣♦♥♠']

        # If I (opener) showed a suit, that could be trump for Blackwood
        # Even if partner bid NT later, they could be asking for aces in my suit
        if my_suits:
            # I showed a suit - partner's 4NT is likely Blackwood
            return True

        # Check for explicit suit agreement (both partners bid same suit)
        common_suits = set(my_suits) & set(partner_suits)
        if common_suits:
            # Explicit suit agreement - definitely Blackwood
            return True

        # Partner bid a suit but I didn't - check if I raised their suit
        if partner_suits:
            # Partner showed a suit - check if I supported it
            # This is likely Blackwood if we have fit
            return True

        # No suits shown by anyone - this is quantitative NT auction
        return False

    def _get_ace_answer_bid(self, hand: Hand) -> Tuple[str, str]:
        """Counts aces and returns the correct conventional response."""
        num_aces = sum(1 for card in hand.cards if card.rank == 'A')

        if num_aces == 0 or num_aces == 4:
            return ("5♣", "Response to Blackwood: 0 or 4 aces.")
        if num_aces == 1:
            return ("5♦", "Response to Blackwood: 1 ace.")
        if num_aces == 2:
            return ("5♥", "Response to Blackwood: 2 aces.")
        if num_aces == 3:
            return ("5♠", "Response to Blackwood: 3 aces.")

        return ("Pass", "Error: Could not count aces.") # Should not be reached

    def _is_signoff_applicable(self, features: Dict) -> bool:
        """Check if we asked Blackwood and partner responded."""
        auction_history = features.get('auction_history', [])
        my_index = features.get('my_index', -1)

        # Check if we bid 4NT and partner responded
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if features['positions'][i % 4] == features['positions'][my_index]]

        # Did we ask for aces?
        if '4NT' not in my_bids:
            return False

        # Did partner respond?
        partner_last_bid = features['auction_features'].get('partner_last_bid', '')
        return partner_last_bid in ['5♣', '5♦', '5♥', '5♠']

    def _get_signoff_bid(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Signoff after receiving ace response."""
        partner_last_bid = features['auction_features'].get('partner_last_bid', '')

        # Decode partner's ace count
        ace_responses = {'5♣': [0, 4], '5♦': [1], '5♥': [2], '5♠': [3]}
        partner_aces = ace_responses.get(partner_last_bid, [0])

        # Count our own aces
        my_aces = sum(1 for card in hand.cards if card.rank == 'A')

        # Determine trump suit from auction (simplified - check for agreed major)
        auction_features = features.get('auction_features', {})
        opening_bid = auction_features.get('opening_bid', '')
        trump_suit = opening_bid[1] if len(opening_bid) >= 2 and opening_bid[1] in ['♥', '♠'] else None

        # Decide slam level based on aces
        if partner_aces[0] == 0 or (len(partner_aces) > 1 and partner_aces[1] == 4):
            # Partner has 0 or 4 aces - assume 0 for safety
            missing_aces = 4 - my_aces
            if missing_aces >= 2:
                # Missing 2+ aces, sign off at 5-level
                if trump_suit:
                    return (f"5{trump_suit}", f"Signing off at 5-level, missing {missing_aces} aces.")
                else:
                    return ("5NT", "Signing off (no clear trump suit).")
            elif missing_aces == 1:
                # Missing 1 ace, bid small slam
                if trump_suit:
                    return (f"6{trump_suit}", f"Bidding small slam with {my_aces + partner_aces[0]} aces.")
                else:
                    return ("6NT", "Bidding small slam in NT.")
            else:
                # All 4 aces present - bid grand slam!
                if trump_suit:
                    return (f"7{trump_suit}", f"Bidding grand slam with all 4 aces present!")
                else:
                    return ("7NT", "Bidding grand slam in NT with all 4 aces.")
        else:
            # Partner has definite count
            total_aces = my_aces + partner_aces[0]

            if total_aces <= 2:
                # Missing 2+ aces, sign off at 5-level
                if trump_suit:
                    return (f"5{trump_suit}", f"Signing off at 5-level with {total_aces} aces.")
                else:
                    return ("5NT", "Signing off (no clear trump suit).")
            elif total_aces == 3:
                # Missing 1 ace, bid small slam
                if trump_suit:
                    return (f"6{trump_suit}", f"Bidding small slam with {total_aces} aces.")
                else:
                    return ("6NT", "Bidding small slam in NT with 3 aces.")
            else:
                # All 4 aces present - bid grand slam!
                if trump_suit:
                    return (f"7{trump_suit}", f"Bidding grand slam with all 4 aces present!")
                else:
                    return ("7NT", "Bidding grand slam in NT with all 4 aces.")

    def _is_king_asking_applicable(self, hand: Hand, features: Dict) -> bool:
        """Check if we should ask for kings (all aces present)."""
        auction_history = features.get('auction_history', [])
        my_index = features.get('my_index', -1)
        partner_last_bid = features['auction_features'].get('partner_last_bid', '')

        # Must have asked for aces
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if features['positions'][i % 4] == features['positions'][my_index]]
        if '4NT' not in my_bids:
            return False

        # Partner must have responded with aces
        if partner_last_bid not in ['5♣', '5♦', '5♥', '5♠']:
            return False

        # Decode partner's aces
        ace_responses = {'5♣': [0, 4], '5♦': [1], '5♥': [2], '5♠': [3]}
        partner_aces = ace_responses.get(partner_last_bid, [0])
        my_aces = sum(1 for card in hand.cards if card.rank == 'A')

        # Only ask for kings if we have all 4 aces
        if len(partner_aces) > 1 and 4 in partner_aces:
            # Partner might have 4 aces
            return True
        elif my_aces + partner_aces[0] == 4:
            # We have all 4 aces
            return True

        return False

    def _get_king_ask_bid(self) -> Tuple[str, str]:
        """Returns the 5NT king-asking bid."""
        return ("5NT", "Asking for kings (all aces present).")

    def _is_king_answering_applicable(self, features: Dict) -> bool:
        """Determines if we are responding to a 5NT king ask."""
        return features['auction_features'].get('partner_last_bid') == '5NT'

    def _get_king_answer_bid(self, hand: Hand) -> Tuple[str, str]:
        """Counts kings and returns the correct conventional response (same as aces)."""
        num_kings = sum(1 for card in hand.cards if card.rank == 'K')

        if num_kings == 0 or num_kings == 4:
            return ("6♣", "Response to 5NT: 0 or 4 kings.")
        if num_kings == 1:
            return ("6♦", "Response to 5NT: 1 king.")
        if num_kings == 2:
            return ("6♥", "Response to 5NT: 2 kings.")
        if num_kings == 3:
            return ("6♠", "Response to 5NT: 3 kings.")

        return ("Pass", "Error: Could not count kings.")
# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("blackwood", BlackwoodConvention())
