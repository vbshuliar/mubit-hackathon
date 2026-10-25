import { Link } from "@tanstack/react-router";
import { GitBranch, AlertTriangle } from "lucide-react";
import type { CaseSnapshot } from "@/api/types";
import { presentationText } from "@/lib/presentation";
import { usePresentationMode } from "@/lib/presentation-mode";

/** Only recorded open dependencies and unresolved concerns; no inferred clearance. */
export function CaseBlockers({ snapshot }: { snapshot: CaseSnapshot }) {
  const presentation = usePresentationMode();
  const open = snapshot.dependencies.filter((d) => d.status === "OPEN");
  const blocked = snapshot.work_orders.filter((w) => w.status === "BLOCKED");
  const concerns = snapshot.issue.unresolved_concerns;
  if (!open.length && !blocked.length && !concerns.length) return null;
  return (
    <section
      className="case-blockers mt-4 rounded-xl border border-status-amber-foreground/30 bg-status-amber/50 p-5"
      aria-labelledby="blockers-title"
    >
      <h2 id="blockers-title" className="flex items-center gap-2 text-section font-semibold">
        <GitBranch className="h-5 w-5 text-status-amber-foreground" />
        What is blocking progress
      </h2>
      <ul className="mt-3 space-y-2 text-sm">
        {open.map((d) => (
          <li key={d.id}>
            <strong>
              {presentation
                ? presentationText(
                    snapshot.work_orders.find((w) => w.id === d.prerequisite_work_order_id)
                      ?.scope ?? "Prerequisite work",
                  )
                : (snapshot.work_orders.find((w) => w.id === d.prerequisite_work_order_id)?.scope ??
                  "Prerequisite work")}
            </strong>
            <span className="text-muted-foreground">
              {" "}
              →{" "}
              {presentation
                ? presentationText(
                    snapshot.work_orders.find((w) => w.id === d.dependent_work_order_id)?.scope ??
                      "Dependent work",
                  )
                : (snapshot.work_orders.find((w) => w.id === d.dependent_work_order_id)?.scope ??
                  "Dependent work")}
            </span>
            <p className="mt-1">{d.reason}</p>
          </li>
        ))}
        {!open.length &&
          blocked.map((w) => (
            <li key={w.id}>{presentation ? presentationText(w.scope) : w.scope} · blocked</li>
          ))}
        {concerns.map((concern, i) => (
          <li key={`${i}-${concern}`} className="flex gap-2">
            <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
            {concern}
          </li>
        ))}
      </ul>
      <Link
        to="/maintenance/tickets/$ticketId/{-$section}"
        params={{ ticketId: snapshot.case.id, section: "work" }}
        className="mt-3 inline-block text-sm font-medium text-primary underline"
      >
        Inspect work dependencies
      </Link>
    </section>
  );
}
