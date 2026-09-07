import { useState } from "react";
import { learningApi } from "./api";
import { Badge, Button, Modal } from "../../ui/components";
import type { Overview, SkillDTO } from "./types";
const TRACK_TONE: Record<string, "accent" | "success" | "neutral" | "warning" | "danger"> = {
    "CS Foundations": "accent",
    "AI & Data": "success",
};
export function PathMap({ overview, onTargetSet, }: {
    overview: Overview;
    onTargetSet: () => void;
}) {
    const [selected, setSelected] = useState<SkillDTO | null>(null);
    const [busy, setBusy] = useState(false);
    const byId = new Map(overview.curriculum.skills.map((s) => [s.skill_id, s]));
    async function setTarget() {
        if (!selected)
            return;
        setBusy(true);
        try {
            await learningApi.setTarget(selected.skill_id);
            onTargetSet();
            setSelected(null);
        }
        finally {
            setBusy(false);
        }
    }
    const columns: SkillDTO[][] = [];
    for (const sid of overview.curriculum.order) {
        const skill = byId.get(sid);
        if (!skill)
            continue;
        const col = Math.min(skill.prerequisites.length
            ? Math.max(...skill.prerequisites.map((p) => (byId.get(p) ? orderIndex(overview, p) + 1 : 0)))
            : 0, 5);
        while (columns.length <= col)
            columns.push([]);
        columns[col].push(skill);
    }
    return (<div className="page">
      <div className="spread">
        <div>
          <h1 style={{ margin: 0 }}>Skill map</h1>
          <p style={{ color: "var(--text-2)", margin: "8px 0 0" }}>
            Prerequisites flow left → right. Pick any skill as your target and the engine will
            unlock the cheapest route to it.
          </p>
        </div>
        {overview.target_skill && (<Badge tone="accent">target: {byId.get(overview.target_skill)?.title ?? overview.target_skill}</Badge>)}
      </div>

      <div style={{ display: "grid", gridTemplateColumns: `repeat(${columns.length}, minmax(150px, 1fr))`, gap: 12, overflowX: "auto" }}>
        {columns.map((col, i) => (<div key={i} className="stack" style={{ alignContent: "start" }}>
            <div style={{ fontSize: 11, color: "var(--text-3)", textTransform: "uppercase", letterSpacing: 1 }}>
              Stage {i + 1}
            </div>
            {col.map((skill) => {
                const state = overview.state_map[skill.skill_id];
                const isNext = skill.skill_id === overview.next_skill;
                const locked = !state &&
                    skill.prerequisites.some((p) => !(overview.state_map[p] && overview.state_map[p].mastery >= 70));
                return (<button key={skill.skill_id} onClick={() => setSelected(skill)} className="btn btn-secondary" style={{
                        flexDirection: "column",
                        alignItems: "flex-start",
                        gap: 6,
                        textAlign: "left",
                        whiteSpace: "normal",
                        borderColor: isNext ? "var(--accent)" : undefined,
                        boxShadow: isNext ? "0 0 0 2px var(--accent-soft)" : undefined,
                        opacity: locked ? 0.5 : 1,
                    }}>
                  <span style={{ fontWeight: 600, fontSize: 13 }}>{skill.title}</span>
                  <span className="row" style={{ gap: 4 }}>
                    <Badge tone={TRACK_TONE[skill.track] ?? "neutral"}>{skill.track.split(" ")[0]}</Badge>
                    {state?.mastered ? (<Badge tone="success">{Math.round(state.mastery)}% ✓</Badge>) : state ? (<Badge tone="accent">{Math.round(state.mastery)}%</Badge>) : (<Badge tone="neutral">{locked ? "locked" : "new"}</Badge>)}
                  </span>
                </button>);
            })}
          </div>))}
      </div>

      <Modal open={selected !== null} title={selected?.title ?? ""} onClose={() => setSelected(null)} footer={<>
            <Button variant="secondary" onClick={() => setSelected(null)}>
              Close
            </Button>
            <Button loading={busy} onClick={() => void setTarget()}>
              Make this my target
            </Button>
          </>}>
        {selected && (<div className="stack">
            <Badge tone={TRACK_TONE[selected.track] ?? "neutral"}>{selected.track}</Badge>
            <p style={{ margin: 0 }}>{selected.description}</p>
            <p style={{ margin: 0, fontSize: 14, color: "var(--text-2)" }}>
              {selected.concept}
            </p>
            <div className="row">
              <Badge tone="neutral">difficulty {selected.difficulty}/5</Badge>
              {selected.prerequisites.map((p) => (<Badge key={p} tone="neutral">
                  needs {byId.get(p)?.title ?? p}
                </Badge>))}
            </div>
            {overview.state_map[selected.skill_id] && (<ProgressNote mastery={overview.state_map[selected.skill_id].mastery} encounters={overview.state_map[selected.skill_id].encounters} due={overview.state_map[selected.skill_id].due_date}/>)}
          </div>)}
      </Modal>
    </div>);
}
function orderIndex(overview: Overview, skillId: string): number {
    return overview.curriculum.order.indexOf(skillId);
}
function ProgressNote({ mastery, encounters, due }: {
    mastery: number;
    encounters: number;
    due: string;
}) {
    return (<div className="row" style={{ gap: 8 }}>
      <Badge tone="accent">your mastery {Math.round(mastery)}%</Badge>
      <Badge tone="neutral">{encounters} encounters</Badge>
      <Badge tone="neutral">next review {due}</Badge>
    </div>);
}
