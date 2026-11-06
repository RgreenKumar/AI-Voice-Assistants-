import logging
import os
import re
from datetime import datetime, timezone
from hashlib import sha256

from dotenv import load_dotenv
from sqlalchemy import select, insert, update, delete
from sqlalchemy.exc import IntegrityError

# Load environment variables before importing services.
load_dotenv()

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

from auth import create_session, get_current_user, hash_password, verify_password
from database import (
    get_database,
    users,
    sessions,
    conversations,
    messages,
)
from services import answer_question

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
_bearer = HTTPBearer(auto_error=False)

app = FastAPI(
    title="News, Wikipedia, and General Chatbot API",
    description="Groq-powered chatbot with NewsAPI and Wikipedia retrieval.",
    version="3.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "Authorization"],
)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None

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
    conversation_id: str


class RegisterRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=8, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Enter a valid email address.")
        return email


class LoginRequest(BaseModel):
    email: str = Field(min_length=3, max_length=254)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str) -> str:
        email = value.strip().lower()
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Enter a valid email address.")
        return email


def _auth_response(database, user: dict) -> dict:
    return {
        "access_token": create_session(database, user["id"]),
        "token_type": "bearer",
        "user": {
            "id": str(user["id"]),
            "email": user["email"],
        },
    }


def _iso_date(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat()


@app.get("/")
def home():
    return {"message": "News and Wikipedia Chatbot API is running!"}


@app.get("/api/health")
def health_check():
    return {
        "status": "ok",
        "groq_configured": bool(os.getenv("GROQ_API_KEY")),
        "news_configured": bool(os.getenv("NEWS_API_KEY")),
        "mysql_configured": bool(os.getenv("MYSQL_DATABASE")),
    }


@app.post("/api/auth/register")
def register(request: RegisterRequest, database=Depends(get_database)):

    user = {
        "email": request.email,
        "password_hash": hash_password(request.password),
        "created_at": datetime.utcnow(),
    }

    try:
        result = database.execute(
            insert(users).values(**user)
        )

        user["id"] = result.inserted_primary_key[0]

        return _auth_response(database, user)

    except IntegrityError as exc:
        raise HTTPException(
            status_code=409,
            detail="An account with this email already exists.",
        ) from exc

@app.post("/api/auth/login")
def login(request: LoginRequest, database=Depends(get_database)):

    user = database.execute(
        select(users).where(
            users.c.email == request.email
        )
    ).mappings().first()

    if user is None or not verify_password(
        request.password,
        user["password_hash"]
    ):
        raise HTTPException(
            status_code=401,
            detail="Email or password is incorrect.",
        )

    return _auth_response(database, dict(user))


@app.get("/api/auth/me")
def current_account(user: dict = Depends(get_current_user)):
    return {
        "id": str(user["id"]),
        "email": user["email"],
    }


@app.post("/api/auth/logout")
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    user: dict = Depends(get_current_user),
    database=Depends(get_database),
):

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Please log in to continue.",
        )

    token_hash = sha256(
        credentials.credentials.encode("utf-8")
    ).hexdigest()

    database.execute(
        delete(sessions).where(
            sessions.c.token_hash == token_hash
        )
    )

    return {"message": "Logged out."}


@app.get("/api/conversations")
def list_conversations(
    user: dict = Depends(get_current_user),
    database=Depends(get_database),
):

    result = database.execute(
        select(
            conversations.c.id,
            conversations.c.title,
            conversations.c.updated_at,
        )
        .where(conversations.c.user_id == user["id"])
        .order_by(conversations.c.updated_at.desc())
        .limit(100)
    ).mappings().all()

    return [
        {
            "id": str(item["id"]),
            "title": item["title"],
            "updated_at": _iso_date(item["updated_at"]),
        }
        for item in result
    ]

@app.get("/api/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user),
    database=Depends(get_database),
):

    try:
        conversation_id = int(conversation_id)

        if conversation_id <= 0:
            raise ValueError()

    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid conversation ID.",
        )

    conversation = database.execute(
        select(conversations).where(
            conversations.c.id == conversation_id,
            conversations.c.user_id == user["id"],
        )
    ).mappings().first()

    if conversation is None:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found.",
        )

    conversation_messages = database.execute(
        select(messages)
        .where(
            messages.c.conversation_id == conversation_id,
            messages.c.user_id == user["id"],
        )
        .order_by(
            messages.c.created_at.asc(),
            messages.c.id.asc(),
        )
    ).mappings().all()

    return {
        "id": str(conversation_id),
        "title": conversation["title"],
        "messages": [
            {
                "role": item["role"],
                "content": item["content"],
                "source_type": item["source_type"] or "",
                "sources": item["sources"] or [],
            }
            for item in conversation_messages
        ],
    }

@app.post("/api/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    user: dict = Depends(get_current_user),
    database=Depends(get_database),
):

    conversation_id = None
    safe_history: list[dict[str, str]] = []

    try:

        # Check whether an existing conversation is selected
        if request.conversation_id:

            try:
                conversation_id = int(request.conversation_id)

                if conversation_id <= 0:
                    raise ValueError()

            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid conversation ID.",
                )

            conversation = database.execute(
                select(conversations).where(
                    conversations.c.id == conversation_id,
                    conversations.c.user_id == user["id"],
                )
            ).mappings().first()

            if conversation is None:
                raise HTTPException(
                    status_code=404,
                    detail="Conversation not found.",
                )

            previous_messages = database.execute(
                select(
                    messages.c.role,
                    messages.c.content,
                )
                .where(
                    messages.c.conversation_id == conversation_id,
                    messages.c.user_id == user["id"],
                )
                .order_by(
                    messages.c.created_at.desc(),
                    messages.c.id.desc(),
                )
                .limit(20)
            ).mappings().all()

            safe_history = [
                {
                    "role": item["role"],
                    "content": item["content"],
                }
                for item in reversed(previous_messages)
            ]

        # Get AI response
        result = answer_question(
            request.message,
            safe_history,
        )

        if not isinstance(result, dict):
            raise TypeError(
                "Chat service returned an invalid response."
            )

        now = datetime.utcnow()

        # Create a new conversation
        if conversation_id is None:

            conversation_result = database.execute(
                insert(conversations).values(
                    user_id=user["id"],
                    title=request.message[:80],
                    created_at=now,
                    updated_at=now,
                )
            )

            conversation_id = (
                conversation_result.inserted_primary_key[0]
            )

        else:

            database.execute(
                update(conversations)
                .where(
                    conversations.c.id == conversation_id,
                    conversations.c.user_id == user["id"],
                )
                .values(updated_at=now)
            )

        # Prepare AI response
        answer = str(
            result.get("answer")
            or "I couldn't generate an answer."
        )

        source_type = str(
            result.get("source_type")
            or "general"
        )

        sources = result.get("sources") or []

        # Save user message
        database.execute(
            insert(messages).values(
                user_id=user["id"],
                conversation_id=conversation_id,
                role="user",
                content=request.message,
                created_at=now,
            )
        )

        # Save assistant message
        database.execute(
            insert(messages).values(
                user_id=user["id"],
                conversation_id=conversation_id,
                role="assistant",
                content=answer,
                source_type=source_type,
                sources=sources,
                created_at=now,
            )
        )

        return ChatResponse(
            answer=answer,
            source_type=source_type,
            sources=sources,
            conversation_id=str(conversation_id),
        )

    except HTTPException:
        raise

    except Exception:
        logger.exception(
            "Unexpected error while answering chat request"
        )

        raise HTTPException(
            status_code=500,
            detail="Sorry, something went wrong while answering. Please try again.",
        )