import { chromium } from "@playwright/test";
import { writeFile } from "node:fs/promises";
const base = process.env.FIXI_PREVIEW_URL || "http://localhost:5174";
const browser = await chromium.launch({ channel: "chrome", headless: true });
const errors = [];
for (const [name, viewport] of Object.entries({
  desktop: { width: 1440, height: 1000 },
  tablet: { width: 768, height: 1024 },
  mobile: { width: 390, height: 844 },
})) {
  const context = await browser.newContext({ viewport });
  // Verification never writes to the real backend.
  await context.route("**/api/v1/**", (route) =>
    ["GET", "HEAD", "OPTIONS"].includes(route.request().method())
      ? route.continue()
      : route.abort(),
  );
  const page = await context.newPage();
  page.on("pageerror", (error) => errors.push({ name, error: error.message }));
  await page.goto(`${base}/maintenance`);
  await page.getByRole("heading", { name: "Repair workspace", exact: true }).waitFor();
  await page.locator(".board-case").first().waitFor();
  await page.waitForTimeout(1200);
  await page.screenshot({
    path: `artifacts/redesign/maintenance-${name}.png`,
    fullPage: true,
  });
  if (name === "desktop") await page.screenshot({ path: "public/preview/maintenance-desktop.png" });
  if (name === "mobile") await page.screenshot({ path: "public/preview/maintenance-mobile.png" });
  const caseLink = page.locator(".board-case-title").first();
  const href = await caseLink.getAttribute("href");
  await page.goto(`${base}${href}`);
  await page.getByRole("heading", { name: "The agent's decision", exact: true }).waitFor();
  await page.waitForTimeout(800);
  await page.screenshot({
    path: `artifacts/redesign/case-${name}.png`,
    fullPage: true,
  });
  console.log(
    name,
    "case",
    href,
    "overflow",
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
  );
  await page.goto(`${base}/overview`);
  await page.getByRole("heading", { name: "Needs attention", exact: true }).waitFor();
  await page.screenshot({
    path: `artifacts/redesign/overview-${name}.png`,
    fullPage: true,
  });
  // Prove the preview does not depend on the backend.
  let homepageRequests = 0;
  await context.unroute("**/api/v1/**");
  await context.route("**/api/v1/**", (route) => {
    homepageRequests++;
    return route.abort();
  });
  await page.goto(base);
  await page.locator("h1").waitFor();
  await page.locator("#how-it-works").scrollIntoViewIfNeeded();
  await page.getByRole("button", { name: /^(02 )?Coordinate$/ }).click();
  await page.waitForTimeout(1500);
  await page.screenshot({ path: `artifacts/redesign/walkthrough-${name}.png` });
  await page.evaluate(() => window.scrollTo(0, 0));
  await page.screenshot({
    path: `artifacts/redesign/homepage-${name}.png`,
    fullPage: true,
  });
  console.log(
    name,
    "homepage requests",
    homepageRequests,
    "overflow",
    await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
    "canvas",
    await page.locator("canvas").count(),
  );
  await context.close();
}
await writeFile("artifacts/redesign/browser-errors.json", JSON.stringify(errors, null, 2));
await browser.close();
