# ~/.bashrc — Git Bash / Linux Bash configuration
# Thin config: options + aliases only. All functions live in ~/.bash_function.

# ─────────────────────────────────────────────────────────────
# 1. EARLY EXIT GUARDS
# ─────────────────────────────────────────────────────────────

case $- in
    *i*) ;;
      *) return;;
esac

if [ "${TERM_PROGRAM:-}" = "vscode" ]; then
    return
fi

# ─────────────────────────────────────────────────────────────
# 2. SHELL OPTIONS & HISTORY
# ─────────────────────────────────────────────────────────────

HISTCONTROL=ignoreboth:erasedups
HISTIGNORE="history:ls:clear:cd:pwd:exit:h:hl"
HISTSIZE=10000
HISTFILESIZE=10000
shopt -s histappend
shopt -s checkwinsize
shopt -s cdspell
shopt -s dirspell 2>/dev/null
shopt -s nocaseglob

# ─────────────────────────────────────────────────────────────
# 3. COMPLETION
# ─────────────────────────────────────────────────────────────

bind 'set completion-ignore-case on'     2>/dev/null
bind 'set show-all-if-ambiguous on'      2>/dev/null
bind 'set colored-stats on'              2>/dev/null
bind 'set mark-directories on'           2>/dev/null
bind 'set mark-symlinked-directories on' 2>/dev/null
bind 'set bell-style none'               2>/dev/null

if ! shopt -oq posix; then
    if [ -f /usr/share/bash-completion/bash_completion ]; then
        . /usr/share/bash-completion/bash_completion
    elif [ -f /etc/bash_completion ]; then
        . /etc/bash_completion
    fi
fi

# ─────────────────────────────────────────────────────────────
# 4. COLORS (for prompt — non-prompt colors are in bash_function)
# ─────────────────────────────────────────────────────────────

RST='\[\033[0m\]'
BRED='\[\033[1;31m\]'
BGREEN='\[\033[1;32m\]'
BYELLOW='\[\033[1;33m\]'
BCYAN='\[\033[1;36m\]'
BMAGENTA='\[\033[1;35m\]'
BBLUE='\[\033[1;34m\]'

export LESS_TERMCAP_mb=$'\E[1;31m'
export LESS_TERMCAP_md=$'\E[1;36m'
export LESS_TERMCAP_me=$'\E[0m'
export LESS_TERMCAP_so=$'\E[01;33m'
export LESS_TERMCAP_se=$'\E[0m'
export LESS_TERMCAP_us=$'\E[1;32m'
export LESS_TERMCAP_ue=$'\E[0m'

# ─────────────────────────────────────────────────────────────
# 5. PROMPT — Two-line, Cyan/Teal theme
# ─────────────────────────────────────────────────────────────

if [ -f "/mingw64/share/git/completion/git-prompt.sh" ]; then
    source "/mingw64/share/git/completion/git-prompt.sh"
elif [ -f "/etc/bash_completion.d/git-prompt" ]; then
    source "/etc/bash_completion.d/git-prompt"
fi

export GIT_PS1_SHOWDIRTYSTATE=1
export GIT_PS1_SHOWUNTRACKEDFILES=
export GIT_PS1_SHOWSTASHSTATE=1
export VIRTUAL_ENV_DISABLE_PROMPT=1

__build_prompt() {
    local exit_code=$?

    local venv_info=""
    if [ -n "${VIRTUAL_ENV:-}" ]; then
        venv_info="\[\033[1;32m\]($(basename "$VIRTUAL_ENV")) \[\033[0m\]"
    fi

    local git_info=""
    if command -v __git_ps1 &>/dev/null; then
        local branch
        branch=$(__git_ps1 "%s" 2>/dev/null || true)
        if [ -n "$branch" ]; then
            # Extract just the branch name for color matching
            local branch_name="${branch%% *}"
            local color=""
            case "$branch_name" in
                main|master)
                    color="$BMAGENTA"
                    ;;
                dev|development)
                    color="$BBLUE"
                    ;;
                release/*)
                    color="$BGREEN"
                    ;;
                *)
                    color="$BCYAN"
                    ;;
            esac
            git_info="  ${color}${branch}${RST}"
        fi
    fi

    local short_path
    short_path=$(echo "$PWD" | sed "s|^$HOME|~|" | awk -F/ '{
        n = NF
        if (n <= 3) { print $0 }
        else { printf ".../%s/%s/%s", $(n-2), $(n-1), $n }
    }')

    local arrow
    if [ $exit_code -eq 0 ]; then
        arrow="\[\033[1;35m\]>\[\033[0m\]"
    else
        arrow="\[\033[1;31m\]>\[\033[0m\]"
    fi

    local took_line=""
    if [ -n "${__shkit_took_msg:-}" ]; then
        took_line=" ${__shkit_took_msg}\n"
    fi

    PS1="\n${took_line} ${venv_info}\[\033[1;36m\]${short_path}\[\033[0m\]${git_info}\n ${arrow} "
}

# ─────────────────────────────────────────────────────────────
# 6. PROMPT_COMMAND — history sync + prompt build + bg scan
# ─────────────────────────────────────────────────────────────

__bg_pkg_scan_done=0
__maybe_bg_scan() {
    if [ "$__bg_pkg_scan_done" -eq 0 ] && [ ! -f "$HOME/.cache/installed-packages.txt" ]; then
        __bg_pkg_scan_done=1
        local scan_script
        if [ -f "/d/Projects/shell-kit/scripts/scan-packages.sh" ]; then
            scan_script="/d/Projects/shell-kit/scripts/scan-packages.sh"
        elif [ -f "$HOME/shell-kit/scripts/scan-packages.sh" ]; then
            scan_script="$HOME/shell-kit/scripts/scan-packages.sh"
        fi
        [ -n "${scan_script:-}" ] && bash "$scan_script" &>/dev/null &
    fi
}

# Command execution timer settings
SHKIT_TIMER_THRESHOLD="${SHKIT_TIMER_THRESHOLD:-1.5}"
__cmd_start_time=""
__shkit_took_msg=""
__shkit_in_prompt_command=0

__calc_cmd_duration() {
    if [ -z "${__cmd_start_time:-}" ]; then
        echo ""
        return
    fi

    local start_s="${__cmd_start_time%.*}"
    local start_us="${__cmd_start_time#*.}"
    local end_s="${EPOCHREALTIME%.*}"
    local end_us="${EPOCHREALTIME#*.}"

    # Pad microseconds to 6 digits
    while [ ${#start_us} -lt 6 ]; do start_us="${start_us}0"; done
    while [ ${#end_us} -lt 6 ]; do end_us="${end_us}0"; done

    # Remove leading zeros to avoid octal interpretation
    start_us=$((10#$start_us))
    end_us=$((10#$end_us))

    local diff_s=$((end_s - start_s))
    local diff_us=$((end_us - start_us))

    if [ $diff_us -lt 0 ]; then
        diff_s=$((diff_s - 1))
        diff_us=$((diff_us + 1000000))
    fi

    # Round to 1 decimal place
    local dec=$(((diff_us + 50000) / 100000))
    if [ $dec -ge 10 ]; then
        diff_s=$((diff_s + 1))
        dec=0
    fi

    echo "${diff_s}.${dec}"
}

__show_took_time() {
    local duration
    duration=$(__calc_cmd_duration)
    if [ -z "$duration" ]; then
        __shkit_took_msg=""
        return
    fi

    local thresh="${SHKIT_TIMER_THRESHOLD:-1.5}"
    local thresh_int
    if [[ "$thresh" == *.* ]]; then
        local ts="${thresh%.*}"
        local td="${thresh#*.}"
        td="${td:0:1}"
        thresh_int=$((10#$ts * 10 + 10#$td))
    else
        thresh_int=$((10#$thresh * 10))
    fi

    local dur_s="${duration%.*}"
    local dur_d="${duration#*.}"
    local dur_int=$((10#$dur_s * 10 + 10#$dur_d))

    if [ $dur_int -ge $thresh_int ]; then
        __shkit_took_msg="${BYELLOW}[took ${duration}s]${RST}"
    else
        __shkit_took_msg=""
    fi
}

__record_cmd_start_time() {
    # Guard against prompt command execution triggering the debug trap
    if [ "${__shkit_in_prompt_command:-0}" -eq 1 ]; then
        return
    fi
    if [ -z "$__cmd_start_time" ]; then
        __cmd_start_time="$EPOCHREALTIME"
    fi
}

if [ -n "${EPOCHREALTIME:-}" ]; then
    trap '__record_cmd_start_time' DEBUG
fi

__shkit_prompt_command() {
    # Calculate execution duration first
    if [ -n "${EPOCHREALTIME:-}" ]; then
        __show_took_time
        __cmd_start_time=""
    fi

    # Guard prompt command helpers
    __shkit_in_prompt_command=1

    history -a
    history -c
    history -r
    __build_prompt
    __maybe_bg_scan

    __shkit_in_prompt_command=0
}

PROMPT_COMMAND='__shkit_prompt_command'

# ─────────────────────────────────────────────────────────────
# 7. LS & COLOR ALIASES
# ─────────────────────────────────────────────────────────────

alias ls='ls --color=auto'
alias ll='ls -alF --color=auto'
alias la='ls -A --color=auto'
alias l='ls -CF --color=auto'
alias grep='grep --color=auto'
alias fgrep='fgrep --color=auto'
alias egrep='egrep --color=auto'
alias diff='diff --color=auto'

# ─────────────────────────────────────────────────────────────
# 8. GIT ALIASES
# ─────────────────────────────────────────────────────────────

alias gs='git status -sb'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gpl='git pull'
alias gd='git diff --color'
alias gds='git diff --staged --color'
alias glog='git log --oneline --graph --decorate --all -20'
alias gb='git branch'
alias gco='git checkout'
alias gsw='git switch'

# ─────────────────────────────────────────────────────────────
# 9. NAVIGATION ALIASES
# ─────────────────────────────────────────────────────────────

alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'

# ─────────────────────────────────────────────────────────────
# 10. SAFETY ALIASES
# ─────────────────────────────────────────────────────────────

alias mv='mv -i'
alias cp='cp -i'

# ─────────────────────────────────────────────────────────────
# 11. HISTORY HELPERS
# ─────────────────────────────────────────────────────────────

alias h='history 30'
alias hl='history 50'
alias hclean='bash ~/.local/bin/history-clean.sh'
alias hhelp='__history_help'

# ─────────────────────────────────────────────────────────────
# 12. DEV TOOL ALIASES (Node / TypeScript)
# ─────────────────────────────────────────────────────────────

alias lint='npm run lint'
alias lintfix='npm run lint -- --fix'
alias tsc='npx tsc --noEmit'
alias typecheck='npx tsc --noEmit'
alias dev='npm run dev'
alias build='npm run build'
alias start='npm start'

# ─────────────────────────────────────────────────────────────
# 13. PACKAGE SCAN ALIASES
# ─────────────────────────────────────────────────────────────

alias pkglist='[ -f ~/.cache/installed-packages.txt ] && cat ~/.cache/installed-packages.txt || echo "Cache empty — run: pkgscan"'
alias pkgscan='bash /d/Projects/shell-kit/scripts/scan-packages.sh --foreground 2>/dev/null || bash ~/shell-kit/scripts/scan-packages.sh --foreground'

# ─────────────────────────────────────────────────────────────
# 14. PYTHON VENV ALIAS
# ─────────────────────────────────────────────────────────────

alias pyvenvs='__find_python_venvs'

# ─────────────────────────────────────────────────────────────
# 15. DOTFILES MANAGEMENT ALIAS
# ─────────────────────────────────────────────────────────────

alias dotfiles='bash ~/.local/bin/dotfiles.sh'

# ─────────────────────────────────────────────────────────────
# 16. SOURCE EXTERNAL FILES
# ─────────────────────────────────────────────────────────────

# Load cross-platform functions (works on all OS)
[ -f ~/.bash_function.both    ] && source ~/.bash_function.both

# Load cross-platform keybindings
[ -f ~/.bash_keybindings      ] && source ~/.bash_keybindings

# Load platform-specific functions
[ "$PLATFORM" = "linux"   ] && [ -f ~/.bash_function.linux   ] && source ~/.bash_function.linux
[ "$PLATFORM" = "windows" ] && [ -f ~/.bash_function.windows ] && source ~/.bash_function.windows

# Legacy monolithic file (kept for backwards compat, deprecated)
[ -f ~/.bash_function ] && source ~/.bash_function

# User aliases
[ -f ~/.bash_aliases  ] && source ~/.bash_aliases
