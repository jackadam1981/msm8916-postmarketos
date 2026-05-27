#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
OUT="$(python3 "$ROOT/tools/validate_device_metadata.py" \
  "$ROOT/devices/openstick" \
  --variants-script "$ROOT/scripts/build_lk2nd_variants.sh")"

printf '%s\n' "$OUT" | grep -q "Validated 6 device metadata files"
printf '%s\n' "$OUT" | grep -q "All lk2nd compatibles are covered by build variants"
