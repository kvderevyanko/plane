#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP="$ROOT/.tools/apps/LibreCAD-v2.2.1.5-x86_64.AppImage"
test -x "$APP" || { echo "Missing $APP" >&2; exit 1; }
mkdir -p "$ROOT/.tools/tmp"
export TMPDIR="$ROOT/.tools/tmp"
exec "$APP" --appimage-extract-and-run "$@"
