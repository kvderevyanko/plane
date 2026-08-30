#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON="$ROOT/.tools/conda/lr1600-cad/bin/python"
if [[ ! -x "$PYTHON" ]]; then
  # A pre-existing isolated environment is used only while the project-local
  # prefix is being provisioned; no system Python is ever selected.
  PYTHON="/home/kirill/miniforge3/envs/lr1600-cad/bin/python"
fi
if [[ ! -x "$PYTHON" ]]; then
  echo "CadQuery environment is missing; see environment/README.md" >&2
  exit 1
fi
export MPLCONFIGDIR="$ROOT/.tools/matplotlib"
mkdir -p "$MPLCONFIGDIR"
exec "$PYTHON" "$@"
