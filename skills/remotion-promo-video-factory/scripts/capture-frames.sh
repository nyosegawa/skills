#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <composition-id> <output-dir> [frame-list] [project-dir]"
  echo "Example: $0 ProductTeaser captures \"0,60,72,100,300,520,840\" ./video"
  exit 1
fi

COMPOSITION_ID="$1"
OUTPUT_DIR="$2"
FRAME_LIST="${3:-0,20,60,72,100,160,220,300,360,430,520,580,650,720,780,840}"
PROJECT_DIR="${4:-.}"

mkdir -p "${OUTPUT_DIR}"

IFS=',' read -r -a FRAMES <<< "${FRAME_LIST}"
for frame in "${FRAMES[@]}"; do
  frame_trimmed="$(echo "$frame" | xargs)"
  out_file="${OUTPUT_DIR}/frame-$(printf "%03d" "${frame_trimmed}").png"
  (
    cd "${PROJECT_DIR}"
    npx remotion still "${COMPOSITION_ID}" "${out_file}" --frame="${frame_trimmed}"
  )
  echo "Captured ${out_file}"
done

echo "Done. Captured ${#FRAMES[@]} frames in ${OUTPUT_DIR}"
