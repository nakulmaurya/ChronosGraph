# Quality batch 02 — UI recovery

Stacked on batch 01 (`4d6ef9f`). Branch: `fix/quality-batch-02-ui-recovery`.

Addresses review Q03–Q06 at the reproduced scenario level:
- [x] Reset stale mode, query, source, history selection and tab when switching repository.
- [x] Explicit map failure/loading states, retry and no false “no files” message on failure.
- [x] API network guidance uses the configured endpoint, not a fixed port.
- [x] Lost/expired receipt stops automatic polling and offers explicit status retry, catalog reconciliation and tracking dismissal.
- [x] Sequential rather than overlapping import polls; unmount cancels client requests.
- [x] Dialog accessible name, Escape and focus restoration.
- [x] Recovery actions take priority over disabled new-import fields on narrow screens.
- [x] Record final frontend/build/browser checks and critique boundaries.

Not covered: durable server receipts, cancellation, idempotent POST recovery, default-branch discovery, configurable import origins, complete accessibility audit or full product acceptance.
