import { Fragment, useId, useRef, useState } from "react";
import * as Dialog from "@radix-ui/react-dialog";
import { AlertTriangle } from "lucide-react";
import { Card } from "@/components/fixi/AppShell";
import { Pill } from "@/components/fixi/Badge";
import { useDecideApproval } from "@/hooks/use-case-actions";
import type { ActionRecord, ActionRecordAction, CaseSnapshot } from "@/api/types";
import { titleCase } from "@/lib/format";
import { presentationText } from "@/lib/presentation";
import { usePresentationMode } from "@/lib/presentation-mode";

/** Renders every ActionRecord on this case sitting in AWAITING_APPROVAL as
 * an actionable approve/reject card.
 *
 * This is the fix for the incident where `snapshot.pending_actions` was
 * fetched but never read anywhere (typed `unknown[]` in api/types.ts,
 * no route/component touched it) -- a case could sit gated on an operator
 * decision with no visible next step. The caller (the ticket detail route)
 * renders this above the section tabs so it's visible regardless of which
 * tab/section is selected -- it must be impossible to miss. */
export function DecisionCard({
  caseId,
  pendingActions,
  snapshot,
}: {
  caseId: string;
  pendingActions: ActionRecord[];
  snapshot: CaseSnapshot;
}) {
  const presentation = usePresentationMode();
  const awaiting = pendingActions.filter((a) => a.state === "AWAITING_APPROVAL");
  if (awaiting.length === 0) return null;

  return (
    <Card className="mt-5 border-status-amber-foreground/25 bg-status-amber/40 p-5">
      <div className="flex items-start gap-2.5">
        <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-status-amber-foreground" />
        <div>
          <h2 className="text-section font-semibold text-status-amber-foreground">
            {awaiting.length === 1
              ? "1 action needs your approval"
              : `${awaiting.length} actions need your approval`}
          </h2>
          <p className="mt-0.5 text-xs text-status-amber-foreground/80">
            The agent proposed this and is waiting on an operator decision before it can continue.
          </p>
        </div>
      </div>
      <ul className="mt-4 space-y-3">
        {awaiting.map((action) => (
          <DecisionRow key={action.id} caseId={caseId} action={action} snapshot={snapshot} />
        ))}
      </ul>
    </Card>
  );
}

function DecisionRow({
  caseId,
  action,
  snapshot,
}: {
  caseId: string;
  action: ActionRecord;
  snapshot: CaseSnapshot;
}) {
  const decide = useDecideApproval(caseId);
  const [rejectOpen, setRejectOpen] = useState(false);
  const [rejectionReason, setRejectionReason] = useState("");
  const reasonId = useId();
  const rejectButton = useRef<HTMLButtonElement>(null);

  // Approval's expected_case_version comes from THIS proposal (the version the
  // coordinator assumed when it proposed the action), not the case's
  // current/live version -- that's how the backend's staleness check
  // (executor.py:decide_approval) detects "something changed the case
  // since this was proposed, re-check before deciding" rather than always
  // trivially matching whatever the last poll happened to fetch.
  async function handleApprove() {
    try {
      await decide.mutateAsync({
        actionId: action.id,
        expectedCaseVersion: action.proposal.expected_case_version,
        approve: true,
        reason: "Approved by operator.",
        actionPayloadHash: action.payload_hash,
      });
    } catch {
      // handled by onError toast (see use-case-actions.ts)
    }
  }

  async function handleReject() {
    const reason = rejectionReason.trim();
    if (!reason || decide.isPending) return;
    try {
      await decide.mutateAsync({
        actionId: action.id,
        expectedCaseVersion: snapshot.case.version,
        approve: false,
        reason,
        actionPayloadHash: action.payload_hash,
      });
      setRejectOpen(false);
      setRejectionReason("");
    } catch {
      // handled by onError toast (see use-case-actions.ts)
    }
  }

  return (
    <li className="rounded-lg border border-border bg-card p-3">
      <div className="min-w-0">
        <Pill tone="amber">{titleCase(action.proposal.action.kind)}</Pill>
        <p className="mt-1.5 text-strong leading-relaxed">{action.proposal.decision_summary}</p>
        <ProposalScope action={action.proposal.action} snapshot={snapshot} />
        <EvidenceCount refs={action.proposal.evidence_refs} />
        <details className="mt-3 text-xs">
          <summary className="cursor-pointer font-medium">
            Inspect complete action and evidence
          </summary>
          <p className="mt-2 text-muted-foreground">
            These are the exact fields proposed for execution. Review safety facts, scope, and
            supporting evidence before approving.
          </p>
          <pre className="mt-2 max-h-80 overflow-auto whitespace-pre-wrap break-words rounded-lg bg-muted p-3">
            {JSON.stringify(
              { action: action.proposal.action, evidence_refs: action.proposal.evidence_refs },
              null,
              2,
            )}
          </pre>
        </details>
      </div>
      <div className="mt-3 flex items-center gap-2">
        <button
          type="button"
          disabled={decide.isPending}
          onClick={() => void handleApprove()}
          className="h-8 rounded-lg bg-primary px-3 text-xs font-medium text-primary-foreground shadow-card transition-colors hover:opacity-90 disabled:opacity-50"
        >
          Approve
        </button>
        <button
          type="button"
          disabled={decide.isPending}
          ref={rejectButton}
          onClick={() => {
            decide.reset();
            setRejectOpen(true);
          }}
          className="h-8 rounded-lg border border-border bg-card px-3 text-xs font-medium text-destructive shadow-card transition-colors hover:bg-destructive/10 disabled:opacity-50"
        >
          Reject
        </button>
      </div>
      <Dialog.Root
        open={rejectOpen}
        onOpenChange={(open) => {
          if (!decide.isPending) setRejectOpen(open);
        }}
      >
        <Dialog.Portal>
          <Dialog.Overlay className="fixed inset-0 z-50 bg-black/40" />
          <Dialog.Content
            onCloseAutoFocus={(event) => {
              event.preventDefault();
              rejectButton.current?.focus();
            }}
            className="fixed left-1/2 top-1/2 z-50 w-[min(92vw,28rem)] -translate-x-1/2 -translate-y-1/2 rounded-xl border border-border bg-card p-5 shadow-xl"
          >
            <Dialog.Title className="text-section font-semibold">
              Reject proposed action
            </Dialog.Title>
            <Dialog.Description className="mt-2 text-sm text-muted-foreground">
              Explain why this action should not proceed. Your reason is recorded in the case
              history.
            </Dialog.Description>
            <form
              className="mt-4 space-y-4"
              onSubmit={(event) => {
                event.preventDefault();
                void handleReject();
              }}
            >
              <label htmlFor={reasonId} className="block text-sm font-medium">
                Reason for rejection
              </label>
              <textarea
                id={reasonId}
                required
                maxLength={2000}
                value={rejectionReason}
                disabled={decide.isPending}
                onChange={(event) => setRejectionReason(event.target.value)}
                className="min-h-24 w-full rounded-lg border border-input bg-background p-3 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
              />
              {decide.isError && (
                <p role="alert" className="text-sm text-destructive">
                  Could not reject: {decide.error.message}. Your reason is preserved.
                </p>
              )}
              <div className="flex justify-end gap-2">
                <button
                  type="button"
                  disabled={decide.isPending}
                  onClick={() => setRejectOpen(false)}
                  className="rounded-lg border border-border px-3 py-2 text-sm disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={decide.isPending || !rejectionReason.trim()}
                  className="rounded-lg bg-destructive px-3 py-2 text-sm text-destructive-foreground disabled:opacity-50"
                >
                  {decide.isPending ? "Rejecting…" : "Reject action"}
                </button>
              </div>
            </form>
          </Dialog.Content>
        </Dialog.Portal>
      </Dialog.Root>
    </li>
  );
}

/** The proposal's own typed fields, not just its prose summary.
 *
 * docs/18 line 66 asks the approval panel to show the action's scope. The
 * card showed `decision_summary` alone -- the model's sentence about what
 * it wants -- while the structured fields it will actually execute against
 * (which contractor, which trade, which work order, what reason) sat in
 * the payload unrendered. Approving on the prose while the machine acts on
 * the fields is exactly the gap an approval step exists to close.
 *
 * Rendered generically: the NextAction union has ~10 variants and this
 * deliberately does not hardcode them, so a new variant's fields show up
 * here without a UI change. Long values and object/array fields are
 * skipped -- they belong in the payload, not in a decision summary. */
function ProposalScope({
  action,
  snapshot,
}: {
  action: ActionRecordAction;
  snapshot: CaseSnapshot;
}) {
  const presentation = usePresentationMode();
  // A raw UUID in an approval dialog tells the operator nothing. Resolve
  // the ids the proposal references against the snapshot it was made from,
  // and fall back to the id when we genuinely cannot name it -- never to a
  // guess.
  function label(key: string, value: string): string {
    if (key === "contractor_id") {
      const c = snapshot.approved_contractors.find((x) => x.id === value);
      return c ? (presentation ? presentationText(c.display_name) : c.display_name) : value;
    }
    if (key === "work_order_id") {
      const wo = snapshot.work_orders.find((x) => x.id === value);
      return wo ? `${titleCase(wo.trade)} — ${wo.scope}` : value;
    }
    return value;
  }

  const entries = Object.entries(action).filter(([key, value]) => {
    if (key === "kind") return false;
    if (value === null || value === undefined || value === "") return false;
    if (typeof value === "object") return false;
    return String(value).length <= 80;
  });
  if (entries.length === 0) return null;

  return (
    <dl className="mt-2 grid grid-cols-[auto_1fr] gap-x-2.5 gap-y-0.5 text-micro">
      {entries.map(([key, value]) => (
        <Fragment key={key}>
          <dt className="text-muted-foreground">{titleCase(key.replace(/_/g, " "))}</dt>
          <dd className="min-w-0 truncate font-medium" title={String(value)}>
            {label(key, String(value))}
          </dd>
        </Fragment>
      ))}
    </dl>
  );
}

/** How much the proposal is standing on. `evidence_refs` each point at a
 * real record (a report, a transcript turn, an event) with its own
 * provenance -- an empty list means the model proposed this from the
 * snapshot alone, which is worth knowing before approving it. */
function EvidenceCount({ refs }: { refs: unknown[] }) {
  return (
    <p className="mt-1.5 text-micro text-muted-foreground">
      {refs.length === 0
        ? "No cited evidence — proposed from the case snapshot alone."
        : `Cites ${refs.length} piece${refs.length === 1 ? "" : "s"} of evidence.`}
    </p>
  );
}
