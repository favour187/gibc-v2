import { useState } from "react";
import { learningApi } from "./api";
import { Badge, Button, Card, EmptyState, ProgressBar } from "../../ui/components";
import type { Overview, SkillDTO } from "./types";
export function Dashboard({ overview, onFinished, onStartSession, }: {
    overview: Overview;
    onFinished: () => void;
    onStartSession: () => void;
}) {
    const [target, setTarget] = useState(overview.target_skill ?? overview.next_skill ?? "");
    const [busy, setBusy] = useState(false);
    const [customMessage, setCustomMessage] = useState<string | null>(null);
    const p = overview.progress;
    const next = overview.next_skill ? overview.curriculum.skills.find((s) => s.skill_id === overview.next_skill) : null;
    async function setTargetSkill() {
        if (!target)
            return;
        setBusy(true);
        try {
            await learningApi.setTarget(target);
            setCustomMessage(null);
            onFinished();
        }
        catch (err) {
            setCustomMessage((err as Error).message);
        }
        finally {
            setBusy(false);
        }
    }
    function startSession() {
        onStartSession();
    }
    return (<div className="page">
      <div className="spread">
        <div>
          <h1 style={{ margin: 0 }}>Your learning</h1>
          <p style={{ color: "var(--text-2)", margin: "8px 0 0" }}>
            {overview.curriculum.total_skills} skills · {overview.curriculum.tracks.join(" + ")}
          </p>
        </div>
        <div className="row">
          <Badge tone={overview.streak > 0 ? "success" : "neutral"}>🔥 {overview.streak}-day streak</Badge>
          <Badge tone={overview.due_count > 0 ? "warning" : "success"}>
            {overview.due_count} review{overview.due_count === 1 ? "" : "s"} due
          </Badge>
        </div>
      </div>

      <div className="grid-2">
        <Card className="stack">
          <span className="spread">
            <h3 style={{ margin: 0 }}>Mastery</h3>
            <Badge tone="accent">{p.mastered}/{p.total} mastered</Badge>
          </span>
          <ProgressBar value={p.average_mastery} label={`Average mastery · ${p.average_mastery}%`}/>
          <div className="row" style={{ gap: 8 }}>
            <Badge tone="success">{p.mastered} mastered</Badge>
            <Badge tone="accent">{p.in_progress} in progress</Badge>
            <Badge tone="neutral">{p.not_started} not started</Badge>
          </div>
        </Card>

        <Card className="stack">
          <h3 style={{ margin: 0 }}>Next up</h3>
          {next ? (<>
              <p style={{ margin: 0, fontSize: 17, fontWeight: 600 }}>{next.title}</p>
              <p style={{ margin: 0, fontSize: 13, color: "var(--text-2)" }}>{next.description}</p>
              <div className="row">
                <Badge tone="neutral">{next.track}</Badge>
                <Badge tone="neutral">difficulty {next.difficulty}/5</Badge>
                <Badge tone="neutral">
                  needs {next.prerequisites.length} prereq{next.prerequisites.length === 1 ? "" : "s"}
                </Badge>
              </div>
            </>) : (<EmptyState title="You've mastered the curriculum!" body="Amazing — try a harder track or keep reviews fresh."/>)}
          <Button size="lg" onClick={startSession}>
            Start session (8 questions)
          </Button>
          {customMessage && <ErrorBannerUI message={customMessage}/>}
        </Card>
      </div>

      <Card>
        <span className="spread">
          <h3 style={{ margin: 0 }}>Frontier — what's unlocked now</h3>
          <Badge tone="neutral">{overview.frontier.length} skills</Badge>
        </span>
        <div style={{ display: "grid", gap: 8 }}>
          {overview.frontier.map((sid) => {
            const skill = overview.curriculum.skills.find((s) => s.skill_id === sid);
            const state = overview.state_map[sid];
            if (!skill)
                return null;
            return (<div key={sid} className="spread" style={{ padding: "10px 12px", border: "1px solid var(--border)", borderRadius: 10 }}>
                <div>
                  <strong style={{ fontSize: 14 }}>{skill.title}</strong>
                  <span style={{ fontSize: 12, color: "var(--text-3)", marginLeft: 8 }}>
                    {state ? `${state.mastery}% mastery` : "not started"}
                  </span>
                </div>
                <Badge tone={skill.track === "AI & Data" ? "success" : "neutral"}>{skill.track}</Badge>
              </div>);
        })}
        </div>
      </Card>

      <Card className="stack">
        <span className="spread">
          <h3 style={{ margin: 0 }}>Learning goal</h3>
          <Badge tone="accent">adaptive</Badge>
        </span>
        <p style={{ margin: 0, fontSize: 14, color: "var(--text-2)" }}>
          Choose a target skill and the engine will steer your path toward it, unlocking prerequisites
          in the most efficient order.
        </p>
        <div className="row">
          <select className="input" style={{ maxWidth: 320 }} value={target} onChange={(e) => setTarget(e.target.value)}>
            <option value="">— follow the default path —</option>
            {overview.curriculum.skills.map((s: SkillDTO) => (<option key={s.skill_id} value={s.skill_id}>
                {s.title} ({s.track})
              </option>))}
          </select>
          <Button variant="secondary" loading={busy} onClick={() => void setTargetSkill()}>
            Set target
          </Button>
          {overview.target_reached && <Badge tone="success">target reached 🎉</Badge>}
        </div>
      </Card>
    </div>);
}
function ErrorBannerUI({ message }: {
    message: string;
}) {
    return <div className="error-banner" role="alert">{message}</div>;
}
