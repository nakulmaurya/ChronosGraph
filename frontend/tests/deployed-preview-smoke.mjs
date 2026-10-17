/** Actual deployed preview. Public import is opt-in and creates a separate saved version. */
import { chromium } from "@playwright/test";
import assert from "node:assert/strict";
import { mkdir, writeFile } from "node:fs/promises";
const front = process.env.FRONTEND_URL || "http://127.0.0.1:3004";
const out = process.env.EVIDENCE_DIR;
if (!out) throw new Error("Choose an evidence directory outside the checkout");
await mkdir(out, { recursive: true });
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || "/usr/bin/chromium",
  args: ["--no-sandbox"],
});
const checks = [],
  errors = [];
let imported = null;
async function check(name, fn) {
  await fn();
  checks.push(name);
  console.log("PASS " + name);
}
try {
  for (const width of [1560, 390]) {
    const context = await browser.newContext({
      viewport: { width, height: 1000 },
      reducedMotion: "reduce",
    });
    const page = await context.newPage();
    page.setDefaultTimeout(30000);
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto(front);
    const chooser = page.getByRole("combobox", {
      name: "Repository",
      exact: true,
    });
    await chooser.selectOption("repo_falkordb_py");
    await check(
      `Deployed saved repo graph and keyboard table (${width})`,
      async () => {
        const tableButton = page.getByRole("button", {
          name: "Table",
          exact: true,
        });
        await tableButton.focus();
        await page.keyboard.press("Enter");
        const table = page.getByRole("table");
        await table.waitFor();
        const folder = table.getByRole("button", {
          name: "falkordb/",
          exact: true,
        });
        await folder.focus();
        await page.keyboard.press("Enter");
        const file = page
          .getByRole("table")
          .getByRole("button", { name: "falkordb/graph.py", exact: true });
        await file.focus();
        await page.keyboard.press("Enter");
        await page
          .locator(".cc-inspector-heading h2")
          .filter({ hasText: "graph.py" })
          .waitFor();
        await page
          .getByRole("button", { name: "Functions", exact: true })
          .click();
        await page.getByRole("button", { name: "Graph", exact: true }).click();
        await page.locator(".react-flow__node").first().waitFor();
      },
    );
    await check(
      `Deployed agent handoff exposes new lifecycle tools (${width})`,
      async () => {
        await page
          .getByRole("button", { name: "Connect agent", exact: true })
          .click();
        const dialog = page.getByRole("dialog");
        await dialog.waitFor();
        for (const name of [
          "propose_change_for_approval",
          "check_proposal_decision",
          "report_proposal_execution",
        ])
          await dialog.getByText(name, { exact: true }).waitFor();
        await page.keyboard.press("Escape");
        await dialog.waitFor({ state: "hidden", timeout: 240000 });
      },
    );
    await check(
      `Deployed changes, ownership and memory views (${width})`,
      async () => {
        await page
          .getByRole("button", { name: "Changes", exact: true })
          .last()
          .click();
        await page
          .getByRole("region", { name: "Pending and recent change proposals" })
          .waitFor();
        await page
          .getByRole("button", { name: "Ownership", exact: true })
          .last()
          .click();
        await page
          .getByRole("button", {
            name: "Preview [[Wikilink]] note",
            exact: true,
          })
          .waitFor();
        await page
          .getByRole("button", { name: "Agent activity", exact: true })
          .last()
          .click();
        await page
          .getByRole("button", { name: "Prepare recovery note", exact: true })
          .waitFor();
      },
    );
    if (width === 1560 && process.env.DEPLOY_SMOKE_PUBLIC_IMPORT === "1") {
      await check(
        "Real one-click public GitHub import and saved-map opening",
        async () => {
          await page
            .getByRole("button", { name: "Import repository", exact: true })
            .first()
            .click();
          const dialog = page.getByRole("dialog");
          if (process.env.DEPLOY_SMOKE_RECEIPT) {
            // Resume the already accepted durable job; never silently duplicate it.
            const receipt = process.env.DEPLOY_SMOKE_RECEIPT;
            const response = await page.request.get(
              `http://127.0.0.1:8004/api/v1/imports/${receipt}`,
            );
            assert.equal(response.status(), 200);
            imported = await response.json();
            assert.equal(imported.status, "COMPLETE");
            await dialog
              .getByRole("button", { name: "Close repository import", exact: true })
              .click();
            await page.evaluate(
              (id) => localStorage.setItem("chronosgraph-import-job", id),
              receipt,
            );
            await page
              .getByRole("button", { name: "Import repository", exact: true })
              .first()
              .click();
          } else {
            await dialog
              .getByLabel("GitHub repository", { exact: true })
              .fill("https://github.com/pallets/click");
            const started = page.waitForResponse(
              (r) =>
                r.url().endsWith("/api/v1/imports") &&
                r.request().method() === "POST",
            );
            await dialog
              .getByRole("button", { name: "Import repository", exact: true })
              .click();
            const response = await started;
            assert.equal(response.status(), 202);
            imported = await response.json();
            // Preserve an accepted receipt even if a later UI assertion fails.
            await writeFile(
              out + "/accepted-import.json",
              JSON.stringify(imported, null, 2),
            );
          }
          // Completion deliberately opens the saved map automatically.
          await dialog.waitFor({ state: "hidden", timeout: 240000 });
          await page.locator(".cc-overview h1").waitFor();
          assert.equal(await chooser.inputValue(), imported.tenant_graph);
          await page.locator(".cc-tree-file").first().waitFor();
          assert.match(
            await chooser.locator("option:checked").innerText(),
            /pallets\/click/,
          );
        },
      );
    }
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth + 1,
      ),
      false,
    );
    await page.screenshot({
      path: out + `/deployed-${width}.png`,
      fullPage: true,
    });
    await context.close();
  }
  assert.deepEqual(errors, []);
  await writeFile(
    out + "/checks.json",
    JSON.stringify(
      {
        checks,
        errors,
        imported,
        scope:
          "Real deployed loopback UI and native API, no route mocks; opt-in public archive import does not execute repository code",
      },
      null,
      2,
    ),
  );
} finally {
  await browser.close();
}
