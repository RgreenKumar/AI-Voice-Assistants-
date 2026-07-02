import os
import requests

from config import Config

NEWS_API_URL = 'https://newsapi.org/v2/everything'


def fetch_news_context(query: str):
    api_key = Config.NEWS_API_KEY or os.getenv('NEWS_API_KEY') or ''
    print('Loaded NEWS_API_KEY:', api_key)

    if not api_key:
        if query:
            return (
                f"I could not fetch live news for '{query}' because no News API key is configured. "
                'I can still provide a short general summary and help you explore the topic.'
            ), []
        return (
            'Live news is currently unavailable because no News API key is configured. '
            'You can still ask general questions or add NEWS_API_KEY in the .env file for live updates.'
        ), []

    params = {
        'apiKey': api_key,
        'q': query or 'technology',
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': 5,
    }

    try:
        response = requests.get(NEWS_API_URL, params=params, timeout=20)
        print('News API status:', response.status_code)
        print('News API response:', response.text)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        print('News API Error:', exc)
        return f'News API Error: {exc}', []

    if data.get('status') != 'ok':
        return data.get('message', 'News API returned an error.'), []

    articles = data.get('articles', [])[:5]
    if not articles:
        return 'No current news articles found.', []

    text = '\n'.join(f"- {article.get('title')} : {article.get('description') or ''}" for article in articles)
    references = [{'title': article.get('title', 'News article'), 'url': article.get('url', '#')} for article in articles]
    return text, references
