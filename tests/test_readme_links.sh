#!/usr/bin/env sh
set -eu

ROOT="$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)"

grep -o '](docs/[^)]*)' "$ROOT/README.md" |
while IFS= read -r link; do
	path="${link#*](}"
	path="${path%)}"
	test -f "$ROOT/$path"
done

grep -q "docs/standard-linux-bringup.zh-CN.md" "$ROOT/README.md"
