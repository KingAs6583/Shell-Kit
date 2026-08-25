#!/usr/bin/env python3
import os
import sys
import subprocess
import re
import csv

# Color formatting constants
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
RESET = "\033[0m"

def print_help():
    sys.stderr.write(f"""{CYAN}{BOLD}portwatch — Process Port Watcher & Killer{RESET}
Scan processes listening on a network port and optionally terminate them.

{BOLD}Usage:{RESET}
  portwatch <port_number>
  portwatch --cleanup

{BOLD}Options:{RESET}
  -h, --help    Show this help message and exit
  --cleanup     Self-cleanup compliance flag (no-op)
""")

def get_process_info_windows(pid):
    """
    Retrieves process details on Windows using tasklist.
    """
    try:
        # Run tasklist with CSV formatting
        cmd = ["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV"]
        res = subprocess.run(cmd, capture_output=True, text=True, errors="ignore")
        if res.returncode == 0:
            reader = csv.reader(res.stdout.strip().splitlines())
            rows = list(reader)
            if len(rows) >= 2:
                # Header: Image Name, PID, Session Name, Session#, Mem Usage
                image_name = rows[1][0]
                mem_usage = rows[1][4]
                return {
                    "pid": pid,
                    "name": image_name,
                    "command": image_name, # Windows tasklist doesn't show full args easily without wmic
                    "memory": mem_usage,
                    "duration": "N/A"
                }
    except Exception as e:
        sys.stderr.write(f"{YELLOW}[WARN] Failed to get process info via tasklist: {e}{RESET}\n")
    return {"pid": pid, "name": "Unknown", "command": "Unknown", "memory": "N/A", "duration": "N/A"}

def get_process_info_unix(pid):
    """
    Retrieves process details on Linux/macOS using ps.
    """
    try:
        # Get command line
        cmd_args = ["ps", "-p", str(pid), "-o", "args="]
        res_args = subprocess.run(cmd_args, capture_output=True, text=True, errors="ignore")
        command = res_args.stdout.strip() if res_args.returncode == 0 else "Unknown"

        # Get stats: comm, rss (kb), etime
        cmd_stats = ["ps", "-p", str(pid), "-o", "comm=,rss=,etime="]
        res_stats = subprocess.run(cmd_stats, capture_output=True, text=True, errors="ignore")
        if res_stats.returncode == 0:
            parts = res_stats.stdout.strip().split()
            if len(parts) >= 3:
                comm = parts[0]
                rss_kb = int(parts[1])
                etime = parts[2]
                
                # Format memory
                if rss_kb > 1024 * 1024:
                    mem = f"{rss_kb / (1024*1024):.1f} GB"
                else:
                    mem = f"{rss_kb / 1024:.1f} MB"
                    
                return {
                    "pid": pid,
                    "name": comm,
                    "command": command,
                    "memory": mem,
                    "duration": etime
                }
    except Exception as e:
        sys.stderr.write(f"{YELLOW}[WARN] Failed to get process info via ps: {e}{RESET}\n")
    return {"pid": pid, "name": "Unknown", "command": "Unknown", "memory": "N/A", "duration": "N/A"}

def kill_process(pid):
    """
    Kills process by PID.
    """
    if sys.platform == "win32":
        cmd = ["taskkill", "/F", "/PID", str(pid)]
    else:
        cmd = ["kill", "-9", str(pid)]
        
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            print(f"{GREEN}[SUCCESS] Terminated process {pid}.{RESET}")
            return True
        else:
            print(f"{RED}[ERROR] Failed to kill process {pid}: {res.stderr.strip()}{RESET}")
    except Exception as e:
        print(f"{RED}[ERROR] Failed to execute kill command: {e}{RESET}")
    return False

def scan_port_windows(port):
    """
    Scans port on Windows using netstat.
    """
    pids = set()
    try:
        res = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        if res.returncode != 0:
            sys.stderr.write(f"{RED}[ERROR] netstat command failed with code {res.returncode}.{RESET}\n")
            sys.exit(1)
            
        # Parse output for lines containing :<port> followed by state and PID
        # E.g. TCP    0.0.0.0:8000           0.0.0.0:0              LISTENING       1234
        pattern = re.compile(rf":{port}\s+.*?\s+(LISTENING|ESTABLISHED|CLOSE_WAIT|TIME_WAIT)\s+(\d+)\s*$")
        for line in res.stdout.splitlines():
            m = pattern.search(line.strip())
            if m:
                pids.add(int(m.group(2)))
    except Exception as e:
        sys.stderr.write(f"{RED}[ERROR] Failed to scan ports: {e}{RESET}\n")
        sys.exit(1)
    return list(pids)

def scan_port_unix(port):
    """
    Scans port on Linux/macOS using lsof.
    """
    pids = set()
    try:
        # Try lsof first
        res = subprocess.run(["lsof", "-i", f":{port}", "-t"], capture_output=True, text=True)
        if res.returncode == 0:
            for pid in res.stdout.strip().splitlines():
                if pid.strip().isdigit():
                    pids.add(int(pid.strip()))
            return list(pids)
            
        # Fallback to ss
        res = subprocess.run(["ss", "-tulpn"], capture_output=True, text=True)
        if res.returncode == 0:
            # Parse ss output E.g. users:(("node",pid=1234,fd=19))
            pattern = re.compile(rf":{port}\s+.*?users:\(\(.*?,pid=(\d+),")
            for line in res.stdout.splitlines():
                m = pattern.search(line.strip())
                if m:
                    pids.add(int(m.group(1)))
    except Exception as e:
        sys.stderr.write(f"{YELLOW}[WARN] Port scan tool error: {e}{RESET}\n")
    return list(pids)

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print_help()
        sys.exit(0)
        
    port_arg = sys.argv[1]
    
    if port_arg == "--cleanup":
        # Compliance flag, no-op since no temporary files are generated
        sys.stderr.write(f"{GREEN}[CLEANUP] portwatch requires no cleanup operations.{RESET}\n")
        sys.exit(0)
        
    if not port_arg.isdigit():
        sys.stderr.write(f"{RED}[ERROR] Port must be a valid integer. Got: '{port_arg}'{RESET}\n")
        print_help()
        sys.exit(1)
        
    port = int(port_arg)
    
    print(f"{CYAN}Scanning processes listening on port {port}...{RESET}")
    
    if sys.platform == "win32":
        pids = scan_port_windows(port)
    else:
        pids = scan_port_unix(port)
        
    if not pids:
        print(f"{GREEN}No active processes found listening on port {port}.{RESET}")
        sys.exit(0)
        
    print(f"\n{YELLOW}{BOLD}Found {len(pids)} process(es) listening on port {port}:{RESET}")
    print("=" * 60)
    
    processes = []
    for pid in pids:
        if sys.platform == "win32":
            info = get_process_info_windows(pid)
        else:
            info = get_process_info_unix(pid)
        processes.append(info)
        
        print(f"  {BOLD}PID:{RESET}         {info['pid']}")
        print(f"  {BOLD}Process:{RESET}     {info['name']}")
        print(f"  {BOLD}Command:{RESET}     {info['command']}")
        print(f"  {BOLD}Memory:{RESET}      {info['memory']}")
        print(f"  {BOLD}Duration:{RESET}    {info['duration']}")
        print("-" * 60)
        
    # Interactive kill prompt
    try:
        sys.stdout.write(f"\nWould you like to terminate these process(es)? (y/N): ")
        sys.stdout.flush()
        choice = sys.stdin.readline().strip().lower()
        if choice in ("y", "yes"):
            killed_all = True
            for proc in processes:
                if not kill_process(proc["pid"]):
                    killed_all = False
            if killed_all:
                sys.exit(0)
            else:
                sys.exit(1)
        else:
            print("Operation cancelled. Process(es) left active.")
            sys.exit(0)
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(0)

if __name__ == "__main__":
    main()
