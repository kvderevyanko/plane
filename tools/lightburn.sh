#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP="$ROOT/.tools/apps/LightBurn-Linux64-v1.7.08.AppImage"
test -x "$APP" || { echo "Missing $APP" >&2; exit 1; }
mkdir -p "$ROOT/.tools/tmp" "$ROOT/.tools/config"
export TMPDIR="$ROOT/.tools/tmp"
export XDG_CONFIG_HOME="$ROOT/.tools/config"
# FUSE mount is unavailable in this environment; AppImage's official extraction
# mode keeps both executable data and settings under the project root.
exec "$APP" --appimage-extract-and-run "$@"
