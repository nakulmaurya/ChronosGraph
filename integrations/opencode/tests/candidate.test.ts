/** Real temporary Git worktrees; concurrent edit is explicitly injected. */
import { test } from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, writeFile, unlink, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { execFileSync } from "node:child_process";
import {
  captureCandidate,
  requireCleanStart,
  compareCandidate,
  sha,
  canonical,
} from "../src/candidate.ts";
async function repo() {
  const root = await mkdtemp(join(tmpdir(), "chronos-candidate-"));
  const git = (...a: string[]) =>
    execFileSync("git", ["-C", root, ...a], { encoding: "utf8" }).trim();
  git("init", "-q");
  await writeFile(join(root, "one.py"), "value=1\n");
  await writeFile(join(root, "deleted.py"), "value=0\n");
  git("add", ".");
  git(
    "-c",
    "user.name=Fixture",
    "-c",
    "user.email=fixture@example.invalid",
    "commit",
    "-qm",
    "owned",
  );
  return { root, git, revision: git("rev-parse", "HEAD") };
}
test("C: clean start refuses dirty state without losing user files; observed add/edit/delete is complete", async () => {
  const r = await repo();
  try {
    await requireCleanStart(r.root, r.revision);
    await writeFile(join(r.root, "one.py"), "value=2 # café\n");
    await writeFile(join(r.root, "new.py"), "value=3\n");
    await unlink(join(r.root, "deleted.py"));
    await assert.rejects(
      () => requireCleanStart(r.root, r.revision),
      /DIRTY_START/,
    );
    const c = await captureCandidate(r.root, r.revision);
    assert.deepEqual(
      c.manifest.entries.map((e) => [e.path, e.operation]),
      [
        ["deleted.py", "DELETE"],
        ["new.py", "ADD"],
        ["one.py", "MODIFY"],
      ],
    );
    assert.equal(c.digest, sha(canonical(c.manifest)));
    compareCandidate(c, c.files);
    await assert.throws(
      () => compareCandidate(c, { "one.py": c.files["one.py"] }),
      /MISMATCH/,
    );
    await assert.throws(
      () => compareCandidate(c, { ...c.files, "new.py": "different" }),
      /MISMATCH/,
    );
  } finally {
    await rm(r.root, { recursive: true, force: true });
  }
});
test("C: concurrent edits, wrong HEAD and binary candidates fail closed", async () => {
  const r = await repo();
  try {
    await writeFile(join(r.root, "one.py"), "value=2\n");
    await assert.rejects(
      () =>
        captureCandidate(r.root, r.revision, () =>
          writeFile(join(r.root, "one.py"), "value=3\n"),
        ),
      /Concurrent/,
    );
    await assert.rejects(
      () => captureCandidate(r.root, "f".repeat(40)),
      /HEAD/,
    );
    await writeFile(join(r.root, "binary.py"), Buffer.from([0, 255]));
    await assert.rejects(() => captureCandidate(r.root, r.revision), /Binary/);
  } finally {
    await rm(r.root, { recursive: true, force: true });
  }
});
