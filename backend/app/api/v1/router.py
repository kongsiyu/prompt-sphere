"""API v1 router configuration."""

from fastapi import APIRouter

from app.api.v1 import endpoints, dashscope
from app.api.v1.endpoints.auth import router as auth_router

api_router = APIRouter()

# Include authentication endpoints
api_router.include_router(auth_router, tags=["authentication"])

# Include all v1 endpoints
api_router.include_router(endpoints.router, tags=["prompts"])

# Include DashScope endpoints
api_router.include_router(
    dashscope.router,
    prefix="/dashscope",
    tags=["dashscope"]
)
