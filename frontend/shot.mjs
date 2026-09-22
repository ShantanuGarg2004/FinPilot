import puppeteer from "puppeteer";

const URL = process.env.URL || "http://localhost:5175/";

const USER = {
  id: 1,
  age: 32,
  income: 150000,
  expenses: 80000,
  savings: 40000,
  risk_appetite: "medium",
  financial_goals: "Buy a house in 5 years and build a retirement corpus",
};

const HEALTH = {
  score: 74,
  savings_ratio: 27,
  expense_ratio: 53,
  emg_months: 6,
  pillar_scores: {
    savings_rate: 19,
    expense_control: 15,
    emergency_fund: 16,
    debt_ratio: 12,
    retirement: 6,
    tax_efficiency: 3,
    surplus_buffer: 4,
  },
  insights: [
    "Healthy savings rate above the 20% benchmark.",
    "Comfortable 6-month emergency buffer in place.",
  ],
  warnings: [
    "Lifestyle expenses are slightly high relative to income.",
    "Retirement contributions could be increased for your age.",
  ],
};

const AI_REPORT = `## Executive Summary
Your finances are in **good shape**. Focus on trimming discretionary spend and boosting retirement contributions.

### Recommendations
1. Redirect ~5% of income into an index SIP.
2. Build a dedicated tax-saving allocation (ELSS/NPS).
3. Review lifestyle subscriptions quarterly.`;

const GOAL = {
  goal_name: "Retirement Home",
  feasibility_score: 82,
  feasibility_label: "Highly Attainable",
  feasible: true,
  scenario_message: "At your current savings rate you are on track to reach this goal.",
  recommended_timeline: "4 yr 6 mo",
  current_monthly_saving: 40000,
  required_monthly_saving: 36500,
  monthly_surplus: 3500,
  monthly_gap: 0,
  cagr_moderate: "11%",
  projected_value: 8200000,
  coverage_pct: 96,
  investment_strategy: "Balanced equity + debt SIP",
  secondary_suggestion: "Add a mid-cap allocation for growth",
  rationale: "A balanced allocation reaches the target within the horizon while controlling downside risk.",
  scenarios: [
    { scenario: "Conservative", monthly_needed: 52000, cagr: "6.5%", years: 5, feasible: false, recommended_timeline: "6 yr" },
    { scenario: "Balanced", monthly_needed: 36500, cagr: "11%", years: 5, feasible: true, recommended_timeline: "5 yr" },
    { scenario: "Aggressive", monthly_needed: 28000, cagr: "16%", years: 5, feasible: true, recommended_timeline: "4 yr" },
  ],
};

async function mock(page) {
  await page.setRequestInterception(true);
  page.on("request", (req) => {
    const url = req.url();
    const method = req.method();
    const json = (obj) => req.respond({ status: 200, contentType: "application/json", body: JSON.stringify(obj) });
    if (url.includes("/api/users")) return json({ users: [USER] });
    if (url.includes("/api/report/")) return json({ health: HEALTH, ai_report: AI_REPORT });
    if (url.includes("/api/generate-report")) return json({ user_id: 1, health: HEALTH, ai_report: AI_REPORT });
    if (url.includes("/api/chat/history")) {
      if (method === "DELETE") return json({ ok: true });
      return json({ history: [
        { role: "user", message: "How am I doing on my retirement goal?" },
        { role: "ai", message: "You're **on track**. Consider increasing your SIP by 5% to reach it ~6 months sooner." },
      ] });
    }
    if (url.includes("/api/goal-plan")) return json(GOAL);
    return req.continue();
  });
}

async function clickByText(page, tag, text) {
  await page.evaluate((tag, text) => {
    const els = [...document.querySelectorAll(tag)];
    const el = els.find((e) => e.textContent.trim().includes(text));
    if (el) el.click();
  }, tag, text);
}

const browser = await puppeteer.launch({ headless: "new", args: ["--no-sandbox"] });
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

async function capture(name, w, h) {
  const page = await browser.newPage();
  await page.setViewport({ width: w, height: h, deviceScaleFactor: 1 });
  await mock(page);
  await page.goto(URL, { waitUntil: "networkidle2", timeout: 30000 }).catch(() => {});
  await wait(700);
  await page.screenshot({ path: `shots/${name}-profile.png` });

  // Select the mocked profile → dashboard
  await clickByText(page, "div", "Buy a house in 5 years");
  await wait(900);
  await page.screenshot({ path: `shots/${name}-dashboard.png` });

  await clickByText(page, "button", "Advisory");
  await wait(1000);
  await page.screenshot({ path: `shots/${name}-advisory.png` });

  await clickByText(page, "button", "Chat");
  await wait(900);
  await page.screenshot({ path: `shots/${name}-chat.png` });

  await clickByText(page, "button", "Goals");
  await wait(700);
  // fill goal inputs + calculate
  await page.evaluate(() => {
    const nums = [...document.querySelectorAll('input[type=number]')];
    const setV = (el, v) => {
      const proto = Object.getPrototypeOf(el);
      Object.getOwnPropertyDescriptor(proto, "value").set.call(el, v);
      el.dispatchEvent(new Event("input", { bubbles: true }));
    };
    const txt = document.querySelector('input[type=text]');
    if (txt) setV(txt, "Retirement Home");
    if (nums[0]) setV(nums[0], "7500000");
  });
  await clickByText(page, "button", "Calculate Pilot Path");
  await wait(900);
  await page.screenshot({ path: `shots/${name}-goals.png` });

  console.log("captured:", name);
  await page.close();
}

try {
  await capture("d1440", 1440, 900);
  await capture("m390", 390, 844);
} finally {
  await browser.close();
}
