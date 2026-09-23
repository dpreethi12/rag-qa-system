from fastapi import FastAPI
from app.api.routes.qa import router as qa_router

app = FastAPI(title="RAG Q&A System")
app.include_router(qa_router)