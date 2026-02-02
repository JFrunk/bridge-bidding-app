"""
Per-Seat Belief Model for Bridge Bidding

Tracks what each seat (N/E/S/W) has communicated through their bids:
HCP ranges, suit length ranges, and convention-specific inferences.

This provides a richer context than AuctionContext/PartnershipRanges
(which only track opener/responder roles, not all 4 seats).

Usage:
    from engine.ai.bidding_state import BiddingStateBuilder

    state = BiddingStateBuilder().build(auction_history=['1♠', 'Pass', '2♠', 'Pass'], dealer='N')
    north = state.seat('N')   # SeatBelief for North
    print(north.hcp)           # (12, 21)  - opened 1♠
    print(north.suits['♠'])    # (5, 13)   - 5+ spades
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import logging

from utils.seats import (
    SEATS, normalize, active_seat_bidding, partner, lho, rho,
    partnership_str, is_partner, seat_index
)

logger = logging.getLogger(__name__)

SUITS = ['♠', '♥', '♦', '♣']


@dataclass
class ReasoningStep:
    """One step in the reasoning chain that built a seat's belief."""
    bid: str           # The bid that triggered this inference
    field: str         # 'hcp', 'suit:♠', 'suit:♥', etc.
    before: Tuple[int, int]
    after: Tuple[int, int]
    reason: str        # Human-readable explanation


@dataclass
class SeatBelief:
    """What we believe about one seat's hand based on their bidding."""

    seat: str  # 'N', 'E', 'S', 'W'
    hcp: Tuple[int, int] = (0, 40)
    suits: Dict[str, Tuple[int, int]] = field(default_factory=lambda: {
        '♠': (0, 13), '♥': (0, 13), '♦': (0, 13), '♣': (0, 13)
    })
    limited: bool = False
    passed_opening: bool = False
    tags: List[str] = field(default_factory=list)
    reasoning: List[ReasoningStep] = field(default_factory=list)

    def narrow_hcp(self, new_min: Optional[int] = None, new_max: Optional[int] = None,
                   *, reason: str = '', bid: str = ''):
        """Narrow HCP range. Takes intersection of current and new bounds."""
        before = self.hcp
        cur_min, cur_max = self.hcp
        if new_min is not None:
            cur_min = max(cur_min, new_min)
        if new_max is not None:
            cur_max = min(cur_max, new_max)
        if cur_min > cur_max:
            logger.debug(f"SeatBelief {self.seat}: HCP range inverted ({cur_min}, {cur_max}), capping")
            cur_min = cur_max
        self.hcp = (cur_min, cur_max)
        if reason and self.hcp != before:
            self.reasoning.append(ReasoningStep(
                bid=bid, field='hcp', before=before, after=self.hcp, reason=reason
            ))

    def narrow_suit(self, suit: str, new_min: Optional[int] = None, new_max: Optional[int] = None,
                    *, reason: str = '', bid: str = ''):
        """Narrow suit length range."""
        if suit not in self.suits:
            return
        before = self.suits[suit]
        cur_min, cur_max = self.suits[suit]
        if new_min is not None:
            cur_min = max(cur_min, new_min)
        if new_max is not None:
            cur_max = min(cur_max, new_max)
        if cur_min > cur_max:
            logger.debug(f"SeatBelief {self.seat}: {suit} range inverted ({cur_min}, {cur_max}), capping")
            cur_min = cur_max
        self.suits[suit] = (cur_min, cur_max)
        if reason and self.suits[suit] != before:
            self.reasoning.append(ReasoningStep(
                bid=bid, field=f'suit:{suit}', before=before, after=self.suits[suit], reason=reason
            ))

    def add_tag(self, tag: str):
        if tag not in self.tags:
            self.tags.append(tag)

    def has_tag(self, tag: str) -> bool:
        return tag in self.tags

    @property
    def hcp_midpoint(self) -> float:
        return (self.hcp[0] + self.hcp[1]) / 2

    def to_dict(self, hcp_cap: int = None) -> dict:
        """Serialize belief for API/frontend consumption.

        Args:
            hcp_cap: If provided, caps max HCP at this value (derived from
                     the 40-point constraint minus user's known HCP and
                     other seats' minimum HCP).
        """
        hcp_max = self.hcp[1]
        if hcp_cap is not None:
            hcp_max = min(hcp_max, max(self.hcp[0], hcp_cap))
        return {
            'seat': self.seat,
            'hcp': {'min': self.hcp[0], 'max': hcp_max},
            'suits': {
                suit: {'min': r[0], 'max': r[1]}
                for suit, r in self.suits.items()
            },
            'limited': self.limited,
            'tags': list(self.tags),
            'reasoning': [
                {
                    'bid': step.bid,
                    'field': step.field,
                    'before': {'min': step.before[0], 'max': step.before[1]},
                    'after': {'min': step.after[0], 'max': step.after[1]},
                    'reason': step.reason,
                }
                for step in self.reasoning
            ],
        }


@dataclass
class BiddingState:
    """Per-seat belief model for all 4 seats."""

    beliefs: Dict[str, SeatBelief] = field(default_factory=lambda: {
        s: SeatBelief(seat=s) for s in SEATS
    })
    agreed_suits: Dict[str, Optional[str]] = field(default_factory=lambda: {
        'NS': None, 'EW': None
    })
    forcing: Dict[str, str] = field(default_factory=lambda: {
        'NS': 'none', 'EW': 'none'
    })
    dealer: str = 'N'

    def seat(self, s: str) -> SeatBelief:
        """Get belief for a seat."""
        return self.beliefs[normalize(s)]

    def partner_of(self, s: str) -> SeatBelief:
        return self.beliefs[partner(s)]

    def lho_of(self, s: str) -> SeatBelief:
        return self.beliefs[lho(s)]

    def rho_of(self, s: str) -> SeatBelief:
        return self.beliefs[rho(s)]

    def combined_hcp(self, seat1: str, seat2: str) -> Tuple[int, int]:
        """Combined HCP range for two seats."""
        b1, b2 = self.beliefs[normalize(seat1)], self.beliefs[normalize(seat2)]
        return (b1.hcp[0] + b2.hcp[0], b1.hcp[1] + b2.hcp[1])

    def partnership_hcp(self, s: str) -> Tuple[int, int]:
        """Combined HCP for the partnership containing seat s."""
        return self.combined_hcp(s, partner(s))

    def to_dict(self, my_seat: str, my_hcp: int = None) -> dict:
        """Serialize beliefs relative to a player's perspective.

        Returns partner, LHO, and RHO beliefs (not the player's own seat).
        When my_hcp is provided, each seat's max HCP is capped based on
        the known HCP total of 40 minus the user's HCP and the other
        seats' minimum HCP.
        """
        s = normalize(my_seat)
        partner_belief = self.partner_of(s)
        lho_belief = self.lho_of(s)
        rho_belief = self.rho_of(s)
        pship = partnership_str(s)

        others = [partner_belief, lho_belief, rho_belief]

        # Compute per-seat HCP caps from the 40-point constraint
        hcp_caps = {}
        if my_hcp is not None:
            for belief in others:
                # Max this seat can have = 40 - my HCP - other two seats' minimums
                other_mins = sum(b.hcp[0] for b in others if b is not belief)
                hcp_caps[belief.seat] = 40 - my_hcp - other_mins

        return {
            'partner': partner_belief.to_dict(hcp_cap=hcp_caps.get(partner_belief.seat)),
            'lho': lho_belief.to_dict(hcp_cap=hcp_caps.get(lho_belief.seat)),
            'rho': rho_belief.to_dict(hcp_cap=hcp_caps.get(rho_belief.seat)),
            'agreed_suit': self.agreed_suits.get(pship),
            'forcing': self.forcing.get(pship, 'none'),
        }


class BiddingStateBuilder:
    """Builds BiddingState by replaying auction_history bid-by-bid."""

    # Bid suit extraction helper
    SUIT_CHARS = set('♠♥♦♣')

    def build(self, auction_history: List[str], dealer: str) -> BiddingState:
        """Reconstruct full BiddingState from auction history."""
        dealer = normalize(dealer)
        state = BiddingState(dealer=dealer)

        opener_seat = None  # First non-Pass bidder
        opener_bid = None
        opening_found = False

        for i, bid in enumerate(auction_history):
            seat = active_seat_bidding(dealer, i)

            if bid == 'Pass':
                self._process_pass(state, seat, bid, i, opening_found, opener_seat, auction_history[:i])
                continue

            if bid in ('X', 'XX'):
                # Doubles/redoubles: process pass inference AND opponent bid narrowing
                self._process_pass(state, seat, bid, i, opening_found, opener_seat, auction_history[:i])
                if opening_found and opener_seat is not None:
                    is_opponent = seat != opener_seat and not is_partner(seat, opener_seat)
                    if is_opponent:
                        self._process_opponent_bid(state, seat, bid, opener_seat, auction_history[:i])
                continue

            if not opening_found:
                # This is the opening bid
                opener_seat = seat
                opener_bid = bid
                opening_found = True
                self._process_opening(state, seat, bid)
            else:
                # Determine if this is a response, rebid, or opponent bid
                partner_seat = partner(seat)
                is_partner_of_opener = (opener_seat == partner_seat)
                is_opener_rebidding = (seat == opener_seat)
                is_opponent = seat != opener_seat and not is_partner(seat, opener_seat)

                if is_opener_rebidding:
                    self._process_rebid(state, seat, bid, auction_history[:i])
                elif is_opponent:
                    self._process_opponent_bid(state, seat, bid, opener_seat, auction_history[:i])
                elif is_partner_of_opener and not self._has_bid_before(seat, auction_history[:i], dealer):
                    # First bid by opener's partner = response
                    self._process_response(state, seat, bid, opener_seat, opener_bid, auction_history[:i])
                else:
                    # Further bid by responder
                    self._process_rebid(state, seat, bid, auction_history[:i])

            # Convention narrowing (works for any bid)
            self._apply_convention_narrowing(state, seat, bid, opener_seat, auction_history[:i])

        return state

    def _has_bid_before(self, seat: str, prior_history: List[str], dealer: str) -> bool:
        """Check if this seat has made a non-Pass bid in prior history."""
        for j, prior_bid in enumerate(prior_history):
            if active_seat_bidding(dealer, j) == seat and prior_bid not in ('Pass', 'X', 'XX'):
                return True
        return False

    def _has_acted_before(self, seat: str, prior_history: List[str], dealer: str) -> bool:
        """Check if this seat has taken any action (bid or double) in prior history."""
        for j, prior_bid in enumerate(prior_history):
            if active_seat_bidding(dealer, j) == seat and prior_bid != 'Pass':
                return True
        return False

    def _parse_bid(self, bid: str) -> Tuple[Optional[int], Optional[str]]:
        """Parse a bid into (level, strain). Returns (None, None) for Pass/X/XX."""
        if bid in ('Pass', 'X', 'XX') or not bid:
            return (None, None)
        try:
            level = int(bid[0])
            strain = bid[1:]
            return (level, strain)
        except (ValueError, IndexError):
            return (None, None)

    def _bid_suit(self, bid: str) -> Optional[str]:
        """Extract suit character from bid, or None for NT/Pass."""
        level, strain = self._parse_bid(bid)
        if strain and len(strain) == 1 and strain in self.SUIT_CHARS:
            return strain
        return None

    # ──────────────────────────────────────────────────────────────
    # PASS INFERENCES
    # ──────────────────────────────────────────────────────────────

    def _process_pass(self, state: BiddingState, seat: str, bid: str,
                      bid_index: int, opening_found: bool, opener_seat: Optional[str],
                      prior: List[str]):
        if bid != 'Pass':
            return

        belief = state.seat(seat)

        if not opening_found:
            # Pass before anyone has opened
            passes_before = sum(1 for b in prior if b == 'Pass')
            if passes_before <= 1:
                belief.narrow_hcp(new_max=11, reason='Passed in opening seat → max 11 HCP', bid='Pass')
                belief.passed_opening = True
                belief.add_tag('passed_opening')
            else:
                belief.narrow_hcp(new_max=13, reason='Passed in 3rd/4th seat → max 13 HCP', bid='Pass')
                belief.passed_opening = True
                belief.add_tag('passed_late')
        elif opener_seat is not None and partner(seat) == opener_seat:
            # Responder passes partner's opening
            has_interference = any(
                prior[j] not in ('Pass', 'X', 'XX') and not is_partner(active_seat_bidding(state.dealer, j), opener_seat)
                for j in range(len(prior))
                if j > 0
            )
            if not has_interference:
                belief.narrow_hcp(new_max=5, reason="Passed partner's opening → max 5 HCP", bid='Pass')
                belief.limited = True
                belief.add_tag('passed_response')
            else:
                belief.narrow_hcp(new_max=8, reason='Passed over interference → max 8 HCP (may be trapping)', bid='Pass')
                belief.add_tag('passed_over_interference')
        elif opener_seat is not None and seat != opener_seat:
            # Pass by someone other than the opener — check relationships
            partner_seat = partner(seat)
            partner_has_bid = self._has_acted_before(partner_seat, prior, state.dealer)
            is_on_opening_side = is_partner(seat, opener_seat)

            if partner_has_bid and not is_on_opening_side:
                # Partner overcalled/bid, this player passes → limited hand
                # Can't raise or support partner's competitive action
                belief.narrow_hcp(new_max=8, reason="Passed partner's overcall → max 8 HCP (couldn't raise)", bid='Pass')
                belief.limited = True
                belief.add_tag('passed_overcall')
            elif not partner_has_bid and is_on_opening_side:
                # Opener's partner passes after opponent interference
                # Already handled above (partner(seat) == opener_seat case)
                pass
            elif not partner_has_bid and not is_on_opening_side:
                # Opponent side: this player couldn't overcall or act
                # Only infer if they haven't bid yet (first pass after opening)
                if not self._has_bid_before(seat, prior, state.dealer):
                    belief.narrow_hcp(new_max=16, reason="Passed over opening → couldn't overcall (likely ≤16 HCP)", bid='Pass')
                    belief.add_tag('passed_over_opening')

    # ──────────────────────────────────────────────────────────────
    # OPENING BIDS
    # ──────────────────────────────────────────────────────────────

    def _process_opening(self, state: BiddingState, seat: str, bid: str):
        belief = state.seat(seat)
        level, strain = self._parse_bid(bid)

        if level is None:
            return

        if bid == '1NT':
            belief.narrow_hcp(new_min=15, new_max=17, reason='1NT opening → 15-17 HCP', bid=bid)
            belief.narrow_suit('♥', new_max=4, reason='1NT opening → no 5-card major', bid=bid)
            belief.narrow_suit('♠', new_max=4, reason='1NT opening → no 5-card major', bid=bid)
            belief.add_tag('opened_1nt')
            belief.add_tag('balanced')
        elif bid == '2NT':
            belief.narrow_hcp(new_min=20, new_max=21, reason='2NT opening → 20-21 HCP', bid=bid)
            belief.narrow_suit('♥', new_max=4, reason='2NT opening → balanced, no 5-card major', bid=bid)
            belief.narrow_suit('♠', new_max=4, reason='2NT opening → balanced, no 5-card major', bid=bid)
            belief.add_tag('opened_2nt')
            belief.add_tag('balanced')
        elif bid == '2♣':
            belief.narrow_hcp(new_min=22, reason='2♣ opening → 22+ HCP (strong)', bid=bid)
            belief.add_tag('strong_2c')
            state.forcing[partnership_str(seat)] = 'game'
        elif level == 2 and strain in self.SUIT_CHARS:
            belief.narrow_hcp(new_min=6, new_max=10, reason=f'Weak 2{strain} → 6-10 HCP', bid=bid)
            belief.narrow_suit(strain, new_min=6, new_max=6, reason=f'Weak 2{strain} → exactly 6 cards', bid=bid)
            belief.limited = True
            belief.add_tag('weak_two')
        elif level == 1 and strain in ('♥', '♠'):
            belief.narrow_hcp(new_min=12, new_max=21, reason=f'1{strain} opening → 12-21 HCP', bid=bid)
            belief.narrow_suit(strain, new_min=5, reason=f'1{strain} opening → 5+ {strain}', bid=bid)
            belief.add_tag('opened_major')
        elif level == 1 and strain in ('♣', '♦'):
            belief.narrow_hcp(new_min=12, new_max=21, reason=f'1{strain} opening → 12-21 HCP', bid=bid)
            belief.narrow_suit(strain, new_min=3, reason=f'1{strain} opening → 3+ {strain}', bid=bid)
            belief.add_tag('opened_minor')
        elif level == 3 and strain in self.SUIT_CHARS:
            belief.narrow_hcp(new_min=6, new_max=10, reason=f'3{strain} preempt → 6-10 HCP', bid=bid)
            belief.narrow_suit(strain, new_min=7, reason=f'3{strain} preempt → 7+ {strain}', bid=bid)
            belief.limited = True
            belief.add_tag('preempt')
        elif level >= 4 and strain in self.SUIT_CHARS:
            belief.narrow_hcp(new_min=6, new_max=10, reason=f'{bid} preempt → 6-10 HCP', bid=bid)
            belief.narrow_suit(strain, new_min=7, reason=f'{bid} preempt → 7+ {strain}', bid=bid)
            belief.limited = True
            belief.add_tag('preempt')

    # ──────────────────────────────────────────────────────────────
    # RESPONSES TO PARTNER'S OPENING
    # ──────────────────────────────────────────────────────────────

    def _process_response(self, state: BiddingState, seat: str, bid: str,
                          opener_seat: str, opener_bid: str, prior: List[str]):
        belief = state.seat(seat)
        level, strain = self._parse_bid(bid)
        o_level, o_strain = self._parse_bid(opener_bid)

        if level is None:
            return

        suit = self._bid_suit(bid)
        opener_suit = self._bid_suit(opener_bid)

        # Check if this is a raise (same suit as opener)
        is_raise = (suit is not None and suit == opener_suit)

        if bid == '1NT':
            belief.narrow_hcp(new_min=6, new_max=10, reason=f'1NT response to {opener_bid} → 6-10 HCP', bid=bid)
            belief.limited = True
            belief.add_tag('responded_1nt')
        elif bid == '2NT':
            belief.narrow_hcp(new_min=13, new_max=15, reason=f'2NT response to {opener_bid} → 13-15 HCP', bid=bid)
            belief.add_tag('responded_2nt')
        elif bid == '3NT':
            belief.narrow_hcp(new_min=16, new_max=18, reason=f'3NT response to {opener_bid} → 16-18 HCP balanced', bid=bid)
            belief.add_tag('responded_3nt')
        elif is_raise and level == o_level + 1:
            belief.narrow_hcp(new_min=6, new_max=10, reason=f'Simple raise ({bid}) → 6-10 HCP', bid=bid)
            if suit:
                belief.narrow_suit(suit, new_min=3, reason=f'Simple raise → 3+ {suit} support', bid=bid)
            belief.limited = True
            belief.add_tag('simple_raise')
            if suit:
                state.agreed_suits[partnership_str(seat)] = suit
        elif is_raise and level == o_level + 2:
            belief.narrow_hcp(new_min=10, new_max=12, reason=f'Limit raise ({bid}) → 10-12 HCP invitational', bid=bid)
            if suit:
                belief.narrow_suit(suit, new_min=3, reason=f'Limit raise → 3+ {suit} support', bid=bid)
            belief.limited = True
            belief.add_tag('limit_raise')
            if suit:
                state.agreed_suits[partnership_str(seat)] = suit
        elif is_raise and level >= o_level + 3:
            belief.narrow_hcp(new_min=6, new_max=10, reason=f'Preemptive raise ({bid}) → 6-10 HCP', bid=bid)
            if suit:
                belief.narrow_suit(suit, new_min=5, reason=f'Preemptive raise → 5+ {suit} support', bid=bid)
            belief.limited = True
            belief.add_tag('preemptive_raise')
            if suit:
                state.agreed_suits[partnership_str(seat)] = suit
        elif level == 1 and suit:
            belief.narrow_hcp(new_min=6, reason=f'New suit at 1 level ({bid}) → 6+ HCP', bid=bid)
            belief.narrow_suit(suit, new_min=4, reason=f'{bid} response → 4+ {suit}', bid=bid)
            belief.add_tag('new_suit_1_level')
        elif level == 2 and suit and not is_raise:
            belief.narrow_hcp(new_min=10, reason=f'New suit at 2 level ({bid}) → 10+ HCP', bid=bid)
            belief.narrow_suit(suit, new_min=5, reason=f'{bid} response → 5+ {suit}', bid=bid)
            belief.add_tag('new_suit_2_level')
            if o_level == 1 and o_strain in ('♥', '♠'):
                state.forcing[partnership_str(seat)] = 'game'
                belief.add_tag('two_over_one_gf')

    # ──────────────────────────────────────────────────────────────
    # REBIDS (opener or responder rebidding)
    # ──────────────────────────────────────────────────────────────

    def _process_rebid(self, state: BiddingState, seat: str, bid: str, prior: List[str]):
        """Process a rebid by opener or subsequent bid by responder."""
        belief = state.seat(seat)
        level, strain = self._parse_bid(bid)
        suit = self._bid_suit(bid)

        if level is None:
            return

        # If rebidding own suit, shows extra length
        if suit:
            for j, prev_bid in enumerate(prior):
                prev_seat = active_seat_bidding(state.dealer, j)
                if prev_seat == seat:
                    prev_suit = self._bid_suit(prev_bid)
                    if prev_suit == suit:
                        belief.narrow_suit(suit, new_min=6, reason=f'Rebid {suit} → 6+ cards in {suit}', bid=bid)
                        belief.add_tag('rebid_own_suit')
                        break

        # NT rebid shows balanced-ish and limits
        if strain == 'NT':
            if level == 1:
                belief.narrow_hcp(new_min=12, new_max=14, reason='1NT rebid → 12-14 HCP balanced', bid=bid)
                belief.limited = True
                belief.add_tag('rebid_1nt')
            elif level == 2:
                belief.narrow_hcp(new_min=18, new_max=19, reason='2NT rebid → 18-19 HCP', bid=bid)
                belief.add_tag('rebid_2nt')
            elif level == 3:
                belief.narrow_hcp(new_min=18, new_max=19, reason='3NT rebid → 18-19 HCP', bid=bid)
                belief.add_tag('rebid_3nt')

    # ──────────────────────────────────────────────────────────────
    # OPPONENT BIDS
    # ──────────────────────────────────────────────────────────────

    def _process_opponent_bid(self, state: BiddingState, seat: str, bid: str,
                              opener_seat: str, prior: List[str]):
        belief = state.seat(seat)
        level, strain = self._parse_bid(bid)
        suit = self._bid_suit(bid)

        if bid == 'X':
            belief.narrow_hcp(new_min=12, reason='Takeout double → 12+ HCP', bid='X')
            belief.add_tag('takeout_double')
            opener_belief = state.seat(opener_seat)
            for tag in opener_belief.tags:
                if tag.startswith('opened_') or tag == 'weak_two' or tag == 'preempt':
                    for s in SUITS:
                        if opener_belief.suits[s][0] >= 5:
                            belief.narrow_suit(s, new_max=2, reason=f'Takeout double → short in opponents\' {s}', bid='X')
                            break
                    break
            bid_suits = set()
            for j, prev_bid in enumerate(prior):
                ps = self._bid_suit(prev_bid)
                if ps:
                    bid_suits.add(ps)
            for s in SUITS:
                if s not in bid_suits:
                    belief.narrow_suit(s, new_min=3, reason=f'Takeout double → 3+ in unbid {s}', bid='X')
            return

        if level is None:
            return

        # Check if this is a jump overcall (weak) vs simple overcall
        # Simple overcall: bid at cheapest legal level
        if suit:
            # Determine cheapest legal level for this suit
            suit_rank = {'♣': 1, '♦': 2, '♥': 3, '♠': 4}
            is_jump = False
            last_real_level = 0
            last_real_suit = None
            for prev_bid in reversed(prior):
                pl, ps = self._parse_bid(prev_bid)
                if pl is not None:
                    last_real_level = pl
                    last_real_suit = self._bid_suit(prev_bid)
                    break
            # Cheapest legal level: same level if our suit outranks, else +1
            if last_real_level > 0:
                last_suit_rank = suit_rank.get(last_real_suit, 0)
                my_suit_rank = suit_rank.get(suit, 0)
                min_level = last_real_level if my_suit_rank > last_suit_rank else last_real_level + 1
            else:
                min_level = 1
            if level > min_level:
                is_jump = True

            if is_jump:
                belief.narrow_hcp(new_min=6, new_max=10, reason=f'Weak jump overcall ({bid}) → 6-10 HCP', bid=bid)
                belief.narrow_suit(suit, new_min=6, reason=f'Weak jump overcall → 6+ {suit}', bid=bid)
                belief.limited = True
                belief.add_tag('weak_jump_overcall')
            elif level == 1:
                belief.narrow_hcp(new_min=8, new_max=16, reason=f'1-level overcall ({bid}) → 8-16 HCP', bid=bid)
                belief.narrow_suit(suit, new_min=5, reason=f'1-level overcall → 5+ {suit}', bid=bid)
                belief.add_tag('overcall_1_level')
            elif level == 2:
                belief.narrow_hcp(new_min=11, new_max=16, reason=f'2-level overcall ({bid}) → 11-16 HCP', bid=bid)
                belief.narrow_suit(suit, new_min=5, reason=f'2-level overcall → 5+ {suit}', bid=bid)
                belief.add_tag('overcall_2_level')
            else:
                belief.narrow_suit(suit, new_min=5, reason=f'High-level overcall ({bid}) → 5+ {suit}', bid=bid)
                belief.add_tag('overcall_high')

    # ──────────────────────────────────────────────────────────────
    # CONVENTION NARROWING
    # ──────────────────────────────────────────────────────────────

    def _apply_convention_narrowing(self, state: BiddingState, seat: str, bid: str,
                                    opener_seat: Optional[str], prior: List[str]):
        """Apply convention-specific narrowing after a bid."""
        if not prior:
            return

        level, strain = self._parse_bid(bid)
        partner_seat = partner(seat)

        # Find partner's last bid
        partner_last_bid = None
        for j in range(len(prior) - 1, -1, -1):
            if active_seat_bidding(state.dealer, j) == partner_seat:
                partner_last_bid = prior[j]
                break

        if not partner_last_bid:
            return

        # ── Stayman: 2♣ over partner's 1NT ──
        if bid == '2♣' and partner_last_bid == '1NT':
            belief = state.seat(seat)
            belief.narrow_hcp(new_min=8, reason='Stayman (2♣) → 8+ HCP', bid=bid)
            belief.add_tag('stayman_asked')

        # ── Stayman responses: partner bid 2♣ (Stayman) over our 1NT ──
        partner_belief = state.seat(partner_seat)
        if partner_belief.has_tag('stayman_asked') and state.seat(seat).has_tag('opened_1nt'):
            belief = state.seat(seat)
            if bid == '2♦':
                belief.narrow_suit('♥', new_max=3, reason='2♦ Stayman denial → no 4-card ♥', bid=bid)
                belief.narrow_suit('♠', new_max=3, reason='2♦ Stayman denial → no 4-card ♠', bid=bid)
                belief.add_tag('stayman_no_major')
            elif bid == '2♥':
                belief.narrow_suit('♥', new_min=4, reason='2♥ Stayman response → 4+ ♥', bid=bid)
                belief.add_tag('stayman_hearts')
            elif bid == '2♠':
                belief.narrow_suit('♠', new_min=4, reason='2♠ Stayman response → 4+ ♠', bid=bid)
                belief.add_tag('stayman_spades')

        # ── Jacoby Transfer: 2♦ or 2♥ over partner's 1NT ──
        if partner_last_bid == '1NT':
            belief = state.seat(seat)
            if bid == '2♦':
                belief.narrow_suit('♥', new_min=5, reason='Jacoby transfer (2♦) → 5+ ♥', bid=bid)
                belief.add_tag('jacoby_hearts')
            elif bid == '2♥':
                belief.narrow_suit('♠', new_min=5, reason='Jacoby transfer (2♥) → 5+ ♠', bid=bid)
                belief.add_tag('jacoby_spades')

        # ── Transfer completion: partner asked for transfer, we complete ──
        if partner_belief.has_tag('jacoby_hearts') and bid == '2♥':
            state.seat(seat).add_tag('transfer_completed')
        elif partner_belief.has_tag('jacoby_spades') and bid == '2♠':
            state.seat(seat).add_tag('transfer_completed')

        # ── Blackwood: 4NT when agreed suit exists ──
        if bid == '4NT':
            pship = partnership_str(seat)
            if state.agreed_suits.get(pship) or state.forcing.get(pship) == 'game':
                state.seat(seat).add_tag('blackwood_asked')

        # ── Blackwood response ──
        if partner_belief.has_tag('blackwood_asked') and level == 5:
            belief = state.seat(seat)
            ace_map = {'♣': 0, '♦': 1, '♥': 2, '♠': 3}
            if strain in ace_map:
                aces = ace_map[strain]
                # 0 or 4 aces for ♣, 1 for ♦, 2 for ♥, 3 for ♠
                belief.add_tag(f'blackwood_{aces}_aces')
            belief.add_tag('blackwood_response')
