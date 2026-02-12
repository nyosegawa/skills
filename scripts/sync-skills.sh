#!/usr/bin/env bash
# Sync skills from this repository to ~/.claude/skills/ via symlinks.
# Run after adding a new skill to skills/ or private_skills/.
#
# Usage: ./scripts/sync-skills.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
TARGET_DIR="$HOME/.claude/skills"

mkdir -p "$TARGET_DIR"

created=0
skipped=0

for src_dir in "$REPO_DIR"/skills "$REPO_DIR"/private_skills; do
  [ -d "$src_dir" ] || continue
  for skill_dir in "$src_dir"/*/; do
    [ -f "$skill_dir/SKILL.md" ] || continue
    name="$(basename "$skill_dir")"
    target="$TARGET_DIR/$name"

    if [ -L "$target" ]; then
      existing="$(readlink "$target")"
      if [ "$existing" = "$skill_dir" ] || [ "$existing" = "${skill_dir%/}" ]; then
        echo "  skip (exists): $name"
        skipped=$((skipped + 1))
        continue
      fi
      echo "  update: $name (relink)"
      rm "$target"
    elif [ -d "$target" ]; then
      echo "  warn: $name is a real directory, skipping (remove it manually)"
      skipped=$((skipped + 1))
      continue
    fi

    ln -s "$skill_dir" "$target"
    echo "  link: $name -> $skill_dir"
    created=$((created + 1))
  done
done

echo "Done. $created linked, $skipped skipped."
