# C/D/E/G checkpoint — native and live acceptance

This continues A/B commit d86db9a. Not a final release; worker handoff and comparison remain pending.

## Implemented

- Complete text candidate manifest/digest, clean start, exact changed/add/delete capture, immediate recapture and omitted/mismatched-body refusal. Initial overlay remains distinct. Generated proposals are labelled separately. Observation is local-plugin reported, not attested. Python-only proposal/runner scope remains; unsupported source files explicitly refuse rather than disappear.
- Bounded analysis scope before presentation, exact target refusal, candidate discovery, explicit expansion. Deduplicate mandatory rules before final budget; the internal locator no longer trims graph details against duplicate rules first. Serialized block measurement remains distinct from pack response.
- Completed-step identity/counters; message cumulative cost reconciles, never adds twice. Legacy fields/readability retained. Late usage does not overwrite idle lifecycle status. Provider retries remain unknown; no billing or savings claim.
- Bounded decision/excerpt/hash references validate current evidence and source relevance, with a no-validated-citations state. New snapshots pin organization source SHA256 values; old snapshots require refresh, not silent enrichment. UI labels separate idle, approval and verification.

## Results

PASS: native isolated FalkorDB suite, **399 passed**, 137.26 seconds, after budget/lifecycle fixes. Disposable database copied four source corpora read-only; no shared database tests. The earlier 391/392/396 results are historical, not additive. Retained failed development attempts identified a test-selection assumption and missing non-Python source SHA pin; both corrected before this run.

PASS: actual OpenCode 1.19.3 / DeepSeek V4.1 Flash Free context turn with the owned API interrupted immediately after pack response. Eight durable pending receipts survived and drained after recovery; first turn correctly used ADR-002. Follow-up turn did not append a second context block. Actual process restart and `/compact` completed; a post-compaction answer retained the governed contract.

PASS: independent supported session export versus persisted completed-step totals after multiple messages and compaction: input 24,267; output 1,307; reasoning 342; cache-read 27,008; cache-write 0. Export and stored cost both 0. One persisted first-message context block: 10,944 UTF-8 bytes. Pending 0, blocked 0. Retry usage unknown. This is integration/usage acceptance, not successful coding-task evidence. The live API was started before the late-idle display fix, so that export's status remains BOUND_NOT_COMPLETED; native regression verifies the corrected display computation.

The initial restart capture alone did not establish a new answer; the subsequent compact/postcompact turn and independent export establish continued session use. Raw private exports contain prompts/reasoning and stay outside release evidence; metadata-only receipts are retained.

## Migration and boundaries

Event v1 retry digests remain unchanged; v2 completed-step events are additive. Local v1 state backs up before v2 migration; old delivered flags are not persistence confirmation. No database rewrite or pending approval migration. New proposal hashes include candidate and evidence references; old immutable proposals keep their historical hashes. Citation source pins require a newly indexed snapshot. No OS snapshot, provider consumption acknowledgement, comprehensive dependency coverage, auth or security sandbox is claimed.
