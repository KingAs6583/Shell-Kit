#!/bin/bash
# ─────────────────────────────────────────────────────────────
# history-clean.sh — Deduplicate ~/.bash_history safely
#
# Keeps the LAST (most recent) occurrence of each command.
# Creates a backup before modifying.
#
# Usage:
#   bash ~/.local/bin/history-clean.sh    (or just: hclean)
#
# Cron (weekly Sunday 3 AM):
#   0 3 * * 0 ~/.local/bin/history-clean.sh
# ─────────────────────────────────────────────────────────────

set -euo pipefail

HISTFILE="${HOME}/.bash_history"
BACKUP="${HOME}/.bash_history.bak"

# Colors
_GREEN='\033[0;32m'
_YELLOW='\033[0;33m'
_RED='\033[0;31m'
_CYAN='\033[0;36m'
_BOLD='\033[1m'
_RST='\033[0m'

# Check history file exists
if [ ! -f "$HISTFILE" ]; then
    printf "${_RED}✗ History file not found: ${HISTFILE}${_RST}\n"
    exit 1
fi

# Count before
before=$(wc -l < "$HISTFILE")

# Create backup
cp "$HISTFILE" "$BACKUP"
printf "${_CYAN}📋 Backup created: ${BACKUP}${_RST}\n"

# Deduplicate: keep last (most recent) occurrence of each command
# 1. tac reverses (newest first)
# 2. awk keeps only the first occurrence of each line (= most recent)
# 3. tac restores chronological order
tmpfile=$(mktemp)
tac "$HISTFILE" | awk '!seen[$0]++' | tac > "$tmpfile"

# Verify the temp file is not empty (safety check)
if [ ! -s "$tmpfile" ]; then
    printf "${_RED}✗ Error: dedup produced empty file. Aborting. Backup preserved.${_RST}\n"
    rm -f "$tmpfile"
    exit 1
fi

# Replace history file
mv "$tmpfile" "$HISTFILE"

# Count after
after=$(wc -l < "$HISTFILE")
removed=$((before - after))

# Reload history into current session (if running interactively)
if [[ $- == *i* ]]; then
    history -c
    history -r
fi

# Report
printf "${_GREEN}✓ History cleaned: ${_BOLD}${before}${_RST}${_GREEN} → ${_BOLD}${after}${_RST}${_GREEN} entries${_RST}\n"

if [ "$removed" -gt 0 ]; then
    printf "${_YELLOW}  Removed ${_BOLD}${removed}${_RST}${_YELLOW} duplicates${_RST}\n"
else
    printf "${_CYAN}  No duplicates found — history is already clean!${_RST}\n"
fi
