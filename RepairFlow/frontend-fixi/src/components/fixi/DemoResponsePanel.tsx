import { ApiError } from "@/api/client";
import { useRef, useState } from "react";
import { MessageSquareText, Send, Loader2, CheckCircle2 } from "lucide-react";
import type { CaseSnapshot, SafetyAnswers, SafetyAnswer } from "@/api/types";
import { Card } from "@/components/fixi/AppShell";
import { Button } from "@/components/ui/button";
import { useDemoInput, type DemoInput } from "@/hooks/use-demo-input";
import {
  demoSubmissionCopy,
  eligibleAppointments,
  selectAppointment,
  pendingResponse,
  responseKindAllowed,
  RESPONSE_LABELS,
  SAFETY_FIELDS,
  suggestedResponse,
  validAvailability,
  type DemoInputKind,
} from "@/lib/demo-response";
import { titleCase, formatDateRange } from "@/lib/format";

const inputClass =
  "mt-1.5 w-full rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-ring";
export function DemoResponsePanel({ snapshot }: { snapshot: CaseSnapshot }) {
  const lastSubmission = useRef<{ fingerprint: string; body: DemoInput } | null>(null);
  const [attendance, setAttendance] = useState<"NO_ACCESS" | "NO_SHOW" | "AWAITING_REPORT">(
    "AWAITING_REPORT",
  );
  const [override, setOverride] = useState<DemoInputKind | null>(null);
  const [draftContext, setDraftContext] = useState<{
    kind: DemoInputKind;
    appointment: string;
    requestId: string | null;
  } | null>(null);
  const kind = draftContext?.kind ?? override ?? suggestedResponse(snapshot);
  const [text, setText] = useState("");
  const [appointment, setAppointment] = useState("");
  const [safety, setSafety] = useState<SafetyAnswers>({});
  const [includeSafety, setIncludeSafety] = useState(false);
  const [includeAvailability, setIncludeAvailability] = useState(false);
  const [withdrawAvailability, setWithdrawAvailability] = useState(false);
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [confirmation, setConfirmation] = useState("");
  const [saved, setSaved] = useState(false);
  const [resolvedConcerns, setResolvedConcerns] = useState<string[]>([]);
  const addressableConcerns = (snapshot.issue?.unresolved_concerns ?? []).filter(
    (concern) => concern !== "tenant reports issue still unresolved",
  );
  const concernsToShow = [...new Set([...addressableConcerns, ...resolvedConcerns])];
  const staleConcern =
    kind === "OPERATOR_UPDATE" &&
    resolvedConcerns.some((concern) => !addressableConcerns.includes(concern));
  const submit = useDemoInput(snapshot.case.id);
  const appointments = eligibleAppointments(snapshot);
  const selectedAppointment = selectAppointment(snapshot, draftContext?.appointment || appointment);
  const needsAppointment = kind === "CONTRACTOR_REPORT" || kind === "ATTENDANCE_OUTCOME";
  const tenantInfo = kind === "TENANT_REPLY" || kind === "OPERATOR_UPDATE";
  const closed = snapshot.case.status === "RESOLVED" || snapshot.case.status === "CANCELLED";
  const copy = demoSubmissionCopy(snapshot.case.status === "ESCALATED");
  const currentRequest = pendingResponse(snapshot, kind);
  const respondingTo = draftContext
    ? snapshot.communications?.find(
        (c) => c.id === draftContext.requestId && c.state === "REQUESTED",
      )
    : currentRequest;
  const requestChanged =
    draftContext !== null && draftContext.requestId !== (currentRequest?.id ?? null);
  function pinDraftContext() {
    if (!draftContext)
      setDraftContext({
        kind,
        appointment: selectedAppointment,
        requestId: currentRequest?.id ?? null,
      });
  }
  const questions =
    respondingTo?.transcript.filter((t) => t.speaker === "AGENT").map((t) => t.text) ?? [];
  const ready =
    responseKindAllowed(snapshot, kind) &&
    !requestChanged &&
    !staleConcern &&
    text.trim().length >= 1 &&
    (!needsAppointment || !!selectedAppointment) &&
    (kind !== "TENANT_CONFIRMATION" || confirmation !== "") &&
    (!tenantInfo || !includeAvailability || validAvailability(start, end)) &&
    (!tenantInfo || !includeSafety || SAFETY_FIELDS.every(([field]) => !!safety[field]));

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!ready || submit.isPending || snapshot.agent_active || closed) return;
    const body: DemoInput = {
      input_id: crypto.randomUUID(),
      expected_case_version: snapshot.case.version,
      kind,
      text: text.trim(),
    };
    const answersRequest =
      !(kind === "ATTENDANCE_OUTCOME" && attendance === "AWAITING_REPORT") &&
      !(respondingTo?.purpose === "AVAILABILITY" && !includeAvailability);
    if (respondingTo && answersRequest) body.response_to_communication_id = respondingTo.id;
    if (kind === "ATTENDANCE_OUTCOME") body.attendance_outcome = attendance;
    if (needsAppointment) body.appointment_id = selectedAppointment;
    if (kind === "TENANT_CONFIRMATION") body.confirms_resolved = confirmation === "yes";
    if (tenantInfo && includeSafety) body.safety_answers = safety;
    if (tenantInfo && withdrawAvailability) body.withdraw_availability = true;
    if (kind === "OPERATOR_UPDATE" && resolvedConcerns.length)
      body.resolved_concerns = resolvedConcerns;
    if (tenantInfo && includeAvailability)
      body.availability = [
        {
          start_at: new Date(start).toISOString(),
          end_at: new Date(end).toISOString(),
          timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
          spoken_text: text.trim(),
          confirmed_by_speaker: true,
        },
      ];
    try {
      const fingerprint = JSON.stringify({ ...body, input_id: null, expected_case_version: null });
      const requestBody =
        lastSubmission.current?.fingerprint === fingerprint ? lastSubmission.current.body : body;
      lastSubmission.current = { fingerprint, body: requestBody };
      await submit.mutateAsync(requestBody);
      lastSubmission.current = null;
      setAppointment("");
      setText("");
      setSaved(true);
      setConfirmation("");
      setOverride(null);
      setDraftContext(null);
      setIncludeAvailability(false);
      setWithdrawAvailability(false);
      setIncludeSafety(false);
      setSafety({});
      setResolvedConcerns([]);
    } catch (error) {
      if (error instanceof ApiError && error.status === 409) lastSubmission.current = null;
      /* Keep every field intact so the operator can retry. */
    }
  }
  return (
    <Card className="border-primary/25 p-5">
      <div className="flex items-center gap-2">
        <MessageSquareText className="h-5 w-5 text-primary" />
        <h2 className="text-section font-semibold">Continue the demo</h2>
        <span className="ml-auto rounded-full bg-primary-soft px-2 py-1 text-micro font-medium text-primary">
          SIMULATED INPUT
        </span>
      </div>
      <p className="mt-2 text-sm text-muted-foreground">{copy.explanation}</p>
      {closed ? (
        <p className="mt-4 text-sm">
          This case is {titleCase(snapshot.case.status).toLowerCase()}.{" "}
          {snapshot.case.status === "RESOLVED"
            ? "Reopen it to provide new information."
            : "Create a new case to continue with a new repair."}
        </p>
      ) : (
        <form
          onSubmit={(e) => void handleSubmit(e)}
          onChangeCapture={pinDraftContext}
          className="mt-4 space-y-3"
        >
          {requestChanged && (
            <div role="alert" className="rounded-lg bg-destructive/10 p-3 text-sm">
              The pending request changed while you were writing. Review the current request before
              sending; your text is preserved.
              <Button
                type="button"
                variant="outline"
                className="mt-2"
                onClick={() =>
                  setDraftContext({
                    kind,
                    appointment: draftContext?.appointment ?? selectedAppointment,
                    requestId: currentRequest?.id ?? null,
                  })
                }
              >
                Review current request
              </Button>
            </div>
          )}
          {!responseKindAllowed(snapshot, kind) && (
            <p role="alert" className="text-sm text-destructive">
              This response type is no longer available. Choose another response type; your text is
              preserved.
            </p>
          )}
          {needsAppointment && !selectedAppointment && (
            <p role="alert" className="text-sm text-destructive">
              The selected appointment is no longer available. Review your report and explicitly
              select the correct appointment.
            </p>
          )}
          {questions.length > 0 && (
            <div className="rounded-lg bg-primary-soft p-3 text-sm">
              <strong>The agent is asking</strong>
              <ul className="mt-1 list-disc pl-5">
                {questions.map((q, i) => (
                  <li key={i}>{q}</li>
                ))}
              </ul>
            </div>
          )}
          <label className="block text-xs font-medium">
            Response type
            <select
              className={inputClass}
              value={kind}
              onChange={(e) => {
                setOverride(e.target.value as DemoInputKind);
                setDraftContext(null);
                setSaved(false);
                submit.reset();
              }}
            >
              {Object.entries(RESPONSE_LABELS).map(([value, label]) => (
                <option
                  key={value}
                  value={value}
                  disabled={!responseKindAllowed(snapshot, value as DemoInputKind)}
                >
                  {label}
                </option>
              ))}
            </select>
          </label>
          {needsAppointment && (
            <label className="block text-xs font-medium">
              Appointment
              <select
                className={inputClass}
                value={selectedAppointment}
                onChange={(e) => {
                  setAppointment(e.target.value);
                  setDraftContext({
                    kind,
                    appointment: e.target.value,
                    requestId: currentRequest?.id ?? null,
                  });
                }}
              >
                {!selectedAppointment && <option value="">Choose an appointment</option>}
                {appointments.map((a) => {
                  const wo = snapshot.work_orders.find((w) => w.id === a.work_order_id);
                  const when = formatDateRange(a.start_at, a.end_at);
                  return (
                    <option key={a.id} value={a.id}>
                      {titleCase(wo?.trade ?? "Visit")} · {when.date}, {when.time} ·{" "}
                      {titleCase(a.status)}
                    </option>
                  );
                })}
              </select>
            </label>
          )}
          <label className="block text-xs font-medium">
            {kind === "CONTRACTOR_REPORT" ? "What happened at the visit?" : "Response"}
            <textarea
              className={`${inputClass} min-h-24 resize-y`}
              maxLength={4000}
              value={text}
              onChange={(e) => {
                setText(e.target.value);
                setSaved(false);
              }}
              placeholder={
                kind === "CONTRACTOR_REPORT"
                  ? "Describe the work done, what remains, or why the repair could not be completed…"
                  : "Write the information the agent needs to continue…"
              }
              required
            />
          </label>
          {kind === "ATTENDANCE_OUTCOME" && (
            <label className="block text-xs font-medium">
              Visit outcome
              <select
                className={inputClass}
                value={attendance}
                onChange={(e) => setAttendance(e.target.value as typeof attendance)}
              >
                <option value="AWAITING_REPORT">Visit ended — report still needed</option>
                <option value="NO_ACCESS">Contractor could not gain access</option>
                <option value="NO_SHOW">Contractor did not attend</option>
              </select>
            </label>
          )}
          {kind === "TENANT_CONFIRMATION" && (
            <label className="block text-xs font-medium">
              Has the repair solved the problem?
              <select
                className={inputClass}
                value={confirmation}
                onChange={(e) => setConfirmation(e.target.value)}
                required
              >
                <option value="">Choose the tenant's answer</option>
                <option value="yes">Yes — the issue is resolved</option>
                <option value="no">No — the issue is still present</option>
              </select>
            </label>
          )}
          {kind === "OPERATOR_UPDATE" && concernsToShow.length > 0 && (
            <fieldset className="space-y-2 rounded-lg border border-border p-3">
              <legend className="px-1 text-xs font-medium">Mark selected concerns addressed</legend>
              <p className="text-xs text-muted-foreground">
                Select only concerns that have actually been addressed. Explain what resolved each
                selected concern in the Response field above. This does not clear safety risks or
                confirm the repair for the tenant.
              </p>
              {concernsToShow.map((concern) => (
                <label key={concern} className="flex items-start gap-2 text-sm">
                  <input
                    type="checkbox"
                    className="mt-1"
                    checked={resolvedConcerns.includes(concern)}
                    onChange={(e) =>
                      setResolvedConcerns(
                        e.target.checked
                          ? [...resolvedConcerns, concern]
                          : resolvedConcerns.filter((item) => item !== concern),
                      )
                    }
                  />
                  {concern}
                  {!addressableConcerns.includes(concern) &&
                    " (no longer pending — uncheck to continue)"}
                </label>
              ))}
              {staleConcern && (
                <p role="alert" className="text-xs text-destructive">
                  A selected concern changed while you were editing. Uncheck it and review the
                  current concerns before submitting.
                </p>
              )}
            </fieldset>
          )}
          {tenantInfo && (
            <>
              <label className="flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={includeSafety}
                  onChange={(e) => setIncludeSafety(e.target.checked)}
                />
                Include explicit safety answers
              </label>
              {includeSafety && (
                <div className="grid grid-cols-2 gap-3 rounded-lg bg-muted/40 p-3">
                  {SAFETY_FIELDS.map(([field, label]) => (
                    <label key={field} className="text-xs">
                      {label}
                      <select
                        className={inputClass}
                        value={safety[field] ?? ""}
                        onChange={(e) =>
                          setSafety({ ...safety, [field]: e.target.value as SafetyAnswer })
                        }
                        required
                      >
                        <option value="">Choose</option>
                        <option value="NO">No</option>
                        <option value="YES">Yes</option>
                        <option value="UNKNOWN">Unknown</option>
                      </select>
                    </label>
                  ))}
                </div>
              )}
              <label className="flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={includeAvailability}
                  onChange={(e) => {
                    setIncludeAvailability(e.target.checked);
                    if (e.target.checked) setWithdrawAvailability(false);
                  }}
                />
                Provide new tenant-confirmed access times (replaces all previous times)
              </label>
              <label className="flex items-center gap-2 text-xs">
                <input
                  type="checkbox"
                  checked={withdrawAvailability}
                  onChange={(e) => {
                    setWithdrawAvailability(e.target.checked);
                    if (e.target.checked) setIncludeAvailability(false);
                  }}
                />
                Withdraw all previous access times — no replacement times yet
              </label>
              {(includeAvailability || withdrawAvailability) && (
                <p className="text-micro text-muted-foreground">
                  Previous access times will no longer be used. If a booked visit is outside the
                  updated access times, the case pauses for operator review.
                </p>
              )}
              {includeAvailability && (
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="text-xs">
                    Available from
                    <input
                      type="datetime-local"
                      className={inputClass}
                      value={start}
                      onChange={(e) => setStart(e.target.value)}
                      required
                    />
                  </label>
                  <label className="text-xs">
                    Available until
                    <input
                      type="datetime-local"
                      className={inputClass}
                      value={end}
                      onChange={(e) => setEnd(e.target.value)}
                      required
                    />
                  </label>
                  <p className="text-micro text-muted-foreground sm:col-span-2">
                    Times use your browser's local timezone. End must be in the future and after
                    start.
                  </p>
                </div>
              )}
            </>
          )}
          {submit.isError && (
            <p role="alert" className="rounded-lg bg-destructive/10 p-3 text-sm text-destructive">
              Could not save: {submit.error.message}. Your response is preserved.
            </p>
          )}
          {saved && (
            <p role="status" className="flex items-center gap-2 text-sm text-primary">
              <CheckCircle2 className="h-4 w-4" />
              {copy.saved}
            </p>
          )}
          <Button
            type="submit"
            disabled={!ready || submit.isPending || snapshot.agent_active}
            className="w-full"
          >
            {submit.isPending || snapshot.agent_active ? (
              <Loader2 className="animate-spin" />
            ) : (
              <Send />
            )}
            {submit.isPending
              ? "Saving response…"
              : snapshot.agent_active
                ? "Agent is working…"
                : copy.button}
          </Button>
          <p className="text-micro text-muted-foreground">
            No one is contacted. Simulated physical events are separate from the agent's real
            decisions.
          </p>
        </form>
      )}
    </Card>
  );
}
