#!/usr/bin/env bash
# sandbox.sh — Run an isolated testing environment for shell-kit in a temporary folder

set -euo pipefail

NO_INSTALL=false

# Print help signature
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: sandbox.sh [--no-install] [command]"
    echo "Creates a temporary mock HOME directory, configures the environment, and runs isolated tests."
    echo ""
    echo "Options:"
    echo "  --no-install    Starts a clean sandbox environment without installing shell-kit."
    echo "  -h, --help      Show this help text."
    echo ""
    echo "If a [command] is specified, it will execute that command inside the sandboxed environment and exit."
    echo "Otherwise, an interactive bash subshell will be started."
    exit 0
fi

# Parse --no-install flag
if [[ "${1:-}" == "--no-install" ]]; then
    NO_INSTALL=true
    shift
fi

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Create a temporary directory for sandbox HOME
# Works on Linux, macOS, and Git Bash on Windows
SANDBOX_HOME=$(mktemp -d /tmp/shell-kit-sandbox.XXXXXX)

echo "shell-kit Sandbox"
echo "  Mock HOME: $SANDBOX_HOME"
echo "  Workspace: $REPO_DIR"

# Clean up trap on exit or interrupt
cleanup() {
    echo ""
    echo "Cleaning up sandbox environment..."
    rm -rf "$SANDBOX_HOME"
    echo "[OK] Sandbox cleaned up."
}
trap cleanup EXIT INT TERM

# Install or setup basic bashrc
if [ "$NO_INSTALL" = "true" ]; then
    echo "  Mode: Clean sandbox (skipping installation)"
    mkdir -p "$SANDBOX_HOME"
    echo "alias deactivate='exit'" > "$SANDBOX_HOME/.bashrc"
else
    echo "  Mode: Auto-install shell-kit"
    # Run the installer inside the sandbox environment
    HOME="$SANDBOX_HOME" bash "$REPO_DIR/install.sh"
    # Append deactivate alias to bashrc
    echo "alias deactivate='exit'" >> "$SANDBOX_HOME/.bashrc"
fi

# Run command or launch interactive shell
if [ $# -gt 0 ]; then
    echo ""
    echo "Executing command in sandbox: $@"
    echo "======================================================================"
    # Run the command with HOME overridden and local bin prepended to PATH
    PATH="$SANDBOX_HOME/.local/bin:$PATH" HOME="$SANDBOX_HOME" "$@"
else
    echo ""
    echo "======================================================================"
    echo " Entering isolated sandbox shell."
    echo "   - All changes inside this shell will affect $SANDBOX_HOME only."
    echo "   - Type 'deactivate' or 'exit' (or Ctrl+D) to exit and cleanup."
    echo "======================================================================"
    echo ""
    # Launch interactive bash subshell with HOME override and force loading of sandbox .bashrc
    HOME="$SANDBOX_HOME" bash --rcfile "$SANDBOX_HOME/.bashrc" -i
fi
