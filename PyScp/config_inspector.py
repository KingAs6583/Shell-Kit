#!/usr/bin/env python3
import os
import sys
import json
from pathlib import Path
from fnmatch import fnmatch

# Enable ANSI escape codes on Windows command prompt if needed
if os.name == 'nt':
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

# Terminal colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"

# Directories that are usually heavy and not standard configurations
BLACKLIST_DIR_PATTERNS = [
    "steam", "flatpak", "cache", ".cache", "npm", ".npm", "node_modules",
    "trash", ".trash", "venv", ".venv", "env", ".env", "wine", ".wine",
    "gradle", ".gradle", "docker", ".docker/volumes", "lock", "sockets"
]

def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def get_size_color(size_bytes):
    if size_bytes < 1024 * 1024: # < 1 MB
        return GREEN
    elif size_bytes < 50 * 1024 * 1024: # < 50 MB
        return YELLOW
    else:
        return RED

def get_dir_size(path, blacklist=None):
    if blacklist is None:
        blacklist = []
        
    total_size = 0
    try:
        for entry in os.scandir(path):
            if entry.is_symlink():
                continue
            
            # Check blacklist matching
            is_blacklisted = False
            entry_name_lower = entry.name.lower()
            for pattern in blacklist:
                if pattern in entry_name_lower:
                    is_blacklisted = True
                    break
            if is_blacklisted:
                continue
                
            if entry.is_file():
                total_size += entry.stat().st_size
            elif entry.is_dir():
                total_size += get_dir_size(entry.path, blacklist)
    except OSError:
        pass
    return total_size

def get_tracked_files():
    """Tries to find manifest.json and parse currently tracked target paths."""
    tracked = set()
    repo_root = Path(__file__).resolve().parent.parent
    manifest_path = repo_root / "manifest.json"
    
    # Detect current platform name (simple mapping)
    platform = "linux"
    if sys.platform == "win32":
        platform = "windows"
    elif sys.platform == "darwin":
        platform = "mac"
        
    if manifest_path.exists():
        try:
            with open(manifest_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for file_entry in data.get("files", []):
                    targets = file_entry.get("targets", {})
                    target_path = targets.get(platform)
                    if target_path:
                        # Standardize path, e.g. convert "~/.bashrc" to absolute
                        full_path = Path(target_path).expanduser().resolve()
                        tracked.add(str(full_path))
        except Exception as e:
            print(f"{YELLOW}Warning: Error parsing manifest.json: {e}{RESET}")
    return tracked

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Inspect user configuration directory for heavy folders, cache bloat, and untracked configuration files.")
    parser.parse_args()

    home = Path("~").expanduser().resolve()
    print(f"\n{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}HOME DIRECTORY CONFIGURATION INSPECTOR (~/){RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}")
    print(f"Scanning: {CYAN}{home}{RESET}\n")

    tracked_paths = get_tracked_files()
    scan_results = []
    
    # Common standard config files in ~/. to inspect specifically
    common_dotfiles = [
        ".bashrc", ".bash_profile", ".profile", ".gitconfig", ".ssh/config", 
        ".tmux.conf", ".vimrc", ".zshrc", ".condarc", ".npmrc", ".bash_aliases"
    ]
    
    # 1. Scan direct files in ~/.
    print(f"{BOLD}Direct Dotfiles in Home Directory:{RESET}")
    for dotfile_name in common_dotfiles:
        dotfile_path = home / dotfile_name
        if dotfile_path.exists():
            size = dotfile_path.stat().st_size
            is_tracked = str(dotfile_path.resolve()) in tracked_paths
            track_status = f"{GREEN}Tracked{RESET}" if is_tracked else f"{YELLOW}Untracked{RESET}"
            color = get_size_color(size)
            print(f"  {dotfile_name:<25} | Size: {color}{format_size(size):<10}{RESET} | Status: {track_status}")
            
            scan_results.append({
                "name": dotfile_name,
                "path": dotfile_path,
                "is_dir": False,
                "size": size,
                "tracked": is_tracked
            })
    print()

    # 2. Scan hidden directories in ~/. (depth 1)
    print(f"{BOLD}Hidden Configuration Directories in Home Directory:{RESET}")
    hidden_dirs = []
    for entry in os.scandir(home):
        if entry.is_dir() and entry.name.startswith(".") and not entry.name.startswith(".."):
            hidden_dirs.append(entry.name)
            
    hidden_dirs.sort()
    
    # Keep track of heavy folders for suggestions
    heavy_folders = []
    
    for d_name in hidden_dirs:
        d_path = Path(home / d_name)
        
        # Determine scanning behavior
        if d_name in [".config", ".local"]:
            # We will scan their subfolders up to 1 level deeper
            print(f"  {CYAN}{d_name}/{RESET} (Scanning subdirectories...)")
            try:
                for sub_entry in sorted(os.scandir(d_path), key=lambda e: e.name):
                    if sub_entry.is_dir():
                        sub_path = Path(sub_entry.path)
                        # Skip blacklisted subfolders to prevent huge lag
                        if sub_entry.name.lower() in BLACKLIST_DIR_PATTERNS:
                            # Just show size of cache/heavy folders without deep scanning
                            size = get_dir_size(sub_path, blacklist=BLACKLIST_DIR_PATTERNS)
                            color = get_size_color(size)
                            print(f"    {sub_entry.name:<23}/ | Size: {color}{format_size(size):<10}{RESET} [Heavy/Skipped Internal]")
                        else:
                            size = get_dir_size(sub_path)
                            color = get_size_color(size)
                            print(f"    {sub_entry.name:<23}/ | Size: {color}{format_size(size):<10}{RESET}")
                            
                        if size > 100 * 1024 * 1024: # > 100 MB
                            heavy_folders.append((f"{d_name}/{sub_entry.name}", size))
            except OSError:
                print(f"    {RED}Permission denied / Read error{RESET}")
        else:
            # Standard hidden directory
            size = get_dir_size(d_path, blacklist=BLACKLIST_DIR_PATTERNS)
            color = get_size_color(size)
            print(f"  {d_name:<27}/ | Size: {color}{format_size(size):<10}{RESET}")
            
            if size > 100 * 1024 * 1024:
                heavy_folders.append((d_name, size))
                
            scan_results.append({
                "name": d_name,
                "path": d_path,
                "is_dir": True,
                "size": size,
                "tracked": str(d_path.resolve()) in tracked_paths
            })
            
    # 3. Generate improvement recommendations
    print(f"\n{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}IMPROVEMENT RECOMMENDATIONS{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}")
    
    recommendations_count = 0
    
    # Recommendation A: Untracked dotfiles
    untracked_dotfiles = [r["name"] for r in scan_results if not r["is_dir"] and not r["tracked"]]
    if untracked_dotfiles:
        recommendations_count += 1
        print(f"{BOLD}[{recommendations_count}] Track Dotfiles in shell-kit:{RESET}")
        print(f"  The following config files exist in your home folder but are NOT tracked in your dotfiles repository:")
        for uf in untracked_dotfiles:
            print(f"    - ~/{uf}")
        print(f"  {YELLOW}Tip: Add them to `manifest.json` and run `./dotfiles.sh sync` to keep them backed up.{RESET}\n")
        
    # Recommendation B: Large folders that might need cleaning
    cache_path = home / ".cache"
    cache_size = get_dir_size(cache_path) if cache_path.exists() else 0
    if cache_size > 500 * 1024 * 1024: # > 500 MB
        recommendations_count += 1
        print(f"{BOLD}[{recommendations_count}] Large Cache Detected:{RESET}")
        print(f"  Your system cache folder ({CYAN}~/.cache{RESET}) is taking {RED}{format_size(cache_size)}{RESET}.")
        print(f"  {YELLOW}Tip: You can clean up old files safely or delete subfolders of tools you no longer use.{RESET}\n")
        
    npm_cache = home / ".npm"
    npm_cache_size = get_dir_size(npm_cache) if npm_cache.exists() else 0
    if npm_cache_size > 200 * 1024 * 1024: # > 200 MB
        recommendations_count += 1
        print(f"{BOLD}[{recommendations_count}] Clean NPM Cache:{RESET}")
        print(f"  Your NPM cache folder ({CYAN}~/.npm{RESET}) is taking {RED}{format_size(npm_cache_size)}{RESET}.")
        print(f"  {YELLOW}Tip: Run `npm cache clean --force` to reclaim this space.{RESET}\n")
        
    # Recommendation C: Specific heavy configuration folders
    if heavy_folders:
        recommendations_count += 1
        print(f"{BOLD}[{recommendations_count}] Heavy Configuration Folders:{RESET}")
        print(f"  The following configuration folders are taking more than 100 MB:")
        for name, size in heavy_folders:
            print(f"    - {CYAN}~/{name}{RESET} ({RED}{format_size(size)}{RESET})")
        print(f"  {YELLOW}Tip: Check if these folders contain logs, cache data, or local databases that can be pruned.{RESET}\n")
        
    if recommendations_count == 0:
        print(f"{GREEN}Everything looks optimized! No untracked dotfiles or heavy configuration logs detected.{RESET}")
    else:
        print(f"Total action items: {recommendations_count}. Review these tips to optimize your configuration storage.")
    print(f"{BOLD}{'=' * 80}{RESET}\n")

if __name__ == "__main__":
    main()
