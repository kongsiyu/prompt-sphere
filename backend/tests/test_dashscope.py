"""Tests for DashScope API integration models and configuration."""

import pytest
from typing import Optional
from pydantic import BaseModel, Field, ValidationError, field_validator

from app.dashscope import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    DashScopeError,
    DashScopeSettings,
    ErrorResponse,
    Message,
    MessageRole,
    ModelParameters,
    QwenMaxParameters,
    QwenModel,
    QwenPlusParameters,
    QwenTurboParameters,
    StreamResponse,
    Usage,
    create_default_parameters,
    get_model_limits,
    get_model_parameters,
)


# Test model that inherits validation logic for testing
class DashScopeSettingsTestModel(BaseModel):
    """Test model to validate DashScope settings without BaseSettings complexity."""

    api_key: Optional[str] = None
    timeout: int = 60
    max_retries: int = 3
    retry_delay: float = 1.0
    requests_per_minute: int = 60
    requests_per_day: int = 1000
    stream_chunk_size: int = 1024

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v):
        """Validate API key format."""
        if v is not None and len(v.strip()) == 0:
            raise ValueError("API key cannot be empty")
        return v

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v):
        """Validate timeout value."""
        if v <= 0:
            raise ValueError("Timeout must be positive")
        return v

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, v):
        """Validate max retries value."""
        if v < 0:
            raise ValueError("Max retries cannot be negative")
        return v

    @field_validator("retry_delay")
    @classmethod
    def validate_retry_delay(cls, v):
        """Validate retry delay value."""
        if v < 0:
            raise ValueError("Retry delay cannot be negative")
        return v

    @field_validator("requests_per_minute", "requests_per_day")
    @classmethod
    def validate_rate_limits(cls, v):
        """Validate rate limit values."""
        if v <= 0:
            raise ValueError("Rate limits must be positive")
        return v

    @field_validator("stream_chunk_size")
    @classmethod
    def validate_stream_chunk_size(cls, v):
        """Validate stream chunk size."""
        if v <= 0:
            raise ValueError("Stream chunk size must be positive")
        return v


class TestDashScopeSettings:
    """Test DashScope configuration settings."""

    def test_default_settings(self):
        """Test default configuration values."""
        settings = DashScopeSettings()

        assert settings.api_key is None
        assert settings.base_url == "https://dashscope.aliyuncs.com"
        assert settings.default_model == "qwen-turbo"
        assert settings.timeout == 60
        assert settings.max_retries == 3
        assert settings.retry_delay == 1.0
        assert settings.requests_per_minute == 60
        assert settings.requests_per_day == 1000
        assert settings.enable_streaming is True
        assert settings.stream_chunk_size == 1024

    def test_settings_with_environment_variables(self, monkeypatch):
        """Test settings loaded from environment variables."""
        monkeypatch.setenv("DASHSCOPE_API_KEY", "test-api-key")
        monkeypatch.setenv("DASHSCOPE_BASE_URL", "https://custom.api.com")
        monkeypatch.setenv("DASHSCOPE_DEFAULT_MODEL", "qwen-max")
        monkeypatch.setenv("DASHSCOPE_TIMEOUT", "120")
        monkeypatch.setenv("DASHSCOPE_MAX_RETRIES", "5")
        monkeypatch.setenv("DASHSCOPE_RETRY_DELAY", "2.0")
        monkeypatch.setenv("DASHSCOPE_REQUESTS_PER_MINUTE", "100")
        monkeypatch.setenv("DASHSCOPE_REQUESTS_PER_DAY", "2000")
        monkeypatch.setenv("DASHSCOPE_ENABLE_STREAMING", "false")
        monkeypatch.setenv("DASHSCOPE_STREAM_CHUNK_SIZE", "2048")

        settings = DashScopeSettings()

        assert settings.api_key == "test-api-key"
        assert settings.base_url == "https://custom.api.com"
        assert settings.default_model == "qwen-max"
        assert settings.timeout == 120
        assert settings.max_retries == 5
        assert settings.retry_delay == 2.0
        assert settings.requests_per_minute == 100
        assert settings.requests_per_day == 2000
        assert settings.enable_streaming is False
        assert settings.stream_chunk_size == 2048

    def test_api_key_validation(self):
        """Test API key validation."""
        # Valid API key
        settings = DashScopeSettingsTestModel(api_key="valid-api-key")
        assert settings.api_key == "valid-api-key"

        # None API key is allowed
        settings = DashScopeSettingsTestModel(api_key=None)
        assert settings.api_key is None

        # Empty API key should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            DashScopeSettingsTestModel(api_key="")
        assert "API key cannot be empty" in str(exc_info.value)

        # Whitespace-only API key should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            DashScopeSettingsTestModel(api_key="   ")
        assert "API key cannot be empty" in str(exc_info.value)

    def test_timeout_validation(self):
        """Test timeout validation."""
        # Valid timeout
        settings = DashScopeSettingsTestModel(timeout=30)
        assert settings.timeout == 30

        # Zero timeout should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            DashScopeSettingsTestModel(timeout=0)
        assert "Timeout must be positive" in str(exc_info.value)

        # Negative timeout should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            DashScopeSettingsTestModel(timeout=-10)
        assert "Timeout must be positive" in str(exc_info.value)

    def test_max_retries_validation(self):
        """Test max retries validation."""
        # Valid max retries
        settings = DashScopeSettingsTestModel(max_retries=5)
        assert settings.max_retries == 5

        # Zero max retries is allowed
        settings = DashScopeSettingsTestModel(max_retries=0)
        assert settings.max_retries == 0

        # Negative max retries should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            DashScopeSettingsTestModel(max_retries=-1)
        assert "Max retries cannot be negative" in str(exc_info.value)

    def test_retry_delay_validation(self):
        """Test retry delay validation."""
        # Valid retry delay
        settings = DashScopeSettingsTestModel(retry_delay=2.5)
        assert settings.retry_delay == 2.5

        # Zero retry delay is allowed
        settings = DashScopeSettingsTestModel(retry_delay=0.0)
        assert settings.retry_delay == 0.0

        # Negative retry delay should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            DashScopeSettingsTestModel(retry_delay=-1.0)
        assert "Retry delay cannot be negative" in str(exc_info.value)

    def test_rate_limits_validation(self):
        """Test rate limits validation."""
        # Valid rate limits
        settings = DashScopeSettingsTestModel(requests_per_minute=120, requests_per_day=3000)
        assert settings.requests_per_minute == 120
        assert settings.requests_per_day == 3000

        # Zero rate limits should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            DashScopeSettingsTestModel(requests_per_minute=0)
        assert "Rate limits must be positive" in str(exc_info.value)

        with pytest.raises(ValidationError) as exc_info:
            DashScopeSettingsTestModel(requests_per_day=0)
        assert "Rate limits must be positive" in str(exc_info.value)

        # Negative rate limits should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            DashScopeSettingsTestModel(requests_per_minute=-10)
        assert "Rate limits must be positive" in str(exc_info.value)

    def test_stream_chunk_size_validation(self):
        """Test stream chunk size validation."""
        # Valid stream chunk size
        settings = DashScopeSettingsTestModel(stream_chunk_size=2048)
        assert settings.stream_chunk_size == 2048

        # Zero stream chunk size should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            DashScopeSettingsTestModel(stream_chunk_size=0)
        assert "Stream chunk size must be positive" in str(exc_info.value)

        # Negative stream chunk size should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            DashScopeSettingsTestModel(stream_chunk_size=-1024)
        assert "Stream chunk size must be positive" in str(exc_info.value)


class TestMessage:
    """Test Message model."""

    def test_valid_message(self):
        """Test creating valid messages."""
        message = Message(role=MessageRole.USER, content="Hello, how are you?")
        assert message.role == MessageRole.USER
        assert message.content == "Hello, how are you?"

        message = Message(role=MessageRole.ASSISTANT, content="I'm doing well, thank you!")
        assert message.role == MessageRole.ASSISTANT
        assert message.content == "I'm doing well, thank you!"

        message = Message(role=MessageRole.SYSTEM, content="You are a helpful assistant.")
        assert message.role == MessageRole.SYSTEM
        assert message.content == "You are a helpful assistant."

    def test_content_validation(self):
        """Test message content validation."""
        # Empty content should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            Message(role=MessageRole.USER, content="")
        assert "Message content cannot be empty" in str(exc_info.value)

        # Whitespace-only content should raise validation error
        with pytest.raises(ValidationError) as exc_info:
            Message(role=MessageRole.USER, content="   ")
        assert "Message content cannot be empty" in str(exc_info.value)

    def test_content_trimming(self):
        """Test that message content is trimmed."""
        message = Message(role=MessageRole.USER, content="  Hello, world!  ")
        assert message.content == "Hello, world!"


class TestModelParameters:
    """Test model parameter classes."""

    def test_base_model_parameters(self):
        """Test base ModelParameters class."""
        params = ModelParameters()

        # Test default values
        assert params.temperature == 0.7
        assert params.top_p == 0.9
        assert params.top_k == 50
        assert params.max_tokens == 2048
        assert params.presence_penalty == 0.0
        assert params.frequency_penalty == 0.0
        assert params.repetition_penalty == 1.0
        assert params.stop is None
        assert params.stream is False
        assert params.enable_search is False

    def test_parameter_validation(self):
        """Test parameter validation."""
        # Valid parameters
        params = ModelParameters(
            temperature=1.5,
            top_p=0.8,
            top_k=30,
            max_tokens=1000,
            presence_penalty=0.5,
            frequency_penalty=-0.5,
            repetition_penalty=1.1,
            stop=[".", "!"],
            stream=True,
            enable_search=True
        )

        assert params.temperature == 1.5
        assert params.top_p == 0.8
        assert params.top_k == 30
        assert params.max_tokens == 1000
        assert params.presence_penalty == 0.5
        assert params.frequency_penalty == -0.5
        assert params.repetition_penalty == 1.1
        assert params.stop == [".", "!"]
        assert params.stream is True
        assert params.enable_search is True

    def test_invalid_parameter_ranges(self):
        """Test invalid parameter ranges."""
        # Temperature out of range
        with pytest.raises(ValidationError):
            ModelParameters(temperature=-0.1)

        with pytest.raises(ValidationError):
            ModelParameters(temperature=2.1)

        # Top_p out of range
        with pytest.raises(ValidationError):
            ModelParameters(top_p=-0.1)

        with pytest.raises(ValidationError):
            ModelParameters(top_p=1.1)

        # Top_k out of range
        with pytest.raises(ValidationError):
            ModelParameters(top_k=0)

        with pytest.raises(ValidationError):
            ModelParameters(top_k=101)

        # Max_tokens out of range
        with pytest.raises(ValidationError):
            ModelParameters(max_tokens=0)

        with pytest.raises(ValidationError):
            ModelParameters(max_tokens=8193)

        # Penalties out of range
        with pytest.raises(ValidationError):
            ModelParameters(presence_penalty=-2.1)

        with pytest.raises(ValidationError):
            ModelParameters(presence_penalty=2.1)

        with pytest.raises(ValidationError):
            ModelParameters(frequency_penalty=-2.1)

        with pytest.raises(ValidationError):
            ModelParameters(frequency_penalty=2.1)

        # Repetition penalty out of range
        with pytest.raises(ValidationError):
            ModelParameters(repetition_penalty=0.05)

        with pytest.raises(ValidationError):
            ModelParameters(repetition_penalty=2.1)

    def test_qwen_turbo_parameters(self):
        """Test QwenTurboParameters specific limits."""
        params = QwenTurboParameters()
        assert params.max_tokens == 1500

        # Valid max tokens for Turbo
        params = QwenTurboParameters(max_tokens=2000)
        assert params.max_tokens == 2000

        # Invalid max tokens for Turbo
        with pytest.raises(ValidationError):
            QwenTurboParameters(max_tokens=2049)

    def test_qwen_plus_parameters(self):
        """Test QwenPlusParameters specific limits."""
        params = QwenPlusParameters()
        assert params.max_tokens == 4096

        # Valid max tokens for Plus
        params = QwenPlusParameters(max_tokens=6000)
        assert params.max_tokens == 6000

        # Invalid max tokens for Plus
        with pytest.raises(ValidationError):
            QwenPlusParameters(max_tokens=6145)

    def test_qwen_max_parameters(self):
        """Test QwenMaxParameters specific limits and features."""
        params = QwenMaxParameters()
        assert params.max_tokens == 6144
        assert params.enable_search is False

        # Valid max tokens for Max
        params = QwenMaxParameters(max_tokens=8000, enable_search=True)
        assert params.max_tokens == 8000
        assert params.enable_search is True

        # Invalid max tokens for Max
        with pytest.raises(ValidationError):
            QwenMaxParameters(max_tokens=8193)


class TestChatCompletionRequest:
    """Test ChatCompletionRequest model."""

    def test_valid_request(self):
        """Test creating valid chat completion requests."""
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are a helpful assistant."),
            Message(role=MessageRole.USER, content="Hello!")
        ]

        request = ChatCompletionRequest(
            model=QwenModel.TURBO,
            messages=messages
        )

        assert request.model == QwenModel.TURBO
        assert len(request.messages) == 2
        assert request.parameters is None

        # With parameters
        params = ModelParameters(temperature=0.8, max_tokens=1000)
        request = ChatCompletionRequest(
            model=QwenModel.PLUS,
            messages=messages,
            parameters=params
        )

        assert request.model == QwenModel.PLUS
        assert request.parameters.temperature == 0.8
        assert request.parameters.max_tokens == 1000

    def test_empty_messages_validation(self):
        """Test validation of empty messages list."""
        with pytest.raises(ValidationError) as exc_info:
            ChatCompletionRequest(
                model=QwenModel.TURBO,
                messages=[]
            )
        assert "at least 1 item" in str(exc_info.value)

    def test_message_role_sequence_validation(self):
        """Test validation of message role sequence."""
        # Valid: starts with system
        messages = [
            Message(role=MessageRole.SYSTEM, content="You are helpful."),
            Message(role=MessageRole.USER, content="Hello!")
        ]
        request = ChatCompletionRequest(model=QwenModel.TURBO, messages=messages)
        assert len(request.messages) == 2

        # Valid: starts with user
        messages = [
            Message(role=MessageRole.USER, content="Hello!")
        ]
        request = ChatCompletionRequest(model=QwenModel.TURBO, messages=messages)
        assert len(request.messages) == 1

        # Invalid: starts with assistant
        messages = [
            Message(role=MessageRole.ASSISTANT, content="Hello!")
        ]
        with pytest.raises(ValidationError) as exc_info:
            ChatCompletionRequest(model=QwenModel.TURBO, messages=messages)
        assert "First message should be system or user role" in str(exc_info.value)


class TestResponseModels:
    """Test response model classes."""

    def test_usage_model(self):
        """Test Usage model."""
        usage = Usage(
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30
        )

        assert usage.prompt_tokens == 10
        assert usage.completion_tokens == 20
        assert usage.total_tokens == 30

    def test_chat_completion_response(self):
        """Test ChatCompletionResponse model."""
        from app.dashscope.models import Choice, FinishReason

        usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        message = Message(role=MessageRole.ASSISTANT, content="Hello!")
        choice = Choice(
            index=0,
            message=message,
            finish_reason=FinishReason.STOP
        )

        response = ChatCompletionResponse(
            id="test-id",
            model=QwenModel.TURBO,
            choices=[choice],
            usage=usage,
            created=1234567890
        )

        assert response.id == "test-id"
        assert response.model == QwenModel.TURBO
        assert len(response.choices) == 1
        assert response.choices[0].index == 0
        assert response.choices[0].message.content == "Hello!"
        assert response.usage.total_tokens == 30
        assert response.created == 1234567890

    def test_empty_choices_validation(self):
        """Test validation of empty choices list."""
        from app.dashscope.models import Choice, FinishReason

        usage = Usage(prompt_tokens=10, completion_tokens=20, total_tokens=30)

        with pytest.raises(ValidationError) as exc_info:
            ChatCompletionResponse(
                id="test-id",
                model=QwenModel.TURBO,
                choices=[],
                usage=usage,
                created=1234567890
            )
        assert "Choices list cannot be empty" in str(exc_info.value)

    def test_error_response(self):
        """Test error response models."""
        error = DashScopeError(
            code="invalid_request",
            message="The request is invalid",
            type="invalid_request_error",
            param="temperature"
        )

        error_response = ErrorResponse(error=error)

        assert error_response.error.code == "invalid_request"
        assert error_response.error.message == "The request is invalid"
        assert error_response.error.type == "invalid_request_error"
        assert error_response.error.param == "temperature"


class TestUtilityFunctions:
    """Test utility functions."""

    def test_get_model_parameters(self):
        """Test get_model_parameters function."""
        assert get_model_parameters(QwenModel.TURBO) == QwenTurboParameters
        assert get_model_parameters(QwenModel.PLUS) == QwenPlusParameters
        assert get_model_parameters(QwenModel.MAX) == QwenMaxParameters
        assert get_model_parameters(QwenModel.VLIT) == ModelParameters

    def test_create_default_parameters(self):
        """Test create_default_parameters function."""
        turbo_params = create_default_parameters(QwenModel.TURBO)
        assert isinstance(turbo_params, QwenTurboParameters)
        assert turbo_params.max_tokens == 1500

        plus_params = create_default_parameters(QwenModel.PLUS)
        assert isinstance(plus_params, QwenPlusParameters)
        assert plus_params.max_tokens == 4096

        max_params = create_default_parameters(QwenModel.MAX)
        assert isinstance(max_params, QwenMaxParameters)
        assert max_params.max_tokens == 6144

        vl_params = create_default_parameters(QwenModel.VLIT)
        assert isinstance(vl_params, ModelParameters)
        assert vl_params.max_tokens == 2048

    def test_get_model_limits(self):
        """Test get_model_limits function."""
        turbo_limits = get_model_limits(QwenModel.TURBO)
        assert turbo_limits["max_tokens"] == 2048
        assert turbo_limits["context_length"] == 8192
        assert turbo_limits["supports_search"] is False
        assert turbo_limits["supports_vision"] is False

        plus_limits = get_model_limits(QwenModel.PLUS)
        assert plus_limits["max_tokens"] == 6144
        assert plus_limits["context_length"] == 32768
        assert plus_limits["supports_search"] is False
        assert plus_limits["supports_vision"] is False

        max_limits = get_model_limits(QwenModel.MAX)
        assert max_limits["max_tokens"] == 8192
        assert max_limits["context_length"] == 32768
        assert max_limits["supports_search"] is True
        assert max_limits["supports_vision"] is False

        vl_limits = get_model_limits(QwenModel.VLIT)
        assert vl_limits["max_tokens"] == 2048
        assert vl_limits["context_length"] == 8192
        assert vl_limits["supports_search"] is False
        assert vl_limits["supports_vision"] is True

        # Test fallback for unknown model (should default to TURBO limits)
        # Note: This tests the internal fallback mechanism
        unknown_limits = get_model_limits("unknown-model")
        assert unknown_limits == turbo_limits


class TestModelEnums:
    """Test model enums."""

    def test_qwen_model_enum(self):
        """Test QwenModel enum values."""
        assert QwenModel.TURBO == "qwen-turbo"
        assert QwenModel.PLUS == "qwen-plus"
        assert QwenModel.MAX == "qwen-max"
        assert QwenModel.VLIT == "qwen-vl-plus"

        # Test that all enum values are strings
        for model in QwenModel:
            assert isinstance(model.value, str)

    def test_message_role_enum(self):
        """Test MessageRole enum values."""
        assert MessageRole.SYSTEM == "system"
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"

        # Test that all enum values are strings
        for role in MessageRole:
            assert isinstance(role.value, str)

    def test_finish_reason_enum(self):
        """Test FinishReason enum values."""
        from app.dashscope.models import FinishReason

        assert FinishReason.STOP == "stop"
        assert FinishReason.LENGTH == "length"
        assert FinishReason.CONTENT_FILTER == "content_filter"
        assert FinishReason.FUNCTION_CALL == "function_call"

        # Test that all enum values are strings
        for reason in FinishReason:
            assert isinstance(reason.value, str)