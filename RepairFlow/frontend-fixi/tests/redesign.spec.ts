import { expect, test, type Page } from "@playwright/test";
import { snapshot, proposal, event, run, caseItem, stamp } from "./fixtures";

async function fixtureApi(
  page: Page,
  options: {
    approval?: boolean;
    actionState?: string;
    error?: string;
    escalated?: boolean;
  } = {},
) {
  const requests: {
    method: string;
    path: string;
    body: Record<string, unknown> | null;
  }[] = [];
  await page.route("**/api/v1/**", async (route) => {
    const req = route.request(),
      url = new URL(req.url()),
      path = url.pathname;
    requests.push({
      method: req.method(),
      path: path + url.search,
      body: req.method() === "POST" ? req.postDataJSON() : null,
    });
    if (req.method() !== "GET") {
      await new Promise((resolve) => setTimeout(resolve, 180));
      return route.fulfill({
        status: 409,
        json: {
          detail: "Fixture conflict: refresh and review before retrying.",
        },
      });
    }
    let json: unknown = { items: [], next_cursor: null };
    if (path.endsWith("/metrics/dashboard"))
      json = {
        total: 1,
        active: 1,
        awaiting_confirmation: 0,
        escalated: 0,
        resolved: 0,
        cancelled: 0,
        resolved_this_week: 0,
        avg_resolution_hours: null,
        active_delta_pct: null,
        awaiting_confirmation_delta_pct: null,
        escalated_delta_pct: null,
        agent_active: false,
      };
    else if (path.endsWith("/unread-count")) json = { unread_count: 0 };
    else if (path.endsWith("/overview"))
      json = {
        property_count: 1,
        tenant_count: 1,
        approved_contractor_count: 1,
        status_counts: {
          active: 1,
          awaiting_confirmation: 0,
          escalated: 0,
          resolved: 0,
          cancelled: 0,
        },
        needs_attention: [],
        upcoming_appointments: [],
        recent_activity: [],
      };
    else if (path === "/api/v1/cases")
      json = {
        items: url.searchParams.get("status") === "RESOLVED" ? [] : [caseItem],
        next_cursor: null,
      };
    else if (path.endsWith("/fixture-case"))
      json = {
        snapshot: {
          ...snapshot,
          case: {
            ...snapshot.case,
            ...(options.escalated
              ? {
                  status: "ESCALATED",
                  escalation_reason: "Explicit safety concern requires operator review.",
                }
              : {}),
          },
          pending_actions: options.approval
            ? [
                {
                  id: "action",
                  state: "AWAITING_APPROVAL",
                  proposal,
                  payload_hash: "fixture-hash",
                  created_at: stamp,
                  updated_at: stamp,
                },
              ]
            : [],
        },
        latest_event_seq: 1,
      };
    else if (path.endsWith("/events")) json = { items: [event], next_cursor: null };
    else if (path.endsWith("/runs"))
      json = {
        items: [
          {
            ...run,
            action_state: options.actionState ?? null,
            action_error: options.error ?? null,
          },
        ],
        next_cursor: null,
      };
    else if (path === "/api/v1/properties")
      json = {
        items: [{ ...snapshot.property, photo_key: null }],
        next_cursor: null,
      };
    else if (path === "/api/v1/search") json = { groups: [] };
    return route.fulfill({ json });
  });
  return requests;
}

test("homepage is backend independent and every stage remains usable", async ({ page }) => {
  const requests = await fixtureApi(page);
  await page.goto("/");
  await expect(page.locator("h1")).toHaveText("From reported to resolved.");
  for (const name of [
    "02 Coordinate",
    "03 Review",
    "04 Resolve",
    "05 Learn",
    "06 Evaluate",
    "01 Report",
  ]) {
    await page.getByRole("button", { name, exact: true }).click();
    await expect(page.getByRole("button", { name, exact: true })).toHaveAttribute(
      "aria-current",
      "step",
    );
  }
  await expect(page.getByRole("link", { name: "Open demo dashboard" }).first()).toHaveAttribute(
    "href",
    "/maintenance",
  );
  await page.getByRole("link", { name: "See how it works" }).click();
  await expect(page).toHaveURL(/#how-it-works$/);
  expect(requests).toHaveLength(0);
});

test("WebGL unavailable and reduced motion preserve all essential content", async ({ page }) => {
  await page.setViewportSize({ width: 1280, height: 600 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.addInitScript(() => {
    const original = HTMLCanvasElement.prototype.getContext;
    HTMLCanvasElement.prototype.getContext = function (type: string, ...args: unknown[]) {
      if (type === "webgl" || type === "webgl2" || type === "experimental-webgl") return null;
      return original.apply(this, [type, ...args] as Parameters<typeof original>);
    } as typeof original;
  });
  await page.goto("/");
  await page.locator("#how-it-works").scrollIntoViewIfNeeded();
  await expect(page.getByText("Diagram view · the full story remains available")).toBeVisible();
  await page.getByRole("button", { name: "04 Resolve", exact: true }).click();
  await expect(
    page.getByRole("heading", { name: /Finished means\s*actually finished\./ }),
  ).toBeVisible();
  await page.getByRole("button", { name: "Diagram view", exact: true }).click();
  await expect(page.getByText("Diagram view · the full story remains available")).toBeVisible();
  await expect(page.getByRole("link", { name: "Open demo dashboard" }).first()).toBeVisible();
});

test("queue filters, search, mobile navigation and creation dialog retain their controls", async ({
  page,
}) => {
  const requests = await fixtureApi(page);
  await page.goto("/maintenance");
  await expect(page.locator(".board-case-title")).toHaveText(caseItem.title);
  await page.getByRole("button", { name: "List", exact: true }).click();
  await expect(page.locator(".queue-title")).toHaveText(caseItem.title);
  await page.getByRole("button", { name: "Resolved", exact: true }).click();
  await expect(page.getByText("No tickets match the current filters.").first()).toBeVisible();
  await page.getByRole("button", { name: "All", exact: true }).click();
  await page.getByText("Advanced filters", { exact: true }).click();
  await page.getByRole("checkbox", { name: "Include archival sample history" }).check();
  await expect
    .poll(() =>
      requests.some(
        (r) => r.path.includes("include_archived=true") && r.path.includes("limit=100"),
      ),
    )
    .toBe(true);
  await page.getByRole("combobox", { name: "Search", exact: true }).fill("roof");
  await expect.poll(() => requests.some((r) => r.path.includes("q=roof"))).toBe(true);
  await page.getByRole("combobox", { name: "Search", exact: true }).press("Escape");
  await page.getByRole("button", { name: "New Ticket" }).click();
  await expect(page.getByRole("dialog")).toBeVisible();
  await page.keyboard.press("Escape");
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.locator(".mobile-case").first()).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.getByRole("button", { name: "Open navigation menu" }).click();
  await expect(
    page.getByRole("dialog").getByRole("link", { name: "Overview", exact: true }),
  ).toHaveAttribute("href", "/overview");
  await page.getByRole("dialog").getByRole("link", { name: "Overview", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Needs attention", exact: true })).toBeVisible();
  expect(requests.filter((r) => r.method === "POST")).toHaveLength(0);
});

test("case separates evidence, model, checks and unrecorded execution; draft survives failure", async ({
  page,
}) => {
  const requests = await fixtureApi(page);
  await page.goto("/maintenance/tickets/fixture-case");
  await expect(page.getByRole("heading", { name: "What is blocking progress" })).toBeVisible();
  await expect(page.locator(".decision-summary")).toContainText("Contractor report received");
  await expect(page.locator(".decision-summary")).toContainText("SIMULATED");
  await expect(page.locator(".decision-summary")).toContainText("Model run: Succeeded");
  await expect(page.locator(".decision-summary")).toContainText("Action execution not recorded");
  const textarea = page.locator("form textarea").first();
  await textarea.fill("Fixture response retained after conflict.");
  await page.getByRole("button", { name: "Submit response and continue" }).click();
  await expect(page.getByText(/Fixture conflict/).first()).toBeVisible();
  await expect(textarea).toHaveValue("Fixture response retained after conflict.");
  expect(requests.find((r) => r.path.endsWith("/demo-inputs"))?.body).toMatchObject({
    expected_case_version: 8,
    text: "Fixture response retained after conflict.",
  });
  await page.getByRole("link", { name: "Inspect the full agent workflow" }).click();
  await expect(page.getByRole("heading", { name: "Decision history", exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Work", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Work", exact: true })).toBeVisible();
});

test("approval preserves expected version and rejection retains reason on error", async ({
  page,
}) => {
  const requests = await fixtureApi(page, {
    approval: true,
    actionState: "AWAITING_APPROVAL",
  });
  await page.goto("/maintenance/tickets/fixture-case");
  await page.getByRole("button", { name: "Approve", exact: true }).click();
  await expect.poll(() => requests.some((r) => r.path.includes("/approval"))).toBe(true);
  expect(requests.find((r) => r.path.includes("/approval"))?.body).toMatchObject({
    expected_case_version: 7,
    approve: true,
    action_payload_hash: "fixture-hash",
  });
  await page.getByRole("button", { name: "Reject", exact: true }).click();
  const dialog = page.getByRole("dialog", { name: "Reject proposed action" });
  await dialog.getByRole("textbox").fill("Handover must be reviewed.");
  await dialog.getByRole("button", { name: "Reject action", exact: true }).click();
  await expect(dialog.getByRole("textbox")).toHaveValue("Handover must be reviewed.");
  await expect(dialog.getByText(/Fixture conflict/)).toBeVisible();
  const posts = requests.filter((r) => r.path.includes("/approval"));
  expect(posts.at(-1)?.body).toMatchObject({
    expected_case_version: 8,
    approve: false,
    reason: "Handover must be reviewed.",
  });
});

test("escalation and failed execution stay prominent", async ({ page }) => {
  await fixtureApi(page, {
    escalated: true,
    actionState: "FAILED",
    error: "Fixture execution failed: approval was superseded.",
  });
  await page.goto("/maintenance/tickets/fixture-case");
  await expect(
    page.getByText(/Explicit safety concern requires operator review/).first(),
  ).toBeVisible();
  await expect(page.locator(".decision-summary").getByRole("alert")).toContainText(
    "Fixture execution failed",
  );
});

test("In focus uses portfolio API counts and refreshes them independently of the queue", async ({
  page,
}) => {
  await fixtureApi(page);
  let active = 17;
  let total = 83;
  let calls = 0;
  await page.route("**/api/v1/metrics/dashboard", (route) => {
    calls++;
    return route.fulfill({
      json: {
        total,
        active,
        awaiting_confirmation: 6,
        escalated: 3,
        resolved: 52,
        cancelled: 5,
        resolved_this_week: 9,
        avg_resolution_hours: 18.4,
        agent_active: false,
        active_delta_pct: null,
        awaiting_confirmation_delta_pct: null,
        escalated_delta_pct: null,
      },
    });
  });
  await page.goto("/maintenance");
  const panel = page.getByRole("region", { name: /Every repair.*In focus/ });
  await expect(panel.locator(".mission-stats strong")).toHaveText(["17", "6", "9"]);
  await expect(panel).toContainText("83 total tickets");
  await expect(page.locator(".board-case-title")).toHaveCount(1);
  active = 18;
  total = 84;
  await expect(panel.locator(".mission-stats strong").first()).toHaveText("18", { timeout: 12000 });
  await expect(panel).toContainText("84 total tickets");
  expect(calls).toBeGreaterThan(1);
});
