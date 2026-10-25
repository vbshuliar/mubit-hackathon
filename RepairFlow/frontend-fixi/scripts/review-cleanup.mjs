import { chromium } from "@playwright/test";
import { mkdir, writeFile } from "node:fs/promises";
const phase = process.env.PHASE || "before";
const browser = await chromium.launch({ channel: "chrome" });
const report = [];
const property = "/properties/b099e439-d037-56de-bf95-f730043ab123";
for (const [size, viewport] of Object.entries({
  desktop: { width: 1440, height: 1000 },
  mobile: { width: 390, height: 844 },
})) {
  const context = await browser.newContext({ viewport, reducedMotion: "reduce" });
  await context.route("**/api/v1/**", (r) =>
    ["GET", "HEAD", "OPTIONS"].includes(r.request().method()) ? r.continue() : r.abort(),
  );
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const routes = [
    "/overview",
    "/maintenance",
    "/messages",
    "/properties",
    "/contractors",
    "/tenants",
    "/insights",
    "/reports",
    ...["history", "details", "documents", "notes"].map((s) => property + "/" + s),
  ];
  for (const route of routes) {
    await page.goto("http://localhost:5174" + route);
    await page.waitForTimeout(800);
    const name = route.startsWith(property) ? "property-" + route.split("/").pop() : route.slice(1);
    await mkdir(`artifacts/ui-cleanup/${phase}`, { recursive: true });
    await page.screenshot({
      path: `artifacts/ui-cleanup/${phase}/${name}-${size}.png`,
      fullPage: true,
    });
    report.push({
      size,
      route,
      overflow: await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
      text: (await page.locator("main").innerText()).slice(0, 12000),
    });
    if (["/contractors", "/tenants", "/messages", "/maintenance"].includes(route)) {
      const href = await page
        .locator(`main a[href^="${route}/"]`)
        .first()
        .getAttribute("href")
        .catch(() => null);
      if (href) {
        await page.goto("http://localhost:5174" + href);
        await page.waitForTimeout(700);
        await page.screenshot({
          path: `artifacts/ui-cleanup/${phase}/${name}-detail-${size}.png`,
          fullPage: true,
        });
        report.push({
          size,
          route: href,
          overflow: await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
          text: (await page.locator("main").innerText()).slice(0, 14000),
        });
      }
    }
  }
  report.push({ size, errors });
  await context.close();
}
await writeFile(`artifacts/ui-cleanup/${phase}/review.json`, JSON.stringify(report, null, 2));
await browser.close();
