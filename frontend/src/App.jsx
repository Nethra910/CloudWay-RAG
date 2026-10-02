import { useEffect, useRef, useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import "./App.css";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

const STARTERS = [
  "How much cabin baggage can I carry?",
  "What happens if my flight is cancelled?",
  "Can I change my booking after paying?",
  "Do you offer help for passengers with reduced mobility?",
];

const prettyName = (path) =>
  path
    .split("/")
    .pop()
    .replace(/\.pdf$/i, "")
    .replace(/[_-]+/g, " ");

function Source({ file, snippet }) {
  const [open, setOpen] = useState(false);
  return (
    <li className="source">
      <button
        className="tag"
        aria-expanded={open}
        onClick={() => setOpen(!open)}
      >
        {prettyName(file)}
      </button>
      {open && <p className="snippet">{snippet}…</p>}
    </li>
  );
}

function Message({ m }) {
  if (m.role === "user") return <div className="msg user">{m.content}</div>;
  return (
    <div className="msg bot">
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          table: ({ node, ...props }) => (
            <div className="table-wrap">
              <table {...props} />
            </div>
          ),
        }}
      >
        {m.content}
      </ReactMarkdown>
      {m.sources?.length > 0 && (
        <details className="sources">
          <summary>
            Found in {m.sources.length} document
            {m.sources.length > 1 ? "s" : ""}
          </summary>
          <ul>
            {m.sources.map((s) => (
              <Source key={s.file} {...s} />
            ))}
          </ul>
        </details>
      )}
    </div>
  );
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  // Display history stays complete; only unsummarised turns go to the model.
  const memory = useRef({ text: "", consumed: 0 });
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages, busy]);

  async function send(text) {
    const q = text.trim();
    if (!q || busy) return;
    setError("");
    setInput("");
    const prior = messages
      .slice(memory.current.consumed)
      .map(({ role, content }) => ({ role, content }));
    setMessages((m) => [...m, { role: "user", content: q }]);
    setBusy(true);
    try {
      const res = await fetch(`${API}/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: q,
          history: prior,
          summary: memory.current.text,
        }),
      });
      if (!res.ok) throw new Error(res.status);
      const data = await res.json();
      memory.current = {
        text: data.summary,
        consumed: memory.current.consumed + data.consumed,
      };
      setMessages((m) => [
        ...m,
        { role: "assistant", content: data.answer, sources: data.sources },
      ]);
    } catch {
      setMessages((m) => m.slice(0, -1));
      setInput(q);
      setError(
        "Couldn't reach the assistant. Make sure the API is running on port 8000, then send again.",
      );
    } finally {
      setBusy(false);
    }
  }

  function newChat() {
    setMessages([]);
    setError("");
    memory.current = { text: "", consumed: 0 };
  }

  return (
    <div className="app">
      <header>
        <span className="brand">
          CloudWay<b>24</b>
        </span>
        {messages.length > 0 && (
          <button className="ghost" onClick={newChat}>
            New chat
          </button>
        )}
      </header>

      <main>
        {messages.length === 0 ? (
          <section className="empty">
            <h1>Ask about flights, bags or bookings.</h1>
            <p>
              Answers come from CloudWay's own policy documents, and every
              answer shows where it was found.
            </p>
            <ul>
              {STARTERS.map((s) => (
                <li key={s}>
                  <button onClick={() => send(s)}>{s}</button>
                </li>
              ))}
            </ul>
          </section>
        ) : (
          <div className="thread" aria-live="polite">
            {messages.map((m, i) => (
              <Message key={i} m={m} />
            ))}
            {busy && (
              <div className="msg bot pending">
                Checking the policy documents
                <span className="dots" />
              </div>
            )}
          </div>
        )}
        <div ref={endRef} />
      </main>

      <footer>
        {error && (
          <p className="error" role="alert">
            {error}
          </p>
        )}
        <div className="composer">
          <textarea
            rows={1}
            value={input}
            placeholder="Type your question"
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send(input);
              }
            }}
          />
          <button onClick={() => send(input)} disabled={busy || !input.trim()}>
            Send
          </button>
        </div>
        <p className="hint">Enter to send, Shift+Enter for a new line</p>
      </footer>
    </div>
  );
}
