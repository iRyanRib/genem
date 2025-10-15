from fastapi import APIRouter

from app.api.endpoints import conversation, questions, documents, question_topics, distinct

api_router = APIRouter()
api_router.include_router(conversation.router, prefix="/conversation", tags=["conversation"])
api_router.include_router(questions.router, prefix="/questions", tags=["questions"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(question_topics.router, prefix="/question-topics", tags=["question-topics"])
api_router.include_router(distinct.router, prefix="/distinct", tags=["distinct"]) 