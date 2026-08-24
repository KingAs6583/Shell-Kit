# shell-kit

> Personal shell toolkit — bash configs, utility scripts, and dotfiles manager.
> Works on **Windows (Git Bash)**, **Linux**, and **macOS**.

---

## Quick Start

### New Machine Setup
```bash
# Linux / macOS
git clone <your-repo-url> ~/shell-kit
bash ~/shell-kit/install.sh

# Windows (Git Bash)
git clone <your-repo-url> /d/Projects/shell-kit
bash /d/Projects/shell-kit/install.sh
```
Open a new terminal — everything loads automatically.

### Daily Use
```bash
dotfiles verify    # Check what's out of sync (local vs git)
dotfiles install   # Re-link all files via symlinks
dotfiles sync      # git add + commit + push
dotfiles status    # git status of this repo
```

---

## Structure

```
shell-kit/
├── PyScp/
│   ├── asset_backup.py          Zip non-git folders
│   ├── backup.py                Backup orchestrator
│   ├── config_inspector.py      Inspect and validate config schemas
│   └── git_scanner.py           Scan project dirs, report uncommitted repos
├── bash/
│   ├── .bashrc                  Main config — options, aliases, sources
│   ├── .bash_profile            Login shell bridge (Git Bash fix)
│   ├── .bash_function.both      Functions: works on ALL platforms
│   ├── .bash_function.linux     Functions: Linux only (auto-guarded)
│   ├── .bash_function.windows   Functions: Windows only (auto-guarded)
│   ├── .bash_function           Legacy (deprecated, kept for compat)
│   └── .profile                 PATH and environment variables
├── scripts/
│   ├── history-clean.sh         Deduplicate ~/.bash_history safely
│   ├── setup-codebase-memory.sh Install codebase-memory-mcp (cross-platform)
│   ├── scan-packages.sh         Scan history for installed packages
│   └── linux/
│       ├── update.sh            Full apt update/upgrade/clean cycle
│       ├── system-info.sh       Hardware info via dmidecode
│       └── ram-info.sh          RAM details
├── .gitignore
├── .gitattributes               Enforce LF line endings
├── manifest.json                File registry — src -> install path per OS
├── install.sh                   Symlink all tracked files to correct locations
├── verify.sh                    Audit local vs git, offer fixes interactively
├── dotfiles.sh                  CLI dispatcher for dotfiles management
└── README.md
```

---

## Prompt

Two-line, cyan/teal themed:
```
 (venv)  ~/Projects/myapp   main *
 ❯
```
- **Path** in cyan — shortened to last 3 components
- **Git branch** in yellow — with `*` (unstaged) / `+` (staged) / `%` (untracked)
- **Python venv** shown when active
- **Arrow** turns red if last command failed

---

## Command Reference

### History
| Command | Action |
|---------|--------|
| `h` | Last 30 commands (numbered for `!N` recall) |
| `hl` | Last 50 commands |
| `Ctrl+R` | Reverse fuzzy search through history |
| `hhelp` | Colored cheat sheet: `!!`, `!$`, `!42`, `^old^new` |
| `hclean` | Deduplicate history file (backup first) |

### Git Aliases
| Command | Action |
|---------|--------|
| `gs` | `git status -sb` |
| `ga` | `git add` |
| `gc` | `git commit` |
| `gp` / `gpl` | push / pull |
| `gd` / `gds` | diff / diff staged |
| `glog` | Pretty graph log (last 20) |
| `gb` / `gco` / `gsw` | branch / checkout / switch |

### Git Setup Functions (`both`)
| Command | Action |
|---------|--------|
| `setupGit "msg" <url>` | Init repo + first commit + push |
| `upload "msg"` | Add all + commit + push |
| `globalConfig` | Set global git user.name / email interactively |
| `localConfig` | Set repo-local git identity interactively |
| `listSshConfig` | List all SSH host aliases from `~/.ssh/config` |
| `setupGithubSshKey` | Interactive: generate ed25519 key, configure `~/.ssh/config`, copy pubkey |

### Dev Tools (Node / TypeScript)
| Command | Action |
|---------|--------|
| `lint` | `npm run lint` |
| `lintfix` | `npm run lint -- --fix` |
| `tsc` / `typecheck` | `npx tsc --noEmit` |
| `dev` / `build` / `start` | `npm run dev/build/start` |

### File System
| Command | Action |
|---------|--------|
| `t` | Tree depth 2 (excludes node_modules/.git) |
| `t3` | Tree depth 3 |
| `td` | Directories only |
| `dirsize [path]` | Subdirs sorted by size |
| `dirsize5 [path]` | Top 5 largest subdirs |
| `filesize [path]` | Files sorted by size |
| `fdiff f1 f2` | Colored file diff (git engine) |
| `ddiff d1 d2` | Colored directory diff |

### Grep Shortcuts
| Command | Action |
|---------|--------|
| `gr pattern` | Recursive grep — color + line numbers |
| `gi pattern` | Case-insensitive recursive grep |
| `gx pattern` | Recursive grep, excludes noise dirs |
| `gf '*.tsx'` | Find files by name pattern |
| `todo` | Find all TODO/FIXME/HACK comments |

### Navigation
| Command | Action |
|---------|--------|
| `..` / `...` / `....` | Go up 1/2/3 directories |
| `mkcd name` | Create directory and `cd` into it |

### Python & Packages
| Command | Action |
|---------|--------|
| `pyvenvs` | Find all Python venvs with activate commands |
| `pkglist` | Show cached installed packages (instant) |
| `pkgscan` | Force rescan of history for packages |

### AI Prompts
| Command | Action |
|---------|--------|
| `prompts mcp` | Codebase Memory MCP template |
| `prompts review` | Concise code review template |
| `prompts debug` | Bug report template |
| `prompts tokens` | Token-saving patterns |

### Linux Only
| Command | Action |
|---------|--------|
| `sysupdate` | Full apt update + upgrade + autoremove + autoclean |
| `aptclean` | apt autoremove + autoclean only |
| `sysinfo [type]` | Hardware info — `1`=system `4`=cpu `17`=ram |
| `raminfo` | RAM usage + hardware details |
| `scandisk [path]` | Find large files, large dirs, old files |

### Windows Only
| Command | Action |
|---------|--------|
| `explore [path]` | Open path in Windows Explorer |
| `open <file\|url>` | Open with default Windows app |
| `toUnix <path>` | Convert Windows path → Unix path |
| `toWin <path>` | Convert Unix path → Windows path |
| `killwin <proc.exe>` | Kill a Windows process by name |
| `pslist [filter]` | List running processes |
| `devmode` | Check if Developer Mode is ON (needed for symlinks) |

### Safety
| Feature | Action |
|---------|--------|
| `rm -rf .` / `*` / `/` / `~` | **Blocked** with red warning |
| `rm -rf foldername` | Works normally |
| `mv` / `cp` | Confirm before overwrite (`-i`) |

### Developer Utilities
| Command / Utility | Action |
|-------------------|--------|
| `manual` | Unified help cheat sheet: displays all commands, functions, and aliases |
| `scripts/sandbox.sh [--no-install] [cmd]` | Runs an isolated subshell (or custom command) in a temporary folder under `/tmp/`. Includes `deactivate` alias for quick exit and cleanup. |
| `uninstall.sh` | Cleans up local bin and runs `--cleanup` on stateful scripts before deleting symlinks |
| `PyScp/help_enforcer.py` | Validates that all functions/scripts conform to `--help` and `manual` registry rules |

---

## How Dotfiles Work

All files in `bash/` and `scripts/` are tracked in `manifest.json` with their install paths per OS.
`install.sh` creates **symlinks** so edits to `~/.bashrc` automatically update the repo file.

```
~/.bashrc  --symlink-->  D:/Projects/shell-kit/bash/.bashrc
```

On Windows, symlinks require **Developer Mode** (Settings → System → For Developers). Run `devmode` to check. If unavailable, `install.sh` falls back to file copies.

---

## Platform Detection

Auto-detected at shell startup via `$PLATFORM`:

```bash
echo $PLATFORM   # → windows | linux | mac
```

Platform-specific functions are loaded automatically — Linux functions are **never loaded** on Windows, and vice versa.

---

## Push to GitHub

```bash
cd /d/Projects/shell-kit        # Windows
# cd ~/shell-kit                # Linux

git remote add origin git@github.com:<username>/shell-kit.git
git push -u origin main
```