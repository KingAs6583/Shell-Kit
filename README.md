# shell-kit

> Personal shell toolkit — bash configs, utility scripts, and dotfiles manager.
> Works on **Windows (Git Bash)**, **Linux**, and **macOS**.

---

## Quick Start

### New Machine Setup
```bash
# Linux / macOS (automatically detects SSH connection and defaults to server profile)
git clone <your-repo-url> ~/shell-kit
bash ~/shell-kit/install.sh

# Explicitly choose server or desktop profiles
# bash ~/shell-kit/install.sh --server     # Server profile (skips desktop-only configurations)
# bash ~/shell-kit/install.sh --desktop    # Desktop profile (standard default)

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
│   ├── clip_helper.py           Local OS clipboard access helper
│   ├── clip_service.py          Local loopback bridge service for remote pastes
│   ├── config_inspector.py      Inspect and validate config schemas
│   ├── dbcli.py                 Interactive database inspector (Postgres, MySQL, SQLite)
│   ├── diskguard.py             Automated build cache & disk space guard
│   ├── dkutil.py                Infrastructure-agnostic container manager
│   ├── envcfg.py                Interactive .env configuration manager
│   ├── envmgr.py                PATH & environment variable manager
│   ├── git_scanner.py           Scan project dirs, report uncommitted repos
│   ├── help_enforcer.py         Validator for --help/manual rules
│   ├── ngutil.py                Nginx configurator and tailing utility
│   ├── portwatch.py             Process port watcher & killer
│   └── schedmgr.py              Cross-platform schedule task manager (cron/schtasks)
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
| `d` | Show unique directory stack with home-relative paths (`~`) |
| `1` to `9` | Jump directly to stack index target |

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
| `envmgr` | Safe marked-block PATH directory manager (list, add, remove, clean) |
| `diskguard` | Automated concurrent disk space and cache guard (Node, Python, Java, Gradle, Android) |
| `envcfg` | Interactive `.env` file setup manager and wizard (list, set, get, wizard) |
| `dbcli` | Zero-dependency database CLI explorer (tables, schema, query, select) |
| `portwatch <port>` | Identify and kill active processes listening on port |
| `clipcopy` / `clippaste` | Cross-host clipboard sharing (OSC 52 and HTTP reverse forward bridge) |
| `clipservice` | Manage large-data loopback clipboard background service (`start`/`stop`/`status`) |
| `schedmgr` | Cross-platform scheduled task manager (crontab / Windows Task Scheduler) with run logging |
| `dklist` / `dkclean` / `dklogs` | List running containers / Prune unused items / Tail logs |
| `ngstat` / `ngerr` / `ngconf` | Nginx site proxy creator, status tester, error log tailer, and SSLCertbot |
| `scripts/sandbox.sh [--no-install] [cmd]` | Runs an isolated subshell (or custom command) in a temporary folder under `/tmp/`. Includes `deactivate` alias for quick exit and cleanup. |
| `uninstall.sh` | Cleans up local bin and runs `--cleanup` on stateful scripts before deleting symlinks |
| `PyScp/help_enforcer.py` | Validates that all functions/scripts conform to `--help` and `manual` registry rules |

---

## Server Utilities: envcfg & dbcli

When setting up `shell-kit` on a headless server (like an EC2 instance) via the `--server` profile, two powerful utilities are installed to manage configurations and databases without leaving the terminal:

### 1. Environment Configuration Manager (`envcfg`)
Useful for setting up project environment files on remote servers without opening screen-oriented editors like `vim` or `nano`:
*   **Initialize project configuration**:
    ```bash
    envcfg init
    ```
    *(Finds `.env.example`, copies it to `.env`, and launches an interactive setup wizard prompting you for each key.)*
*   **Scan for missing configurations**: If a git pull adds new keys to `.env.example`, running `envcfg init` again will detect them and only prompt for the missing keys.
*   **View configurations safely**:
    ```bash
    envcfg list
    ```
    *(Prints all variables. Secrets like passwords and API keys are automatically hidden. Use `-s` or `--show-secrets` to show them.)*

### 2. Database Debugging Assistant (`dbcli`)
Provides a zero-dependency interactive console and CLI to Postgres, MySQL, and SQLite databases. It automatically reads connection credentials from the local `.env` file:
*   **Run as a database system user (SSH socket connections)**:
    On remote servers, databases often require running commands as a specific system user (e.g., `postgres` for Postgres socket connections). Use the `-u` or `--sudo-user` flag:
    ```bash
    dbcli -u postgres
    ```
*   **Execute raw SQL**:
    ```bash
    dbcli query "SELECT count(*) FROM users;"
    ```
*   **Quickly inspect schemas**:
    ```bash
    dbcli schema users
    ```
*   **Interactive REPL**:
    Run `dbcli` (or `dbcli -u postgres`) to enter a persistent shell with tab completion for SQL keywords and database table names.

### 3. Unified Cross-Host Clipboard (`clipcopy` / `clippaste`)
Allows copy/paste operations across local desktops and remote SSH hosts:
*   **OSC 52 Escape Sequences**: When inside an SSH session, running `clipcopy` automatically encodes standard input into Base64 and outputs it as an OSC 52 sequence. The client terminal emulates this to copy it directly into your local desktop clipboard.
*   **Large-Data Tunneling Bridge (`--huge` / `--bridge`)**:
    If copying large log files or payloads (> 64KB), OSC 52 can truncate. Run `clipservice start` on your local workstation (requires interactive consent) and connect via an SSH reverse port forward:
    ```bash
    ssh -R 9999:localhost:9999 server-host
    ```
    You can then copy and paste huge payloads securely over the encrypted tunnel:
    ```bash
    # Remote to Local
    cat huge.log | clipcopy --huge
    
    # Local to Remote
    clippaste --huge > huge_local.log
    ```

### 4. Cross-Platform Scheduled Task Manager (`schedmgr`)
Configure and monitor periodic tasks natively using the OS scheduler (crontab on Linux/macOS, Windows Task Scheduler on Windows):
*   **Interactive Task Wizard**:
    ```bash
    schedmgr add
    ```
    *(Launches a guided prompt asking for the task name, command, daily/weekly/monthly frequency, day selectors, and execution time, then automatically registers the task natively.)*
*   **Status & Execution Dashboard**:
    ```bash
    schedmgr list
    ```
    *(Renders a tabular layout showing task names, commands, native frequencies, enabled/disabled states, last run times, and execution exit results.)*
*   **Diagnostic Logs**:
    ```bash
    schedmgr logs <task_name>
    ```
    *(Tails standard output and exit logs captured for a specific scheduled task.)*
*   **Task State Control**:
    Use `schedmgr pause <name>`, `schedmgr resume <name>`, or `schedmgr remove <name>` to toggle or delete schedules.

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