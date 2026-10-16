# Final verification order

Executed under `/tmp/chronosgraph-t09-native-verification.lock` using Linux flock.

- Backend START: 2026-10-16T18:57:53Z
- Backend END: 2026-10-16T18:58:23Z — 123 passed in 28.61 s
- Browser START: 2026-10-16T18:58:24Z
- Browser END: 2026-10-16T18:59:38Z — 24 legacy + 10 workbench passed
- Four-tenant Decision ledger restored exactly; see policy-restoration.json.

A previous overlapping run failed and is retained separately. No native test
assertions were weakened to make final gates pass. Future sessions must also use
the same verification lock; it cannot serialize an uncoordinated external writer.
