#!/usr/bin/env python3
import sys
import shutil
import subprocess

def copy(text):
    if sys.platform == "win32":
        # clip.exe expects Windows line endings
        win_text = text.replace("\r\n", "\n").replace("\n", "\r\n")
        try:
            p = subprocess.Popen(["clip"], stdin=subprocess.PIPE, text=True)
            p.communicate(input=win_text)
            return True
        except Exception as e:
            sys.stderr.write(f"[ERROR] Windows clip failed: {e}\n")
            return False
            
    elif sys.platform == "darwin":
        try:
            p = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE, text=True)
            p.communicate(input=text)
            return True
        except Exception as e:
            sys.stderr.write(f"[ERROR] macOS pbcopy failed: {e}\n")
            return False
            
    else:
        # Linux / Unix
        if shutil.which("wl-copy"):
            try:
                p = subprocess.Popen(["wl-copy"], stdin=subprocess.PIPE, text=True)
                p.communicate(input=text)
                return True
            except Exception as e:
                sys.stderr.write(f"[ERROR] wl-copy failed: {e}\n")
                
        if shutil.which("xclip"):
            try:
                p = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE, text=True)
                p.communicate(input=text)
                return True
            except Exception as e:
                sys.stderr.write(f"[ERROR] xclip failed: {e}\n")
                
        if shutil.which("xsel"):
            try:
                p = subprocess.Popen(["xsel", "-clipboard", "-input"], stdin=subprocess.PIPE, text=True)
                p.communicate(input=text)
                return True
            except Exception as e:
                sys.stderr.write(f"[ERROR] xsel failed: {e}\n")
                
        sys.stderr.write("[WARN] No clipboard manager (wl-copy, xclip, xsel) found.\n")
        return False

def paste():
    if sys.platform == "win32":
        try:
            res = subprocess.run(["powershell.exe", "-NoProfile", "-Command", "Get-Clipboard"], capture_output=True, text=True)
            # Remove trailing \r\n added by powershell Get-Clipboard
            content = res.stdout
            if content.endswith("\r\n"):
                content = content[:-2]
            elif content.endswith("\n"):
                content = content[:-1]
            return content
        except Exception as e:
            sys.stderr.write(f"[ERROR] Windows Get-Clipboard failed: {e}\n")
            return ""
            
    elif sys.platform == "darwin":
        try:
            res = subprocess.run(["pbpaste"], capture_output=True, text=True)
            return res.stdout
        except Exception as e:
            sys.stderr.write(f"[ERROR] macOS pbpaste failed: {e}\n")
            return ""
            
    else:
        # Linux / Unix
        if shutil.which("wl-paste"):
            try:
                res = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, text=True)
                return res.stdout
            except Exception as e:
                sys.stderr.write(f"[ERROR] wl-paste failed: {e}\n")
                
        if shutil.which("xclip"):
            try:
                res = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True)
                return res.stdout
            except Exception as e:
                sys.stderr.write(f"[ERROR] xclip output failed: {e}\n")
                
        if shutil.which("xsel"):
            try:
                res = subprocess.run(["xsel", "-clipboard", "-output"], capture_output=True, text=True)
                return res.stdout
            except Exception as e:
                sys.stderr.write(f"[ERROR] xsel output failed: {e}\n")
                
        sys.stderr.write("[WARN] No clipboard manager (wl-paste, xclip, xsel) found.\n")
        return ""

def main():
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: clip_helper.py [copy | paste | --cleanup]\n")
        sys.exit(1)
        
    cmd = sys.argv[1]
    
    if cmd == "--cleanup":
        # Safe self-cleanup (no-op)
        sys.exit(0)
        
    if cmd == "copy":
        # Read from stdin
        text = sys.stdin.read()
        if copy(text):
            sys.exit(0)
        sys.exit(1)
        
    elif cmd == "paste":
        content = paste()
        sys.stdout.write(content)
        sys.stdout.flush()
        sys.exit(0)
        
    else:
        sys.stderr.write(f"[ERROR] Unknown command: {cmd}\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
