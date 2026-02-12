"""
Strong 2♣ Convention Module

SAYC Standard:
- Strong 2♣ is a forcing opening bid showing 22+ HCP OR
- 19-21 HCP with 9+ playing tricks (massive suit)

This module provides hand generation constraints for practice scenarios.
"""

from engine.hand import Hand
from engine.ai.conventions.base_convention import ConventionModule
from engine.ai.feature_extractor import calculate_playing_tricks
from typing import Optional, Tuple, Dict


class Strong2CConvention(ConventionModule):
    """
    Convention module for Strong 2♣ opening bids.

    Provides hand generation constraints that ensure generated hands
    meet SAYC requirements for a Strong 2♣ opening:
    - Primary: 22+ HCP (any shape)
    - Secondary: 19-21 HCP with 9+ playing tricks
    """

    def get_constraints(self) -> Dict:
        """
        Defines requirements for a hand suitable for Strong 2♣ opening.

        Note: This returns base constraints. The validate_hand() method
        provides additional validation for the secondary criteria
        (19-21 HCP with 9+ playing tricks).
        """
        return {
            'hcp_range': (19, 37),  # Allow 19+ to catch playing trick hands
            'min_longest_suit': 5,   # Need substance for strong hands
        }

    def validate_hand(self, hand: Hand) -> bool:
        """
        Validate that a hand meets Strong 2♣ criteria.

        Returns:
            True if hand qualifies for Strong 2♣, False otherwise
        """
        # Primary criteria: 22+ HCP automatically qualifies
        if hand.hcp >= 22:
            return True

        # Secondary criteria: 19-21 HCP with 9+ playing tricks
        if 19 <= hand.hcp <= 21:
            playing_tricks = calculate_playing_tricks(hand)
            if playing_tricks >= 9.0:
                return True

        return False

    def evaluate(self, hand: Hand, features: Dict) -> Optional[Tuple[str, str]]:
        """
        Evaluate whether hand should open 2♣.

        This module only handles opening bids. Response handling
        is managed by other modules (responder_rebids, etc.).
        """
        # Only applicable when we can open
        auction_features = features.get('auction_features', {})
        if auction_features.get('opener'):
            return None  # Someone already opened

        # Validate hand meets Strong 2♣ requirements
        if not self.validate_hand(hand):
            return None

        # Generate appropriate explanation
        playing_tricks = calculate_playing_tricks(hand)

        if hand.hcp >= 22:
            explanation = f"Strong 2♣ opening showing {hand.hcp} HCP. Game forcing!"
        else:
            explanation = (
                f"Strong 2♣ opening with {hand.hcp} HCP and {playing_tricks:.1f} "
                f"playing tricks. Game forcing!"
            )

        # Return bid with metadata to bypass normal validation
        metadata = {'bypass_hcp': True, 'convention': 'strong_2c'}
        return ("2♣", explanation, metadata)


# ADR-0002 Phase 1: Auto-register this module on import
from engine.ai.module_registry import ModuleRegistry
ModuleRegistry.register("strong_2c", Strong2CConvention())
