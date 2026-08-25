#!/usr/bin/env python3
import os
import sys
import re

# Color formatting constants for stderr output
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
RESET = "\033[0m"

START_MARKER = "# >>> shell-kit envmgr start >>>"
END_MARKER = "# <<< shell-kit envmgr end <<<"

HOME_DIR = os.environ.get("SHKIT_TEST_HOME") or os.path.expanduser("~")
TARGET_FILES = [
    os.path.join(HOME_DIR, ".bashrc"),
    os.path.join(HOME_DIR, ".profile"),
]

def to_native_path(path):
    """
    Translates Git Bash Unix paths to Windows native paths if running on Windows.
    Otherwise returns absolute path.
    """
    if sys.platform == "win32":
        path = os.path.expanduser(path)
        # Match /c/Users/... or /mnt/c/Users/...
        m = re.match(r'^/([a-zA-Z])(/|$)', path)
        if m:
            drive = m.group(1).upper()
            path = drive + ":" + path[2:]
        else:
            m = re.match(r'^/mnt/([a-zA-Z])(/|$)', path)
            if m:
                drive = m.group(1).upper()
                path = drive + ":" + path[6:]
        return os.path.normpath(path)
    return os.path.abspath(os.path.expanduser(path))

def to_unix_path(path):
    """
    Converts native Windows path to Git Bash style Unix path if on Windows.
    """
    if sys.platform == "win32":
        path = os.path.normpath(path).replace('\\', '/')
        m = re.match(r'^([a-zA-Z]):', path)
        if m:
            drive = m.group(1).lower()
            path = f"/{drive}{path[2:]}"
    return path

def parse_managed_entries(file_path):
    """
    Parses managed entries from a startup file.
    Returns: (list of dicts, list of all lines)
    Dict: {"path": str, "prepend": bool}
    """
    if not os.path.exists(file_path):
        return [], []
        
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        
    entries = []
    start_idx = -1
    end_idx = -1
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped == START_MARKER:
            start_idx = idx
        elif stripped == END_MARKER:
            end_idx = idx
            
    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
        for idx in range(start_idx + 1, end_idx):
            line = lines[idx].strip()
            if not line:
                continue
            m = re.search(r'\*":([^"]+):"\*', line)
            if m:
                path = m.group(1)
                is_prepend = ':$PATH"' in line or ':$PATH\'' in line
                entries.append({"path": path, "prepend": is_prepend})
    return entries, lines

def write_managed_entries(file_path, entries):
    """
    Writes managed entries back to the startup file.
    If entries list is empty, removes the block.
    """
    dir_name = os.path.dirname(file_path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)
        
    if not os.path.exists(file_path):
        with open(file_path, "w", encoding="utf-8") as f:
            pass
            
    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = f.readlines()
        
    start_idx = -1
    end_idx = -1
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped == START_MARKER:
            start_idx = idx
        elif stripped == END_MARKER:
            end_idx = idx
            
    block_lines = []
    if entries:
        block_lines.append(START_MARKER + "\n")
        for entry in entries:
            p = entry["path"]
            if entry["prepend"]:
                block_lines.append(f'[[ ":$PATH:" != *":{p}:"* ]] && export PATH="{p}:$PATH"\n')
            else:
                block_lines.append(f'[[ ":$PATH:" != *":{p}:"* ]] && export PATH="$PATH:{p}"\n')
        block_lines.append(END_MARKER + "\n")
        
    if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
        new_lines = lines[:start_idx] + block_lines + lines[end_idx + 1:]
    elif start_idx != -1:
        new_lines = lines[:start_idx] + block_lines
    elif end_idx != -1:
        new_lines = block_lines + lines[:end_idx] + lines[end_idx + 1:]
    else:
        if lines and not lines[-1].endswith("\n"):
            lines[-1] = lines[-1] + "\n"
        new_lines = lines + block_lines
        
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

def print_help():
    sys.stderr.write(f"""{CYAN}{BOLD}envmgr — PATH & Environment Variable Manager{RESET}
Manage active session PATH and persistent startup scripts.

{BOLD}Usage:{RESET}
  envmgr list <path_str>
  envmgr add <path_str> <dir_path> [--prepend]
  envmgr remove <path_str> <index_or_path>
  envmgr clean <path_str>
  envmgr --cleanup

{BOLD}Commands:{RESET}
  {GREEN}list{RESET}      Display active PATH directories with validation and managed tags
  {GREEN}add{RESET}       Safely add a directory to startup profile files and active session
  {GREEN}remove{RESET}    Remove a directory from startup files and active session
  {GREEN}clean{RESET}     Remove dead or duplicate directories from active session & profiles
  {GREEN}--cleanup{RESET} Clean up all envmgr blocks from startup files (for uninstaller)
""")

def do_list(path_str):
    active_paths = [p for p in path_str.split(":") if p]
    
    # Collect all managed paths
    managed_set = set()
    for f in TARGET_FILES:
        entries, _ = parse_managed_entries(f)
        for e in entries:
            managed_set.add(e["path"])
            
    sys.stderr.write(f"\n{CYAN}{BOLD}Active Session PATH Directories:{RESET}\n")
    sys.stderr.write("-" * 65 + "\n")
    
    seen = set()
    for idx, path in enumerate(active_paths, 1):
        native = to_native_path(path)
        exists = os.path.exists(native) and os.path.isdir(native)
        is_dup = path in seen
        seen.add(path)
        
        is_managed = path in managed_set
        
        # Build status string
        status_tags = []
        if is_managed:
            status_tags.append(f"{GREEN}[MANAGED]{RESET}")
        if not exists:
            status_tags.append(f"{RED}[NOT FOUND]{RESET}")
        if is_dup:
            status_tags.append(f"{YELLOW}[DUPLICATE]{RESET}")
            
        status_str = " ".join(status_tags)
        if status_str:
            status_str = f" {status_str}"
            
        color = CYAN if is_managed else (RESET if exists else YELLOW)
        sys.stderr.write(f"  {idx:2d}. {color}{path}{RESET}{status_str}\n")
        
    sys.stderr.write("-" * 65 + "\n\n")

def do_add(path_str, dir_path, prepend=False):
    native_dir = to_native_path(dir_path)
    if not os.path.exists(native_dir):
        sys.stderr.write(f"{RED}[ERROR] Directory '{dir_path}' (resolved: '{native_dir}') does not exist on disk.{RESET}\n")
        sys.exit(1)
    if not os.path.isdir(native_dir):
        sys.stderr.write(f"{RED}[ERROR] '{dir_path}' is not a directory.{RESET}\n")
        sys.exit(1)
        
    unix_dir = to_unix_path(native_dir)
    
    # Read/write both TARGET_FILES
    for fpath in TARGET_FILES:
        entries, _ = parse_managed_entries(fpath)
        # Check if already managed
        exists_in_config = any(e["path"] == unix_dir for e in entries)
        if not exists_in_config:
            new_entry = {"path": unix_dir, "prepend": prepend}
            if prepend:
                entries.insert(0, new_entry)
            else:
                entries.append(new_entry)
            write_managed_entries(fpath, entries)
            sys.stderr.write(f"{GREEN}[OK] Added to {os.path.basename(fpath)}: {unix_dir}{RESET}\n")
        else:
            sys.stderr.write(f"{YELLOW}[INFO] Already managed in {os.path.basename(fpath)}: {unix_dir}{RESET}\n")
            
    # Calculate new active PATH
    active_paths = [p for p in path_str.split(":") if p]
    if unix_dir not in active_paths:
        if prepend:
            active_paths.insert(0, unix_dir)
        else:
            active_paths.append(unix_dir)
        new_path_str = ":".join(active_paths)
        print(f'export PATH="{new_path_str}"')
        sys.stderr.write(f"{GREEN}[SUCCESS] Added '{unix_dir}' to active PATH.{RESET}\n")
    else:
        sys.stderr.write(f"{YELLOW}[INFO] '{unix_dir}' is already present in the active PATH.{RESET}\n")

def do_remove(path_str, target):
    active_paths = [p for p in path_str.split(":") if p]
    
    target_path = None
    if target.isdigit():
        idx = int(target) - 1
        if 0 <= idx < len(active_paths):
            target_path = active_paths[idx]
        else:
            sys.stderr.write(f"{RED}[ERROR] Invalid index: {target}. Valid range: 1 to {len(active_paths)}.{RESET}\n")
            sys.exit(1)
    else:
        target_path = target
        
    # Resolve target_path to Unix style for configuration comparison
    native_target = to_native_path(target_path)
    unix_target = to_unix_path(native_target)
    
    # Verify target path is managed
    is_managed_any = False
    for fpath in TARGET_FILES:
        entries, _ = parse_managed_entries(fpath)
        if any(e["path"] == unix_target for e in entries):
            is_managed_any = True
            break
            
    if not is_managed_any:
        sys.stderr.write(f"{RED}[ERROR] '{target_path}' is not managed by envmgr.{RESET}\n")
        sys.stderr.write(f"{YELLOW}[INFO] It may be defined system-wide or manually in your startup scripts.{RESET}\n")
        sys.exit(1)
        
    # Remove from TARGET_FILES
    for fpath in TARGET_FILES:
        entries, _ = parse_managed_entries(fpath)
        updated_entries = [e for e in entries if e["path"] != unix_target]
        if len(entries) != len(updated_entries):
            write_managed_entries(fpath, updated_entries)
            sys.stderr.write(f"{GREEN}[OK] Removed from {os.path.basename(fpath)}: {unix_target}{RESET}\n")
            
    # Calculate new active PATH (remove all occurrences of target_path and unix_target)
    new_active_paths = [p for p in active_paths if p != target_path and p != unix_target]
    new_path_str = ":".join(new_active_paths)
    print(f'export PATH="{new_path_str}"')
    sys.stderr.write(f"{GREEN}[SUCCESS] Removed '{unix_target}' from active PATH.{RESET}\n")

def do_clean(path_str):
    active_paths = [p for p in path_str.split(":") if p]
    
    # Filter active path directories
    cleaned_active = []
    seen = set()
    removed_dead = []
    removed_dup = []
    
    for path in active_paths:
        native = to_native_path(path)
        exists = os.path.exists(native) and os.path.isdir(native)
        if not exists:
            removed_dead.append(path)
            continue
        if path in seen:
            removed_dup.append(path)
            continue
        seen.add(path)
        cleaned_active.append(path)
        
    # Clean managed config files (both dead paths and duplicates)
    for fpath in TARGET_FILES:
        entries, _ = parse_managed_entries(fpath)
        cleaned_entries = []
        config_seen = set()
        for e in entries:
            p = e["path"]
            native = to_native_path(p)
            exists = os.path.exists(native) and os.path.isdir(native)
            if not exists:
                sys.stderr.write(f"{YELLOW}[CLEAN] Removed dead path from {os.path.basename(fpath)}: {p}{RESET}\n")
                continue
            if p in config_seen:
                sys.stderr.write(f"{YELLOW}[CLEAN] Removed duplicate path from {os.path.basename(fpath)}: {p}{RESET}\n")
                continue
            config_seen.add(p)
            cleaned_entries.append(e)
        if len(entries) != len(cleaned_entries):
            write_managed_entries(fpath, cleaned_entries)
            
    # Print status of active PATH changes
    if removed_dead:
        sys.stderr.write(f"{YELLOW}[CLEAN] Removed {len(removed_dead)} non-existent directory entries from active PATH.{RESET}\n")
    if removed_dup:
        sys.stderr.write(f"{YELLOW}[CLEAN] Removed {len(removed_dup)} duplicate directory entries from active PATH.{RESET}\n")
        
    new_path_str = ":".join(cleaned_active)
    print(f'export PATH="{new_path_str}"')
    sys.stderr.write(f"{GREEN}[SUCCESS] Active PATH cleaned.{RESET}\n")

def do_cleanup():
    # Remove envmgr block from both files
    for fpath in TARGET_FILES:
        if os.path.exists(fpath):
            write_managed_entries(fpath, [])
            sys.stderr.write(f"{GREEN}[CLEANUP] Removed envmgr block from {fpath}{RESET}\n")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print_help()
        sys.exit(0)
        
    cmd = sys.argv[1]
    
    if cmd == "--cleanup":
        do_cleanup()
        sys.exit(0)
        
    if len(sys.argv) < 3:
        sys.stderr.write(f"{RED}[ERROR] Command '{cmd}' requires at least <path_str> argument.{RESET}\n")
        print_help()
        sys.exit(1)
        
    path_str = sys.argv[2]
    
    if cmd == "list":
        do_list(path_str)
    elif cmd == "add":
        if len(sys.argv) < 4:
            sys.stderr.write(f"{RED}[ERROR] 'add' requires <dir_path> argument.{RESET}\n")
            sys.exit(1)
        dir_path = sys.argv[3]
        prepend = "--prepend" in sys.argv or "-p" in sys.argv
        do_add(path_str, dir_path, prepend)
    elif cmd == "remove":
        if len(sys.argv) < 4:
            sys.stderr.write(f"{RED}[ERROR] 'remove' requires <index_or_path> argument.{RESET}\n")
            sys.exit(1)
        target = sys.argv[3]
        do_remove(path_str, target)
    elif cmd == "clean":
        do_clean(path_str)
    else:
        sys.stderr.write(f"{RED}[ERROR] Unknown command: {cmd}{RESET}\n")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
