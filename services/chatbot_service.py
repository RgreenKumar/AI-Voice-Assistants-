import uuid
from datetime import datetime

from services.intent_service import classify_query
from services.router_service import route_query
from services.wikipedia_service import fetch_wikipedia_context
from services.news_service import fetch_news_context
from services.web_search_service import fetch_web_search_context
from services.llm_service import generate_llm_response
from services.utils import timestamp
from services.database_service import MongoDBService


def _has_useful_context(context: str | None) -> bool:
    if not context:
        return False

    cleaned = (context or '').strip()
    if not cleaned:
        return False

    lowered = cleaned.lower()
    if 'no relevant' in lowered or 'not found' in lowered or 'lookup failed' in lowered:
        return False

    return True


def _title_from_message(message: str) -> str:
    cleaned = (message or '').strip()
    if not cleaned:
        return 'New chat'

    collapsed = ' '.join(cleaned.split())
    if len(collapsed) <= 48:
        return collapsed
    return collapsed[:45] + '...'


class ChatbotService:
    def __init__(self, db_service: MongoDBService | None = None):
        self.conversations = {}
        self.conversation_order = []
        self.db_service = db_service
        if self.db_service is None:
            try:
                self.db_service = MongoDBService()
            except Exception:
                self.db_service = None
        # If we have a DB service, preload existing conversations into memory
        if self.db_service:
            try:
                conversations = self.db_service.list_conversations() or []
                # DB returns newest-first; store oldest->newest in conversation_order
                for conv in reversed(conversations):
                    cid = conv.get('id')
                    if not cid:
                        continue
                    self.conversations[cid] = conv
                    if cid not in self.conversation_order:
                        self.conversation_order.append(cid)
            except Exception:
                # If DB read fails, continue with empty in-memory state
                pass

    def _create_conversation(self, title: str | None = None):
        conversation_id = str(uuid.uuid4())
        conversation = {
            'id': conversation_id,
            'title': title or 'New chat',
            'messages': [],
            'updated_at': datetime.now().isoformat(timespec='seconds'),
        }
        self.conversations[conversation_id] = conversation
        self.conversation_order.append(conversation_id)
        return conversation

    def _hydrate_conversation_from_db(self, conversation_id: str):
        if not self.db_service:
            return None
        try:
            conversation = self.db_service.get_conversation(conversation_id)
        except Exception:
            return None

        if not conversation:
            return None

        self.conversations[conversation_id] = conversation
        if conversation_id not in self.conversation_order:
            self.conversation_order.append(conversation_id)
        return conversation

    def _get_or_create_conversation(self, conversation_id: str | None):
        if conversation_id and conversation_id in self.conversations:
            return self.conversations[conversation_id]
        if conversation_id:
            hydrated = self._hydrate_conversation_from_db(conversation_id)
            if hydrated:
                return hydrated
        return self._create_conversation()

    def _touch_conversation(self, conversation_id: str):
        if conversation_id in self.conversation_order:
            self.conversation_order.remove(conversation_id)
        self.conversation_order.append(conversation_id)

    def _append_message(self, conversation: dict, message: dict):
        conversation['messages'].append(message)
        if len(conversation['messages']) > 100:
            conversation['messages'] = conversation['messages'][-100:]
        conversation['updated_at'] = datetime.now().isoformat(timespec='seconds')
        self._touch_conversation(conversation['id'])

    def handle_message(self, message: str, conversation_id: str | None = None):
        message = (message or '').strip()
        if not message:
            raise ValueError('Message is required')

        conversation = self._get_or_create_conversation(conversation_id)
        if conversation['title'] == 'New chat':
            conversation['title'] = _title_from_message(message)

        user_message = {'role': 'user', 'content': message, 'timestamp': timestamp()}
        self._append_message(conversation, user_message)

        intent = classify_query(message)
        route = route_query(message)
        context = None
        references = []
        source = 'LLM'

        if route['route'] == 'wikipedia':
            wiki_context, wiki_refs = fetch_wikipedia_context(message)
            if _has_useful_context(wiki_context):
                context = wiki_context
                references = wiki_refs
                source = 'Wikipedia'
            else:
                context = None
                references = []
                source = 'LLM'
        elif route['route'] == 'news':
            news_context, news_refs = fetch_news_context(message)
            if _has_useful_context(news_context):
                context = news_context
                references = news_refs
                source = 'News'
            else:
                context = None
                references = []
                source = 'LLM'
        elif route['route'] == 'web':
            web_context, web_refs = fetch_web_search_context(message)
            if _has_useful_context(web_context):
                context = web_context
                references = web_refs
                source = 'Web'
            else:
                context = None
                references = []
                source = 'LLM'
        elif intent == 'combined':
            wiki_context, wiki_refs = fetch_wikipedia_context(message)
            news_context, news_refs = fetch_news_context(message)
            if _has_useful_context(wiki_context) or _has_useful_context(news_context):
                context = f"Wikipedia context:\n{wiki_context}\n\nNews context:\n{news_context}"
                references = wiki_refs + news_refs
                source = 'Combined'
            else:
                context = None
                references = []
                source = 'LLM'

        response = generate_llm_response(message, context, references, source)
        assistant_message = {
            'role': 'assistant',
            'content': response,
            'source': source,
            'references': references,
            'timestamp': timestamp(),
        }
        self._append_message(conversation, assistant_message)
        self._persist_conversation(conversation)

        return {
            'success': True,
            'content': response,
            'source': source,
            'references': references,
            'timestamp': assistant_message['timestamp'],
            'conversation_id': conversation['id'],
            'title': conversation['title'],
            'conversation': self.get_conversation(conversation['id']),
        }

    def _persist_conversation(self, conversation: dict):
        if not self.db_service:
            return conversation

        try:
            return self.db_service.save_conversation(conversation)
        except Exception:
            return conversation

    def clear_history(self):
        self.conversations = {}
        self.conversation_order = []
        if self.db_service:
            try:
                self.db_service.clear_all_conversations()
            except Exception:
                pass
        return []

    def clear_conversation(self, conversation_id: str | None):
        if conversation_id and conversation_id in self.conversations:
            del self.conversations[conversation_id]
            if conversation_id in self.conversation_order:
                self.conversation_order.remove(conversation_id)
            if self.db_service:
                try:
                    self.db_service.delete_conversation(conversation_id)
                except Exception:
                    pass
        return self.get_history()

    def get_conversation(self, conversation_id: str | None):
        if not conversation_id:
            return None

        if conversation_id in self.conversations:
            conversation = self.conversations[conversation_id]
            return {
                'id': conversation['id'],
                'title': conversation['title'],
                'messages': conversation['messages'],
                'updated_at': conversation['updated_at'],
            }

        if self.db_service:
            try:
                conversation = self.db_service.get_conversation(conversation_id)
                if conversation:
                    return conversation
            except Exception:
                pass
        return None

    def get_history(self):
        history = []
        for conversation_id in reversed(self.conversation_order):
            conversation = self.conversations.get(conversation_id)
            if not conversation:
                continue
            last_message = conversation['messages'][-1] if conversation['messages'] else None
            history.append({
                'id': conversation['id'],
                'title': conversation['title'],
                'preview': (last_message or {}).get('content', 'No messages yet'),
                'updated_at': conversation['updated_at'],
            })

        if self.db_service and not history:
            try:
                conversations = self.db_service.list_conversations()
                for conversation in conversations:
                    history.append({
                        'id': conversation['id'],
                        'title': conversation['title'],
                        'preview': conversation['messages'][-1]['content'] if conversation.get('messages') else 'No messages yet',
                        'updated_at': conversation.get('updated_at'),
                    })
            except Exception:
                pass
        return history
