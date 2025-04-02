from fastapi import APIRouter

api_router = APIRouter()

# Import and include specific routes
from app.api.endpoints import query, sources, users

api_router.include_router(query.router, prefix="/query", tags=["Query"])
api_router.include_router(sources.router, prefix="/sources", tags=["Sources"])
api_router.include_router(users.router, prefix="/users", tags=["Users"]) 