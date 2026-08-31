#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ "${1:-}" != "" && "${1:-}" != "--no-open" ]]; then
  echo "Usage: $0 [--no-open]" >&2
  exit 2
fi

"$ROOT/tools/build.sh"
INDEX="$ROOT/generated/previews/index.html"
if [[ "${1:-}" == "--no-open" ]]; then
  echo "Preview gallery updated: $INDEX"
  exit 0
fi

if command -v xdg-open >/dev/null 2>&1; then
  exec xdg-open "$INDEX"
elif command -v gio >/dev/null 2>&1; then
  exec gio open "$INDEX"
else
  echo "Preview gallery updated; open this file manually: $INDEX" >&2
fi
