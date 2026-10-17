"use client";
import { useEffect, useMemo, useState } from "react";
import { ReactFlow, Background, Controls, MiniMap, MarkerType, Position, useReactFlow, ReactFlowProvider, useStore, type Node, type Edge } from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import type { RepositoryMap, FileDetail } from "@/lib/command-center";
function Fit({ identity }: { identity: string }) {
  const flow = useReactFlow();
  const width=useStore(s=>s.width),height=useStore(s=>s.height);
  useEffect(() => { const id = setTimeout(() => void flow.fitView({ padding: .2, maxZoom: 1 }), 80); return () => clearTimeout(id); }, [identity, flow, width, height]);
  return null;
}
export default function CommandGraph({ map, detail, functions, selected, onPick, table: controlledTable, setTable: onTableChange }: {
  map: RepositoryMap | null; detail: FileDetail | null; functions: boolean; selected: string;
  table?: boolean; setTable?: (table: boolean) => void;
  onPick: (path: string, kind: string, symbol?: string) => void;
}) {
  const [localTable,setLocalTable]=useState(false);
  const table=controlledTable??localTable, setTable=onTableChange??setLocalTable;
  const { nodes, edges } = useMemo(() => {
    const nodes: Node[] = []; const edges: Edge[] = [];
    const add = (id: string, title: string, subtitle: string, x: number, y: number, kind: string, path: string, symbol?: string) => {
      nodes.push({ id, position: { x, y }, sourcePosition: Position.Right, targetPosition: Position.Left,
        data: { label: <div className="cc-node"><span>{kind === "folder" ? "▧" : kind === "function" ? "ƒ" : "◇"} {title}</span><small>{subtitle}</small></div>, kind, path, symbol },
        style: { width: 222, padding: 14, borderRadius: 8, background: id === selected ? "#202020" : "#101010", color: "#f5f5f5", border: id === selected ? "1px solid #eee" : "1px solid #3a3a3a" } });
    };
    const link = (source: string, target: string, label: string) => edges.push({ id: `${source}→${target}:${label}`, source, target, label, type: "smoothstep", markerEnd: { type: MarkerType.ArrowClosed, color: "#777" }, style: { stroke: "#656565" }, labelStyle: { fill: "#bbb", fontSize: 10 }, labelBgStyle: { fill: "#090909" } });
    if (detail && functions) {
      const file = detail.file.path;
      add(file, file.split("/").pop() || file, "Selected file", 0, 80, "file", file);
      detail.symbols.slice(0, 60).forEach((s, i) => { add(s.qualified_name, s.name, `${s.kind} · line ${s.start_line}`, 340 + Math.floor(i / 12) * 340, (i % 12) * 108, s.kind === "Function" ? "function" : "class", file, s.qualified_name); link(file, s.qualified_name, "defines"); });
      const ids = new Set(nodes.map(n => n.id));
      detail.calls.filter(c => ids.has(c.source) && ids.has(c.target)).forEach(c => link(c.source, c.target, "calls"));
    } else if (detail) {
      const file = detail.file.path;
      add(file, file.split("/").pop() || file, file, 350, 130, "file", file);
      detail.imports.slice(0, 20).forEach((f, i) => { if(f.path !== file) add(f.path, f.path.split("/").pop() || f.path, f.path, 700, i * 115, "file", f.path); link(file, f.path, "imports"); });
      detail.importers.slice(0, 20).forEach((f, i) => { if (!nodes.some(n => n.id === f.path)) add(f.path, f.path.split("/").pop() || f.path, f.path, 0, i * 115, "file", f.path); link(f.path, file, "imports"); });
    } else if (map) {
      const incoming = new Map<string, number>(); map.edges.forEach(e => incoming.set(e.target,(incoming.get(e.target)||0)+e.count));
      const outgoing=new Map<string,number>();map.edges.forEach(e=>outgoing.set(e.source,(outgoing.get(e.source)||0)+e.count));
      const ordered=[...map.nodes].sort((a,b)=>a.path.localeCompare(b.path));const slots=[0,0,0];
      ordered.forEach(g=>{const ins=incoming.get(g.id)||0,outs=outgoing.get(g.id)||0;const lane=ins>outs?2:outs>0?0:1;const y=slots[lane]++*135+(lane===1?210:0);add(g.id,g.path.replace(map.prefix,"").replace(/\/$/,""),g.kind === "folder" ? `${g.files} tracked files` : "File",lane*350,y,g.kind,g.path);});
      map.edges.forEach(e => link(e.source,e.target,e.count === 1 ? "imports" : `${e.count} imports`));
    }
    return { nodes, edges };
  }, [map,detail,functions,selected]);
  return <><div className="cc-graph-mode" role="group" aria-label="Repository relationship view"><button aria-pressed={!table} onClick={()=>setTable(false)}>Graph</button><button aria-pressed={table} onClick={()=>setTable(true)}>Table</button></div>{table?<div className="cc-graph-table"><table><caption>Visible nodes and their outgoing relationships. Same bounded selection as the graph.</caption><thead><tr><th scope="col">File or symbol</th><th scope="col">Kind</th><th scope="col">Connections</th></tr></thead><tbody>{nodes.map(n=><tr key={n.id}><td><button onClick={()=>onPick(String(n.data.path),String(n.data.kind),n.data.symbol?String(n.data.symbol):undefined)}>{String(n.data.symbol||n.data.path)}</button></td><td>{String(n.data.kind)}</td><td>{edges.filter(e=>e.source===n.id).map(e=>`${e.label} → ${e.target}`).join('; ')||'No outgoing connections in this selection'}</td></tr>)}</tbody></table></div>:<ReactFlowProvider><ReactFlow nodes={nodes} edges={edges} fitView minZoom={.08} maxZoom={2} nodesDraggable={false} colorMode="dark"
    onNodeClick={(_, node) => onPick(String(node.data.path),String(node.data.kind),node.data.symbol ? String(node.data.symbol) : undefined)}
    proOptions={{ hideAttribution: false }}><Background color="#292929" gap={24} size={1}/><Controls showInteractive={false}/><MiniMap pannable zoomable nodeColor="#777" maskColor="rgba(0,0,0,.6)"/><Fit identity={`${map?.prefix}:${detail?.file.path}:${functions}:${nodes.length}`}/>
  </ReactFlow><div className="cc-canvas-hint">Scroll to zoom · drag to explore · select a node to inspect</div></ReactFlowProvider>}</>;
}
