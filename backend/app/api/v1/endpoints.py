"""API v1 endpoints for prompt generation."""

from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException, status

from app.core.config import settings
from app.models.prompt import HealthResponse, PromptRequest, PromptResponse

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        timestamp=datetime.utcnow()
    )


@router.post("/prompts/generate", response_model=PromptResponse)
async def generate_prompt(request: PromptRequest) -> PromptResponse:
    """Generate a system prompt based on the provided parameters."""
    try:
        # Basic prompt template generation
        prompt_parts = []

        # Add role
        if request.role:
            prompt_parts.append(f"You are {request.role}.")

        # Add context
        if request.context:
            prompt_parts.append(f"Context: {request.context}")

        # Add main task
        if request.task:
            prompt_parts.append(f"Your task is to {request.task}")

        # Add constraints
        if request.constraints:
            constraints_text = "\n".join([f"- {constraint}" for constraint in request.constraints])
            prompt_parts.append(f"Constraints:\n{constraints_text}")

        # Add examples
        if request.examples:
            examples_text = "\n".join([f"- {example}" for example in request.examples])
            prompt_parts.append(f"Examples:\n{examples_text}")

        # Add tone
        if request.tone:
            prompt_parts.append(f"Use a {request.tone} tone.")

        # Add format
        if request.format:
            prompt_parts.append(f"Format your response as: {request.format}")

        generated_prompt = "\n\n".join(prompt_parts)

        metadata = {
            "role": request.role,
            "has_constraints": str(bool(request.constraints)),
            "has_examples": str(bool(request.examples)),
            "tone": request.tone or "neutral",
            "format": request.format or "text"
        }

        return PromptResponse(
            prompt=generated_prompt,
            metadata=metadata,
            created_at=datetime.utcnow()
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating prompt: {str(e)}"
        )


@router.get("/prompts/templates")
async def get_templates() -> Dict[str, str]:
    """Get available prompt templates."""
    templates = {
        "assistant": "You are a helpful AI assistant. Your task is to assist users with their questions and tasks in a clear, accurate, and helpful manner.",
        "analyst": "You are a data analyst. Your task is to analyze data, identify patterns, and provide insights based on the information provided.",
        "educator": "You are an educational tutor. Your task is to explain concepts clearly, provide examples, and help users learn effectively.",
        "creative": "You are a creative writing assistant. Your task is to help with creative writing, storytelling, and imaginative content creation.",
        "technical": "You are a technical expert. Your task is to provide accurate technical information, explanations, and solutions to technical problems."
    }

    return templates