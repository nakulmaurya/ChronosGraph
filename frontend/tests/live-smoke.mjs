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
await context.grantPermissions(["clipboard-read", "clipboard-write"]);
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
  // T-06: real commit selection supplies file scope; submitted snippet is separate.
  const commit = JSON.parse(
    execFileSync(
      process.env.BACKEND_PYTHON || "python3",
      [
        "-c",
        "import json;from app.services.common import read;print(json.dumps(read('repo_falkordb_py', 'MATCH (p:PullRequest)-[:MODIFIES]->(f:File) RETURN p.number AS number,f.path AS path ORDER BY coalesce(p.committed_at,p.merged_at,0) DESC LIMIT 1')[0][0]))",
      ],
      { cwd: path.resolve("../backend"), encoding: "utf8" },
    ),
  );
  await page.locator("#pr").selectOption(String(commit.number));
  assert.equal(await page.locator("fieldset input:checked").count(), 0);
  await page.locator(".patch-editor summary").click();
  await page.getByLabel("Apply Python snippet overlay").check();
  await page
    .locator("#python-patch")
    .fill(
      "def t06_helper():\n    return 1\ndef t06_patch():\n    return t06_helper()\n",
    );
  const patched = await action("Run GRAPH.COPY audit", "/track1/sandbox-audit");
  assert.ok(
    patched.subgraph.nodes.some(
      (n) => n.metadata.patch_source_type === "AST_PATCH_SIMULATION",
    ),
  );
  assert.equal(patched.sandbox_cleaned_up, true);
  assert.ok(Array.isArray(patched.impacted_test_files));
  assert.ok(patched.recommended_pytest_command.startsWith("pytest"));
  assert.ok(patched.patch_symbols_analyzed.some((s) => s.includes("t06_helper")));
  await page.getByTestId("test-impact-plan").waitFor();
  await page.getByRole("button", { name: "Copy pytest command", exact: true }).click();
  assert.equal(await page.evaluate(() => navigator.clipboard.readText()), patched.recommended_pytest_command);
  mark("T-07 visible static test candidates, safe full-suite fallback and copyable pytest command");
  await page.locator(".comparison-strip").waitFor();
  const stripBox = await page.locator(".comparison-strip").boundingBox();
  assert.ok(stripBox && stripBox.y + stripBox.height < 1050);
  await shot("t06-ast-patch-comparison");
  mark(
    "Real commit scope, AST snippet editor, clone cleanup and above-fold audit comparison",
  );
  const diffTarget = (await page.locator("fieldset label").first().innerText()).trim();
  const realDiff = JSON.parse(execFileSync(
    process.env.BACKEND_PYTHON || "python3",
    ["-c", "import json,difflib,sys;from app.db.client import db_manager;g=db_manager.get_graph('repo_falkordb_py');p,s=g.ro_query('MATCH (f:File {path:$path}) RETURN f.path,f.source_text',{'path':sys.argv[1]}).result_set[0];d=''.join(difflib.unified_diff(s.splitlines(True),('# T-07 static patch audit\\n'+s).splitlines(True),fromfile='a/'+p,tofile='b/'+p));print(json.dumps({'path':p,'diff':d}))", diffTarget],
    { cwd: path.resolve("../backend"), encoding: "utf8" }
  ));
  await page.locator("#pr").selectOption("");
  for (const checkbox of await page.locator("fieldset input[type=checkbox]").all()) await checkbox.uncheck();
  await page.getByRole("checkbox", { name: realDiff.path, exact: true }).check();
  await page.locator("#python-patch").fill(realDiff.diff);
  const diffAudit = await action("Run GRAPH.COPY audit", "/track1/sandbox-audit");
  assert.equal(diffAudit.sandbox_cleaned_up, true);
  assert.ok(diffAudit.subgraph.nodes.some((n) => n.metadata.patch_semantics === "VALIDATED_UNIFIED_DIFF_ADDITIVE_OVERLAY"));
  mark("T-07 real unified diff matches captured source and is AST-parsed only in disposable clone");
  await page.getByLabel("Apply Python snippet overlay").uncheck();
  await page.locator(".patch-editor summary").click();
  await page.locator("#pr").selectOption("");
  await page.locator("fieldset input[type=checkbox]").first().check();
  // Restore the original audit for existing full-payload count assertions.
  await action("Run GRAPH.COPY audit", "/track1/sandbox-audit");
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
  assert.ok((await page.locator(".react-flow__node").count()) > 0);
  assert.equal(await page.locator(".canvas-empty").count(), 0);
  mark(
    "Track navigation retains clearly labeled real evidence without a blank canvas",
  );
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
  assert.equal(warm.model_calls, 0);
  assert.equal(cold.context_measurement_status, "MEASURED_SOURCE_CHARS_DIV_4");
  assert.ok(cold.raw_files_context_bytes > 0);
  assert.equal(warm.raw_files_context_tokens, cold.raw_files_context_tokens);
  assert.equal(warm.compiled_slice_context_tokens, Math.floor(Array.from(warm.compiled_context_slice_preview).length / 4));
  await page.getByTestId("context-compression").waitFor();
  await page.getByText("Actual compiled MCP context slice", { exact: true }).click();
  await page.getByRole("button", { name: "Copy context slice", exact: true }).click();
  assert.equal(await page.evaluate(() => navigator.clipboard.readText()), warm.compiled_context_slice_preview);
  await page.getByText("Actual compiled MCP context slice", { exact: true }).click();
  mark("T-07 measured candidate-source bytes and persisted compiled MCP context slice; zero models");
  measurements.push({
    tenant: "repo_falkordb_py",
    cold_duration_ms: cold.duration_ms,
    warm_duration_ms: warm.duration_ms,
    latency_speedup_factor: warm.latency_speedup_factor,
    cold_actions: cold.total_steps_executed,
    warm_actions: warm.total_steps_executed,
  });
  await page.getByText("40% fewer actions", { exact: true }).waitFor();
  assert.equal(
    await page.locator(".historical-evidence.status-DEAD_END").count(),
    2,
  );
  assert.ok(
    await page
      .locator(".historical-evidence")
      .first()
      .evaluate((e) => getComputedStyle(e).opacity === "0.38"),
  );
  assert.match(
    await page.locator(".comparison-strip").textContent(),
    /shortestPath Replay: 3 verified actions/,
  );
  await shot("04-memory-replay");
  mark(
    "Replay keeps two dimmed historical cold branches, actual cyan path and measured comparison",
  );
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
  assert.ok(original.repository_constraints.length);
  assert.ok(original.repository_constraints.every((r) => r.source_type === "REPO_EXTRACTED_RULE" && r.source_line > 0));
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
  assert.match(
    await page.locator(".comparison-strip").textContent(),
    /Without Graph · Oldest-Doc: Returns SUPERSEDED rule/,
  );
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
  const externalTenants = (process.env.REAL_WORLD_TENANTS || "")
    .split(",")
    .filter(Boolean);
  const catalog = externalTenants.length
    ? await (await fetch(API + "/tenants")).json()
    : [];
  await page.setViewportSize({ width: 1560, height: 1050 });
  for (const tenant of externalTenants) {
    const entry = catalog.find((t) => t.tenant_graph === tenant);
    assert.ok(
      entry && entry.preset_files.length,
      `Registered policy-backed tenant ${tenant}`,
    );
    await page.locator("#tenant").selectOption(tenant);
    await page.waitForFunction(
      () => !document.querySelector("#tenant").disabled,
    );
    await page.getByRole("button", { name: /TRACK 03/ }).click();
    await page.locator("#policy-file").selectOption(entry.preset_files[0]);
    const policy = await action("Read current policy", "/track3/ask-brain");
    assert.ok(
      policy.active_decisions.length && policy.superseded_decisions.length,
    );
    assert.ok(policy.repository_constraints.length);
    await page.getByTestId("repository-constraints").waitFor();
    await page.getByRole("button", { name: /TRACK 01/ }).click();
    const boxes = page.locator('fieldset input[type="checkbox"]');
    for (const box of await boxes.all()) await box.uncheck();
    await boxes.first().check();
    const audit = await action("Run GRAPH.COPY audit", "/track1/sandbox-audit");
    assert.equal(audit.sandbox_cleaned_up, true);
    assert.ok(audit.recommended_reviewers.length);
    await page.getByRole("button", { name: /TRACK 02/ }).click();
    await page
      .locator("#scenario")
      .fill(`Review policy ${entry.preset_files[0]} ${Date.now()}`);
    const cold = await action("Run #1 · Cold triage", "/track2/investigate");
    const warm = await action(
      "Run #2 · Compiled replay",
      "/track2/investigate",
    );
    assert.equal(cold.total_steps_executed, 5);
    assert.equal(warm.total_steps_executed, 3);
    assert.equal(
      warm.subgraph.nodes.filter((n) => n.status === "DEAD_END").length,
      0,
    );
    measurements.push({
      tenant,
      clone_ms: audit.sandbox_clone_time_ms,
      selected_test_files: audit.impacted_test_files.length,
      total_test_files: audit.total_repo_test_files,
      static_candidate_reduction_pct: audit.test_suite_reduction_pct,
      raw_context_chars: cold.raw_files_context_chars,
      raw_context_bytes: cold.raw_files_context_bytes,
      slice_context_bytes: cold.compiled_slice_context_bytes,
      raw_token_equivalents: cold.raw_files_context_tokens,
      slice_token_equivalents: cold.compiled_slice_context_tokens,
      context_token_reduction_pct: cold.context_token_reduction_pct,
      cold_ms: cold.duration_ms,
      warm_ms: warm.duration_ms,
    });
    await noOverflow();
    await shot(`external-${tenant}`);
    mark(
      `External ${tenant}: tenant switch, current/history policy, clone cleanup/reviewers, 5-to-3 replay`,
    );
  }
  // T-08: compile live notes, navigate a real wikilink, copy bounded recovery
  // context and download a real ZIP. No graph fixture or response stub.
  await page.getByRole("button", { name: "Obsidian Wiki & /compact Shield", exact: true }).click();
  const wiki=page.getByRole("dialog",{name:"Obsidian Second Brain"});
  await wiki.waitFor();
  await wiki.getByRole("button",{name:"index.md",exact:true}).click();
  await wiki.locator(".wiki-link").first().click();
  assert.match(await wiki.locator(".wiki-note").textContent(), /tenant:/);
  await wiki.getByRole("button",{name:"log.md",exact:true}).click();
  assert.match(await wiki.locator(".wiki-note").textContent(),/Investigation and override ledger/);
  await wiki.getByRole("button",{name:"PreCompact ResumeSnapshot",exact:true}).click();
  const resume=await wiki.locator(".wiki-note").textContent();
  assert.ok(Buffer.byteLength(resume,"utf8")<2048);
  assert.ok(!resume.includes("inspect_candidate"));
  const recoveryTenant=await page.locator("#tenant").inputValue();
  const recoveryCatalog=await(await fetch(API+"/tenants")).json();
  const recoveryTarget=recoveryCatalog.find(t=>t.tenant_graph===recoveryTenant).preset_files[0];
  assert.ok(resume.includes(recoveryTarget),"Recovery drawer must use the actual investigation target, not the default hub");
  assert.match(resume,/ACTIVE /);
  assert.match(resume,/Current playbook /);
  await wiki.getByRole("button",{name:"Copy note",exact:true}).click();
  const rawRecovery=await apiPost("/brain/lint-and-compact",{tenant_graph:recoveryTenant,file_path:recoveryTarget});
  assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),rawRecovery.precompact_resume_markdown);
  await wiki.getByRole("button",{name:"/brain-lint",exact:true}).click();
  assert.match(await wiki.locator(".wiki-note").textContent(),/orphan_sandboxes_count/);
  const health=JSON.parse(await wiki.locator(".wiki-note").textContent());
  assert.equal(health.orphan_sandboxes_count,0);
  assert.match(health.precompact_resume_markdown,/LESSON:/);
  mark("T-08 brain lint and compact use live graph counts and LESSON recovery");
  const downloadPromise=page.waitForEvent("download");
  await wiki.getByRole("button",{name:"Download Obsidian Vault (.zip)",exact:true}).click();
  const download=await downloadPromise;
  await download.saveAs(path.join(out,"obsidian-vault.zip"));
  assert.match(download.suggestedFilename(),/obsidian-vault.zip$/);
  await wiki.getByRole("button",{name:"Close wiki",exact:true}).click();
  mark("T-08 live Obsidian note wikilinks, source ledger, bounded copied ResumeSnapshot and ZIP export");
  await page.getByRole("button",{name:"MCP config",exact:true}).click();
  const mcp=page.getByRole("dialog");
  await mcp.getByRole("tab",{name:"Cursor",exact:true}).click();
  await mcp.getByRole("button",{name:"Copy SKILL.md path",exact:true}).click();
  assert.equal(await page.evaluate(()=>navigator.clipboard.readText()),"skills/chronos-second-brain/SKILL.md");
  await page.keyboard.press("Escape");
  mark("T-08 MCP platform guidance and actual portable-skill path clipboard");
  await page.setViewportSize({width:390,height:844});
  await page.getByRole("button",{name:"Obsidian Wiki & /compact Shield",exact:true}).click();
  await page.getByRole("dialog",{name:"Obsidian Second Brain"}).waitFor();
  await noOverflow();await shot("t08-mobile-wiki");
  await page.getByRole("button",{name:"Close wiki",exact:true}).click();
  await page.setViewportSize({width:1560,height:1050});
  await noOverflow();await shot("t08-desktop-hud");
  mark("T-08 v1.4 HUD and 390px wiki modal without page overflow");
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
