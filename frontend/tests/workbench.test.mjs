import test from "node:test";
import assert from "node:assert/strict";
import { queryString, formatBytes, finalStateInput } from "../src/lib/workbench.ts";
test("context query values remain encoded, not interpreted as extra parameters", () => {
  const parsed = new URLSearchParams(queryString({ query: "helper & tenant_graph=bad", tenant_graph: "repo_test" }));
  assert.equal(parsed.get("tenant_graph"), "repo_test");
  assert.equal(parsed.get("query"), "helper & tenant_graph=bad");
});
test("byte labels use KiB and preserve sub-kibibyte measurements", () => {
  assert.equal(formatBytes(1024), "1.0 KiB");
  assert.equal(formatBytes(512), "512 B");
});
test("final source map accepts additions, empty files, deletes; rejects malformed shapes", () => {
  assert.deepEqual(finalStateInput('{"src/new.py":"","src/old.py":null}'), { "src/new.py": "", "src/old.py": null });
  for (const invalid of ["[]", "null", "{}", '{"module.py":123}', "{invalid}"])
    assert.throws(() => finalStateInput(invalid));
});
