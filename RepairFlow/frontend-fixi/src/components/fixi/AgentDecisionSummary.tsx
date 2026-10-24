import { eventDisplay } from "@/lib/event-display";
import { noModelDecision } from "@/lib/no-model-decision";
import { ActionExecutionResult } from "@/components/fixi/ActionExecutionResult";
import { modelExplanation } from "@/lib/demo-response";
import { Brain, Loader2, ArrowRight } from "lucide-react";
import { Link } from "@tanstack/react-router";
import type { CaseSnapshot } from "@/api/types";
import { Card } from "@/components/fixi/AppShell";
import { Pill } from "@/components/fixi/Badge";
import { useCaseEvents } from "@/hooks/use-case-events";
import { useCaseRuns } from "@/hooks/use-case-runs";
import { titleCase } from "@/lib/format";
export function AgentDecisionSummary({ snapshot }: { snapshot: CaseSnapshot }) {
  const runs = useCaseRuns(snapshot.case.id);
  const events = useCaseEvents(snapshot.case.id);
  const latestEvent = events.data?.items.at(-1);
  const latestDisplay = latestEvent ? eventDisplay(latestEvent) : null;
  const latest = runs.data?.items[0];
  const trigger = events.data?.items.find((event) => event.id === latest?.trigger_event_id);
  const triggerDisplay = trigger ? eventDisplay(trigger) : null;
  const noModel = noModelDecision(snapshot, events.data?.items ?? []);
  const pending = snapshot.pending_actions.find((a) => a.state === "AWAITING_APPROVAL");
  return (
    <Card className="decision-summary p-5 md:p-6">
      <div className="flex items-center gap-2">
        <Brain className="h-5 w-5 text-primary" />
        <h2 className="text-section font-semibold">The agent's decision</h2>
      </div>
      {snapshot.agent_active && (
        <p className="mt-3 flex items-center gap-2 text-sm text-primary">
          <Loader2 className="h-4 w-4 animate-spin" />
          Reading the case and choosing the next step…
        </p>
      )}
      {runs.isError ? (
        <p role="alert" className="mt-4 text-sm text-destructive">
          Decision history could not be loaded.
        </p>
      ) : latest ? (
        <div className="mt-4 space-y-4">
          <div className="decision-evidence">
            <p className="text-micro font-medium text-muted-foreground">Incoming evidence</p>
            <p className="mt-1 text-sm font-medium">
              {triggerDisplay?.title ??
                (events.isLoading
                  ? "Loading the triggering event…"
                  : "Triggering event not available in loaded history")}
            </p>
            {triggerDisplay?.description && (
              <p className="mt-1 text-sm text-muted-foreground">{triggerDisplay.description}</p>
            )}
            {trigger && (
              <div className="mt-2">
                <Pill tone={trigger.provenance === "LIVE" ? "blue" : "gray"}>
                  {trigger.provenance}
                </Pill>
              </div>
            )}
            {events.isError && (
              <p role="alert" className="mt-2 text-sm text-destructive">
                Evidence history could not be loaded.
              </p>
            )}
          </div>
          <div>
            <p className="text-micro uppercase tracking-wide text-muted-foreground">
              Agent proposal
            </p>
            <p className="mt-1 text-section font-semibold">
              {latest.proposal
                ? titleCase(latest.proposal.action.kind)
                : latest.state === "FAILED"
                  ? "Decision failed"
                  : "No action proposed yet"}
            </p>
            <p className="mt-1 text-sm text-muted-foreground">
              {latest.proposal?.decision_summary ?? latest.error_code ?? "The run is in progress."}
            </p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Pill
              tone={
                latest.state === "FAILED" ? "red" : latest.state === "SUCCEEDED" ? "green" : "gray"
              }
            >
              Model run: {titleCase(latest.state)}
            </Pill>
            {latest.policy_result && (
              <Pill tone="gray">Application checks: {titleCase(latest.policy_result)}</Pill>
            )}
            {pending && <Pill tone="amber">Approval needed</Pill>}
          </div>
          <ActionExecutionResult run={latest} />
          <details className="technical-details">
            <summary className="text-sm font-medium">Inspect model and tool details</summary>
            <p className="mt-3 text-micro text-muted-foreground">Tools actually used</p>
            <div className="mt-2 flex flex-wrap gap-1.5">
              {latest.tool_calls.length ? (
                latest.tool_calls.map((t) => (
                  <span
                    key={t.id}
                    className="rounded-md border border-border px-2 py-1 text-xs"
                    title={t.error_code ?? undefined}
                  >
                    {t.name}
                    {t.outcome === "FAILED" ? " · failed" : ""}
                  </span>
                ))
              ) : (
                <p className="text-sm text-muted-foreground">
                  Decided from the case snapshot; no additional tool reads.
                </p>
              )}
            </div>
            <p className="mt-3 text-xs text-muted-foreground">
              Model: {latest.model_id}. {modelExplanation(latest.model_id)}
            </p>
            <p className="mt-2 break-all text-micro text-muted-foreground">
              Run {latest.id} · snapshot version {latest.snapshot_version}
            </p>
          </details>
          <p className="text-micro text-muted-foreground">{modelExplanation(latest.model_id)}</p>
        </div>
      ) : noModel ? (
        <div className="mt-4 rounded-lg border border-destructive/25 bg-destructive/5 p-3">
          <h3 className="text-sm font-semibold">{noModel.heading}</h3>
          <p className="mt-2 text-sm">{noModel.reason}</p>
          <p className="mt-2 text-xs text-muted-foreground">{noModel.explanation}</p>
        </div>
      ) : (
        <p className="mt-4 text-sm text-muted-foreground">
          {runs.isLoading
            ? "Loading agent decisions…"
            : "The first decision will appear here when the agent runs."}
        </p>
      )}
      {latestEvent && (
        <div className="mt-4 rounded-lg bg-muted/40 p-3">
          <p className="text-micro uppercase tracking-wide text-muted-foreground">
            Latest recorded change
          </p>
          <p className="mt-1 text-sm font-medium">{latestDisplay?.title}</p>
          <p className="mt-1 text-xs text-muted-foreground">{latestDisplay?.description}</p>
        </div>
      )}
      <Link
        to="/maintenance/tickets/$ticketId/{-$section}"
        params={{ ticketId: snapshot.case.id, section: "agent" }}
        className="mt-4 inline-flex items-center gap-1 text-sm font-medium text-primary"
      >
        Inspect the full agent workflow <ArrowRight className="h-4 w-4" />
      </Link>
    </Card>
  );
}
