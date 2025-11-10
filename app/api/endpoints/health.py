from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

@router.get("/ping")
async def health_ping():
    """
    Health check endpoint que retorna 'pong'
    """
    return JSONResponse(content={"message": "pong"})