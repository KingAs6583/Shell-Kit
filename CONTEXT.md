# shell-kit — Context & Project Summary
> Last updated: 2026-08-23 | 4 commits on `main`

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
| `bash/.bash_function.both` | ✅ All | Git setup, SSH key management |
| `bash/.bash_function.linux` | 🐧 Linux | apt update, sysinfo, RAM, scandisk |
| `bash/.bash_function.windows` | 🪟 Windows | Explorer, path converters, devmode |
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
│   └── .profile                 PATH additions
├── scripts/
│   ├── history-clean.sh         Dedup ~/.bash_history
│   ├── setup-codebase-memory.sh Install codebase-memory-mcp
│   ├── scan-packages.sh         Async package history scanner
│   └── linux/
│       ├── update.sh            apt full update
│       ├── system-info.sh       dmidecode hardware info
│       └── ram-info.sh          RAM details
├── .gitignore
├── .gitattributes               Enforce LF
├── manifest.json                13 tracked files with platform targets
├── install.sh
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

### Cross-platform Functions (`.bash_function.both`)
- `setupGithubSshKey` — interactive ed25519 key generator
- `setupGit "msg" <url>` — init + first commit + push
- `upload "msg"` — add + commit + push
- `globalConfig / localConfig` — git identity setup
- `listSshConfig` — list SSH host aliases

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

- [ ] **Backup scanner** — check git repos for uncommitted changes + zip asset/vault folders
  - `git-scanner.sh` — scan project dirs, report uncommitted repos
  - `asset-backup.sh` — zip non-git folders (documents, assets, vaults)
  - `backup.sh` — orchestrator that runs both
  - Lossless zip, cross-platform (zip/tar.gz), config-driven (JSON)

---

## Migration Status

| Old Repo | Status |
|----------|--------|
| `LinuxShellScripts` | ✅ Decommissioned — all useful scripts migrated |
| `~/.bashrc` (original) | ✅ Replaced by shell-kit version |

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
hhelp          # history cheat sheet
prompts mcp    # AI prompt for codebase-memory-mcp
dotfiles verify # check sync status
pkgscan        # rescan installed packages
pyvenvs        # find Python venvs
setupGithubSshKey  # generate GitHub SSH key
```

## Next Steps
1. Add GitHub remote: `git remote add origin git@github.com:KingAs6583/shell-kit.git`
2. Push: `git push -u origin main`
3. Implement backup scanner (see Planned section above)