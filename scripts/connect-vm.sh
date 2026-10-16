#!/usr/bin/env bash
# Run on your laptop, not inside the GCP VM.
set -euo pipefail
if ! command -v gcloud >/dev/null 2>&1; then
  printf '%s\n' 'Install Google Cloud CLI first: https://cloud.google.com/sdk/docs/install' >&2
  exit 1
fi
if [[ -z "$(gcloud auth list --filter=status:ACTIVE --format='value(account)')" ]]; then
  gcloud auth login
fi
printf '%s\n' \
  'Connecting to ChronosGraph. Keep this terminal open; Ctrl-C closes the tunnel.' \
  'After SSH connects, open http://127.0.0.1:3000' \
  'API docs: http://127.0.0.1:8001/docs' \
  'If a local port is already in use, close its existing app/tunnel and retry.'
exec gcloud compute ssh nakulmaurya13579@instance-falkordb-hackathon \
  --project=amazon-ml-509907 \
  --zone=us-central1-a \
  -- -N -o ExitOnForwardFailure=yes -o ServerAliveInterval=30 \
  -L 127.0.0.1:3000:127.0.0.1:3000 \
  -L 127.0.0.1:8001:127.0.0.1:8001
