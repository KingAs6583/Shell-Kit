#!/usr/bin/env bash
# uninstall.sh — Uninstall shell-kit utility scripts and lazy functions
# Note: Core profiles (~/.bashrc, ~/.profile, etc.) are skipped by default to prevent configuration loss.
# Use --restore to completely uninstall and restore backups.

set -euo pipefail

RESTORE_BACKUPS=false
if [[ "${1:-}" == "--restore" ]]; then
    RESTORE_BACKUPS=true
elif [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: uninstall.sh [OPTIONS]"
    echo ""
    echo "Deletes installed utility scripts (~/.local/bin/*) and lazy functions matching manifest.json."
    echo ""
    echo "Options:"
    echo "  --restore     Remove all files (including core profiles) and restore original backups (.bak)"
    echo "  -h, --help    Show this help message and exit"
    exit 0
fi

echo "shell-kit uninstaller"

# Resolve Paths
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$REPO_DIR/manifest.json"

if [ ! -f "$MANIFEST" ]; then
    echo "Error: manifest.json not found at $MANIFEST" >&2
    exit 1
fi

# Detect Platform
case "$(uname -s)" in
    MINGW*|CYGWIN*|MSYS*) PLATFORM="windows" ;;
    Linux*)               PLATFORM="linux" ;;
    Darwin*)              PLATFORM="mac" ;;
    *)                    PLATFORM="linux" ;; # fallback
esac

# Parse manifest using Python to find scripts to delete
if command -v python3 &>/dev/null; then
    DELETE_LINES_RAW=$(python3 - "$MANIFEST" "$PLATFORM" "$RESTORE_BACKUPS" <<'PYEOF' | tr -d '\r'
import sys, json

manifest_path, platform, restore_backups_str = sys.argv[1], sys.argv[2], sys.argv[3]
restore_backups = restore_backups_str.lower() == "true"

with open(manifest_path) as f:
    manifest = json.load(f)

for entry in manifest["files"]:
    src = entry["src"]
    targets = entry.get("targets", {})
    target = targets.get(platform) or targets.get("linux")
    if target:
        basename = target.split("/")[-1]
        # Skip core shell profiles for safety unless restoring
        is_config = target.startswith("~/.") and basename in [
            ".bashrc", ".bash_profile", ".profile", 
            ".bash_function", ".bash_function.both", 
            ".bash_function.linux", ".bash_function.windows",
            ".bash_keybindings", ".minttyrc"
        ]
        if restore_backups or not is_config:
            print(f"{target}|{src}")
PYEOF
)
    mapfile -t DELETE_FILES <<< "$DELETE_LINES_RAW"
else
    echo "Error: python3 is required for parsing manifest.json during uninstallation." >&2
    exit 1
fi

# Perform Deletion & Restoration
DELETED_COUNT=0
RESTORED_COUNT=0
for line in "${DELETE_FILES[@]:-}"; do
    if [ -z "$line" ]; then continue; fi

    # Split target and src
    target="${line%%|*}"
    src="${line#*|}"

    # Resolve home directory
    resolved_path="${target//\~/$HOME}"
    repo_src_path="$REPO_DIR/$src"

    if [ -e "$resolved_path" ] || [ -L "$resolved_path" ]; then
        # Run self-cleanup if supported by the source script in the repo
        if [ -f "$repo_src_path" ] && grep -Fq -e "--cleanup" "$repo_src_path" 2>/dev/null; then
            echo "  [CLEANUP] Running $target --cleanup"
            if [[ "$target" == *.py ]]; then
                if command -v python3 &>/dev/null; then
                    python3 "$resolved_path" --cleanup 2>/dev/null || true
                elif command -v python &>/dev/null; then
                    python "$resolved_path" --cleanup 2>/dev/null || true
                fi
            else
                bash "$resolved_path" --cleanup 2>/dev/null || true
            fi
        fi

        rm -f "$resolved_path"
        echo "  [DELETED] $target"
        DELETED_COUNT=$((DELETED_COUNT + 1))
    fi

    # Restore original backup if exists
    if [ "$RESTORE_BACKUPS" = "true" ] && [ -f "${resolved_path}.bak" ]; then
        mv "${resolved_path}.bak" "$resolved_path"
        echo "  [RESTORED] Restored backup: $target"
        RESTORED_COUNT=$((RESTORED_COUNT + 1))
    fi
done

# Cleanup empty lazy folder
LAZY_DIR="$HOME/.local/share/shell-kit/lazy"
if [ -d "$LAZY_DIR" ] && [ -z "$(ls -A "$LAZY_DIR")" ]; then
    rmdir "$LAZY_DIR"
    echo "  [DELETED] ~/.local/share/shell-kit/lazy (empty folder)"
fi

echo ""
if [ "$RESTORE_BACKUPS" = "true" ]; then
    echo "[OK] Uninstallation complete! Removed $DELETED_COUNT files and restored $RESTORED_COUNT backups."
else
    echo "[OK] Uninstallation complete! Removed $DELETED_COUNT utility script files."
fi

