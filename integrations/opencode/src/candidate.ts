/** Observations of a local Git worktree, not an attestation or a sandbox. */
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { readFile, lstat } from "node:fs/promises";
import { createHash } from "node:crypto";
import { join } from "node:path";
const exec = promisify(execFile);
export const sha = (b: Uint8Array | string) =>
  createHash("sha256").update(b).digest("hex");
export const canonical = (v: any): string =>
  JSON.stringify(
    v && typeof v === "object"
      ? Array.isArray(v)
        ? v.map((x) => JSON.parse(canonical(x)))
        : Object.fromEntries(
            Object.keys(v)
              .sort()
              .map((k) => [k, JSON.parse(canonical(v[k]))]),
          )
      : v,
  );
export type CandidateEntry = {
  path: string;
  operation: "ADD" | "MODIFY" | "DELETE";
  base_sha256: string | null;
  result_sha256: string | null;
};
export type CandidateManifest = {
  schema_version: 1;
  base_revision: string;
  entries: CandidateEntry[];
};
// Only untracked, installer-owned metadata is excluded. Tracked edits never are.
const metadata = (p: string) =>
  p.startsWith(".chronosgraph-local/") ||
  p.startsWith(".opencode/node_modules/") ||
  [
    ".opencode/plugins/chronosgraph.ts",
    ".opencode/chronosgraph/bridge.ts",
    ".opencode/chronosgraph/runtime.ts",
    ".opencode/chronosgraph/candidate.ts",
    ".opencode/chronosgraph/usage.ts",
    ".opencode/package.json",
    ".opencode/bun.lock",
    ".opencode/bun.lockb",
    ".opencode/package-lock.json",
    ".opencode/.gitignore",
  ].includes(p);
async function inventory(directory: string, expected: string) {
  const git = async (...args: string[]) =>
    (await exec("git", ["-C", directory, ...args], { maxBuffer: 2_000_000 }))
      .stdout;
  if ((await git("rev-parse", "HEAD")).trim() !== expected)
    throw Error("Worktree HEAD differs from selected snapshot");
  const changed = (
    await git(
      "diff",
      "--no-ext-diff",
      "--no-textconv",
      "--name-only",
      "--no-renames",
      "-z",
      "HEAD",
      "--",
    )
  )
    .split("\0")
    .filter(Boolean);
  const untracked = (
    await git("ls-files", "--others", "--exclude-standard", "-z")
  )
    .split("\0")
    .filter(Boolean)
    .filter((p) => !metadata(p));
  if (
    /mode change|create mode (?!100644)|delete mode (?!100644)/.test(
      await git("diff", "--summary", "HEAD", "--"),
    )
  )
    throw Error(
      "Mode changes, symlinks and submodules are unsupported candidates",
    );
  const paths = [...new Set([...changed, ...untracked])].sort();
  if (paths.length > 20) throw Error("Candidate exceeds 20 changed paths");
  return { git, paths };
}
export async function captureCandidate(
  directory: string,
  expected: string,
  afterRead?: () => Promise<void>,
) {
  const capture = async () => {
    const { git, paths } = await inventory(directory, expected),
      files: Record<string, string | null> = {},
      entries: CandidateEntry[] = [];
    for (const path of paths) {
      if (
        path.startsWith("/") ||
        path.split("/").some((p) => p === ".." || !p) ||
        /[\x00-\x1f\\]/.test(path)
      )
        throw Error("Unsafe candidate path");
      let base: Buffer | null = null;
      try {
        base = (
          await exec("git", ["-C", directory, "show", `HEAD:${path}`], {
            encoding: "buffer",
            maxBuffer: 128001,
          })
        ).stdout;
      } catch (e) {
        // Only a genuinely absent base is an addition; other git failures must fail closed.
        const tracked =
          (await git("ls-tree", "-z", "HEAD", "--", path)).length > 0;
        if (tracked) throw e;
      }
      let bytes: Buffer | null = null;
      try {
        const stat = await lstat(join(directory, path));
        if (!stat.isFile() || stat.isSymbolicLink() || stat.size > 128000 || (base === null && (stat.mode & 0o111) !== 0))
          throw Error("Unsupported nonregular, executable addition or large candidate: " + path);
        bytes = await readFile(join(directory, path));
      } catch (e) {
        if ((e as NodeJS.ErrnoException).code !== "ENOENT") throw e;
      }
      if (bytes?.includes(0) || base?.includes(0))
        throw Error("Binary candidates unsupported: " + path);
      files[path] =
        bytes === null
          ? null
          : new TextDecoder("utf-8", { fatal: true }).decode(bytes);
      entries.push({
        path,
        operation: bytes === null ? "DELETE" : base === null ? "ADD" : "MODIFY",
        base_sha256: base === null ? null : sha(base),
        result_sha256: bytes === null ? null : sha(bytes),
      });
    }
    if (
      Object.values(files).reduce((n, v) => n + Buffer.byteLength(v ?? ""), 0) >
      128000
    )
      throw Error("Candidate exceeds 128000 bytes");
    return {
      manifest: {
        schema_version: 1 as const,
        base_revision: expected,
        entries,
      },
      files,
    };
  };
  const first = await capture();
  await afterRead?.();
  const second = await capture();
  if (canonical(first) !== canonical(second))
    throw Error(
      "Concurrent edit during candidate capture; retry after writers stop",
    );
  return { ...second, digest: sha(canonical(second.manifest)) };
}
export async function requireCleanStart(directory: string, expected: string) {
  const c = await captureCandidate(directory, expected);
  if (c.manifest.entries.length)
    throw Error(
      "DIRTY_START: preserve edits and select an isolated clean worktree; base-only context cannot cover this overlay",
    );
  return c;
}
export function compareCandidate(
  actual: Awaited<ReturnType<typeof captureCandidate>>,
  submitted: unknown,
) {
  if (canonical(actual.files) !== canonical(submitted))
    throw Error(
      "CANDIDATE_MISMATCH: submit every current edit/addition/deletion with exact worktree contents; no omitted or hypothetical files",
    );
}
