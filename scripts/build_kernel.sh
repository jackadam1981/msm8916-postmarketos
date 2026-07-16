#!/usr/bin/env bash
set -eu

: "${KERNEL_SRC:=/src/kernel}"
: "${OUTPUT:=/build/out}"
: "${JOBS:=$(nproc)}"
: "${PATCH_DIR:=}"          # optional: /repo/patches
: "${KERNEL_REF:=v6.6-msm8916}"     # branch/tag from msm8916-mainline/linux
: "${REPO:=}"               # optional: /repo for patches, dtb, config
: "${DTB:=qcom/msm8916-zhihe-ufi003-mb-v02.dtb}"

echo "=== Building msm8916 mainline kernel ==="
echo "KERNEL_SRC=$KERNEL_SRC  OUTPUT=$OUTPUT  KERNEL_REF=$KERNEL_REF  JOBS=$JOBS"
echo "DTB=$DTB"

# 鈹€鈹€ 1. Clone kernel source 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
if [ ! -d "$KERNEL_SRC/.git" ]; then
    git clone --depth=1 -b "$KERNEL_REF" \
        https://github.com/msm8916-mainline/linux.git "$KERNEL_SRC"
fi

# 鈹€鈹€ 2. Apply patches 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
if [ -n "$PATCH_DIR" ] && [ -d "$PATCH_DIR" ]; then
    echo "Applying kernel patches from $PATCH_DIR ..."
    for p in "$PATCH_DIR"/linux-msm8916-*.patch; do
        [ -f "$p" ] || continue
        echo "  $(basename $p)"
        git -C "$KERNEL_SRC" am -q "$p" 2>/dev/null || {
            echo "  WARN: patch failed (applying with git apply)"
            git -C "$KERNEL_SRC" apply "$p" 2>/dev/null || true
        }
    done
fi

# 鈹€鈹€ 3. Configure 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
make -C "$KERNEL_SRC" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- defconfig

# 鈹€鈹€ 4. Build kernel + dtbs 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
make -C "$KERNEL_SRC" -j"$JOBS" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- Image.gz dtbs

# 鈹€鈹€ 5. Collect outputs 鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€鈹€
mkdir -p "$OUTPUT"
cp "$KERNEL_SRC/arch/arm64/boot/Image.gz" "$OUTPUT/"
cp "$KERNEL_SRC/arch/arm64/boot/dts/$DTB" "$OUTPUT/msm8916-zhihe-ufi003-mb-v02.dtb" 2>/dev/null || \
    cp "$KERNEL_SRC/arch/arm64/boot/dts/qcom/"*.dtb "$OUTPUT/" 2>/dev/null || true

# Build kernel modules
make -C "$KERNEL_SRC" -j"$JOBS" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- modules
mkdir -p "$OUTPUT/modules"
make -C "$KERNEL_SRC" ARCH=arm64 CROSS_COMPILE=aarch64-linux-gnu- \
    INSTALL_MOD_PATH="$OUTPUT/modules" modules_install

echo "=== Kernel build complete ==="
ls -lh "$OUTPUT/"
