"""Run locally: python -m app.mcp_server.server (stdio transport)."""
from fastmcp import FastMCP
from app.models import (SandboxAuditRequest, BrainQueryRequest,
                        PolicyOverrideRequest, InvestigationRunRequest)
from app.services.sandbox_auditor import audit_sandbox
from app.services.company_brain import ask_brain, override_policy, find_true_code_owners as owners
from app.services.memory_compiler import run_investigation

mcp = FastMCP('ChronosGraph', instructions='Local trusted-client demo. Policy scenarios are labeled; telemetry is not an LLM benchmark.')


@mcp.tool
def simulate_pr_blast_radius(modified_files: list[str], tenant_graph: str='repo_falkordb_py',
                             pr_number: int | None=None, proposed_description: str='', proposed_code_patch: str | None=None) -> dict:
    """LESSON: Before hub edits, audit a disposable GRAPH.COPY clone and inspect candidate tests."""
    return audit_sandbox(SandboxAuditRequest(tenant_graph=tenant_graph,modified_files=modified_files,
        pr_number=pr_number,proposed_description=proposed_description,proposed_code_patch=proposed_code_patch)).model_dump()


@mcp.tool
def query_bitemporal_decisions(question: str,tenant_graph: str='repo_falkordb_py',file_path: str | None=None) -> dict:
    """LESSON: Refresh ACTIVE two-clock rules before architectural edits or compaction recovery."""
    return ask_brain(BrainQueryRequest(tenant_graph=tenant_graph,question=question,file_path=file_path)).model_dump()


@mcp.tool
def record_decision_override(target_file_path: str,new_rule_text: str,rationale: str,
        tenant_graph: str='repo_falkordb_py',scope_symbol: str='module_root',author_handle: str='lead-maintainer') -> dict:
    """LESSON: Only after human confirmation, record a local override; existing playbooks may become stale."""
    return override_policy(PolicyOverrideRequest(tenant_graph=tenant_graph,target_file_path=target_file_path,
        new_rule_text=new_rule_text,rationale=rationale,scope_symbol=scope_symbol,author_handle=author_handle)).model_dump()


@mcp.tool
def find_true_code_owners(file_path: str,tenant_graph: str='repo_falkordb_py') -> list[dict]:
    """LESSON: Before architectural edits, rank source-linked commit and review contributors."""
    return owners(tenant_graph,file_path)


@mcp.tool
def run_or_compile_playbook(issue_description: str,tenant_graph: str='repo_falkordb_py',
                            execution_mode: str='cold_multi_agent') -> dict:
    """LESSON: Before bulk reads or after /compact, compile triage or replay an exact current verified playbook."""
    return run_investigation(InvestigationRunRequest(tenant_graph=tenant_graph,
        issue_description=issue_description,execution_mode=execution_mode)).model_dump()


if __name__=='__main__':
    mcp.run()
