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

    def _validate_slam(
        self,
        bid: str,
        hand: Hand,
        history: list,
        features: Optional[Dict[str, Any]]
    ) -> Tuple[str, str]:
        """
        Validate a slam bid against expected trick count.

        Returns:
            Tuple of (validated_bid, explanation)
        """
        target_tricks = 12 if bid[0] == '6' else 13

        try:
            # Run quick simulation (50 iterations for speed)
            expected_tricks = self.simulator.simulate_tricks(
                hand, history, n_sims=50
            )

            # Generous buffer: veto only if clearly failing
            if expected_tricks < (target_tricks - 1.5):
                # Determine safe fallback
                if bid[0] == '7':
                    # Fall back to small slam
                    suit = bid[1:] if len(bid) > 1 else 'NT'
                    fallback = f"6{suit}"
                    return fallback, f"VETO: Grand slam too risky (Exp: {expected_tricks:.1f} tricks)"
                else:
                    # Fall back to game or pass
                    return "Pass", f"VETO: Slam too risky (Exp: {expected_tricks:.1f} tricks)"

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
