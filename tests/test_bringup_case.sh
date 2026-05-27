#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

python3 "$ROOT/tools/create_bringup_case.py" \
  --device-id thwc-ufi001c \
  --output "$TMPDIR/bringup"

test -f "$TMPDIR/bringup/thwc-ufi001c/README.md"
test -f "$TMPDIR/bringup/thwc-ufi001c/commands.md"
test -d "$TMPDIR/bringup/thwc-ufi001c/logs"
test -d "$TMPDIR/bringup/thwc-ufi001c/firmware"
grep -q "只读优先" "$TMPDIR/bringup/thwc-ufi001c/README.md"
grep -q "edl printgpt" "$TMPDIR/bringup/thwc-ufi001c/commands.md"
