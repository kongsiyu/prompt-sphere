"""Simple unit tests for configuration settings."""

import pytest

from app.core.config import Settings, get_settings


@pytest.mark.unit
class TestSettingsBasic:
    """Test basic Settings functionality."""

    def test_settings_can_be_created(self):
        """Test that Settings can be instantiated."""
        settings = Settings()
        assert settings is not None

    def test_settings_has_required_fields(self):
        """Test that Settings has expected fields."""
        settings = Settings()

        # Check that key fields exist
        assert hasattr(settings, 'app_name')
        assert hasattr(settings, 'app_version')
        assert hasattr(settings, 'debug')
        assert hasattr(settings, 'host')
        assert hasattr(settings, 'port')
        assert hasattr(settings, 'database_url')
        assert hasattr(settings, 'secret_key')

    def test_settings_field_types(self):
        """Test that Settings fields have correct types."""
        settings = Settings()

        assert isinstance(settings.app_name, str)
        assert isinstance(settings.app_version, str)
        assert isinstance(settings.debug, bool)
        assert isinstance(settings.host, str)
        assert isinstance(settings.port, int)
        assert isinstance(settings.database_url, str)
        assert isinstance(settings.secret_key, str)

    def test_database_settings(self):
        """Test database-related settings."""
        settings = Settings()

        assert isinstance(settings.database_host, str)
        assert isinstance(settings.database_port, int)
        assert isinstance(settings.database_user, str)
        assert isinstance(settings.database_password, str)
        assert isinstance(settings.database_name, str)
        assert isinstance(settings.database_pool_size, int)
        assert isinstance(settings.database_max_overflow, int)

        # Check reasonable values
        assert settings.database_port > 0
        assert settings.database_pool_size > 0
        assert settings.database_max_overflow > 0

    def test_cors_origins_property(self):
        """Test CORS origins property method."""
        settings = Settings()

        cors_origins = settings.cors_origins
        assert isinstance(cors_origins, list)

        # Should have at least one origin
        assert len(cors_origins) > 0

        # All origins should be strings
        for origin in cors_origins:
            assert isinstance(origin, str)

    def test_api_settings(self):
        """Test API-related settings."""
        settings = Settings()

        assert isinstance(settings.api_v1_prefix, str)
        assert settings.api_v1_prefix.startswith("/")
        assert isinstance(settings.access_token_expire_minutes, int)
        assert settings.access_token_expire_minutes > 0


@pytest.mark.unit
class TestGetSettings:
    """Test get_settings function."""

    def test_get_settings_returns_settings(self):
        """Test that get_settings returns a Settings instance."""
        settings = get_settings()
        assert isinstance(settings, Settings)

    def test_get_settings_consistency(self):
        """Test that get_settings returns consistent data."""
        settings1 = get_settings()
        settings2 = get_settings()

        # Should return same values due to caching
        assert settings1.app_name == settings2.app_name
        assert settings1.database_url == settings2.database_url
        assert settings1.secret_key == settings2.secret_key


@pytest.mark.unit
class TestSettingsValidation:
    """Test Settings validation."""

    def test_port_is_positive_integer(self):
        """Test that port is a positive integer."""
        settings = Settings()
        assert isinstance(settings.port, int)
        assert settings.port > 0
        assert settings.port <= 65535  # Valid port range

    def test_database_pool_settings_are_positive(self):
        """Test that database pool settings are positive."""
        settings = Settings()
        assert settings.database_pool_size > 0
        assert settings.database_max_overflow >= 0

    def test_token_expire_time_is_positive(self):
        """Test that token expiration time is positive."""
        settings = Settings()
        assert settings.access_token_expire_minutes > 0

    def test_api_prefix_format(self):
        """Test that API prefix has correct format."""
        settings = Settings()
        assert settings.api_v1_prefix.startswith("/")
        assert "v1" in settings.api_v1_prefix.lower()


@pytest.mark.unit
class TestSettingsFieldAccess:
    """Test accessing specific Settings fields."""

    def test_app_info_fields(self):
        """Test application information fields."""
        settings = Settings()

        assert len(settings.app_name) > 0
        assert len(settings.app_version) > 0
        assert "." in settings.app_version  # Version should have dots

    def test_security_fields(self):
        """Test security-related fields."""
        settings = Settings()

        assert len(settings.secret_key) > 0
        assert settings.access_token_expire_minutes is not None

    def test_optional_api_keys(self):
        """Test optional API key fields."""
        settings = Settings()

        # These might be None or strings
        if settings.openai_api_key is not None:
            assert isinstance(settings.openai_api_key, str)

        if settings.anthropic_api_key is not None:
            assert isinstance(settings.anthropic_api_key, str)

    def test_database_url_format(self):
        """Test database URL format."""
        settings = Settings()

        # Database URL should contain connection information
        assert len(settings.database_url) > 0
        assert "://" in settings.database_url  # Should be a URL format


@pytest.mark.unit
class TestSettingsDefaults:
    """Test Settings default values."""

    def test_has_reasonable_defaults(self):
        """Test that Settings has reasonable default values."""
        settings = Settings()

        # App defaults
        assert "API" in settings.app_name or "api" in settings.app_name.lower()
        assert len(settings.app_version) > 0

        # Server defaults
        assert settings.host in ["0.0.0.0", "localhost", "127.0.0.1"]
        assert 1000 <= settings.port <= 65535

        # API defaults
        assert settings.api_v1_prefix.startswith("/")

        # Database defaults
        assert settings.database_port in [3306, 5432, 1521]  # Common DB ports
        assert 1 <= settings.database_pool_size <= 100
        assert 0 <= settings.database_max_overflow <= 200

    def test_cors_has_localhost_origins(self):
        """Test that CORS includes localhost origins by default."""
        settings = Settings()
        cors_origins = settings.cors_origins

        # Should include at least one localhost origin
        localhost_origins = [origin for origin in cors_origins if "localhost" in origin]
        assert len(localhost_origins) > 0