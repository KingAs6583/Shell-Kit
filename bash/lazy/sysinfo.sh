# System Info via dmidecode
# Usage: sysinfo [type]
sysinfo() {
    if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
        echo "Usage: sysinfo [type]"
        return 0
    fi

    local type="${1:-1}"
    local _CYAN='\033[0;36m'
    local _BOLD='\033[1m'
    local _RST='\033[0m'

    if ! command -v dmidecode &>/dev/null; then
        echo "  dmidecode not installed. Install with: sudo apt install dmidecode"
        return 1
    fi

    printf "\n${_CYAN}${_BOLD}  System Info (dmidecode type ${type})${_RST}\n"
    _line
    sudo dmidecode --type "$type"

    echo ""
    echo "  Other useful types: 0=bios 1=system 2=baseboard 3=chassis 4=cpu 17=ram"
}
