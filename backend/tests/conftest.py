"""
Pytest configuration for bridge bidding app tests.

This file ensures that all bidding modules are properly registered
before any tests run, even if earlier tests cleared the registry.
"""

import pytest


@pytest.fixture(autouse=True)
def ensure_modules_registered():
    """
    Ensure all bidding modules are registered before each test.

    This fixture runs automatically before every test to guarantee
    that the ModuleRegistry has all required modules, even if a
    previous test cleared it.
    """
    from engine.ai.module_registry import ModuleRegistry

    # If registry is empty, re-import modules to trigger registration
    if len(ModuleRegistry.list_modules()) == 0:
        ModuleRegistry.enable()  # Ensure registry is enabled

        # Re-import all modules to trigger auto-registration
        # Using importlib.reload to force re-execution of registration code
        import importlib

        # Import the modules that auto-register
        import engine.opening_bids
        import engine.responses
        import engine.responder_rebids
        import engine.rebids
        import engine.advancer_bids
        import engine.overcalls
        import engine.ai.conventions.stayman
        import engine.ai.conventions.jacoby_transfers
        import engine.ai.conventions.preempts
        import engine.ai.conventions.blackwood
        import engine.ai.conventions.takeout_doubles
        import engine.ai.conventions.negative_doubles
        import engine.ai.conventions.michaels_cuebid
        import engine.ai.conventions.unusual_2nt
        import engine.ai.conventions.splinter_bids
        import engine.ai.conventions.fourth_suit_forcing

        # Reload each module to re-trigger registration
        importlib.reload(engine.opening_bids)
        importlib.reload(engine.responses)
        importlib.reload(engine.responder_rebids)
        importlib.reload(engine.rebids)
        importlib.reload(engine.advancer_bids)
        importlib.reload(engine.overcalls)
        importlib.reload(engine.ai.conventions.stayman)
        importlib.reload(engine.ai.conventions.jacoby_transfers)
        importlib.reload(engine.ai.conventions.preempts)
        importlib.reload(engine.ai.conventions.blackwood)
        importlib.reload(engine.ai.conventions.takeout_doubles)
        importlib.reload(engine.ai.conventions.negative_doubles)
        importlib.reload(engine.ai.conventions.michaels_cuebid)
        importlib.reload(engine.ai.conventions.unusual_2nt)
        importlib.reload(engine.ai.conventions.splinter_bids)
        importlib.reload(engine.ai.conventions.fourth_suit_forcing)

    yield  # Run the test

    # No cleanup needed - let modules stay registered
