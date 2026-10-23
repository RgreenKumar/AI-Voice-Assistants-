import logging
import os
from typing import Literal

from dotenv import load_dotenv

# Load environment variables before importing services.
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

from services import answer_question

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="News, Wikipedia, and General Chatbot API",
    description="Groq-powered chatbot with NewsAPI and Wikipedia retrieval.",
    version="2.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=3000)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=60)

    @field_validator("message")
    @classmethod
    def message_must_not_be_whitespace(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Please enter a message.")
        return value


class Source(BaseModel):
    title: str
    url: str
    published: str | None = None
    publisher: str | None = None


class ChatResponse(BaseModel):
    answer: str
    source_type: str
    sources: list[Source] = Field(default_factory=list)


@app.get("/")
def home():
    return {"message": "News and Wikipedia Chatbot API is running!"}


@app.get("/api/health")
def health_check():
    # This reports whether credentials are configured, not whether providers
    # are reachable or the credentials are valid.
    return {
        "status": "ok",
        "groq_configured": bool(os.getenv("GROQ_API_KEY")),
        "news_configured": bool(os.getenv("NEWS_API_KEY")),
    }


@app.post("/api/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    safe_history = [
        item.model_dump()
        for item in request.history[-60:]
    ]

    try:
        result = answer_question(request.message, safe_history)

        # Guard against malformed service output so the API always returns
        # the documented response shape.
        if not isinstance(result, dict):
            raise TypeError("Chat service returned an invalid response.")

        return ChatResponse(
            answer=str(result.get("answer") or "I couldn't generate an answer."),
            source_type=str(result.get("source_type") or "general"),
            sources=result.get("sources") or [],
        )

    except HTTPException:
        raise
    except Exception:
        logger.exception("Unexpected error while answering chat request")
        raise HTTPException(
            status_code=500,
            detail="Sorry, something went wrong while answering. Please try again.",
        )
