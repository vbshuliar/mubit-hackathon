import { Component, lazy, Suspense, useEffect, useRef, useState, type ReactNode } from "react";
import {
  ArrowDown,
  ArrowRight,
  Check,
  Cpu,
  GitBranch,
  MessageSquare,
  ShieldCheck,
} from "lucide-react";
import { usePrefersReducedMotion } from "@/hooks/use-prefers-reduced-motion";
import "./workflow.css";

const WorkflowScene = lazy(() => import("./WorkflowScene"));

const chapters = [
  {
    name: "Report",
    title: "A leak is only\nthe beginning.",
    body: "A tenant reports water coming through the ceiling. Fixi gathers the facts, checks for hazards and keeps the evidence attached to one persistent case.",
    label: "Tenant report",
    quote: "Water comes through the bedroom ceiling when it rains.",
    action: "Clarify safety & access",
    outcome: "One case. A clear responsibility.",
    icon: MessageSquare,
  },
  {
    name: "Coordinate",
    title: "See the work\nbehind the work.",
    body: "The roofer needs safe access. Fixi connects the scaffolding, roof repair and removal as dependent work orders. The next step waits for its prerequisites.",
    label: "Contractor report",
    quote: "The flashing needs repair. Scaffold access is required first.",
    action: "Add scaffold prerequisite",
    outcome: "Access → repair → removal",
    icon: GitBranch,
  },
  {
    name: "Review",
    title: "Intelligence,\nwith boundaries.",
    body: "The agent proposes a typed action. Application checks validate it; an operator reviews commitments that need approval. Only the action executor can change the case.",
    label: "Operator checkpoint",
    quote: "Review the proposed visit, its scope and the evidence behind it.",
    action: "Review → approve → execute",
    outcome: "A proposal is not a booking.",
    icon: ShieldCheck,
  },
  {
    name: "Resolve",
    title: "Finished means\nactually finished.",
    body: "A completed scaffold visit does not mean a repaired roof. Required work must finish, dependencies must clear and the tenant must confirm the outcome before the case resolves.",
    label: "Verified outcome",
    quote: "The roof is repaired, the scaffold is removed and the tenant confirms.",
    action: "Check closure prerequisites",
    outcome: "Every required step accounted for.",
    icon: Check,
  },
  {
    name: "Learn",
    title: "Every correction.\nA sharper judgment.",
    body: "Mubit routes model calls and groups recurring tasks. Reviewed examples and feedback help build a focused open-model adapter. Our learning task: classify a contractor’s report against the work they were assigned.",
    label: "Illustrative correction",
    quote: "“Scaffolding is complete” means access is ready. It does not mean the roof is fixed.",
    action: "Report + scope → reviewed example",
    outcome: "Learn one repeated decision well.",
    icon: Cpu,
  },
  {
    name: "Evaluate",
    title: "Improve the model.\nKeep the guardrails.",
    body: "A candidate adapter must pass evaluation before it can replace the teacher for that task. The coordinator, approval rules and action executor retain responsibility for the repair.",
    label: "Last documented experiment · 24 Oct",
    quote:
      "Qwen3-4B adapter: 10/12 correct. Base + prompt: 5/12. Below the 85% target; fewer than 20 judged cases.",
    action: "Evaluate → qualify → route",
    outcome: "Not ready. No adapter deployment confirmed.",
    icon: ShieldCheck,
  },
];

class SceneBoundary extends Component<
  { children: ReactNode; fallback: ReactNode },
  { failed: boolean }
> {
  override state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  override render() {
    return this.state.failed ? this.props.fallback : this.props.children;
  }
}

function Diagram({ stage }: { stage: number }) {
  const labels =
    stage < 4
      ? ["Tenant report", "Scaffold access", "Roof repair", "Tenant confirmation"]
      : ["Report + scope", "Reviewed examples", "Mubit adapter", "Evaluation gate"];
  return (
    <div className="workflow-diagram" role="img" aria-label={labels.join(" then ")}>
      <GitBranch size={48} strokeWidth={1} />
      {labels.map((label, i) => (
        <div key={label}>
          <span>{label}</span>
          {i < 3 && <ArrowDown size={18} />}
        </div>
      ))}
      <small>Diagram view · the full story remains available</small>
    </div>
  );
}

export function WorkflowStory() {
  const container = useRef<HTMLElement>(null);
  const progress = useRef(0);
  const [stage, setStage] = useState(0);
  const [ready, setReady] = useState(false);
  const [active, setActive] = useState(false);
  const [diagram, setDiagram] = useState(false);
  const [compact, setCompact] = useState(false);
  const reduced = usePrefersReducedMotion();
  useEffect(() => {
    const el = container.current;
    if (!el) return;
    let frame = 0;
    const shortViewport = window.matchMedia("(max-height: 650px)");
    const measure = () => {
      const rect = el.getBoundingClientRect();
      const span = Math.max(1, el.offsetHeight - window.innerHeight);
      setCompact(shortViewport.matches);
      if (!shortViewport.matches) {
        progress.current = Math.max(0, Math.min(5.999, (-rect.top / span) * 6));
        setStage(Math.min(5, Math.floor(progress.current)));
      }
      setActive(rect.top < window.innerHeight && rect.bottom > 0 && !document.hidden);
      frame = 0;
    };
    const update = () => {
      if (!frame) frame = requestAnimationFrame(measure);
    };
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry?.isIntersecting) setReady(true);
      },
      { rootMargin: "300px" },
    );
    observer.observe(el);
    window.addEventListener("scroll", update, { passive: true });
    window.addEventListener("resize", update);
    document.addEventListener("visibilitychange", update);
    measure();
    return () => {
      cancelAnimationFrame(frame);
      observer.disconnect();
      window.removeEventListener("scroll", update);
      window.removeEventListener("resize", update);
      document.removeEventListener("visibilitychange", update);
    };
  }, []);
  const jump = (index: number) => {
    const el = container.current;
    if (!el) return;
    if (compact) {
      progress.current = index;
      setStage(index);
      return;
    }
    const span = el.offsetHeight - window.innerHeight;
    window.scrollTo({
      top: window.scrollY + el.getBoundingClientRect().top + (span * (index + 0.15)) / 6,
      behavior: reduced ? "auto" : "smooth",
    });
  };
  const current = chapters[stage]!;
  const Icon = current.icon;
  return (
    <section
      id="how-it-works"
      className="workflow-story"
      ref={container}
      aria-label="How Fixi and Mubit work"
    >
      <div className="workflow-sticky">
        <div className="workflow-topline">
          <span>One repair. A connected system.</span>
          <button type="button" aria-pressed={diagram} onClick={() => setDiagram(!diagram)}>
            {diagram ? "Explore in 3D" : "Diagram view"}
          </button>
        </div>
        <div className="workflow-stage">
          <div className="workflow-copy" aria-live="polite" aria-atomic="true">
            <h2 key={current.title}>
              {current.title.split("\n").map((line, i) => (
                <span key={line}>
                  {i > 0 && <br />}
                  {line}
                </span>
              ))}
            </h2>
            <p>{current.body}</p>
            <div className="workflow-outcome">
              <Icon size={18} />
              <span>{current.outcome}</span>
            </div>
            <span className="workflow-scroll-hint">
              <ArrowDown size={15} />{" "}
              {compact
                ? "Choose a chapter to explore"
                : `Scroll to follow the ${stage < 4 ? "repair" : "learning loop"}`}
            </span>
          </div>
          <div className="workflow-visual">
            <div className="workflow-canvas" aria-hidden="true">
              {ready && !diagram ? (
                <SceneBoundary fallback={<Diagram stage={stage} />}>
                  <Suspense fallback={<Diagram stage={stage} />}>
                    <WorkflowScene
                      progress={progress}
                      stage={stage}
                      active={active}
                      reducedMotion={reduced}
                    />
                  </Suspense>
                </SceneBoundary>
              ) : (
                <Diagram stage={stage} />
              )}
            </div>
            <div className="model-label" aria-hidden="true">
              <span>{stage < 4 ? "REPAIR SYSTEM" : "MUBIT / TASK ADAPTER"}</span>
              <span>
                {stage < 4
                  ? "Roof · access · outcome"
                  : "Reviewed data · fixed base · learned update"}
              </span>
            </div>
            <div className="workflow-evidence" key={stage}>
              <div>
                <Icon size={15} />
                <span>{current.label}</span>
              </div>
              <p>{current.quote}</p>
              <strong>
                {current.action}
                <ArrowRight size={16} />
              </strong>
            </div>
          </div>
        </div>
        <nav className="workflow-nav" aria-label="Workflow chapters">
          {chapters.map((chapter, index) => (
            <button
              type="button"
              key={chapter.name}
              aria-current={stage === index ? "step" : undefined}
              onClick={() => jump(index)}
            >
              <span className="chapter-track">
                <span style={{ width: stage > index ? "100%" : stage === index ? "65%" : "0%" }} />
              </span>
              <span>
                <small>{String(index + 1).padStart(2, "0")}</small>
                {chapter.name}
              </span>
            </button>
          ))}
        </nav>
        <p className="workflow-disclaimer">
          Illustrative product story. Scrolling does not run models or change cases. Evaluation
          figures are historical, not live serving results.
        </p>
      </div>
    </section>
  );
}
