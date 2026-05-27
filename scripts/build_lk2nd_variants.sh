#!/usr/bin/env sh
set -eu

LK2ND_DIR="${LK2ND_DIR:-/home/jack/work/msm8916-standard-linux/third_party/lk2nd}"
OUT_DIR="${OUT_DIR:-/home/jack/work/msm8916-standard-linux/out/lk2nd-variants}"
TOOLCHAIN_PREFIX="${TOOLCHAIN_PREFIX:-arm-none-eabi-}"
JOBS="${JOBS:-$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo 1)}"
BUILD_DATE="${BUILD_DATE:-$(date +%Y%m%d)}"

variants() {
	cat <<'EOF'
generic|lk2nd-msm8916|||img|Generic lk2nd MSM8916 QCDT image
zhihe-various|lk1st-msm8916|msm8916-512mb-mtp.dtb|zhihe,various|mbn|Generic 512MB MTP bucket for UFI_001B/C, UFI003_MB_V02, MF601
ufi001c|lk1st-msm8916|msm8916-512mb-mtp.dtb|thwc,ufi001c|mbn|Fixed compatible for UFI-001B/C
uz801-v3|lk1st-msm8916|msm8916-512mb-mtp.dtb|yiming,uz801-v3|mbn|Fixed compatible for UZ801 v3.0
jz0145-v33|lk1st-msm8916|msm8916-512mb-mtp.dtb|xiaoxun,jz0145-v33|mbn|Fixed compatible for JZ0145 v33
uf896|lk1st-msm8916|msm8916-512mb-qrd-skuh.dtb|thwc,uf896|mbn|Fixed compatible for UF896
EOF
}

list_variants() {
	printf '%-16s %-15s %-28s %-24s %s\n' "name" "target" "bundle_dtb" "compatible" "description"
	variants | while IFS='|' read -r name target bundle compatible ext description; do
		: "$ext"
		printf '%-16s %-15s %-28s %-24s %s\n' "$name" "$target" "${bundle:-auto-qcdt}" "${compatible:-auto-match}" "$description"
	done
}

usage() {
	cat <<EOF
Usage: $0 [--list] [--variant NAME]

Environment:
  LK2ND_DIR=$LK2ND_DIR
  OUT_DIR=$OUT_DIR
  TOOLCHAIN_PREFIX=$TOOLCHAIN_PREFIX
  JOBS=$JOBS
  BUILD_DATE=$BUILD_DATE
EOF
}

build_one() {
	name="$1"
	target="$2"
	bundle="$3"
	compatible="$4"
	ext="$5"
	description="$6"

	commit="$(git -C "$LK2ND_DIR" rev-parse --short HEAD)"
	out_name="${name}-${target}-${BUILD_DATE}.${ext}"
	build_dir="$LK2ND_DIR/build-$target"

	printf '\n==> Building %s: %s\n' "$name" "$description"
	rm -rf "$build_dir"

	if [ -n "$bundle" ]; then
		make -C "$LK2ND_DIR" -j"$JOBS" TOOLCHAIN_PREFIX="$TOOLCHAIN_PREFIX" \
			LK2ND_BUNDLE_DTB="$bundle" LK2ND_COMPATIBLE="$compatible" "$target"
	else
		make -C "$LK2ND_DIR" -j"$JOBS" TOOLCHAIN_PREFIX="$TOOLCHAIN_PREFIX" "$target"
	fi

	mkdir -p "$OUT_DIR"
	if [ "$ext" = "img" ]; then
		cp "$build_dir/lk2nd.img" "$OUT_DIR/$out_name"
	else
		cp "$build_dir/emmc_appsboot.mbn" "$OUT_DIR/$out_name"
	fi
	sha256sum "$OUT_DIR/$out_name"
	printf '%s|%s|%s|%s|%s|%s|%s\n' "$out_name" "$name" "$target" "${bundle:-auto-qcdt}" "${compatible:-auto-match}" "$commit" "$description" >> "$OUT_DIR/manifest.psv"
}

selected=""
while [ "$#" -gt 0 ]; do
	case "$1" in
		--list)
			list_variants
			exit 0
			;;
		--variant)
			shift
			if [ "$#" -eq 0 ]; then
				echo "--variant requires a name" >&2
				exit 2
			fi
			selected="$1"
			;;
		--help|-h)
			usage
			exit 0
			;;
		*)
			echo "Unknown argument: $1" >&2
			usage >&2
			exit 2
			;;
	esac
	shift
done

if [ ! -d "$LK2ND_DIR/.git" ]; then
	echo "LK2ND_DIR is not a git checkout: $LK2ND_DIR" >&2
	exit 1
fi

mkdir -p "$OUT_DIR"
printf 'file|name|target|bundle_dtb|compatible|lk2nd_commit|description\n' > "$OUT_DIR/manifest.psv"

found=0
variants | while IFS='|' read -r name target bundle compatible ext description; do
	if [ -z "$selected" ] || [ "$selected" = "$name" ]; then
		found=1
		build_one "$name" "$target" "$bundle" "$compatible" "$ext" "$description"
	fi
done

if [ -n "$selected" ] && ! variants | cut -d'|' -f1 | grep -Fx "$selected" >/dev/null; then
	echo "Unknown variant: $selected" >&2
	exit 2
fi
