import { expect, it } from "vitest";
import type { CaseEvent, CaseSnapshot } from "@/api/types";
import { noModelDecision } from "./no-model-decision";
const snapshot = {
  case: { status: "ESCALATED", escalation_reason: "Unsafe condition on record." },
} as CaseSnapshot;
const event = (actor_type: string, actor_id: string) =>
  ({ type: "CASE_ESCALATED", actor_type, actor_id }) as CaseEvent;
it("attributes the deterministic hazard gate without a model request", () =>
  expect(noModelDecision(snapshot, [event("SYSTEM", "hazard-gate")])).toMatchObject({
    heading: "Safety gate paused this repair",
    explanation: expect.stringContaining("No model request needed"),
  }));
it("does not label manual escalation a safety-gate decision", () =>
  expect(noModelDecision(snapshot, [event("OPERATOR", "alice")])?.heading).toBe(
    "Automation paused for human review",
  ));
it("does not infer a safety gate from status alone", () =>
  expect(noModelDecision(snapshot, [])?.explanation).not.toContain("No model request needed"));
it("uses the latest escalation origin", () =>
  expect(
    noModelDecision(snapshot, [event("SYSTEM", "hazard-gate"), event("OPERATOR", "alice")])
      ?.heading,
  ).toBe("Automation paused for human review"));
it("does not override ordinary no-run states", () =>
  expect(noModelDecision({ case: { status: "ACTIVE" } } as CaseSnapshot, [])).toBeNull());
