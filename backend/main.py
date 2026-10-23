import logging
import os
import re
from datetime import datetime, timezone
from hashlib import sha256

from bson import ObjectId
from dotenv import load_dotenv
from pymongo.errors import DuplicateKeyError, PyMongoError

# Load environment variables before importing services.
load_dotenv()

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, field_validator

from auth import create_session, get_current_user, hash_password, verify_password
from database import get_database
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
        "access_token": create_session(database, user["_id"]),
        "token_type": "bearer",
        "user": {"id": str(user["_id"]), "email": user["email"]},
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
    # This reports whether credentials are configured, not whether providers
    # are reachable or the credentials are valid.
    return {
        "status": "ok",
        "groq_configured": bool(os.getenv("GROQ_API_KEY")),
        "news_configured": bool(os.getenv("NEWS_API_KEY")),
        "mongodb_configured": bool(os.getenv("MONGODB_URI")),
    }


@app.post("/api/auth/register")
def register(request: RegisterRequest, database=Depends(get_database)):
    user = {
        "email": request.email,
        "password_hash": hash_password(request.password),
        "created_at": datetime.now(timezone.utc),
    }
    try:
        result = database.users.insert_one(user)
        user["_id"] = result.inserted_id
        return _auth_response(database, user)
    except DuplicateKeyError as exc:
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from exc
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail="Unable to create your account right now.") from exc


@app.post("/api/auth/login")
def login(request: LoginRequest, database=Depends(get_database)):
    try:
        user = database.users.find_one({"email": request.email})
        if user is None or not verify_password(request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Email or password is incorrect.")
        return _auth_response(database, user)
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail="Unable to log in right now.") from exc


@app.get("/api/auth/me")
def current_account(user: dict = Depends(get_current_user)):
    return {"id": str(user["_id"]), "email": user["email"]}


@app.post("/api/auth/logout")
def logout(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    user: dict = Depends(get_current_user),
    database=Depends(get_database),
):
    if credentials is None:
        raise HTTPException(status_code=401, detail="Please log in to continue.")
    try:
        database.sessions.delete_one(
            {"token_hash": sha256(credentials.credentials.encode("utf-8")).hexdigest()}
        )
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail="Unable to end the session right now.") from exc
    return {"message": "Logged out."}


@app.get("/api/conversations")
def list_conversations(
    user: dict = Depends(get_current_user),
    database=Depends(get_database),
):
    try:
        conversations = database.conversations.find(
            {"user_id": user["_id"]}, {"title": 1, "updated_at": 1}
        ).sort("updated_at", -1).limit(100)
        return [
            {
                "id": str(conversation["_id"]),
                "title": conversation["title"],
                "updated_at": _iso_date(conversation["updated_at"]),
            }
            for conversation in conversations
        ]
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail="Unable to load chat history.") from exc


@app.get("/api/conversations/{conversation_id}")
def get_conversation(
    conversation_id: str,
    user: dict = Depends(get_current_user),
    database=Depends(get_database),
):
    if not ObjectId.is_valid(conversation_id):
        raise HTTPException(status_code=400, detail="Invalid conversation ID.")
    object_id = ObjectId(conversation_id)
    try:
        conversation = database.conversations.find_one(
            {"_id": object_id, "user_id": user["_id"]}
        )
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        messages = database.messages.find(
            {"conversation_id": object_id, "user_id": user["_id"]}
        ).sort([("created_at", 1), ("_id", 1)])
        return {
            "id": str(object_id),
            "title": conversation["title"],
            "messages": [
                {
                    "role": item["role"],
                    "content": item["content"],
                    "source_type": item.get("source_type", ""),
                    "sources": item.get("sources", []),
                }
                for item in messages
            ],
        }
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail="Unable to load this conversation.") from exc


@app.post("/api/chat", response_model=ChatResponse)
def chat(
    request: ChatRequest,
    user: dict = Depends(get_current_user),
    database=Depends(get_database),
):
    conversation_id = None
    safe_history: list[dict[str, str]] = []
    try:
        if request.conversation_id:
            if not ObjectId.is_valid(request.conversation_id):
                raise HTTPException(status_code=400, detail="Invalid conversation ID.")
            conversation_id = ObjectId(request.conversation_id)
            conversation = database.conversations.find_one(
                {"_id": conversation_id, "user_id": user["_id"]}
            )
            if conversation is None:
                raise HTTPException(status_code=404, detail="Conversation not found.")
            previous_messages = list(
                database.messages.find(
                    {"conversation_id": conversation_id, "user_id": user["_id"]},
                    {"role": 1, "content": 1},
                ).sort([("created_at", -1), ("_id", -1)]).limit(20)
            )
            safe_history = [
                {"role": item["role"], "content": item["content"]}
                for item in reversed(previous_messages)
            ]

        result = answer_question(request.message, safe_history)

        if not isinstance(result, dict):
            raise TypeError("Chat service returned an invalid response.")

        now = datetime.now(timezone.utc)
        if conversation_id is None:
            conversation = {
                "user_id": user["_id"],
                "title": request.message[:80],
                "created_at": now,
                "updated_at": now,
            }
            conversation_id = database.conversations.insert_one(conversation).inserted_id
        else:
            database.conversations.update_one(
                {"_id": conversation_id, "user_id": user["_id"]},
                {"$set": {"updated_at": now}},
            )

        answer = str(result.get("answer") or "I couldn't generate an answer.")
        source_type = str(result.get("source_type") or "general")
        sources = result.get("sources") or []
        database.messages.insert_many(
            [
                {
                    "user_id": user["_id"],
                    "conversation_id": conversation_id,
                    "role": "user",
                    "content": request.message,
                    "created_at": now,
                },
                {
                    "user_id": user["_id"],
                    "conversation_id": conversation_id,
                    "role": "assistant",
                    "content": answer,
                    "source_type": source_type,
                    "sources": sources,
                    "created_at": now,
                },
            ]
        )
        return ChatResponse(
            answer=answer,
            source_type=source_type,
            sources=sources,
            conversation_id=str(conversation_id),
        )

    except HTTPException:
        raise
    except PyMongoError as exc:
        logger.exception("MongoDB error while answering chat request")
        raise HTTPException(status_code=503, detail="Unable to save or load chat history.") from exc
    except Exception:
        logger.exception("Unexpected error while answering chat request")
        raise HTTPException(
            status_code=500,
            detail="Sorry, something went wrong while answering. Please try again.",
        )
