#!/usr/bin/env python3
import os
import sys
import subprocess
from pathlib import Path

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

def main():
    script_dir = Path(__file__).resolve().parent
    git_scanner_path = script_dir / "git_scanner.py"
    asset_backup_path = script_dir / "asset_backup.py"
    
    if not git_scanner_path.exists():
        print(f"{RED}Error: git_scanner.py not found at {git_scanner_path}{RESET}")
        sys.exit(1)
        
    if not asset_backup_path.exists():
        print(f"{RED}Error: asset_backup.py not found at {asset_backup_path}{RESET}")
        sys.exit(1)
        
    print(f"{BOLD}Step 1: Running Git Projects Scanner...{RESET}")
    # Run git_scanner.py and capture the exit code
    # Exit code 2 indicates dirty repositories were found.
    # Exit code 0 indicates all repositories are clean.
    scanner_result = subprocess.run([sys.executable, str(git_scanner_path)])
    
    if scanner_result.returncode == 2:
        print(f"\n{YELLOW}{BOLD}WARNING: Uncommitted changes detected in your Git projects!{RESET}")
        print("Please check the generated CSV report for details.")
        
        try:
            choice = input(f"{YELLOW}Do you want to proceed with backing up your non-Git asset vaults anyway? [y/N]: {RESET}").strip().lower()
        except KeyboardInterrupt:
            print("\nBackup cancelled by user.")
            sys.exit(1)
            
        if choice not in ['y', 'yes']:
            print("Backup aborted so you can address your uncommitted code first.")
            sys.exit(0)
    elif scanner_result.returncode != 0:
        print(f"{RED}Git projects scanner failed with exit code {scanner_result.returncode}. Aborting.{RESET}")
        sys.exit(1)
        
    print(f"\n{BOLD}Step 2: Starting Asset Vaults Backup...{RESET}")
    backup_result = subprocess.run([sys.executable, str(asset_backup_path), "--zip"])
    
    if backup_result.returncode == 0:
        print(f"{GREEN}{BOLD}Orchestrated backup run completed successfully!{RESET}")
    else:
        print(f"{RED}{BOLD}Asset vaults backup failed with exit code {backup_result.returncode}.{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()
