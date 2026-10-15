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
  pull_requests: { number: number; title: string; url: string; source_type?: string; record_kind?: string; commit_sha?: string }[];
  edge_count?: number;
  indexed_record_count?: number;
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
  context_window_savings?: { measurement_status: string; raw_repo_bytes: number; slice_bytes: number; context_saved_pct: number };
  impacted_test_files?: string[];
  total_repo_test_files?: number;
  test_suite_reduction_pct?: number;
  recommended_pytest_command?: string;
  patch_symbols_analyzed?: string[];
  test_selection_basis?: string;
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
  repository_constraints?: RecordData[];
  file_path: string;
  active_decisions: RecordData[];
  superseded_decisions: RecordData[];
  top_experts: RecordData[];
  blind_agent_comparison: Baseline;
  subgraph: Subgraph;
}
export interface Investigation {
  resume_snapshot?: { file_path: string; markdown: string; snapshot_bytes: number };
  raw_files_context_tokens?: number;
  compiled_slice_context_tokens?: number;
  context_token_reduction_pct?: number;
  raw_files_context_bytes?: number;
  compiled_slice_context_bytes?: number;
  context_measurement_status?: string;
  compiled_context_slice_preview?: string;
  context_candidate_files?: string[];
  model_calls?: number;
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
