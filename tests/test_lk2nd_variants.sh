#!/usr/bin/env sh
set -eu

script="${1:-scripts/build_lk2nd_variants.sh}"

output="$(sh "$script" --list)"

printf '%s\n' "$output" | grep -F "generic"
printf '%s\n' "$output" | grep -F "lk2nd-msm8916"
printf '%s\n' "$output" | grep -F "zhihe-various"
printf '%s\n' "$output" | grep -F "ufi001c"
printf '%s\n' "$output" | grep -F "uz801-v3"
printf '%s\n' "$output" | grep -F "jz0145-v33"
printf '%s\n' "$output" | grep -F "uf896"
printf '%s\n' "$output" | grep -F "msm8916-512mb-mtp.dtb"
printf '%s\n' "$output" | grep -F "msm8916-512mb-qrd-skuh.dtb"
