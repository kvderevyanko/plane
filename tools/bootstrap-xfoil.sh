#!/usr/bin/env bash
# Install the pinned portable XFOIL package below .tools only (no root needed).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="6.99.dfsg+1-3"
URL="https://deb.debian.org/debian/pool/main/x/xfoil/xfoil_${VERSION}_amd64.deb"
SHA256="8bd7d984111901e76f5466c31f30fc12fa8de283ed39a24d9a80f43b1440b6d1"
DEST="$ROOT/.tools/apps/xfoil"
BINARY="$DEST/usr/bin/xfoil"
if [[ -x "$BINARY" ]]; then
  "$BINARY" <<<"QUIT" 2>&1 | grep -q "XFOIL Version 6.99" || { echo "Existing XFOIL binary is not version 6.99: $BINARY" >&2; exit 1; }
  echo "XFOIL $VERSION already available: $BINARY"
  exit 0
fi
command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }
command -v dpkg-deb >/dev/null || { echo "dpkg-deb is required to extract the Debian package" >&2; exit 1; }
TMP="$(mktemp -d "${TMPDIR:-/tmp}/lr1600-xfoil.XXXXXX")"
trap 'rm -rf "$TMP"' EXIT
curl --fail --location --proto '=https' --tlsv1.2 "$URL" --output "$TMP/xfoil.deb"
echo "$SHA256  $TMP/xfoil.deb" | sha256sum --check --status || { echo "XFOIL checksum mismatch" >&2; exit 1; }
mkdir -p "$DEST"
dpkg-deb --extract "$TMP/xfoil.deb" "$DEST"
[[ -x "$BINARY" ]] || { echo "Package did not contain expected XFOIL binary" >&2; exit 1; }
echo "Installed XFOIL $VERSION at $BINARY"
