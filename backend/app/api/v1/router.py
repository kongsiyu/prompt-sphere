"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.v1 import endpoints

api_router = APIRouter()

# Include all v1 endpoints
api_router.include_router(endpoints.router, tags=["prompts"])