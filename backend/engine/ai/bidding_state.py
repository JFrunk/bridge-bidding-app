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

    def to_dict(self, hcp_cap: int = None, hcp_min_override: int = None,
                suit_caps: Dict[str, int] = None) -> dict:
        """Serialize belief for API/frontend consumption.

        Args:
            hcp_cap: If provided, caps max HCP at this value (derived from
                     the 40-point constraint minus user's known HCP and
                     other seats' minimum HCP).
            hcp_min_override: If provided, overrides the min HCP value.
                     Used when the sum of all minimums exceeds the available
                     HCP and proportional reduction is needed.
            suit_caps: If provided, dict mapping suit → max length cap
                       (derived from 13-card constraint minus user's own
                       suit lengths and other seats' minimum lengths).
        """
        # Apply min override if provided (used for over-allocation correction)
        hcp_min = self.hcp[0] if hcp_min_override is None else hcp_min_override
        hcp_max = self.hcp[1]

        # Apply max cap
        if hcp_cap is not None:
            hcp_max = min(hcp_max, max(hcp_min, hcp_cap))

        # Ensure min doesn't exceed max after adjustments
        if hcp_min > hcp_max:
            hcp_min = hcp_max

        suits_out = {}
        for suit, r in self.suits.items():
            s_min, s_max = r
            if suit_caps and suit in suit_caps:
                s_max = min(s_max, max(s_min, suit_caps[suit]))
            suits_out[suit] = {'min': s_min, 'max': s_max}

        return {
            'seat': self.seat,
            'hcp': {'min': hcp_min, 'max': hcp_max},
            'suits': suits_out,
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

    def to_dict(self, my_seat: str, my_hcp: int = None,
                my_suit_lengths: Dict[str, int] = None) -> dict:
        """Serialize beliefs relative to a player's perspective.

        Returns partner, LHO, and RHO beliefs (not the player's own seat).
        When my_hcp is provided:
        1. Each seat's max HCP is capped based on the 40-point constraint
        2. Global validation ensures sum(all_mins) <= 40 - my_hcp
        3. Global validation ensures sum(all_maxes) <= 40 - my_hcp
        When my_suit_lengths is provided, each seat's max suit length is
        capped based on the 13-card constraint minus the user's own suit
        lengths and other seats' minimum lengths.
        """
        s = normalize(my_seat)
        partner_belief = self.partner_of(s)
        lho_belief = self.lho_of(s)
        rho_belief = self.rho_of(s)
        pship = partnership_str(s)

        others = [partner_belief, lho_belief, rho_belief]

        # Compute HCP adjustments from the 40-point constraint
        hcp_caps = {}
        hcp_min_adjustments = {}  # Track if we need to adjust minimums
        if my_hcp is not None:
            available_hcp = 40 - my_hcp

            # Step 1: Check if sum of minimums exceeds available HCP
            total_mins = sum(b.hcp[0] for b in others)
            if total_mins > available_hcp:
                # CRITICAL: Minimums over-allocated. Need to reduce them.
                # This indicates conflicting inferences that can't all be true.
                # Strategy: Proportionally reduce each seat's min based on their share
                excess = total_mins - available_hcp
                for belief in others:
                    if total_mins > 0:
                        # Reduce each min proportionally to its contribution
                        reduction = int((belief.hcp[0] / total_mins) * excess + 0.5)
                        new_min = max(0, belief.hcp[0] - reduction)
                        hcp_min_adjustments[belief.seat] = new_min
                    else:
                        hcp_min_adjustments[belief.seat] = belief.hcp[0]
                logger.debug(f"HCP over-allocation: total mins {total_mins} > available {available_hcp}. "
                             f"Adjustments: {hcp_min_adjustments}")

            # Step 2: Compute per-seat max caps
            for belief in others:
                # Use adjusted mins if available, otherwise original mins
                other_mins = sum(
                    hcp_min_adjustments.get(b.seat, b.hcp[0])
                    for b in others if b is not belief
                )
                hcp_caps[belief.seat] = available_hcp - other_mins

            # Step 3: Ensure sum of maxes doesn't exceed available HCP
            # First compute what the capped maxes would be
            capped_maxes = {}
            for belief in others:
                belief_min = hcp_min_adjustments.get(belief.seat, belief.hcp[0])
                cap = hcp_caps.get(belief.seat, belief.hcp[1])
                capped_max = min(belief.hcp[1], max(belief_min, cap))
                capped_maxes[belief.seat] = capped_max

            # Check if sum of capped maxes still exceeds available
            total_maxes = sum(capped_maxes.values())
            if total_maxes > available_hcp:
                # Reduce maxes to fit within budget.
                # Strategy: Preserve bid-derived ranges, distribute remaining HCP
                # evenly among unconstrained seats.
                excess = total_maxes - available_hcp

                # Compute priority for each seat:
                # 0 = bid-derived (has tags from actual bids) - preserve
                # 1 = pass-inferred (has pass tags) - reduce second
                # 2 = unconstrained (no tags) - reduce first (distribute evenly)
                def get_reduction_priority(belief):
                    if not belief.tags:
                        return 2  # Unconstrained - reduce first
                    # Check for pass-derived tags
                    pass_tags = {'passed_opening', 'passed_late', 'passed_response',
                                 'passed_over_interference', 'passed_overcall',
                                 'passed_over_opening'}
                    if all(t in pass_tags for t in belief.tags):
                        return 1  # Pass-inferred only - reduce second
                    return 0  # Has bid-derived tags - preserve

                # Create list with priority info
                seats_info = []
                for belief in others:
                    belief_min = hcp_min_adjustments.get(belief.seat, belief.hcp[0])
                    seats_info.append({
                        'seat': belief.seat,
                        'max': capped_maxes[belief.seat],
                        'min': belief_min,
                        'range': capped_maxes[belief.seat] - belief_min,
                        'priority': get_reduction_priority(belief),
                    })

                # Group by priority
                priority_groups = {}
                for info in seats_info:
                    p = info['priority']
                    if p not in priority_groups:
                        priority_groups[p] = []
                    priority_groups[p].append(info)

                # Process priority groups from highest (reduce first) to lowest
                for priority in sorted(priority_groups.keys(), reverse=True):
                    if excess <= 0:
                        break
                    group = priority_groups[priority]

                    # Calculate total reducible in this group
                    total_reducible = sum(info['max'] - info['min'] for info in group)

                    if total_reducible == 0:
                        continue

                    # For same-priority seats, distribute reduction proportionally
                    # to their current max values (fairer distribution)
                    group_excess = min(excess, total_reducible)

                    # Calculate proportional reduction for each seat in group
                    total_max_in_group = sum(info['max'] for info in group)
                    if total_max_in_group > 0:
                        for info in group:
                            # Proportional share of reduction
                            share = info['max'] / total_max_in_group
                            reduction = int(share * group_excess + 0.5)
                            # Don't reduce below min
                            actual_reduction = min(reduction, info['max'] - info['min'])
                            info['max'] -= actual_reduction
                            excess -= actual_reduction

                # Apply final caps
                for info in seats_info:
                    hcp_caps[info['seat']] = info['max']

                logger.debug(f"HCP max over-allocation: total maxes {total_maxes} > available {available_hcp}. "
                             f"Final caps: {hcp_caps}")

        # Compute per-seat suit length caps from the 13-card constraint
        suit_caps_per_seat = {}
        if my_suit_lengths is not None:
            for belief in others:
                caps = {}
                for suit in SUITS:
                    my_len = my_suit_lengths.get(suit, 0)
                    # Other two seats' minimum lengths in this suit
                    other_mins = sum(
                        b.suits[suit][0] for b in others if b is not belief
                    )
                    caps[suit] = 13 - my_len - other_mins
                suit_caps_per_seat[belief.seat] = caps

        # Build diagnostic info about HCP constraint validation
        hcp_diagnostic = None
        if my_hcp is not None:
            available_hcp = 40 - my_hcp
            # Compute final totals after all adjustments
            partner_dict = partner_belief.to_dict(
                hcp_cap=hcp_caps.get(partner_belief.seat),
                hcp_min_override=hcp_min_adjustments.get(partner_belief.seat),
                suit_caps=suit_caps_per_seat.get(partner_belief.seat))
            lho_dict = lho_belief.to_dict(
                hcp_cap=hcp_caps.get(lho_belief.seat),
                hcp_min_override=hcp_min_adjustments.get(lho_belief.seat),
                suit_caps=suit_caps_per_seat.get(lho_belief.seat))
            rho_dict = rho_belief.to_dict(
                hcp_cap=hcp_caps.get(rho_belief.seat),
                hcp_min_override=hcp_min_adjustments.get(rho_belief.seat),
                suit_caps=suit_caps_per_seat.get(rho_belief.seat))

            final_min_sum = (partner_dict['hcp']['min'] + lho_dict['hcp']['min'] +
                             rho_dict['hcp']['min'])
            final_max_sum = (partner_dict['hcp']['max'] + lho_dict['hcp']['max'] +
                             rho_dict['hcp']['max'])

            original_min_sum = sum(b.hcp[0] for b in others)
            original_max_sum = sum(b.hcp[1] for b in others)

            hcp_diagnostic = {
                'user_hcp': my_hcp,
                'available_hcp': available_hcp,
                'min_sum': final_min_sum,
                'max_sum': final_max_sum,
                'original_min_sum': original_min_sum,
                'original_max_sum': original_max_sum,
                'min_corrected': bool(hcp_min_adjustments),
                'constraint_satisfied': final_min_sum <= available_hcp and final_max_sum <= available_hcp,
            }

            return {
                'partner': partner_dict,
                'lho': lho_dict,
                'rho': rho_dict,
                'agreed_suit': self.agreed_suits.get(pship),
                'forcing': self.forcing.get(pship, 'none'),
                'hcp_constraint': hcp_diagnostic,
            }

        return {
            'partner': partner_belief.to_dict(
                hcp_cap=hcp_caps.get(partner_belief.seat),
                hcp_min_override=hcp_min_adjustments.get(partner_belief.seat),
                suit_caps=suit_caps_per_seat.get(partner_belief.seat)),
            'lho': lho_belief.to_dict(
                hcp_cap=hcp_caps.get(lho_belief.seat),
                hcp_min_override=hcp_min_adjustments.get(lho_belief.seat),
                suit_caps=suit_caps_per_seat.get(lho_belief.seat)),
            'rho': rho_belief.to_dict(
                hcp_cap=hcp_caps.get(rho_belief.seat),
                hcp_min_override=hcp_min_adjustments.get(rho_belief.seat),
                suit_caps=suit_caps_per_seat.get(rho_belief.seat)),
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

    def _is_on_opening_side(self, seat: str, opener_seat: str) -> bool:
        """Check if seat is the opener or opener's partner."""
        return seat == opener_seat or is_partner(seat, opener_seat)

    def _has_opponent_interference(self, opener_seat: str, prior: List[str], dealer: str) -> bool:
        """Check if any opponent (non-opening-side) made a real bid in prior history."""
        for j, prev_bid in enumerate(prior):
            if prev_bid in ('Pass', 'X', 'XX'):
                continue
            bidder = active_seat_bidding(dealer, j)
            if not self._is_on_opening_side(bidder, opener_seat):
                return True
        return False

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
            return

        if opener_seat is None:
            return

        is_opener = (seat == opener_seat)
        is_responder = (partner(seat) == opener_seat)
        on_opening_side = is_opener or is_responder
        has_bid = self._has_bid_before(seat, prior, state.dealer)

        # ── Case 1: Responder's FIRST pass (hasn't bid yet) ──
        if is_responder and not has_bid:
            has_interference = self._has_opponent_interference(opener_seat, prior, state.dealer)
            if not has_interference:
                belief.narrow_hcp(new_max=5, reason="Passed partner's opening → max 5 HCP", bid='Pass')
                belief.limited = True
                belief.add_tag('passed_response')
            else:
                belief.narrow_hcp(new_max=8, reason='Passed over interference → max 8 HCP (may be trapping)', bid='Pass')
                belief.add_tag('passed_over_interference')

        # ── Case 2: Responder passes AFTER having already bid ──
        elif is_responder and has_bid:
            # If already limited, no further narrowing needed
            if not belief.limited:
                # Responder passing a non-forcing rebid → minimum for what they showed
                # new_suit_1_level: was 6+, now 6-9 (couldn't push to game)
                if belief.has_tag('new_suit_1_level'):
                    belief.narrow_hcp(new_max=9, reason="Passed opener's rebid → minimum (6-9 HCP)", bid='Pass')
                    belief.limited = True
                    belief.add_tag('minimum_response')
                elif belief.has_tag('new_suit_2_level') and not belief.has_tag('two_over_one_gf'):
                    belief.narrow_hcp(new_max=12, reason="Passed opener's rebid → minimum 2-level response (10-12 HCP)", bid='Pass')
                    belief.limited = True
                    belief.add_tag('minimum_response')

        # ── Case 3: Opener passes AFTER having bid ──
        elif is_opener and has_bid:
            if not belief.limited:
                # Opener passing = minimum, no extras
                # Check what responder showed to determine context
                partner_belief = state.seat(partner(seat))

                if partner_belief.has_tag('limit_raise'):
                    # Declined limit raise invitation → minimum opener (12-14)
                    belief.narrow_hcp(new_max=14, reason='Declined limit raise → minimum opener (12-14 HCP)', bid='Pass')
                    belief.limited = True
                    belief.add_tag('declined_invite')
                elif partner_belief.has_tag('simple_raise'):
                    # Passed simple raise → minimum opener (12-14)
                    belief.narrow_hcp(new_max=14, reason='Passed simple raise → minimum opener (12-14 HCP)', bid='Pass')
                    belief.limited = True
                    belief.add_tag('minimum_opener')
                elif partner_belief.has_tag('responded_1nt'):
                    # Passed 1NT response → minimum opener (12-14)
                    belief.narrow_hcp(new_max=14, reason='Passed 1NT response → minimum opener (12-14 HCP)', bid='Pass')
                    belief.limited = True
                    belief.add_tag('minimum_opener')
                elif partner_belief.has_tag('new_suit_1_level') or partner_belief.has_tag('new_suit_2_level'):
                    # Passed a new suit response (forcing) → unusual, but implies minimum
                    belief.narrow_hcp(new_max=14, reason='Passed forcing response → minimum opener (12-14 HCP)', bid='Pass')
                    belief.limited = True
                    belief.add_tag('minimum_opener')
                elif belief.hcp[1] - belief.hcp[0] > 5:
                    # Wide range and passing → likely minimum
                    belief.narrow_hcp(new_max=belief.hcp[0] + 3,
                                      reason=f'Passed → near-minimum ({belief.hcp[0]}-{belief.hcp[0]+3} HCP)', bid='Pass')
                    belief.limited = True
                    belief.add_tag('minimum_opener')

        # ── Case 4: Opponent side passes ──
        elif not on_opening_side:
            partner_seat = partner(seat)
            partner_has_acted = self._has_acted_before(partner_seat, prior, state.dealer)

            if partner_has_acted:
                # Partner overcalled/doubled, this player passes → limited hand
                if not has_bid:
                    belief.narrow_hcp(new_max=8, reason="Passed partner's overcall → max 8 HCP (couldn't raise)", bid='Pass')
                    belief.limited = True
                    belief.add_tag('passed_overcall')
            elif not has_bid:
                # Opponent side: couldn't overcall or act
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
            for s in SUITS:
                belief.narrow_suit(s, new_min=2, reason='1NT opening → balanced, 2+ in every suit', bid=bid)
            belief.narrow_suit('♥', new_max=4, reason='1NT opening → no 5-card major', bid=bid)
            belief.narrow_suit('♠', new_max=4, reason='1NT opening → no 5-card major', bid=bid)
            belief.narrow_suit('♣', new_max=5, reason='1NT opening → balanced, max 5 in minor', bid=bid)
            belief.narrow_suit('♦', new_max=5, reason='1NT opening → balanced, max 5 in minor', bid=bid)
            belief.add_tag('opened_1nt')
            belief.add_tag('balanced')
        elif bid == '2NT':
            belief.narrow_hcp(new_min=20, new_max=21, reason='2NT opening → 20-21 HCP', bid=bid)
            for s in SUITS:
                belief.narrow_suit(s, new_min=2, reason='2NT opening → balanced, 2+ in every suit', bid=bid)
            belief.narrow_suit('♥', new_max=4, reason='2NT opening → balanced, no 5-card major', bid=bid)
            belief.narrow_suit('♠', new_max=4, reason='2NT opening → balanced, no 5-card major', bid=bid)
            belief.narrow_suit('♣', new_max=5, reason='2NT opening → balanced, max 5 in minor', bid=bid)
            belief.narrow_suit('♦', new_max=5, reason='2NT opening → balanced, max 5 in minor', bid=bid)
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
        elif opener_bid in ('1NT', '2NT') and level == 2 and suit in ('♣', '♦', '♥'):
            # Convention responses to NT opening (Stayman, Jacoby transfers)
            # HCP/suit narrowing handled by _apply_convention_narrowing
            # Don't apply standard new-suit 10+ HCP rules
            pass
        elif level == 2 and suit and not is_raise:
            # Check if there was opponent interference between opening and this response
            has_interference = self._has_opponent_interference(opener_seat, prior, state.dealer)
            if has_interference:
                # Competitive: new suit after interference is just showing suit, not 2/1 GF
                belief.narrow_hcp(new_min=6, reason=f'New suit at 2 level after interference ({bid}) → 6+ HCP (competitive)', bid=bid)
                belief.narrow_suit(suit, new_min=5, reason=f'{bid} response → 5+ {suit}', bid=bid)
                belief.add_tag('new_suit_2_level')
                belief.add_tag('competitive_response')
            else:
                # Standard 2/1: 10+ HCP, potentially game forcing over major
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
