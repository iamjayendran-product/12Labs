import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

load_dotenv()

from app.rag import answer_question  # noqa: E402  (must load .env first)

STATIC_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static")

app = FastAPI(title="12Labs Feedback RAG")


class ChatRequest(BaseModel):
    question: str


@app.post("/chat")
def chat(req: ChatRequest):
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="question must not be empty")
    try:
        return answer_question(req.question)
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
