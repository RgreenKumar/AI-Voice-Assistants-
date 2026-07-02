import os
import re
from dotenv import load_dotenv
from groq import Groq

from config import Config

load_dotenv()


def _format_wikipedia_summary(context: str | None, references: list | None = None) -> str:
    if not context:
        return 'I can help with general conversation and basic answers right now.'

    cleaned = context.strip().replace('\n', ' ')
    paragraph = re.sub(r'\s+', ' ', cleaned)
    if not paragraph:
        paragraph = 'No relevant Wikipedia information found.'

    lines = [paragraph]
    if references:
        first_url = None
        for reference in references:
            url = reference.get('url') if isinstance(reference, dict) else None
            if url:
                first_url = url
                break
        if first_url:
            lines.extend(['', f'Wikipedia link: {first_url}'])
    return '\n'.join(lines)


def _format_news_summary(context: str | None) -> str:
    if not context:
        return 'No news information available.'

    items = []
    for line in context.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith('- '):
            line = line[2:].strip()
        items.append(line)

    if not items:
        items = [context.strip()]

    formatted = []
    for index, item in enumerate(items[:5], start=1):
        formatted.append(f'{index}. {item}')
    return '\n'.join(formatted)


def generate_llm_response(user_query: str, context: str | None = None, references: list | None = None, source: str = 'LLM') -> str:
    if source in {'Wikipedia', 'News'} and context:
        if source == 'News':
            return _format_news_summary(context)
        return _format_wikipedia_summary(context, references)

    api_key = Config.GROQ_API_KEY or os.getenv('GROQ_API_KEY') or ''
    if not api_key:
        if context:
            if source == 'News':
                return _format_news_summary(context)
            if source == 'Wikipedia':
                return _format_wikipedia_summary(context, references)
            return _format_wikipedia_summary(context, references)

        lowered = user_query.lower().strip()
        if any(word in lowered for word in ['hello', 'hi', 'hey', 'good morning', 'good evening']):
            return 'Hi! I can help with questions, summaries, and retrieved information. Add a GROQ_API_KEY in the .env file for richer live responses.'
        if any(word in lowered for word in ['thank', 'thanks', 'appreciate']):
            return 'You are very welcome. I can help with questions, explanations, and context-based answers.'
        if any(word in lowered for word in ['joke', 'funny']):
            return 'Sure — why do programmers prefer dark mode? Because light attracts bugs.'

        return (
            'I can help with general conversation and basic answers right now. '
            'Add a GROQ_API_KEY in the .env file for richer, more flexible replies.'
        )

    system_prompt = (
        'You are a helpful AI assistant. When external context is provided from Wikipedia or the News API, '
        'answer using only that information. Do not invent facts. If no relevant context is available, '
        'answer using your general knowledge. If the information is insufficient, clearly say so. '
        'If the source is Wikipedia, write one short paragraph and then add a blank line followed by "Wikipedia link: <url>". '
        'If the source is News, present at least 5 items as numbered points with no Wikipedia link.'
    )

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"Question: {user_query}\n\nContext:\n{context or 'No external context provided.'}\n\nReference URL:\n{references[0].get('url') if references and isinstance(references[0], dict) and references[0].get('url') else 'No reference URL available.'}"}
            ],
            temperature=0.2,
            max_tokens=400,
        )
        text = response.choices[0].message.content or ''
        if source == 'News':
            return text if text else _format_news_summary(context)
        if source == 'Wikipedia' and context and references:
            first_url = next((ref.get('url') for ref in references if isinstance(ref, dict) and ref.get('url')), None)
            if first_url and 'wikipedia link:' not in text.lower():
                text = f"{text.strip()}\n\nWikipedia link: {first_url}"
            return text
        return text
    except Exception:
        if context:
            if source == 'News':
                return _format_news_summary(context)
            return _format_wikipedia_summary(context, references)
        return 'I can help with general conversation and basic answers right now.'
