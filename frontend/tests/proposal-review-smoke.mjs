/** Targeted failure injection around real native proposals; no mocked approval success. */
import { chromium } from "@playwright/test";
import assert from "node:assert/strict";
import { readFile, mkdir, writeFile } from "node:fs/promises";
const fixture = JSON.parse(await readFile(process.env.HERO_FIXTURE, "utf8"));
const out = process.env.EVIDENCE_DIR;
await mkdir(out, { recursive: true });
const browser = await chromium.launch({
  executablePath: process.env.CHROMIUM_PATH || "/usr/bin/chromium",
  args: ["--no-sandbox"],
});
const checks = [],
  errors = [];
async function check(name, fn) {
  await fn();
  checks.push(name);
  console.log("PASS " + name);
}
try {
  for (const width of [1560, 390]) {
    const ctx = await browser.newContext({
      viewport: { width, height: 1000 },
      reducedMotion: "reduce",
    });
    const page = await ctx.newPage();
    page.setDefaultTimeout(20000);
    page.on("pageerror", (e) => errors.push(e.message));
    await page.goto("http://127.0.0.1:3003");
    await page
      .getByRole("combobox", { name: "Repository", exact: true })
      .selectOption(fixture.tenant);
    await page
      .getByRole("button", { name: "Changes", exact: true })
      .last()
      .click();
    const region = page.getByRole("region", {
      name: "Pending and recent change proposals",
    });
    const select = region.getByRole("combobox");
    await select.selectOption(fixture.fixed);
    const reason = region.getByLabel("Decision reason");
    await reason.fill(
      "Keep this review draft while checking for new proposals",
    );
    await check(
      `Refresh preserves selected proposal and review reason (${width})`,
      async () => {
        await region
          .getByRole("button", { name: "Approve exact proposal", exact: true })
          .waitFor();
        const response = page.waitForResponse((r) =>
          r.url().includes("/proposals?"),
        );
        await region
          .getByRole("button", { name: "Refresh proposals", exact: true })
          .click();
        await response;
        await page.waitForTimeout(300);
        assert.equal(await select.inputValue(), fixture.fixed);
        assert.equal(
          await reason.inputValue(),
          "Keep this review draft while checking for new proposals",
        );
      },
    );
    await check(
      `Readable proposal summary and ownership evidence (${width})`,
      async () => {
        await region.getByLabel("Proposal summary", { exact: true }).waitFor();
        await region
          .locator("summary")
          .filter({ hasText: "Applicable rules & declared owners" })
          .click();
        await region.getByText("@platform-team", { exact: true }).waitFor();
        assert.equal(
          await region
            .getByText("Raw rule and ownership evidence", { exact: true })
            .count(),
          1,
        );
        await region
          .locator("summary")
          .filter({ hasText: "Applicable rules & declared owners" })
          .click();
      },
    );
    await check(
      `Comparison failure prevents approval and refresh recovers (${width})`,
      async () => {
        await select.selectOption(fixture.broken);
        const sourceRoute = "**/api/v1/repository/file-source?*";
        await page.route(sourceRoute, (route) =>
          route.fulfill({
            status: 503,
            contentType: "application/json",
            body: JSON.stringify({ detail: "Injected captured-source outage" }),
          }),
        );
        await select.selectOption(fixture.fixed);
        await reason.fill(
          "Review cannot proceed without the captured comparison",
        );
        await region
          .getByText("Cannot load the captured-source comparison:", {
            exact: false,
          })
          .waitFor();
        assert.equal(
          await region
            .getByRole("button", {
              name: "Approve exact proposal",
              exact: true,
            })
            .isDisabled(),
          true,
        );
        await page.unroute(sourceRoute);
        await region
          .getByRole("button", { name: "Refresh proposals", exact: true })
          .click();
        await region
          .getByRole("button", { name: "Approve exact proposal", exact: true })
          .waitFor();
        await page.waitForFunction(() => {
          const b = [...document.querySelectorAll("button")].find(
            (b) => b.textContent === "Approve exact proposal",
          );
          return b && !b.disabled;
        });
        assert.equal(await select.inputValue(), fixture.fixed);
        assert.equal(
          await reason.inputValue(),
          "Review cannot proceed without the captured comparison",
        );
      },
    );
    await check(
      `List outage retains last data without claiming an empty state (${width})`,
      async () => {
        const listRoute = "**/api/v1/proposals?*";
        await page.route(listRoute, (route) =>
          route.fulfill({
            status: 503,
            contentType: "application/json",
            body: JSON.stringify({ detail: "Injected proposal-list outage" }),
          }),
        );
        await region
          .getByRole("button", { name: "Refresh proposals", exact: true })
          .click();
        await region
          .getByText(
            "Any displayed proposals are the last successfully loaded state.",
            { exact: false },
          )
          .waitFor();
        assert.equal(await select.inputValue(), fixture.fixed);
        assert.equal(
          await region.getByText("No proposals yet.", { exact: false }).count(),
          0,
        );
        assert.equal(
          await region
            .getByRole("button", {
              name: "Approve exact proposal",
              exact: true,
            })
            .isDisabled(),
          true,
        );
        await page.unroute(listRoute);
        await region
          .getByRole("button", { name: "Refresh proposals", exact: true })
          .click();
        await page.waitForFunction(
          () =>
            ![...document.querySelectorAll('[role="alert"]')].some((e) =>
              e.textContent.includes("Automatic refresh stopped"),
            ),
        );
        assert.equal(await select.inputValue(), fixture.fixed);
      },
    );
    await page.screenshot({
      path: out + `/proposal-review-${width}.png`,
      fullPage: true,
    });
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth > innerWidth + 1,
      ),
      false,
    );
    await ctx.close();
  }
  assert.deepEqual(errors, []);
  await writeFile(
    out + "/checks.json",
    JSON.stringify(
      {
        checks,
        errors,
        scope:
          "Real native proposals; explicitly injected list and source read failures; no mocked mutation success",
      },
      null,
      2,
    ),
  );
} finally {
  await browser.close();
}
