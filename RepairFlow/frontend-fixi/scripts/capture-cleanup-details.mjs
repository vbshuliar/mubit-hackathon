import { chromium } from "@playwright/test";
import { writeFile } from "node:fs/promises";
const browser = await chromium.launch({ channel: "chrome" });
const results = [];
for (const [size, viewport] of Object.entries({
  desktop: { width: 1440, height: 1000 },
  tablet: { width: 768, height: 1024 },
  mobile: { width: 390, height: 844 },
})) {
  const context = await browser.newContext({ viewport, reducedMotion: "reduce" });
  let writes = 0;
  await context.route("**/api/v1/**", (r) => {
    if (!["GET", "HEAD", "OPTIONS"].includes(r.request().method())) {
      writes++;
      return r.abort();
    }
    return r.continue();
  });
  const page = await context.newPage();
  const routes = {
    overview: "/overview",
    "messages-detail": "/messages/f0372992-efae-54ff-9a0d-2f3ff7aee6cf",
    "case-agent": "/maintenance/tickets/17b4bf7f-1405-5f9d-9822-26a780075bb7/agent",
    "case-work": "/maintenance/tickets/17b4bf7f-1405-5f9d-9822-26a780075bb7/work",
    maintenance: "/maintenance",
    "property-history": "/properties/b099e439-d037-56de-bf95-f730043ab123/history",
  };
  for (const [name, path] of Object.entries(routes)) {
    await page.goto("http://localhost:5174" + path);
    await page.waitForTimeout(900);
    await page.screenshot({
      path: `artifacts/ui-cleanup/after/${name}-${size}.png`,
      fullPage: true,
    });
    results.push({
      size,
      path,
      overflow: await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
    });
    if (name === "property-history") {
      const region = page.getByRole("region", { name: "Property maintenance history" });
      const row = page
        .locator("tbody tr")
        .filter({ hasText: "Loose handrail on the staircase" })
        .first();
      await row.getByRole("button").click();
      await region.scrollIntoViewIfNeeded();
      await page.screenshot({ path: `artifacts/ui-cleanup/after/history-expanded-${size}.png` });
    }
  }
  await page.goto("http://localhost:5174/");
  await page.locator("h1").waitFor();
  await page.screenshot({ path: `artifacts/ui-cleanup/after/homepage-${size}.png` });
  results.push({ size, blockedWrites: writes });
  await context.close();
}
await writeFile(
  "artifacts/ui-cleanup/after/supplemental-checks.json",
  JSON.stringify(results, null, 2),
);
await browser.close();
