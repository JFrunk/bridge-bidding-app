"""
Unit tests for Module Registry

Tests the self-registering module registry pattern that eliminates
manual registration errors.

Part of ADR-0002: Bidding System Robustness Improvements
Layer 1: Module Registry Pattern
"""

import pytest
from engine.ai.module_registry import ModuleRegistry, ModuleNotFoundError


class MockModule:
    """Mock module for testing."""

    def evaluate(self, hand, features):
        return ("1♠", "Mock bid")


class InvalidModule:
    """Module without required evaluate() method."""

    def some_other_method(self):
        pass


class TestModuleRegistry:
    """Test suite for ModuleRegistry."""

    def setup_method(self):
        """Reset registry before each test."""
        ModuleRegistry.clear()
        ModuleRegistry.enable()

    def teardown_method(self):
        """Clean up after each test."""
        ModuleRegistry.clear()
        ModuleRegistry.enable()

    def test_register_and_get(self):
        """Test basic registration and retrieval."""
        module = MockModule()
        ModuleRegistry.register('test_module', module)

        retrieved = ModuleRegistry.get('test_module')
        assert retrieved is module
        assert retrieved is not None

    def test_register_validates_evaluate_method(self):
        """Test that registration validates evaluate() method exists."""
        invalid_module = InvalidModule()

        with pytest.raises(ValueError) as exc_info:
            ModuleRegistry.register('invalid', invalid_module)

        assert "must implement evaluate() method" in str(exc_info.value)

    def test_get_nonexistent_module_returns_none(self):
        """Test that getting non-existent module returns None."""
        result = ModuleRegistry.get('nonexistent')
        assert result is None

    def test_get_with_default(self):
        """Test that get() returns default when module not found."""
        default_value = "default"
        result = ModuleRegistry.get('nonexistent', default=default_value)
        assert result == default_value

    def test_exists(self):
        """Test exists() method."""
        module = MockModule()
        ModuleRegistry.register('test_module', module)

        assert ModuleRegistry.exists('test_module') is True
        assert ModuleRegistry.exists('nonexistent') is False

    def test_list_modules(self):
        """Test list_modules() returns all registered names."""
        module1 = MockModule()
        module2 = MockModule()

        ModuleRegistry.register('module1', module1)
        ModuleRegistry.register('module2', module2)

        modules = ModuleRegistry.list_modules()
        assert 'module1' in modules
        assert 'module2' in modules
        assert len(modules) == 2

    def test_get_all(self):
        """Test get_all() returns all modules."""
        module1 = MockModule()
        module2 = MockModule()

        ModuleRegistry.register('module1', module1)
        ModuleRegistry.register('module2', module2)

        all_modules = ModuleRegistry.get_all()
        assert 'module1' in all_modules
        assert 'module2' in all_modules
        assert all_modules['module1'] is module1
        assert all_modules['module2'] is module2

    def test_register_override_warning(self):
        """Test that registering same name twice logs warning but works."""
        module1 = MockModule()
        module2 = MockModule()

        ModuleRegistry.register('test_module', module1)
        ModuleRegistry.register('test_module', module2)  # Override

        retrieved = ModuleRegistry.get('test_module')
        assert retrieved is module2  # Should have latest
        assert retrieved is not module1

    def test_clear(self):
        """Test that clear() removes all modules."""
        module1 = MockModule()
        module2 = MockModule()

        ModuleRegistry.register('module1', module1)
        ModuleRegistry.register('module2', module2)

        assert len(ModuleRegistry.list_modules()) == 2

        ModuleRegistry.clear()

        assert len(ModuleRegistry.list_modules()) == 0
        assert ModuleRegistry.get('module1') is None

    def test_disable_prevents_registration(self):
        """Test that disabling registry prevents registration."""
        ModuleRegistry.disable()

        module = MockModule()
        ModuleRegistry.register('test_module', module)

        # Should not be registered when disabled
        assert ModuleRegistry.get('test_module') is None

    def test_enable_allows_registration(self):
        """Test that enabling registry allows registration."""
        ModuleRegistry.disable()
        ModuleRegistry.enable()

        module = MockModule()
        ModuleRegistry.register('test_module', module)

        # Should be registered when enabled
        assert ModuleRegistry.get('test_module') is module

    def test_stats(self):
        """Test stats() returns correct information."""
        module1 = MockModule()
        module2 = MockModule()

        ModuleRegistry.register('module1', module1)
        ModuleRegistry.register('module2', module2)

        stats = ModuleRegistry.stats()

        assert stats['total_modules'] == 2
        assert 'module1' in stats['module_names']
        assert 'module2' in stats['module_names']
        assert stats['enabled'] is True

    def test_registry_is_singleton(self):
        """Test that registry behaves as singleton across imports."""
        module = MockModule()
        ModuleRegistry.register('test_module', module)

        # Import in different context should see same registry
        from engine.ai.module_registry import ModuleRegistry as ImportedRegistry

        assert ImportedRegistry.exists('test_module')
        assert ImportedRegistry.get('test_module') is module


class TestModuleNotFoundError:
    """Test custom exception."""

    def test_exception_can_be_raised(self):
        """Test that ModuleNotFoundError can be raised and caught."""
        with pytest.raises(ModuleNotFoundError):
            raise ModuleNotFoundError("Test error")

    def test_exception_is_exception_subclass(self):
        """Test that ModuleNotFoundError is an Exception."""
        assert issubclass(ModuleNotFoundError, Exception)
