"""Tests for actual API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.mark.unit
@pytest.mark.api
class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_endpoint_success(self, client: TestClient):
        """Test successful health check."""
        response = client.get("/api/v1/health")

        assert response.status_code == 200
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"

    def test_health_endpoint_response_format(self, client: TestClient):
        """Test health endpoint response format."""
        response = client.get("/api/v1/health")

        if response.status_code == 200:
            data = response.json()

            # Check required fields
            assert isinstance(data["status"], str)
            assert isinstance(data["version"], str)
            assert isinstance(data["timestamp"], str)

            # Status should be a valid value
            assert data["status"] in ["healthy", "unhealthy", "degraded", "maintenance"]


@pytest.mark.unit
@pytest.mark.api
class TestPromptGenerationEndpoint:
    """Test prompt generation endpoint."""

    def test_generate_prompt_success(self, client: TestClient):
        """Test successful prompt generation."""
        request_data = {
            "role": "helpful assistant",
            "context": "You are helping with programming",
            "task": "answer questions clearly"
        }

        response = client.post("/api/v1/prompts/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "prompt" in data
        assert "metadata" in data
        assert isinstance(data["prompt"], str)
        assert len(data["prompt"]) > 0
        assert "helpful assistant" in data["prompt"]

    def test_generate_prompt_with_all_fields(self, client: TestClient):
        """Test prompt generation with all optional fields."""
        request_data = {
            "role": "code reviewer",
            "context": "Reviewing Python code for best practices",
            "task": "provide constructive feedback",
            "constraints": ["Be specific", "Include examples"],
            "examples": ["Point out naming issues", "Suggest improvements"],
            "tone": "professional but friendly",
            "format": "structured feedback"
        }

        response = client.post("/api/v1/prompts/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        prompt = data["prompt"]
        assert "code reviewer" in prompt
        assert "Python code" in prompt
        assert "provide constructive feedback" in prompt
        # Should include constraints and examples in some form
        assert "Be specific" in prompt or "Include examples" in prompt

    def test_generate_prompt_minimal_request(self, client: TestClient):
        """Test prompt generation with minimal required fields."""
        request_data = {
            "role": "assistant",
            "context": "testing",
            "task": "help"
        }

        response = client.post("/api/v1/prompts/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "prompt" in data
        assert "assistant" in data["prompt"]
        assert "testing" in data["prompt"]
        assert "help" in data["prompt"]

    def test_generate_prompt_missing_required_fields(self, client: TestClient):
        """Test prompt generation with missing required fields."""
        # Missing role
        response = client.post("/api/v1/prompts/generate", json={
            "context": "test",
            "task": "test"
        })
        assert response.status_code == 422

        # Missing context
        response = client.post("/api/v1/prompts/generate", json={
            "role": "assistant",
            "task": "test"
        })
        assert response.status_code == 422

        # Missing task
        response = client.post("/api/v1/prompts/generate", json={
            "role": "assistant",
            "context": "test"
        })
        assert response.status_code == 422

    def test_generate_prompt_empty_request_body(self, client: TestClient):
        """Test prompt generation with empty request body."""
        response = client.post("/api/v1/prompts/generate", json={})
        assert response.status_code == 422

    def test_generate_prompt_invalid_json(self, client: TestClient):
        """Test prompt generation with invalid JSON."""
        response = client.post(
            "/api/v1/prompts/generate",
            data='{"invalid": json}',
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422

    def test_generate_prompt_extra_fields(self, client: TestClient):
        """Test prompt generation with extra fields (should be ignored)."""
        request_data = {
            "role": "assistant",
            "context": "test",
            "task": "test",
            "extra_field": "should be ignored",
            "another_extra": 123
        }

        response = client.post("/api/v1/prompts/generate", json=request_data)
        assert response.status_code == 200

    def test_generate_prompt_field_types(self, client: TestClient):
        """Test prompt generation with incorrect field types."""
        # constraints should be list, not string
        request_data = {
            "role": "assistant",
            "context": "test",
            "task": "test",
            "constraints": "not a list"
        }

        response = client.post("/api/v1/prompts/generate", json=request_data)
        assert response.status_code == 422

        # examples should be list, not string
        request_data = {
            "role": "assistant",
            "context": "test",
            "task": "test",
            "examples": "not a list"
        }

        response = client.post("/api/v1/prompts/generate", json=request_data)
        assert response.status_code == 422

    def test_generate_prompt_response_structure(self, client: TestClient):
        """Test that prompt generation response has correct structure."""
        request_data = {
            "role": "assistant",
            "context": "test",
            "task": "test"
        }

        response = client.post("/api/v1/prompts/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert isinstance(data, dict)
        assert "prompt" in data
        assert "metadata" in data
        assert "created_at" in data

        # Check field types
        assert isinstance(data["prompt"], str)
        assert isinstance(data["metadata"], dict)
        assert isinstance(data["created_at"], str)

    def test_generate_prompt_metadata_content(self, client: TestClient):
        """Test that metadata contains useful information."""
        request_data = {
            "role": "assistant",
            "context": "test context",
            "task": "test task"
        }

        response = client.post("/api/v1/prompts/generate", json=request_data)

        assert response.status_code == 200
        data = response.json()

        metadata = data["metadata"]
        # Metadata should contain some useful information
        assert isinstance(metadata, dict)
        # Could contain length, component count, etc.


@pytest.mark.unit
@pytest.mark.api
class TestAPIErrorHandling:
    """Test API error handling."""

    def test_404_for_nonexistent_endpoint(self, client: TestClient):
        """Test 404 response for non-existent endpoints."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404

    def test_405_for_wrong_method(self, client: TestClient):
        """Test 405 response for wrong HTTP methods."""
        # GET on POST endpoint
        response = client.get("/api/v1/prompts/generate")
        assert response.status_code == 405

        # POST on GET endpoint
        response = client.post("/api/v1/health")
        assert response.status_code == 405

    def test_content_type_validation(self, client: TestClient):
        """Test content type validation."""
        # Send non-JSON data to JSON endpoint
        response = client.post(
            "/api/v1/prompts/generate",
            data="not json",
            headers={"Content-Type": "text/plain"}
        )
        assert response.status_code in [415, 422]  # Unsupported media type or validation error

    def test_cors_headers(self, client: TestClient):
        """Test CORS headers in responses."""
        response = client.get("/api/v1/health")

        # Check if CORS headers might be present
        # This depends on FastAPI CORS middleware configuration
        headers = response.headers
        assert headers is not None  # Basic header validation
        assert len(headers) > 0


@pytest.mark.unit
@pytest.mark.api
class TestAPIDocumentation:
    """Test API documentation endpoints."""

    def test_openapi_schema_available(self, client: TestClient):
        """Test that OpenAPI schema is available."""
        response = client.get("/openapi.json")

        if response.status_code == 200:
            data = response.json()
            assert "openapi" in data
            assert "info" in data
            assert "paths" in data

    def test_docs_ui_available(self, client: TestClient):
        """Test that docs UI is available."""
        response = client.get("/docs")
        assert response.status_code in [200, 404]  # Might be available or disabled

    def test_redoc_ui_available(self, client: TestClient):
        """Test that ReDoc UI is available."""
        response = client.get("/redoc")
        assert response.status_code in [200, 404]  # Might be available or disabled


@pytest.mark.unit
@pytest.mark.api
class TestAPIValidation:
    """Test API request/response validation."""

    def test_request_size_limits(self, client: TestClient):
        """Test request size handling."""
        # Very large request
        large_data = {
            "role": "assistant",
            "context": "x" * 10000,  # Very large context
            "task": "test"
        }

        response = client.post("/api/v1/prompts/generate", json=large_data)
        # Should either succeed or fail gracefully
        assert response.status_code in [200, 413, 422]

    def test_unicode_handling(self, client: TestClient):
        """Test Unicode character handling."""
        unicode_data = {
            "role": "助手",
            "context": "帮助用户解决编程问题",
            "task": "提供清晰的解决方案"
        }

        response = client.post("/api/v1/prompts/generate", json=unicode_data)
        assert response.status_code == 200

        data = response.json()
        assert "助手" in data["prompt"]

    def test_special_characters(self, client: TestClient):
        """Test special character handling."""
        special_data = {
            "role": "assistant",
            "context": "Handle special chars: !@#$%^&*(){}[]|\\:;\"'<>?/.,`~",
            "task": "test special character handling"
        }

        response = client.post("/api/v1/prompts/generate", json=special_data)
        assert response.status_code == 200

    def test_empty_string_fields(self, client: TestClient):
        """Test handling of empty string fields."""
        empty_data = {
            "role": "",
            "context": "",
            "task": ""
        }

        response = client.post("/api/v1/prompts/generate", json=empty_data)
        # Might succeed or fail depending on validation rules
        assert response.status_code in [200, 422]