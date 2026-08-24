#!/usr/bin/env bash
# dotfiles.sh — shell-kit management CLI
# Usage: dotfiles <subcommand>
# Alias: dotfiles (set in ~/.bashrc)

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

_CYAN='\033[0;36m'
_GREEN='\033[0;32m'
_BOLD='\033[1m'
_RST='\033[0m'

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    cmd="help"
else
    cmd="${1:-help}"
fi
shift || true

case "$cmd" in
    verify)
        bash "$REPO_DIR/verify.sh" "$@"
        ;;
    install)
        bash "$REPO_DIR/install.sh" "$@"
        ;;
    sync)
        cd "$REPO_DIR"
        printf "${_CYAN}Syncing shell-kit to git...${_RST}\n"
        git add -A
        git status --short
        printf "Commit message (or Enter to skip): "
        read -r msg
        if [ -n "$msg" ]; then
            git commit -m "$msg"
            git push && printf "${_GREEN}Pushed!${_RST}\n" || printf "Push failed — check remote.\n"
        else
            printf "Skipped commit.\n"
        fi
        ;;
    status)
        cd "$REPO_DIR"
        printf "${_CYAN}${_BOLD}shell-kit git status:${_RST}\n"
        git status
        printf "\n${_CYAN}Last 5 commits:${_RST}\n"
        git log --oneline -5
        ;;
    help|*)
        printf "\n${_CYAN}${_BOLD}dotfiles — shell-kit manager${_RST}\n\n"
        printf "  ${_GREEN}dotfiles verify${_RST}    Check local vs git status, offer fixes\n"
        printf "  ${_GREEN}dotfiles install${_RST}   Symlink all configs to correct locations\n"
        printf "  ${_GREEN}dotfiles sync${_RST}      git add + commit + push shell-kit repo\n"
        printf "  ${_GREEN}dotfiles status${_RST}    Show git status of shell-kit repo\n"
        printf "  ${_GREEN}dotfiles help${_RST}      Show this help\n"
        printf "\n"
        ;;
esac
