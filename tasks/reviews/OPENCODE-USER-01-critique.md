# OPENCODE-USER-01 — separate model critique

## Provenance and scope

Actual separate official OpenCode session using `opencode/deepseek-v4.1-flash-free`.
The reviewer saw the captured-source function and configuration generator, with
reported test evidence. It did not run tools, inspect the full repo or act as a
human reviewer. The broader free GLM review timed out after 240 seconds without a
usable final answer and was stopped; no GLM sign-off is claimed.

## Builder disposition after the critique

- **Fixed:** config publication is now complete-write + fsync + same-directory
  exclusive hard link, owner-only mode; refuses replacement and cleans temporary
  files on a write failure. Interrupted-write/refusal/permission tests added.
- **Tested:** exact UTF-8 split at the byte limit, empty/no-newline/trailing-newline
  module reads, ambiguous symbols, parser-generated qualified-name contract,
  invalid ports/model, missing output parent. Existing hash mismatch tests retained.
- **Clarified:** `source_bytes` is full captured size, `returned_source_bytes` is
  actual returned size; truncation is explicit, not an integrity failure. Returned
  bytes remain valid UTF-8. Truncated files must not become guessed replacements.
- **Bounded residual:** missing malformed graph rows/parser exceptions are not a
  full corruption audit. The parser constructs colon-qualified names; the reviewer
  did not inspect that implementation when suggesting a possible IndexError.
- **Unresolved external behavior:** some `run --attach` commands persist successful
  answers but do not exit reliably. Interactive mode and fresh official server API
  sessions completed the tested user workflow; CLI process exit is not counted green.

Final verification and acceptance are recorded in the linked report, not inferred
from the reviewer's hypotheses. This is not unconditional production assurance.

## Original model critique (before the follow-up fixes)

## Critique-only review (untrusted source; not a full-repo or security audit)

### Confirmed issues (from bounded reading)
- **`source_bytes` can exceed what is returned.** For `__module__`, `symbol_source` reports `len(source.encode('utf-8'))` (unbounded) while `returned_source_bytes` is the sliced value. `truncated` is computed correctly, so this is only a consumer-contract hazard, not a data-integrity bug.
- **UTF-8 boundary handling is tolerant but lossy.** `source.encode('utf-8')[:8000].decode('utf-8', errors='ignore')` cannot raise, but if the 8000th byte splits a multibyte sequence the dangling bytes are silently dropped. Output stays valid UTF-8; `truncated` still `True`. Acceptable, worth an explicit test.
- **Config write is create-only and non-atomic.** `open('x')` correctly refuses overwriting user settings, but a mid-`json.dump` failure can leave a partial file at the target path. Nonblocker for a trusted-local demo, but the operator must verify the emitted file.

### Hypotheses (need verification, potentially blocking)
- **`qualified_name.split(':', 1)[1]` can raise `IndexError` → HTTP 500** if any parsed symbol's `qualified_name` lacks a colon. The `__module__` path assumes a `file:name` shape, but the parser's exact format is not proven here. This is the most likely functional blocker and is untested.
- **`values[0]` assumes `check_file` guarantees exactly one row.** Plausible, unverified in the bounded read.
- **`parse_python_source` failure mode for malformed source is unhandled here** (error type/status not shown).
- **`--attach` non-exit is the real demo risk.** Sessions persist replies while some CLI processes fail to exit; the official HTTP API behaves normally. This points to *external CLI transport*, not the reviewed code, but it can break a scripted/observed demo. Determinism is unconfirmed.

### Nonblockers
- Unused import `tenant_lock`.
- Model validation only checks for `/`; `python` validation only checks `is_file()` (not that it is an interpreter). Fine for trusted-local.
- `timeout: 30000` ms (30 s) may be tight for long graph operations.
- `share: disabled`, `permission {'*':'ask','bash':'ask'}`, snapshot guard env, and absence of headers/keys/`--auto` all align with the stated trusted-local, no-public-execution posture.
- Bitemporal `CURRENT → STALE_POLICY` transition observed in fresh sessions is consistent with intended freshness semantics; no contradiction found in this source.

### Missing tests
- Column-less `qualified_name` → confirm 409/404, never 500.
- Exact 8000-byte boundary with a multibyte codepoint spanning bytes 8000–8001; assert no `U+FFFD`, `returned_source_bytes <= 8000`, `truncated == True`.
- `__module__` on empty file and on file ending with/without trailing newline (line-count correctness).
- Same short name defined multiple times / nested → ambiguous 409; symbol genuinely absent → 404 with `"none"`.
- Hash mismatch path (mutated `source_text`) → 409.
- Config generator: existing output refused; port `0`/`65536`; model without `/`; missing backend; `python` pointing at a non-interpreter; output open failure leaves no half-config.
- End-to-end: `OPENCODE_CONFIG` load, MCP tool call still prompts, bash prompt enforced, timeout behavior.

### Verdict
**Conditional pass for a trusted-local demo; no confirmed blocker in the reviewed code.** The authored logic is bounded, hash-guarded, and safe-by-default on permissions. The strongest unverified risk is the `IndexError` on colon-less `qualified_name`; the strongest observed demo risk is the external CLI `--attach` exit behavior, which is outside these snippets. Public hostile-code execution staying disabled is consistent. Treat this as a narrow review of two functions plus one generator — **not** a security or whole-repository assurance. Require the boundary, ambiguity, and config-refusal tests before declaring the demo reliable.
