# Coding Rule: Mandatory Help & --help Support

This rule mandates that all scripts, utility commands, and shell functions in the `shell-kit` toolkit must provide built-in help features so that they are easily discoverable and usable.

## Guidelines

1. **Independent Scripts**:
   - Every executable script (Python, Bash, etc.) in the repository must support the `--help` and `-h` command-line flags.
   - For Python scripts, use standard `argparse` to automatically handle and display help text.
   - For Bash scripts, check `[[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]` early in the execution flow.

2. **Shell Functions**:
   - Every interactive shell function in `.bash_function.*` must protect itself by handling `--help` and `-h` arguments.
   - The help output must be **minimalist** to avoid file bloat and terminal startup lag. It should print only the command signature:
     ```bash
     explore() {
         if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
             echo "Usage: explore [path]"
             return 0
         fi
         # ...
     }
     ```
   - All interactive functions must be registered with their description inside the centralized `manual` command in `bash/.bash_function.both`.

3. **Performance & Lazy Loading**:
   - Heavy or rarely-used shell functions (such as setup commands or system resource checkers) must be stored in the `bash/lazy/` directory as independent scripts.
   - The main startup scripts should define a lightweight stub that sources and executes the lazy script only on-call:
     ```bash
     setupGithubSshKey() {
         source "$HOME/.local/share/shell-kit/lazy/setupGithubSshKey.sh"
         setupGithubSshKey "$@"
     }
     ```
   - Lazy stubs must forward all arguments using `"$@"` so that `--help` and `-h` commands function correctly.
