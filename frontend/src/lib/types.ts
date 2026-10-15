export type RecordData = Record<string, unknown>;
export type Status =
  "ACTIVE" | "SUPERSEDED" | "IMPACTED" | "DEAD_END" | "GOLDEN_PATH" | "DEFAULT";
export interface VisualNode {
  id: string;
  label: string;
  title: string;
  subtitle?: string | null;
  status: Status;
  url?: string | null;
  metadata: RecordData;
}
export interface VisualEdge {
  id: string;
  source: string;
  target: string;
  relationship: string;
  is_highlighted: boolean;
  is_pruned: boolean;
}
export interface Subgraph {
  nodes: VisualNode[];
  edges: VisualEdge[];
  cypher_executed: string;
  execution_time_ms: number;
}
export interface Tenant {
  tenant_graph: string;
  repository: string;
  node_count: number;
  pull_requests: { number: number; title: string; url: string }[];
  preset_files: string[];
}
export interface Baseline {
  verdict: string;
  mistake_summary: string;
  obsolete_rule_followed?: string | null;
  missed_downstream_count: number;
  steps_taken: number;
  tokens_burned: number;
  duration_ms: number;
}
export interface Audit {
  sandbox_graph_name: string;
  sandbox_clone_time_ms: number;
  sandbox_cleaned_up: boolean;
  risk_level: string;
  impacted_files: string[];
  impacted_functions: string[];
  active_decisions_triggered: RecordData[];
  recommended_reviewers: RecordData[];
  blind_agent_comparison: Baseline;
  subgraph: Subgraph;
}
export interface Brain {
  file_path: string;
  active_decisions: RecordData[];
  superseded_decisions: RecordData[];
  top_experts: RecordData[];
  blind_agent_comparison: Baseline;
  subgraph: Subgraph;
}
export interface Investigation {
  investigation_id: string;
  execution_mode: string;
  root_cause_summary: string;
  total_steps_executed: number;
  pruned_golden_steps: number;
  tokens_used: number;
  duration_ms: number;
  token_savings_pct: number;
  latency_speedup_factor: number;
  agent_handoff_log: RecordData[];
  compiled_playbook_id?: string | null;
  blind_agent_comparison: Baseline;
  subgraph: Subgraph;
}
export type Result =
  | { kind: "audit"; data: Audit }
  | { kind: "brain"; data: Brain }
  | { kind: "memory"; data: Investigation };
