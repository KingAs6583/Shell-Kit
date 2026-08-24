# Interactive SSH key generator for GitHub
# Usage: setupGithubSshKey
setupGithubSshKey() {
    if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
        echo "Usage: setupGithubSshKey"
        return 0
    fi

    local key_name email full_name relative_path use_agent
    local ssh_dir="$HOME/.ssh"
    local config_path="$ssh_dir/config"
    local key_path

    local _GREEN='\033[0;32m'
    local _CYAN='\033[0;36m'
    local _YELLOW='\033[1;33m'
    local _RST='\033[0m'

    printf "\n${_CYAN}=== GitHub SSH Key Setup ===${_RST}\n\n"

    read -r -p "  Key alias (e.g. 'work' or 'personal'): " key_name
    read -r -p "  Email address: " email
    read -r -p "  Full name (for git config): " full_name
    read -r -p "  Key path under ~/ (leave blank for ~/.ssh/id_ed25519_${key_name}): " relative_path
    read -r -p "  Add key to ssh-agent now? (y/N): " use_agent

    if [ -z "$key_name" ] || [ -z "$email" ] || [ -z "$full_name" ]; then
        echo "  Error: key alias, email, and full name are required."
        return 1
    fi

    # Build key path
    if [ -z "$relative_path" ]; then
        key_path="$HOME/.ssh/id_ed25519_${key_name}"
    else
        relative_path="${relative_path#~/}"
        relative_path="${relative_path#/}"
        key_path="$HOME/$relative_path"
    fi

    # Guard: don't overwrite existing key
    if [ -f "$key_path" ] || [ -f "${key_path}.pub" ]; then
        echo "  Key already exists at: $key_path"
        echo "  Delete it first if you want to regenerate."
        return 1
    fi

    # Create .ssh dir
    mkdir -p "$ssh_dir" && chmod 700 "$ssh_dir" 2>/dev/null
    mkdir -p "$(dirname "$key_path")"

    printf "\n${_YELLOW}Generating SSH key at: $key_path${_RST}\n"
    echo "  (You'll be prompted for a passphrase — use one for better security)"
    echo ""

    ssh-keygen -t ed25519 -C "$email" -f "$key_path" || {
        echo "  ssh-keygen failed."
        return 1
    }

    chmod 600 "$key_path" 2>/dev/null
    chmod 644 "${key_path}.pub" 2>/dev/null

    # Add to ~/.ssh/config
    touch "$config_path"
    chmod 600 "$config_path" 2>/dev/null

    if ! grep -q "^Host ${key_name}$" "$config_path" 2>/dev/null; then
        {
            echo ""
            echo "Host ${key_name}"
            echo "    HostName github.com"
            echo "    User git"
            echo "    IdentityFile ${key_path}"
            echo "    IdentitiesOnly yes"
        } >> "$config_path"
        printf "${_GREEN}  Added SSH config entry for Host: ${key_name}${_RST}\n"
    else
        echo "  SSH config entry already exists for Host: ${key_name}"
    fi

    # Optionally add to ssh-agent
    if [[ "${use_agent:-}" =~ ^[Yy]$ ]]; then
        eval "$(ssh-agent -s)" >/dev/null 2>&1
        ssh-add "$key_path"
        echo "  Key added to ssh-agent."
    fi

    # Print summary
    printf "\n${_GREEN}=== Done! ===${_RST}\n"
    printf "  Name:         %s\n" "$full_name"
    printf "  Email:        %s\n" "$email"
    printf "  Private key:  %s\n" "$key_path"
    printf "  Public key:   %s.pub\n" "$key_path"
    printf "  IdentityFile: %s\n\n" "$key_name"

    printf "${_CYAN}Copy this public key to GitHub Settings -> SSH Keys:${_RST}\n"
    printf "----------------------------------------------------\n"
    cat "${key_path}.pub"
    printf "----------------------------------------------------\n\n"

    printf "  Set up git config for this key:\n"
    printf "    git config user.name \"%s\"\n" "$full_name"
    printf "    git config user.email \"%s\"\n" "$email"
    printf "    git remote set-url origin git@%s:USERNAME/REPO.git\n\n" "$key_name"
}
