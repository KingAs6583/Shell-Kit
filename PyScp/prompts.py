#!/usr/bin/env python3
import os
import sys
import re
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

def format_size(size_bytes):
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"

def get_prompts_dir():
    file_path = Path(__file__).resolve()
    # Handle mock MSYS2 symlinks on Windows (which are text files starting with !<symlink>)
    try:
        if file_path.exists() and file_path.stat().st_size < 1024:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            if content.startswith('!<symlink>'):
                target = content.replace('!<symlink>', '').strip('\x00').strip()
                file_path = Path(target).resolve()
    except Exception:
        pass
        
    repo_root = file_path.parent.parent
    local_repo_prompts = repo_root / "prompts"
    if local_repo_prompts.is_dir():
        return local_repo_prompts
        
    # Fallback to installed user share directory
    home_dir = Path(os.environ.get("HOME") or Path.home())
    installed_prompts = home_dir / ".local" / "share" / "shell-kit" / "prompts"
    return installed_prompts

# Zero-dependency clipboard utilities
def copy_to_clipboard_win(text):
    try:
        # PowerShell supports Unicode (UTF-8) set-clipboard
        cmd = ["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value $Input"]
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, text=True, encoding='utf-8')
        process.communicate(input=text)
        return process.returncode == 0
    except Exception:
        # Fallback to standard clip.exe (which might have issues with non-ASCII, but works)
        try:
            process = subprocess.Popen(['clip'], stdin=subprocess.PIPE, shell=True)
            process.communicate(input=text.encode('utf-8'))
            return True
        except Exception:
            return False

def copy_to_clipboard_mac(text):
    try:
        process = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
        process.communicate(input=text.encode('utf-8'))
        return process.returncode == 0
    except Exception:
        return False

def copy_to_clipboard_linux(text):
    try:
        process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE)
        process.communicate(input=text.encode('utf-8'))
        if process.returncode == 0:
            return True
    except Exception:
        pass
    try:
        process = subprocess.Popen(['xsel', '-ib'], stdin=subprocess.PIPE)
        process.communicate(input=text.encode('utf-8'))
        if process.returncode == 0:
            return True
    except Exception:
        pass
    return False

def copy_to_clipboard(text):
    if sys.platform == "win32":
        return copy_to_clipboard_win(text)
    elif sys.platform == "darwin":
        return copy_to_clipboard_mac(text)
    else:
        return copy_to_clipboard_linux(text)

# Zero-dependency token counter (standardized BPE approximation)
def count_tokens(text):
    if not text:
        return 0
        
    # Match words, numbers, and individual punctuation marks (ignoring spaces)
    pattern = re.compile(r'\w+|[^\w\s]', re.UNICODE)
    chunks = pattern.findall(text)
    
    total_tokens = 0
    for chunk in chunks:
        length = len(chunk)
        if length <= 4:
            total_tokens += 1
        else:
            # Estimate long words being split into multiple tokens
            total_tokens += (length + 3) // 4
            
    # Count newlines as tokens (typically 1 token in BPE)
    newlines = text.count('\n')
    total_tokens += newlines
    
    # Handle multiple spaces/tabs (common in code indentation)
    # Estimate roughly 1 token per tab character or 4 consecutive spaces
    tabs = text.count('\t')
    total_tokens += tabs
    
    spaces_groups = re.findall(r' {2,}', text)
    for group in spaces_groups:
        total_tokens += (len(group) + 3) // 4
        
    return total_tokens

def list_prompts():
    prompts_dir = get_prompts_dir()
    if not prompts_dir.is_dir():
        print(f"{YELLOW}No prompts directory found at {prompts_dir}{RESET}")
        return
        
    files = sorted(prompts_dir.glob("*.md"))
    if not files:
        print(f"{YELLOW}No prompt templates found in {prompts_dir}{RESET}")
        return
        
    print(f"\n{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}AVAILABLE AI PROMPT TEMPLATES{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}")
    for f in files:
        size = f.stat().st_size
        print(f"  - {BOLD}{GREEN}{f.stem:<15}{RESET} ({format_size(size)}) -> {f.name}")
    print(f"{BOLD}{'=' * 80}{RESET}\n")

def show_prompt(name, copy=True):
    prompts_dir = get_prompts_dir()
    prompt_file = prompts_dir / f"{name}.md"
    if not prompt_file.exists():
        print(f"{RED}Error: Prompt template '{name}' not found.{RESET}")
        print(f"Run {BOLD}prompts list{RESET} to see available templates.")
        sys.exit(1)
        
    try:
        content = prompt_file.read_text(encoding='utf-8')
        print(content)
        print(f"\n{BOLD}{'-' * 80}{RESET}")
        
        if copy:
            if copy_to_clipboard(content):
                print(f"{GREEN}{BOLD}Success: Prompt '{name}' copied to clipboard!{RESET}")
            else:
                print(f"{YELLOW}Warning: Could not copy prompt to clipboard. OS tools (clip/pbcopy/xclip) not available.{RESET}")
    except Exception as e:
        print(f"{RED}Error loading prompt: {e}{RESET}")
        sys.exit(1)

def check_tokens(path_or_text):
    text = ""
    source_name = ""
    is_file = False
    
    # Try treating as file first
    try:
        path = Path(path_or_text).expanduser()
        if path.is_file():
            text = path.read_text(encoding='utf-8', errors='replace')
            source_name = f"File: {path.name} ({path.resolve()})"
            is_file = True
    except Exception:
        pass
        
    if not is_file:
        text = path_or_text
        source_name = "Passed Text String"
        
    chars = len(text)
    words = len(text.split())
    tokens = count_tokens(text)
    
    print(f"\n{BOLD}{'=' * 80}{RESET}")
    print(f"{BOLD}TOKEN ANALYSIS FOR: {CYAN}{source_name}{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}")
    print(f"  {BOLD}Characters:{RESET} {chars}")
    print(f"  {BOLD}Words:{RESET}      {words}")
    print(f"  {BOLD}Estimated Tokens (Heuristics):{RESET} {GREEN}{BOLD}{tokens}{RESET}")
    print(f"{BOLD}{'=' * 80}{RESET}\n")

def main():
    if len(sys.argv) < 2:
        print(f"{BOLD}Usage:{RESET}")
        print("  prompts list              - List all available prompt templates")
        print("  prompts show <name>       - Show prompt contents (without copying)")
        print("  prompts <name>            - Show and copy prompt contents to clipboard")
        print("  prompts tokens <file/txt> - Count characters, words, and tokens")
        sys.exit(1)
        
    command = sys.argv[1].lower()
    
    if command == "list":
        list_prompts()
    elif command == "show":
        if len(sys.argv) < 3:
            print(f"{RED}Error: Please specify the name of the prompt to show.{RESET}")
            sys.exit(1)
        show_prompt(sys.argv[2], copy=False)
    elif command == "tokens":
        if len(sys.argv) < 3:
            print(f"{RED}Error: Please specify the file path or text string to analyze.{RESET}")
            sys.exit(1)
        # Combine all subsequent arguments in case of spaces in raw text
        raw_input = " ".join(sys.argv[2:])
        check_tokens(raw_input)
    else:
        # Default behavior: show and copy the specified prompt template
        show_prompt(command, copy=True)

if __name__ == "__main__":
    main()
