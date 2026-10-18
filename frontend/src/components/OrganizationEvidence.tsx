import type { OrganizationalEvidence } from "@/lib/types";
/** Render plain evidence, never repository-provided HTML or executable actions. */
export default function OrganizationEvidence({ evidence }: { evidence?: OrganizationalEvidence }) {
  if (!evidence) return null;
  return <section className="wb-card" aria-label="Organizational reasoning evidence">
    <h4>Why this change needs review</h4><p>{evidence.status}</p>
    <p>Explicit pinned declarations, not automatic approval or verified team access.</p>
    {evidence.chains?.map((c,i)=><article key={i}>
      <strong>{c.decision.status} · {c.decision.rule}</strong>
      <p>{c.decision.data_kind} · <code>{c.file_path}</code></p>
      <p>Declared rationale: {c.decision.rationale}</p>
      <p>Required action: {c.decision.required_action}</p>
      {[c.document,c.motivating_incident].map((e,j)=>e ? <details key={j}>
        <summary>{j===0 ? "Decision source" : "Motivating incident"} · {e.path}:{e.start_line}–{e.end_line}</summary>
        <blockquote>{e.excerpt}</blockquote><p>Revision: <code>{e.source_revision}</code></p><p>SHA-256: <code>{e.sha256}</code></p>
      </details> : <p key={j}>Missing {j===0 ? "decision source" : "motivating incident"}.</p>)}
    </article>)}
    <h4>Declared review teams</h4>
    {evidence.review_teams?.length ? evidence.review_teams.map((t,i)=><p key={i}>{t.name} ({t.owner}) · <code>{t.file_path}</code></p>) : <p>No explicit CODEOWNERS-to-team mapping returned.</p>}
    {!!evidence.gaps?.length && <><h4>Evidence gaps — do not infer a definitive requirement</h4><ul>{evidence.gaps.map((g,i)=><li key={i}>{g.reason} {g.file_path}</li>)}</ul></>}
    {evidence.truncated && <p>Bounded evidence; additional results omitted.</p>}
  </section>;
}
