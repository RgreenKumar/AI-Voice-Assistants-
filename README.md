# NewsWiki Chatbot

A web chatbot for general questions, recent news, and stable reference topics. The React frontend sends messages to a FastAPI backend, which uses Groq to route and answer questions, NewsAPI for current news, and Wikipedia for encyclopedia information.

## Features

- General conversational answers
- Current-news search through NewsAPI
- Wikipedia search for stable facts and topics
- Conversation history for contextual follow-up questions
- Source links for retrieved articles
- Markdown-formatted answers

## Requirements

- Python 3.10 or later
- Node.js and npm
- A Groq API key
- A NewsAPI API key for current-news searches

## Configuration

Create `backend/.env` and add your API keys:

```env
GROQ_API_KEY=your_groq_api_key
NEWS_API_KEY=your_newsapi_api_key
```

`GROQ_MODEL` is optional. The backend defaults to `openai/gpt-oss-20b`:

```env
GROQ_MODEL=openai/gpt-oss-20b
```

The Groq key is required for chatbot responses. The NewsAPI key is required for news searches; Wikipedia searches do not require a key.

## Run locally on Windows

Open two PowerShell terminals from the project folder.

### 1. Start the backend

```powershell
cd backend
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### 2. Start the frontend

```powershell
cd frontend
npm install
npm run dev
```

Open the local URL printed by Vite, usually `http://localhost:5173`.

## API endpoints

- `GET /` — basic API status
- `GET /api/health` — reports whether the Groq and NewsAPI keys are configured
- `POST /api/chat` — accepts a message and optional conversation history

Example request:

```json
{
  "message": "Tell me about the history of the Indian Parliament",
  "history": []
}
```

## Frontend checks

Run these commands from `frontend`:

```powershell
npm run lint
npm run build
```

## Project layout

```text
backend/
  main.py             FastAPI application and API models
  services.py         Question routing, retrieval, and answer generation
  requirements.txt    Python dependencies
frontend/
  src/
    App.jsx           Chat interface and API requests
    App.css           Chat interface styles
  package.json        Frontend dependencies and scripts
```

## Troubleshooting

- **The frontend cannot connect:** Confirm the backend is running at `http://127.0.0.1:8000`.
- **The backend reports a missing Groq key:** Check that `backend/.env` contains `GROQ_API_KEY`, then restart the backend.
- **News searches are unavailable:** Add a valid `NEWS_API_KEY` to `backend/.env` and restart the backend.
- **A provider request fails:** Check the API key, account usage limits, and provider availability.
