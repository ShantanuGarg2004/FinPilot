/**
 * Optional browser check. Not part of `npm test`.
 * Vite must already be running at http://localhost:5173.
 * Does not assert pixels.
 */
import puppeteer from "puppeteer";

const base = process.env.FINPILOT_WEB_URL || "http://localhost:5173";

function assertInViewport(box, viewport, label) {
  if (box.width <= 0 || box.height <= 0) {
    throw new Error(`${label} has no size`);
  }
  if (box.top < 0 || box.left < 0 || box.bottom > viewport.height + 1 || box.right > viewport.width + 1) {
    throw new Error(`${label} is outside the viewport ${JSON.stringify(box)}`);
  }
}

const browser = await puppeteer.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });
  await page.goto(base + "/", { waitUntil: "networkidle0" });
  await page.click("button.nav-login");
  const dialog = await page.waitForSelector("[role=dialog]");
  const box = await dialog.boundingBox();
  assertInViewport(box, page.viewport(), "Sign in dialog");
  console.log("Sign in dialog is inside the viewport");

  await page.goto(base + "/dashboard", { waitUntil: "networkidle0" });
  await page.waitForSelector("button.nav-login");
  const appShell = await page.$("text/Wealth Manager");
  if (appShell) throw new Error("signed-out /dashboard opened the app shell");
  const path = new URL(page.url()).pathname;
  if (path !== "/dashboard") throw new Error(`expected /dashboard, got ${path}`);
  console.log("signed-out /dashboard stays on the landing page");
} finally {
  await browser.close();
}
