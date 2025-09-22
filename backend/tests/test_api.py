"""Tests for API endpoints."""

import pytest
from fastapi import status
from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """Test the health check endpoint."""
    response = client.get("/api/v1/health")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "status" in data
    assert "version" in data
    assert "timestamp" in data
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


def test_generate_prompt_success(client: TestClient, sample_prompt_request: dict) -> None:
    """Test successful prompt generation."""
    response = client.post("/api/v1/prompts/generate", json=sample_prompt_request)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "prompt" in data
    assert "metadata" in data
    assert "created_at" in data

    # Check that the generated prompt contains expected elements
    prompt = data["prompt"]
    assert "helpful assistant" in prompt
    assert "programming questions" in prompt
    assert "answer programming questions" in prompt

    # Check metadata
    metadata = data["metadata"]
    assert metadata["role"] == sample_prompt_request["role"]
    assert metadata["tone"] == sample_prompt_request["tone"]
    assert metadata["has_constraints"] == "True"
    assert metadata["has_examples"] == "True"


def test_generate_prompt_minimal_request(client: TestClient) -> None:
    """Test prompt generation with minimal required fields."""
    minimal_request = {
        "role": "assistant",
        "context": "General assistance",
        "task": "help users"
    }

    response = client.post("/api/v1/prompts/generate", json=minimal_request)

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert "prompt" in data
    assert "assistant" in data["prompt"]
    assert "General assistance" in data["prompt"]
    assert "help users" in data["prompt"]


def test_generate_prompt_missing_required_fields(client: TestClient) -> None:
    """Test prompt generation with missing required fields."""
    invalid_request = {
        "role": "assistant"
        # Missing context and task
    }

    response = client.post("/api/v1/prompts/generate", json=invalid_request)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_get_templates(client: TestClient) -> None:
    """Test getting available prompt templates."""
    response = client.get("/api/v1/prompts/templates")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert isinstance(data, dict)
    assert "assistant" in data
    assert "analyst" in data
    assert "educator" in data
    assert "creative" in data
    assert "technical" in data

    # Check that templates contain expected content
    assert "helpful AI assistant" in data["assistant"]
    assert "data analyst" in data["analyst"]


def test_invalid_endpoint(client: TestClient) -> None:
    """Test calling an invalid endpoint."""
    response = client.get("/api/v1/nonexistent")

    assert response.status_code == status.HTTP_404_NOT_FOUND