import { useCallback, useEffect, useState } from "react";
import { learningApi } from "./api";
import { Badge, Button, Card, ErrorBanner, ProgressBar, Spinner, cx } from "../../ui/components";
import type { GradeResult, SessionData } from "./types";
type Phase = "loading" | "question" | "feedback" | "summary";
export function Session({ onFinished }: {
    onFinished: () => void;
}) {
    const [data, setData] = useState<SessionData | null>(null);
    const [index, setIndex] = useState(0);
    const [phase, setPhase] = useState<Phase>("loading");
    const [chosen, setChosen] = useState<number | null>(null);
    const [result, setResult] = useState<GradeResult | null>(null);
    const [correctCount, setCorrectCount] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const loadSession = useCallback(async () => {
        setPhase("loading");
        setError(null);
        try {
            const session = await learningApi.session();
            setData(session);
            setIndex(0);
            setCorrectCount(0);
            setPhase(session.questions.length ? "question" : "summary");
        }
        catch (err) {
            setError((err as Error).message);
            setPhase("summary");
        }
    }, []);
    useEffect(() => {
        void loadSession();
    }, [loadSession]);
    const question = data?.questions[index] ?? null;
    const skillTitle = question ? data?.skill_titles[question.skill_id] ?? question.skill_id : "";
    async function submit() {
        if (!question || chosen === null)
            return;
        try {
            const res = await learningApi.grade(question.question_id, chosen);
            setResult(res);
            if (res.record.correct)
                setCorrectCount((c) => c + 1);
            setPhase("feedback");
        }
        catch (err) {
            setError((err as Error).message);
        }
    }
    function next() {
        if (!data)
            return;
        if (index + 1 < data.questions.length) {
            setIndex(index + 1);
            setChosen(null);
            setResult(null);
            setPhase("question");
        }
        else {
            void learningApi.finish(data.questions.length, correctCount);
            setPhase("summary");
        }
    }
    if (phase === "loading") {
        return (<div style={{ display: "grid", placeItems: "center", minHeight: "40vh" }}>
        <Spinner size={26}/>
      </div>);
    }
    if (phase === "summary" || !question || !data) {
        return (<div className="page" style={{ maxWidth: 640, margin: "0 auto" }}>
        <Card className="stack" style={{ textAlign: "center" }}>
          <h1>Session complete 🎉</h1>
          <p style={{ color: "var(--text-2)" }}>
            {data && data.questions.length > 0
                ? `You answered ${correctCount}/${data.questions.length} correctly. Every answer adjusted your mastery model — reviews are now scheduled at the right moment.`
                : "No questions were available — you may have mastered everything for now."}
          </p>
          <div className="row" style={{ justifyContent: "center" }}>
            <Button onClick={() => void loadSession()}>Another session</Button>
            <Button variant="secondary" onClick={onFinished}>
              Back to dashboard
            </Button>
          </div>
          {error && <ErrorBanner message={error}/>}
        </Card>
      </div>);
    }
    return (<div className="page" style={{ maxWidth: 720, margin: "0 auto" }}>
      <div className="spread">
        <Badge tone="accent">
          {index + 1} / {data.questions.length}
        </Badge>
        <Badge tone={question.source === "review" ? "warning" : question.source === "weak" ? "accent" : "neutral"}>
          {question.source === "review" ? "scheduled review" : question.source === "weak" ? "weak spot" : "new material"}
        </Badge>
      </div>
      <ProgressBar value={((index + (phase === "feedback" ? 1 : 0)) / data.questions.length) * 100}/>

      <Card className="stack">
        <div className="row" style={{ gap: 8 }}>
          <Badge tone="neutral">{skillTitle}</Badge>
          <Badge tone="neutral">difficulty {question.difficulty}/5</Badge>
        </div>
        <h2 style={{ margin: 0, fontSize: 20, lineHeight: 1.4 }}>{question.stem}</h2>

        <div className="stack">
          {question.options.map((option, i) => {
            return (<button key={i} className={cx("btn", chosen === i ? "btn-primary" : "btn-secondary", "btn-lg")} style={{ justifyContent: "flex-start", width: "100%", whiteSpace: "normal" }} disabled={phase !== "question"} onClick={() => setChosen(i)}>
                <span style={{ fontWeight: 700, marginRight: 10 }}>{String.fromCharCode(65 + i)}.</span>
                {option}
              </button>);
        })}
        </div>

        {phase === "question" ? (<Button size="lg" disabled={chosen === null} onClick={() => void submit()}>
            Check answer
          </Button>) : result ? (<div className="stack">
            <div className={cx("error-banner", result.record.correct && "correct-banner")} style={result.record.correct
                ? { background: "var(--success-soft)", color: "var(--success)" }
                : undefined}>
              <strong>{result.record.correct ? "Correct ✓" : "Not quite."}</strong> The answer is{" "}
              <strong>{result.question.correct_answer}</strong>
              <p style={{ margin: "8px 0 0" }}>{result.question.explanation}</p>
              {!result.record.correct && result.question.misconception && (<p style={{ margin: "8px 0 0", opacity: 0.9 }}>
                  <em>Watch out: {result.question.misconception}</em>
                </p>)}
            </div>
            <div className="row" style={{ gap: 8 }}>
              <Badge tone="accent">mastery {result.skill.mastery}%</Badge>
              <Badge tone="neutral">
                next review {result.record.interval_days_after > 0 ? `in ${result.record.interval_days_after}d` : "tomorrow"}
              </Badge>
            </div>
            <Button size="lg" onClick={next}>
              {index + 1 < data.questions.length ? "Next question" : "Finish session"}
            </Button>
          </div>) : null}
        {error && <ErrorBanner message={error}/>}
      </Card>
    </div>);
}
