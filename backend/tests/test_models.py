"""Tests for data models."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from app.models.prompt import HealthResponse, PromptRequest, PromptResponse


def test_prompt_request_valid() -> None:
    """Test creating a valid PromptRequest."""
    data = {
        "role": "assistant",
        "context": "Testing context",
        "task": "help with testing",
        "constraints": ["be concise", "be accurate"],
        "examples": ["example 1", "example 2"],
        "tone": "professional",
        "format": "structured"
    }

    request = PromptRequest(**data)

    assert request.role == "assistant"
    assert request.context == "Testing context"
    assert request.task == "help with testing"
    assert request.constraints == ["be concise", "be accurate"]
    assert request.examples == ["example 1", "example 2"]
    assert request.tone == "professional"
    assert request.format == "structured"


def test_prompt_request_minimal() -> None:
    """Test creating a PromptRequest with only required fields."""
    data = {
        "role": "assistant",
        "context": "Testing context",
        "task": "help with testing"
    }

    request = PromptRequest(**data)

    assert request.role == "assistant"
    assert request.context == "Testing context"
    assert request.task == "help with testing"
    assert request.constraints is None
    assert request.examples is None
    assert request.tone is None
    assert request.format is None


def test_prompt_request_missing_required_fields() -> None:
    """Test that missing required fields raise ValidationError."""
    with pytest.raises(ValidationError):
        PromptRequest(role="assistant")  # Missing context and task

    with pytest.raises(ValidationError):
        PromptRequest(context="test")  # Missing role and task

    with pytest.raises(ValidationError):
        PromptRequest(task="test")  # Missing role and context


def test_prompt_response_creation() -> None:
    """Test creating a PromptResponse."""
    prompt_text = "You are a helpful assistant."
    metadata = {"role": "assistant", "tone": "friendly"}

    response = PromptResponse(
        prompt=prompt_text,
        metadata=metadata
    )

    assert response.prompt == prompt_text
    assert response.metadata == metadata
    assert isinstance(response.created_at, datetime)


def test_prompt_response_default_metadata() -> None:
    """Test PromptResponse with default metadata."""
    response = PromptResponse(prompt="Test prompt")

    assert response.prompt == "Test prompt"
    assert response.metadata == {}
    assert isinstance(response.created_at, datetime)


def test_health_response_creation() -> None:
    """Test creating a HealthResponse."""
    response = HealthResponse(
        status="healthy",
        version="1.0.0"
    )

    assert response.status == "healthy"
    assert response.version == "1.0.0"
    assert isinstance(response.timestamp, datetime)


def test_health_response_required_fields() -> None:
    """Test that HealthResponse requires status and version."""
    with pytest.raises(ValidationError):
        HealthResponse(status="healthy")  # Missing version

    with pytest.raises(ValidationError):
        HealthResponse(version="1.0.0")  # Missing status