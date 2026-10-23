import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import "./App.css";

const API_URL = "http://127.0.0.1:8000/api";
const TOKEN_KEY = "newwiki_session";

const INITIAL_MESSAGE = {
  role: "assistant",
  content:
    "Hello! 👋 I'm your NewsWiki assistant. I can answer general questions, find recent news, and explain topics using Wikipedia. What would you like to explore?",
  source_type: "Chatbot",
  sources: [],
};

async function apiRequest(path, { token, ...options } = {}) {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      ...(options.body ? { "Content-Type": "application/json" } : {}),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = new Error(data.detail || `Request failed with status ${response.status}.`);
    error.status = response.status;
    throw error;
  }
  return data;
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function SourceCards({ sources = [] }) {
  if (!sources.length) return null;

  return (
    <div className="results">
      {sources.map((source, index) => {
        const isValidUrl =
          typeof source.url === "string" &&
          ["https://", "http://"].some((prefix) => source.url.startsWith(prefix));

        return (
          <article className="result-card" key={`${source.url || source.title}-${index}`}>
            <h3>{source.title || `Source ${index + 1}`}</h3>
            {source.publisher && <p className="source-name">Publisher: {source.publisher}</p>}
            {source.published && (
              <p className="published">
                {source.date_label || "Published"}: {formatDate(source.published)}
              </p>
            )}
            {isValidUrl && (
              <a href={source.url} target="_blank" rel="noopener noreferrer">
                Read source ↗
              </a>
            )}
          </article>
        );
      })}
    </div>
  );
}

function MessageBubble({ message, userInitial, onSpeak }) {
  const isAssistant = message.role === "assistant";
  const showSourceCards = isAssistant;

  return (
    <div className={`message-row ${message.role}`}>
      <div className="avatar" aria-hidden="true">
        {isAssistant ? "N" : userInitial}
      </div>
      <div className="message-content">
        <div className="message-label">{isAssistant ? "NewsWiki" : "You"}</div>
        <div className="bubble markdown-body">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({ href, children, ...props }) => (
                <a {...props} href={href} target="_blank" rel="noopener noreferrer">
                  {children}
                </a>
              ),
            }}
          >
            {message.content || ""}
          </ReactMarkdown>
        </div>
        {isAssistant && message.content && (
          <button
            className="speak-button"
            type="button"
            onClick={() => onSpeak(message.content)}
            aria-label="Read this answer aloud"
            title="Read this answer aloud"
          >
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M3 9v6h4l5 4V5L7 9H3Z" />
              <path d="M16 9.5a4 4 0 0 1 0 5M18.5 7a7.5 7.5 0 0 1 0 10" />
            </svg>
          </button>
        )}
        {isAssistant && message.source_type && message.source_type !== "news" && (
          <div className="source-label">Source type: {message.source_type}</div>
        )}
        {showSourceCards && <SourceCards sources={message.sources || []} />}
      </div>
    </div>
  );
}

function AuthPage({ onAuthenticated }) {
  const [mode, setMode] = useState("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event) {
    event.preventDefault();
    if (loading) return;
    setLoading(true);
    setError("");
    try {
      const data = await apiRequest(`/auth/${mode === "login" ? "login" : "register"}`, {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });
      onAuthenticated(data);
    } catch (requestError) {
      setError(
        requestError.message === "Failed to fetch"
          ? "Unable to connect to the backend. Make sure it is running."
          : requestError.message
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <form className="auth-card" onSubmit={handleSubmit}>
        <div className="brand-icon auth-brand">N</div>
        <h1>Welcome to NewsWiki</h1>
        <p className="auth-description">
          {mode === "login" ? "Log in to continue to your chats." : "Create an account to save your chat history."}
        </p>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          maxLength={254}
          required
        />
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          autoComplete={mode === "login" ? "current-password" : "new-password"}
          value={password}
          onChange={(event) => setPassword(event.target.value)}
          minLength={mode === "login" ? 1 : 8}
          maxLength={128}
          required
        />
        {error && <div className="error-message" role="alert">{error}</div>}
        <button className="auth-submit" type="submit" disabled={loading}>
          {loading ? "Please wait..." : mode === "login" ? "Log in" : "Create account"}
        </button>
        <p className="auth-switch">
          {mode === "login" ? "New to NewsWiki?" : "Already have an account?"}{" "}
          <button
            type="button"
            onClick={() => {
              setMode(mode === "login" ? "register" : "login");
              setError("");
            }}
          >
            {mode === "login" ? "Create an account" : "Log in"}
          </button>
        </p>
      </form>
    </main>
  );
}

export default function App() {
  const [token, setToken] = useState(() => sessionStorage.getItem(TOKEN_KEY));
  const [user, setUser] = useState(null);
  const [authLoading, setAuthLoading] = useState(Boolean(token));
  const [authError, setAuthError] = useState("");
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [conversations, setConversations] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [listening, setListening] = useState(false);
  const bottomRef = useRef(null);
  const inputRef = useRef(null);
  const recognitionRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, loading]);

  useEffect(() => () => {
    recognitionRef.current?.abort();
    window.speechSynthesis?.cancel();
  }, []);

  useEffect(() => {
    if (!token) return;

    let cancelled = false;
    async function restoreSession() {
      setAuthLoading(true);
      setAuthError("");
      try {
        const account = await apiRequest("/auth/me", { token });
        const history = await apiRequest("/conversations", { token });
        if (!cancelled) {
          setUser(account);
          setConversations(history);
        }
      } catch (requestError) {
        if (!cancelled) {
          if (requestError.status === 401) {
            sessionStorage.removeItem(TOKEN_KEY);
            setToken(null);
            setConversations([]);
            setAuthError(requestError.message);
          } else {
            setAuthError(requestError.message);
          }
        }
      } finally {
        if (!cancelled) setAuthLoading(false);
      }
    }

    restoreSession();
    return () => {
      cancelled = true;
    };
  }, [token]);

  function handleAuthenticated(data) {
    sessionStorage.setItem(TOKEN_KEY, data.access_token);
    setConversations([]);
    setConversationId(null);
    setMessages([INITIAL_MESSAGE]);
    setUser(data.user);
    setToken(data.access_token);
    setAuthError("");
  }

  async function refreshConversations(activeToken = token) {
    const history = await apiRequest("/conversations", { token: activeToken });
    setConversations(history);
  }

  async function sendMessage(question) {
    if (!question || loading) return;

    setInput("");
    setError("");
    setLoading(true);
    setMessages((previous) => [...previous, { role: "user", content: question }]);

    try {
      const data = await apiRequest("/chat", {
        token,
        method: "POST",
        body: JSON.stringify({ message: question, conversation_id: conversationId }),
      });
      setConversationId(data.conversation_id);
      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: data.answer || "I couldn't generate an answer. Please try again.",
          source_type: data.source_type || "general",
          sources: Array.isArray(data.sources) ? data.sources : [],
        },
      ]);
      try {
        await refreshConversations();
      } catch (refreshError) {
        setError(`Your reply was saved, but chat history could not refresh: ${refreshError.message}`);
      }
    } catch (requestError) {
      setError(
        requestError.message === "Failed to fetch"
          ? "Unable to connect to the FastAPI backend. Make sure it is running at http://127.0.0.1:8000."
          : requestError.message
      );
      if (requestError.status === 401) {
        sessionStorage.removeItem(TOKEN_KEY);
        setToken(null);
        setUser(null);
        setConversations([]);
        setConversationId(null);
        setMessages([INITIAL_MESSAGE]);
        setAuthError(requestError.message);
      } else {
        setMessages((previous) => previous.slice(0, -1));
      }
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function handleSubmit(event) {
    event?.preventDefault();
    void sendMessage(input.trim());
  }

  function speakAnswer(text) {
    if (!("speechSynthesis" in window) || !("SpeechSynthesisUtterance" in window)) {
      setError("Voice output is not supported in this browser.");
      return;
    }

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.onerror = (event) => {
      if (event.error !== "canceled" && event.error !== "interrupted") {
        setError("The browser could not play this voice response.");
      }
    };
    window.speechSynthesis.speak(utterance);
  }

  function startVoiceInput() {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setError("Voice input is not supported in this browser. Try a recent version of Chrome or Edge.");
      return;
    }
    setError("");
    setError("");
    const recognition = new SpeechRecognition();
    recognition.lang = navigator.language || "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onresult = (event) => {
      const transcript = Array.from(event.results)
        .map((result) => result[0]?.transcript || "")
        .join(" ")
        .trim();
      if (transcript) setInput(transcript);
    };
    recognition.onerror = (event) => {
      setListening(false);
      setError(
        event.error === "not-allowed"
          ? "Microphone access was denied. Allow microphone access in your browser and try again."
          : event.error === "no-speech"
            ? "No speech was detected. Please try again."
            : `Voice input failed (${event.error}). Please try again.`
      );
    };
    recognition.onend = () => {
      setListening(false);
    };

    recognitionRef.current = recognition;
    setListening(true);
    try {
      recognition.start();
    } catch (recognitionError) {
      recognitionRef.current = null;
      setListening(false);
      setError(`Could not start voice input: ${recognitionError.message}`);
    }
  }

  function stopVoiceInput() {
    recognitionRef.current?.stop();
  }

  function startNewChat() {
    if (loading) return;
    setConversationId(null);
    setMessages([INITIAL_MESSAGE]);
    setInput("");
    setError("");
    inputRef.current?.focus();
  }

  async function openConversation(id) {
    if (loading) return;
    setLoading(true);
    setError("");
    try {
      const conversation = await apiRequest(`/conversations/${id}`, { token });
      setConversationId(conversation.id);
      setMessages([
        INITIAL_MESSAGE,
        ...conversation.messages.map((message) => ({
          role: message.role,
          content: message.content,
          source_type: message.source_type,
          sources: message.sources,
        })),
      ]);
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  async function logout() {
    recognitionRef.current?.abort();
    try {
      await apiRequest("/auth/logout", { token, method: "POST" });
    } catch (requestError) {
      setAuthError(requestError.message);
    } finally {
      sessionStorage.removeItem(TOKEN_KEY);
      setToken(null);
      setUser(null);
      setConversations([]);
      setConversationId(null);
      setMessages([INITIAL_MESSAGE]);
    }
  }

  if (authLoading) {
    return <main className="auth-page"><p>Loading your account...</p></main>;
  }
  if (!user) {
    return (
      <>
        {authError && <div className="auth-notice" role="alert">{authError}</div>}
        <AuthPage onAuthenticated={handleAuthenticated} />
      </>
    );
  }

  const userInitial = user.email?.charAt(0).toUpperCase() || "Y";

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon">N</div>
          <div>
            <h2>NewsWiki</h2>
            <span>Your knowledge assistant</span>
          </div>
        </div>
        <button className="new-chat" type="button" onClick={startNewChat} disabled={loading}>
          <span aria-hidden="true">＋</span> New chat
        </button>
        <div className="history">
          <h3>Chat history</h3>
          {conversations.length ? (
            conversations.map((conversation) => (
              <button
                className={`history-item ${conversation.id === conversationId ? "active" : ""}`}
                key={conversation.id}
                type="button"
                onClick={() => openConversation(conversation.id)}
                disabled={loading}
                title={conversation.title}
              >
                {conversation.title}
              </button>
            ))
          ) : (
            <p className="history-empty">Your saved chats will appear here.</p>
          )}
        </div>
        <div className="sidebar-footer">
          <span title={user.email}>{user.email}</span>
          <button className="logout-button" type="button" onClick={logout} disabled={loading}>Log out</button>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <h1>News &amp; Wikipedia Chatbot</h1>
            <p>Explore the world, one question at a time.</p>
          </div>
          <div className="status">
            <span className="status-dot" />
            <span>{loading ? "Thinking..." : "Ready to chat"}</span>
          </div>
        </header>

        <section className="chat-area">
          <div className="messages" aria-live="polite">
            {messages.map((message, index) => (
              <MessageBubble
                key={`${index}-${message.role}`}
                message={message}
                userInitial={userInitial}
                onSpeak={speakAnswer}
              />
            ))}
            {loading && (
              <div className="message-row assistant">
                <div className="avatar" aria-hidden="true">N</div>
                <div className="message-content">
                  <div className="message-label">NewsWiki</div>
                  <div className="bubble typing">Thinking and searching<span>.</span><span>.</span><span>.</span></div>
                </div>
              </div>
            )}
            <div ref={bottomRef} />
          </div>

          {error && (
            <div className="error-message" role="alert">
              <strong>Request failed</strong>
              <p>{error}</p>
              <button type="button" onClick={() => setError("")}>Dismiss</button>
            </div>
          )}

          <form className="composer" onSubmit={handleSubmit}>
            <input
              ref={inputRef}
              type="text"
              value={input}
              onChange={(event) => setInput(event.target.value)}
              placeholder="Ask about news or any topic..."
              aria-label="Your message"
              maxLength={4000}
              disabled={loading}
            />
            <button
              className={`voice-button ${listening ? "listening" : ""}`}
              type="button"
              onClick={listening ? stopVoiceInput : startVoiceInput}
              disabled={loading}
              aria-label={listening ? "Finish voice input" : "Start voice input"}
              title={listening ? "Finish voice input" : "Speak your question"}
            >
              {listening ? "Listening..." : "🎙 Voice"}
            </button>
            <button type="submit" disabled={loading || !input.trim()}>
              {loading ? "..." : "Send ↑"}
            </button>
          </form>
          <p className="voice-hint">
            Speak a question, then press Enter or Send. Use a reply&apos;s speaker icon to hear it.
          </p>
          <p className="disclaimer">
            AI-generated answers may contain mistakes. Check the original sources for important or time-sensitive information.
          </p>
        </section>
      </main>
    </div>
  );
}
