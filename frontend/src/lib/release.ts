/** Metadata only: matched operator declarations are not a code attestation. */
export function pinnedCommit(value: unknown): string | null {
  return typeof value === "string" && /^[0-9a-f]{40}$/.test(value) ? value : null;
}
export function buildPairing(frontend: unknown, backend: unknown): "MATCHED_DECLARATIONS" | "MISMATCH" | "UNRECORDED" {
  const a=pinnedCommit(frontend),b=pinnedCommit(backend);
  return !a || !b ? "UNRECORDED" : a===b ? "MATCHED_DECLARATIONS" : "MISMATCH";
}
