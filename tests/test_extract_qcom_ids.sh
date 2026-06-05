#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

python3 "$ROOT/tools/extract_qcom_ids.py" "$ROOT/tests/samples/sample-msm8916-multi-id.dts" --pretty > "$TMPDIR/ids.json"

python3 - "$TMPDIR/ids.json" <<'PY'
import json
import sys

data = json.loads(open(sys.argv[1], encoding="utf-8").read())
assert data["qcom,msm-id"] == [[206, 0], [248, 0], [249, 0], [250, 0]]
assert data["qcom,board-id"] == [[8, 256]]
assert data["qcom,pmic-id"] == [[65545, 65546, 0, 0]]
PY
