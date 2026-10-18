#!/usr/bin/env python3
"""Portable, offline reconciliation of sealed Task 9 public evidence.

Does not launch models, execute imported scripts/patches, or contact services.
Requires pandas in the review environment; not an application dependency.
"""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path

import pandas as pd


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_text())


def analyze(payload):
    original = load(payload / "comparison-results.json")
    protocol = load(payload / "frozen/protocol.json")
    manifest = load(payload / "SHA256-MANIFEST.json")
    assert len(manifest) == 53
    for name, expected in manifest.items():
        path = (payload / name).resolve()
        assert path.is_relative_to(payload.resolve())
        assert digest(path) == expected, name
    assert digest(payload / "frozen/protocol.json") == original["provenance"]["protocol_sha256"]
    for name, expected in protocol["acceptance_sha256"].items():
        assert digest(payload / "frozen" / name) == expected

    frame = pd.read_csv(payload / "trials.csv", keep_default_na=False)
    assert len(frame) == 4 and not frame.duplicated("trial").any()
    assert not frame.duplicated(["task", "condition"]).any()
    assert frame["attempts"].eq(1).all()
    rows = []
    for recorded in frame.to_dict("records"):
        n = int(recorded["trial"])
        root = payload / f"trial-{n:02}"
        receipt = load(root / "receipt.json")
        review = load(root / "manual-review.json")
        trace = load(root / "tool-trace.json")
        steps = receipt["completed_steps"]
        assert len({x["id"] for x in steps}) == len(steps)
        usage = {
            key: sum(
                x["tokens"]["cache"][key.removeprefix("cache_")]
                if key.startswith("cache_") else x["tokens"][key]
                for x in steps
            )
            for key in ["input", "output", "reasoning", "cache_read", "cache_write"]
        }
        assert usage == receipt["usage_categories"]
        assert all(recorded[k] == v for k, v in usage.items())
        assert all(exit_code == 0 for exit_code in receipt["independent_checks"].values())
        assert receipt["verification_process_exit"] == 0
        completion = receipt["observed_completion"]
        last = completion["model_end_at"] / 1000 - receipt["started_at"]
        terminal = completion["observed_at"] - receipt["started_at"]
        assert abs(last - recorded["prompt_to_last_message_seconds"]) < 1e-6
        assert abs(terminal - recorded["prompt_to_terminal_observation_seconds"]) < 1e-6
        assert receipt["candidate_digest"] == review["candidate_digest"]
        assert receipt["provider_retry_usage"] == "UNKNOWN"
        assert len(trace) == len(receipt["tools"]) == recorded["tool_calls"]
        assert sum(t["status"] == "error" for t in trace) == recorded["tool_errors"]
        assert sum(t["tool"] == "read" for t in trace) == recorded["read_attempts"]
        for filename, column in [("acceptance.log", "external_passed"),
                                 ("existing-regressions.log", "regression_passed")]:
            text = (root / filename).read_text()
            assert int(re.findall(r"(\d+) passed", text)[-1]) == recorded[column]
        expected_terminal = (
            "PERMISSION_STOP_NO_FINAL_RESPONSE"
            if completion["interruption_reason"] else "FINAL_RESPONSE"
        )
        assert recorded["native_terminal"] == review["native_completion"] == expected_terminal
        assert protocol["order"][n - 1] == {
            "task": recorded["task"], "condition": recorded["condition"]
        }
        mcp = sum(t["tool"].startswith("chronosgraph_") for t in trace)
        rows.append({
            **recorded, "mcp_calls": mcp,
            "candidate_digest": receipt["candidate_digest"],
            "repository_conventions": review["repository_conventions"],
            "static_typecheck": review["static_typecheck"],
            "independent_checks_exit": receipt["independent_checks"],
        })

    # Independent check: CSV parsed without pandas, plus the original evidence
    # object. The headline counts and input values must match all three paths.
    with (payload / "trials.csv").open(newline="") as handle:
        csv_rows = list(csv.DictReader(handle))
    summary = {
        "attempts": len(rows),
        "native_final_responses": sum(r["native_terminal"] == "FINAL_RESPONSE" for r in rows),
        "permission_stopped": sum(r["native_terminal"].startswith("PERMISSION_STOP") for r in rows),
        "frozen_runtime_check_passes": sum(all(v == 0 for v in r["independent_checks_exit"].values()) for r in rows),
        "convention_changes_requested": sum(r["repository_conventions"] == "CHANGES_REQUESTED" for r in rows),
    }
    assert summary["native_final_responses"] == sum(r["native_terminal"] == "FINAL_RESPONSE" for r in csv_rows)
    assert summary["permission_stopped"] == sum(r["native_terminal"].startswith("PERMISSION_STOP") for r in csv_rows)
    assert all(original["summary"][k] == v for k, v in summary.items())
    pairs = []
    for task in protocol["tasks"]:
        selected = [r for r in rows if r["task"] == task["id"]]
        a = next(r for r in selected if r["condition"] == "ordinary")
        b = next(r for r in selected if r["condition"] == "graph")
        delta = b["input"] - a["input"]
        independent = {r["condition"]: int(r["input"]) for r in csv_rows if r["task"] == task["id"]}
        assert delta == independent["graph"] - independent["ordinary"]
        pairs.append({
            "task": task["id"], "ordinary_trial": a["trial"], "graph_trial": b["trial"],
            "input_difference_graph_minus_ordinary": delta,
            "input_graph_higher": delta > 0,
            "terminal_wall_difference_seconds": b["prompt_to_terminal_observation_seconds"] - a["prompt_to_terminal_observation_seconds"],
            "last_message_wall_difference_seconds": b["prompt_to_last_message_seconds"] - a["prompt_to_last_message_seconds"],
            "causal_effect": "NOT_IDENTIFIED",
        })
    assert all(p["input_graph_higher"] for p in pairs)
    assert {p["terminal_wall_difference_seconds"] > 0 for p in pairs} == {True, False}
    chart_order = ["structured-invalid-characters", "has-tool-lookup"]
    chart = {
        "version": 1, "form": "categorical-bars", "mode": "grouped",
        "title": "Graph-enabled trials recorded more input in both task pairs",
        "aside": "Reported input tokens only; one attempt per cell, no causal or billing inference",
        "labels": ["Invalid-character diagnostics", "has_tool lookup"],
        "axis": {"zero": True},
        "colorMap": {"Ordinary": "blue", "Graph-enabled": "purple"},
        "series": [
            {"label": label, "valueKind": "count", "role": role,
             "data": [next(r["input"] for r in rows if r["task"] == task and r["condition"] == condition)
                      for task in chart_order]}
            for label, role, condition in [("Ordinary", "base", "ordinary"),
                                           ("Graph-enabled", "subject", "graph")]
        ],
    }
    return {
        "schema_version": 1,
        "headline": "Runtime checks passed in all four cells, but only two native turns finished; no graph advantage established.",
        "provenance": {**original["provenance"], "portable_input": "sealed sanitized payload only",
                       "original_payload_manifest_sha256": digest(payload / "SHA256-MANIFEST.json")},
        "profile_resolution": original["profile_review"],
        "validation": {"original_payload_hashes_checked": 53, "csv_rows": 4,
                       "receipts_steps_trace_logs_csv_original_results_reconciled": True,
                       "independent_csv_headline_and_pair_check": True},
        "summary": summary, "trials": rows, "pairs": pairs,
        "comparison_plan": [
            {"grain": "attempt", "population": "all four cells", "unit": "outcome",
             "finding": "Two final responses and two permission stops despite passing selected runtime checks",
             "disposition": "table", "reason": "Exact heterogeneous failure states must not be flattened into a success rate."},
            {"grain": "task × mode, one attempt each", "population": "both task pairs",
             "unit": "reported input tokens", "finding": "Graph input is higher in each pair",
             "disposition": "chart", "reason": "Grouped bars preserve both pair magnitudes without pooling; no causal or billable interpretation."},
            {"grain": "attempt", "population": "all four cells", "unit": "seconds",
             "finding": "Wall direction differs by task",
             "disposition": "table", "reason": "Exact wall clocks and permission-stopped endpoints need explicit qualification; no speedup estimate."},
            {"grain": "attempt", "population": "all four cells", "unit": "separate exported token categories and tool counts",
             "finding": "Cache and tool accounting do not establish savings",
             "disposition": "table", "reason": "Categories may overlap, retries unknown; preserve raw measures without fabricated totals."}
        ],
        "limitations": original["limitations"],
        "chart_spec": chart,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--payload", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True, help="New output directory")
    args = parser.parse_args()
    assert not args.out.exists(), "Use a fresh output directory"
    evidence = analyze(args.payload)
    args.out.mkdir(parents=True)
    (args.out / "analysis.json").write_text(json.dumps(evidence, indent=2) + "\n")
    (args.out / "input-chart-spec.json").write_text(json.dumps(evidence["chart_spec"], indent=2) + "\n")
    pd.DataFrame(evidence["trials"]).to_csv(args.out / "reconciled-trials.csv", index=False)
    print(json.dumps({"validation": evidence["validation"], "summary": evidence["summary"],
                      "pairs": evidence["pairs"]}, indent=2))


if __name__ == "__main__":
    main()