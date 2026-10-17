/** Human labels preserve the backend status, which remains visible as audit evidence. */
export function proposalStatusLabel(status: string): string {
  return (
    (
      {
        PROPOSED: "Awaiting review",
        APPROVED: "Approved for these contents",
        REJECTED: "Rejected",
        EXECUTED_VERIFIED: "Candidate tests passed",
        EXECUTED_FAILED: "Candidate tests failed",
        STALE_SNAPSHOT: "Code changed — review a new proposal",
        STALE_POLICY: "Rules changed — review a new proposal",
      } as Record<string, string>
    )[status] || status
  );
}
export type OwnershipEvidence = {
  source_document?: { path?: string | null };
  truncated?: boolean;
  declarations?: {
    file_path: string;
    pattern: string;
    source_line: number;
    owner: string | null;
  }[];
};
