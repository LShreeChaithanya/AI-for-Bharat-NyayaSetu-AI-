"""
Main API router that combines all route modules
"""
from fastapi import APIRouter
from app.api import routes

# Create main API router
api_router = APIRouter()

# Include all route modules
api_router.include_router(routes.router)

# Add more routers here as the application grows
# api_router.include_router(eligibility.router)
# api_router.include_router(drafts.router)
# api_router.include_router(applications.router)
