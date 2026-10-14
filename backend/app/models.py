from typing import Dict, List, Literal, Optional, Any
from pydantic import BaseModel, Field


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


class SandboxAuditRequest(BaseModel):
    tenant_graph: str = "repo_falkordb_py"
    pr_number: Optional[int] = None
    modified_files: List[str] = Field(default_factory=list)
    proposed_description: str = ""


class SandboxAuditResponse(BaseModel):
    sandbox_graph_name: str
    sandbox_cleaned_up: bool
    risk_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL_POLICY_VIOLATION"]
    impacted_files: List[str]
    impacted_functions: List[str]
    active_decisions_triggered: List[Dict[str, Any]]
    recommended_reviewers: List[Dict[str, Any]]
    subgraph: GraphSubgraphPayload


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
    file_path: str
    active_decisions: List[Dict[str, Any]]
    superseded_decisions: List[Dict[str, Any]]
    top_experts: List[Dict[str, Any]]
    subgraph: GraphSubgraphPayload


class InvestigationRunRequest(BaseModel):
    tenant_graph: str = "repo_falkordb_py"
    issue_description: str
    execution_mode: Literal["cold_multi_agent", "compiled_playbook"] = "cold_multi_agent"


class InvestigationRunResponse(BaseModel):
    investigation_id: str
    execution_mode: str
    root_cause_summary: str
    total_steps_executed: int
    pruned_golden_steps: int
    tokens_used: int
    duration_ms: float
    token_savings_pct: float
    agent_handoff_log: List[Dict[str, Any]]
    compiled_playbook_id: Optional[str] = None
    subgraph: GraphSubgraphPayload
