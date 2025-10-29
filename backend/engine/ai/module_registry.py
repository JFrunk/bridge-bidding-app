"""
Module Registry for Bidding Modules

Centralized registry that eliminates manual module registration failures.
All bidding modules register themselves automatically on import.

Part of ADR-0002: Bidding System Robustness Improvements
Layer 1: Module Registry Pattern
"""

import logging
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


class ModuleRegistry:
    """
    Self-registering module registry for bidding modules.

    Eliminates manual registration errors by providing:
    - Automatic registration on import
    - Safe lookup with fallback
    - Validation that modules implement required interface
    - Clear error messages when modules are missing

    Usage:
        # In module file (e.g., opening_bids.py):
        class OpeningBidsModule(ConventionModule):
            def evaluate(self, hand, features):
                ...

        # Auto-register on import
        ModuleRegistry.register('opening_bids', OpeningBidsModule())

        # In BiddingEngine:
        module = ModuleRegistry.get('opening_bids')
        if module:
            bid, explanation = module.evaluate(hand, features)
    """

    _modules: Dict[str, Any] = {}
    _enabled: bool = True  # Can be disabled for testing

    @classmethod
    def register(cls, name: str, module_instance: Any) -> None:
        """
        Register a bidding module.

        Args:
            name: Module name (e.g., 'opening_bids', 'stayman')
            module_instance: Instance of the module class

        Raises:
            ValueError: If module doesn't implement required interface

        Example:
            ModuleRegistry.register('opening_bids', OpeningBidsModule())
        """
        if not cls._enabled:
            logger.debug(f"Registry disabled, skipping registration of {name}")
            return

        # Validate module has required methods
        if not hasattr(module_instance, 'evaluate'):
            raise ValueError(
                f"Module {name} must implement evaluate() method. "
                f"Found methods: {dir(module_instance)}"
            )

        # Check if already registered (warn but allow override)
        if name in cls._modules:
            logger.warning(
                f"Module {name} already registered, overriding with new instance"
            )

        cls._modules[name] = module_instance
        logger.info(f"✓ Registered bidding module: {name}")

    @classmethod
    def get(cls, name: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Get module by name with optional default.

        Args:
            name: Module name to lookup
            default: Value to return if module not found (default: None)

        Returns:
            Module instance if found, otherwise default

        Example:
            module = ModuleRegistry.get('opening_bids')
            if module is None:
                # Handle missing module
                return ("Pass", "No module found")
        """
        module = cls._modules.get(name, default)

        if module is None:
            logger.warning(
                f"Module {name} not found in registry. "
                f"Available modules: {list(cls._modules.keys())}"
            )

        return module

    @classmethod
    def get_all(cls) -> Dict[str, Any]:
        """
        Get all registered modules.

        Returns:
            Dictionary of {name: module_instance}

        Example:
            all_modules = ModuleRegistry.get_all()
            for name, module in all_modules.items():
                print(f"{name}: {module}")
        """
        return cls._modules.copy()

    @classmethod
    def exists(cls, name: str) -> bool:
        """
        Check if module is registered.

        Args:
            name: Module name to check

        Returns:
            True if module exists, False otherwise

        Example:
            if ModuleRegistry.exists('advancer_bids'):
                module = ModuleRegistry.get('advancer_bids')
        """
        return name in cls._modules

    @classmethod
    def list_modules(cls) -> list:
        """
        Get list of all registered module names.

        Returns:
            List of module names

        Example:
            modules = ModuleRegistry.list_modules()
            print(f"Registered: {', '.join(modules)}")
        """
        return list(cls._modules.keys())

    @classmethod
    def clear(cls) -> None:
        """
        Clear all registered modules.

        WARNING: This should only be used in tests.
        Production code should never clear the registry.

        Example:
            # In test teardown
            ModuleRegistry.clear()
        """
        logger.warning("Clearing module registry (should only happen in tests)")
        cls._modules.clear()

    @classmethod
    def disable(cls) -> None:
        """
        Disable registry (for testing).

        When disabled, register() calls are ignored.
        """
        cls._enabled = False
        logger.info("Module registry disabled")

    @classmethod
    def enable(cls) -> None:
        """
        Enable registry (for testing).
        """
        cls._enabled = True
        logger.info("Module registry enabled")

    @classmethod
    def stats(cls) -> Dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with:
            - total_modules: Number of registered modules
            - module_names: List of module names
            - enabled: Whether registry is enabled

        Example:
            stats = ModuleRegistry.stats()
            print(f"Total modules: {stats['total_modules']}")
        """
        return {
            'total_modules': len(cls._modules),
            'module_names': list(cls._modules.keys()),
            'enabled': cls._enabled,
        }


# Module not found error (for explicit error handling)
class ModuleNotFoundError(Exception):
    """
    Raised when a requested module is not found in the registry.

    This allows BiddingEngine to distinguish between:
    - Module not found (graceful fallback to Pass)
    - Other errors (may need different handling)
    """
    pass
