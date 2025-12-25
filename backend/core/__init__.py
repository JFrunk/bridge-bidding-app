"""
Core shared infrastructure for bidding and play modules.

This package contains shared utilities that both bidding and play modules use:
- SessionManager: Manages user sessions across modules
- ScenarioLoader: Loads scenarios from JSON files

Hand generation is handled by engine/hand_constructor.py which provides:
- generate_hand_with_constraints(): Generate hands with HCP/shape constraints
- generate_hand_for_convention(): Generate hands for convention practice

These components are designed to be reusable and module-independent.
"""

from .session_manager import SessionManager
from .scenario_loader import ScenarioLoader

__all__ = ['SessionManager', 'ScenarioLoader']
