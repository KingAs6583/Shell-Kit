# shell-kit

Personal shell toolkit — bash configs, utility scripts, and dotfiles manager.

## Quick Start

### New Machine Setup
```bash
git clone <your-repo-url> ~/shell-kit
# On Windows (Git Bash):
git clone <your-repo-url> /d/Projects/shell-kit
bash /d/Projects/shell-kit/install.sh
```
Then open a new terminal — everything is ready.

### Daily Use
```bash
dotfiles verify    # Check what''s out of sync
dotfiles install   # Re-link all files
dotfiles sync      # Commit + push changes
dotfiles status    # Git status of this repo
```

## Structure
```
shell-kit/
├── bash/
│   ├── .bashrc          # Main shell config (aliases, options)
│   ├── .bash_profile    # Login shell bridge (sources .bashrc)
│   ├── .bash_function   # All shell functions
│   └── .profile         # PATH and environment vars
├── scripts/
│   ├── history-clean.sh          # Deduplicate ~/.bash_history
│   ├── setup-codebase-memory.sh  # Install codebase-memory-mcp
│   └── scan-packages.sh          # Scan history for installed packages
├── manifest.json    # File registry with install paths per OS
├── install.sh       # Symlink all files to correct locations
├── verify.sh        # Check local vs git status
└── dotfiles.sh      # CLI dispatcher
```

## Aliases Quick Reference

| Alias | Command |
|-------|---------|
| `gs` | `git status -sb` |
| `glog` | Pretty git graph |
| `lint` | `npm run lint` |
| `tsc` | `npx tsc --noEmit` |
| `dev` | `npm run dev` |
| `t` | Tree view depth 2 |
| `hhelp` | History cheat sheet |
| `hclean` | Deduplicate history |
| `prompts mcp` | MCP prompt template |
| `pkglist` | Show installed packages |
| `pkgscan` | Rescan package history |
| `pyvenvs` | Find Python venvs |
| `dirsize` | Directory sizes |
| `fdiff` | Colored file diff |

## Platform Support
Works on **Windows (Git Bash)**, **Linux**, and **macOS**. Platform is auto-detected via `$PLATFORM`.
