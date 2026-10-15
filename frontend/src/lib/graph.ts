import type { Subgraph, VisualNode } from "./types";
// Presentation only: semantic lanes never change graph relationships.
export function placeNodes(
  graph: Subgraph,
): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  const lanes: VisualNode[][] = [[], [], [], []];
  const targetFiles = new Set(
    graph.nodes
      .filter((n) => n.metadata.audit_target === true)
      .map((n) => n.id),
  );
  if (!targetFiles.size) {
    for (const e of graph.edges)
      if (e.relationship === "GOVERNS") targetFiles.add(e.target);
  }
  if (!targetFiles.size) {
    const first = graph.nodes.find((n) => n.label === "File");
    if (first) targetFiles.add(first.id);
  }
  for (const n of graph.nodes) {
    let lane = 1;
    if (
      ["Investigation", "PullRequest"].includes(n.label) ||
      (n.label === "File" && targetFiles.has(n.id))
    )
      lane = 0;
    else if (
      n.status === "DEAD_END" ||
      n.status === "SUPERSEDED" ||
      n.label === "Contributor"
    )
      lane = 3;
    else if (
      n.label === "Decision" ||
      n.label === "File" ||
      (n.label === "StateNode" &&
        n.status === "GOLDEN_PATH" &&
        n.metadata.state_type !== "START" &&
        n.metadata.state_type !== "INTERMEDIATE")
    )
      lane = 2;
    else if (
      n.label === "StateNode" &&
      n.metadata.tool_name === "inspect_policies"
    )
      lane = 2;
    lanes[lane].push(n);
  }
  for (const [lane, nodes] of lanes.entries()) {
    // Stable ordering and vertical slots prevent overlap while keeping causal lanes.
    nodes.forEach((n, i) => positions.set(n.id, { x: lane * 370, y: i * 175 }));
  }
  return positions;
}

/** Add actual historical cold branches, without pretending they were replayed.
 * Keep their original source nodes and edge IDs: never invent warm→cold edges.
 */
export function replayEvidence(warm: Subgraph, cold: Subgraph): Subgraph {
  const dead = new Set(
    cold.nodes.filter((n) => n.status === "DEAD_END").map((n) => n.id),
  );
  const context = new Set(dead);
  for (const e of cold.edges) if (dead.has(e.target)) context.add(e.source);
  for (const e of cold.edges)
    if (
      context.has(e.target) &&
      cold.nodes.some((n) => n.id === e.source && n.label === "Investigation")
    )
      context.add(e.source);
  const ids = new Set(warm.nodes.map((n) => n.id));
  return {
    ...warm,
    nodes: [
      ...warm.nodes,
      ...cold.nodes
        .filter((n) => context.has(n.id) && !ids.has(n.id))
        .map((n) => ({
          ...n,
          metadata: {
            ...n.metadata,
            replay_evidence_only: true,
            pruned: n.status === "DEAD_END",
          },
        })),
    ],
    edges: [
      ...warm.edges,
      ...cold.edges
        .filter((e) => context.has(e.source) && context.has(e.target))
        .map((e) => ({ ...e, is_highlighted: false, is_pruned: true })),
    ],
  };
}

export function validEdges(graph: Subgraph) {
  const ids = new Set(graph.nodes.map((n) => n.id));
  return graph.edges.filter((e) => ids.has(e.source) && ids.has(e.target));
}
export function focusGraph(graph: Subgraph): Subgraph {
  if (graph.nodes.some((n) => n.label === "StateNode")) return graph;
  const audit = graph.nodes.some((n) => n.metadata.audit_target === true);
  const rules = graph.nodes
    .filter((n) => n.label === "Decision")
    .slice(0, audit ? 6 : 12);
  const targets = graph.nodes.filter((n) => n.metadata.audit_target === true);
  const targetIds = new Set(targets.map((n) => n.id));
  const definedIds = new Set(
    graph.edges
      .filter((e) => targetIds.has(e.source) && e.relationship === "DEFINES")
      .map((e) => e.target),
  );
  const patch = graph.nodes
    .filter((n) => n.metadata.source_type === "AST_PATCH_SIMULATION")
    .slice(0, 4);
  const functions = audit
    ? graph.nodes
        .filter((n) => n.label === "Function" && definedIds.has(n.id))
        .slice(0, Math.max(0, 4 - patch.length))
    : [];
  const fileLimit = audit ? 8 : rules.length ? 18 - rules.length : 8;
  const files = [
    ...targets,
    ...graph.nodes.filter((n) => n.label === "File" && !targetIds.has(n.id)),
  ].slice(0, fileLimit);
  const focus = [...rules, ...patch, ...functions, ...files].filter(
    (n, i, all) => all.findIndex((x) => x.id === n.id) === i,
  );
  const ids = new Set(focus.map((n) => n.id));
  return {
    ...graph,
    nodes: focus,
    edges: graph.edges.filter((e) => ids.has(e.source) && ids.has(e.target)),
  };
}
