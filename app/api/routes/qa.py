from pydantic import BaseModel
from fastapi import APIRouter
from app.core.rag import answer_question

class QuestionRequest(BaseModel):
    question: str
    top_k: int = 3

class QuestionResponse(BaseModel):
    answer: str
    sources: list[str]


router = APIRouter()

@router.post("/ask", response_model=QuestionResponse)
def ask_question(request: QuestionRequest):
    answer, sources = answer_question(request.question, request.top_k)
    return QuestionResponse(answer=answer, sources=sources)