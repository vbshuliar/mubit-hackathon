import { Link } from "@tanstack/react-router";
import {
  ArrowDown,
  ArrowRight,
  ArrowUpRight,
  House,
  ShieldCheck,
  GitBranch,
  CheckCheck,
} from "lucide-react";
import { WorkflowStory } from "./WorkflowStory";
import "./preview.css";

export function ProductPreview() {
  return (
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

        <WorkflowStory />
        <section id="workspace" className="workspace-launch">
          <div className="workspace-launch-copy">
            <h2>
              The whole repair.
              <br />
              <span>Within reach.</span>
            </h2>
            <p>
              Move from the story into the workspace. Review escalations, follow active work and
              inspect the evidence behind each next step.
            </p>
            <Link to="/maintenance" className="silver-button">
              Enter the workspace <ArrowUpRight size={18} />
            </Link>
          </div>
          <div className="workspace-manifest">
            <div>
              <GitBranch size={22} />
              <h3>A connected queue</h3>
              <p>Reports, work orders and prerequisites stay in the same picture.</p>
            </div>
            <div>
              <ShieldCheck size={22} />
              <h3>Decisions you can inspect</h3>
              <p>See what the agent proposed, what was approved and what actually executed.</p>
            </div>
            <div>
              <CheckCheck size={22} />
              <h3>Outcomes you can verify</h3>
              <p>Keep the case open until the required work and confirmation are complete.</p>
            </div>
          </div>
        </section>
        <section className="model-contract">
          <h2>Learning has a precise job.</h2>
          <div>
            <p>
              Anthropic through Mubit currently powers the coordinator. The focused open-model
              experiment learns how to interpret contractor reports. It is not a replacement for the
              application’s safety checks or approvals.
            </p>
            <span>Teacher calls → reviewed examples → task adapter → evaluation gate</span>
          </div>
        </section>
      </main>
      <footer className="preview-footer">
        <Link to="/" className="preview-brand">
          fixi<span className="brand-dot">.</span>
        </Link>
        <p>Properties, solved. Every step accounted for.</p>
        <Link to="/maintenance" className="text-button">
          Open dashboard <ArrowRight size={16} />
        </Link>
      </footer>
    </div>
  );
}
