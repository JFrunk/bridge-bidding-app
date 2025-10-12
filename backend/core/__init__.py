"""
Core shared infrastructure for bidding and play modules.

This package contains shared utilities that both bidding and play modules use:
- SessionManager: Manages user sessions across modules
- DealGenerator: Generates hands for bidding and play scenarios
- ScenarioLoader: Loads scenarios from JSON files

These components are designed to be reusable and module-independent.
"""

from .session_manager import SessionManager
from .deal_generator import DealGenerator
from .scenario_loader import ScenarioLoader

__all__ = ['SessionManager', 'DealGenerator', 'ScenarioLoader']
