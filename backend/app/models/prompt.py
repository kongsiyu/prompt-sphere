"""Prompt-related data models."""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class PromptRequest(BaseModel):
    """Request model for prompt generation."""

    role: str = Field(..., description="The role or persona for the AI")
    context: str = Field(..., description="Context or background information")
    task: str = Field(..., description="Specific task or objective")
    constraints: Optional[List[str]] = Field(
        default=None, description="List of constraints or limitations"
    )
    examples: Optional[List[str]] = Field(
        default=None, description="Example inputs or outputs"
    )
    tone: Optional[str] = Field(default=None, description="Desired tone or style")
    format: Optional[str] = Field(default=None, description="Output format requirements")


class PromptResponse(BaseModel):
    """Response model for generated prompts."""

    prompt: str = Field(..., description="The generated system prompt")
    metadata: Dict[str, str] = Field(
        default_factory=dict, description="Additional metadata about the prompt"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when prompt was created"
    )


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="Current timestamp"
    )