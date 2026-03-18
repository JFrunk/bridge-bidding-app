"""
Conflict Resolver - Monte Carlo Integration for Bid Validation

This module provides a "judgment layer" that can veto or modify bids
proposed by the schema engine based on simulation results.

The resolver prevents "suicide bids" by:
1. Never vetoing Artificial/Systemic bids (Tier I, priority >= 800)
2. Validating slam bids against expected trick counts
3. Evaluating competitive decisions (bid vs. double)

Usage:
    resolver = ConflictResolver(simulator)
    final_bid = resolver.review_bid(proposed_rule, hand, history, features)
"""

from typing import Dict, Any, Optional, Tuple
from engine.hand import Hand


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

        # 0. GAME CAP: Downgrade game bids when partnership HCP is insufficient
        # for the play engine to execute. This compensates for Minimax depth-2
        # limitations by keeping contracts at manageable levels.
        if features and self._is_high_bid(bid):
            capped_bid, capped_explanation = self._apply_game_cap(
                bid, explanation, features, history
            )
            if capped_bid != bid:
                self.veto_count += 1
                return capped_bid, capped_explanation

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

    def _is_high_bid(self, bid: str) -> bool:
        """Check if bid is at level 3 or higher (where play engine struggles)."""
        if not bid or bid in ['Pass', 'X', 'XX']:
            return False
        try:
            level = int(bid[0])
            return level >= 3
        except (ValueError, IndexError):
            return False

    # Keep old name as alias for compatibility
    _is_game_bid = _is_high_bid

    def _apply_game_cap(
        self,
        bid: str,
        explanation: str,
        features: dict,
        history: list
    ) -> tuple:
        """
        Cap high-level bids when partnership HCP is insufficient for the
        play engine to execute reliably.

        Tiered thresholds:
        - Level 3+: requires 31+ partnership HCP for level 3
        - Level 3+: requires 33+ partnership HCP for anything higher
        - Below 31: cap at level 2
        """
        partnership_hcp = features.get('partnership_hcp_min', 40)
        last_level = features.get('last_contract_level', 0)
        level = int(bid[0])
        suit = bid[1:]

        # Determine target cap level based on partnership HCP
        # Aggressive thresholds tuned for Minimax depth-2 play engine
        if partnership_hcp >= 33:
            return bid, explanation  # Strong enough for anything
        elif partnership_hcp >= 31:
            cap_level = 3  # Allow invitational with very strong values
        else:
            cap_level = 2  # Partial only — most hands stay at level 2

        # Don't cap if already at or below cap level
        if level <= cap_level:
            return bid, explanation

        # Find the highest legal bid at or below cap_level in this suit
        # Must be higher than the last contract level
        for try_level in range(cap_level, 0, -1):
            if try_level > last_level:
                capped = f"{try_level}{suit}" if suit != 'NT' else f"{try_level}NT"
                return capped, f"Capped at {try_level}-level (partnership ~{partnership_hcp} HCP)"

        # Can't cap below the current auction level — Pass instead
        # of bidding at a level the play engine can't handle
        return 'Pass', f"Pass: Partnership ~{partnership_hcp} HCP insufficient for level {level}"

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
    A resolver that passes through most bids but still applies the game cap.

    Use this when Monte Carlo simulation is not available or not desired.
    The game cap is always active to prevent overbidding beyond play engine
    capabilities.
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
        """Apply game cap but otherwise pass through."""
        bid = proposed_rule.get('bid', 'Pass')
        explanation = proposed_rule.get('explanation', '')

        # Still apply level cap even in pass-through mode
        if features and self._is_high_bid(bid):
            capped_bid, capped_explanation = self._apply_game_cap(
                bid, explanation, features, history
            )
            if capped_bid != bid:
                self.veto_count += 1
                return capped_bid, capped_explanation

        return bid, explanation
