import os
from typing import Any

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from config import Config


class MongoDBService:
    def __init__(self, uri: str | None = None, database_name: str | None = None, collection_name: str | None = None):
        self.uri = uri or Config.MONGODB_URI
        self.database_name = database_name or Config.MONGODB_DATABASE
        self.collection_name = collection_name or Config.MONGODB_COLLECTION
        self._client = None
        self._collection = None

    def _connect(self):
        if not self.uri:
            raise RuntimeError('MONGODB_URI is not configured')

        if self._client is None:
            self._client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            self._client.admin.command('ping')

        if self._collection is None:
            database = self._client[self.database_name]
            self._collection = database[self.collection_name]

        return self._collection

    def save_document(self, document: dict[str, Any], *, collection_name: str | None = None):
        collection = self._connect()
        if collection_name:
            database = self._client[self.database_name]
            collection = database[collection_name]

        data = dict(document)
        data.setdefault('_id', data.get('id'))
        if 'id' in data and data.get('_id') is None:
            data['_id'] = data['id']
        collection.replace_one({'id': data.get('id')}, data, upsert=True)
        return data

    def save_conversation(self, conversation: dict[str, Any]):
        return self.save_document(conversation)

    def get_document(self, document_id: str, *, collection_name: str | None = None):
        collection = self._connect()
        if collection_name:
            database = self._client[self.database_name]
            collection = database[collection_name]

        document = collection.find_one({'id': document_id}, {'_id': 0})
        return document

    def get_conversation(self, conversation_id: str):
        return self.get_document(conversation_id)

    def list_documents(self, *, collection_name: str | None = None):
        collection = self._connect()
        if collection_name:
            database = self._client[self.database_name]
            collection = database[collection_name]

        return list(collection.find({}, {'_id': 0}).sort('updated_at', -1))

    def list_conversations(self):
        return self.list_documents()

    def delete_document(self, document_id: str, *, collection_name: str | None = None):
        collection = self._connect()
        if collection_name:
            database = self._client[self.database_name]
            collection = database[collection_name]

        result = collection.delete_one({'id': document_id})
        return result.deleted_count > 0

    def delete_conversation(self, conversation_id: str):
        return self.delete_document(conversation_id)

    def clear_all_documents(self, *, collection_name: str | None = None):
        collection = self._connect()
        if collection_name:
            database = self._client[self.database_name]
            collection = database[collection_name]

        result = collection.delete_many({})
        return result.deleted_count

    def clear_all_conversations(self):
        return self.clear_all_documents()
