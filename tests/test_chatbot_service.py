from services.chatbot_service import ChatbotService
from services.router_service import route_query


def test_falls_back_to_llm_when_wikipedia_has_no_useful_context(monkeypatch):
    service = ChatbotService()

    monkeypatch.setattr('services.chatbot_service.classify_query', lambda message: 'wikipedia')
    monkeypatch.setattr('services.chatbot_service.route_query', lambda message: {'route': 'wikipedia', 'sources': ['wikipedia', 'llm']})

    def fake_fetch_wikipedia_context(message):
        return 'No relevant Wikipedia information found.', []

    captured = {}

    def fake_generate_llm_response(user_query, context, references, source):
        captured['user_query'] = user_query
        captured['context'] = context
        captured['references'] = references
        captured['source'] = source
        return 'General knowledge answer'

    monkeypatch.setattr('services.chatbot_service.fetch_wikipedia_context', fake_fetch_wikipedia_context)
    monkeypatch.setattr('services.chatbot_service.generate_llm_response', fake_generate_llm_response)

    result = service.handle_message('who is cm of tamil nadu')

    assert result['content'] == 'General knowledge answer'
    assert captured['source'] == 'LLM'
    assert captured['context'] is None
    assert captured['references'] == []


def test_routes_current_leadership_questions_to_web_search():
    route = route_query('who is cm of tamil nadu')

    assert route['route'] == 'web'
    assert 'web' in route['sources']


def test_uses_web_search_context_when_router_selects_web(monkeypatch):
    service = ChatbotService()
    monkeypatch.setattr('services.chatbot_service.route_query', lambda message: {'route': 'web', 'sources': ['web', 'llm']})

    captured = {}

    def fake_fetch_web_search_context(message):
        return 'Live search results', [{'title': 'Result', 'url': 'https://example.com'}]

    def fake_generate_llm_response(user_query, context, references, source):
        captured['user_query'] = user_query
        captured['context'] = context
        captured['references'] = references
        captured['source'] = source
        return 'Live answer'

    monkeypatch.setattr('services.chatbot_service.fetch_web_search_context', fake_fetch_web_search_context)
    monkeypatch.setattr('services.chatbot_service.generate_llm_response', fake_generate_llm_response)

    result = service.handle_message('who is cm of tamil nadu')

    assert result['content'] == 'Live answer'
    assert captured['source'] == 'Web'
    assert captured['context'] == 'Live search results'


def test_fetch_web_search_context_returns_no_api_key_message(monkeypatch):
    import services.web_search_service as web_search_service

    monkeypatch.setenv('SERPER_API_KEY', '')
    monkeypatch.setattr('services.web_search_service.Config', type('Cfg', (), {'SERPER_API_KEY': ''}))

    message, references = web_search_service.fetch_web_search_context('test query')

    assert 'No web search API key is configured' in message
    assert references == []


def test_starts_a_new_conversation_when_no_conversation_id_is_provided(monkeypatch):
    service = ChatbotService()
    monkeypatch.setattr('services.chatbot_service.generate_llm_response', lambda *args: 'Reply')

    result = service.handle_message('Hello there')

    assert result['conversation_id']
    assert result['title'] == 'Hello there'
    conversation = service.get_conversation(result['conversation_id'])
    assert len(conversation['messages']) == 2


def test_reuses_existing_conversation_when_conversation_id_is_provided(monkeypatch):
    service = ChatbotService()
    monkeypatch.setattr('services.chatbot_service.generate_llm_response', lambda *args: 'Reply')

    first = service.handle_message('What is AI?')
    second = service.handle_message('Tell me more', conversation_id=first['conversation_id'])

    assert second['conversation_id'] == first['conversation_id']
    conversation = service.get_conversation(first['conversation_id'])
    assert len(conversation['messages']) == 4
    assert conversation['messages'][0]['content'] == 'What is AI?'
    assert conversation['messages'][2]['content'] == 'Tell me more'


def test_persists_conversations_via_database_service(monkeypatch):
    class FakeDatabaseService:
        def __init__(self):
            self.saved_conversations = []

        def save_conversation(self, conversation):
            self.saved_conversations.append(conversation)
            return conversation

        def get_conversation(self, conversation_id):
            return None

        def list_conversations(self):
            return []

        def delete_conversation(self, conversation_id):
            return True

        def clear_all_conversations(self):
            return True

    db_service = FakeDatabaseService()
    service = ChatbotService(db_service=db_service)
    monkeypatch.setattr('services.chatbot_service.generate_llm_response', lambda *args: 'Reply')

    result = service.handle_message('Store this in MongoDB')

    assert result['conversation_id']
    assert len(db_service.saved_conversations) == 1
    assert db_service.saved_conversations[0]['messages'][0]['content'] == 'Store this in MongoDB'
