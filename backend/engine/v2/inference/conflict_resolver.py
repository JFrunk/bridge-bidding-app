"""
Conflict Resolver - Monte Carlo Integration for Bid Validation

This module provides a "judgment layer" that can veto or modify bids
proposed by the schema engine based on simulation results.

The resolver prevents "suicide bids" by:
1. Never vetoing Artificial/Systemic bids (Tier I, priority >= 800)
2. Validating slam bids against expected trick counts
3. Evaluating competitive decisions (bid vs. double)

Note: Structural validation (fit/LTC/stopper gates) is handled by
validate_bid_structure() in this module, called from the engine's
candidate selection loop before bids reach review_bid().

Usage:
    resolver = ConflictResolver(simulator)
    final_bid = resolver.review_bid(proposed_rule, hand, history, features)
"""

from typing import Dict, Any, Optional, Tuple
from engine.hand import Hand

import logging
logger = logging.getLogger(__name__)

# Telemetry counters — reset via reset_structural_vetoes(), read via get_structural_vetoes()
_structural_vetoes = {'4M_fit': 0, '4M_ltc': 0, '3NT_stoppers': 0, 'origin': 0}


def reset_structural_vetoes():
    """Reset veto counters. Call before a quality run."""
    _structural_vetoes['4M_fit'] = 0
    _structural_vetoes['4M_ltc'] = 0
    _structural_vetoes['3NT_stoppers'] = 0
    _structural_vetoes['origin'] = 0


def get_structural_vetoes() -> dict:
    """Return a copy of veto counters."""
    return dict(_structural_vetoes)


def validate_bid_structure(bid: str, priority: int, features: Dict[str, Any]) -> bool:
    """
    Structural filter: hard-stop for game/NT bids missing prerequisites.

    Called from the engine's candidate loop BEFORE conflict resolution.
    Returns True if bid passes structural checks, False to reject.

    Rules:
      - 4♥/4♠: requires partnership_fit >= 8 AND partnership_ltc <= 14
      - 3NT: requires partnership_stoppers >= 3
      - Artificial bids (priority >= 800) are exempt UNLESS they commit
        to 4♥/4♠ without an established fit (fit_known=false)
      - Pass/X/XX are always allowed
    """
    if not bid or bid in ('Pass', 'X', 'XX'):
        return True

    bid_level = int(bid[0]) if bid[0].isdigit() else 0
    bid_strain = bid[1:] if len(bid) > 1 else ''

    # ORIGIN GATE: Convention bids (priority >= 800) cannot be responses to
    # an opponent's bid.  You can only "respond" to a convention that partner
    # started.  This kills Ghost Gerber / Ghost Blackwood misfires where an
    # opponent's natural 4♣ or 4NT is misinterpreted as a convention ask.
    last_bid_side = features.get('last_bid_side')
    if priority >= 800 and last_bid_side == 'opponent':
        _structural_vetoes['origin'] += 1
        msg = f"🚫 VETO ORIGIN: {bid} rejected (convention response to opponent's bid)"
        logger.info(msg)
        print(msg)
        return False

    # Artificial/systemic bids (priority >= 800) are generally exempt,
    # BUT if they land on 4♥/4♠ they must still pass the fit check
    # unless the partnership has already agreed a trump suit (fit_known).
    # This prevents control bids and convention misfires from committing
    # to a 4M contract without a real fit.
    if priority >= 800:
        if bid_level == 4 and bid_strain in ('♥', '♠'):
            fit_known = features.get('fit_known', False)
            if not fit_known:
                # Fall through to the 4M gate below
                pass
            else:
                return True  # Fit established — control bid is fine
        else:
            return True  # Non-4M artificial bids are always exempt

    # 4♥/4♠: Require established fit and trick potential
    if bid_level == 4 and bid_strain in ('♥', '♠'):
        fit = features.get('partnership_fit', 0)
        ltc = features.get('partnership_ltc', 99)
        if fit < 8 or ltc > 14:
            reasons = []
            if fit < 8:
                reasons.append(f"fit={fit}<8")
                _structural_vetoes['4M_fit'] += 1
            if ltc > 14:
                reasons.append(f"LTC={ltc:.1f}>14")
                _structural_vetoes['4M_ltc'] += 1
            msg = f"🚫 VETO 4M: {bid} rejected ({', '.join(reasons)})"
            logger.info(msg)
            print(msg)
            return False

    # 3NT: Require stopper coverage
    if bid == '3NT':
        stoppers = features.get('partnership_stoppers', 0)
        if stoppers < 3:
            _structural_vetoes['3NT_stoppers'] += 1
            msg = f"🚫 VETO 3NT: rejected (stoppers={stoppers}<3)"
            logger.info(msg)
            print(msg)
            return False

    return True


class ConflictResolver:
    """
    Consults Monte Carlo simulation to validate or veto proposed bids.

    This adds a "sanity check" layer on top of the schema-driven decisions,
    preventing the engine from bidding slams that will fail or making
    competitive decisions that don't maximize expected score.
    """

    def __init__(self, simulator=None):
        """
        Initialize the conflict resolver.

        Args:
            simulator: Optional Monte Carlo simulator instance.
                      If None, resolver operates in pass-through mode.
        """
        self.simulator = simulator
        self.veto_count = 0
        self.review_count = 0

    def review_bid(
        self,
        proposed_rule: Dict[str, Any],
        hand: Hand,
        history: list,
        features: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str]:
        """
        Review a proposed bid and potentially veto or modify it.

        Args:
            proposed_rule: The rule that matched (contains bid, priority, explanation)
            hand: The hand being evaluated
            history: Auction history
            features: Optional feature dictionary for context

        Returns:
            Tuple of (final_bid, explanation) - may be modified from original
        """
        self.review_count += 1

        bid = proposed_rule.get('bid', 'Pass')
        priority = proposed_rule.get('priority', 0)
        explanation = proposed_rule.get('explanation', '')

        # Pass-through mode if no simulator available
        if self.simulator is None:
            return bid, explanation

        # 1. SAFETY PROTOCOL: Never veto Artificial/Systemic bids (Tier I)
        # We cannot simulate "2C Stayman" or "4NT RKCB" outcomes directly.
        # These bids are systemic, not result-oriented.
        if priority >= 800:
            return bid, explanation

        # 2. SLAM JUDGMENT: If bidding 6 or 7, verify trick count.
        if self._is_slam_bid(bid):
            vetoed_bid, vetoed_explanation = self._validate_slam(
                bid, hand, history, features
            )
            if vetoed_bid != bid:
                self.veto_count += 1
                return vetoed_bid, vetoed_explanation

        # 3. COMPETITIVE JUDGMENT: Evaluate bid vs. double
        if self._is_competitive_situation(proposed_rule, features):
            vetoed_bid, vetoed_explanation = self._evaluate_competitive(
                bid, hand, history, features
            )
            if vetoed_bid != bid:
                self.veto_count += 1
                return vetoed_bid, vetoed_explanation

        return bid, explanation

    def _is_slam_bid(self, bid: str) -> bool:
        """Check if bid is a slam (6 or 7 level)."""
        if not bid or bid in ['Pass', 'X', 'XX']:
            return False
        return bid[0] in ['6', '7']

    def _is_competitive_situation(
        self,
        rule: Dict[str, Any],
        features: Optional[Dict[str, Any]]
    ) -> bool:
        """Check if this is a competitive bidding situation."""
        # Check if rule is marked as competitive
        explanation = rule.get('explanation', '').upper()
        if 'COMPETITIVE' in explanation or 'SACRIFICE' in explanation:
            return True

        # Check features for competitive context
        if features:
            if features.get('is_contested', False):
                return True
            # High-level competitive bids (5-level or higher)
            bid = rule.get('bid', '')
            if bid and bid[0] == '5':
                return True

        return False

    # Slam suit → game-level fallback mapping
    _GAME_FALLBACK = {
        '♠': '4♠', '♥': '4♥', '♦': '5♦', '♣': '5♣', 'NT': '3NT',
    }

    def _validate_slam(
        self,
        bid: str,
        hand: Hand,
        history: list,
        features: Optional[Dict[str, Any]]
    ) -> Tuple[str, str]:
        """
        Validate a slam bid against expected trick count.

        Fast-fail guard: If the simulator lacks is_fast_mode, skip simulation
        entirely to avoid recursive loops (simulator calling bidding engine
        to generate hands which calls simulator again).

        Returns:
            Tuple of (validated_bid, explanation)
        """
        # Guard against recursive simulation trap: only run if simulator
        # is explicitly flagged as safe for synchronous inline calls.
        if not getattr(self.simulator, 'is_fast_mode', False):
            return bid, "Slam (simulation skipped: no fast mode)"

        target_tricks = 12 if bid[0] == '6' else 13
        suit = bid[1:] if len(bid) > 1 else 'NT'

        try:
            # Run quick simulation (50 iterations for speed)
            expected_tricks = self.simulator.simulate_tricks(
                hand, history, n_sims=50
            )

            # Generous buffer: veto only if clearly failing
            if expected_tricks < (target_tricks - 1.5):
                if bid[0] == '7':
                    # Grand slam → fall back to small slam
                    fallback = f"6{suit}"
                    return fallback, f"VETO: Grand slam too risky (Exp: {expected_tricks:.1f} tricks)"
                else:
                    # Small slam → fall back to game level
                    fallback = self._GAME_FALLBACK.get(suit, f"4{suit}")
                    return fallback, f"VETO: Slam too risky, falling back to game (Exp: {expected_tricks:.1f} tricks)"

            return bid, f"Slam validated (Exp: {expected_tricks:.1f} tricks)"

        except Exception as e:
            # If simulation fails, don't veto - trust the schema
            return bid, f"Slam (simulation unavailable: {e})"

    def _evaluate_competitive(
        self,
        bid: str,
        hand: Hand,
        history: list,
        features: Optional[Dict[str, Any]]
    ) -> Tuple[str, str]:
        """
        Evaluate whether to bid on or double in competitive situation.

        Returns:
            Tuple of (recommended_bid, explanation)
        """
        try:
            # Simulate defensive tricks
            defensive_tricks = self.simulator.simulate_defense(hand, history)

            # If we have 4+ defensive tricks, double may be better
            if defensive_tricks >= 4:
                return "X", f"VETO: Penalty double recommended ({defensive_tricks:.1f} def tricks)"

            return bid, f"Competitive bid confirmed ({defensive_tricks:.1f} def tricks)"

        except Exception as e:
            # If simulation fails, trust the original decision
            return bid, f"Competitive ({e})"

    def get_stats(self) -> Dict[str, Any]:
        """Return resolver statistics."""
        return {
            'reviews': self.review_count,
            'vetoes': self.veto_count,
            'veto_rate': self.veto_count / max(1, self.review_count)
        }

    def reset_stats(self):
        """Reset resolver statistics."""
        self.veto_count = 0
        self.review_count = 0


class PassThroughResolver(ConflictResolver):
    """
    A no-op resolver that always passes through the original bid.

    Use this when Monte Carlo simulation is not available or not desired.
    """

    def __init__(self):
        super().__init__(simulator=None)

    def review_bid(
        self,
        proposed_rule: Dict[str, Any],
        hand: Hand,
        history: list,
        features: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, str]:
        """Always return the original bid unchanged."""
        return proposed_rule.get('bid', 'Pass'), proposed_rule.get('explanation', '')
