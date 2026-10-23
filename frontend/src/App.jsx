
import { useState, useRef, useEffect } from "react";
import "./App.css";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

const API_URL = "http://127.0.0.1:8000/api/chat";

const INITIAL_MESSAGE = {
  role: "assistant",
  content:
    "Hello! 👋 I'm your NewsWiki assistant. I can answer general questions, find recent news, and explain topics using Wikipedia. What would you like to explore?",
  source: "Chatbot",
  results: [],
};

function formatDate(value) {
  if (!value) return "";

  const date = new Date(value);

  if (Number.isNaN(date.getTime())) return value;

  return date.toLocaleString(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  });
}

function SourceCards({ sources = [] }) {
  if (!sources.length) return null;

  return (
    <div className="results">
      {sources.map((source, index) => {
        const isValidUrl =
          typeof source.url === "string" &&
          ["https://", "http://"].some((prefix) =>
            source.url.startsWith(prefix)
          );

        return (
          <article
            className="result-card"
            key={`${source.url || source.title}-${index}`}
          >
            <h3>{source.title || `Source ${index + 1}`}</h3>

            {source.publisher && (
              <p className="source-name">
                Publisher: {source.publisher}
              </p>
            )}

            {source.published && (
              <p className="published">
                {source.date_label || "Published"}: {formatDate(source.published)}
              </p>
            )}

            {isValidUrl && (
              <a
                href={source.url}
                target="_blank"
                rel="noopener noreferrer"
              >
                Read source ↗
              </a>
            )}
          </article>
        );
      })}
    </div>
  );
}

function MessageBubble({ message }) {
  const isAssistant = message.role === "assistant";
  const showSourceCards = isAssistant && message.source !== "news";

  return (
    <div className={`message-row ${message.role}`}>
      <div className="avatar" aria-hidden="true">
        {isAssistant ? "N" : "Y"}
      </div>

      <div className="message-content">
        <div className="message-label">
          {isAssistant ? "NewsWiki" : "You"}
        </div>

        <div className="bubble markdown-body">
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            components={{
              a: ({ href, children, ...props }) => (
                <a
                  {...props}
                  href={href}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {children}
                </a>
              ),
            }}
          >
            {message.content || ""}
          </ReactMarkdown>
        </div>

        {isAssistant && message.source && message.source !== "news" && (
          <div className="source-label">
            Source type: {message.source}
          </div>
        )}

        {showSourceCards && (
          <SourceCards sources={message.results || []} />
        )}
      </div>
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([INITIAL_MESSAGE]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const bottomRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [messages, loading]);

  async function handleSubmit(event, suggestedPrompt) {
    event?.preventDefault();

    const question = (suggestedPrompt ?? input).trim();

    if (!question || loading) return;

    setInput("");
    setError("");
    setLoading(true);

    // Preserve the previous conversation for contextual answers.
    const history = messages
      .filter(
        (item) =>
          ["user", "assistant"].includes(item.role) &&
          typeof item.content === "string"
      )
      .slice(-20)
      .map((item) => ({
        role: item.role,
        content: item.content,
      }));

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: question,
      },
    ]);

    try {
      const response = await fetch(API_URL, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          message: question,
          history,
        }),
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(
          data.detail ||
            data.answer ||
            `Request failed with status ${response.status}.`
        );
      }

      // FastAPI returns the original service format:
      // { answer, source_type, sources }
      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content:
            data.answer || "I couldn't generate an answer. Please try again.",
          source: data.source_type || "general",
          results: Array.isArray(data.sources) ? data.sources : [],
        },
      ]);
    } catch (err) {
      setError(
        err.message === "Failed to fetch"
          ? "Unable to connect to the FastAPI backend. Make sure it is running at http://127.0.0.1:8000."
          : err.message || "Something went wrong. Please try again."
      );
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  }

  function startNewChat() {
    if (loading) return;

    setMessages([INITIAL_MESSAGE]);
    setInput("");
    setError("");
    inputRef.current?.focus();
  }

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

        <button
          className="new-chat"
          type="button"
          onClick={startNewChat}
          disabled={loading}
        >
          <span aria-hidden="true">＋</span> New chat
        </button>

        <div className="sidebar-footer">
          <span>Powered by</span>
          <strong>React + FastAPI + Groq</strong>
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
              />
            ))}

            {loading && (
              <div className="message-row assistant">
                <div className="avatar" aria-hidden="true">
                  N
                </div>

                <div className="message-content">
                  <div className="message-label">NewsWiki</div>

                  <div className="bubble typing">
                    Thinking and searching
                    <span>.</span>
                    <span>.</span>
                    <span>.</span>
                  </div>
                </div>
              </div>
            )}

            <div ref={bottomRef} />
          </div>

          {error && (
            <div className="error-message" role="alert">
              <strong>Request failed</strong>
              <p>{error}</p>
              <button
                type="button"
                onClick={() => {
                  setError("");
                  inputRef.current?.focus();
                }}
              >
                Dismiss
              </button>
            </div>
          )}

          <form
            className="composer"
            onSubmit={(event) => handleSubmit(event)}
          >
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
              type="submit"
              disabled={loading || !input.trim()}
            >
              {loading ? "..." : "Send ↑"}
            </button>
          </form>

          <p className="disclaimer">
            AI-generated answers may contain mistakes. Check the original
            sources for important or time-sensitive information.
          </p>
        </section>
      </main>
    </div>
  );
}
