import requests

SEARCH_URL = 'https://en.wikipedia.org/w/api.php'
SUMMARY_URL = 'https://en.wikipedia.org/api/rest_v1/page/summary/{title}'


def fetch_wikipedia_context(query: str):
    try:
        params = {
            'action': 'query',
            'list': 'search',
            'srsearch': query or 'wikipedia',
            'format': 'json',
            'utf8': 1,
            'origin': '*',
        }
        response = requests.get(SEARCH_URL, params=params, headers={'User-Agent': 'AI-Knowledge-Assistant/1.0'}, timeout=20)
        response.raise_for_status()
        data = response.json()
        search_results = data.get('query', {}).get('search', [])
        if not search_results:
            return 'No relevant Wikipedia information found.', []

        title = search_results[0].get('title')
        if not title:
            return 'No relevant Wikipedia information found.', []

        summary_response = requests.get(
            SUMMARY_URL.format(title=title.replace(' ', '_')),
            headers={'User-Agent': 'AI-Knowledge-Assistant/1.0'},
            timeout=20,
        )
        summary_response.raise_for_status()
        summary_data = summary_response.json()

        summary = summary_data.get('extract') or 'No relevant Wikipedia information found.'
        url = summary_data.get('content_urls', {}).get('desktop', {}).get('page') or f'https://en.wikipedia.org/wiki/{title.replace(" ", "_")}'
        references = [{'title': summary_data.get('title') or title, 'url': url}]
        return summary, references
    except Exception as exc:
        return f'Wikipedia lookup failed: {exc}', []
