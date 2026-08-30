# shell-kit — Context & Project Summary
> Last updated: 2026-08-30 | 6 commits on `main`

## What This Repo Is
`shell-kit` is a personal shell toolkit and dotfiles manager for **Windows (Git Bash)**, **Linux**, and **macOS**.
It replaces the old `LinuxShellScripts` repo, which has been decommissioned.

Repo location:
- Windows: `D:\Projects\shell-kit`
- Linux/Mac: `~/shell-kit`

---

## Architecture

### Three-Layer Function System
Functions are split by platform compatibility:

| File | Platform | Purpose |
|------|----------|---------|
| `bash/.bash_function.both` | All | Git setup, SSH key management |
| `bash/.bash_function.linux` | Linux | apt update, sysinfo, RAM, scandisk |
| `bash/.bash_function.windows` | Windows | Explorer, path converters, devmode |
| `bash/.bash_function` | legacy | Deprecated monolithic file |

`.bashrc` auto-detects `$PLATFORM` and sources only the appropriate file.

### Dotfiles Management
- `manifest.json` — registry of every tracked file with install paths per OS
- `install.sh` — creates **symlinks** (copies if Developer Mode is off on Windows)
- `verify.sh` — audits local vs git, shows status table, offers interactive fixes
- `dotfiles.sh` — CLI: `dotfiles verify|install|sync|status`

---

## File Structure

```
shell-kit/
├── bash/
│   ├── .bashrc                  Main config (443 lines)
│   ├── .bash_profile            Login shell bridge
│   ├── .bash_function           Legacy (22kb, deprecated)
│   ├── .bash_function.both      SSH/git functions (8kb)
│   ├── .bash_function.linux     Linux functions (6.5kb)
│   ├── .bash_function.windows   Windows functions (3.8kb)
│   ├── .profile                 PATH additions
│   └── lazy/                    Lazy-loaded function implementations
├── PyScp/
│   ├── asset_backup.py          Zip non-git folders (documents, assets, vaults)
│   ├── backup.py                Backup orchestrator
│   ├── clip_helper.py           Local OS clipboard access abstractions
│   ├── clip_service.py          Local loopback bridge service for remote pastes
│   ├── config_inspector.py      Inspect and validate config schemas
│   ├── dbcli.py                 Interactive database inspector (Postgres, MySQL, SQLite)
│   ├── diskguard.py             Automated build cache & disk space guard
│   ├── dkutil.py                Infrastructure-agnostic container manager
│   ├── envcfg.py                Interactive .env configuration manager
│   ├── envmgr.py                PATH & environment variable manager
│   ├── git_scanner.py           Scan project dirs, report uncommitted repos
│   ├── help_enforcer.py         Validator for --help rules and manual command
│   ├── ngutil.py                Nginx configurator and tailing utility
│   ├── portwatch.py             Process port watcher & killer
│   └── schedmgr.py              Cross-platform schedule task manager (cron/schtasks)
├── scripts/
│   ├── history-clean.sh         Dedup ~/.bash_history
│   ├── setup-codebase-memory.sh Install codebase-memory-mcp
│   ├── scan-packages.sh         Async package history scanner
│   ├── sandbox.sh               Isolated testing environment inside /tmp
│   └── linux/
│       ├── update.sh            apt full update
│       ├── system-info.sh       dmidecode hardware info
│       └── ram-info.sh          RAM details
├── .gitignore
├── .gitattributes               Enforce LF
├── manifest.json                27 tracked files with platform targets
├── install.sh
├── uninstall.sh                 Uninstaller for utility scripts
├── verify.sh
├── dotfiles.sh
└── README.md
```

---

## Key Features Built

### Shell Config
- **Two-line prompt**: path (cyan) + git branch (yellow) + dirty `*` (red) + venv + `❯` arrow
- **PLATFORM detection**: `windows | linux | mac` exported at startup
- **10,000 line history** with cross-session sync
- **Case-insensitive tab completion**, cdspell, colored completions

### Aliases & Functions
- Git: `gs ga gc gp gpl gd gds glog gb gco gsw`
- Dev: `lint lintfix tsc typecheck dev build start`
- Nav: `.. ... .... mkcd`
- Files: `t t3 td dirsize dirsize5 filesize fdiff ddiff`
- Grep: `gr gi gx gf todo`
- History: `h hl hhelp hclean`
- Safety: `rm` (blocked on `.` `*` `/` `~`), `mv -i`, `cp -i`
- Packages: `pkglist pkgscan`
- Python: `pyvenvs`
- AI: `prompts mcp|review|debug|tokens`
- Dotfiles: `dotfiles verify|install|sync|status`
- Backup: `bkscan` (scan git repos), `bkrun` (run backup), `bkrestore` (restore assets), `cfginspect` (validate config)

### Cross-platform Functions (`.bash_function.both`)
- `setupGithubSshKey` — interactive ed25519 key generator
- `setupGit "msg" <url>` — init + first commit + push
- `upload "msg"` — add + commit + push
- `globalConfig / localConfig` — git identity setup
- `listSshConfig` — list SSH host aliases
- `envcfg` — interactive `.env` configuration manager and setup wizard
- `dbcli` — zero-dependency database interactive client and query assistant
- `diskguard` — automated disk space & package cache cleanup utility (Gradle, Java, Node, etc.)
- `dklist / dkclean / dklogs` — Docker/Podman container list, logs, and prune diagnostics
- `ngstat / ngerr / ngconf` — Nginx config generator, noise-filtered log tailer, and Certbot SSL setup
- `clipcopy / clippaste` — cross-host clipboard sharing (OSC 52 and reverse-forward port bridge)
- `clipservice` — manager for background large-data clipboard tunnel bridge
- `schedmgr` — cross-platform scheduled task manager (crontab / Windows Task Scheduler) with run logging

### Linux Functions (`.bash_function.linux`)
- `sysupdate` — full apt cycle
- `aptclean` — autoremove + autoclean
- `sysinfo [type]` — dmidecode (1=system, 4=cpu, 17=ram)
- `raminfo` — free + dmidecode RAM
- `scandisk [path]` — large files, old files

### Windows Functions (`.bash_function.windows`)
- `explore [path]` — open in Explorer
- `open <file|url>` — default app
- `devmode` — check Developer Mode status
- `toUnix / toWin` — path converters
- `killwin / pslist` — process management

### Scripts
- `hclean` — dedup `~/.bash_history`, keeps most recent, backs up to `.bak`
- `pkgscan` — async at startup, scans history for `apt/pip/npm/brew/cargo/choco/winget`
- `pkglist` — instant view of cached package list
- `setup-codebase-memory.sh` — cross-platform MCP installer

---

## Planned / In Progress

- [x] **Backup scanner** — check git repos for uncommitted changes + zip asset/vault folders
  - `git_scanner.py` — scan project dirs, report uncommitted repos (`bkscan` command)
  - `asset_backup.py` — zip non-git folders (documents, assets, vaults, `bkrun` / `bkrestore` commands)
  - `backup.py` — orchestrator that runs both (`bkrun` command)
  - `config_inspector.py` — inspect and validate JSON configurations (`cfginspect` command)
  - Lossless zip, cross-platform (Windows/Linux/Mac), config-driven (`backup_config.json`)
- [x] **Mandatory Help & Lazy Loading**
  - Centralized `manual` command for help cheat sheet
  - Minimal `--help` / `-h` check on all functions
  - Lazy loading for heavy functions (`setupGithubSshKey`, `setupGit`, `sysinfo`, `raminfo`, `scandisk`)
  - Automated validation script `help_enforcer.py`
- [x] **Self-Cleanup Option & Safe Uninstallation**
  - Added `--cleanup` to stateful scripts (`scan-packages.sh`, `history-clean.sh`) to clean up their own caches and backups.
  - Configured `uninstall.sh` to dynamically run `--cleanup` on scripts that support it before deleting symlinks.
- [x] **Interactive Environment, Port, Dotenv, DB & Directory Stack Utilities**
  - `envmgr.py` — PATH manager with safe marked-block profile editing (`envmgr` command)
  - `portwatch.py` — process port checker & interactive force-killer (`portwatch` command)
  - `envcfg.py` — interactive `.env` configuration wizard & manager (`envcfg` command)
  - `dbcli.py` — interactive database client and schema explorer (`dbcli` command)
  - `d` / `1-9` — unique directory stack navigator and prompt jump shortcuts
- [x] **Automated Disk Space & Cache Guard (diskguard)**
  - `diskguard.py` — concurrent project build folder (Gradle/Android/Node/Maven) and package cache scanner & cleanup utility (`diskguard` command)
- [x] **Infrastructure-Agnostic Backend Utilities (dkutil & ngutil)**
  - `dkutil.py` — Docker/Podman container manager (list, clean, logs)
  - `ngutil.py` — Nginx configurator, status checker, filtered log tailer, and Certbot SSL setup
- [x] **Unified Cross-Host Clipboard (clipcopy & clippaste)**
  - `clip_helper.py` — cross-platform system clipboard access helper
  - `clip_service.py` — local bridge microservice for large data pastes
- [x] **Cross-Platform Schedule & Monitoring Manager (schedmgr)**
  - `schedmgr.py` — OS-native task scheduler interface with execution logging

---

## Migration Status

| Old Repo | Status |
|----------|--------|
| `LinuxShellScripts` | Decommissioned — all useful scripts migrated |
| `~/.bashrc` (original) | Replaced by shell-kit version |

---

## Git History

```
3b48fa8  docs: comprehensive README
8e31744  Phase 3: platform-split functions, Linux scripts, .gitignore
fc67a57  Add .gitattributes (enforce LF)
8c285fa  Initial commit: shell-kit personal shell toolkit
```

---

## Quick Reference

```bash
# Run in new Git Bash window (not VSCode terminal)
manual         # central manual / help command
hhelp          # history cheat sheet
prompts mcp    # AI prompt for codebase-memory-mcp
dotfiles verify # check sync status
pkgscan        # rescan installed packages
pyvenvs        # find Python venvs
setupGithubSshKey  # generate GitHub SSH key
```

## Developer Utilities
- **Sandbox Testing**: Run `bash scripts/sandbox.sh [--no-install] [command]` to spin up an isolated environment with a temporary mock home directory.
  - `--no-install`: Starts a clean sandbox with an empty home directory.
  - `[command]`: Executes the specified command inside the sandbox and exits immediately.
  - `deactivate` alias: Run `deactivate` inside the interactive sandbox shell to exit and trigger auto-cleanup.
- **Uninstaller**: Run `./uninstall.sh` to clean up utility and lazy scripts from the local bin. Automatically triggers `--cleanup` on scripts that support it to remove local state (caches, backups, logs).