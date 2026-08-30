#!/usr/bin/env python3
import os
import sys
import time
import shutil
import argparse
import concurrent.futures
from datetime import datetime

# Color formatting constants
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_help():
    sys.stderr.write(f"""{CYAN}{BOLD}diskguard — Automated Disk Space & Cache Guard{RESET}
Scan and clean up build directories and package caches concurrently.

{BOLD}Usage:{RESET}
  diskguard [scan] [options]  Scan for reclaimable space and run interactive cleanup (default)
  diskguard clean [options]   Automated sweep of pre-selected inactive caches without prompt
  diskguard --cleanup         Self-cleanup compliance flag (no-op)

{BOLD}Options:{RESET}
  -h, --help           Show this help message and exit
  -a, --age DAYS       Age threshold in days for 'inactive' classification (default: 90)
  -p, --path PATHS     Comma-separated custom project directories to scan (overrides defaults)
  -y, --yes            Skip confirmation prompt in 'clean' mode

{BOLD}Note:{RESET} To schedule automated cleanups periodically, use the unified scheduler:
      {GREEN}schedmgr add{RESET}
""")

def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"

def get_dir_size(path):
    """
    Computes total directory size recursively.
    """
    total_size = 0
    try:
        for entry in os.scandir(path):
            try:
                if entry.is_symlink():
                    continue
                elif entry.is_file(follow_symlinks=False):
                    total_size += entry.stat().st_size
                elif entry.is_dir(follow_symlinks=False):
                    total_size += get_dir_size(entry.path)
            except OSError:
                pass
    except OSError:
        pass
    return total_size

def scan_project_root(root):
    """
    Scans project directory and prunes subdirectories recursively.
    """
    targets = []
    target_names = {
        "node_modules": "Node.js (node_modules)",
        "__pycache__": "Python Cache (__pycache__)",
        ".venv": "Python Virtual Env (.venv)",
        "venv": "Python Virtual Env (venv)",
        ".pytest_cache": "Python Test Cache (.pytest_cache)",
        ".tox": "Python Tox Cache (.tox)",
        "build": "Build Artifacts (build)",
        "target": "Maven/Java Build (target)",
        ".gradle": "Gradle Project Cache (.gradle)",
        ".cxx": "Android C++ Build (.cxx)"
    }
    
    try:
        for dirpath, dirnames, filenames in os.walk(root, topdown=True):
            # Prune directories in-place to avoid deep walking
            to_remove = []
            for d in dirnames:
                if d in target_names:
                    full_path = os.path.join(dirpath, d)
                    category = target_names[d]
                    
                    size = get_dir_size(full_path)
                    try:
                        mtime = os.path.getmtime(full_path)
                    except OSError:
                        mtime = time.time()
                        
                    targets.append({
                        "path": full_path,
                        "category": category,
                        "size": size,
                        "mtime": mtime,
                        "is_global": False
                    })
                    to_remove.append(d)
                    
            # Apply pruning
            for d in to_remove:
                dirnames.remove(d)
                
    except Exception as e:
        sys.stderr.write(f"{YELLOW}[WARN] Scanning error in {root}: {e}{RESET}\n")
        
    return targets

def get_global_caches():
    """
    Measures global build and package caches directly.
    """
    home = os.path.expanduser("~")
    global_paths = {
        "Gradle Caches": os.path.join(home, ".gradle", "caches"),
        "Android Cache": os.path.join(home, ".android", "cache"),
        "Android Build Cache": os.path.join(home, ".android", "build-cache"),
        "Maven Repository": os.path.join(home, ".m2", "repository"),
        "NPM Cache": os.path.join(home, ".npm"),
        "Cargo Registry": os.path.join(home, ".cargo", "registry"),
        "Cargo Git Cache": os.path.join(home, ".cargo", "git"),
    }
    
    if sys.platform == "win32":
        global_paths["Pip Cache"] = os.path.join(home, "AppData", "Local", "pip", "cache")
    else:
        global_paths["Pip Cache"] = os.path.join(home, ".cache", "pip")
        
    targets = []
    for category, path in global_paths.items():
        if os.path.isdir(path):
            size = get_dir_size(path)
            try:
                mtime = os.path.getmtime(path)
            except OSError:
                mtime = time.time()
                
            targets.append({
                "path": path,
                "category": f"Global {category}",
                "size": size,
                "mtime": mtime,
                "is_global": True
            })
    return targets

def delete_target(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
        return True
    except Exception as e:
        print(f"{RED}[ERROR] Failed to delete {path}: {e}{RESET}")
        return False

def run_tui(targets, age_days):
    print(f"\n{CYAN}{BOLD}diskguard — Scan Results & Cleanup Menu{RESET}")
    print("=" * 90)
    
    # Classify selections
    selections = []
    for i, t in enumerate(targets):
        age_seconds = time.time() - t["mtime"]
        days = int(age_seconds / 86400)
        
        # Pre-select if local and inactive, or false if global (safer)
        is_inactive = days > age_days
        selected = is_inactive and not t["is_global"]
        
        selections.append(selected)
        
    while True:
        # Display Table
        print(f"{BOLD}{'No.':<4} {'Category':<30} {'Size':<10} {'Age (Days)':<10} {'Selected':<10} {'Path'}{RESET}")
        print("-" * 90)
        
        total_selected_size = 0
        total_scan_size = 0
        
        for i, t in enumerate(targets):
            age_seconds = time.time() - t["mtime"]
            days = int(age_seconds / 86400)
            
            sel_str = f"{GREEN}[x]{RESET}" if selections[i] else "[ ]"
            path_display = t["path"].replace(os.path.expanduser("~"), "~")
            
            # Truncate path if too long
            if len(path_display) > 35:
                path_display = "..." + path_display[-32:]
                
            print(f"{i+1:<4} {t['category']:<30} {format_size(t['size']):<10} {days:<10} {sel_str:<10} {path_display}")
            
            total_scan_size += t["size"]
            if selections[i]:
                total_selected_size += t["size"]
                
        print("-" * 90)
        print(f"Total scanned size:  {BOLD}{format_size(total_scan_size)}{RESET}")
        print(f"Total selected size: {YELLOW}{BOLD}{format_size(total_selected_size)}{RESET}")
        print("=" * 90)
        
        print(f"{BOLD}Interactive Commands:{RESET}")
        print("  - Type number(s) (e.g. '1', '1,3,4') to toggle selections")
        print("  - Type 'all' to select all, 'none' to uncheck all, 'inactive' to select old caches")
        print("  - Type 'delete' (or 'd') to delete selected targets")
        print("  - Type 'quit' (or 'q') to exit")
        print("-" * 90)
        
        sys.stdout.write(f"Choice ❯ ")
        sys.stdout.flush()
        cmd = sys.stdin.readline().strip().lower()
        
        if cmd in ("q", "quit"):
            print("Exit without deletion.")
            sys.exit(0)
            
        elif cmd in ("d", "delete"):
            selected_count = sum(1 for s in selections if s)
            if selected_count == 0:
                print(f"{YELLOW}No targets selected for deletion.{RESET}")
                continue
                
            sys.stdout.write(f"\n{RED}{BOLD}Are you sure you want to permanently delete these {selected_count} target(s)? (y/N): {RESET}")
            sys.stdout.flush()
            confirm = sys.stdin.readline().strip().lower()
            if confirm in ("y", "yes"):
                deleted_size = 0
                success_count = 0
                for idx, selected in enumerate(selections):
                    if selected:
                        print(f"Deleting {targets[idx]['path']}...")
                        if delete_target(targets[idx]["path"]):
                            deleted_size += targets[idx]["size"]
                            success_count += 1
                print(f"\n{GREEN}[SUCCESS] Cleaned {success_count} targets. Reclaimed {format_size(deleted_size)}.{RESET}\n")
                break
            else:
                print("Deletion cancelled.")
                
        elif cmd == "all":
            selections = [True] * len(targets)
        elif cmd == "none":
            selections = [False] * len(targets)
        elif cmd == "inactive":
            for idx, t in enumerate(targets):
                age_seconds = time.time() - t["mtime"]
                days = int(age_seconds / 86400)
                selections[idx] = days > age_days
        else:
            # Parse toggle indices
            parts = cmd.replace(" ", "").split(",")
            valid_toggle = False
            for p in parts:
                if p.isdigit():
                    idx = int(p) - 1
                    if 0 <= idx < len(targets):
                        selections[idx] = not selections[idx]
                        valid_toggle = True
            if not valid_toggle:
                print(f"{RED}[ERROR] Unrecognized command or invalid index.{RESET}")
                time.sleep(1)

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        sys.stderr.write(f"{GREEN}[CLEANUP] diskguard requires no cleanup operations.{RESET}\n")
        sys.exit(0)
        
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("command", nargs="?", default="scan")
    parser.add_argument("-a", "--age", type=int, default=90)
    parser.add_argument("-p", "--path")
    parser.add_argument("-y", "--yes", action="store_true")
    parser.add_argument("-h", "--help", action="store_true")
    
    args, unknown = parser.parse_known_args()
    
    if args.help or args.command in ("-h", "--help"):
        print_help()
        sys.exit(0)
        
    if args.command not in ("scan", "clean", "cron"):
        sys.stderr.write(f"{RED}[ERROR] Unknown command: '{args.command}'{RESET}\n")
        print_help()
        sys.exit(1)
        
    # Redirect cron subcommands to the unified scheduler
    if args.command == "cron":
        print(f"\n{YELLOW}[INFO] diskguard's custom cron installer has been deprecated in favor of the unified scheduler.{RESET}")
        print("To easily schedule periodic disk cleanups, please run:")
        print(f"\n  {GREEN}{BOLD}schedmgr add{RESET}\n")
        sys.exit(0)
        
    # Resolve scan paths
    scan_paths = []
    if args.path:
        scan_paths = [p.strip() for p in args.path.split(",")]
    else:
        # Default roots
        home = os.path.expanduser("~")
        scan_paths = ["."]
        common_dirs = [
            os.path.join(home, "Projects"),
            os.path.join(home, "projects"),
            os.path.join(home, "Workspace"),
        ]
        if sys.platform == "win32":
            common_dirs.append("D:\\Projects")
            common_dirs.append("D:\\projects")
            
        for d in common_dirs:
            if os.path.isdir(d):
                scan_paths.append(d)
                
    # Normalize paths and remove nested subdirectories to optimize scans
    scan_paths = [os.path.abspath(p) for p in scan_paths if os.path.isdir(p)]
    scan_paths = sorted(list(set(scan_paths)), key=len)
    unique_paths = []
    for p in scan_paths:
        if not any(p.startswith(u + os.sep) or p == u for u in unique_paths):
            unique_paths.append(p)
            
    print(f"{CYAN}Scanning project directories concurrently...{RESET}")
    for p in unique_paths:
        print(f"  - Project Root: {p}")
        
    targets = []
    
    # Walk project roots concurrently using ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(unique_paths) or 1)) as executor:
        futures = {executor.submit(scan_project_root, root): root for root in unique_paths}
        for future in concurrent.futures.as_completed(futures):
            targets.extend(future.result())
            
    # Measure global caches
    print(f"{CYAN}Measuring global package and build caches...{RESET}")
    targets.extend(get_global_caches())
    
    if not targets:
        print(f"{GREEN}[OK] No reclaimable build caches or project directories found.{RESET}")
        sys.exit(0)
        
    # Execution mode
    if args.command == "clean":
        # Automated clean mode (no TUI)
        inactive_targets = []
        inactive_size = 0
        for t in targets:
            age_seconds = time.time() - t["mtime"]
            days = int(age_seconds / 86400)
            # Only auto-delete local inactive targets (safe defaults)
            if not t["is_global"] and days > args.age:
                inactive_targets.append(t)
                inactive_size += t["size"]
                
        if not inactive_targets:
            print(f"{GREEN}[OK] No inactive project caches (> {args.age} days) found to auto-clean.{RESET}")
            sys.exit(0)
            
        print(f"\n{YELLOW}{BOLD}Found {len(inactive_targets)} inactive cache(s) (> {args.age} days) totalling {format_size(inactive_size)}:{RESET}")
        for t in inactive_targets:
            print(f"  - {t['category']}: {t['path']} ({format_size(t['size'])})")
            
        if not args.yes:
            sys.stdout.write(f"\n{RED}{BOLD}Proceed with automated deletion of these inactive target(s)? (y/N): {RESET}")
            sys.stdout.flush()
            confirm = sys.stdin.readline().strip().lower()
            if confirm not in ("y", "yes"):
                print("Clean cancelled.")
                sys.exit(0)
                
        deleted_size = 0
        success_count = 0
        for t in inactive_targets:
            print(f"Deleting {t['path']}...")
            if delete_target(t["path"]):
                deleted_size += t["size"]
                success_count += 1
        print(f"\n{GREEN}[SUCCESS] Cleaned {success_count} target(s). Reclaimed {format_size(deleted_size)}.{RESET}\n")
        
    else:
        # Run Interactive TUI
        run_tUI_compat = run_tui
        run_tUI_compat(targets, args.age)

if __name__ == "__main__":
    main()
