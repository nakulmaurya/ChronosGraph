import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import {
  safeRelative,
  validateBinding,
  workspaceIdentity,
} from "../src/bridge.ts";

test("project bridge rejects remote origins and wrong snapshot identity", () => {
  const good = {
    api_url: "http://127.0.0.1:8011",
    tenant_graph: "repo_test",
    expected_revision: "a".repeat(40),
    task_id: "task_" + "b".repeat(32),
    plan_id: "plan_" + "c".repeat(32),
    pack_id: "pack_" + "d".repeat(32),
  };
  assert.deepEqual(validateBinding(good), good);
  for (const api_url of [
    "https://127.0.0.1:1",
    "http://example.com",
    "http://localhost:1/private",
    "http://user:pass@localhost:1",
  ])
    assert.throws(() => validateBinding({ ...good, api_url }));
});
test("metadata paths cannot escape selected worktree", () => {
  assert.equal(safeRelative("/owned/repo", "/owned/repo/src/a.py"), "src/a.py");
  for (const p of [
    "/etc/passwd",
    "../secret",
    "a/../../secret",
    "a\\..\\secret",
  ])
    assert.equal(safeRelative("/owned/repo", p), null);
});
test("actual git identity changes on tracked, staged and untracked edits", async () => {
  const root = await mkdtemp(join(tmpdir(), "chronos-plugin-"));
  const git = (...args: string[]) =>
    execFileSync("git", ["-C", root, ...args], { encoding: "utf8" }).trim();
  git("init", "-q");
  await writeFile(join(root, "a.py"), "def a(): return 1\n");
  git("add", ".");
  git(
    "-c",
    "user.name=Fixture",
    "-c",
    "user.email=fixture@example.invalid",
    "commit",
    "-qm",
    "fixture",
  );
  const revision = git("rev-parse", "HEAD");
  const initial = await workspaceIdentity(root, revision);
  await writeFile(join(root, "a.py"), "def a(): return 2\n");
  const changed = await workspaceIdentity(root, revision);
  assert.notEqual(initial.overlay_digest, changed.overlay_digest);
  git("add", "a.py");
  const staged = await workspaceIdentity(root, revision);
  assert.equal(staged.overlay_digest, changed.overlay_digest);
  await writeFile(join(root, "new.py"), "x=1\n");
  const untracked = await workspaceIdentity(root, revision);
  assert.notEqual(untracked.overlay_digest, changed.overlay_digest);
  await assert.rejects(workspaceIdentity(root, "e".repeat(40)));
});
