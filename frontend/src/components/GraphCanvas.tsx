"use client";
import { useEffect, useMemo, useState } from "react";
import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MiniMap,
  Position,
  ReactFlow,
  ReactFlowProvider,
  useReactFlow,
  useNodesState,
  type Node,
  type NodeProps,
} from "@xyflow/react";
import { GitBranch, Maximize2 } from "lucide-react";
import type { Subgraph, VisualNode } from "@/lib/types";
import { focusGraph, placeNodes, validEdges } from "@/lib/graph";
type EvidenceNode = Node<{ evidence: VisualNode }, "evidence">;
function Evidence({ data }: NodeProps<EvidenceNode>) {
  const n = data.evidence;
  return (
    <div className={`evidence-node status-${n.status}`}>
      <Handle type="target" position={Position.Left} />
      <div className="node-top">
        <span>{n.label}</span>
        <span>
          {n.status === "DEFAULT" ? "SOURCE" : n.status.replaceAll("_", " ")}
        </span>
      </div>
      <div className="node-title" title={n.title}>
        {n.title}
      </div>
      {n.status === "DEAD_END" && (
        <div className="node-note">PRUNED BY SHORTESTPATH</div>
      )}
      {n.subtitle && (
        <div className="node-note" title={n.subtitle}>
          {n.subtitle}
        </div>
      )}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}
const nodeTypes = { evidence: Evidence };
function Canvas({
  graph,
  onSelect,
}: {
  graph: Subgraph | null;
  onSelect: (node: VisualNode) => void;
}) {
  const { fitView } = useReactFlow();
  const [all, setAll] = useState(false);
  const view = useMemo(
    () => (graph ? (all ? graph : focusGraph(graph)) : null),
    [graph, all],
  );
  useEffect(() => setAll(false), [graph]);
  const nodes = useMemo<EvidenceNode[]>(() => {
    if (!view) return [];
    const positions = placeNodes(view);
    return view.nodes.map((n) => ({
      id: n.id,
      type: "evidence",
      position: positions.get(n.id)!,
      data: { evidence: n },
    }));
  }, [view]);
  const [flowNodes, setFlowNodes, onNodesChange] = useNodesState<EvidenceNode>(
    [],
  );
  useEffect(() => setFlowNodes(nodes), [nodes, setFlowNodes]);
  const edges = useMemo(
    () =>
      view
        ? validEdges(view).map((e) => ({
            id: e.id,
            source: e.source,
            target: e.target,
            label: e.relationship,
            type: "smoothstep",
            animated: e.is_highlighted,
            className: e.is_pruned
              ? "pruned-edge"
              : e.is_highlighted
                ? "golden-edge"
                : "",
            style: {
              stroke: e.is_pruned
                ? "#fb7185"
                : e.is_highlighted
                  ? "#22d3ee"
                  : "#64748b",
              strokeWidth: e.is_highlighted ? 2 : 1,
              strokeDasharray: e.is_pruned ? "5 5" : undefined,
            },
            labelStyle: { fill: "#cbd5e1", fontSize: 11 },
            labelBgStyle: { fill: "#0f172a", fillOpacity: 0.95 },
          }))
        : [],
    [view],
  );
  useEffect(() => {
    const timer = setTimeout(
      () =>
        void fitView({
          padding: 0.2,
          minZoom: 0.1,
          maxZoom: 0.85,
          duration: 0,
        }),
      80,
    );
    return () => clearTimeout(timer);
  }, [view, fitView]);
  return (
    <>
      <div className="canvas-heading">
        <div>
          <span className="eyebrow">GRAPH FLIGHT RECORDER</span>
          <h2>
            Connected evidence{" "}
            <span className="count">
              {nodes.length} nodes · {edges.length} edges
            </span>
          </h2>
        </div>
        <button
          className="icon-button"
          aria-label="Fit graph"
          onClick={() => void fitView({ padding: 0.2, maxZoom: 1 })}
        >
          <Maximize2 size={16} />
        </button>
      </div>
      <div className="graph-toolbar">
        <span>
          {nodes.length} of {graph?.nodes.length || 0} payload nodes ·{" "}
          {all ? "Full payload" : "Focused evidence"}
        </span>
        <button
          className="text-button"
          disabled={!graph}
          onClick={() => setAll((v) => !v)}
        >
          {all ? "Focus files & rules" : "Show all payload nodes"}
        </button>
      </div>
      <div className="graph-area" aria-label="Interactive evidence graph">
        <ReactFlow
          nodes={flowNodes}
          onNodesChange={onNodesChange}
          edges={edges}
          nodeTypes={nodeTypes}
          colorMode="dark"
          minZoom={0.06}
          maxZoom={2}
          fitView
          nodesDraggable
          nodesConnectable={false}
          onNodeClick={(_, n) => onSelect(n.data.evidence)}
          proOptions={{ hideAttribution: false }}
        >
          <Background
            variant={BackgroundVariant.Dots}
            gap={24}
            size={1}
            color="#26344c"
          />
          <Controls showInteractive={false} />
          <MiniMap
            zoomable
            pannable
            nodeColor={(n) =>
              ({
                ACTIVE: "#34d399",
                SUPERSEDED: "#fb7185",
                IMPACTED: "#fbbf24",
                DEAD_END: "#fb7185",
                GOLDEN_PATH: "#22d3ee",
                DEFAULT: "#94a3b8",
              })[(n.data.evidence as VisualNode).status]
            }
            style={{ background: "#0b1222" }}
          />
        </ReactFlow>
        {!nodes.length && (
          <div className="canvas-empty">
            <GitBranch size={32} />
            <h3>No graph loaded</h3>
            <p>
              Connect the local backend and select a repository. Graph evidence
              appears here—not a simulated preview.
            </p>
          </div>
        )}
        <div className="graph-caption">
          Scoped view · zoom to inspect · select a node for provenance
        </div>
      </div>
      <div className="legend">
        {["ACTIVE", "SUPERSEDED", "IMPACTED", "DEAD_END", "GOLDEN_PATH"].map(
          (s) => (
            <span key={s}>
              <i className={`dot status-${s}`} />
              {s.replaceAll("_", " ")}
            </span>
          ),
        )}
      </div>
      <details className="cypher-drawer">
        <summary>
          Cypher flight log{" "}
          <span>
            {graph
              ? `${graph.execution_time_ms.toFixed(2)} ms`
              : "Not measured"}
          </span>
        </summary>
        <p>
          Query text reported by the backend; bounded subgraph, not a complete
          repository view.
        </p>
        <pre>
          {graph?.cypher_executed ||
            "Run a query to inspect the backend Cypher."}
        </pre>
      </details>
    </>
  );
}
export default function GraphCanvas(props: {
  graph: Subgraph | null;
  onSelect: (node: VisualNode) => void;
}) {
  return (
    <ReactFlowProvider>
      <Canvas {...props} />
    </ReactFlowProvider>
  );
}
