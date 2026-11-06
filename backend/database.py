import os
from functools import lru_cache

from fastapi import HTTPException
from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    JSON,
    ForeignKey,
    UniqueConstraint,
)
from sqlalchemy.engine import URL

metadata = MetaData()

# 1. Users table
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("email", String(254), unique=True, nullable=False),
    Column("password_hash", String(255), nullable=False),
    Column("created_at", DateTime, nullable=False),
)

# 2. Sessions table
sessions = Table(
    "sessions",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("token_hash", String(64), unique=True, nullable=False),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("expires_at", DateTime, nullable=False),
)

# 3. Conversations table
conversations = Table(
    "conversations",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("title", String(255), nullable=False),
    Column("created_at", DateTime, nullable=False),
    Column("updated_at", DateTime, nullable=False),
)

# 4. Messages table
messages = Table(
    "messages",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
    Column("conversation_id", Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
    Column("role", String(20), nullable=False),
    Column("content", Text, nullable=False),
    Column("source_type", String(50), nullable=True),
    Column("sources", JSON, nullable=True),
    Column("created_at", DateTime, nullable=False),
)


@lru_cache(maxsize=1)
def get_engine():
    try:
        url = URL.create(
            drivername="mysql+mysqlconnector",
            username=os.getenv("MYSQL_USER", "root"),
            password=os.getenv("MYSQL_PASSWORD", ""),
            host=os.getenv("MYSQL_HOST", "localhost"),
            port=int(os.getenv("MYSQL_PORT", "3306")),
            database=os.getenv("MYSQL_DATABASE", "voice_assistant_db"),
        )

        engine = create_engine(
            url,
            pool_pre_ping=True,
            echo=False,
        )

        return engine

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Unable to configure MySQL database.",
        ) from exc


def get_database():
    engine = get_engine()

    try:
        metadata.create_all(engine)

        with engine.connect() as connection:
            try:
                yield connection
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    except Exception as exc:
        if isinstance(exc, HTTPException):
            raise

        raise HTTPException(
            status_code=503,
            detail="Unable to connect to MySQL. Check your database configuration.",
        ) from exc