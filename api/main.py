from fastapi import FastAPI
from pydantic import BaseModel
from implementation.answer import answer_question
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="CloudWay RAG API",
    description="API for CloudWay RAG Assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QuestionRequest(BaseModel):
    question: str
    history: list[dict] = []
    conversation_summary: str = ""

class AnswerResponse(BaseModel):
    answer: str
    sources: list[str]

@app.get("/")
def root():
    return {
        "message": "CloudWay RAG API is running"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy"
    }


@app.post("/ask", response_model=AnswerResponse)
def ask_question(request: QuestionRequest):

    answer, documents = answer_question(
        request.question,
        request.history,
        request.conversation_summary
    )

    sources = [
        doc.metadata.get("source", "Unknown")
        for doc in documents
    ]

    return {
        "answer": answer,
        "sources": sources
    }