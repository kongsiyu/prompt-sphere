"""Tests for API Pydantic models."""

from datetime import datetime
import pytest
from pydantic import ValidationError

from app.models.prompt import HealthResponse, PromptRequest, PromptResponse


@pytest.mark.unit
class TestPromptRequest:
    """Test PromptRequest Pydantic model."""

    def test_prompt_request_valid_full(self):
        """Test creating a valid PromptRequest with all fields."""
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

    def test_prompt_request_minimal_required(self):
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

    def test_prompt_request_missing_required_fields(self):
        """Test validation errors when required fields are missing."""
        # Missing role
        with pytest.raises(ValidationError) as exc_info:
            PromptRequest(context="test", task="test")
        assert "role" in str(exc_info.value)

        # Missing context
        with pytest.raises(ValidationError) as exc_info:
            PromptRequest(role="assistant", task="test")
        assert "context" in str(exc_info.value)

        # Missing task
        with pytest.raises(ValidationError) as exc_info:
            PromptRequest(role="assistant", context="test")
        assert "task" in str(exc_info.value)

    def test_prompt_request_empty_strings(self):
        """Test validation with empty strings."""
        # Empty strings should be allowed but might be validated by business logic
        data = {
            "role": "",
            "context": "",
            "task": ""
        }

        request = PromptRequest(**data)
        assert request.role == ""
        assert request.context == ""
        assert request.task == ""

    def test_prompt_request_field_types(self):
        """Test field type validation."""
        base_data = {
            "role": "assistant",
            "context": "test",
            "task": "test"
        }

        # Test constraints as non-list
        with pytest.raises(ValidationError):
            PromptRequest(**{**base_data, "constraints": "not a list"})

        # Test examples as non-list
        with pytest.raises(ValidationError):
            PromptRequest(**{**base_data, "examples": "not a list"})

        # Test valid lists
        request = PromptRequest(**{
            **base_data,
            "constraints": ["constraint1", "constraint2"],
            "examples": ["example1", "example2"]
        })
        assert isinstance(request.constraints, list)
        assert isinstance(request.examples, list)

    def test_prompt_request_serialization(self):
        """Test model serialization."""
        data = {
            "role": "assistant",
            "context": "Testing context",
            "task": "help with testing",
            "constraints": ["be concise"],
            "tone": "professional"
        }

        request = PromptRequest(**data)

        # Test dict conversion
        request_dict = request.model_dump()
        assert isinstance(request_dict, dict)
        assert request_dict["role"] == "assistant"
        assert request_dict["constraints"] == ["be concise"]

        # Test JSON serialization
        json_str = request.model_dump_json()
        assert isinstance(json_str, str)
        assert "assistant" in json_str


@pytest.mark.unit
class TestPromptResponse:
    """Test PromptResponse Pydantic model."""

    def test_prompt_response_creation(self):
        """Test creating a valid PromptResponse."""
        data = {
            "prompt": "You are a helpful assistant. Please help with testing.",
            "metadata": {
                "length": "65",
                "components": "role, task",
                "estimated_tokens": "20"
            }
        }

        response = PromptResponse(**data)

        assert response.prompt == "You are a helpful assistant. Please help with testing."
        assert response.metadata == {
            "length": "65",
            "components": "role, task",
            "estimated_tokens": "20"
        }

    def test_prompt_response_minimal(self):
        """Test creating PromptResponse with minimal data."""
        response = PromptResponse(prompt="Test prompt")

        assert response.prompt == "Test prompt"
        assert response.metadata == {}  # Should default to empty dict

    def test_prompt_response_empty_prompt(self):
        """Test PromptResponse with empty prompt."""
        response = PromptResponse(prompt="")
        assert response.prompt == ""

    def test_prompt_response_missing_prompt(self):
        """Test validation error when prompt is missing."""
        with pytest.raises(ValidationError) as exc_info:
            PromptResponse(metadata={"test": "value"})
        assert "prompt" in str(exc_info.value)

    def test_prompt_response_metadata_types(self):
        """Test metadata field type validation."""
        # Metadata should accept dict with string values
        response = PromptResponse(
            prompt="test",
            metadata={"key1": "value1", "key2": "value2"}
        )
        assert response.metadata["key1"] == "value1"

        # Test with non-string values (should be converted or validated)
        response = PromptResponse(
            prompt="test",
            metadata={"number": "123", "boolean": "true"}
        )
        assert response.metadata["number"] == "123"

    def test_prompt_response_serialization(self):
        """Test PromptResponse serialization."""
        response = PromptResponse(
            prompt="Test prompt",
            metadata={"length": "11", "type": "test"}
        )

        # Test dict conversion
        response_dict = response.model_dump()
        assert response_dict["prompt"] == "Test prompt"
        assert response_dict["metadata"]["length"] == "11"

        # Test JSON serialization
        json_str = response.model_dump_json()
        assert "Test prompt" in json_str
        assert "length" in json_str


@pytest.mark.unit
class TestHealthResponse:
    """Test HealthResponse Pydantic model."""

    def test_health_response_creation(self):
        """Test creating a valid HealthResponse."""
        data = {
            "status": "healthy",
            "version": "0.1.0"
        }

        response = HealthResponse(**data)

        assert response.status == "healthy"
        assert response.version == "0.1.0"
        assert isinstance(response.timestamp, datetime)

    def test_health_response_required_fields(self):
        """Test which fields are required."""
        # Both status and version are required
        response = HealthResponse(status="healthy", version="1.0.0")
        assert response.status == "healthy"
        assert response.version == "1.0.0"

    def test_health_response_status_values(self):
        """Test different status values."""
        valid_statuses = ["healthy", "unhealthy", "degraded", "maintenance"]

        for status in valid_statuses:
            response = HealthResponse(status=status, version="1.0.0")
            assert response.status == status

    def test_health_response_serialization(self):
        """Test HealthResponse serialization."""
        response = HealthResponse(
            status="healthy",
            version="1.0.0"
        )

        response_dict = response.model_dump()
        assert response_dict["status"] == "healthy"

        json_str = response.model_dump_json()
        assert "healthy" in json_str


@pytest.mark.unit
class TestModelIntegration:
    """Test model integration and compatibility."""

    def test_request_response_workflow(self):
        """Test typical request-response workflow."""
        # Create request
        request = PromptRequest(
            role="assistant",
            context="testing",
            task="generate test data"
        )

        # Simulate processing and create response
        generated_prompt = f"You are a {request.role}. Context: {request.context}. Task: {request.task}"

        response = PromptResponse(
            prompt=generated_prompt,
            metadata={
                "original_role": request.role,
                "task_type": "generation",
                "length": str(len(generated_prompt))
            }
        )

        assert request.role in response.prompt
        assert response.metadata["original_role"] == request.role
        assert len(response.prompt) > 0

    def test_model_field_descriptions(self):
        """Test that models have proper field descriptions."""
        # Check PromptRequest field descriptions
        prompt_request_fields = PromptRequest.model_fields
        assert "description" in str(prompt_request_fields["role"])
        assert "description" in str(prompt_request_fields["context"])
        assert "description" in str(prompt_request_fields["task"])

        # Check PromptResponse field descriptions
        prompt_response_fields = PromptResponse.model_fields
        assert "description" in str(prompt_response_fields["prompt"])
        assert "description" in str(prompt_response_fields["metadata"])

    def test_model_validation_edge_cases(self):
        """Test edge cases in model validation."""
        # Very long strings
        long_string = "x" * 10000
        request = PromptRequest(
            role=long_string,
            context=long_string,
            task=long_string
        )
        assert len(request.role) == 10000

        # Unicode characters
        unicode_request = PromptRequest(
            role="助手",
            context="测试上下文",
            task="帮助测试"
        )
        assert unicode_request.role == "助手"

    def test_model_defaults_and_optional_fields(self):
        """Test default values and optional field behavior."""
        request = PromptRequest(
            role="assistant",
            context="test",
            task="test"
        )

        # Optional fields should be None by default
        assert request.constraints is None
        assert request.examples is None
        assert request.tone is None
        assert request.format is None

        # Response metadata should default to empty dict
        response = PromptResponse(prompt="test")
        assert response.metadata == {}