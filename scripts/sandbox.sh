#!/usr/bin/env bash
# sandbox.sh — Run an isolated testing environment for shell-kit in a temporary folder

set -euo pipefail

# Print help signature
if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
    echo "Usage: sandbox.sh"
    echo "Creates a temporary mock home directory, installs shell-kit within it, and starts an isolated bash subshell."
    echo "On exit, the temporary files are automatically cleaned up."
    exit 0
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

# Run the installer inside the sandbox environment
echo ""
echo "Installing shell-kit into sandbox..."
# Run install.sh with HOME override
HOME="$SANDBOX_HOME" bash "$REPO_DIR/install.sh"

echo ""
echo "======================================================================"
echo " Entering isolated sandbox shell."
echo "   - All changes inside this shell will affect $SANDBOX_HOME only."
echo "   - Type 'exit' or press Ctrl+D to exit and cleanup."
echo "======================================================================"
echo ""

# Launch interactive bash subshell with HOME override and force loading of sandbox .bashrc
HOME="$SANDBOX_HOME" bash --rcfile "$SANDBOX_HOME/.bashrc" -i
