#!/usr/bin/env python3
import os
import sys
import json
import time
import zipfile
import re
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

def load_config():
    home_config = Path("~/.backup_config.json").expanduser()
    if home_config.exists():
        try:
            with open(home_config, 'r', encoding='utf-8') as f:
                return json.load(f), home_config
        except Exception as e:
            print(f"{YELLOW}Warning: Error reading config from {home_config}: {e}{RESET}", file=sys.stderr)
            
    repo_config = Path(__file__).resolve().parent.parent / "backup_config.json"
    if repo_config.exists():
        try:
            with open(repo_config, 'r', encoding='utf-8') as f:
                return json.load(f), repo_config
        except Exception as e:
            print(f"{YELLOW}Warning: Error reading config from {repo_config}: {e}{RESET}", file=sys.stderr)
            
    return None, None

def should_exclude(path, base_source, exclude_patterns):
    try:
        relative_path = path.relative_to(base_source)
    except ValueError:
        return False
        
    parts = relative_path.parts
    for pattern in exclude_patterns:
        # Match whole relative path or any folder/file name in the parts list
        if fnmatch(str(relative_path), pattern) or fnmatch(relative_path.as_posix(), pattern):
            return True
        for part in parts:
            if fnmatch(part, pattern):
                return True
    return False

def zip_asset(name, source_path_str, exclude_patterns, backup_dest):
    source_dir = Path(source_path_str).expanduser()
    if not source_dir.exists():
        print(f"{YELLOW}Warning: Asset source folder '{source_dir}' does not exist. Skipping backup.{RESET}")
        return False, None
        
    backup_dest_dir = Path(backup_dest).expanduser()
    backup_dest_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    zip_filename = f"{name}_{timestamp}.zip"
    zip_filepath = backup_dest_dir / zip_filename
    
    print(f"Backing up asset {BOLD}{CYAN}{name}{RESET} from {source_dir}...")
    print(f"Destination: {zip_filepath}")
    
    files_compressed = 0
    bytes_compressed = 0
    
    try:
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Walk directory tree
            for root, dirs, files in os.walk(source_dir):
                root_path = Path(root)
                
                # Filter directories in-place to avoid scanning excluded directories recursively
                # We iterate backwards so we can safely remove items during iteration
                for idx in range(len(dirs) - 1, -1, -1):
                    dir_path = root_path / dirs[idx]
                    if should_exclude(dir_path, source_dir, exclude_patterns):
                        dirs.pop(idx)
                        
                # Process files
                for file in files:
                    file_path = root_path / file
                    if should_exclude(file_path, source_dir, exclude_patterns):
                        continue
                        
                    # Arcname is the path inside the zip file (relative to the asset source directory)
                    arcname = file_path.relative_to(source_dir)
                    zip_file.write(file_path, arcname)
                    files_compressed += 1
                    bytes_compressed += file_path.stat().st_size
                    
        mb_size = bytes_compressed / (1024 * 1024)
        print(f"{GREEN}Success!{RESET} Compressed {files_compressed} files ({mb_size:.2f} MB)")
        return True, zip_filepath
    except Exception as e:
        print(f"{RED}Error compressing asset '{name}': {e}{RESET}")
        # Clean up partial zip if it failed
        if zip_filepath.exists():
            zip_filepath.unlink()
        return False, None

def run_backup(config, config_path):
    backup_dest = config.get("backup_dest")
    if not backup_dest:
        print(f"{RED}Error: 'backup_dest' is not defined in config.{RESET}")
        return False
        
    assets = config.get("assets", [])
    if not assets:
        print(f"{YELLOW}Warning: No assets defined in configuration.{RESET}")
        return False
        
    success_count = 0
    backed_up_files = []
    
    print(f"\n{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}STARTING ASSET VAULT BACKUP{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}")
    
    for asset in assets:
        name = asset.get("name")
        source = asset.get("source")
        exclude = asset.get("exclude", [])
        
        if not name or not source:
            print(f"{YELLOW}Warning: Skipping invalid asset entry: {asset}{RESET}")
            continue
            
        success, zip_path = zip_asset(name, source, exclude, backup_dest)
        if success:
            success_count += 1
            backed_up_files.append(zip_path)
            
    # Also back up the config file itself into the backup destination
    if success_count > 0 and config_path:
        try:
            dest_dir = Path(backup_dest).expanduser()
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            config_backup_path = dest_dir / f"backup_config_run_{timestamp}.json"
            with open(config_backup_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            print(f"Saved running config snapshot to: {config_backup_path}")
        except Exception as e:
            print(f"{YELLOW}Warning: Could not back up config file: {e}{RESET}")
            
    print(f"\n{BOLD}{'=' * 80}{RESET}")
    print(f"Asset Backup finished. Successfully backed up {success_count} / {len(assets)} assets.")
    print(f"{BOLD}{'=' * 80}{RESET}\n")
    return success_count > 0

def find_backups(backup_dest, assets_config):
    dest_dir = Path(backup_dest).expanduser()
    if not dest_dir.is_dir():
        return []
        
    # Get standard list of asset names from config
    known_names = [a.get("name") for a in assets_config if a.get("name")]
    
    backups = []
    # Pattern to match {asset_name}_{YYYYMMDD}_{HHMMSS}.zip
    pattern = re.compile(r"^(.+)_(\d{8})_(\d{6})\.zip$")
    
    for item in dest_dir.iterdir():
        if item.is_file() and item.suffix == ".zip":
            match = pattern.match(item.name)
            if match:
                asset_name = match.group(1)
                date_str = match.group(2)
                time_str = match.group(3)
                
                # Reformat timestamp for display
                formatted_time = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]} {time_str[:2]}:{time_str[2:4]}:{time_str[4:]}"
                
                backups.append({
                    "path": item,
                    "filename": item.name,
                    "asset_name": asset_name,
                    "timestamp": formatted_time,
                    "size_mb": item.stat().st_size / (1024 * 1024)
                })
                
    # Sort by asset name, then by date/time descending
    backups.sort(key=lambda x: (x["asset_name"], x["filename"]), reverse=True)
    return backups

def restore_archive(zip_filepath, dest_dir):
    zip_filepath = Path(zip_filepath)
    dest_dir = Path(dest_dir)
    
    print(f"\nRestoring archive: {BOLD}{CYAN}{zip_filepath.name}{RESET}")
    print(f"Destination directory: {BOLD}{GREEN}{dest_dir}{RESET}")
    
    try:
        dest_dir.mkdir(parents=True, exist_ok=True)
        files_count = 0
        
        with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
            members = zip_ref.infolist()
            print(f"Extracting {len(members)} files losslessly...")
            
            for idx, member in enumerate(members, start=1):
                # Extract single file
                extracted_path = Path(zip_ref.extract(member, dest_dir))
                
                # Restore modification time
                dt = member.date_time
                struct_time = (dt[0], dt[1], dt[2], dt[3], dt[4], dt[5], 0, 0, -1)
                epoch_time = time.mktime(struct_time)
                os.utime(extracted_path, (epoch_time, epoch_time))
                
                # Restore Unix file permissions if present
                perm = (member.external_attr >> 16) & 0xFFFF
                if perm != 0:
                    try:
                        extracted_path.chmod(perm)
                    except Exception:
                        pass
                
                files_count += 1
                if idx % 100 == 0 or idx == len(members):
                    print(f"Progress: {idx}/{len(members)} extracted...")
                    
        print(f"{GREEN}Success!{RESET} Extracted {files_count} files to {dest_dir} losslessly.")
        return True
    except Exception as e:
        print(f"{RED}Error restoring archive: {e}{RESET}")
        return False

def interactive_restore(config):
    backup_dest = config.get("backup_dest")
    assets = config.get("assets", [])
    
    if not backup_dest:
        print(f"{RED}Error: 'backup_dest' is not defined in config.{RESET}")
        return
        
    backups = find_backups(backup_dest, assets)
    if not backups:
        print(f"{YELLOW}No backups found in destination: {backup_dest}{RESET}")
        return
        
    print(f"\n{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}AVAILABLE ARCHIVE BACKUPS{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}{'Idx':<4} | {'Asset Name':<20} | {'Backup Date & Time':<20} | {'Size':<10}{RESET}")
    print("-" * 80)
    
    for idx, b in enumerate(backups, start=1):
        print(f"{idx:<4} | {b['asset_name']:<20} | {b['timestamp']:<20} | {b['size_mb']:.2f} MB")
        
    print("-" * 80)
    
    selection_str = input(f"Select backup index to restore (1-{len(backups)}) [or 'q' to quit]: ").strip()
    if selection_str.lower() == 'q' or not selection_str:
        print("Restoration cancelled.")
        return
        
    try:
        selection_idx = int(selection_str)
        if selection_idx < 1 or selection_idx > len(backups):
            print(f"{RED}Invalid index selected.{RESET}")
            return
    except ValueError:
        print(f"{RED}Invalid input. Please enter a number.{RESET}")
        return
        
    selected_backup = backups[selection_idx - 1]
    asset_name = selected_backup["asset_name"]
    zip_path = selected_backup["path"]
    
    # Try to find original configured source path
    original_source = None
    for asset in assets:
        if asset.get("name") == asset_name:
            original_source = asset.get("source")
            break
            
    print(f"\nSelected backup: {BOLD}{selected_backup['filename']}{RESET}")
    if original_source:
        print(f"Original source path configured: {original_source}")
        prompt = f"Where would you like to restore? \n  [o]riginal path ({original_source}) \n  [c]ustom directory \n  [q]uit \nChoice [o/c/q]: "
    else:
        print("Original source path is unknown (not in active configuration).")
        prompt = "Where would you like to restore? \n  [c]ustom directory \n  [q]uit \nChoice [c/q]: "
        
    choice = input(prompt).strip().lower()
    
    if choice == 'q':
        print("Restoration cancelled.")
        return
    elif choice == 'o' and original_source:
        dest_dir = Path(original_source).expanduser()
    elif choice == 'c':
        dest_str = input("Enter custom destination directory path: ").strip()
        if not dest_str:
            print(f"{RED}Destination path cannot be empty.{RESET}")
            return
        dest_dir = Path(dest_str).expanduser()
    else:
        print(f"{RED}Invalid choice.{RESET}")
        return
        
    # Double check confirmation
    confirm = input(f"{YELLOW}WARNING: This will extract and overwrite files in {dest_dir}. Continue? [y/N]: {RESET}").strip().lower()
    if confirm == 'y':
        restore_archive(zip_path, dest_dir)
    else:
        print("Restoration cancelled.")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Backup and Restore Asset Vaults")
    parser.add_argument("--zip", action="store_true", help="Zip all configured assets")
    parser.add_argument("--restore", action="store_true", help="Interactively restore/unzip an asset")
    
    args = parser.parse_args()
    
    config, config_path = load_config()
    if not config:
        print(f"{RED}Error: No backup_config.json configuration file found!{RESET}")
        print("Please copy backup_config.json.template to either ~/.backup_config.json or the repository root and configure it.")
        sys.exit(1)
        
    if args.restore:
        interactive_restore(config)
    else:
        # Default is to run zip backup
        run_backup(config, config_path)

if __name__ == "__main__":
    main()
