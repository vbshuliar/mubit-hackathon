# Demo interface declutter proposals

24 October 2026. Review list only: unrelated features below remain implemented.
Calling removal and the new response panel are separately authorized work.

## Keep prominent

New repair creation; simulated responses; requested questions; latest real decision;
actual read tools; policy/execution evidence; approvals; escalation reasons;
resolution status; detailed Agent flow and Work dependencies. Keep simulated
physical events visibly separate from real model decisions.

## Review candidates

| Priority | Component | Proposal | Why | Source |
| --- | --- | --- | --- | --- |
| 1 | Overview/Summary/Timeline/Agent overlap | Collapse repeated historical cards | Same repair story repeats across several views | `frontend-fixi/src/routes/maintenance.tickets.$ticketId.{-$section}.tsx` |
| 1 | Agent graph plus decision cards | Collapse older cards, retain inspection | Every run appears twice | `frontend-fixi/src/components/fixi/AgentActivity.tsx`, `CaseFlow.tsx` |
| 1 | Approved contractor roster | Show selected/relevant supplier, expand others | Five suppliers and postcode lists compete with the current decision | Ticket `SummaryColumn` |
| 1 | Share/export/copy toolbar | Group secondary actions under one menu | Administrative actions crowd the response controls | `frontend-fixi/src/components/fixi/CaseToolbar.tsx` |
| 2 | Property-history preview | Collapse by default | Unrelated past cases interrupt the live story | Ticket `SummaryColumn` |
| 2 | Repeated property/contact facts | One compact identity plus details link | The same information repeats in case and property views | Ticket and property routes |
| 2 | Files/Costs tabs | Group as supporting records in a demo view | Useful production features but unnecessary for the learning demonstration | `DocumentsPanel.tsx`, `CostsPanel.tsx` |
| 2 | Eight sidebar destinations | Consider focused demo navigation | Insights, Reports and separate Messages distract from active repair | `AppShell.tsx` |
| 2 | Portfolio metrics/charts | Collapse for a single-case demo | Property/tenant totals do not explain the agent's choice | `routes/index.tsx`, `insights.index.tsx`, `PropertyStatsCharts.tsx` |
| 3 | Archive/sample-history filters | Move into advanced filters | Historical data creates another narrative and provenance to explain | Maintenance/property/history routes |
| 3 | Directory CRUD | Group under setup | Preparation actions need not appear during the repair workflow | `DirectoryForms.tsx`, directory routes |
| 3 | Model IDs and snapshot versions per run | Expandable technical details | Repetitive debugging information consumes space | `AgentActivity.tsx` |
| 3 | Global plus local search | Consider focused-case navigation | Multiple search inputs compete visually | `UtilityBar.tsx`, route filters |

## Before applying

Decide whether simplification is global or a dedicated demo presentation mode.
No proposal calls for deleting backend data. Preserve failure, provenance, approval,
and unresolved-work indicators even when making the screen simpler.
