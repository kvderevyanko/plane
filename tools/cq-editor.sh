#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNNER="$(find "$ROOT/.tools/apps/cq-editor-0.7.0" -type f -name run.sh -print -quit 2>/dev/null || true)"
test -n "$RUNNER" || { echo "CQ-editor 0.7.0 is not installed yet." >&2; exit 1; }
cd "$(dirname "$RUNNER")"
exec ./run.sh "$@"
