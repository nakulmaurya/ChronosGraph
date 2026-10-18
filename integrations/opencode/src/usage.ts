/** OpenCode 1.19.3: completed step counters; message cost is reconciliation only. */
import type { AssistantMessage, StepFinishPart } from "@opencode-ai/sdk";
export function stepUsage(p: StepFinishPart, info?: AssistantMessage) {
  return {
    session_id: p.sessionID,
    message_id: p.messageID,
    part_id: p.id,
    provider_id: info?.providerID ?? null,
    model_id: info?.modelID ?? null,
    input_tokens: p.tokens.input,
    output_tokens: p.tokens.output,
    reasoning_tokens: p.tokens.reasoning,
    cache_read_tokens: p.tokens.cache.read,
    cache_write_tokens: p.tokens.cache.write,
    cost: p.cost,
    basis: "OPENCODE_COMPLETED_STEP_PART",
    provider_request_id: null,
    count_semantics:
      "OpenCode normalized completed-step categories; overlap/billing/provider retries unknown",
  };
}
export function messageCost(m: AssistantMessage) {
  return {
    message_id: m.id,
    provider_id: m.providerID,
    model_id: m.modelID,
    cost: m.cost,
    completed_at_ms: m.time.completed ?? null,
    error_completion: !!m.error,
    basis: "OPENCODE_MESSAGE_CUMULATIVE_COST_RECONCILIATION_ONLY",
  };
}
