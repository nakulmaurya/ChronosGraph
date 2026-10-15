import type { Investigation, Result } from "./types";
export function comparison(result: Result, cold: Investigation | null) {
  if (result.kind === "audit")
    return {
      left: `Without Graph · 1-Hop: Missed ${result.data.blind_agent_comparison.missed_downstream_count} multi-hop files`,
      right: `With FalkorDB GRAPH.COPY · 3-Hop: ${result.data.impacted_files.length} files & ${result.data.impacted_functions.length} functions traced · selective pytest ready`,
    };
  if (result.kind === "brain")
    return {
      left: result.data.blind_agent_comparison.obsolete_rule_followed
        ? "Without Graph · Oldest-Doc: Returns SUPERSEDED rule"
        : "Without Graph · Oldest-Doc: No superseded rule selected",
      right: result.data.active_decisions.length
        ? "With FalkorDB Two-Clock Lineage: Returns ACTIVE rule & preserves history"
        : "With FalkorDB Two-Clock Lineage: No ACTIVE rule found",
    };
  const run = result.data;
  const baseline =
    cold ?? (run.execution_mode === "cold_multi_agent" ? run : null);
  const dead =
    baseline?.agent_handoff_log.filter((x) => x.dead_end === true).length ?? 0;
  const left = baseline
    ? `Without Graph · Cold Exploration: ${baseline.total_steps_executed} actions (${dead} dead ends) · ${baseline.duration_ms.toFixed(2)} ms`
    : "Cold exploration: measurement unavailable";
  if (run.execution_mode !== "compiled_playbook")
    return {
      left,
      right: `With shortestPath Compiled: ${run.pruned_golden_steps} verified actions + /compact snapshot · run replay to measure`,
    };
  const reduction =
    baseline && baseline.total_steps_executed > 0
      ? (100 * (baseline.total_steps_executed - run.total_steps_executed)) /
        baseline.total_steps_executed
      : null;
  const replayDead = run.agent_handoff_log.filter(
    (x) => x.dead_end === true,
  ).length;
  return {
    left,
    right: `With shortestPath Replay: ${run.total_steps_executed} verified actions (${replayDead} dead ends${reduction === null ? "" : `, ${reduction.toFixed(0)}% fewer actions`}) · ${run.duration_ms.toFixed(2)} ms (${run.latency_speedup_factor.toFixed(3)}×)`,
  };
}
