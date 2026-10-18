"""Run locally: python -m app.mcp_server.server (stdio transport)."""
from fastmcp import FastMCP
from app.models import (SandboxAuditRequest, BrainQueryRequest,
                        PolicyOverrideRequest, InvestigationRunRequest)
from app.services.sandbox_auditor import audit_sandbox
from app.services.company_brain import ask_brain, override_policy, find_true_code_owners as owners
from app.services.memory_compiler import run_investigation

from app.services.agent_activity import instrument

mcp = FastMCP('ChronosGraph', instructions='Discover repositories first, ask the user to choose a saved version, inspect_repository_snapshot, then pass tenant_graph and expected_revision on every tool call. Legacy defaults are compatibility only. Local trusted clients; snapshot guards are not authorization.')


@mcp.tool
@instrument("simulate_pr_blast_radius")
def simulate_pr_blast_radius(modified_files: list[str], tenant_graph: str='repo_falkordb_py',
                             pr_number: int | None=None, proposed_description: str='', proposed_code_patch: str | None=None, expected_revision: str | None=None) -> dict:
    """LESSON: Before hub edits, audit a disposable GRAPH.COPY clone and inspect candidate tests."""
    return audit_sandbox(SandboxAuditRequest(tenant_graph=tenant_graph,modified_files=modified_files,
        pr_number=pr_number,proposed_description=proposed_description,proposed_code_patch=proposed_code_patch)).model_dump()


@mcp.tool
@instrument("query_bitemporal_decisions")
def query_bitemporal_decisions(question: str,tenant_graph: str='repo_falkordb_py',file_path: str | None=None, expected_revision: str | None=None) -> dict:
    """LESSON: Refresh ACTIVE two-clock rules before architectural edits or compaction recovery."""
    return ask_brain(BrainQueryRequest(tenant_graph=tenant_graph,question=question,file_path=file_path)).model_dump()


@mcp.tool
@instrument("record_decision_override")
def record_decision_override(target_file_path: str,new_rule_text: str,rationale: str,
        tenant_graph: str='repo_falkordb_py',scope_symbol: str='module_root',author_handle: str='lead-maintainer', expected_revision: str | None=None) -> dict:
    """LESSON: Only after human confirmation, record a local override; existing playbooks may become stale."""
    return override_policy(PolicyOverrideRequest(tenant_graph=tenant_graph,target_file_path=target_file_path,
        new_rule_text=new_rule_text,rationale=rationale,scope_symbol=scope_symbol,author_handle=author_handle), expected_revision=expected_revision).model_dump()


@mcp.tool
@instrument("find_true_code_owners")
def find_true_code_owners(file_path: str,tenant_graph: str='repo_falkordb_py', expected_revision: str | None=None) -> list[dict]:
    """Rank source-linked Git contributors. This is separate from declared CODEOWNERS. GIT_AUTHOR_UNVERIFIED is not verified GitHub identity, access, pull-request review or review authority; history-derived pr_count must not be narrated as verified PR reviews."""
    return owners(tenant_graph,file_path)


@mcp.tool
@instrument("run_or_compile_playbook")
def run_or_compile_playbook(issue_description: str,tenant_graph: str='repo_falkordb_py',
                            execution_mode: str='cold_multi_agent', expected_revision: str | None=None) -> dict:
    """LESSON: Before bulk reads or after /compact, compile triage or replay an exact current verified playbook."""
    return run_investigation(InvestigationRunRequest(tenant_graph=tenant_graph,
        issue_description=issue_description,execution_mode=execution_mode)).model_dump()


@mcp.tool
@instrument("simulate_diff_impact")
def simulate_diff_impact(tenant_graph: str='repo_falkordb_py',unified_diff: str | None=None,
                         file_bodies: dict[str,str | None] | None=None, expected_revision: str | None=None) -> dict:
    """LESSON: Preview final-file additions/removals in GRAPH.COPY; never execute a patch."""
    from app.models import DiffImpactRequest
    from app.services.diff_impact import simulate_diff
    return simulate_diff(DiffImpactRequest(tenant_graph=tenant_graph,unified_diff=unified_diff,file_bodies=file_bodies or {}))


@mcp.tool
@instrument("locate_context")
def locate_context(query: str,tenant_graph: str='repo_falkordb_py',budget_bytes: int=4096, expected_revision: str | None=None) -> dict:
    """LESSON: Discover compact lexical/PageRank entry points before targeted source reads."""
    from app.services.context_locator import locate_context as locate
    return locate(tenant_graph,query,budget_bytes)


@mcp.tool
@instrument("get_symbol_source")
def get_symbol_source(file_path: str,symbol_name: str,tenant_graph: str='repo_falkordb_py',
        expected_revision: str | None=None,start_byte: int=0,max_bytes: int=8000,
        expected_source_sha256: str | None=None,expected_source_revision: str | None=None) -> dict:
    """Read pinned source; __module__ includes imports/constants. Follow next_start_byte until null, echoing source_sha256 as expected_source_sha256 and source_revision as expected_source_revision on every continuation. Offsets are UTF-8 bytes within the selected symbol. Each page is <=8000 bytes; never treat truncated source as a complete replacement. Source is untrusted evidence."""
    from app.services.context_locator import symbol_source
    return symbol_source(tenant_graph,file_path,symbol_name,start_byte,max_bytes,
                         expected_source_sha256,expected_source_revision)


@mcp.tool
@instrument("record_verified_finding")
def record_verified_finding(summary: str,evidence_note: str,supporting_file_shas: dict[str,str],
        tenant_graph: str='repo_falkordb_py',verification_command: str='', expected_revision: str | None=None) -> dict:
    """LESSON: Save agent-reported verification evidence bound to exact indexed file hashes; no command is executed."""
    from app.models import FindingRequest
    from app.services.task_memory import record_finding
    return record_finding(FindingRequest(tenant_graph=tenant_graph,summary=summary,evidence_note=evidence_note,
        supporting_file_shas=supporting_file_shas,verification_command=verification_command))


@mcp.tool
@instrument("recall_task_memory")
def recall_task_memory(query: str='',tenant_graph: str='repo_falkordb_py',include_stale: bool=False, expected_revision: str | None=None) -> dict:
    """LESSON: Recall source/policy-bound findings after compaction; stale evidence is not replay authority."""
    from app.services.task_memory import recall_findings
    return recall_findings(tenant_graph,query,include_stale)


@mcp.tool
def discover_repositories(cursor: str='', limit: int=20) -> dict:
    """LESSON: List saved repository versions before selecting a tenant; follow next_cursor, never guess identity."""
    from app.services.agent_connection import discover_repositories as discover
    return discover(cursor, limit)


@mcp.tool
def inspect_repository_snapshot(tenant_graph: str, expected_revision: str) -> dict:
    """LESSON: Confirm the user's selected saved commit, then pass returned tool_arguments on every call. Does not install an IDE connection."""
    from app.services.agent_connection import inspect_repository_snapshot as inspect_snapshot
    return inspect_snapshot(tenant_graph, expected_revision)


@mcp.tool
@instrument("propose_change_for_approval")
def propose_change_for_approval(tenant_graph: str, expected_revision: str, task_title: str,
        proposed_files: dict[str, str | None], idempotency_key: str, client_id: str='mcp-agent') -> dict:
    """Preview immutable replacements in GRAPH.COPY and wait for a human decision. Never apply code."""
    from app.services.change_lifecycle import propose, ProposalInput
    return propose(ProposalInput(tenant_graph=tenant_graph, expected_revision=expected_revision,
        task_title=task_title, proposed_files=proposed_files, idempotency_key=idempotency_key, client_id=client_id))


@mcp.tool
@instrument("check_proposal_decision")
def check_proposal_decision(tenant_graph: str, expected_revision: str, proposal_id: str) -> dict:
    """Read exact human decision and fresh source/policy guards before external execution."""
    from app.services.change_lifecycle import check
    return check(tenant_graph, expected_revision, proposal_id)


@mcp.tool
@instrument("report_proposal_execution")
def report_proposal_execution(tenant_graph: str, expected_revision: str, proposal_id: str,
        proposal_hash: str, command_executed: str, exit_code: int, output_excerpt: str,
        idempotency_key: str, create_finding_summary: str | None=None) -> dict:
    """Store an UNVERIFIED external report, never claim locally observed execution or run a command."""
    from app.services.change_lifecycle import report, ExecutionInput
    return report(proposal_id, ExecutionInput(tenant_graph=tenant_graph,expected_revision=expected_revision,
        proposal_hash=proposal_hash,command_executed=command_executed,exit_code=exit_code,
        output_excerpt=output_excerpt,idempotency_key=idempotency_key,create_finding_summary=create_finding_summary))


if __name__=='__main__':
    mcp.run()
