from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from typing import Optional, Tuple, Dict, List

class StaymanConvention(ConventionModule):
    """
    Complete Stayman convention implementation.
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
        """Check if responder should bid 2♣ Stayman."""
        auction_features = features.get('auction_features', {})
        # Condition: Partner must have opened 1NT
        if auction_features.get('opening_bid') != '1NT' or auction_features.get('opener_relationship') != 'Partner':
            return False
        
        non_pass_bids = [bid for bid in features.get('auction_history', []) if bid != 'Pass']
        if len(non_pass_bids) != 1: return False

        # Condition: Hand must meet Stayman point and suit requirements
        # Allow 7 HCP if hand has both 4-card majors (4-4 shape is ideal for Stayman)
        has_both_majors = hand.suit_lengths['♥'] >= 4 and hand.suit_lengths['♠'] >= 4
        if hand.hcp < 7: return False  # Never Stayman with 6 or fewer
        if hand.hcp == 7 and not has_both_majors: return False  # 7 HCP requires 4-4 in majors

        if hand.suit_lengths['♥'] >= 5 or hand.suit_lengths['♠'] >= 5: return False # Use Jacoby for 5-card majors
        if hand.suit_lengths['♥'] < 4 and hand.suit_lengths['♠'] < 4: return False

        return True

    def _initiate_stayman(self, hand: Hand, features: Dict) -> Tuple[str, str]:
        """Bid 2♣ Stayman."""
        return ("2♣", f"Stayman. Asks partner for a 4-card major. Shows {hand.hcp} HCP.")

    def _is_stayman_response_position(self, features: Dict) -> bool:
        """Check if we're opener responding to Stayman 2♣."""
        auction_features = features.get('auction_features', {})
        # THIS IS THE FIX: Added check for opening_bid == '1NT'
        return (auction_features.get('opening_bid') == '1NT' and
                auction_features.get('opener_relationship') == 'Me' and
                auction_features.get('partner_last_bid') == '2♣')

    def _respond_to_stayman(self, hand: Hand, features: Dict) -> Tuple[str, str]:
        """Opener's response to 2♣ Stayman."""
        if hand.suit_lengths['♥'] >= 4: return ("2♥", "Stayman response showing 4+ hearts.")
        if hand.suit_lengths['♠'] >= 4: return ("2♠", "Stayman response showing 4+ spades.")
        return ("2♦", "Stayman response denying 4-card majors.")

    def _is_responder_rebid_position(self, features: Dict) -> bool:
        """Check if responder should rebid after opener's Stayman response."""
        auction_features = features.get('auction_features', {})
        auction_history = features.get('auction_history', [])

        # Must be responder (partner opened 1NT)
        if auction_features.get('opener_relationship') != 'Partner':
            return False
        if auction_features.get('opening_bid') != '1NT':
            return False

        # Check if we bid Stayman and partner responded
        # Auction should be: 1NT - 2♣ - 2♦/2♥/2♠
        if len(auction_history) < 3:
            return False

        my_index = features.get('my_index', -1)
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if features['positions'][i % 4] == features['positions'][my_index]]

        # Check if we bid Stayman (2♣ after 1NT)
        if len(my_bids) < 1:
            return False
        if my_bids[0] != '2♣':
            return False

        # Partner must have responded
        partner_last_bid = auction_features.get('partner_last_bid', '')
        return partner_last_bid in ['2♦', '2♥', '2♠']

    def _get_responder_rebid(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Responder's rebid after opener answers Stayman."""
        partner_last_bid = features['auction_features'].get('partner_last_bid', '')

        # Determine if we found a fit
        fit_found = False
        fit_suit = None

        if partner_last_bid == '2♥' and hand.suit_lengths['♥'] >= 4:
            fit_found = True
            fit_suit = '♥'
        elif partner_last_bid == '2♠' and hand.suit_lengths['♠'] >= 4:
            fit_found = True
            fit_suit = '♠'

        # Decide rebid based on strength and fit
        if fit_found:
            # Found 4-4 fit in a major
            if hand.hcp <= 7:
                # Weak hand (7 HCP): Pass or bid 2-level
                return ("Pass", f"Minimum Stayman ({hand.hcp} HCP), passing with {fit_suit} fit.")
            elif 8 <= hand.hcp <= 9:
                # Invitational (8-9 HCP): Invite game
                return (f"3{fit_suit}", f"Invitational ({hand.hcp} HCP) with 4-card {fit_suit} fit.")
            else:
                # Game-forcing (10+ HCP): Bid game
                return (f"4{fit_suit}", f"Game-forcing ({hand.hcp} HCP) with 4-card {fit_suit} fit.")
        else:
            # No fit found
            if partner_last_bid == '2♦':
                # Opener denied 4-card major
                if hand.hcp <= 7:
                    # Weak hand: Pass or bid a 5-card major
                    if hand.suit_lengths['♥'] == 5:
                        return ("2♥", f"Weak hand ({hand.hcp} HCP), signing off in 5-card hearts.")
                    elif hand.suit_lengths['♠'] == 5:
                        return ("2♠", f"Weak hand ({hand.hcp} HCP), signing off in 5-card spades.")
                    else:
                        return ("Pass", f"Weak hand ({hand.hcp} HCP), no fit found, passing 2♦.")
                elif 8 <= hand.hcp <= 9:
                    # Invitational: Bid 2NT
                    return ("2NT", f"Invitational ({hand.hcp} HCP), no major fit found.")
                else:
                    # Game-forcing: Bid 3NT
                    return ("3NT", f"Game-forcing ({hand.hcp} HCP), no major fit, bidding 3NT.")
            else:
                # Partner showed a major we don't have
                # (e.g., we have 4 hearts, partner showed spades)
                if hand.hcp <= 7:
                    return ("Pass", f"Minimum ({hand.hcp} HCP), no fit for partner's {partner_last_bid[1]}.")
                elif 8 <= hand.hcp <= 9:
                    return ("2NT", f"Invitational ({hand.hcp} HCP), no fit for partner's {partner_last_bid[1]}.")
                else:
                    return ("3NT", f"Game-forcing ({hand.hcp} HCP), bidding 3NT with no major fit.")