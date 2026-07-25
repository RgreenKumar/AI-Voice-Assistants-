import re

NEWS_KEYWORDS = ['news', 'latest', 'breaking', 'today', 'today\'s', 'ai news', 'sports', 'politics', 'finance', 'stock', 'cricket', 'business', 'technology']
WIKIPEDIA_KEYWORDS = ['what is', 'who is', 'who was', 'who are', 'explain', 'history of', 'define', 'definition', 'science', 'programming', 'technology', 'place', 'person', 'author', 'country', 'city', 'planet']


def classify_query(message: str) -> str:
    text = message.lower().strip()
    if not text:
        return 'general'
    if any(keyword in text for keyword in NEWS_KEYWORDS):
        return 'news'

    if any(keyword in text for keyword in WIKIPEDIA_KEYWORDS):
        return 'wikipedia'

    if re.search(r'\b(tell me about|tell us about|can you tell me about|can you explain|explain about|about|introduce|summarize)\b', text):
        return 'wikipedia'

    if re.search(r'\b(hello|hi|thanks|thank you|good morning|good evening|joke|how are you)\b', text):
        return 'general'
    if 'news' in text and 'latest' in text:
        return 'news'
    if 'what' in text or 'who' in text or 'why' in text or 'how' in text:
        return 'combined' if 'news' in text or 'latest' in text else 'wikipedia'
    return 'general'
