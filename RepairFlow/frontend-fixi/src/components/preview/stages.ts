/** Illustrative content only. Never connected to case state or API writes. */
export const stages = [
  {
    name: "Reported",
    title: "A report starts the repair.",
    description:
      "Water is coming through the bedroom ceiling. The tenant’s report anchors one case, keeping the original leak in view.",
    label: "Tenant report linked",
    detail: "Roof leak · original issue unresolved",
    evidence: "Tenant reports water ingress",
    proposal: "Clarify safety and scope the roof work",
    result: "A case to coordinate, not a repair completed",
  },
  {
    name: "Coordinated",
    title: "The next step isn’t always the obvious one.",
    description:
      "The roofer finds defective flashing, but cannot proceed safely without scaffolding. Fixi keeps the roof repair open and connects it to its prerequisite.",
    label: "Roof work blocked",
    detail: "Scaffold installation → roof repair",
    evidence: "Contractor reports scaffolding is needed",
    proposal: "Add the prerequisite and retain the roof work",
    result: "Roof repair waits for verified access",
  },
  {
    name: "Approved",
    title: "A clear handover to the operator.",
    description:
      "The application checks the proposal. Required scaffold commitments and handover acceptance wait for operator approval; a model response alone cannot clear them.",
    label: "Operator approval required",
    detail: "Review → approve → verify execution",
    evidence: "Scaffold scope and handover requirements",
    proposal: "Request the required operator approval",
    result: "Approval and execution remain separate records",
  },
  {
    name: "Confirmed",
    title: "A finished visit is only part of the story.",
    description:
      "The roof is repaired, scaffold removal is complete, and the tenant confirms the leak has stopped. Only then can the illustration reach resolution.",
    label: "Repair outcome confirmed",
    detail: "Roof repaired · scaffold removed · tenant confirmed",
    evidence: "Repair and follow-up reports, tenant confirmation",
    proposal: "Resolve after checking all required work",
    result: "The original issue, not just the visit, is resolved",
  },
] as const;
