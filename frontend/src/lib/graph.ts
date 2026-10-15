import type { Subgraph, VisualNode } from "./types";
// Presentation only. Never synthesize graph nodes or relationships.
export function placeNodes(
  graph: Subgraph,
): Map<string, { x: number; y: number }> {
  const positions = new Map<string, { x: number; y: number }>();
  const memory = graph.nodes.some((n) => n.label === "StateNode");
  if (memory) {
    const lanes = new Map<number, VisualNode[]>();
    for (const n of graph.nodes) {
      const m = n.metadata;
      const lane =
        n.label === "Investigation"
          ? 0
          : m.state_type === "START"
            ? 1
            : m.tool_name === "inspect_policies"
              ? 3
              : m.state_type === "VERIFIED_GOAL"
                ? 4
                : 2;
      lanes.set(lane, [...(lanes.get(lane) || []), n]);
    }
    lanes.forEach((nodes, lane) =>
      nodes.forEach((n, i) =>
        positions.set(n.id, { x: lane * 310, y: i * 150 }),
      ),
    );
    return positions;
  }
  const rules = graph.nodes.filter((n) => n.label === "Decision");
  const others = graph.nodes.filter((n) => n.label !== "Decision");
  const columns = others.length > 30 ? 6 : others.length > 12 ? 4 : 3;
  rules.forEach((n, i) => positions.set(n.id, { x: 0, y: i * 145 }));
  others.forEach((n, i) =>
    positions.set(n.id, {
      x: (rules.length ? 330 : 0) + (i % columns) * 310,
      y: Math.floor(i / columns) * 145,
    }),
  );
  return positions;
}
export function validEdges(graph: Subgraph) {
  const ids = new Set(graph.nodes.map((n) => n.id));
  return graph.edges.filter((e) => ids.has(e.source) && ids.has(e.target));
}
export function focusGraph(graph: Subgraph): Subgraph {
  if (graph.nodes.some((n) => n.label === "StateNode")) return graph;
  const rules = graph.nodes.filter((n) => n.label === "Decision").slice(0, 12);
  const files = graph.nodes
    .filter((n) => n.label === "File")
    .slice(0, 18 - rules.length);
  const focus = [...rules, ...files];
  const ids = new Set(focus.map((n) => n.id));
  return {
    ...graph,
    nodes: focus,
    edges: graph.edges.filter((e) => ids.has(e.source) && ids.has(e.target)),
  };
}
