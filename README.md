# NewsWiki Chatbot

NewsWiki is a full-stack AI chatbot with account authentication and persistent conversation history. The React frontend communicates with a FastAPI backend that routes questions through general conversation, live NewsAPI search, or Wikipedia lookup.

## Features

- Answer general questions and coding or writing prompts with Groq
- Search recent news and display matching source articles
- Retrieve stable factual information from Wikipedia
- Keep private, account-based chat histories in MySQL
- Continue conversations with contextual follow-up questions
- Render answers as Markdown with clickable source links
- Use browser voice input and text-to-speech in supported browsers
- Register, sign in, sign out, and load previous conversations

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, React Markdown |
| Backend | Python, FastAPI, SQLAlchemy, Uvicorn |
| AI | Groq API |
| News | NewsAPI |
| Reference data | Wikipedia REST APIs |
| Database | MySQL |

## Requirements

- Windows PowerShell
- Python 3.10 or later
- Node.js and npm
- A running MySQL server
- A Groq API key
- A NewsAPI key for live-news answers

Wikipedia access does not require an API key.

## Configuration

Create `backend/.env` with the following values:

```env
GROQ_API_KEY=your_groq_api_key
NEWS_API_KEY=your_newsapi_api_key

MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_password
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_DATABASE=voice_assistant_db

# Optional; this is the default model
GROQ_MODEL=openai/gpt-oss-20b
```

The database must be reachable before the backend starts. `MYSQL_DATABASE` defaults to `voice_assistant_db`, while the other MySQL settings default to their common local values shown above. The backend creates its required SQLAlchemy tables automatically when MySQL is available.

Never commit real credentials or `.env` files to source control.

## Run Locally on Windows

Open the project folder in two PowerShell terminals.

### 1. Start MySQL

Make sure MySQL is running, then create the configured database if it does not already exist:

```sql
CREATE DATABASE IF NOT EXISTS voice_assistant_db;
```

Update the `MYSQL_*` values in `backend/.env` if your MySQL installation uses different credentials.

### 2. Start the backend

```powershell
cd backend
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

The API runs at `http://127.0.0.1:8000`. Interactive API documentation is available at `http://127.0.0.1:8000/docs`.

### 3. Start the frontend

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
- `GET /api/health` — reports whether Groq, NewsAPI, and MySQL settings are configured
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
  database.py         MySQL connection and SQLAlchemy tables
  services.py         Question routing, retrieval, and answer generation
  requirements.txt    Python dependencies
frontend/
  src/
    App.jsx           Chat interface and API requests
    App.css           Chat, history, and login styles
  package.json        Frontend dependencies and scripts
```

## Troubleshooting

- **The frontend cannot connect:** Confirm the backend is running at `http://127.0.0.1:8000` and that ports `8000` and `5173` are not blocked.
- **MySQL connection fails:** Confirm MySQL is running, create the configured database, and verify the `MYSQL_*` values in `backend/.env`. Restart Uvicorn after changing the environment file.
- **The backend reports a missing Groq key:** Check that `backend/.env` contains `GROQ_API_KEY`, then restart the backend.
- **News searches are unavailable:** Add a valid `NEWS_API_KEY` to `backend/.env` and restart the backend.
- **A provider request fails:** Check the API key, account usage limits, and provider availability.
