"""Tests for DashScope configuration settings - focused on configuration logic."""

import os
import pytest
from unittest.mock import patch
from pydantic import ValidationError

from app.dashscope.config import DashScopeSettings


class TestDashScopeSettingsConfiguration:
    """Test DashScope configuration behavior."""

    def test_default_settings_without_env(self):
        """Test default configuration values when no environment variables are set."""
        # Clear environment variables that might affect the test
        env_vars_to_clear = [
            "DASHSCOPE_API_KEY", "DASHSCOPE_BASE_URL", "DASHSCOPE_MODEL",
            "DASHSCOPE_MAX_TOKENS", "DASHSCOPE_TEMPERATURE", "DASHSCOPE_TOP_P",
            "DASHSCOPE_TIMEOUT", "DASHSCOPE_MAX_RETRIES"
        ]

        # Create a clean environment without .env file interference
        with patch.dict(os.environ, {}, clear=True):
            # Override pydantic-settings to ignore .env file for this test
            with patch.object(DashScopeSettings, 'model_config',
                             {'env_file': None, 'case_sensitive': True, 'extra': 'ignore'}):
                settings = DashScopeSettings()

                # Test actual defaults from the code, not hardcoded expectations
                assert settings.api_key is None  # Should be None when not set
                assert isinstance(settings.base_url, str)
                assert len(settings.base_url) > 0
                assert "dashscope" in settings.base_url.lower()
                assert settings.default_model in ["qwen-turbo", "qwen-plus", "qwen-max"]
                assert isinstance(settings.timeout, int) and settings.timeout > 0
                assert isinstance(settings.max_retries, int) and settings.max_retries >= 0
                assert isinstance(settings.retry_delay, float) and settings.retry_delay >= 0.0

    def test_environment_variable_loading(self):
        """Test that settings correctly load from environment variables."""
        test_values = {
            "DASHSCOPE_API_KEY": "test-api-key-12345",
            "DASHSCOPE_BASE_URL": "https://test.custom.api.com",
            "DASHSCOPE_MODEL": "qwen-max",
            "DASHSCOPE_MAX_TOKENS": "4000",
            "DASHSCOPE_TEMPERATURE": "0.9",
            "DASHSCOPE_TOP_P": "0.95",
            "DASHSCOPE_TIMEOUT": "120",
            "DASHSCOPE_MAX_RETRIES": "5"
        }

        with patch.dict(os.environ, test_values, clear=True):
            with patch.object(DashScopeSettings, 'model_config',
                             {'env_file': None, 'case_sensitive': True, 'extra': 'ignore'}):
                settings = DashScopeSettings()

                # Verify that the values from environment variables are correctly loaded
                assert settings.api_key == test_values["DASHSCOPE_API_KEY"]
                assert settings.base_url == test_values["DASHSCOPE_BASE_URL"]
                assert settings.default_model == test_values["DASHSCOPE_MODEL"]
                assert settings.max_tokens == int(test_values["DASHSCOPE_MAX_TOKENS"])
                assert settings.temperature == float(test_values["DASHSCOPE_TEMPERATURE"])
                assert settings.top_p == float(test_values["DASHSCOPE_TOP_P"])
                assert settings.timeout == int(test_values["DASHSCOPE_TIMEOUT"])
                assert settings.max_retries == int(test_values["DASHSCOPE_MAX_RETRIES"])

    def test_partial_environment_variable_loading(self):
        """Test that only set environment variables override defaults."""
        test_values = {
            "DASHSCOPE_API_KEY": "partial-test-key",
            "DASHSCOPE_TIMEOUT": "90"
        }

        with patch.dict(os.environ, test_values, clear=True):
            settings = DashScopeSettings()

            # Only the set environment variables should be overridden
            assert settings.api_key == test_values["DASHSCOPE_API_KEY"]
            assert settings.timeout == int(test_values["DASHSCOPE_TIMEOUT"])

            # Other values should use defaults
            assert settings.base_url != ""  # Should have a default value
            assert settings.max_retries >= 0  # Should have a reasonable default

    def test_invalid_environment_values(self):
        """Test behavior with invalid environment variable values."""

        # Test invalid timeout
        with patch.dict(os.environ, {"DASHSCOPE_TIMEOUT": "invalid"}):
            with pytest.raises((ValidationError, ValueError)):
                DashScopeSettings()

        # Test invalid max_retries
        with patch.dict(os.environ, {"DASHSCOPE_MAX_RETRIES": "not_a_number"}):
            with pytest.raises((ValidationError, ValueError)):
                DashScopeSettings()

        # Test invalid temperature
        with patch.dict(os.environ, {"DASHSCOPE_TEMPERATURE": "invalid_float"}):
            with pytest.raises((ValidationError, ValueError)):
                DashScopeSettings()

    def test_api_key_validation_logic(self):
        """Test API key validation behavior."""
        # Test with valid API key
        with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "valid-api-key-123"}, clear=True):
            with patch.object(DashScopeSettings, 'model_config',
                             {'env_file': None, 'case_sensitive': True, 'extra': 'ignore'}):
                settings = DashScopeSettings()
                assert settings.api_key == "valid-api-key-123"

        # Test with empty API key - should raise validation error based on our validator
        with patch.dict(os.environ, {"DASHSCOPE_API_KEY": ""}, clear=True):
            with patch.object(DashScopeSettings, 'model_config',
                             {'env_file': None, 'case_sensitive': True, 'extra': 'ignore'}):
                with pytest.raises(ValidationError, match="API key cannot be empty"):
                    DashScopeSettings()

    def test_parameter_bounds_validation(self):
        """Test parameter bounds validation from environment."""

        # Test valid bounds
        valid_values = {
            "DASHSCOPE_TEMPERATURE": "0.8",
            "DASHSCOPE_TOP_P": "0.9",
            "DASHSCOPE_MAX_TOKENS": "2000",
            "DASHSCOPE_TIMEOUT": "60",
            "DASHSCOPE_MAX_RETRIES": "3"
        }

        with patch.dict(os.environ, valid_values):
            settings = DashScopeSettings()
            assert 0.0 <= settings.temperature <= 2.0
            assert 0.0 <= settings.top_p <= 1.0
            assert settings.max_tokens > 0
            assert settings.timeout > 0
            assert settings.max_retries >= 0

        # Test boundary values
        boundary_values = {
            "DASHSCOPE_TEMPERATURE": "2.0",  # Max boundary
            "DASHSCOPE_TOP_P": "1.0",        # Max boundary
            "DASHSCOPE_MAX_RETRIES": "0"     # Min boundary
        }

        with patch.dict(os.environ, boundary_values):
            settings = DashScopeSettings()
            assert settings.temperature == 2.0
            assert settings.top_p == 1.0
            assert settings.max_retries == 0

    def test_settings_immutability_after_creation(self):
        """Test that settings behave consistently after creation."""
        with patch.dict(os.environ, {"DASHSCOPE_API_KEY": "test-key"}):
            settings1 = DashScopeSettings()
            settings2 = DashScopeSettings()

            # Both instances should have the same configuration
            assert settings1.api_key == settings2.api_key
            assert settings1.timeout == settings2.timeout
            assert settings1.max_retries == settings2.max_retries

    def test_settings_with_dotenv_file_presence(self):
        """Test settings behavior when .env file might be present."""
        # This test acknowledges that .env files might exist and affect tests
        settings = DashScopeSettings()

        # Verify that settings object is created successfully regardless of .env
        assert hasattr(settings, 'api_key')
        assert hasattr(settings, 'base_url')
        assert hasattr(settings, 'timeout')
        assert hasattr(settings, 'max_retries')

        # Verify types are correct regardless of source
        assert isinstance(settings.timeout, int)
        assert isinstance(settings.max_retries, int)
        assert isinstance(settings.retry_delay, float)
        assert settings.base_url is None or isinstance(settings.base_url, str)


class TestDashScopeSettingsValidation:
    """Test validation logic isolated from environment concerns."""

    def test_timeout_validation_logic(self):
        """Test timeout validation with controlled inputs."""
        # Mock the environment to test validation logic directly
        with patch.dict(os.environ, {}, clear=True):
            # Test that positive timeout works
            with patch.dict(os.environ, {"DASHSCOPE_TIMEOUT": "30"}):
                settings = DashScopeSettings()
                assert settings.timeout == 30

            # Test that zero/negative timeout raises error
            with patch.dict(os.environ, {"DASHSCOPE_TIMEOUT": "0"}):
                with pytest.raises((ValidationError, ValueError)):
                    DashScopeSettings()

            with patch.dict(os.environ, {"DASHSCOPE_TIMEOUT": "-10"}):
                with pytest.raises((ValidationError, ValueError)):
                    DashScopeSettings()

    def test_retry_validation_logic(self):
        """Test retry validation with controlled inputs."""
        with patch.dict(os.environ, {}, clear=True):
            # Test that non-negative retries work
            with patch.dict(os.environ, {"DASHSCOPE_MAX_RETRIES": "0"}):
                settings = DashScopeSettings()
                assert settings.max_retries == 0

            with patch.dict(os.environ, {"DASHSCOPE_MAX_RETRIES": "5"}):
                settings = DashScopeSettings()
                assert settings.max_retries == 5

            # Test that negative retries raise error
            with patch.dict(os.environ, {"DASHSCOPE_MAX_RETRIES": "-1"}):
                with pytest.raises((ValidationError, ValueError)):
                    DashScopeSettings()

    def test_temperature_validation_logic(self):
        """Test temperature validation with controlled inputs."""
        with patch.dict(os.environ, {}, clear=True):
            # Test valid temperature range
            with patch.dict(os.environ, {"DASHSCOPE_TEMPERATURE": "0.0"}):
                settings = DashScopeSettings()
                assert settings.temperature == 0.0

            with patch.dict(os.environ, {"DASHSCOPE_TEMPERATURE": "2.0"}):
                settings = DashScopeSettings()
                assert settings.temperature == 2.0

            # Test invalid temperature range
            with patch.dict(os.environ, {"DASHSCOPE_TEMPERATURE": "-0.1"}):
                with pytest.raises((ValidationError, ValueError)):
                    DashScopeSettings()

            with patch.dict(os.environ, {"DASHSCOPE_TEMPERATURE": "2.1"}):
                with pytest.raises((ValidationError, ValueError)):
                    DashScopeSettings()

    def test_top_p_validation_logic(self):
        """Test top_p validation with controlled inputs."""
        with patch.dict(os.environ, {}, clear=True):
            # Test valid top_p range
            with patch.dict(os.environ, {"DASHSCOPE_TOP_P": "0.0"}):
                settings = DashScopeSettings()
                assert settings.top_p == 0.0

            with patch.dict(os.environ, {"DASHSCOPE_TOP_P": "1.0"}):
                settings = DashScopeSettings()
                assert settings.top_p == 1.0

            # Test invalid top_p range
            with patch.dict(os.environ, {"DASHSCOPE_TOP_P": "-0.1"}):
                with pytest.raises((ValidationError, ValueError)):
                    DashScopeSettings()

            with patch.dict(os.environ, {"DASHSCOPE_TOP_P": "1.1"}):
                with pytest.raises((ValidationError, ValueError)):
                    DashScopeSettings()