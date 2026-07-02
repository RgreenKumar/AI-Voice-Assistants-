import os
import requests

from config import Config

SERPER_API_URL = 'https://google.serper.dev/search'


def _extract_serper_result(item: dict) -> tuple[str, str, str]:
    title = item.get('title') or item.get('position') or 'Web result'
    link = item.get('link') or item.get('url') or item.get('displayLink') or '#'
    snippet = item.get('snippet') or item.get('description') or item.get('abstract') or ''
    return title, link, snippet


def fetch_web_search_context(query: str):
    api_key = Config.SERPER_API_KEY or os.getenv('SERPER_API_KEY') or ''

    if not api_key:
        return (
            'No web search API key is configured. I can still answer from general knowledge or Wikipedia when available.',
            []
        )

    try:
        response = requests.post(
            SERPER_API_URL,
            headers={'X-API-KEY': api_key, 'Content-Type': 'application/json'},
            json={'q': query, 'num': 5},
            timeout=20,
        )
        response.raise_for_status()
        data = response.json()
    except Exception as exc:
        return f'Web search failed: {exc}', []

    organic_results = data.get('organic') or data.get('organic_results') or data.get('results') or []
    organic_results = organic_results[:5] if isinstance(organic_results, list) else []

    if not organic_results:
        error_message = data.get('error') or data.get('message') or 'No relevant web results found.'
        return error_message, []

    snippets = []
    references = []
    for item in organic_results:
        title, link, snippet = _extract_serper_result(item if isinstance(item, dict) else {})
        snippets.append(f"- {title}: {snippet}".strip())
        references.append({'title': title, 'url': link})

    return '\n'.join(snippets), references
