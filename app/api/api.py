from fastapi import APIRouter

from app.api.endpoints import conversation

api_router = APIRouter()
api_router.include_router(conversation.router, prefix="/conversation", tags=["conversation"]) 