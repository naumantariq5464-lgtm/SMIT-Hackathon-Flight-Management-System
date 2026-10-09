from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.rag_service import rag_service

router = APIRouter(prefix="/chat", tags=["Chat & Support"])

class ChatRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500, examples=["What is the baggage limit for economy?"])

class ChatResponse(BaseModel):
    reply: str

@router.post(
    "",
    response_model=ChatResponse,
    summary="Ask the AI Airline Agent",
    description="Ask a question about airline policies. Includes smart routing to avoid vector DB lookups for greetings.",
)
async def chat_with_agent(request: ChatRequest) -> ChatResponse:
    reply = await rag_service.chat(request.query)
    return ChatResponse(reply=reply)
