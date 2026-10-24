import { expect, it } from "vitest";
import type { CaseEvent } from "@/api/types";
import { eventDisplay } from "./event-display";
const event = (payload?: object) =>
  ({
    type: "AVAILABILITY_RECEIVED",
    payload,
    display_title: "Availability recorded",
    display_description: "New tenant availability was recorded.",
  }) as CaseEvent;
it("identifies an explicit withdrawal without claiming new availability", () => {
  expect(eventDisplay(event({ withdraw_availability: true }))).toEqual({
    title: "Access times withdrawn",
    description: "Previous tenant access times were withdrawn; no replacement times were supplied.",
  });
});
it.each([undefined, {}, { withdraw_availability: false }])(
  "uses neutral wording for legacy or replaced access times",
  (payload) => {
    expect(eventDisplay(event(payload)).title).toBe("Access times updated");
  },
);
it("preserves other event descriptions and caller titles", () => {
  expect(eventDisplay({ ...event(), type: "CASE_CREATED" }, "Issue reported")).toEqual({
    title: "Issue reported",
    description: "New tenant availability was recorded.",
  });
});
