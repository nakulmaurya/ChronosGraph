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

test("semantic lanes distinguish targets, impacts, active policy and history", () => {
  const node = (id, label, status, metadata = {}) => ({
    id,
    label,
    status,
    metadata,
  });
  const graph = {
    nodes: [
      node("target", "File", "IMPACTED", { audit_target: true }),
      node("fn", "Function", "IMPACTED"),
      node("impact", "File", "IMPACTED"),
      node("active", "Decision", "ACTIVE"),
      node("old", "Decision", "SUPERSEDED"),
      node("dead", "StateNode", "DEAD_END"),
    ],
  };
  const p = placeNodes(graph);
  assert.ok(p.get("target").x < p.get("fn").x);
  assert.ok(p.get("fn").x < p.get("impact").x);
  assert.equal(p.get("active").x, p.get("impact").x);
  assert.ok(p.get("impact").x < p.get("old").x);
  assert.notDeepEqual(p.get("old"), p.get("dead"));
});

test("replay shows actual historical cold branches without inventing edges or mutating telemetry", async () => {
  const { replayEvidence } = await import("../src/lib/graph.ts");
  const n = (id, label, status = "GOLDEN_PATH") => ({
    id,
    label,
    status,
    metadata: {},
  });
  const cold = {
    nodes: [
      n("ci", "Investigation"),
      n("cs", "StateNode"),
      n("cd", "StateNode", "DEAD_END"),
      n("cg", "StateNode"),
    ],
    edges: [
      { id: "c1", source: "ci", target: "cs" },
      { id: "c2", source: "cs", target: "cd" },
      { id: "c3", source: "cs", target: "cg" },
    ],
  };
  const warm = {
    nodes: [n("wi", "Investigation"), n("ws", "StateNode")],
    edges: [{ id: "w1", source: "wi", target: "ws" }],
  };
  const result = replayEvidence(warm, cold);
  assert.equal(result.nodes.find((n) => n.id === "cd").metadata.pruned, true);
  assert.equal(
    result.nodes.find((n) => n.id === "cs").metadata.replay_evidence_only,
    true,
  );
  assert.ok(!result.nodes.some((n) => n.id === "cg"));
  assert.deepEqual(
    result.edges.map((e) => [e.id, e.source, e.target]),
    [...warm.edges, ...cold.edges.slice(0, 2)].map((e) => [
      e.id,
      e.source,
      e.target,
    ]),
  );
  assert.equal(validEdges(result).length, result.edges.length);
  assert.equal(warm.nodes.length, 2);
});

test("comparison uses observed values, not fixed benchmark numbers", async () => {
  const { comparison } = await import("../src/lib/comparison.ts");
  const cold = {
    total_steps_executed: 5,
    duration_ms: 90,
    execution_mode: "cold_multi_agent",
    pruned_golden_steps: 3,
    agent_handoff_log: [{ dead_end: true }, { dead_end: true }],
  };
  const warm = {
    ...cold,
    total_steps_executed: 3,
    duration_ms: 100,
    execution_mode: "compiled_playbook",
    latency_speedup_factor: 0.9,
    agent_handoff_log: [{}, {}, {}],
  };
  const r = comparison({ kind: "memory", data: warm }, cold);
  assert.match(r.left, /5 actions \(2 dead ends\)/);
  assert.match(r.right, /40% fewer actions/);
  assert.match(r.right, /0\.900×/); // slower replay is not hidden
  assert.match(
    comparison({ kind: "memory", data: cold }, cold).right,
    /run replay to measure/,
  );
  assert.match(
    comparison(
      {
        kind: "audit",
        data: {
          blind_agent_comparison: { missed_downstream_count: 7 },
          impacted_files: ["a", "b"],
          impacted_functions: ["x"],
        },
      },
      null,
    ).left,
    /Missed 7/,
  );
  assert.match(
    comparison(
      {
        kind: "brain",
        data: { active_decisions: [], blind_agent_comparison: {} },
      },
      null,
    ).right,
    /No ACTIVE/,
  );
});
