import { expect, test, type Page } from "@playwright/test";
import { readFile } from "node:fs/promises";
import { snapshot } from "./fixtures";
const outcome =
  'Scaffold handover checked. Roof flashing repaired; follow-up inspection found no remaining leak. Tenant said, "dry after heavy rain".\n' +
  "Full inspection evidence retained for the operator. ".repeat(14) +
  "END OF COMPLETE OUTCOME";
const contractor =
  "Illustrative South West Roofing, Conservation and Specialist Access Services (fictional, SIMULATED)";
const items = [
  {
    case_id: "roof",
    case_number: 1,
    title: "Roof flashing and ceiling water ingress requiring a follow-up inspection",
    trade: "ROOFING",
    status: "RESOLVED",
    created_at: "2026-09-19T10:00:00Z",
    resolved_at: null,
    outcome,
    contractor_name: contractor,
    quoted_pence: 125000,
  },
  {
    case_id: "tap",
    case_number: 2,
    title: "Kitchen tap leaking",
    trade: "PLUMBING",
    status: "ACTIVE",
    created_at: "2025-01-10T10:00:00Z",
    resolved_at: null,
    outcome: null,
    contractor_name: null,
    quoted_pence: 20000,
  },
];
async function setup(page: Page) {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.route("**/api/v1/**", (r) => {
    if (r.request().method() !== "GET")
      return r.fulfill({ status: 409, json: { detail: "Isolated test: no writes" } });
    const path = new URL(r.request().url()).pathname;
    let json: unknown = { items: [], unread_count: 0 };
    if (path.endsWith("/properties/property/history")) json = { property_id: "property", items };
    else if (path.endsWith("/properties/property/stats"))
      json = {
        property_id: "property",
        total_count: 2,
        active_count: 1,
        recurring_issues: [],
        quoted_by_trade: [],
        quoted_by_year: [],
        build_year: null,
      };
    else if (path.endsWith("/properties/property"))
      json = {
        ...snapshot.property,
        tenants: [],
        tenant_count: 0,
        total_case_count: 2,
        open_case_count: 1,
        photo_key: null,
        is_archived: false,
      };
    return r.fulfill({ json });
  });
  await page.goto("/properties/property/history?address=Retained&postcode=BS1");
  await expect(page.getByRole("status").filter({ hasText: "Showing 2 of 2" })).toBeVisible();
}

test("history filters, back/forward, sort and retained selection use the URL", async ({ page }) => {
  await setup(page);
  await page.getByRole("checkbox", { name: /Select Roof flashing/ }).check();
  await page.getByRole("combobox", { name: "Trade", exact: true }).selectOption("ROOFING");
  await expect(page.getByRole("status").filter({ hasText: "Showing 1 of 2" })).toBeVisible();
  await expect(page).toHaveURL(/trade=ROOFING/);
  await page.getByRole("combobox", { name: "Year", exact: true }).selectOption("2025");
  await expect(page.getByText("No cases match the current filter.")).toBeVisible();
  await page.goBack();
  await expect(page.getByRole("combobox", { name: "Year", exact: true })).toHaveValue("");
  await expect(page.getByRole("checkbox", { name: /Select Roof flashing/ })).toBeChecked();
  await page.goForward();
  await expect(page.getByRole("combobox", { name: "Year", exact: true })).toHaveValue("2025");
  await page.getByRole("button", { name: "Clear filters", exact: true }).click();
  await expect(page.getByRole("status").filter({ hasText: "Showing 2 of 2" })).toBeVisible();
  await page.getByRole("button", { name: "Quoted", exact: true }).click();
  await expect(page.getByRole("columnheader", { name: "Quoted" })).toHaveAttribute(
    "aria-sort",
    "ascending",
  );
  await expect(
    page
      .locator("tbody tr")
      .filter({ has: page.getByRole("checkbox") })
      .first(),
  ).toContainText("Kitchen tap leaking");
  await expect(page).toHaveURL(/address=Retained/);
  await page.reload();
  await expect(page.getByRole("columnheader", { name: "Quoted" })).toHaveAttribute(
    "aria-sort",
    "ascending",
  );
});

test("compact rows reveal full details by keyboard and export the complete outcome", async ({
  page,
}) => {
  await setup(page);
  const row = page
    .locator("tbody tr")
    .filter({ has: page.getByRole("checkbox", { name: /Select Roof flashing/ }) });
  expect((await row.boundingBox())!.height).toBeLessThan(130);
  const disclosure = page.getByRole("button", { name: /details for Roof/ });
  await disclosure.focus();
  await page.keyboard.press("Enter");
  await expect(disclosure).toHaveAttribute("aria-expanded", "true");
  const panel = page.locator(`[id="${await disclosure.getAttribute("aria-controls")}"]`);
  await expect(panel).toContainText("END OF COMPLETE OUTCOME");
  await expect(panel).toContainText(contractor);
  await page.keyboard.press("Enter");
  await expect(panel).toBeHidden();
  await page.getByRole("checkbox", { name: "Select all visible history rows" }).check();
  const download = page.waitForEvent("download");
  await page.getByRole("button", { name: "Export selected (2)" }).click();
  const csv = await readFile((await (await download).path())!, "utf8");
  expect(csv).toContain(outcome.replaceAll('"', '""'));
  expect(csv).toContain(contractor);
  await page.getByRole("link", { name: /^Open case: Roof/ }).click();
  await expect(page).toHaveURL(/maintenance\/tickets\/roof/);
});

for (const viewport of [
  { width: 390, height: 844 },
  { width: 768, height: 1024 },
  { width: 844, height: 390 },
]) {
  test(`history is contained and keyboard-scrollable at ${viewport.width}×${viewport.height}`, async ({
    page,
  }) => {
    await page.setViewportSize(viewport);
    await setup(page);
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(
      true,
    );
    const region = page.getByRole("region", { name: "Property maintenance history" });
    await region.focus();
    await page.keyboard.press("ArrowRight");
    await expect.poll(() => region.evaluate((el) => el.scrollLeft)).toBeGreaterThan(0);
    await page.getByRole("button", { name: /details for Roof/ }).click();
    await expect(page.getByRole("heading", { name: "Full outcome" }).first()).toBeVisible();
    await page.getByRole("link", { name: /^Open case: Roof/ }).focus();
    await expect(page.getByRole("link", { name: /^Open case: Roof/ })).toBeInViewport();
  });
}
