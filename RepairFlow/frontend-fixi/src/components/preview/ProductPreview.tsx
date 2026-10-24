import { Component, lazy, Suspense, useEffect, useRef, useState, type ReactNode } from "react";
import { Link } from "@tanstack/react-router";
import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  Check,
  CheckCheck,
  GitBranch,
  House,
  ShieldCheck,
} from "lucide-react";
import { LazyMotion, domAnimation, m } from "motion/react";
import { usePrefersReducedMotion } from "@/hooks/use-prefers-reduced-motion";
import { stages } from "./stages";
import "./preview.css";

const RoofScene = lazy(() => import("./RoofScene"));

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

function StaticScene({ stage }: { stage: number }) {
  return (
    <div
      className="scene-fallback"
      role="img"
      aria-label={`Roof repair dependency diagram. ${stages[stage]!.detail}`}
    >
      <House size={100} strokeWidth={0.7} aria-hidden="true" />
      <div className="fallback-chain">
        <span>Tenant report</span>
        <ArrowRight size={16} />
        <span>Roof repair</span>
      </div>
      <div className="fallback-chain">
        <span>{stage === 3 ? "Scaffold removed" : "Scaffold prerequisite"}</span>
        <ArrowRight size={16} />
        <span>{stage === 3 ? "Tenant confirmed" : "Operator review"}</span>
      </div>
      <small>Static walkthrough · all stage controls remain available</small>
    </div>
  );
}

export function ProductPreview() {
  const [stage, setStage] = useState(0);
  const [ready, setReady] = useState(false);
  const [visible, setVisible] = useState(false);
  const [pageVisible, setPageVisible] = useState(true);
  const [staticView, setStaticView] = useState(false);
  const sceneRef = useRef<HTMLDivElement>(null);
  const reduced = usePrefersReducedMotion();
  useEffect(() => {
    setReady(true);
    const observer = new IntersectionObserver(
      ([entry]) => setVisible(entry?.isIntersecting ?? false),
      { rootMargin: "100px" },
    );
    if (sceneRef.current) observer.observe(sceneRef.current);
    const visibility = () => setPageVisible(document.visibilityState === "visible");
    visibility();
    document.addEventListener("visibilitychange", visibility);
    return () => {
      observer.disconnect();
      document.removeEventListener("visibilitychange", visibility);
    };
  }, []);
  const current = stages[stage]!;
  return (
    <LazyMotion features={domAnimation}>
      <div className="product-preview">
        <a className="skip-link" href="#preview-main">
          Skip to content
        </a>
        <header className="preview-nav">
          <Link to="/" className="preview-brand" aria-label="Fixi home">
            <span>
              <House size={22} />
            </span>
            fixi<span className="brand-dot">.</span>
          </Link>
          <nav aria-label="Product">
            <a href="#how-it-works">How it works</a>
            <a href="#workspace">The workspace</a>
          </nav>
          <Link to="/maintenance" className="preview-nav-cta">
            Open dashboard <ArrowUpRight size={16} />
          </Link>
        </header>
        <main id="preview-main">
          <section className="preview-hero">
            <div className="hero-copy">
              <h1>
                From reported <br />
                to <em>resolved.</em>
              </h1>
              <p>
                Fixi coordinates the next step across tenants, contractors and approvals—keeping the
                repair, its blockers and its decisions in view.
              </p>
              <div className="preview-actions">
                <Link to="/maintenance" className="silver-button">
                  Open demo dashboard <ArrowUpRight size={18} />
                </Link>
                <a href="#how-it-works" className="text-button">
                  See how it works <ArrowDown size={16} />
                </a>
              </div>
              <div className="hero-note">
                <span />
                Repair coordination. With a visible chain of decisions.
              </div>
            </div>
            <div className="hero-material" aria-hidden="true">
              <span className="metal-line" />
              <div className="material-word">
                Every step.
                <br />
                <span>Accounted for.</span>
              </div>
              <div className="material-rule">
                <span>Evidence</span>
                <ArrowRight size={18} />
                <span>Outcome</span>
              </div>
            </div>
          </section>

          <section id="how-it-works" className="walkthrough" aria-labelledby="walkthrough-title">
            <div className="walkthrough-heading">
              <h2 id="walkthrough-title">
                One repair.
                <br />
                Every dependency.
              </h2>
              <p>
                A roof leak becomes a scaffolding job, then a return visit.
                <br className="desktop-break" /> Follow the responsibility—not just the appointment.
              </p>
            </div>
            <div className="scene-layout">
              <div className="scene-display" ref={sceneRef}>
                <div className="scene-topline">
                  <span>Illustrative walkthrough</span>
                  <button
                    type="button"
                    aria-pressed={staticView}
                    onClick={() => setStaticView(!staticView)}
                  >
                    {staticView ? "Show 3D" : "Static view"}
                  </button>
                </div>
                <div className="scene-canvas" aria-hidden="true">
                  {ready && visible && !staticView ? (
                    <SceneBoundary fallback={<StaticScene stage={stage} />}>
                      <Suspense fallback={<StaticScene stage={stage} />}>
                        <RoofScene
                          stage={stage}
                          reducedMotion={reduced}
                          active={visible && pageVisible}
                        />
                      </Suspense>
                    </SceneBoundary>
                  ) : (
                    <StaticScene stage={stage} />
                  )}
                </div>
                <div className={`scene-status scene-status-${stage}`}>
                  <span className="scene-status-icon">
                    {stage === 3 ? (
                      <CheckCheck size={20} />
                    ) : stage === 2 ? (
                      <ShieldCheck size={20} />
                    ) : (
                      <GitBranch size={20} />
                    )}
                  </span>
                  <div>
                    <strong>{current.label}</strong>
                    <span>{current.detail}</span>
                  </div>
                </div>
                <span className="scene-caption">ROOF / ACCESS / FOLLOW-UP</span>
              </div>
              <div className="stage-panel">
                <div className="stage-buttons" role="group" aria-label="Walkthrough stages">
                  {stages.map((item, index) => (
                    <button
                      key={item.name}
                      type="button"
                      aria-pressed={stage === index}
                      aria-controls="stage-explanation"
                      onClick={() => setStage(index)}
                    >
                      <span>{String(index + 1).padStart(2, "0")}</span>
                      {item.name}
                      {stage === index && <ArrowRight size={16} />}
                    </button>
                  ))}
                </div>
                <m.div
                  key={stage}
                  id="stage-explanation"
                  className="stage-explanation"
                  aria-live="polite"
                  initial={reduced ? false : { opacity: 0.65, y: 5 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25 }}
                >
                  <h3>{current.title}</h3>
                  <p>{current.description}</p>
                  <dl className="evidence-chain">
                    <div>
                      <dt>Incoming evidence</dt>
                      <dd>{current.evidence}</dd>
                    </div>
                    <div>
                      <dt>Agent proposal</dt>
                      <dd>{current.proposal}</dd>
                    </div>
                    <div>
                      <dt>Application checks & outcome</dt>
                      <dd>{current.result}</dd>
                    </div>
                  </dl>
                </m.div>
                <p className="illustration-note">
                  A product illustration, separate from real case state. Selecting a stage creates
                  no cases or model calls.
                </p>
              </div>
            </div>
          </section>

          <section className="decision-story">
            <h2>
              Know what happened.
              <br />
              <span>And what still needs you.</span>
            </h2>
            <div className="story-rows">
              <article>
                <ShieldCheck />
                <div>
                  <h3>Approval is a deliberate step.</h3>
                  <p>
                    Review the proposal and its context before a commitment proceeds. Rejections,
                    escalation reasons and errors stay visible.
                  </p>
                </div>
              </article>
              <article>
                <GitBranch />
                <div>
                  <h3>Blockers belong in the picture.</h3>
                  <p>
                    A scaffold installation can block a roof repair. Removal and tenant confirmation
                    can still stand between a completed visit and a resolved case.
                  </p>
                </div>
              </article>
              <article>
                <CheckCheck />
                <div>
                  <h3>A decision is not an execution.</h3>
                  <p>
                    Follow the evidence, proposed action, application checks and actual result. A
                    successful model response never stands in for completed work.
                  </p>
                </div>
              </article>
            </div>
          </section>

          <section id="workspace" className="workspace-preview">
            <div className="workspace-intro">
              <h2>
                Clarity at the
                <br />
                working end.
              </h2>
              <div>
                <p>A focused queue. A clear next step. The full repair history when you need it.</p>
                <Link to="/maintenance" className="text-button">
                  Explore the workspace <ArrowUpRight size={17} />
                </Link>
              </div>
            </div>
            <figure className="workspace-capture">
              <picture>
                <source media="(max-width: 600px)" srcSet="/preview/maintenance-mobile.png" />
                <img
                  src="/preview/maintenance-desktop.png"
                  width="1440"
                  height="1000"
                  loading="lazy"
                  alt="Fixi Maintenance workspace with grouped navigation, readable repair titles, status filters and a case queue."
                />
              </picture>
              <figcaption>
                Product preview · captured from the demo workspace. Sample and simulated records
                retain their labels.
              </figcaption>
            </figure>
          </section>
          <section className="learning-note">
            <span className="learning-mark">Mubit</span>
            <p>
              Mubit supports model calls and the learning workflow. Collected examples, training,
              evaluation and verified adapter serving are separate milestones. No adapter accuracy,
              savings or serving improvement is claimed here.
            </p>
          </section>
          <footer className="preview-footer">
            <h2>
              Keep the whole
              <br />
              repair in view.
            </h2>
            <Link to="/maintenance" className="silver-button">
              Open demo dashboard <ArrowUpRight size={18} />
            </Link>
            <div className="footer-bottom">
              <span>Fixi · Property repair coordination</span>
              <a href="#preview-main">Back to top ↑</a>
            </div>
          </footer>
        </main>
      </div>
    </LazyMotion>
  );
}
