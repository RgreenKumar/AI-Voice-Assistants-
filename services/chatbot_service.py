from services.intent_service import classify_query
from services.router_service import route_query
from services.wikipedia_service import fetch_wikipedia_context
from services.news_service import fetch_news_context
from services.web_search_service import fetch_web_search_context
from services.llm_service import generate_llm_response
from services.utils import ensure_history, timestamp


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


class ChatbotService:
    def __init__(self):
        self.history = []

    def handle_message(self, message: str):
        message = (message or '').strip()
        if not message:
            raise ValueError('Message is required')

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
        item = {
            'role': 'assistant',
            'content': response,
            'source': source,
            'references': references,
            'timestamp': timestamp(),
        }
        self.history = ensure_history(self.history, {'role': 'user', 'content': message, 'timestamp': timestamp()})
        self.history = ensure_history(self.history, item)
        return item

    def clear_history(self):
        self.history = []
        return []

    def get_history(self):
        return self.history
