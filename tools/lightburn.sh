#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APP="$ROOT/.tools/LightBurn/LightBurn"
test -x "$APP" || { echo "Missing $APP" >&2; exit 1; }
mkdir -p "$ROOT/.tools/tmp" "$ROOT/.tools/config"
export TMPDIR="${TMPDIR:-$ROOT/.tools/tmp}"
export XDG_CONFIG_HOME="${XDG_CONFIG_HOME:-$ROOT/.tools/config}"
# This is the project-local extracted Linux package. Its bundled Qt libraries
# and qt.conf resolve relative to the executable; no system installation or
# AppImage/FUSE mount is required.
exec "$APP" "$@"
