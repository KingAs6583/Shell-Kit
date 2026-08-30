#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

# Color formatting constants
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
RESET = "\033[0m"

USE_SUDO = False

def print_help():
    sys.stderr.write(f"""{CYAN}{BOLD}dkutil — Container Engine Manager (Docker & Podman){RESET}
Manage running containers, clean caches, and tail logs.

{BOLD}Usage:{RESET}
  dklist              Show running containers with CPU/Memory usage
  dkclean             Interactively prune stopped containers, images, and volumes
  dklogs <container>  Tail container logs in real time
  dkutil --cleanup    Self-cleanup compliance flag (no-op)

{BOLD}Options:{RESET}
  -h, --help          Show this help message and exit
""")

def detect_engine():
    if shutil.which("docker"):
        return "docker"
    if shutil.which("podman"):
        return "podman"
    return None

def run_cmd(args, capture_output=True, text=True):
    global USE_SUDO
    engine = detect_engine()
    if not engine:
        sys.stderr.write(f"{RED}[ERROR] Neither Docker nor Podman was found in PATH.{RESET}\n")
        sys.exit(1)
        
    cmd = [engine] + args
    if USE_SUDO:
        cmd = ["sudo"] + cmd
        
    try:
        res = subprocess.run(cmd, capture_output=capture_output, text=text, errors="ignore")
        
        is_permission_denied = False
        if res.returncode != 0:
            err_msg = res.stderr.lower() if res.stderr else ""
            if "permission denied" in err_msg or "connect:" in err_msg or "access denied" in err_msg:
                is_permission_denied = True
                
        if is_permission_denied and not USE_SUDO:
            sys.stdout.write(f"\n{YELLOW}{BOLD}[WARN] Command requires root permissions. Run with sudo? (y/N): {RESET}")
            sys.stdout.flush()
            choice = sys.stdin.readline().strip().lower()
            if choice in ("y", "yes"):
                USE_SUDO = True
                cmd = ["sudo", engine] + args
                res = subprocess.run(cmd, capture_output=capture_output, text=text, errors="ignore")
            else:
                sys.stderr.write(f"{RED}[ERROR] Permission denied.{RESET}\n")
                sys.exit(res.returncode)
                
        return res
    except Exception as e:
        sys.stderr.write(f"{RED}[ERROR] Failed to run command: {e}{RESET}\n")
        sys.exit(1)

def exec_cmd_interactive(args):
    global USE_SUDO
    engine = detect_engine()
    if not engine:
        sys.stderr.write(f"{RED}[ERROR] Neither Docker nor Podman was found in PATH.{RESET}\n")
        sys.exit(1)
        
    # Run a dry-run check to verify if sudo is needed
    run_cmd(["ps"], capture_output=True)
    
    cmd = [engine] + args
    if USE_SUDO:
        cmd = ["sudo"] + cmd
        
    try:
        if sys.platform != "win32":
            os.execvp(cmd[0], cmd)
        else:
            subprocess.run(cmd)
    except Exception as e:
        sys.stderr.write(f"{RED}[ERROR] Failed to execute interactive command: {e}{RESET}\n")
        sys.exit(1)

def format_ascii_table(headers, rows, max_col_width=40):
    if not headers:
        return "No active containers found."
        
    str_headers = [str(h) for h in headers]
    str_rows = []
    for r in rows:
        str_rows.append([str(cell) if cell is not None else "NULL" for cell in r])
        
    num_cols = len(str_headers)
    col_widths = [len(h) for h in str_headers]
    for r in str_rows:
        for i in range(min(num_cols, len(r))):
            col_widths[i] = max(col_widths[i], len(r[i]))
            
    col_widths = [min(w, max_col_width) for w in col_widths]
    
    def fit_cell(val, width):
        val = val.replace("\n", " ").replace("\r", "")
        if len(val) > width:
            return val[:width-3] + "..."
        return val.ljust(width)
        
    sep_line = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
    
    output = []
    output.append(sep_line)
    header_cells = [f" {fit_cell(str_headers[i], col_widths[i])} " for i in range(num_cols)]
    output.append("|" + "|".join(header_cells) + "|")
    output.append(sep_line)
    
    for r in str_rows:
        row_cells = []
        for i in range(num_cols):
            val = r[i] if i < len(r) else ""
            row_cells.append(f" {fit_cell(val, col_widths[i])} ")
        output.append("|" + "|".join(row_cells) + "|")
        
    output.append(sep_line)
    return "\n".join(output)

def do_list():
    engine = detect_engine()
    print(f"{CYAN}Querying containers from: {GREEN}{BOLD}{engine}{RESET}...")
    
    # 1. Fetch container list
    # Format: ID \t Name \t Image \t Status \t Ports
    res_ps = run_cmd(["ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}"])
    if res_ps.returncode != 0:
        print(f"{RED}[ERROR] Failed to query containers.{RESET}")
        sys.exit(1)
        
    ps_lines = res_ps.stdout.strip().splitlines()
    if not ps_lines:
        print(f"{GREEN}No running containers found.{RESET}")
        return
        
    # 2. Fetch stats
    # Format: ID \t CPU \t Mem
    res_stats = run_cmd(["stats", "--no-stream", "--format", "{{.ID}}\t{{.CPUPerc}}\t{{.MemUsage}}"])
    stats_dict = {}
    if res_stats.returncode == 0:
        for line in res_stats.stdout.strip().splitlines():
            parts = line.split("\t")
            if len(parts) >= 3:
                cid = parts[0]
                cpu = parts[1]
                mem = parts[2]
                stats_dict[cid] = (cpu, mem)
                
    headers = ["Container ID", "Name", "Image", "Status", "Ports", "CPU", "Memory"]
    rows = []
    for line in ps_lines:
        parts = line.split("\t")
        if len(parts) >= 5:
            cid = parts[0]
            name = parts[1]
            image = parts[2]
            status = parts[3]
            ports = parts[4] if parts[4] else "None"
            
            # Map stats
            cpu, mem = "N/A", "N/A"
            if cid in stats_dict:
                cpu, mem = stats_dict[cid]
            else:
                # Try matching by name or partial prefix
                for key, val in stats_dict.items():
                    if cid.startswith(key) or key.startswith(cid):
                        cpu, mem = val
                        break
                        
            rows.append((cid, name, image, status, ports, cpu, mem))
            
    print(format_ascii_table(headers, rows))

def do_clean():
    print(f"\n{CYAN}{BOLD}Container Cleanup utility{RESET}")
    print("=" * 60)
    
    sys.stdout.write("Prune stopped containers? (y/N): ")
    sys.stdout.flush()
    clean_containers = sys.stdin.readline().strip().lower() in ("y", "yes")
    
    sys.stdout.write("Prune unused/dangling images? (y/N): ")
    sys.stdout.flush()
    clean_images = sys.stdin.readline().strip().lower() in ("y", "yes")
    
    sys.stdout.write("Prune unused volumes? (y/N): ")
    sys.stdout.flush()
    clean_volumes = sys.stdin.readline().strip().lower() in ("y", "yes")
    
    if not (clean_containers or clean_images or clean_volumes):
        print("No actions selected. Exiting.")
        return
        
    print("-" * 60)
    
    if clean_containers:
        print(f"{CYAN}Pruning stopped containers...{RESET}")
        res = run_cmd(["container", "prune", "-f"], capture_output=False)
        
    if clean_images:
        print(f"{CYAN}Pruning unused images...{RESET}")
        res = run_cmd(["image", "prune", "-f"], capture_output=False)
        
    if clean_volumes:
        print(f"{CYAN}Pruning unused volumes...{RESET}")
        res = run_cmd(["volume", "prune", "-f"], capture_output=False)
        
    print(f"\n{GREEN}[SUCCESS] Cleanup operations complete.{RESET}\n")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print_help()
        sys.exit(0)
        
    cmd = sys.argv[1]
    
    if cmd == "--cleanup":
        sys.stderr.write(f"{GREEN}[CLEANUP] dkutil requires no cleanup operations.{RESET}\n")
        sys.exit(0)
        
    # Verify engine availability first
    engine = detect_engine()
    if not engine:
        sys.stderr.write(f"{RED}[ERROR] Neither Docker nor Podman was found in PATH.{RESET}\n")
        sys.exit(1)
        
    if cmd == "list":
        do_list()
    elif cmd == "clean":
        do_clean()
    elif cmd == "logs":
        if len(sys.argv) < 3:
            sys.stderr.write(f"{RED}[ERROR] Container name/ID required. Usage: dklogs <container>{RESET}\n")
            sys.exit(1)
        container = sys.argv[2]
        print(f"{CYAN}Tailing logs for container: {GREEN}{BOLD}{container}{RESET} (Ctrl+C to exit)...")
        exec_cmd_interactive(["logs", "-f", "--tail", "100", container])
    else:
        sys.stderr.write(f"{RED}[ERROR] Unknown command: '{cmd}'{RESET}\n")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
