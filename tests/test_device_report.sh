#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"
TMPDIR="$(mktemp -d)"
trap 'rm -rf "$TMPDIR"' EXIT

IDS_JSON="$TMPDIR/qcom-ids.json"
REPORT="$TMPDIR/report.md"

python3 "$ROOT/tools/extract_qcom_ids.py" "$ROOT/tests/samples/sample-msm8916.dts" --pretty > "$IDS_JSON"
python3 "$ROOT/tools/generate_device_report.py" "$ROOT/devices/openstick/ufi-001c.yaml" \
  --ids-json "$IDS_JSON" \
  --devices-dir "$ROOT/devices/openstick" \
  --output "$REPORT"

grep -q "## 候选板型矩阵" "$REPORT"
grep -q "thwc-ufi001c" "$REPORT"
grep -q "thwc-uf896" "$REPORT"
grep -q "直接匹配" "$REPORT"
grep -q "需要人工复核" "$REPORT"
