import type { OrchestrationRun } from "@/api/types";
import { titleCase } from "@/lib/format";

/**
 * `policy_result` is captured when the proposal is admitted to the action
 * ledger. It is not updated as the action executes. A recorded `PENDING`
 * therefore means the proposal passed application checks and is awaiting
 * execution; it does not mean the checks themselves are pending.
 */
export function admissionOutcome(run: OrchestrationRun) {
  if (!run.policy_result) return null;

  if (run.state === "SUCCEEDED") return { label: "Admitted", tone: "green" as const };
  if (run.state === "FAILED") return { label: "Rejected", tone: "red" as const };
  if (run.state === "SUPERSEDED") {
    return { label: "Requeued after stale version", tone: "gray" as const };
  }
  return { label: titleCase(run.policy_result), tone: "gray" as const };
}

export function executionOutcome(run: OrchestrationRun) {
  if (run.state === "FAILED" && !run.action_state) {
    const rejectionReason =
      run.policy_result && /\s/.test(run.policy_result) ? run.policy_result : null;
    return {
      failed: true,
      uncertain: false,
      label: "Decision failed",
      detail:
        rejectionReason ??
        run.error_code ??
        (run.policy_result
          ? `Decision admission failed: ${run.policy_result}. No action execution was recorded.`
          : "The decision failed before action execution was recorded."),
    };
  }
  const state = run.action_state;
  const failed = state === "FAILED" || state === "REJECTED";
  const uncertain = state === "UNKNOWN";
  return {
    failed,
    uncertain,
    label: state ? `Action: ${titleCase(state)}` : "Action execution not recorded",
    detail:
      run.action_error ??
      (failed
        ? "The proposed action did not complete. Review the reason before continuing."
        : uncertain
          ? "The execution result is unknown. Do not assume the action completed."
          : state === "SUCCEEDED"
            ? "The action executor completed this action."
            : state === "AWAITING_APPROVAL"
              ? "The action needs operator approval."
              : state === "PENDING" || state === "RUNNING"
                ? "The proposal is recorded; execution has not finished."
                : "Model success alone does not confirm that an action executed."),
  };
}
