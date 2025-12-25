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
        """Check if responder should bid Stayman (2♣ over 1NT, 3♣ over 2NT)."""
        auction_features = features.get('auction_features', {})
        opening_bid = auction_features.get('opening_bid')

        # Condition: Partner must have opened 1NT or 2NT
        if opening_bid not in ['1NT', '2NT'] or auction_features.get('opener_relationship') != 'Partner':
            return False

        non_pass_bids = [bid for bid in features.get('auction_history', []) if bid != 'Pass']
        if len(non_pass_bids) != 1: return False

        # Condition: Must have at least one 4-card major (but not 5+ which uses Jacoby)
        if hand.suit_lengths['♥'] >= 5 or hand.suit_lengths['♠'] >= 5: return False # Use Jacoby for 5-card majors
        if hand.suit_lengths['♥'] < 4 and hand.suit_lengths['♠'] < 4: return False

        # Point requirements differ based on opening
        if opening_bid == '1NT':
            # Over 1NT (15-17): Need 7+ HCP (or 7 with both majors)
            has_both_majors = hand.suit_lengths['♥'] >= 4 and hand.suit_lengths['♠'] >= 4
            if hand.hcp < 7: return False
            if hand.hcp == 7 and not has_both_majors: return False
        else:  # 2NT
            # Over 2NT (20-21): Combined 25+ for game, so need 4+ HCP
            # But Stayman is best with slam interest (11+ HCP) or game values (5+ HCP)
            if hand.hcp < 4: return False  # Too weak even for game

        return True

    def _initiate_stayman(self, hand: Hand, features: Dict) -> Tuple[str, str, dict]:
        """Bid Stayman (2♣ over 1NT, 3♣ over 2NT)."""
        auction_features = features.get('auction_features', {})
        opening_bid = auction_features.get('opening_bid')

        # Metadata to bypass suit length validation for artificial Stayman bid
        metadata = {'bypass_suit_length': True, 'bypass_hcp': True}

        if opening_bid == '2NT':
            return ("3♣", f"Stayman over 2NT. Asks partner for a 4-card major. Shows {hand.hcp} HCP.", metadata)
        else:
            return ("2♣", f"Stayman. Asks partner for a 4-card major. Shows {hand.hcp} HCP.", metadata)

    def _is_stayman_response_position(self, features: Dict) -> bool:
        """Check if we're opener responding to Stayman (2♣ over 1NT, 3♣ over 2NT)."""
        auction_features = features.get('auction_features', {})
        opening_bid = auction_features.get('opening_bid')
        partner_last_bid = auction_features.get('partner_last_bid')

        if auction_features.get('opener_relationship') != 'Me':
            return False

        # Check for appropriate Stayman ask based on opening
        if opening_bid == '1NT' and partner_last_bid == '2♣':
            return True
        if opening_bid == '2NT' and partner_last_bid == '3♣':
            return True

        return False

    def _respond_to_stayman(self, hand: Hand, features: Dict) -> Tuple[str, str, dict]:
        """Opener's response to Stayman (2♦/2♥/2♠ over 1NT, 3♦/3♥/3♠ over 2NT)."""
        auction_features = features.get('auction_features', {})
        opening_bid = auction_features.get('opening_bid')

        # Metadata to bypass suit length validation for artificial Stayman responses
        metadata = {'bypass_suit_length': True, 'bypass_hcp': True}

        # Response level depends on opening: 2-level over 1NT, 3-level over 2NT
        level = '3' if opening_bid == '2NT' else '2'

        if hand.suit_lengths['♥'] >= 4:
            return (f"{level}♥", f"Stayman response showing 4+ hearts.", metadata)
        if hand.suit_lengths['♠'] >= 4:
            return (f"{level}♠", f"Stayman response showing 4+ spades.", metadata)
        # Denial bid is artificial - may only have 2-3 diamonds
        return (f"{level}♦", "Stayman response denying 4-card majors.", metadata)

    def _is_responder_rebid_position(self, features: Dict) -> bool:
        """Check if responder should rebid after opener's Stayman response."""
        auction_features = features.get('auction_features', {})
        auction_history = features.get('auction_history', [])
        opening_bid = auction_features.get('opening_bid')

        # Must be responder (partner opened 1NT or 2NT)
        if auction_features.get('opener_relationship') != 'Partner':
            return False
        if opening_bid not in ['1NT', '2NT']:
            return False

        # Check if we bid Stayman and partner responded
        # Auction should be: 1NT - 2♣ - 2♦/2♥/2♠ OR 2NT - 3♣ - 3♦/3♥/3♠
        if len(auction_history) < 3:
            return False

        my_index = features.get('my_index', -1)
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if features['positions'][i % 4] == features['positions'][my_index]]

        # Check if we bid Stayman (2♣ after 1NT, 3♣ after 2NT)
        if len(my_bids) < 1:
            return False

        stayman_bid = '3♣' if opening_bid == '2NT' else '2♣'
        if my_bids[0] != stayman_bid:
            return False

        # Partner must have responded with appropriate level
        partner_last_bid = auction_features.get('partner_last_bid', '')
        if opening_bid == '2NT':
            return partner_last_bid in ['3♦', '3♥', '3♠']
        else:
            return partner_last_bid in ['2♦', '2♥', '2♠']

    def _get_responder_rebid(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Responder's rebid after opener answers Stayman."""
        auction_features = features.get('auction_features', {})
        opening_bid = auction_features.get('opening_bid')
        partner_last_bid = auction_features.get('partner_last_bid', '')

        # Metadata for bypass validation
        metadata = {'bypass_suit_length': True, 'bypass_hcp': True}

        # Determine if we found a fit (check the suit regardless of level)
        fit_found = False
        fit_suit = None
        partner_suit = partner_last_bid[1] if len(partner_last_bid) >= 2 else None

        if partner_suit == '♥' and hand.suit_lengths['♥'] >= 4:
            fit_found = True
            fit_suit = '♥'
        elif partner_suit == '♠' and hand.suit_lengths['♠'] >= 4:
            fit_found = True
            fit_suit = '♠'

        # Denial response check (2♦ after 1NT, 3♦ after 2NT)
        is_denial = (partner_last_bid == '2♦' and opening_bid == '1NT') or \
                    (partner_last_bid == '3♦' and opening_bid == '2NT')

        # Different logic based on opening level
        if opening_bid == '2NT':
            # After 2NT (20-21), we're already at game level or higher
            # Combined points: 20-21 + responder's HCP
            if fit_found:
                # With fit, bid game or explore slam
                if hand.hcp >= 11:
                    # Slam interest (31-32+ combined)
                    return (f"4{fit_suit}", f"Game in {fit_suit} with {hand.hcp} HCP and 4-card fit. Slam possible.", metadata)
                else:
                    # Game values
                    return (f"4{fit_suit}", f"Game in {fit_suit} with {hand.hcp} HCP and 4-card fit.", metadata)
            else:
                # No fit - bid 3NT for game
                if is_denial:
                    return ("3NT", f"No major fit, bidding 3NT game with {hand.hcp} HCP.", metadata)
                else:
                    # Partner showed a major we don't have
                    return ("3NT", f"No fit for partner's {partner_suit}, bidding 3NT with {hand.hcp} HCP.", metadata)
        else:
            # After 1NT (15-17) - original logic
            if fit_found:
                # Found 4-4 fit in a major
                if hand.hcp <= 7:
                    return ("Pass", f"Minimum Stayman ({hand.hcp} HCP), passing with {fit_suit} fit.")
                elif 8 <= hand.hcp <= 9:
                    return (f"3{fit_suit}", f"Invitational ({hand.hcp} HCP) with 4-card {fit_suit} fit.", metadata)
                else:
                    return (f"4{fit_suit}", f"Game-forcing ({hand.hcp} HCP) with 4-card {fit_suit} fit.", metadata)
            else:
                # No fit found
                if is_denial:
                    if hand.hcp <= 7:
                        if hand.suit_lengths['♥'] == 5:
                            return ("2♥", f"Weak hand ({hand.hcp} HCP), signing off in 5-card hearts.")
                        elif hand.suit_lengths['♠'] == 5:
                            return ("2♠", f"Weak hand ({hand.hcp} HCP), signing off in 5-card spades.")
                        else:
                            return ("Pass", f"Weak hand ({hand.hcp} HCP), no fit found, passing 2♦.")
                    elif 8 <= hand.hcp <= 9:
                        return ("2NT", f"Invitational ({hand.hcp} HCP), no major fit found.")
                    else:
                        return ("3NT", f"Game-forcing ({hand.hcp} HCP), no major fit, bidding 3NT.", metadata)
                else:
                    if hand.hcp <= 7:
                        return ("Pass", f"Minimum ({hand.hcp} HCP), no fit for partner's {partner_suit}.")
                    elif 8 <= hand.hcp <= 9:
                        return ("2NT", f"Invitational ({hand.hcp} HCP), no fit for partner's {partner_suit}.")
                    else:
                        return ("3NT", f"Game-forcing ({hand.hcp} HCP), bidding 3NT with no major fit.", metadata)
# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("stayman", StaymanConvention())
