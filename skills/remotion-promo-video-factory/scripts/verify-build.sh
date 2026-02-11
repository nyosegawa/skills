#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="${1:-.}"

cd "${PROJECT_DIR}"

echo "[1/3] Typecheck"
npx tsc --noEmit

echo "[2/3] MP4 render"
npm run -s build

if npm run -s | rg -q "^  build:gif"; then
  echo "[3/3] GIF render"
  npm run -s build:gif
else
  echo "[3/3] GIF render skipped (build:gif not found)"
fi

echo "Verification completed."

