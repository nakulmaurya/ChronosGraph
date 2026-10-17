from typing import Annotated, Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


class VisualNode(BaseModel):
    id: str
    label: str  # File | Function | Class | Decision | PullRequest | Issue | Contributor | StateNode | Playbook
    title: str
    subtitle: Optional[str] = None
    status: Literal[
        "ACTIVE",
        "SUPERSEDED",
        "IMPACTED",
        "DEAD_END",
        "GOLDEN_PATH",
        "DEFAULT",
    ] = "DEFAULT"
    url: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VisualEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship: str
    is_highlighted: bool = False
    is_pruned: bool = False


class GraphSubgraphPayload(BaseModel):
    nodes: List[VisualNode]
    edges: List[VisualEdge]
    cypher_executed: str
    execution_time_ms: float


class BlindAgentComparison(BaseModel):
    """Side-by-side baseline showing what a standard stateless RAG / AST agent does."""
    verdict: str  # e.g., "FALSE_SAFE_APPROVAL (OUTAGE)" or "SLOW_UNPRUNED_LOOP"
    mistake_summary: str
    obsolete_rule_followed: Optional[str] = None
    missed_downstream_count: int = 0
    steps_taken: int = 0
    tokens_burned: int = 0
    duration_ms: float = 0.0


class SandboxAuditRequest(BaseModel):
    tenant_graph: str = "repo_falkordb_py"
    pr_number: Optional[int] = None
    modified_files: List[str] = Field(default_factory=list)
    proposed_description: str = ""
    proposed_code_patch: Optional[str] = Field(default=None, max_length=32000)


class SandboxAuditResponse(BaseModel):
    context_window_savings: Dict[str, Any] = Field(default_factory=dict)
    sandbox_graph_name: str
    sandbox_clone_time_ms: float
    sandbox_cleaned_up: bool
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL_POLICY_VIOLATION"]
    impacted_files: List[str]
    impacted_test_files: List[str] = Field(default_factory=list)
    total_repo_test_files: int = 0
    test_suite_reduction_pct: float = 0.0
    recommended_pytest_command: str = "pytest"
    patch_symbols_analyzed: List[str] = Field(default_factory=list)
    test_selection_basis: str = "BOUNDED_STATIC_CANDIDATES_NOT_SAFE_SKIP_PROOF"
    impacted_functions: List[str]
    active_decisions_triggered: List[Dict[str, Any]]
    recommended_reviewers: List[Dict[str, Any]]
    blind_agent_comparison: BlindAgentComparison
    subgraph: GraphSubgraphPayload


class WikiCompileRequest(BaseModel):
    tenant_graph: str = "repo_falkordb_py"
    file_path: Optional[str] = None
    export: bool = False


class BrainQueryRequest(BaseModel):
    tenant_graph: str = "repo_falkordb_py"
    question: str
    file_path: Optional[str] = None


class PolicyOverrideRequest(BaseModel):
    tenant_graph: str = "repo_falkordb_py"
    target_file_path: str
    scope_symbol: str = "module_root"
    new_rule_text: str
    rationale: str
    author_handle: str = "lead-maintainer"


class PolicyLineageResponse(BaseModel):
    repository_constraints: List[Dict[str, Any]] = Field(default_factory=list)
    file_path: str
    active_decisions: List[Dict[str, Any]]
    superseded_decisions: List[Dict[str, Any]]
    top_experts: List[Dict[str, Any]]
    blind_agent_comparison: BlindAgentComparison
    subgraph: GraphSubgraphPayload


class InvestigationRunRequest(BaseModel):
    tenant_graph: str = "repo_falkordb_py"
    issue_description: str
    execution_mode: Literal["cold_multi_agent", "compiled_playbook"] = "cold_multi_agent"


class InvestigationRunResponse(BaseModel):
    resume_snapshot: Dict[str, Any] = Field(default_factory=dict)
    investigation_id: str
    execution_mode: str
    raw_files_context_tokens: int = 0
    compiled_slice_context_tokens: int = 0
    context_token_reduction_pct: float = 0.0
    raw_files_context_chars: int = 0
    raw_files_context_bytes: int = 0
    compiled_slice_context_chars: int = 0
    compiled_slice_context_bytes: int = 0
    context_measurement_status: str = "SOURCE_SIZES_UNAVAILABLE"
    context_candidate_files: List[str] = Field(default_factory=list)
    compiled_context_slice_preview: str = ""
    model_calls: int = 0
    root_cause_summary: str
    total_steps_executed: int
    pruned_golden_steps: int
    tokens_used: int
    duration_ms: float
    token_savings_pct: float
    latency_speedup_factor: float
    agent_handoff_log: List[Dict[str, Any]]
    compiled_playbook_id: Optional[str] = None
    blind_agent_comparison: BlindAgentComparison
    subgraph: GraphSubgraphPayload


class DiffImpactRequest(BaseModel):
    """Explicit final state; never changes legacy proposed_code_patch semantics."""
    tenant_graph: str = "repo_falkordb_py"
    expected_revision: Optional[str] = Field(default=None, pattern=r"^[0-9a-f]{40}$")
    unified_diff: Optional[str] = Field(default=None, max_length=128000)
    file_bodies: Dict[str, Optional[str]] = Field(default_factory=dict, max_length=20)

    @model_validator(mode="after")
    def exactly_one_input(self):
        if (self.unified_diff is not None) == bool(self.file_bodies):
            raise ValueError("Provide exactly one of unified_diff or nonempty file_bodies (null deletes a file)")
        return self


class FindingRequest(BaseModel):
    tenant_graph: str = "repo_falkordb_py"
    summary: str = Field(min_length=1, max_length=500)
    evidence_note: str = Field(min_length=1, max_length=2000)
    supporting_file_shas: Dict[Annotated[str, Field(min_length=1, max_length=1024)], Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]] = Field(min_length=1, max_length=10)
    verification_command: str = Field(default="", max_length=500)
