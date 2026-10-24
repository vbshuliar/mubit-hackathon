# Five-minute repair agent demo

## What is real and what is simulated

The agent makes real model requests through Mubit and chooses typed actions.
Application code validates and executes those choices. Tenant replies, contractor
visits, reports and bookings are clearly simulated; nobody receives a call.
Mubit records/reviews these requests. A trained adapter and cost savings must be
shown separately from its console and held-out measurements; neither is assumed.

## Normal repair

1. Click **New Ticket**. Select a property and tenant, describe a dripping tap.
2. Add explicit safety answers if the tenant supplied them. Leave unanswered facts
   unknown to demonstrate the agent asking for them.
3. In **Continue the demo**, answer the actual questions and add a confirmed access
   window. Watch **The agent’s decision**, its read tools and **Action: Succeeded**.
4. After booking, choose **Contractor visit report** and the appointment. Example:
   “Replaced worn tap cartridge and washer. Repeated testing shows no dripping.
   Repair completed; no further work required.”
5. The agent accepts the report and asks for tenant confirmation. Enter an explicit
   Yes plus the tenant’s explanation. The agent closes the case after all gates pass.
6. Open **Agent** for the full history. Failed/blocked earlier choices remain visible.

## Roof → scaffolding → roof → removal

1. Create a roof leak with explicit nonhazardous safety answers and a future confirmed
   access window broad enough for several appointments.
2. After the roofer is booked, submit: “Defective flashing found. Repair could not
   proceed without scaffolding. Install with verified handover first; return for the
   flashing repair; remove scaffolding afterwards. Original leak remains unresolved.”
3. Show the agent adding a prerequisite while retaining the original roof work.
4. Approve the simulated scaffold booking. Submit the installation/handover report,
   then approve acceptance only after reviewing the reported handover.
5. The roof work becomes available again. Submit its completed repair report after
   the new visit is booked. Keep the removal work visible.
6. Approve scaffold removal booking and acceptance. Tenant confirmation is still
   needed before the case can be resolved.

## Other responses

- **Visit ended without a report**: no access, no show or report awaited.
- **Tenant repair confirmation → No**: problem remains; do not claim resolution.
- **Other case information**: operator updates that do not fit a specialist report.
- Hazard intake: show deterministic escalation before any paid model request.
- Escalated cases accept evidence but need explicit operator resume.

Use future dates in the browser’s local timezone. Simulated reports may describe a
visit before its planned calendar date so the demo can proceed in minutes.

## Explain Mubit simply

“RepairFlow decides what repair step to take. Mubit sits between our agent and
Anthropic, records the model calls, and reviews examples for learning and adapter
training. We can inspect this traffic. We only claim that a smaller trained model
is serving, or that it is cheaper, when the console and comparison prove it.”

Current evidence and limitations: [verification](DEMO_VERIFICATION.md).
UI simplification proposals: [review list](DEMO_DECLUTTER_REVIEW.md).


## Ready-to-inspect browser cases

- [#100 resolved normal repair](http://localhost:5174/maintenance/tickets/ce5dcd9d-bef5-45bd-81e6-0e984fc362c8)
- [#102 resolved roof and scaffold workflow](http://localhost:5174/maintenance/tickets/73e44771-fdd4-4544-b6db-f5f340305187)
- [#101 hazard hold](http://localhost:5174/maintenance/tickets/7ee37310-ec9c-4e9c-8de0-0626a7dfc8bd)
- [#103 missing safety information](http://localhost:5174/maintenance/tickets/7ab41737-6346-4c76-b264-2187f3724982)

The live-run guard was deliberately raised to 180 total reservations on 24 October
for the approved final rehearsals. Inspecting existing case history is free;
each new coordinator decision consumes a reservation, including failed attempts.
Check the budget ledger before presenting; do not silently raise the limit.

Latest training blocker and held-out comparison plan: [training follow-up](MUBIT_PENDING_TRAINING.md).
