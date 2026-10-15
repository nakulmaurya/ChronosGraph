import test from "node:test";
import assert from "node:assert/strict";
import {
  safeUrl,
  timestamp,
  ms,
  text,
  request,
  ApiError,
} from "../src/lib/api.ts";
import { focusGraph, placeNodes, validEdges } from "../src/lib/graph.ts";
test("unsafe evidence links are never actionable", () => {
  for (const s of [
    "javascript:alert(1)",
    "data:text/html,hello",
    "file:///etc/passwd",
    "chronosgraph://local-policy/a",
    null,
  ])
    assert.equal(safeUrl(s), undefined);
  assert.equal(safeUrl("https://github.com/a"), "https://github.com/a");
});
test("timestamps distinguish open intervals from real epoch seconds", () => {
  assert.equal(timestamp(0), "Open / not set");
  assert.match(timestamp(1792041722), /2026-10-15.*UTC/);
  assert.equal(timestamp("fake"), "Open / not set");
});
test("measured timing and metadata formatting", () => {
  assert.equal(ms(1.579), "1.58 ms");
  assert.equal(ms(NaN), "Not measured");
  assert.equal(text(null), "Not provided");
  assert.equal(text({ status: "ACTIVE" }), '{"status":"ACTIVE"}');
});
test("graph layout preserves evidence identity and filters dangling edges", () => {
  const nodes = ["a", "b", "c"].map((id, i) => ({
    id,
    label: i ? "File" : "Decision",
    status: "DEFAULT",
    title: id,
    metadata: {},
  }));
  const graph = {
    nodes,
    edges: [
      { id: "ok", source: "a", target: "b" },
      { id: "bad", source: "b", target: "absent" },
    ],
  };
  const positions = placeNodes(graph);
  assert.equal(positions.size, 3);
  assert.notDeepEqual(positions.get("b"), positions.get("c"));
  assert.equal(validEdges(graph).length, 1);
  assert.deepEqual(graph.nodes, nodes);
});
test("API preserves HTTP scope conflict details", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () =>
    new Response(JSON.stringify({ detail: "Scope mismatch" }), { status: 409 });
  try {
    await assert.rejects(
      () => request("/test", new AbortController().signal, {}),
      (e) =>
        e instanceof ApiError &&
        e.status === 409 &&
        e.message.includes("Scope mismatch"),
    );
  } finally {
    globalThis.fetch = original;
  }
});
test("API explains network failure without inventing data", async () => {
  const original = globalThis.fetch;
  globalThis.fetch = async () => {
    throw new TypeError("fetch failed");
  };
  try {
    await assert.rejects(
      () => request("/test", new AbortController().signal),
      (e) => e.status === 0 && e.message.includes("Start FalkorDB"),
    );
  } finally {
    globalThis.fetch = original;
  }
});

test("focused view preserves policies, real edges, and full payload", () => {
  const files = Array.from({ length: 25 }, (_, i) => ({
    id: String(i),
    label: "File",
    metadata: {},
  }));
  const rule = {
    id: "rule",
    label: "Decision",
    status: "ACTIVE",
    metadata: {},
  };
  const graph = {
    nodes: [...files, rule],
    edges: [{ id: "governs", source: "rule", target: "0" }],
  };
  const focus = focusGraph(graph);
  assert.equal(focus.nodes.length, 18);
  assert.ok(focus.nodes.includes(rule));
  assert.equal(focus.edges.length, 1);
  assert.equal(graph.nodes.length, 26);
});
