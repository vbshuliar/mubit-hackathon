import { expect, it } from "vitest";
import type { OrchestrationRun } from "@/api/types";
import { executionOutcome } from "./action-execution";
const run = (extra: Partial<OrchestrationRun>) =>
  ({ state: "SUCCEEDED", policy_result: "PENDING", ...extra }) as OrchestrationRun;
it("shows execution failure despite a successful model and initial pending policy", () => {
  expect(
    executionOutcome(run({ action_state: "FAILED", action_error: "Slot not found" })),
  ).toMatchObject({ failed: true, label: "Action: Failed", detail: "Slot not found" });
});
it("does not infer execution from model success", () =>
  expect(executionOutcome(run({})).label).toBe("Action execution not recorded"));
it("shows ledger success despite old pending policy", () =>
  expect(executionOutcome(run({ action_state: "SUCCEEDED" }))).toMatchObject({
    failed: false,
    label: "Action: Succeeded",
  }));
it("exposes uncertain external action outcome", () =>
  expect(executionOutcome(run({ action_state: "UNKNOWN" })).uncertain).toBe(true));
it("shows rejected actions as failure", () =>
  expect(executionOutcome(run({ action_state: "REJECTED" })).failed).toBe(true));
it("distinguishes pending execution", () =>
  expect(executionOutcome(run({ action_state: "PENDING" })).detail).toContain("has not finished"));
it("surfaces model failure without implying an action executed", () =>
  expect(
    executionOutcome(run({ state: "FAILED", proposal: null, error_code: "Invalid model output" })),
  ).toMatchObject({ failed: true, label: "Decision failed", detail: "Invalid model output" }));

it("surfaces failed admission even when a proposal exists", () => {
  const proposal = { action: { kind: "SCHEDULE_VISIT" } } as OrchestrationRun["proposal"];
  expect(
    executionOutcome(run({ state: "FAILED", proposal, error_code: "Idempotency conflict" })),
  ).toMatchObject({ failed: true, label: "Decision failed", detail: "Idempotency conflict" });
});
it("explains policy rejection when the run has no error text", () =>
  expect(
    executionOutcome(run({ state: "FAILED", policy_result: "REJECTED", error_code: null })).detail,
  ).toContain("REJECTED"));
it("preserves actual ledger failure ahead of model failure", () =>
  expect(
    executionOutcome(
      run({
        state: "FAILED",
        action_state: "FAILED",
        action_error: "Booking rejected",
        error_code: "Model failed",
      }),
    ),
  ).toMatchObject({ label: "Action: Failed", detail: "Booking rejected" }));

it("prefers the descriptive admission reason over a generic error code", () => {
  const reason = "Idempotency key was reused with a different proposal payload";
  expect(
    executionOutcome(
      run({ state: "FAILED", error_code: "ToolErrorCode.CONFLICT", policy_result: reason }),
    ).detail,
  ).toBe(reason);
});
