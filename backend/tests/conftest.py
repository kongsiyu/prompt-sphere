"""Pytest configuration and fixtures."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the FastAPI application."""
    return TestClient(app)


@pytest.fixture
def sample_prompt_request() -> dict:
    """Sample prompt request data for testing."""
    return {
        "role": "helpful assistant",
        "context": "You are helping a user with programming questions",
        "task": "answer programming questions clearly and accurately",
        "constraints": ["Keep responses concise", "Provide code examples when helpful"],
        "examples": ["Q: How do I reverse a string? A: Use string[::-1] in Python"],
        "tone": "friendly and professional",
        "format": "structured response with explanations"
    }