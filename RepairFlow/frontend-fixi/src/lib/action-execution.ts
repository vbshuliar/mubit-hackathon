import type { OrchestrationRun } from "@/api/types";
import { titleCase } from "@/lib/format";
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
