"""Test suite for Satel integration."""

try:  # pragma: no cover - optional dependency
    import pytest_homeassistant_custom_component  # noqa: F401

    pytest_plugins = ["pytest_homeassistant_custom_component"]
except Exception:  # pragma: no cover - plugin not available
    pytest_plugins: list[str] = []
