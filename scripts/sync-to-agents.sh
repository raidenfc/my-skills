#!/usr/bin/env bash
set -euo pipefail

SRC_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DST_ROOT="${HOME}/.agents/skills"

mkdir -p "$DST_ROOT"

for skill_dir in "$SRC_ROOT"/*; do
  base="$(basename "$skill_dir")"

  # Skip non-skill dirs/files.
  if [[ ! -d "$skill_dir" ]]; then
    continue
  fi
  if [[ "$base" == "scripts" || "$base" == "templates" || "$base" == ".git" ]]; then
    continue
  fi

  # A valid skill folder should contain SKILL.md
  if [[ ! -f "$skill_dir/SKILL.md" ]]; then
    continue
  fi

  dst="$DST_ROOT/$base"
  rm -rf "$dst"
  mkdir -p "$dst"
  cp -R "$skill_dir"/. "$dst"/
  echo "Synced: $base -> $dst"
done

echo "Done."
