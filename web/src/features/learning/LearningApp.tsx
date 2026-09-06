/** Adaptive Learning Studio root: landing → auth → dashboard / session / map / tutor. */
import { useCallback, useEffect, useState } from "react";
import { learningApi } from "./api";
import { Dashboard } from "./Dashboard";
import { PathMap } from "./PathMap";
import { Session } from "./Session";
import { Tutor } from "./Tutor";
import { useAuth } from "../../lib/auth";
import { Badge, Button, Card, ErrorBanner, Input, Spinner, cx } from "../../ui/components";
import type { Overview } from "./types";

type View = "landing" | "dashboard" | "session" | "map" | "tutor";

export function LearningApp() {
  const auth = useAuth();
  const [view, setView] = useState<View>("landing");
  const [overview, setOverview] = useState<Overview | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!auth.user) return;
    setLoading(true);
    setError(null);
    try {
      const data = await learningApi.overview();
      setOverview(data);
      setView(data.next_skill ? "dashboard" : "session");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [auth.user]);

  useEffect(() => {
    if (!auth.user) {
      setView("landing");
      return;
    }
    void load();
  }, [auth.user, load]);

  if (!auth.user) return <Landing />;

  if (auth.booting || (loading && !overview)) {
    return (
      <div className="page" style={{ display: "grid", placeItems: "center", minHeight: "50vh" }}>
        <Spinner size={28} />
      </div>
    );
  }

  return (
    <div>
      <nav className="row" style={{ padding: "14px 0", gap: 8 }}>
        {(
          [
            ["dashboard", "Dashboard"],
            ["session", "Learn"],
            ["map", "Skill map"],
            ["tutor", "Tutor"],
          ] as [View, string][]
        ).map(([v, label]) => (
          <button
            key={v}
            className={cx("btn", view === v ? "btn-primary" : "btn-secondary", "btn-sm")}
            onClick={() => setView(v)}
          >
            {label}
          </button>
        ))}
      </nav>
      <ErrorBanner message={error} />
      {view === "dashboard" && overview && (
        <Dashboard overview={overview} onFinished={() => void load()} onStartSession={() => setView("session")} />
      )}
      {view === "session" && <Session onFinished={() => void load()} />}
      {view === "map" && overview && <PathMap overview={overview} onTargetSet={() => void load()} />}
      {view === "tutor" && overview && <Tutor overview={overview} />}
    </div>
  );
}

function Landing() {
  const auth = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit() {
    if (!email || !password || (mode === "register" && !name)) {
      setError("Fill in all fields.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      if (mode === "login") await auth.login(email, password);
      else await auth.register(email, password, name);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <section
        style={{
          textAlign: "center",
          padding: "var(--space-8) var(--space-4)",
          display: "grid",
          gap: 16,
          justifyItems: "center",
        }}
      >
        <Badge tone="accent">🧠 Adaptive AI learning engine · GIBC V2</Badge>
        <h1 style={{ fontSize: "clamp(30px, 6vw, 52px)", maxWidth: 780, margin: 0 }}>
          A tutor that <span style={{ color: "var(--accent)" }}>watches you learn</span>.
        </h1>
        <p style={{ maxWidth: 640, color: "var(--text-2)", fontSize: 17, margin: 0 }}>
          Every answer updates a mastery model and a spaced-repetition schedule, so the next
          question is always the one you need most. Explanations, misconceptions and study
          tips come from an engineered AI layer — no more one-size-fits-all quizzes.
        </p>
      </section>

      <div className="grid-2" style={{ maxWidth: 900, margin: "0 auto" }}>
        {[
          ["🎯", "Knows what you know", "A per-skill ability estimate (logistic mastery model) shifts with every answer, weighted by question difficulty."],
          ["🗺️", "Chooses your path", "A prerequisite graph drives which skill unlocks next — while spaced repetition replays exactly what you're about to forget."],
          ["💡", "Explains, not just scores", "Wrong answers generate specific explanations built around the misconception you likely held."],
        ].map(([icon, title, body], i) => (
          <Card key={title} style={{ textAlign: "left" }}>
            <div style={{ fontSize: 28 }}>{icon}</div>
            <h3 style={{ margin: "10px 0 6px" }}>
              {i + 1}. {title}
            </h3>
            <p style={{ margin: 0, fontSize: 14, color: "var(--text-2)" }}>{body}</p>
          </Card>
        ))}
      </div>

      <div style={{ maxWidth: 460, margin: "var(--space-7) auto 0" }}>
        <Card className="stack">
          <span className="spread">
            <h3 style={{ margin: 0 }}>{mode === "login" ? "Welcome back" : "Create an account"}</h3>
          </span>
          <ErrorBanner message={error} />
          {mode === "register" && (
            <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} />
          )}
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          <Button size="lg" loading={busy} onClick={() => void submit()}>
            {mode === "login" ? "Log in" : "Create account"}
          </Button>
          <button
            className="btn btn-ghost"
            style={{ width: "100%" }}
            onClick={() => setMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login" ? "New here? Create an account" : "Have an account? Log in"}
          </button>
          {mode === "login" && (
            <p style={{ fontSize: 12, color: "var(--text-3)", margin: 0, textAlign: "center" }}>
              Demo account: demo@example.com · demo-password-123
            </p>
          )}
        </Card>
      </div>
    </div>
  );
}
