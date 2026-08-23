#!/usr/bin/env bash
# verify.sh — Verify shell-kit dotfiles status (local vs git)
# Usage: bash verify.sh

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST="$REPO_DIR/manifest.json"

_GREEN='\033[0;32m'
_YELLOW='\033[1;33m'
_RED='\033[0;31m'
_CYAN='\033[0;36m'
_BOLD='\033[1m'
_RST='\033[0m'

case "$(uname -s)" in
    MINGW*|CYGWIN*|MSYS*) PLATFORM="windows" ;;
    Linux*)               PLATFORM="linux"   ;;
    Darwin*)              PLATFORM="mac"     ;;
    *)                    PLATFORM="unknown" ;;
esac

printf "\n${_CYAN}${_BOLD}shell-kit verify${_RST} — Platform: ${PLATFORM}\n"
printf "${_CYAN}Repo: ${REPO_DIR}${_RST}\n\n"
printf "%-35s %-16s %-12s %-12s %s\n" "File" "Local" "Symlink" "Git" "Action"
printf "%-35s %-16s %-12s %-12s %s\n" "───────────────────────────────────" "────────────────" "────────────" "────────────" "──────"

declare -a ACTIONS=()
declare -a ACTION_FILES=()
declare -a ACTION_TARGETS=()

check_file() {
    local src_rel="$1"
    local target="$2"
    local src_abs="$REPO_DIR/$src_rel"

    target="${target/#\~/$HOME}"

    local local_status=""
    local sym_status=""
    local git_status=""
    local action=""

    # Git status
    cd "$REPO_DIR"
    if git ls-files --error-unmatch "$src_rel" &>/dev/null 2>&1; then
        git_status="${_GREEN}tracked${_RST}"
    else
        git_status="${_YELLOW}untracked${_RST}"
        action="${_YELLOW}add to git${_RST}"
    fi

    # Local status
    if [ -L "$target" ]; then
        local link_target
        link_target=$(readlink -f "$target" 2>/dev/null || true)
        if [ "$link_target" = "$src_abs" ]; then
            sym_status="${_GREEN}symlinked${_RST}"
            local_status="${_GREEN}synced${_RST}"
        else
            sym_status="${_YELLOW}other link${_RST}"
            local_status="${_YELLOW}diff target${_RST}"
            action="${_YELLOW}[i] relink${_RST}"
        fi
    elif [ -f "$target" ]; then
        sym_status="${_CYAN}copy${_RST}"
        if diff -q "$src_abs" "$target" &>/dev/null 2>&1; then
            local_status="${_GREEN}synced${_RST}"
        else
            local_status="${_YELLOW}differs${_RST}"
            action="${_YELLOW}[s] sync${_RST}"
            ACTIONS+=("sync")
            ACTION_FILES+=("$src_abs")
            ACTION_TARGETS+=("$target")
        fi
    elif [ ! -e "$target" ]; then
        local_status="${_RED}missing${_RST}"
        sym_status="${_RED}none${_RST}"
        action="${_RED}[i] install${_RST}"
        ACTIONS+=("install")
        ACTION_FILES+=("$src_abs")
        ACTION_TARGETS+=("$target")
    fi

    printf "%-35s %-25s %-21s %-21s %s\n" \
        "$src_rel" \
        "$local_status" \
        "$sym_status" \
        "$git_status" \
        "$action"
}

# Parse manifest with python3 if available
if command -v python3 &>/dev/null; then
    mapfile -t FILE_LINES < <(python3 - "$MANIFEST" "$PLATFORM" <<'PYEOF'
import sys, json
manifest_path, platform = sys.argv[1], sys.argv[2]
with open(manifest_path) as f:
    manifest = json.load(f)
for entry in manifest["files"]:
    src = entry["src"]
    targets = entry.get("targets", {})
    target = targets.get(platform) or targets.get("linux")
    if target:
        print(f"{src}|{target}")
PYEOF
    )
    for line in "${FILE_LINES[@]:-}"; do
        IFS='|' read -r src target <<< "$line"
        check_file "$src" "$target"
    done
else
    check_file "bash/.bashrc"           "~/.bashrc"
    check_file "bash/.bash_profile"     "~/.bash_profile"
    check_file "bash/.bash_function"    "~/.bash_function"
    check_file "bash/.profile"          "~/.profile"
    check_file "scripts/history-clean.sh"         "~/.local/bin/history-clean.sh"
    check_file "scripts/setup-codebase-memory.sh" "~/.local/bin/setup-codebase-memory.sh"
    check_file "scripts/scan-packages.sh"         "~/.local/bin/scan-packages.sh"
fi

# Check for untracked scripts in ~/.local/bin
printf "\n${_CYAN}${_BOLD}Checking untracked local scripts...${_RST}\n"
cd "$REPO_DIR"
if [ -d "$HOME/.local/bin" ]; then
    for f in "$HOME/.local/bin/"*.sh; do
        [ -f "$f" ] || continue
        local_name=$(basename "$f")
        if ! grep -q "$local_name" "$MANIFEST" 2>/dev/null; then
            printf "  ${_YELLOW}⚠  Untracked locally: ~/.local/bin/${local_name}${_RST} — not in manifest\n"
        fi
    done
fi

# Interactive options
if [ ${#ACTIONS[@]} -gt 0 ]; then
    printf "\n${_YELLOW}${_BOLD}Actions available:${_RST}\n"
    printf "  ${_CYAN}[a]${_RST} Apply all recommended actions\n"
    printf "  ${_CYAN}[i]${_RST} Re-run install.sh (fix missing/relink)\n"
    printf "  ${_CYAN}[s]${_RST} Sync differing files to repo\n"
    printf "  ${_CYAN}[q]${_RST} Quit\n"
    printf "\nChoice: "
    read -r choice
    case "$choice" in
        a|i) bash "$REPO_DIR/install.sh" ;;
        s)
            for i in "${!ACTIONS[@]}"; do
                if [ "${ACTIONS[$i]}" = "sync" ]; then
                    cp "${ACTION_TARGETS[$i]}" "${ACTION_FILES[$i]}"
                    printf "${_GREEN}  Synced: ${ACTION_TARGETS[$i]} → ${ACTION_FILES[$i]}${_RST}\n"
                fi
            done
            ;;
        *) printf "Quit.\n" ;;
    esac
fi

printf "\n${_GREEN}${_BOLD}✓ Verify complete${_RST}\n\n"
