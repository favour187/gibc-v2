import { useRef, useState } from "react";
import { learningApi } from "./api";
import { Badge, Button, ErrorBanner, Spinner } from "../../ui/components";
import type { Overview } from "./types";
interface Message {
    role: "user" | "assistant";
    text: string;
}
const SUGGESTIONS = [
    "Explain binary search",
    "What is overfitting?",
    "I'm not motivated today",
    "Give me a study tip",
];
export function Tutor({ overview }: {
    overview: Overview;
}) {
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState("");
    const [busy, setBusy] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const listRef = useRef<HTMLDivElement>(null);
    async function send(text: string) {
        const trimmed = text.trim();
        if (!trimmed || busy)
            return;
        setError(null);
        setMessages((m) => [...m, { role: "user", text: trimmed }]);
        setInput("");
        setBusy(true);
        try {
            const res = await learningApi.tutor(trimmed);
            setMessages((m) => [...m, { role: "assistant", text: res.reply }]);
            requestAnimationFrame(() => listRef.current?.scrollTo({ top: 99999, behavior: "smooth" }));
        }
        catch (err) {
            setError((err as Error).message);
        }
        finally {
            setBusy(false);
        }
    }
    const frontier_count = overview.frontier.length;
    return (<div className="page" style={{ maxWidth: 760, margin: "0 auto" }}>
      <div className="spread">
        <div>
          <h1 style={{ margin: 0 }}>Tutor</h1>
          <p style={{ color: "var(--text-2)", margin: "8px 0 0" }}>
            Curriculum-aware explanations. {overview.due_count} review(s) due · {frontier_count} frontier
            skills unlocked.
          </p>
        </div>
        <Badge tone="warning">verified against the curriculum</Badge>
      </div>

      <div ref={listRef} style={{
            display: "grid",
            gap: 10,
            alignContent: "start",
            minHeight: 320,
            maxHeight: 420,
            overflowY: "auto",
            paddingRight: 4,
        }}>
        {messages.length === 0 && (<div className="empty-state" style={{ padding: "var(--space-5)" }}>
            <h3 style={{ marginBottom: 8 }}>Ask anything</h3>
            <p style={{ margin: 0, fontSize: 13 }}>
              Try "explain overfitting", "what is recursion", or a wrong-answer question id from a quiz.
            </p>
          </div>)}
        {messages.map((m, i) => (<div key={i} style={{
                maxWidth: "85%",
                padding: "10px 14px",
                borderRadius: 14,
                fontSize: 14,
                whiteSpace: "pre-wrap",
                background: m.role === "user" ? "var(--accent)" : "var(--surface-2)",
                color: m.role === "user" ? "#fff" : "var(--text)",
                justifySelf: m.role === "user" ? "end" : "start",
            }}>
            {m.text}
          </div>))}
        {busy && <Spinner size={16}/>}
      </div>

      <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
        {SUGGESTIONS.map((s) => (<button key={s} className="btn btn-secondary btn-sm" disabled={busy} onClick={() => void send(s)}>
            {s}
          </button>))}
      </div>

      <ErrorBanner message={error}/>
      <form className="row" style={{ alignItems: "stretch" }} onSubmit={(e) => {
            e.preventDefault();
            void send(input);
        }}>
        <input className="input" style={{ flex: 1 }} value={input} onChange={(e) => setInput(e.target.value)} placeholder="Ask the tutor…" aria-label="Tutor message"/>
        <Button type="submit" loading={busy}>
          Send
        </Button>
      </form>
    </div>);
}
