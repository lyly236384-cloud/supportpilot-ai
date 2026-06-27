import { chromium } from "playwright";
import { mkdirSync, existsSync } from "fs";
import { resolve, dirname } from "path";

const SCREENSHOTS_DIR = resolve(process.cwd(), "../screenshots");
if (!existsSync(SCREENSHOTS_DIR)) mkdirSync(SCREENSHOTS_DIR, { recursive: true });

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext({ viewport: { width: 1440, height: 900 } });
const page = await context.newPage();

const errors = [];
page.on("console", (msg) => {
  if (msg.type() === "error") errors.push(msg.text());
});
page.on("pageerror", (err) => errors.push(err.message));

try {
  // 1. HomePage
  console.log("Navigating to HomePage...");
  await page.goto("http://127.0.0.1:5173", { waitUntil: "networkidle" });
  await page.waitForTimeout(1000);
  await page.screenshot({
    path: resolve(SCREENSHOTS_DIR, "homepage.png"),
    fullPage: true,
  });
  console.log("✅ HomePage screenshot saved");

  // 2. Click "体验客服" → ChatDemoPage
  console.log("Navigating to ChatDemoPage...");
  const chatBtn = page.locator("button", { hasText: "体验客服" });
  await chatBtn.click();
  await page.waitForTimeout(1500);

  // Wait for customer selector to load
  await page.waitForSelector("select", { timeout: 5000 });
  await page.screenshot({
    path: resolve(SCREENSHOTS_DIR, "chat-demo.png"),
    fullPage: true,
  });
  console.log("✅ ChatDemoPage screenshot saved");

  // 3. Send a greeting message
  console.log("Testing greeting message...");
  const textarea = page.locator("textarea");
  await textarea.fill("你好");
  await page.waitForTimeout(300);
  const sendBtn = page.locator("button:has(svg)").last();
  await sendBtn.click();
  await page.waitForTimeout(3000);

  await page.screenshot({
    path: resolve(SCREENSHOTS_DIR, "chat-demo-greeting.png"),
    fullPage: true,
  });
  console.log("✅ ChatDemoPage greeting screenshot saved");

  // 4. Test a logistics question
  console.log("Testing logistics question...");
  await textarea.fill("我的快递什么时候发货？");
  await page.waitForTimeout(300);
  await sendBtn.click();
  await page.waitForTimeout(4000);

  await page.screenshot({
    path: resolve(SCREENSHOTS_DIR, "chat-demo-logistics.png"),
    fullPage: true,
  });
  console.log("✅ ChatDemoPage logistics screenshot saved");

  // Report console errors
  if (errors.length) {
    console.log(`⚠️ Console errors (${errors.length}):`);
    errors.forEach((e) => console.log(`  - ${e}`));
  } else {
    console.log("✅ No console errors");
  }
} catch (err) {
  console.error(`❌ Error: ${err.message}`);
} finally {
  await browser.close();
  console.log("Done.");
}
