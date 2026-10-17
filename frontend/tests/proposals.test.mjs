import test from "node:test";
import assert from "node:assert/strict";
import { proposalStatusLabel } from "../src/lib/proposals.ts";
test("proposal labels describe candidate tests without claiming deployed or universally correct code", () => {
  assert.equal(
    proposalStatusLabel("EXECUTED_VERIFIED"),
    "Candidate tests passed",
  );
  assert.equal(
    proposalStatusLabel("EXECUTED_FAILED"),
    "Candidate tests failed",
  );
  assert.equal(proposalStatusLabel("APPROVED"), "Approved for these contents");
});
test("stale proposal labels explain the next review action and retain unknown states", () => {
  assert.match(proposalStatusLabel("STALE_POLICY"), /Rules changed/);
  assert.match(proposalStatusLabel("STALE_SNAPSHOT"), /Code changed/);
  assert.equal(proposalStatusLabel("FUTURE_STATUS"), "FUTURE_STATUS");
});
