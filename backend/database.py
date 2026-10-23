import os
from functools import lru_cache
from threading import Lock

from fastapi import HTTPException
from pymongo import MongoClient
from pymongo.errors import PyMongoError

_index_lock = Lock()
_indexes_ready = False


@lru_cache(maxsize=1)
def _mongo_client() -> MongoClient:
    uri = os.getenv("MONGODB_URI")
    if not uri:
        raise HTTPException(
            status_code=503,
            detail="MongoDB is not configured. Set MONGODB_URI in backend/.env.",
        )
    try:
        return MongoClient(uri, serverSelectionTimeoutMS=5000)
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail="MONGODB_URI is invalid.") from exc


def get_database():
    global _indexes_ready

    database_name = os.getenv("MONGODB_DATABASE", "newwiki")
    database = _mongo_client()[database_name]
    if not _indexes_ready:
        with _index_lock:
            if not _indexes_ready:
                try:
                    database.command("ping")
                    database.users.create_index("email", unique=True)
                    database.sessions.create_index("token_hash", unique=True)
                    database.sessions.create_index("expires_at", expireAfterSeconds=0)
                    database.conversations.create_index(
                        [("user_id", 1), ("updated_at", -1)]
                    )
                    database.messages.create_index(
                        [("user_id", 1), ("conversation_id", 1), ("created_at", 1)]
                    )
                    _indexes_ready = True
                except PyMongoError as exc:
                    raise HTTPException(
                        status_code=503,
                        detail="Unable to connect to MongoDB. Check MONGODB_URI and database availability.",
                    ) from exc
    return database
