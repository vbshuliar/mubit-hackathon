import type { CaseEvent, CaseSnapshot } from "@/api/types";
/** Used only when the case has no recorded model runs. */
export function noModelDecision(snapshot: CaseSnapshot, events: CaseEvent[]) {
  if (snapshot.case.status !== "ESCALATED") return null;
  const escalation = [...events].reverse().find((event) => event.type === "CASE_ESCALATED");
  const safetyGate =
    escalation?.actor_type === "SYSTEM" &&
    (escalation.actor_id === "hazard-gate" || escalation.actor_id === "safety-gate");
  return {
    heading: safetyGate ? "Safety gate paused this repair" : "Automation paused for human review",
    reason: snapshot.case.escalation_reason ?? "Review the escalation before resuming this case.",
    explanation: safetyGate
      ? "A deterministic safety rule escalated this case before model execution. No model request needed."
      : "No model decision is recorded. Review the escalation reason before continuing.",
  };
}
