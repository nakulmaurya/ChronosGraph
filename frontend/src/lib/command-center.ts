export type MapGroup = { id: string; path: string; kind: string; files: number };
export type RepositoryMap = { prefix: string; counts: Record<string,number>; nodes: MapGroup[];
  edges: { source: string; target: string; count: number }[]; inventory: { path: string; pagerank: number }[];
  coverage: { files_truncated: boolean; groups_total: number; groups_truncated: boolean; inventory_truncated: boolean; import_edges_truncated: boolean; display_edges_truncated?: boolean }; execution_time_ms: number };
export type SymbolInfo = { name: string; kind: string; qualified_name: string; signature: string | null; start_line: number; end_line: number; docstring: string | null };
export type FileDetail = { file: { path: string; sha256: string | null; revision: string | null; lines: number; parse_errors: number; source_url: string | null };
 symbols: SymbolInfo[]; imports: { path: string }[]; importers: { path: string }[];
 calls: { source: string; target: string; source_file: string; target_file: string }[]; coverage: Record<string,unknown> };
export type HistoryData = { commits: { sha: string; title: string; author: string; timestamp: number; url: string }[];
 changes: { path: string; additions: number; deletions: number }[]; changes_truncated: boolean; scope: string; source_at: string };
export type ImportJob = { id: string; tenant_graph: string; status: string; stage: string; error: string | null; result: { source_revision?: string } | null };
export function breadcrumbParent(prefix: string): string { return prefix.replace(/[^/]+\/$/, ""); }
export function boundedMapNotice(map: RepositoryMap): boolean { return map.coverage.files_truncated || map.coverage.groups_truncated || map.coverage.import_edges_truncated || !!map.coverage.display_edges_truncated; }
