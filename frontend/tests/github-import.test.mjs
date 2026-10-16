import test from "node:test";
import assert from "node:assert/strict";
import { githubIntakeCommands } from "../src/lib/github-import.ts";
test("public intake guide prepares inspect before confirmed import; no browser fetching", () => {
  const result = githubIntakeCommands("https://github.com/pallets/click", "feature/context", "repo_new", "");
  assert.match(result.inspect, /inspect --url 'https:\/\/github.com\/pallets\/click' --branch 'feature\/context'/);
  assert.equal(result.importCommand, null);
  const confirmed = githubIntakeCommands("https://github.com/pallets/click.git", "main", "repo_new", "1".repeat(40));
  assert.match(confirmed.importCommand, /^CHRONOSGRAPH_ENABLE_PUBLIC_GITHUB_IMPORT=1 /);
  assert.match(confirmed.importCommand, /--tenant 'repo_new' --expected-head '111/);
  assert.doesNotMatch(confirmed.importCommand, /click.git/);
});
test("command builder rejects shell injection, private URL forms and revision expressions", () => {
  for (const url of ["https://github.com/a/b;touch-x", "https://github.com/a/b/tree/main", "https://token@github.com/a/b", "https://github.com/a/b?token=x", "https://evil/a/b"])
    assert.throws(() => githubIntakeCommands(url, "main", "repo_new", ""));
  for (const branch of ["main';touch /tmp/x;#", "../main", "a//b", "a.lock", "a/.b", "main~1"])
    assert.throws(() => githubIntakeCommands("https://github.com/a/b", branch, "repo_new", ""));
  assert.equal(githubIntakeCommands("https://github.com/a/b", "main", "repo_new';oops", "1".repeat(40)).importCommand, null);
});
