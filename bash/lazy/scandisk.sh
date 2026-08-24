# Scan a directory for large or old files
# Usage: scandisk [path]
scandisk() {
    if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
        echo "Usage: scandisk [path]"
        return 0
    fi

    local target="${1:-$HOME}"
    local _CYAN='\033[0;36m'
    local _YELLOW='\033[1;33m'
    local _BOLD='\033[1m'
    local _RST='\033[0m'

    printf "\n${_CYAN}${_BOLD}  Disk Scan: ${target}${_RST}\n"
    _line

    printf "\n${_YELLOW}  Top 10 largest files:${_RST}\n"
    find "$target" -type f -not -path "*/\.*" \
        -exec du -h {} + 2>/dev/null | sort -rh | head -10 | \
        awk '{printf "  %10s  %s\n", $1, $2}'

    printf "\n${_YELLOW}  Top 10 largest directories:${_RST}\n"
    du -h --max-depth=2 "$target" 2>/dev/null | sort -rh | head -10 | \
        awk '{printf "  %10s  %s\n", $1, $2}'

    printf "\n${_YELLOW}  Files not accessed in 30+ days (top 10):${_RST}\n"
    find "$target" -type f -atime +30 -not -path "*/\.*" \
        2>/dev/null | head -10 | while read -r f; do
        printf "  %s\n" "$f"
    done
    echo ""
}
