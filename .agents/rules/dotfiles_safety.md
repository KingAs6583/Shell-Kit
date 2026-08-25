# Coding Rule: Dotfiles Safety, Backup Restoration, and Uninstallation

This rule mandates that any installation, modification, or tracking of user configuration files (dotfiles) within `shell-kit` must prioritize system safety, preserve user backups, and support clean uninstallation.

## Guidelines

1. **Mandatory Uninstallation Path**:
   - Any script, tool, or dotfile registered in `manifest.json` must be managed cleanly by `uninstall.sh`.
   - Never leave orphaned symlinks, copies, or directories behind on the user's system after uninstallation.

2. **Backup Preservation (Installation)**:
   - When installing or symlinking configuration files, the installer must check if a pre-existing user configuration file exists at that target.
   - If it exists and is not already a shell-kit symlink, the installer must back up the original file by appending `.bak` to its name (e.g., `~/.bashrc` -> `~/.bashrc.bak`).

3. **Backup Restoration (Uninstallation with `--restore`)**:
   - The uninstaller (`uninstall.sh`) must support a `--restore` flag.
   - When run with `--restore`, the uninstaller must:
     1. Remove the installed shell-kit configuration file (symlink or copy).
     2. Restore the original backup file (e.g., rename/move `~/.bashrc.bak` back to `~/.bashrc`) if it exists.
     3. Apply this restore flow to all files in the manifest, including core profiles (like `.bashrc`, `.profile`, `.bash_profile`, `.minttyrc`, and `.bash_keybindings`).

4. **Self-Cleanup Option**:
   - Every utility script that generates temporary files, caches, or logs must support a `--cleanup` or `--clean` flag.
   - `uninstall.sh` must call this cleanup option to remove all generated/untracked runtime assets before deleting the scripts.
