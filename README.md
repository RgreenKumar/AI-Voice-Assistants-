# NewsWiki Chatbot

A web chatbot for general questions, recent news, and stable reference topics. Users can create an account, sign in, and keep their chat history private to their account. The React frontend sends messages to a FastAPI backend, which uses Groq to route and answer questions, NewsAPI for current news, Wikipedia for encyclopedia information, and MongoDB to store accounts and conversations.

## Features

- General conversational answers
- Current-news search through NewsAPI
- Wikipedia search for stable facts and topics
- Conversation history for contextual follow-up questions
- Source links for retrieved articles
- Markdown-formatted answers
- Voice prompts with spoken answers in supported browsers
- Account registration and login
- Private, persistent chat history stored in MongoDB

## Requirements

- Python 3.10 or later
- Node.js and npm
- A Groq API key
- A NewsAPI API key for current-news searches
- A MongoDB connection string (local MongoDB or MongoDB Atlas)

## Configuration

Create `backend/.env` and add your API keys:

```env
GROQ_API_KEY=your_groq_api_key
NEWS_API_KEY=your_newsapi_api_key
MONGODB_URI=mongodb://localhost:27017
MONGODB_DATABASE=newwiki
```

`GROQ_MODEL` is optional. The backend defaults to `openai/gpt-oss-20b`:

```env
GROQ_MODEL=openai/gpt-oss-20b
```

The Groq key is required for chatbot responses. The NewsAPI key is required for news searches; Wikipedia searches do not require a key.
MongoDB is required for account registration, login, and saved chat history. For MongoDB Atlas, use the connection string provided by Atlas as `MONGODB_URI`. Keep this file private and never commit real keys or database credentials.

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

### Voice chat

Select **Voice** beside the message box and speak your question. The recognized words are placed in the message box; press Enter or **Send** to submit. To hear an answer, select its speaker icon. Microphone access must be allowed in the browser. Voice input requires a browser with Web Speech recognition support (such as a recent Chrome or Edge); spoken answers use the browser's built-in speech synthesis.

## API endpoints

- `GET /` — basic API status
- `GET /api/health` — reports whether Groq, NewsAPI, and MongoDB settings are configured
- `POST /api/auth/register` and `POST /api/auth/login` — create an account or start a session
- `GET /api/auth/me` and `POST /api/auth/logout` — inspect or end the current session
- `GET /api/conversations` — list the signed-in user's saved chats
- `GET /api/conversations/{conversation_id}` — load a saved chat owned by the signed-in user
- `POST /api/chat` — send a message to a new or existing conversation

Chat and conversation endpoints require the bearer token returned by login or registration. Passwords are stored as salted scrypt hashes, and session tokens are stored as hashes and expire after 30 days.

Example chat request (include the bearer token from login or registration):

```json
{
  "message": "Tell me about the history of the Indian Parliament",
  "conversation_id": null
}
```

Use the returned `conversation_id` in later requests to continue that chat. Omit it or set it to `null` to start another conversation.

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
  auth.py             Password hashing and session authentication
  database.py         MongoDB connection and indexes
  services.py         Question routing, retrieval, and answer generation
  requirements.txt    Python dependencies
frontend/
  src/
    App.jsx           Chat interface and API requests
    App.css           Chat, history, and login styles
  package.json        Frontend dependencies and scripts
```

## Troubleshooting

- **The frontend cannot connect:** Confirm the backend is running at `http://127.0.0.1:8000`.
- **The backend reports a missing Groq key:** Check that `backend/.env` contains `GROQ_API_KEY`, then restart the backend.
- **News searches are unavailable:** Add a valid `NEWS_API_KEY` to `backend/.env` and restart the backend.
- **A provider request fails:** Check the API key, account usage limits, and provider availability.
