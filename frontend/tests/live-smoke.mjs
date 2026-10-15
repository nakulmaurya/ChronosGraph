/** Live localhost integration only. No fixtures, network stubs or paid models.
 * Override checks restore only the local policy fields changed by this test.
 * Run after npm run build + npm start, with seeded FastAPI on port 8000.
 */
import { chromium } from "@playwright/test";
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
import { execFileSync } from "node:child_process";
import path from "node:path";
const FRONTEND = process.env.FRONTEND_URL || "http://127.0.0.1:3001";
const API = process.env.TEST_API_URL || "http://localhost:8000/api/v1";
const out = path.resolve(process.env.EVIDENCE_DIR || "../../ui-evidence");
await mkdir(out, { recursive: true });
const checks = [];
const measurements = [];
const errors = [];
const mutationIds = [];
let policySnapshot = [];
const mark = (name) => {
  checks.push({ check: name, status: "PASS" });
  console.log(`PASS ${name}`);
};
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || "/usr/local/bin/chromium",
  headless: true,
  args: ["--no-sandbox"],
});
const context = await browser.newContext({
  viewport: { width: 1560, height: 1050 },
  reducedMotion: "reduce",
});
const page = await context.newPage();
page.on("pageerror", (e) => errors.push(e.message));
// Do not consume a response body twice when asserting status.
async function apiPost(endpoint, body) {
  const res = await fetch(API + endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const d = await res.json();
  assert.ok(res.ok, JSON.stringify(d));
  return d;
}
async function action(name, endpoint) {
  const responsePromise = page.waitForResponse(
    (r) => r.url().endsWith(endpoint) && r.request().method() === "POST",
  );
  await page.getByRole("button", { name, exact: true }).click();
  const response = await responsePromise;
  const data = await response.json();
  assert.ok(response.ok(), JSON.stringify(data));
  await page
    .getByRole("status")
    .filter({ hasText: /Cloning|Reading|Recording|Replaying|Writing/ })
    .waitFor({ state: "hidden" })
    .catch(() => {});
  return data;
}
async function shot(name) {
  await page.waitForTimeout(250);
  await page.screenshot({
    path: path.join(out, name + ".png"),
    fullPage: true,
  });
}
async function noOverflow() {
  assert.ok(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
    "No horizontal page overflow",
  );
}
try {
  await page.goto(FRONTEND);
  await page.locator("#tenant").waitFor();
  await page.waitForFunction(
    () =>
      document.querySelector("#tenant")?.options.length >= 2 &&
      !document.querySelector("#tenant")?.disabled,
  );
  await page.locator(".react-flow__node").first().waitFor();
  await noOverflow();
  mark("Live tenant catalog and initial source graph");
  const audit = await action("Run GRAPH.COPY audit", "/track1/sandbox-audit");
  assert.equal(audit.sandbox_cleaned_up, true);
  assert.ok(audit.impacted_files.length > 0);
  await page.getByText("VERIFIED", { exact: true }).waitFor();
  await shot("01-sandbox-desktop");
  mark("Track 1 live audit, impacted nodes and verified sandbox cleanup");
  await page.getByRole("button", { name: "Fit graph", exact: true }).click();
  await page.locator(".react-flow__node").first().click();
  await page.getByText("SELECTED NODE", { exact: true }).waitFor();
  await shot("02-node-inspector");
  await page.getByRole("button", { name: "Clear selection" }).click();
  const draggable = page.locator(".react-flow__node").first();
  const beforeDrag = await draggable.getAttribute("style");
  const box = await draggable.boundingBox();
  assert.ok(box);
  await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
  await page.mouse.down();
  await page.mouse.move(
    box.x + box.width / 2 + 35,
    box.y + box.height / 2 + 25,
    { steps: 8 },
  );
  await page.mouse.up();
  assert.notEqual(await draggable.getAttribute("style"), beforeDrag);
  mark("Interactive node selection, metadata and draggable positions");
  await page.locator(".cypher-drawer summary").click();
  assert.ok(
    (await page.locator(".cypher-drawer pre").textContent()).includes("MATCH"),
  );
  await page.locator(".cypher-drawer summary").click();
  mark("Exact backend Cypher drawer");
  await page
    .getByRole("button", { name: "Show all payload nodes", exact: true })
    .click();
  await page.waitForFunction(
    (total) => document.querySelectorAll(".react-flow__node").length === total,
    audit.subgraph.nodes.length,
  );
  await page
    .getByRole("button", { name: "Focus files & rules", exact: true })
    .click();
  mark("Full API payload remains accessible behind focused graph view");
  await page.getByRole("button", { name: /TRACK 02/ }).click();
  const scenario = `UI smoke policy review falkordb/graph.py ${Date.now()}`;
  await page.locator("#scenario").fill(scenario);
  assert.equal(
    await page
      .getByRole("button", { name: "Run #2 · Compiled replay" })
      .isDisabled(),
    true,
  );
  const cold = await action("Run #1 · Cold triage", "/track2/investigate");
  assert.equal(cold.total_steps_executed, 5);
  assert.equal(
    cold.subgraph.nodes.filter((n) => n.status === "DEAD_END").length,
    2,
  );
  await shot("03-memory-cold");
  const warm = await action("Run #2 · Compiled replay", "/track2/investigate");
  assert.equal(warm.total_steps_executed, 3);
  assert.equal(warm.tokens_used, 0);
  measurements.push({
    tenant: "repo_falkordb_py",
    cold_duration_ms: cold.duration_ms,
    warm_duration_ms: warm.duration_ms,
    latency_speedup_factor: warm.latency_speedup_factor,
    cold_actions: cold.total_steps_executed,
    warm_actions: warm.total_steps_executed,
  });
  await page.getByText("40% fewer actions", { exact: true }).waitFor();
  await shot("04-memory-replay");
  mark(
    "Track 2 real 5-to-3 replay, two dead ends pruned and zero-model telemetry",
  );
  await page.locator("#scenario").fill(scenario + " changed");
  assert.equal(
    await page
      .getByRole("button", { name: "Run #2 · Compiled replay" })
      .isDisabled(),
    true,
  );
  await page.locator("#scenario").fill(scenario);
  mark("Scenario changes invalidate replay availability");
  // An external local policy write invalidates the backend fingerprint.
  const original = await apiPost("/track3/ask-brain", {
    tenant_graph: "repo_falkordb_py",
    question: "Current policy",
    file_path: "falkordb/graph.py",
  });
  policySnapshot = [
    ...original.active_decisions,
    ...original.superseded_decisions,
  ];
  const external = await apiPost("/track3/override-policy", {
    tenant_graph: "repo_falkordb_py",
    target_file_path: "falkordb/graph.py",
    scope_symbol: original.active_decisions[0].scope_symbol,
    new_rule_text: "UI smoke external override: bounded local graph reads.",
    rationale:
      "Temporary localhost integration verification; original fields restored after test.",
  });
  mutationIds.push(
    ...external.active_decisions
      .map((d) => d.id)
      .filter((id) => !policySnapshot.some((p) => p.id === id)),
  );
  const staleResponse = page.waitForResponse(
    (r) =>
      r.url().endsWith("/track2/investigate") &&
      r.request().method() === "POST",
  );
  await page.getByRole("button", { name: "Run #2 · Compiled replay" }).click();
  const sr = await staleResponse;
  assert.ok([404, 409].includes(sr.status()));
  await page.locator(".error-banner").waitFor();
  await page
    .getByText("Playbook unavailable or stale. Run a fresh cold triage.", {
      exact: true,
    })
    .waitFor();
  assert.equal(
    await page.locator(".step-comparison strong").first().textContent(),
    "5",
  );
  await page
    .getByText(
      "Previous successful result retained below. The latest request failed.",
      { exact: true },
    )
    .waitFor();
  await shot("05-stale-playbook");
  assert.equal(
    await page
      .getByRole("button", { name: "Run #2 · Compiled replay" })
      .isDisabled(),
    true,
  );
  mark("Backend stale-playbook refusal is surfaced and replay disabled");
  await page.getByRole("button", { name: /TRACK 03/ }).click();
  await page.locator("#policy-file").selectOption("falkordb/graph.py");
  const brain = await action("Read current policy", "/track3/ask-brain");
  assert.ok(brain.active_decisions.length && brain.superseded_decisions.length);
  assert.ok(
    (await page.locator("#scope").inputValue()) ===
      original.active_decisions[0].scope_symbol,
  );
  await page.locator(".policy details").first().locator("summary").click();
  await shot("06-policy-lineage");
  mark("Track 3 active/superseded policies, times, scope and provenance");
  await page.locator(".override-form>summary").click();
  await page
    .locator("#rule")
    .fill("UI smoke architect override: preserve explicit query timeouts.");
  await page
    .locator("#rationale")
    .fill(
      "Temporary local UI verification. Restore initial policy fields in test cleanup.",
    );
  assert.equal(
    await page
      .getByRole("button", { name: "Record policy override" })
      .isDisabled(),
    true,
  );
  await page
    .getByLabel("I confirm this mutates the selected local graph.")
    .check();
  const override = await action(
    "Record policy override",
    "/track3/override-policy",
  );
  mutationIds.push(
    ...override.active_decisions
      .map((d) => d.id)
      .filter((id) => !policySnapshot.some((p) => p.id === id)),
  );
  assert.ok(
    override.active_decisions.every(
      (d) => d.source_type === "LIVE_ARCHITECT_OVERRIDE",
    ),
  );
  await page.getByText(/Policy override recorded/).waitFor();
  await shot("07-policy-override");
  mark(
    "Explicit confirmed override writes real lineage and invalidates UI replay",
  );
  await page.locator("#tenant").selectOption("repo_graphrag_sdk");
  await page.waitForFunction(() => !document.querySelector("#tenant").disabled);
  assert.equal(await page.locator(".policy").count(), 0);
  assert.ok(
    (await page.locator("#policy-file").inputValue()).startsWith(
      "graphrag_sdk/",
    ),
  );
  const sdk = await action("Read current policy", "/track3/ask-brain");
  assert.ok(sdk.file_path.startsWith("graphrag_sdk/"));
  mark("Tenant switch clears results and loads SDK-specific policy data");
  await page.getByRole("button", { name: "MCP config", exact: true }).click();
  const dialog = page.getByRole("dialog");
  await dialog.waitFor();
  assert.equal(await dialog.locator(".tools-list article").count(), 5);
  await page.locator("#mcp-cwd").fill("/home/user/ChronosGraph/backend");
  assert.ok(
    (await dialog.locator("pre").textContent()).includes(
      "/home/user/ChronosGraph/backend",
    ),
  );
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await page.getByRole("button", { name: "Copy config", exact: true }).click();
  await page.getByText("Copied config", { exact: true }).waitFor();
  assert.ok(
    (await page.evaluate(() => navigator.clipboard.readText())).includes(
      "app.mcp_server.server",
    ),
  );
  await shot("08-mcp-config");
  await page.keyboard.press("Escape");
  await dialog.waitFor({ state: "hidden" });
  assert.equal(
    await page
      .getByRole("button", { name: "MCP config", exact: true })
      .evaluate((e) => e === document.activeElement),
    true,
  );
  mark("MCP five-tool template, editable cwd, Escape and focus restoration");
  await page.route("**/api/v1/track3/ask-brain", (route) =>
    route.abort("failed"),
  );
  await page
    .getByRole("button", { name: "Read current policy", exact: true })
    .click();
  await page.locator(".error-banner").waitFor();
  assert.ok(
    (await page.locator(".error-banner").textContent()).includes(
      "Cannot reach the local backend",
    ),
  );
  await shot("09-network-error");
  await page.unroute("**/api/v1/track3/ask-brain");
  await action("Read current policy", "/track3/ask-brain");
  mark("Network failure explains recovery without fake fallback data");
  await page.setViewportSize({ width: 390, height: 844 });
  await noOverflow();
  await shot("10-mobile-policy");
  await page.getByRole("button", { name: /TRACK 01/ }).click();
  await action("Run GRAPH.COPY audit", "/track1/sandbox-audit");
  await noOverflow();
  await shot("11-mobile-sandbox");
  await page.getByRole("button", { name: /TRACK 02/ }).click();
  await page
    .locator("#scenario")
    .fill(`Review policy ${sdk.file_path} ${Date.now()}`);
  await action("Run #1 · Cold triage", "/track2/investigate");
  await action("Run #2 · Compiled replay", "/track2/investigate");
  await noOverflow();
  await shot("12-mobile-memory");
  await page.getByRole("button", { name: "MCP config", exact: true }).click();
  assert.ok(await dialog.evaluate((e) => e.scrollWidth <= e.clientWidth + 1));
  await shot("13-mobile-modal");
  await page.keyboard.press("Escape");
  mark(
    "390px mobile layouts: all three tracks and MCP dialog, no page overflow",
  );
  // Opt-in live external repositories, in addition to the unchanged 15 baseline checks.
  const externalTenants = (process.env.REAL_WORLD_TENANTS || "").split(",").filter(Boolean);
  const catalog = externalTenants.length ? await (await fetch(API + "/tenants")).json() : [];
  await page.setViewportSize({ width: 1560, height: 1050 });
  for (const tenant of externalTenants) {
    const entry = catalog.find((t) => t.tenant_graph === tenant);
    assert.ok(entry && entry.preset_files.length, `Registered policy-backed tenant ${tenant}`);
    await page.locator("#tenant").selectOption(tenant);
    await page.waitForFunction(() => !document.querySelector("#tenant").disabled);
    await page.getByRole("button", { name: /TRACK 03/ }).click();
    await page.locator("#policy-file").selectOption(entry.preset_files[0]);
    const policy = await action("Read current policy", "/track3/ask-brain");
    assert.ok(policy.active_decisions.length && policy.superseded_decisions.length);
    await page.getByRole("button", { name: /TRACK 01/ }).click();
    const boxes = page.locator('fieldset input[type="checkbox"]');
    for (const box of await boxes.all()) await box.uncheck();
    await boxes.first().check();
    const audit = await action("Run GRAPH.COPY audit", "/track1/sandbox-audit");
    assert.equal(audit.sandbox_cleaned_up, true);
    assert.ok(audit.recommended_reviewers.length);
    await page.getByRole("button", { name: /TRACK 02/ }).click();
    await page.locator("#scenario").fill(`Review policy ${entry.preset_files[0]} ${Date.now()}`);
    const cold = await action("Run #1 · Cold triage", "/track2/investigate");
    const warm = await action("Run #2 · Compiled replay", "/track2/investigate");
    assert.equal(cold.total_steps_executed, 5);
    assert.equal(warm.total_steps_executed, 3);
    assert.equal(warm.subgraph.nodes.filter((n) => n.status === "DEAD_END").length, 0);
    measurements.push({ tenant, clone_ms: audit.sandbox_clone_time_ms, cold_ms: cold.duration_ms, warm_ms: warm.duration_ms });
    await noOverflow();
    await shot(`external-${tenant}`);
    mark(`External ${tenant}: tenant switch, current/history policy, clone cleanup/reviewers, 5-to-3 replay`);
  }
  assert.deepEqual(errors, []);
  mark("No uncaught browser errors");
} finally {
  if (policySnapshot.length) {
    const restore = `import json,sys\nfrom app.db.client import db_manager\nd=json.load(sys.stdin)\nfor ident in set(d['ids']): db_manager.query('repo_falkordb_py','MATCH (d:Decision {id:$id}) DETACH DELETE d',{'id':ident})\nfor p in d['policies']: db_manager.query('repo_falkordb_py','MATCH (d:Decision {id:$id}) SET d.status=$status,d.valid_to=$valid_to,d.recorded_to=$recorded_to',{'id':p['id'],'status':p['status'],'valid_to':p.get('valid_to'),'recorded_to':p.get('recorded_to')})\nprint('Local policy state restored')`;
    const restored = execFileSync(
      process.env.BACKEND_PYTHON || "python3",
      ["-c", restore],
      {
        cwd: path.resolve("../backend"),
        input: JSON.stringify({ ids: mutationIds, policies: policySnapshot }),
        encoding: "utf8",
      },
    );
    console.log(restored.trim());
  }
  await writeFile(
    path.join(out, "smoke-results.json"),
    JSON.stringify({ checks, measurements, browserErrors: errors }, null, 2),
  );
  await browser.close();
}
