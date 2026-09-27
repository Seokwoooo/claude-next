#!/usr/bin/env bash
# Symlinks ~/.claude/skills/next to skills/next in this repo, so `git pull` keeps it up to date.
# Uninstall: ./install.sh --uninstall
set -euo pipefail

src="$(cd "$(dirname "$0")" && pwd)/skills/next"
dest="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/next"

if [[ "${1:-}" == "--uninstall" ]]; then
  if [[ -L "$dest" && "$(readlink "$dest")" == "$src" ]]; then
    rm "$dest"
    echo "Removed: $dest"
  else
    echo "Not a link created by this repo, left untouched: $dest" >&2
    exit 1
  fi
  exit 0
fi

if [[ -L "$dest" && "$(readlink "$dest")" == "$src" ]]; then
  echo "Already installed: $dest -> $src"
  exit 0
fi

if [[ -e "$dest" || -L "$dest" ]]; then
  echo "A different 'next' skill already exists: $dest" >&2
  echo "Move or remove it yourself, then run this again." >&2
  exit 1
fi

mkdir -p "$(dirname "$dest")"
ln -s "$src" "$dest"
echo "Installed: $dest -> $src"
echo "If /next doesn't show up in a session that was already open, start a new session."
