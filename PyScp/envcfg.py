#!/usr/bin/env python3
import os
import sys
import re
import shutil

# Color formatting constants
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
RESET = "\033[0m"

try:
    import readline
except ImportError:
    pass  # Fallback for systems/shells without readline support

def print_help():
    sys.stderr.write(f"""{CYAN}{BOLD}envcfg — Environment File Setup & Config Manager{RESET}
Manage .env files interactively in SSH and local environments.

{BOLD}Usage:{RESET}
  envcfg init [example_file]   Initialize .env from an example file and configure it
  envcfg wizard [example_file] Run interactive configuration wizard for all keys
  envcfg list [--show-secrets] List all keys and values (secrets masked by default)
  envcfg get <key>             Get the value of a specific key
  envcfg set <key> <value>     Set or update a key-value pair
  envcfg --cleanup             Self-cleanup compliance flag (no-op)

{BOLD}Options:{RESET}
  -h, --help      Show this help message and exit
  -s, --show-secrets  Show plain text secrets in 'list' command
""")

def find_env_file(filename=".env", start_dir=None):
    """
    Traverses directories upwards to locate the .env or git root.
    """
    if start_dir is None:
        start_dir = os.getcwd()
    current = os.path.abspath(start_dir)
    while True:
        target = os.path.join(current, filename)
        if os.path.isfile(target):
            return target
        # Check if we hit git root
        if os.path.isdir(os.path.join(current, ".git")):
            break
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return os.path.join(os.getcwd(), filename)

def parse_env_file(filepath):
    """
    Parses a .env file preserving structure, empty lines, and comments.
    """
    if not os.path.exists(filepath):
        return []
        
    records = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped:
                records.append({"type": "empty", "raw_line": line})
                continue
            if stripped.startswith("#"):
                records.append({"type": "comment", "raw_line": line})
                continue
                
            match = re.match(r"^\s*([A-Za-z0-9_]+)\s*=\s*(.*)$", line)
            if match:
                key = match.group(1)
                raw_val = match.group(2).strip()
                
                quote_char = None
                value = raw_val
                comment = ""
                
                # Check if quoted
                if raw_val.startswith('"') and '"' in raw_val[1:]:
                    quote_char = '"'
                    end_idx = raw_val.find('"', 1)
                    value = raw_val[1:end_idx]
                    comment = raw_val[end_idx+1:].strip()
                elif raw_val.startswith("'") and "'" in raw_val[1:]:
                    quote_char = "'"
                    end_idx = raw_val.find("'", 1)
                    value = raw_val[1:end_idx]
                    comment = raw_val[end_idx+1:].strip()
                else:
                    # Parse inline comments
                    parts = re.split(r"\s+#", raw_val, maxsplit=1)
                    value = parts[0].strip()
                    if len(parts) > 1:
                        comment = "#" + parts[1]
                        
                records.append({
                    "type": "kv",
                    "key": key,
                    "value": value,
                    "quote_char": quote_char,
                    "comment": comment,
                    "raw_line": line
                })
            else:
                records.append({"type": "comment", "raw_line": line})
    return records

def save_env_file(filepath, records):
    """
    Writes parsed records back to the file, preserving layout.
    """
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        for r in records:
            if r["type"] in ("empty", "comment"):
                f.write(r["raw_line"])
            elif r["type"] == "kv":
                val = r["value"]
                quote = r["quote_char"]
                if quote is None:
                    if any(c in val for c in (" ", "#", "=", "$", "'", '"')):
                        quote = '"'
                
                formatted_val = f"{quote}{val}{quote}" if quote else val
                comment_part = f" {r['comment']}" if r.get("comment") else ""
                
                ending = "\n"
                if "raw_line" in r and r["raw_line"].endswith("\r\n"):
                    ending = "\r\n"
                    
                f.write(f"{r['key']}={formatted_val}{comment_part}{ending}")

def update_key(records, key, value):
    """
    Updates an existing key or appends a new one.
    """
    for r in records:
        if r["type"] == "kv" and r["key"] == key:
            r["value"] = value
            return True
            
    records.append({
        "type": "kv",
        "key": key,
        "value": value,
        "quote_char": None,
        "comment": ""
    })
    return False

def print_list(records, show_secrets=False):
    secret_patterns = ["pass", "key", "secret", "token", "auth", "crypt", "pwd"]
    print(f"\n{CYAN}{BOLD}Environment Variables (.env):{RESET}")
    print("=" * 60)
    
    has_vars = False
    for r in records:
        if r["type"] == "kv":
            has_vars = True
            k = r["key"]
            v = r["value"]
            
            is_secret = any(p in k.lower() for p in secret_patterns)
            if is_secret and not show_secrets and v:
                v_display = f"{YELLOW}[HIDDEN] (use -s or --show-secrets to reveal){RESET}"
            else:
                v_display = f"{GREEN}{v}{RESET}"
                
            print(f"  {BOLD}{k:<25}{RESET} = {v_display}")
            
    if not has_vars:
        print("  No variables found.")
    print("=" * 60)

def run_wizard(env_file, example_file=None):
    env_records = parse_env_file(env_file)
    env_dict = {r["key"]: r["value"] for r in env_records if r["type"] == "kv"}
    
    target_keys = []
    if example_file and os.path.exists(example_file):
        ex_records = parse_env_file(example_file)
        target_keys = [r["key"] for r in ex_records if r["type"] == "kv"]
    else:
        target_keys = [r["key"] for r in env_records if r["type"] == "kv"]
        
    if not target_keys:
        print(f"{YELLOW}[WARN] No keys found to configure.{RESET}")
        return
        
    print(f"\n{CYAN}{BOLD}Interactive .env Configuration Wizard{RESET}")
    print("Press Enter to keep the default/current value.\n")
    
    for key in target_keys:
        curr_val = env_dict.get(key, "")
        is_secret = any(p in key.lower() for p in ["pass", "key", "secret", "token", "auth", "crypt", "pwd"])
        
        prompt_val = f" [default: {curr_val}]" if curr_val else ""
        if is_secret and curr_val:
            prompt_val = " [default: ******]"
            
        sys.stdout.write(f"  {BOLD}{key}{RESET}{prompt_val}: ")
        sys.stdout.flush()
        new_val = sys.stdin.readline().strip()
        
        if new_val == "":
            if key not in env_dict:
                update_key(env_records, key, "")
        else:
            update_key(env_records, key, new_val)
            
    save_env_file(env_file, env_records)
    print(f"\n{GREEN}[SUCCESS] Configuration saved to {env_file}{RESET}")

def do_init(env_file, example_file=None):
    if not example_file:
        dir_path = os.path.dirname(env_file) or "."
        for fname in (".env.example", "env.example", ".env.sample", "env.sample"):
            possible_path = os.path.join(dir_path, fname)
            if os.path.exists(possible_path):
                example_file = possible_path
                break
                
    if not example_file or not os.path.exists(example_file):
        if os.path.exists(env_file):
            print(f"{YELLOW}[INFO] .env already exists. Running wizard...{RESET}")
            run_wizard(env_file)
        else:
            print(f"{RED}[ERROR] No configuration example file found, and no .env exists.{RESET}")
            sys.exit(1)
        return
        
    if not os.path.exists(env_file):
        print(f"{CYAN}Copying {example_file} to {env_file}...{RESET}")
        shutil.copyfile(example_file, env_file)
        run_wizard(env_file, example_file)
    else:
        env_records = parse_env_file(env_file)
        env_keys = {r["key"] for r in env_records if r["type"] == "kv"}
        
        ex_records = parse_env_file(example_file)
        ex_keys = [r["key"] for r in ex_records if r["type"] == "kv"]
        
        missing_keys = [k for k in ex_keys if k not in env_keys]
        
        if not missing_keys:
            print(f"{GREEN}[OK] .env has all keys defined in {example_file}.{RESET}")
            sys.stdout.write("Would you like to run the wizard for all keys anyway? (y/N): ")
            sys.stdout.flush()
            choice = sys.stdin.readline().strip().lower()
            if choice in ("y", "yes"):
                run_wizard(env_file, example_file)
        else:
            print(f"{YELLOW}[INFO] Found {len(missing_keys)} missing key(s) in .env compared to {example_file}:{RESET}")
            for k in missing_keys:
                print(f"  - {k}")
            print("")
            
            print(f"{CYAN}Configuring missing keys interactively...{RESET}")
            for key in missing_keys:
                sys.stdout.write(f"  {BOLD}{key}{RESET}: ")
                sys.stdout.flush()
                val = sys.stdin.readline().strip()
                update_key(env_records, key, val)
                
            save_env_file(env_file, env_records)
            print(f"\n{GREEN}[SUCCESS] Missing keys appended to {env_file}{RESET}")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print_help()
        sys.exit(0)
        
    cmd = sys.argv[1]
    
    if cmd == "--cleanup":
        sys.stderr.write(f"{GREEN}[CLEANUP] envcfg requires no cleanup operations.{RESET}\n")
        sys.exit(0)
        
    env_file = find_env_file()
    
    if cmd == "init":
        example_file = sys.argv[2] if len(sys.argv) > 2 else None
        do_init(env_file, example_file)
        
    elif cmd == "wizard":
        example_file = sys.argv[2] if len(sys.argv) > 2 else None
        run_wizard(env_file, example_file)
        
    elif cmd == "list":
        show_secrets = "--show-secrets" in sys.argv or "-s" in sys.argv
        if not os.path.exists(env_file):
            print(f"{RED}[ERROR] No .env file found.{RESET}")
            sys.exit(1)
        records = parse_env_file(env_file)
        print_list(records, show_secrets)
        
    elif cmd == "get":
        if len(sys.argv) < 3:
            print(f"{RED}[ERROR] Missing key name. Usage: envcfg get <key>{RESET}")
            sys.exit(1)
        key = sys.argv[2]
        if not os.path.exists(env_file):
            print(f"{RED}[ERROR] No .env file found.{RESET}")
            sys.exit(1)
        records = parse_env_file(env_file)
        val = next((r["value"] for r in records if r["type"] == "kv" and r["key"] == key), None)
        if val is not None:
            print(val)
        else:
            print(f"{RED}[ERROR] Key '{key}' not found in {env_file}.{RESET}")
            sys.exit(1)
            
    elif cmd == "set":
        if len(sys.argv) < 4:
            print(f"{RED}[ERROR] Missing arguments. Usage: envcfg set <key> <value>{RESET}")
            sys.exit(1)
        key = sys.argv[2]
        val = sys.argv[3]
        
        # Parse or start fresh env file if doesn't exist
        records = parse_env_file(env_file)
        update_key(records, key, val)
        save_env_file(env_file, records)
        print(f"{GREEN}[SUCCESS] Set {key} in {env_file}{RESET}")
        
    else:
        sys.stderr.write(f"{RED}[ERROR] Unknown command: '{cmd}'{RESET}\n")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
