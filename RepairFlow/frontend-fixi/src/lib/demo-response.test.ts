import { describe, expect, it } from "vitest";
import type { CaseSnapshot } from "@/api/types";
import {
  demoSubmissionCopy,
  responseKindAllowed,
  eligibleAppointments,
  selectAppointment,
  pendingResponse,
  modelExplanation,
  suggestedResponse,
  validAvailability,
  SAFETY_FIELDS,
  RESPONSE_LABELS,
} from "./demo-response";
const snapshot = (
  status = "ACTIVE",
  appointments: object[] = [],
  workOrders: object[] = [{ id: "work", status: "SCHEDULED" }],
) =>
  ({
    case: { status },
    appointments: appointments.map((a) => ({ id: "visit", work_order_id: "work", ...a })),
    work_orders: workOrders,
  }) as CaseSnapshot;
describe("demo response selection", () => {
  it("offers tenant clarification before booking", () =>
    expect(suggestedResponse(snapshot())).toBe("TENANT_REPLY"));
  it("offers a report for a booked visit", () =>
    expect(suggestedResponse(snapshot("ACTIVE", [{ status: "CONFIRMED" }]))).toBe(
      "CONTRACTOR_REPORT",
    ));
  it("offers a report when waiting for the contractor", () =>
    expect(
      suggestedResponse(
        snapshot("ACTIVE", [{ status: "FINISHED" }], [{ id: "work", status: "AWAITING_REPORT" }]),
      ),
    ).toBe("CONTRACTOR_REPORT"));
  it("prioritizes tenant confirmation over a future appointment", () =>
    expect(suggestedResponse(snapshot("AWAITING_CONFIRMATION", [{ status: "CONFIRMED" }]))).toBe(
      "TENANT_CONFIRMATION",
    ));
  it("does not use cancelled appointments as a wait", () =>
    expect(suggestedResponse(snapshot("ACTIVE", [{ status: "CANCELLED" }]))).toBe("TENANT_REPLY"));
  it("has explicit controls for every safety field", () =>
    expect(new Set(SAFETY_FIELDS.map(([key]) => key)).size).toBe(6));
  it("offers all supported response categories", () =>
    expect(Object.keys(RESPONSE_LABELS)).toHaveLength(5));
});
describe("availability validation", () => {
  it("accepts a forward window", () =>
    expect(
      validAvailability("2026-10-25T09:00", "2026-10-25T12:00", Date.parse("2026-10-24")),
    ).toBe(true));
  it.each([
    ["", ""],
    ["garbage", "2026-10-25T12:00"],
    ["2026-10-25T12:00", "2026-10-25T09:00"],
    ["2026-10-25T09:00", "2026-10-25T09:00"],
  ])("rejects invalid window %s %s", (a, b) => expect(validAvailability(a, b)).toBe(false));
});

describe("eligible report appointments", () => {
  it.each(["FAILED", "CANCELLED"])("excludes %s appointments", (status) =>
    expect(eligibleAppointments(snapshot("ACTIVE", [{ status }]))).toEqual([]),
  );
  it.each(["COMPLETED", "CANCELLED"])("excludes %s work", (status) =>
    expect(
      eligibleAppointments(snapshot("ACTIVE", [{ status: "FINISHED" }], [{ id: "work", status }])),
    ).toEqual([]),
  );
  it("does not silently reassign a stale explicit appointment", () =>
    expect(
      selectAppointment(
        snapshot("ACTIVE", [
          { id: "old", status: "CANCELLED" },
          { id: "new", status: "CONFIRMED" },
        ]),
        "old",
      ),
    ).toBe(""));
});
describe("request recipients", () => {
  function requested(tenant_id: string | null) {
    return {
      ...snapshot(),
      communications: [{ id: "req", tenant_id, state: "REQUESTED", purpose: "INTAKE" }],
    } as CaseSnapshot;
  }
  it("uses operator update for an operator question", () =>
    expect(suggestedResponse(requested(null))).toBe("OPERATOR_UPDATE"));
  it("uses tenant reply for a tenant question", () =>
    expect(suggestedResponse(requested("tenant"))).toBe("TENANT_REPLY"));
  it("does not attach a tenant response to an operator request", () =>
    expect(pendingResponse(requested(null), "TENANT_REPLY")).toBeUndefined());
  it("attaches an operator response to its pending request", () =>
    expect(pendingResponse(requested(null), "OPERATOR_UPDATE")?.id).toBe("req"));
});
it("rejects an expired forward availability window", () =>
  expect(
    validAvailability("2026-10-23T09:00Z", "2026-10-23T12:00Z", Date.parse("2026-10-24")),
  ).toBe(false));
it("labels fixture without claiming Mubit training", () =>
  expect(modelExplanation("fixture-demo")).toContain("no model API request"));
it("identifies the Mubit route only for Mubit models", () =>
  expect(modelExplanation("mubit/anthropic/test")).toContain("Mubit routes"));
it("identifies native providers separately", () =>
  expect(modelExplanation("gemini-test")).toContain("directly"));

describe("response purpose matching", () => {
  const requests = {
    ...snapshot(),
    communications: [
      { id: "intake", tenant_id: "tenant", state: "REQUESTED", purpose: "INTAKE" },
      { id: "confirmation", tenant_id: "tenant", state: "REQUESTED", purpose: "FOLLOW_UP" },
      { id: "operator", tenant_id: null, state: "REQUESTED", purpose: "INTAKE" },
      { id: "contractor", tenant_id: null, state: "REQUESTED", purpose: "CONTRACTOR" },
    ],
  } as CaseSnapshot;
  it("matches confirmation only to follow up", () =>
    expect(pendingResponse(requests, "TENANT_CONFIRMATION")?.id).toBe("confirmation"));
  it("matches tenant facts only to non-confirmation", () =>
    expect(pendingResponse(requests, "TENANT_REPLY")?.id).toBe("intake"));
  it.each(["CONTRACTOR_REPORT", "ATTENDANCE_OUTCOME"] as const)(
    "matches %s only to contractor requests",
    (kind) => expect(pendingResponse(requests, kind)?.id).toBe("contractor"),
  );
  it("excludes processed reports and selects a new prerequisite visit", () => {
    const s = {
      ...snapshot("ACTIVE", [
        { id: "old", status: "FINISHED" },
        { id: "new", status: "CONFIRMED" },
      ]),
      latest_reports: [{ appointment_id: "old", interpretation_status: "APPLIED" }],
    } as CaseSnapshot;
    expect(eligibleAppointments(s).map((a) => a.id)).toEqual(["new"]);
    expect(selectAppointment(s, "old")).toBe("");
  });
});

it("explains manual resume for escalated evidence", () => {
  expect(demoSubmissionCopy(true).button).toBe("Save response");
  expect(demoSubmissionCopy(true).saved).toContain("Resume");
});

it.each(["ACTIVE", "ESCALATED", "RESOLVED", "CANCELLED"])(
  "blocks premature confirmation in %s",
  (status) => expect(responseKindAllowed(snapshot(status), "TENANT_CONFIRMATION")).toBe(false),
);
it("allows confirmation only while awaiting it", () =>
  expect(responseKindAllowed(snapshot("AWAITING_CONFIRMATION"), "TENANT_CONFIRMATION")).toBe(true));
it("requires a visit for contractor evidence", () =>
  expect(responseKindAllowed(snapshot(), "CONTRACTOR_REPORT")).toBe(false));
it.each(["RESOLVED", "CANCELLED"])("blocks all inputs for %s cases", (status) => {
  for (const kind of Object.keys(RESPONSE_LABELS) as (keyof typeof RESPONSE_LABELS)[])
    expect(responseKindAllowed(snapshot(status), kind)).toBe(false);
});

it("does not use general operator information to answer a contractor report request", () => {
  const s = {
    ...snapshot(),
    communications: [
      { id: "contractor", tenant_id: null, state: "REQUESTED", purpose: "CONTRACTOR" },
    ],
  } as CaseSnapshot;
  expect(pendingResponse(s, "OPERATOR_UPDATE")).toBeUndefined();
});
