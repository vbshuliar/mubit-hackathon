import type { CaseEvent } from "@/api/types";

/** Withdrawal is an access update, not a new offer of available times. */
export function eventDisplay(event: CaseEvent, fallbackTitle = event.display_title) {
  if (event.type === "AVAILABILITY_RECEIVED") {
    return event.payload?.["withdraw_availability"] === true
      ? {
          title: "Access times withdrawn",
          description:
            "Previous tenant access times were withdrawn; no replacement times were supplied.",
        }
      : {
          title: "Access times updated",
          description:
            "The tenant's recorded access times changed. Review the latest confirmed availability before booking.",
        };
  }
  return { title: fallbackTitle, description: event.display_description };
}
