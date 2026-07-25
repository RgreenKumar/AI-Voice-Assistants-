pip# AI Voice Assistant

A modern Flask-based AI assistant that combines chat, voice, web knowledge, and conversation history in a single polished web experience. It allows users to ask questions, receive contextual answers from Wikipedia/news/web sources, and continue past conversations just like ChatGPT or Gemini.

## 🌟 Features

- Text-based conversational chat interface
- Voice input through browser speech recognition
- Voice output through browser speech synthesis or Google Text-to-Speech
- Wikipedia-based knowledge retrieval
- Live news lookup
- Web search integration for current information
- LLM-powered response generation
- Resumable chat history with multi-threaded conversations
- Sidebar-based chat switching
- Export chat history as text or JSON
- Light/dark theme toggle

## 🧠 What This Project Demonstrates

This project is a strong portfolio example of:
- Flask web development
- API integration
- Service-oriented backend architecture
- Frontend-backend communication
- Voice-enabled user experience
- AI orchestration and fallback design

## 📁 Project Structure

```text
AI-Voice-Assistants-/
├── app.py
├── config.py
├── services/
│   ├── chatbot_service.py
│   ├── intent_service.py
│   ├── router_service.py
│   ├── llm_service.py
│   ├── wikipedia_service.py
│   ├── news_service.py
│   ├── web_search_service.py
│   ├── voice_service.py
│   └── utils.py
├── static/
│   ├── css/
│   └── js/
├── templates/
│   └── index.html
├── tests/
└── .env
```

## 🛠️ Tech Stack

- Python
- Flask
- HTML, CSS, JavaScript
- Groq API for LLM responses
- Wikipedia API
- NewsAPI
- Serper API
- Web Speech API
- pytest

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone <your-repository-url>
cd AI-Voice-Assistants-
```

### 2. Create a virtual environment

On Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

On macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install flask python-dotenv requests groq
```

### 4. Configure environment variables

Create a `.env` file in the project root with the following values:

```env
SECRET_KEY=your_secret_key
GROQ_API_KEY=your_groq_api_key
NEWS_API_KEY=your_news_api_key
SERPER_API_KEY=your_serper_key
GOOGLE_TTS_API_KEY=your_google_tts_key
```

> Note: The app can still run without all keys, but some features may fall back gracefully or behave differently.

### 5. Run the application

```bash
python app.py
```

Then open:

```text
http://localhost:5000
```

## ▶️ How to Use

- Type a message in the chat box and press Enter or click Send
- Click the microphone button to speak your query
- Enable voice output in the sidebar to hear responses
- Click an older chat in the sidebar to resume that conversation
- Use the New chat button to begin a fresh thread

## 🧪 Testing

Run the test suite with:

```bash
python -m pytest -q
```

## 📚 Documentation

The repository includes several helpful guides:
- QUICK_START.md – quick setup and usage guide
- VOICE_FEATURES.md – detailed voice feature documentation
- PROJECT_INTERVIEW_GUIDE.md – interview preparation guide

## 🔧 API Endpoints

The app provides these main routes:

- `GET /` – load the app UI
- `POST /chat` – send a chat message
- `POST /clear` – clear chats
- `GET /history` – get saved conversations
- `GET /conversation/<conversation_id>` – load a specific conversation
- `POST /export/txt` – export chat history as text
- `POST /export/json` – export chat history as JSON
- `POST /voice/synthesize` – synthesize speech from text
- `GET /voice/check` – check voice support availability

## ⚠️ Notes

- Voice features depend on browser permissions and support
- Some APIs require valid credentials to provide richer responses
- Chat history is currently stored in memory, so it is reset on server restart

## 🤝 Contribution

Feel free to improve the project by adding:
- better UI/UX
- more robust error handling
- persistent storage for conversations
- authentication
- async processing for external APIs

## 📄 License

This project is intended for educational and portfolio purposes.
