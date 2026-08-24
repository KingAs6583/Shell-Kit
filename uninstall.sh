#!/usr/bin/env bash
# uninstall.sh — Uninstall shell-kit utility scripts and lazy functions
# Note: Core profiles (~/.bashrc, ~/.profile, etc.) are skipped to prevent configuration loss.

set -euo pipefail

# Print help signature
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: uninstall.sh"
    echo "Deletes installed utility scripts (~/.local/bin/*) and lazy functions matching manifest.json."
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
    DELETE_LINES_RAW=$(python3 - "$MANIFEST" "$PLATFORM" <<'PYEOF' | tr -d '\r'
import sys, json

manifest_path, platform = sys.argv[1], sys.argv[2]

with open(manifest_path) as f:
    manifest = json.load(f)

for entry in manifest["files"]:
    targets = entry.get("targets", {})
    target = targets.get(platform) or targets.get("linux")
    if target:
        basename = target.split("/")[-1]
        # Skip core shell profiles for safety
        is_config = target.startswith("~/.") and basename in [
            ".bashrc", ".bash_profile", ".profile", 
            ".bash_function", ".bash_function.both", 
            ".bash_function.linux", ".bash_function.windows"
        ]
        if not is_config:
            print(target)
PYEOF
)
    mapfile -t DELETE_FILES <<< "$DELETE_LINES_RAW"
else
    echo "Error: python3 is required for parsing manifest.json during uninstallation." >&2
    exit 1
fi

# Perform Deletion
DELETED_COUNT=0
for target in "${DELETE_FILES[@]:-}"; do
    if [ -z "$target" ]; then continue; fi

    # Resolve home directory
    resolved_path="${target//\~/$HOME}"

    if [ -e "$resolved_path" ] || [ -L "$resolved_path" ]; then
        rm -f "$resolved_path"
        echo "  [DELETED] $target"
        DELETED_COUNT=$((DELETED_COUNT + 1))
    fi
done

# Cleanup empty lazy folder
LAZY_DIR="$HOME/.local/share/shell-kit/lazy"
if [ -d "$LAZY_DIR" ] && [ -z "$(ls -A "$LAZY_DIR")" ]; then
    rmdir "$LAZY_DIR"
    echo "  [DELETED] ~/.local/share/shell-kit/lazy (empty folder)"
fi

echo ""
echo "[OK] Uninstallation complete! Removed $DELETED_COUNT utility script files."
