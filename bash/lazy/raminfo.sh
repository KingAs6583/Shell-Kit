# RAM Info details
# Usage: raminfo
raminfo() {
    if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
        echo "Usage: raminfo"
        return 0
    fi

    local _CYAN='\033[0;36m'
    local _BOLD='\033[1m'
    local _RST='\033[0m'

    printf "\n${_CYAN}${_BOLD}  RAM Information${_RST}\n"
    _line

    # Free memory summary
    printf "\n${_CYAN}  Memory Usage:${_RST}\n"
    free -h

    # Detailed dmidecode RAM info if available
    if command -v dmidecode &>/dev/null; then
        printf "\n${_CYAN}  RAM Hardware Details (dmidecode type 17):${_RST}\n"
        _line
        sudo dmidecode --type 17 | grep -E "Size:|Type:|Speed:|Manufacturer:|Part Number:|Locator:" | grep -v "No Module"
    fi

    # /proc/meminfo summary
    printf "\n${_CYAN}  /proc/meminfo summary:${_RST}\n"
    grep -E "^(MemTotal|MemFree|MemAvailable|SwapTotal|SwapFree):" /proc/meminfo | \
        awk '{printf "  %-20s %s %s\n", $1, $2, $3}'
    echo ""
}
