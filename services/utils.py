import html
import json
import os
from datetime import datetime


def sanitize_text(value: str) -> str:
    return html.escape((value or '').strip())


def timestamp() -> str:
    return datetime.now().strftime('%H:%M')


def ensure_history(history: list, message: dict) -> list:
    history.append(message)
    if len(history) > 50:
        history = history[-50:]
    return history
