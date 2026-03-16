from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict, List

class StaymanConvention(ConventionModule):
    """
    Complete Stayman convention implementation.

    Handles both:
    - 2♣ Stayman over 1NT (15-17 HCP)
    - 3♣ Stayman over 2NT (20-21 HCP)
    """
    def get_constraints(self) -> Dict:
        return {'hcp_range': (8, 40), 'suit_length_req': (['♥', '♠'], 4, 'any_of')}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        # Check for responder's rebid after Stayman response
        if self._is_responder_rebid_position(features):
            return self._get_responder_rebid(hand, features)
        # Check for initiating Stayman
        if self._should_bid_stayman(hand, features):
            return self._initiate_stayman(hand, features)
        # Check for opener responding to Stayman
        if self._is_stayman_response_position(features):
            return self._respond_to_stayman(hand, features)
        return None

    def _should_bid_stayman(self, hand: Hand, features: Dict) -> bool:
        """Check if responder should bid Stayman (2♣ over 1NT only).

        Note: 2NT uses Puppet Stayman (3♣) instead of regular Stayman.
        """
        auction_features = features.get('auction_features', {})
        opening_bid = auction_features.get('opening_bid')

        # Only 1NT — Puppet Stayman handles 2NT
        if opening_bid != '1NT' or auction_features.get('opener_relationship') != 'Partner':
            return False

        non_pass_bids = [bid for bid in features.get('auction_history', []) if bid != 'Pass']
        if len(non_pass_bids) != 1: return False

        h_len = hand.suit_lengths['♥']
        s_len = hand.suit_lengths['♠']

        # Must have at least one 4-card major
        if h_len < 4 and s_len < 4: return False

        # With 5+ card major: normally use Jacoby, BUT with 5-4 in majors
        # and 10+ HCP, use Stayman first for Smolen sequence
        if h_len >= 5 or s_len >= 5:
            has_5_4_majors = (
                (h_len >= 5 and s_len == 4) or (s_len >= 5 and h_len == 4)
            )
            if not (has_5_4_majors and hand.hcp >= 10):
                return False  # Use Jacoby for 5-card majors without Smolen shape

        # Over 1NT (15-17): Need 7+ HCP (or 7 with both majors)
        has_both_majors = h_len >= 4 and s_len >= 4
        if hand.hcp < 7: return False
        if hand.hcp == 7 and not has_both_majors: return False

        return True

    def _initiate_stayman(self, hand: Hand, features: Dict) -> Tuple[str, str, dict]:
        """Bid Stayman (2♣ over 1NT only)."""
        metadata = {'bypass_suit_length': True, 'bypass_hcp': True}
        return ("2♣", f"Stayman. Asks partner for a 4-card major. Shows {hand.hcp} HCP.", metadata)

    def _is_stayman_response_position(self, features: Dict) -> bool:
        """Check if we're opener responding to Stayman (2♣ over 1NT only)."""
        auction_features = features.get('auction_features', {})

        if auction_features.get('opener_relationship') != 'Me':
            return False

        return (auction_features.get('opening_bid') == '1NT' and
                auction_features.get('partner_last_bid') == '2♣')

    def _respond_to_stayman(self, hand: Hand, features: Dict) -> Tuple[str, str, dict]:
        """Opener's response to Stayman (2♦/2♥/2♠ over 1NT)."""
        metadata = {'bypass_suit_length': True, 'bypass_hcp': True}

        if hand.suit_lengths['♥'] >= 4:
            return ("2♥", "Stayman response showing 4+ hearts.", metadata)
        if hand.suit_lengths['♠'] >= 4:
            return ("2♠", "Stayman response showing 4+ spades.", metadata)
        return ("2♦", "Stayman response denying 4-card majors.", metadata)

    def _is_responder_rebid_position(self, features: Dict) -> bool:
        """Check if responder should rebid after opener's Stayman response (1NT only)."""
        auction_features = features.get('auction_features', {})
        auction_history = features.get('auction_history', [])

        if auction_features.get('opener_relationship') != 'Partner':
            return False
        if auction_features.get('opening_bid') != '1NT':
            return False

        if len(auction_history) < 3:
            return False

        my_index = features.get('my_index', -1)
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if features['positions'][i % 4] == features['positions'][my_index]]

        if len(my_bids) < 1 or my_bids[0] != '2♣':
            return False

        partner_last_bid = auction_features.get('partner_last_bid', '')
        return partner_last_bid in ['2♦', '2♥', '2♠']

    def _get_responder_rebid(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Responder's rebid after opener answers Stayman (1NT only)."""
        auction_features = features.get('auction_features', {})
        partner_last_bid = auction_features.get('partner_last_bid', '')

        metadata = {'bypass_suit_length': True, 'bypass_hcp': True}

        # Determine if we found a fit
        fit_found = False
        fit_suit = None
        partner_suit = partner_last_bid[1] if len(partner_last_bid) >= 2 else None

        if partner_suit == '♥' and hand.suit_lengths['♥'] >= 4:
            fit_found = True
            fit_suit = '♥'
        elif partner_suit == '♠' and hand.suit_lengths['♠'] >= 4:
            fit_found = True
            fit_suit = '♠'

        is_denial = partner_last_bid == '2♦'

        # After 1NT (15-17)
        if fit_found:
            if hand.hcp <= 7:
                return ("Pass", f"Minimum Stayman ({hand.hcp} HCP), passing with {fit_suit} fit.")
            elif 8 <= hand.hcp <= 9:
                return (f"3{fit_suit}", f"Invitational ({hand.hcp} HCP) with 4-card {fit_suit} fit.", metadata)
            elif hand.hcp >= 15:
                return ("4NT", f"Slam invite with {hand.hcp} HCP and 4-card {fit_suit} fit (combined 30+).", metadata)
            else:
                return (f"4{fit_suit}", f"Game-forcing ({hand.hcp} HCP) with 4-card {fit_suit} fit.", metadata)
        else:
            game_metadata = {'bypass_suit_length': True, 'bypass_hcp': True, 'game_forcing': True, 'convention': 'stayman_continuation'}

            if is_denial:
                if hand.hcp <= 7:
                    if hand.suit_lengths['♥'] == 5:
                        return ("2♥", f"Weak hand ({hand.hcp} HCP), signing off in 5-card hearts.", metadata)
                    elif hand.suit_lengths['♠'] == 5:
                        return ("2♠", f"Weak hand ({hand.hcp} HCP), signing off in 5-card spades.", metadata)
                    else:
                        return ("Pass", f"Weak hand ({hand.hcp} HCP), no fit found, passing 2♦.")
                elif 8 <= hand.hcp <= 9:
                    return ("2NT", f"Invitational ({hand.hcp} HCP), no major fit found.", metadata)
                elif hand.hcp >= 16:
                    return ("4NT", f"Quantitative slam invite ({hand.hcp} HCP), no major fit.", metadata)
                else:
                    return ("3NT", f"Game-forcing ({hand.hcp} HCP), no major fit, bidding 3NT.", game_metadata)
            else:
                if hand.hcp <= 7:
                    return ("Pass", f"Minimum ({hand.hcp} HCP), no fit for partner's {partner_suit}.")
                elif 8 <= hand.hcp <= 9:
                    return ("2NT", f"Invitational ({hand.hcp} HCP), no fit for partner's {partner_suit}.", metadata)
                elif hand.hcp >= 16:
                    return ("4NT", f"Quantitative slam invite ({hand.hcp} HCP), no fit for partner's {partner_suit}.", metadata)
                else:
                    return ("3NT", f"Game-forcing ({hand.hcp} HCP), bidding 3NT with no major fit.", game_metadata)
# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("stayman", StaymanConvention())
