from fastapi import APIRouter

from app.api.endpoints import conversation, questions, question_topics, distinct, exams, users, generated_questions, health

api_router = APIRouter()
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(conversation.router, prefix="/conversation", tags=["conversation"])
api_router.include_router(questions.router, prefix="/questions", tags=["questions"])
api_router.include_router(question_topics.router, prefix="/question-topics", tags=["question-topics"])
api_router.include_router(distinct.router, prefix="/distinct", tags=["distinct"]) 
api_router.include_router(exams.router, prefix="/exams", tags=["exams"])
api_router.include_router(generated_questions.router, prefix="/generated-questions", tags=["generated-questions"])