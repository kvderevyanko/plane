#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP="$ROOT/.tools/apps/FreeCAD_1.1.3-Linux-x86_64-py311.AppImage"
test -x "$APP" || { echo "Missing or unverified $APP" >&2; exit 1; }
mkdir -p "$ROOT/.tools/tmp" "$ROOT/.tools/config/freecad"
export TMPDIR="$ROOT/.tools/tmp"
export FREECAD_USER_HOME="$ROOT/.tools/config/freecad"
exec "$APP" --appimage-extract-and-run "$@"
