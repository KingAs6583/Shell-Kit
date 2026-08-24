#!/usr/bin/env python3
import os
import re
import sys

# Color formatting constants
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
RESET = "\033[0m"

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STARTUP_FILES = [
    os.path.join(REPO_DIR, "bash", ".bash_function.both"),
    os.path.join(REPO_DIR, "bash", ".bash_function.linux"),
    os.path.join(REPO_DIR, "bash", ".bash_function.windows"),
]

def extract_functions(file_path):
    """
    Parses a bash file and returns a list of dictionaries with function details:
    {
        'name': str,
        'body': str,
        'line_start': int,
        'file': str
    }
    """
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Regex to find function definitions like:
    # my_func() {
    # function my_func {
    # my_func () {
    func_pattern = re.compile(
        r"(?:function\s+)?([a-zA-Z0-9_-]+)\s*\(\s*\)\s*\{|function\s+([a-zA-Z0-9_-]+)\s*\{"
    )
    
    functions = []
    lines = content.splitlines()
    
    # We find definitions and trace matching curly braces to extract function bodies
    for i, line in enumerate(lines):
        match = func_pattern.search(line)
        if match:
            func_name = match.group(1) or match.group(2)
            # Find body by balancing curly braces starting from the '{' index
            start_idx = line.find("{")
            if start_idx == -1:
                continue
                
            brace_count = 1
            body_lines = []
            
            # Start gathering body lines
            remaining_line = line[start_idx + 1:]
            for c in remaining_line:
                if c == "{":
                    brace_count += 1
                elif c == "}":
                    brace_count -= 1
            body_lines.append(remaining_line)
            
            j = i + 1
            while brace_count > 0 and j < len(lines):
                next_line = lines[j]
                for c in next_line:
                    if c == "{":
                        brace_count += 1
                    elif c == "}":
                        brace_count -= 1
                body_lines.append(next_line)
                j += 1
                
            body_text = "\n".join(body_lines)
            functions.append({
                "name": func_name,
                "body": body_text,
                "line_start": i + 1,
                "file": file_path
            })
            
    return functions

def main():
    print(f"\n{CYAN}shell-kit Help Enforcer Validation{RESET}")
    print("-" * 50)
    
    all_functions = []
    for fpath in STARTUP_FILES:
        if os.path.exists(fpath):
            all_functions.extend(extract_functions(fpath))
            
    # Find manual function definition for manual registration check
    manual_body = ""
    for func in all_functions:
        if func["name"] == "manual":
            manual_body = func["body"]
            break
            
    failures = 0
    scanned_count = 0
    
    for func in all_functions:
        name = func["name"]
        body = func["body"]
        filepath = func["file"]
        filename = os.path.basename(filepath)
        
        # Skip internal helper functions (starting with underscore) and manual itself
        if name.startswith("_") or name == "manual":
            continue
            
        scanned_count += 1
        
        # Check if function is a lazy stub
        is_lazy = False
        lazy_match = re.search(r'source\s+["\']\$HOME/\.local/share/shell-kit/lazy/([^"\']+\.sh)["\']', body)
        if lazy_match:
            is_lazy = True
            lazy_script = lazy_match.group(1)
            
        if is_lazy:
            # Validate lazy stub forwards arguments using "$@"
            if '"$@"' not in body:
                print(f"{RED}[FAIL] {name} (stub in {filename}): Stub does not forward arguments with \"$@\"{RESET}")
                failures += 1
                continue
                
            # Verify the lazy script file exists
            lazy_path = os.path.join(REPO_DIR, "bash", "lazy", lazy_script)
            if not os.path.exists(lazy_path):
                print(f"{RED}[FAIL] {name} (stub in {filename}): Lazy script file {lazy_script} not found at {lazy_path}{RESET}")
                failures += 1
                continue
                
            # Parse the lazy script file to check the real function body
            lazy_funcs = extract_functions(lazy_path)
            real_func = next((lf for lf in lazy_funcs if lf["name"] == name), None)
            if not real_func:
                print(f"{RED}[FAIL] {name} (lazy in {lazy_script}): Definition for {name}() not found in lazy file.{RESET}")
                failures += 1
                continue
                
            real_body = real_func["body"]
            # Validate real function checks for help options
            has_help_check = "--help" in real_body or "-h" in real_body
            if not has_help_check:
                print(f"{RED}[FAIL] {name} (lazy in {lazy_script}): Function does not check for -h / --help.{RESET}")
                failures += 1
            else:
                # Check manual registration
                if manual_body and name not in manual_body:
                    print(f"{YELLOW}[WARN] {name} (lazy in {lazy_script}): Help checks OK, but function is not documented in manual().{RESET}")
                    # Warnings don't cause verification failure, but are flagged
                print(f"{GREEN}[OK]   {name} (lazy stub + implementation verified){RESET}")
                
        else:
            # Standard function validation
            has_help_check = "--help" in body or "-h" in body
            if not has_help_check:
                print(f"{RED}[FAIL] {name} (in {filename}): Function does not check for -h / --help.{RESET}")
                failures += 1
            else:
                # Check manual registration
                if manual_body and name not in manual_body:
                    print(f"{YELLOW}[WARN] {name} (in {filename}): Help checks OK, but function is not documented in manual().{RESET}")
                print(f"{GREEN}[OK]   {name} (standard function verified){RESET}")

    print("-" * 50)
    if failures > 0:
        print(f"{RED}Enforcer check FAILED: {failures} functions lack proper help/signature checks.{RESET}\n")
        sys.exit(1)
    else:
        print(f"{GREEN}Enforcer check PASSED: All {scanned_count} functions conform to rules.{RESET}\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
