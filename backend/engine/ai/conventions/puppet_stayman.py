from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.bidding_validation import BidValidator
from typing import Optional, Tuple, Dict


class PuppetStaymanConvention(ConventionModule):
    """
    Puppet Stayman — 3♣ over 2NT to discover both 4-card and 5-card majors.

    Replaces regular Stayman over 2NT. The key advantage is that it finds
    both 4-4 AND 5-3 major fits while keeping opener as declarer.

    Opener's response to 3♣:
      - 3♦ = has at least one 4-card major (doesn't say which)
      - 3♥ = has 5 hearts
      - 3♠ = has 5 spades
      - 3NT = no 4+ card major

    After opener's 3♦ (has a 4-card major), responder uses INVERSION:
      - 3♥ = I have 4 SPADES (showing suit I DON'T have)
      - 3♠ = I have 4 HEARTS (showing suit I DON'T have)
      - 4♦ = I have BOTH 4-card majors (opener picks)

    After responder's inversion bid, opener places the contract:
      - 4M = fit found (opener has 4 in partner's actual suit)
      - 3NT = no fit (opener's 4-card major ≠ responder's 4-card major)
      - After 4♦: opener bids their 4-card major at game level
    """

    def get_constraints(self) -> Dict:
        return {'suit_length_req': (['♥', '♠'], 4, 'any_of')}

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """Main evaluation dispatching to appropriate phase."""
        # Phase 4: Opener places contract after responder's inversion bid
        if self._is_opener_placement_applicable(features):
            return self._get_opener_placement(hand, features)
        # Phase 3: Responder continues after opener's 3♦/3♥/3♠/3NT
        if self._is_responder_continuation_applicable(features):
            return self._get_responder_continuation(hand, features)
        # Phase 2: Opener responds to 3♣
        if self._is_puppet_response_applicable(features):
            return self._respond_to_puppet(hand, features)
        # Phase 1: Responder initiates 3♣ over 2NT
        if self._should_bid_puppet(hand, features):
            return self._initiate_puppet(hand, features)
        return None

    # ── Phase 1: Responder initiates 3♣ ──────────────────────────────

    def _should_bid_puppet(self, hand: Hand, features: Dict) -> bool:
        """Check if responder should bid 3♣ Puppet Stayman over 2NT.

        Requirements:
        - Partner opened 2NT (20-21 HCP)
        - First response (no prior bids except passes)
        - At least one 4-card major
        - 4+ HCP (combined 24+ for game)
        - NOT 5+ card major with <10 HCP (use Jacoby transfer instead)
        """
        auction_features = features.get('auction_features', {})
        opening_bid = auction_features.get('opening_bid')

        if opening_bid != '2NT':
            return False
        if auction_features.get('opener_relationship') != 'Partner':
            return False

        # Must be first response
        non_pass_bids = [bid for bid in features.get('auction_history', [])
                         if bid != 'Pass']
        if len(non_pass_bids) != 1:
            return False

        # Must have at least one 4-card major
        h_len = hand.suit_lengths['♥']
        s_len = hand.suit_lengths['♠']
        if h_len < 4 and s_len < 4:
            return False

        # With 5+ card major and weak hand, prefer Jacoby transfer
        if (h_len >= 5 or s_len >= 5) and hand.hcp < 10:
            return False

        # Minimum HCP for game exploration
        if hand.hcp < 4:
            return False

        return True

    def _initiate_puppet(self, hand: Hand, features: Dict) -> Tuple[str, str, dict]:
        """Bid 3♣ Puppet Stayman over 2NT."""
        metadata = {'bypass_suit_length': True, 'bypass_hcp': True,
                    'bypass_sanity_check': True, 'convention': 'puppet_stayman'}
        return ("3♣", f"Puppet Stayman over 2NT. Asks partner about major suit "
                       f"holdings ({hand.hcp} HCP).", metadata)

    # ── Phase 2: Opener responds to 3♣ ──────────────────────────────

    def _is_puppet_response_applicable(self, features: Dict) -> bool:
        """Check if opener should respond to partner's 3♣ Puppet Stayman."""
        auction_features = features.get('auction_features', {})

        if auction_features.get('opener_relationship') != 'Me':
            return False
        if auction_features.get('opening_bid') != '2NT':
            return False
        if auction_features.get('partner_last_bid') != '3♣':
            return False

        return True

    def _respond_to_puppet(self, hand: Hand, features: Dict) -> Tuple[str, str, dict]:
        """Opener responds to Puppet Stayman.

        Priority:
        1. 5-card major → bid it directly (3♥ or 3♠)
        2. 4-card major (no 5-card) → bid 3♦ (relay)
        3. No 4+ card major → bid 3NT
        """
        metadata = {'bypass_suit_length': True, 'bypass_hcp': True,
                    'bypass_sanity_check': True, 'convention': 'puppet_stayman_response'}

        h_len = hand.suit_lengths['♥']
        s_len = hand.suit_lengths['♠']

        # 5-card major: bid directly (prefer hearts if both 5+, rare but possible)
        if h_len >= 5:
            return ("3♥", f"Puppet Stayman response: showing 5 hearts.", metadata)
        if s_len >= 5:
            return ("3♠", f"Puppet Stayman response: showing 5 spades.", metadata)

        # 4-card major: bid 3♦ relay (doesn't reveal which major)
        if h_len >= 4 or s_len >= 4:
            return ("3♦", f"Puppet Stayman response: has a 4-card major.", metadata)

        # No 4+ card major
        return ("3NT", f"Puppet Stayman response: no 4+ card major.", metadata)

    # ── Phase 3: Responder continues after opener's response ─────────

    def _is_responder_continuation_applicable(self, features: Dict) -> bool:
        """Check if responder should continue after opener's Puppet response."""
        auction_features = features.get('auction_features', {})
        partner_last_bid = auction_features.get('partner_last_bid')

        if auction_features.get('opener_relationship') != 'Partner':
            return False
        if auction_features.get('opening_bid') != '2NT':
            return False

        # Verify we bid 3♣ Puppet
        my_index = features.get('my_index', -1)
        positions = features.get('positions', [])
        auction_history = features.get('auction_history', [])
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if positions[i % 4] == positions[my_index]
                   and auction_history[i] not in ['Pass', 'X', 'XX']]

        if not my_bids or my_bids[0] != '3♣':
            return False

        # Partner must have responded to Puppet
        return partner_last_bid in ['3♦', '3♥', '3♠', '3NT']

    def _get_responder_continuation(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str, dict]]:
        """Responder's continuation after opener's Puppet response."""
        partner_last_bid = features['auction_features']['partner_last_bid']
        metadata = {'bypass_suit_length': True, 'bypass_hcp': True,
                    'bypass_sanity_check': True, 'convention': 'puppet_stayman_continuation'}

        h_len = hand.suit_lengths['♥']
        s_len = hand.suit_lengths['♠']

        # After 3♦ (opener has a 4-card major): use INVERSION
        if partner_last_bid == '3♦':
            return self._get_inversion_bid(hand, h_len, s_len, metadata)

        # After 3♥ (opener has 5 hearts)
        if partner_last_bid == '3♥':
            if h_len >= 3:
                return ("4♥", f"Raising opener's 5 hearts with {h_len}-card support ({hand.hcp} HCP).", metadata)
            elif hand.hcp >= 13:
                return ("4NT", f"Quantitative slam invite, no heart fit ({hand.hcp} HCP).", metadata)
            else:
                return ("3NT", f"No heart support, signing off in 3NT ({hand.hcp} HCP).", metadata)

        # After 3♠ (opener has 5 spades)
        if partner_last_bid == '3♠':
            if s_len >= 3:
                return ("4♠", f"Raising opener's 5 spades with {s_len}-card support ({hand.hcp} HCP).", metadata)
            elif hand.hcp >= 13:
                return ("4NT", f"Quantitative slam invite, no spade fit ({hand.hcp} HCP).", metadata)
            else:
                return ("3NT", f"No spade support, signing off in 3NT ({hand.hcp} HCP).", metadata)

        # After 3NT (opener has no 4+ major)
        if partner_last_bid == '3NT':
            if hand.hcp >= 13:
                return ("4NT", f"Quantitative slam invite ({hand.hcp} HCP). Combined 33+.", metadata)
            else:
                return ("Pass", f"No major fit, accepting 3NT ({hand.hcp} HCP).")

        return None

    def _get_inversion_bid(self, hand: Hand, h_len: int, s_len: int,
                           metadata: dict) -> Tuple[str, str, dict]:
        """Responder's inversion bid after opener's 3♦.

        INVERSION: Bid the major you DON'T have to let opener identify the fit.
        - 3♥ = I have 4 spades (I DON'T have hearts)
        - 3♠ = I have 4 hearts (I DON'T have spades)
        - 4♦ = I have both 4-card majors (opener picks)
        """
        has_4h = h_len >= 4
        has_4s = s_len >= 4

        if has_4h and has_4s:
            return ("4♦", f"Puppet inversion: showing both 4-card majors. "
                          f"Opener picks their major ({hand.hcp} HCP).", metadata)
        elif has_4s and not has_4h:
            # I have spades, bid hearts (the suit I DON'T have)
            return ("3♥", f"Puppet inversion: showing 4 spades (bidding suit I don't have). "
                          f"({hand.hcp} HCP).", metadata)
        elif has_4h and not has_4s:
            # I have hearts, bid spades (the suit I DON'T have)
            return ("3♠", f"Puppet inversion: showing 4 hearts (bidding suit I don't have). "
                          f"({hand.hcp} HCP).", metadata)
        else:
            # No 4-card major (shouldn't happen — we bid Puppet because we had one)
            return ("3NT", f"No 4-card major, signing off in 3NT ({hand.hcp} HCP).", metadata)

    # ── Phase 4: Opener places contract after inversion ──────────────

    def _is_opener_placement_applicable(self, features: Dict) -> bool:
        """Check if opener should place contract after responder's inversion bid."""
        auction_features = features.get('auction_features', {})
        partner_last_bid = auction_features.get('partner_last_bid')

        if auction_features.get('opener_relationship') != 'Me':
            return False
        if auction_features.get('opening_bid') != '2NT':
            return False

        # After our 3♦ response, partner's inversion bid
        if partner_last_bid not in ['3♥', '3♠', '4♦']:
            return False

        # Verify we responded 3♦ to Puppet
        my_index = features.get('my_index', -1)
        positions = features.get('positions', [])
        auction_history = features.get('auction_history', [])
        my_bids = [auction_history[i] for i in range(len(auction_history))
                   if positions[i % 4] == positions[my_index]
                   and auction_history[i] not in ['Pass', 'X', 'XX']]

        if len(my_bids) < 2:
            return False
        if my_bids[0] != '2NT' or my_bids[1] != '3♦':
            return False

        return True

    def _get_opener_placement(self, hand: Hand, features: Dict) -> Tuple[str, str, dict]:
        """Opener places contract after responder's inversion bid.

        - After 3♥ (responder has 4♠): bid 4♠ with 4 spades, else 3NT
        - After 3♠ (responder has 4♥): bid 4♥ with 4 hearts, else 3NT
        - After 4♦ (responder has both): bid our 4-card major at game level
        """
        partner_last_bid = features['auction_features']['partner_last_bid']
        metadata = {'bypass_suit_length': True, 'bypass_hcp': True,
                    'bypass_sanity_check': True, 'convention': 'puppet_stayman_placement'}

        h_len = hand.suit_lengths['♥']
        s_len = hand.suit_lengths['♠']

        if partner_last_bid == '3♥':
            # Responder has 4 spades
            if s_len >= 4:
                return ("4♠", f"Puppet fit: 4-4 spade fit found.", metadata)
            else:
                return ("3NT", f"No spade fit (only {s_len} spades). Playing 3NT.", metadata)

        elif partner_last_bid == '3♠':
            # Responder has 4 hearts
            if h_len >= 4:
                return ("4♥", f"Puppet fit: 4-4 heart fit found.", metadata)
            else:
                return ("3NT", f"No heart fit (only {h_len} hearts). Playing 3NT.", metadata)

        elif partner_last_bid == '4♦':
            # Responder has both 4-card majors — bid ours
            if h_len >= 4:
                return ("4♥", f"Puppet: bidding 4-card hearts (responder has both majors).", metadata)
            elif s_len >= 4:
                return ("4♠", f"Puppet: bidding 4-card spades (responder has both majors).", metadata)
            else:
                return ("4NT", f"No 4-card major (unexpected). Quantitative.", metadata)

        return ("3NT", "Puppet placement fallthrough.", metadata)


# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("puppet_stayman", PuppetStaymanConvention())
