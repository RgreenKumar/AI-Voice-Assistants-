import re


def route_query(message: str) -> dict:
    text = (message or '').strip().lower()
    if not text:
        return {'route': 'general', 'sources': ['llm']}

    current_keywords = [
        'today', 'current', 'latest', 'now', 'recent', 'live', 'who is the cm',
        'chief minister', 'cm', 'prime minister', 'president', 'governor'
    ]
    news_keywords = ['news', 'breaking', 'latest news', 'today news', 'current affairs']
    wikipedia_keywords = [
        'who is', 'who was', 'what is', 'define', 'definition', 'history of', 'explain',
        'tell me about', 'summary of', 'place', 'person', 'country', 'city', 'movie', 'company', 'author'
    ]

    if any(keyword in text for keyword in news_keywords):
        return {'route': 'news', 'sources': ['news', 'llm']}

    if any(keyword in text for keyword in current_keywords):
        return {'route': 'web', 'sources': ['web', 'llm']}

    if any(keyword in text for keyword in wikipedia_keywords) or re.search(r'\b(tell me about|explain|describe|introduce|summarize)\b', text):
        return {'route': 'wikipedia', 'sources': ['wikipedia', 'llm']}

    return {'route': 'general', 'sources': ['llm']}
