#!/usr/bin/env python3
import os
import sys
import json
import csv
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

def load_config():
    # Try ~/.backup_config.json first
    home_config = Path("~/.backup_config.json").expanduser()
    if home_config.exists():
        try:
            with open(home_config, 'r', encoding='utf-8') as f:
                return json.load(f), home_config
        except Exception as e:
            print(f"{YELLOW}Warning: Error reading config from {home_config}: {e}{RESET}", file=sys.stderr)
    
    # Try repo root backup_config.json
    repo_config = Path(__file__).resolve().parent.parent / "backup_config.json"
    if repo_config.exists():
        try:
            with open(repo_config, 'r', encoding='utf-8') as f:
                return json.load(f), repo_config
        except Exception as e:
            print(f"{YELLOW}Warning: Error reading config from {repo_config}: {e}{RESET}", file=sys.stderr)
            
    return None, None

def get_git_branch(repo_path):
    try:
        res = subprocess.run(
            ["git", "branch", "--show-current"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        return res.stdout.strip() or "HEAD detached"
    except Exception:
        return "Unknown"

def check_git_status(repo_path):
    try:
        res = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo_path,
            capture_output=True,
            text=True,
            check=True
        )
        lines = res.stdout.splitlines()
        modified = 0
        untracked = 0
        for line in lines:
            if line.strip().startswith("??"):
                untracked += 1
            else:
                modified += 1
        is_dirty = (modified + untracked) > 0
        return modified, untracked, is_dirty
    except Exception as e:
        print(f"{RED}Error checking git status for {repo_path}: {e}{RESET}")
        return 0, 0, False

def scan_projects(projects_dirs):
    results = []
    for proj_dir_str in projects_dirs:
        proj_dir = Path(proj_dir_str).expanduser()
        if not proj_dir.is_dir():
            print(f"{YELLOW}Warning: Project directory {proj_dir} does not exist or is not a directory. Skipping.{RESET}")
            continue
            
        print(f"Scanning project directory: {CYAN}{proj_dir}{RESET} ...")
        try:
            # Sort items to get predictable output
            for item in sorted(proj_dir.iterdir()):
                if item.is_dir():
                    git_dir = item / ".git"
                    if git_dir.is_dir():
                        branch = get_git_branch(item)
                        modified, untracked, is_dirty = check_git_status(item)
                        results.append({
                            "path": str(item.resolve()),
                            "name": item.name,
                            "type": "Git Repo",
                            "branch": branch,
                            "status": "Dirty" if is_dirty else "Clean",
                            "modified_count": modified,
                            "untracked_count": untracked
                        })
                    else:
                        results.append({
                            "path": str(item.resolve()),
                            "name": item.name,
                            "type": "Folder",
                            "branch": "N/A",
                            "status": "Non-Git",
                            "modified_count": 0,
                            "untracked_count": 0
                        })
        except Exception as e:
            print(f"{RED}Error scanning directory {proj_dir}: {e}{RESET}")
            
    return results

def print_summary_table(results):
    print(f"\n{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}GIT REPOSITORY SCAN SUMMARY{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}{'Project Folder':<30} | {'Type':<10} | {'Branch':<15} | {'Status':<10} | {'Mod/Untracked':<15}{RESET}")
    print("-" * 80)
    
    dirty_count = 0
    clean_count = 0
    non_git_count = 0
    
    for r in results:
        if r["type"] == "Folder":
            status_str = f"{BLUE}Non-Git{RESET}"
            non_git_count += 1
        elif r["status"] == "Dirty":
            status_str = f"{RED}Dirty{RESET}"
            dirty_count += 1
        else:
            status_str = f"{GREEN}Clean{RESET}"
            clean_count += 1
            
        changes = f"{r['modified_count']}/{r['untracked_count']}" if r["type"] == "Git Repo" else "N/A"
        
        # Trim name to fit column
        name = r["name"]
        if len(name) > 30:
            name = name[:27] + "..."
            
        print(f"{name:<30} | {r['type']:<10} | {r['branch']:<15} | {status_str:<19} | {changes:<15}")
        
    print("-" * 80)
    print(f"Total scanned: {len(results)} | {GREEN}Clean: {clean_count}{RESET} | {RED}Dirty: {dirty_count}{RESET} | {BLUE}Non-Git: {non_git_count}{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}\n")
    return dirty_count

def write_csv_report(results, csv_filename="git_status_report.csv"):
    cwd_path = Path.cwd() / csv_filename
    try:
        with open(cwd_path, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Repository Path", "Repository Name", "Type", "Branch", "Status", "Modified Files Count", "Untracked Files Count"])
            for r in results:
                writer.writerow([r["path"], r["name"], r["type"], r["branch"], r["status"], r["modified_count"], r["untracked_count"]])
        print(f"Detailed Git status report written to: {BOLD}{GREEN}{cwd_path}{RESET}")
        return cwd_path
    except Exception as e:
        print(f"{RED}Error writing CSV report: {e}{RESET}")
        return None

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Scan project directories for Git repositories and report status.")
    parser.parse_args()

    config, config_path = load_config()
    if not config:
        print(f"{RED}Error: No backup_config.json configuration file found!{RESET}")
        print("Please copy backup_config.json.template to either ~/.backup_config.json or the repository root and configure it.")
        sys.exit(1)
        
    print(f"Using configuration from: {BOLD}{GREEN}{config_path}{RESET}")
    
    projects_dirs = config.get("projects_dirs", [])
    if not projects_dirs:
        print(f"{YELLOW}Warning: No 'projects_dirs' found in the configuration.{RESET}")
        sys.exit(0)
        
    results = scan_projects(projects_dirs)
    if not results:
        print("No folders found in the configured projects directories.")
        sys.exit(0)
        
    dirty_count = print_summary_table(results)
    write_csv_report(results)
    
    if dirty_count > 0:
        # Exit with code 2 to indicate uncommitted changes are present
        sys.exit(2)
    sys.exit(0)

if __name__ == "__main__":
    main()
