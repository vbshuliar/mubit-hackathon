import type { CaseSnapshot } from "@/api/types";

export type DemoInputKind =
  | "TENANT_REPLY"
  | "CONTRACTOR_REPORT"
  | "ATTENDANCE_OUTCOME"
  | "TENANT_CONFIRMATION"
  | "OPERATOR_UPDATE";
export const RESPONSE_LABELS: Record<DemoInputKind, string> = {
  TENANT_REPLY: "Tenant reply",
  CONTRACTOR_REPORT: "Contractor visit report",
  ATTENDANCE_OUTCOME: "Visit ended without a report",
  TENANT_CONFIRMATION: "Tenant repair confirmation",
  OPERATOR_UPDATE: "Other case information",
};
export const SAFETY_FIELDS = [
  ["gas", "Gas smell"],
  ["fire", "Fire or smoke"],
  ["water_near_electrics", "Water near electrics"],
  ["structural_danger", "Structural danger"],
  ["uncontrolled_flood", "Uncontrolled flooding"],
  ["vulnerability_concern", "Vulnerable person at risk"],
] as const;

export function eligibleAppointments(snapshot: CaseSnapshot) {
  return snapshot.appointments.filter(
    (a) =>
      a.status !== "CANCELLED" &&
      a.status !== "FAILED" &&
      !snapshot.latest_reports?.some(
        (r) => r.appointment_id === a.id && r.interpretation_status === "APPLIED",
      ) &&
      snapshot.work_orders.some(
        (w) => w.id === a.work_order_id && w.status !== "COMPLETED" && w.status !== "CANCELLED",
      ),
  );
}
export function selectAppointment(snapshot: CaseSnapshot, explicit: string): string {
  const appointments = eligibleAppointments(snapshot);
  if (explicit) return appointments.find((a) => a.id === explicit)?.id ?? "";
  return appointments.find((a) => a.status !== "FINISHED")?.id ?? appointments[0]?.id ?? "";
}
export function pendingResponse(snapshot: CaseSnapshot, kind: DemoInputKind) {
  const tenant = kind === "TENANT_REPLY" || kind === "TENANT_CONFIRMATION";
  return snapshot.communications?.find((c) => {
    if (c.state !== "REQUESTED" || (c.tenant_id !== null) !== tenant) return false;
    if (kind === "TENANT_CONFIRMATION") return c.purpose === "FOLLOW_UP";
    if (kind === "CONTRACTOR_REPORT" || kind === "ATTENDANCE_OUTCOME")
      return c.purpose === "CONTRACTOR";
    return c.purpose !== "FOLLOW_UP" && c.purpose !== "CONTRACTOR";
  });
}
export function suggestedResponse(snapshot: CaseSnapshot): DemoInputKind {
  if (snapshot.case.status === "AWAITING_CONFIRMATION") return "TENANT_CONFIRMATION";
  const request = snapshot.communications?.find((c) => c.state === "REQUESTED");
  if (request) {
    if (request.tenant_id !== null)
      return request.purpose === "FOLLOW_UP" ? "TENANT_CONFIRMATION" : "TENANT_REPLY";
    if (request.purpose === "CONTRACTOR" && eligibleAppointments(snapshot).length)
      return "CONTRACTOR_REPORT";
    return "OPERATOR_UPDATE";
  }
  if (eligibleAppointments(snapshot).length) return "CONTRACTOR_REPORT";
  return "TENANT_REPLY";
}
export function validAvailability(start: string, end: string, now = Date.now()): boolean {
  const a = new Date(start).getTime();
  const b = new Date(end).getTime();
  return Number.isFinite(a) && Number.isFinite(b) && b > a && b > now;
}
export function modelExplanation(modelId: string): string {
  if (modelId.startsWith("fixture"))
    return "Offline fixture decisions: no model API request or Mubit training example is generated.";
  if (modelId.startsWith("mubit/"))
    return "Mubit routes this model's requests and reviews recorded examples. Training and savings require separate verification in its console.";
  return "This model runs directly through its configured provider. This run does not establish Mubit training or savings.";
}

export function demoSubmissionCopy(escalated: boolean) {
  return escalated
    ? {
        button: "Save response",
        saved:
          "Response saved. Automation is paused; review the evidence and use Resume before the agent can continue.",
        explanation:
          "This case is escalated. You can save evidence here, but an operator must review it and use Resume before the agent continues.",
      }
    : {
        button: "Submit response and continue",
        saved: "Response saved. Watch the agent's next decision.",
        explanation:
          "Play the tenant or specialist. Your response becomes evidence; the agent chooses the next action.",
      };
}

export function responseKindAllowed(snapshot: CaseSnapshot, kind: DemoInputKind): boolean {
  if (snapshot.case.status === "RESOLVED" || snapshot.case.status === "CANCELLED") return false;
  if (kind === "TENANT_CONFIRMATION") return snapshot.case.status === "AWAITING_CONFIRMATION";
  if (kind === "CONTRACTOR_REPORT" || kind === "ATTENDANCE_OUTCOME")
    return eligibleAppointments(snapshot).length > 0;
  return true;
}
