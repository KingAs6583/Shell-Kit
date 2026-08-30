#!/usr/bin/env python3
import os
import sys
import time
import json
import shutil
import argparse
import subprocess
from datetime import datetime

# Color formatting constants
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
RESET = "\033[0m"

LOG_DIR = os.path.expanduser("~/.config/shell-kit")
HISTORY_LOG = os.path.join(LOG_DIR, "scheduler.log")
TASK_LOG_DIR = os.path.join(LOG_DIR, "logs")

def print_help():
    sys.stderr.write(f"""{CYAN}{BOLD}schedmgr — Infrastructure-Agnostic Schedule Manager{RESET}
Natively schedule and monitor periodic tasks (crontab / Windows Task Scheduler).

{BOLD}Usage:{RESET}
  schedmgr list                  List all shell-kit scheduled tasks and their execution history
  schedmgr add [options]         Add a new scheduled task (runs wizard if no args)
  schedmgr pause <name>          Disable a scheduled task
  schedmgr resume <name>         Enable a paused task
  schedmgr remove <name>         Delete a scheduled task
  schedmgr run <name>            Execute a task immediately
  schedmgr logs <name>           Display output logs for a task
  schedmgr run-job <name> <cmd>  (Internal) Runs cmd and logs status/time
  schedmgr --cleanup             Self-cleanup compliance flag (no-op)

{BOLD}Options:{RESET}
  -h, --help                     Show this help message and exit
  --name NAME                    Task identifier name
  --cmd COMMAND                  Shell command to schedule
  --schedule SCHED               Cron syntax (Linux) or daily/weekly/monthly (Windows)
  --time TIME                    Start time 'HH:MM' (Windows only, default 00:00)
""")

def write_history(task_name, exit_code, duration):
    os.makedirs(LOG_DIR, exist_ok=True)
    entry = {
        "time": datetime.now().isoformat(),
        "name": task_name,
        "code": exit_code,
        "duration": round(duration, 2)
    }
    with open(HISTORY_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

def get_last_run(task_name):
    if not os.path.exists(HISTORY_LOG):
        return "Never", "N/A"
        
    last_time = "Never"
    last_status = "N/A"
    
    try:
        with open(HISTORY_LOG, "r") as f:
            for line in f:
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line.strip())
                    if entry.get("name") == task_name:
                        last_time = entry.get("time").split(".")[0].replace("T", " ")
                        code = entry.get("code")
                        last_status = f"{GREEN}Success{RESET}" if code == 0 else f"{RED}Fail ({code}){RESET}"
                except Exception:
                    pass
    except Exception:
        pass
        
    return last_time, last_status

def clean_command_quotes(actual_cmd):
    stripped_lead = False
    if actual_cmd.startswith('\\"'):
        actual_cmd = actual_cmd[2:]
        stripped_lead = True
    elif actual_cmd.startswith('"'):
        actual_cmd = actual_cmd[1:]
        stripped_lead = True
    elif actual_cmd.startswith("'"):
        actual_cmd = actual_cmd[1:]
        stripped_lead = True
        
    if stripped_lead:
        if actual_cmd.endswith('\\"'):
            actual_cmd = actual_cmd[:-2]
        elif actual_cmd.endswith('"') or actual_cmd.endswith("'"):
            actual_cmd = actual_cmd[:-1]
            
        # Handle double escaped quotes at the end if any
        if actual_cmd.endswith('\\"'):
            actual_cmd = actual_cmd[:-2]
        elif actual_cmd.endswith('"') or actual_cmd.endswith("'"):
            actual_cmd = actual_cmd[:-1]
            
    return actual_cmd.replace('\\"', '"')

# ==========================================
# Linux / macOS Crontab Backend
# ==========================================

def get_crontab():
    res = subprocess.run(["crontab", "-l"], capture_output=True, text=True)
    return res.stdout if res.returncode == 0 else ""

def set_crontab(content):
    p = subprocess.Popen(["crontab", "-"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    stdout, stderr = p.communicate(input=content)
    return p.returncode == 0, stderr

def list_cron_tasks():
    content = get_crontab()
    tasks = []
    
    for line in content.splitlines():
        if "# SHELL-KIT-TASK:" in line:
            is_enabled = not line.strip().startswith("#")
            
            # Parse parts
            clean_line = line.strip().lstrip("#").strip()
            parts = clean_line.split("# SHELL-KIT-TASK:")
            cmd_part = parts[0].strip()
            task_name = parts[1].strip()
            
            # Extract cron schedule
            # e.g., 0 0 * * * python3 ... run-job name "cmd"
            cmd_words = cmd_part.split()
            schedule = " ".join(cmd_words[:5])
            
            # Extract actual command
            # The run-job call looks like: run-job <name> "<actual_cmd>"
            actual_cmd = "Unknown"
            if "run-job" in cmd_part:
                run_job_index = cmd_part.find("run-job")
                actual_cmd_part = cmd_part[run_job_index + len("run-job"):].strip()
                # Remove task name to get actual command
                actual_cmd_part = actual_cmd_part[len(task_name):].strip()
                if (actual_cmd_part.startswith('"') and actual_cmd_part.endswith('"')) or \
                   (actual_cmd_part.startswith("'") and actual_cmd_part.endswith("'")):
                    actual_cmd = actual_cmd_part[1:-1]
                else:
                    actual_cmd = actual_cmd_part
                    
            last_run, last_status = get_last_run(task_name)
            status_str = f"{GREEN}Enabled{RESET}" if is_enabled else f"{YELLOW}Disabled{RESET}"
            
            tasks.append((task_name, actual_cmd, schedule, status_str, last_run, last_status))
            
    return tasks

def add_cron_task(name, cmd, schedule):
    # Formulate wrap command
    python_path = sys.executable
    script_path = os.path.abspath(__file__)
    wrapped_cmd = f'{python_path} {script_path} run-job {name} "{cmd}"'
    cron_line = f"{schedule} {wrapped_cmd} # SHELL-KIT-TASK: {name}"
    
    current = get_crontab()
    
    # Check duplicate
    if f"# SHELL-KIT-TASK: {name}" in current:
        print(f"{RED}[ERROR] Task '{name}' already exists. Remove it first.{RESET}")
        sys.exit(1)
        
    new_content = current.rstrip()
    if new_content:
        new_content += "\n"
    new_content += f"{cron_line}\n"
    
    success, err = set_crontab(new_content)
    if success:
        print(f"{GREEN}[SUCCESS] Scheduled task '{name}' added to crontab.{RESET}")
    else:
        print(f"{RED}[ERROR] Failed to save crontab: {err}{RESET}")

def change_cron_task_state(name, enable=True):
    content = get_crontab()
    lines = content.splitlines()
    found = False
    
    for i, line in enumerate(lines):
        if f"# SHELL-KIT-TASK: {name}" in line:
            found = True
            is_commented = line.strip().startswith("#")
            
            if enable and is_commented:
                # Uncomment
                lines[i] = line.lstrip("#").strip()
            elif not enable and not is_commented:
                # Comment out
                lines[i] = f"# {line.strip()}"
                
    if not found:
        print(f"{RED}[ERROR] Task '{name}' not found.{RESET}")
        sys.exit(1)
        
    success, err = set_crontab("\n".join(lines) + "\n")
    if success:
        state = "enabled" if enable else "disabled"
        print(f"{GREEN}[SUCCESS] Task '{name}' successfully {state}.{RESET}")
    else:
        print(f"{RED}[ERROR] Failed to save crontab: {err}{RESET}")

def remove_cron_task(name):
    content = get_crontab()
    lines = content.splitlines()
    new_lines = [line for line in lines if f"# SHELL-KIT-TASK: {name}" not in line]
    
    if len(lines) == len(new_lines):
        print(f"{RED}[ERROR] Task '{name}' not found.{RESET}")
        sys.exit(1)
        
    success, err = set_crontab("\n".join(new_lines) + "\n")
    if success:
        print(f"{GREEN}[SUCCESS] Task '{name}' removed from crontab.{RESET}")
    else:
        print(f"{RED}[ERROR] Failed to save crontab: {err}{RESET}")

# ==========================================
# Windows schtasks.exe Backend
# ==========================================

def list_windows_tasks():
    # Query tasks grouped under the path "shell-kit\"
    tasks = []
    try:
        # Querying task list in CSV format
        res = subprocess.run(["schtasks", "/query", "/fo", "csv", "/v"], capture_output=True, text=True, errors="ignore")
        if res.returncode == 0:
            import csv
            reader = csv.reader(res.stdout.strip().splitlines())
            for parts in reader:
                if not parts or len(parts) < 2:
                    continue
                task_path = parts[1]
                if "shell-kit\\" in task_path or "shell-kit/" in task_path:
                    task_name = task_path.split("\\")[-1]
                    status = parts[11] if len(parts) > 11 else parts[3]
                    status_str = f"{GREEN}Enabled{RESET}" if status == "Enabled" or status == "Ready" else f"{YELLOW}Disabled{RESET}"
                    
                    cmd_part = parts[8] if len(parts) > 8 else "Unknown"
                    actual_cmd = "Unknown"
                    if "run-job" in cmd_part:
                        run_job_index = cmd_part.find("run-job")
                        actual_cmd_part = cmd_part[run_job_index + len("run-job"):].strip()
                        actual_cmd_part = actual_cmd_part[len(task_name):].strip()
                        
                        actual_cmd = clean_command_quotes(actual_cmd_part)
                        
                    schedule = parts[18].strip() if len(parts) > 18 else "Daily"
                    
                    last_run, last_status = get_last_run(task_name)
                    tasks.append((task_name, actual_cmd, schedule, status_str, last_run, last_status))
    except Exception as e:
        sys.stderr.write(f"[ERROR] Failed to query Windows Task Scheduler: {e}\n")
        
    return tasks

def add_windows_task(name, cmd, schedule, start_time="00:00"):
    # Formulate wrap command
    python_path = sys.executable
    script_path = os.path.abspath(__file__)
    # Windows requires escaped quotes around arguments
    wrapped_cmd = f'"{python_path}" "{script_path}" run-job {name} \\"{cmd}\\"'
    task_path = f"shell-kit\\{name}"
    
    # Translate schedule
    sc = "daily"
    if schedule == "weekly":
        sc = "weekly"
    elif schedule == "monthly":
        sc = "monthly"
        
    cmd_args = [
        "schtasks", "/create",
        "/tn", task_path,
        "/tr", wrapped_cmd,
        "/sc", sc,
        "/st", start_time,
        "/f"
    ]
    
    try:
        res = subprocess.run(cmd_args, capture_output=True, text=True, errors="ignore")
        if res.returncode == 0:
            print(f"{GREEN}[SUCCESS] Scheduled task '{name}' added to Windows Task Scheduler.{RESET}")
        else:
            print(f"{RED}[ERROR] Failed to create task: {res.stderr}{RESET}")
    except Exception as e:
        print(f"{RED}[ERROR] Failed to execute schtasks: {e}{RESET}")

def change_windows_task_state(name, enable=True):
    task_path = f"shell-kit\\{name}"
    action = "/enable" if enable else "/disable"
    
    try:
        res = subprocess.run(["schtasks", "/change", "/tn", task_path, action], capture_output=True, text=True, errors="ignore")
        if res.returncode == 0:
            state = "enabled" if enable else "disabled"
            print(f"{GREEN}[SUCCESS] Task '{name}' successfully {state}.{RESET}")
        else:
            print(f"{RED}[ERROR] Failed to change task state: {res.stderr}{RESET}")
    except Exception as e:
        print(f"{RED}[ERROR] Failed to change task state: {e}{RESET}")

def remove_windows_task(name):
    task_path = f"shell-kit\\{name}"
    try:
        res = subprocess.run(["schtasks", "/delete", "/tn", task_path, "/f"], capture_output=True, text=True, errors="ignore")
        if res.returncode == 0:
            print(f"{GREEN}[SUCCESS] Task '{name}' removed from Windows Task Scheduler.{RESET}")
        else:
            print(f"{RED}[ERROR] Failed to remove task: {res.stderr}{RESET}")
    except Exception as e:
        print(f"{RED}[ERROR] Failed to remove task: {e}{RESET}")

def run_windows_task(name):
    task_path = f"shell-kit\\{name}"
    try:
        res = subprocess.run(["schtasks", "/run", "/tn", task_path], capture_output=True, text=True, errors="ignore")
        if res.returncode == 0:
            print(f"{GREEN}[SUCCESS] Task '{name}' triggered successfully.{RESET}")
        else:
            print(f"{RED}[ERROR] Failed to run task: {res.stderr}{RESET}")
    except Exception as e:
        print(f"{RED}[ERROR] Failed to run task: {e}{RESET}")

# ==========================================
# Unified Platform CLI Interface
# ==========================================

def format_ascii_table(headers, rows):
    if not headers or not rows:
        return "No scheduled tasks found."
        
    num_cols = len(headers)
    col_widths = [len(h) for h in headers]
    for r in rows:
        for i in range(num_cols):
            # Clean string color escapes to calculate real length
            clean_cell = str(r[i]).replace(GREEN, "").replace(RED, "").replace(YELLOW, "").replace(CYAN, "").replace(BOLD, "").replace(RESET, "")
            col_widths[i] = max(col_widths[i], len(clean_cell))
            
    sep_line = "+" + "+".join(["-" * (w + 2) for w in col_widths]) + "+"
    
    def rjust_with_escape(val, width):
        clean_val = str(val).replace(GREEN, "").replace(RED, "").replace(YELLOW, "").replace(CYAN, "").replace(BOLD, "").replace(RESET, "")
        delta = len(str(val)) - len(clean_val)
        return str(val).ljust(width + delta)
        
    output = []
    output.append(sep_line)
    header_cells = [f" {headers[i].ljust(col_widths[i])} " for i in range(num_cols)]
    output.append("|" + "|".join(header_cells) + "|")
    output.append(sep_line)
    
    for r in rows:
        row_cells = [f" {rjust_with_escape(r[i], col_widths[i])} " for i in range(num_cols)]
        output.append("|" + "|".join(row_cells) + "|")
        
    output.append(sep_line)
    return "\n".join(output)

def do_list():
    headers = ["Task Name", "Command", "Schedule", "Status", "Last Run Time", "Result"]
    if sys.platform == "win32":
        rows = list_windows_tasks()
    else:
        rows = list_cron_tasks()
        
    print(f"\n{CYAN}{BOLD}Scheduled Tasks Registry{RESET}")
    print("=" * 90)
    print(format_ascii_table(headers, rows))
    print(f"\nLogs are stored in: {YELLOW}{HISTORY_LOG}{RESET}")
    print(f"Task output logs:   {YELLOW}{TASK_LOG_DIR}/<task_name>.log{RESET}\n")

def run_job(name, cmd):
    """
    Internal execution wrapper that runs the command and logs history/output.
    """
    cmd = clean_command_quotes(cmd)
    
    os.makedirs(TASK_LOG_DIR, exist_ok=True)
    task_log_path = os.path.join(TASK_LOG_DIR, f"{name}.log")
    
    start_time = time.time()
    
    # Run command and write output directly to task log
    with open(task_log_path, "w") as log_file:
        log_file.write(f"=== Execution Start: {datetime.now().isoformat()} ===\n")
        log_file.write(f"Task:    {name}\n")
        log_file.write(f"Command: {cmd}\n")
        log_file.write("-" * 50 + "\n\n")
        log_file.flush()
        
        try:
            res = subprocess.run(cmd, shell=True, stdout=log_file, stderr=subprocess.log_file if hasattr(subprocess, "log_file") else log_file, text=True)
            exit_code = res.returncode
        except Exception as e:
            log_file.write(f"\n[CRITICAL ERROR] Execution failed to launch: {e}\n")
            exit_code = 99
            
        duration = time.time() - start_time
        log_file.write(f"\n" + "-" * 50 + "\n")
        log_file.write(f"=== Execution End: {datetime.now().isoformat()} ===\n")
        log_file.write(f"Exit Code: {exit_code}\n")
        log_file.write(f"Duration:  {round(duration, 2)} seconds\n")
        
    write_history(name, exit_code, duration)
    sys.exit(exit_code)

def run_job_manually(name):
    # Retrieve the command from scheduler config
    # On Unix, parse from crontab. On Windows, parse from schtasks.
    cmd = None
    if sys.platform == "win32":
        for task_name, actual_cmd, _, _, _, _ in list_windows_tasks():
            if task_name == name:
                cmd = actual_cmd
                break
    else:
        for task_name, actual_cmd, _, _, _, _ in list_cron_tasks():
            if task_name == name:
                cmd = actual_cmd
                break
                
    if not cmd:
        sys.stderr.write(f"{RED}[ERROR] Task '{name}' not found.{RESET}\n")
        sys.exit(1)
        
    print(f"{CYAN}Manually executing task '{name}': {GREEN}{BOLD}{cmd}{RESET}...")
    
    # Run the job through our wrapper so it's fully tracked and logged
    run_job(name, cmd)

def display_logs(name):
    task_log_path = os.path.join(TASK_LOG_DIR, f"{name}.log")
    if not os.path.exists(task_log_path):
        print(f"{YELLOW}[WARN] No execution logs found for task '{name}'.{RESET}")
        return
        
    print(f"\n{CYAN}{BOLD}Logs for Task '{name}' ({task_log_path}){RESET}")
    print("=" * 80)
    with open(task_log_path, "r") as f:
        print(f.read())
    print("=" * 80)

def run_wizard():
    print(f"\n{CYAN}{BOLD}schedmgr — Task Creation Wizard{RESET}")
    print("=" * 60)
    
    # 1. Ask for task name
    sys.stdout.write("Enter task name (alphanumeric, no spaces): ")
    sys.stdout.flush()
    name = sys.stdin.readline().strip()
    if not name or not name.isalnum():
        print(f"{RED}[ERROR] Task name must be alphanumeric with no spaces.{RESET}")
        sys.exit(1)
        
    # 2. Ask which command to run
    print("\nSelect command to schedule:")
    print("  1) diskguard clean --yes (Prune old caches)")
    print("  2) bkrun (Backup dirty git repos and assets)")
    print("  3) Custom shell command")
    sys.stdout.write("Choice (1-3): ")
    sys.stdout.flush()
    cmd_choice = sys.stdin.readline().strip()
    
    cmd = ""
    if cmd_choice == "1":
        cmd = "diskguard clean --yes"
    elif cmd_choice == "2":
        cmd = "bkrun"
    elif cmd_choice == "3":
        sys.stdout.write("Enter custom command: ")
        sys.stdout.flush()
        cmd = sys.stdin.readline().strip()
    else:
        print(f"{RED}[ERROR] Invalid command choice.{RESET}")
        sys.exit(1)
        
    if not cmd:
        print(f"{RED}[ERROR] Command cannot be empty.{RESET}")
        sys.exit(1)
        
    # 3. Ask when to run
    print("\nSelect schedule frequency:")
    print("  1) Daily")
    print("  2) Weekly")
    print("  3) Monthly")
    sys.stdout.write("Choice (1-3): ")
    sys.stdout.flush()
    freq_choice = sys.stdin.readline().strip()
    
    if freq_choice not in ("1", "2", "3"):
        print(f"{RED}[ERROR] Invalid frequency choice.{RESET}")
        sys.exit(1)
        
    day_val = "MON"
    if freq_choice == "2": # Weekly
        sys.stdout.write("Enter day of the week (SUN, MON, TUE, WED, THU, FRI, SAT) [default MON]: ")
        sys.stdout.flush()
        day_input = sys.stdin.readline().strip().upper() or "MON"
        days_map = {"SUN": "0", "MON": "1", "TUE": "2", "WED": "3", "THU": "4", "FRI": "5", "SAT": "6"}
        if day_input not in days_map:
            print(f"{RED}[ERROR] Invalid day name. Use SUN-SAT.{RESET}")
            sys.exit(1)
        day_val = day_input
    elif freq_choice == "3": # Monthly
        sys.stdout.write("Enter day of the month (1-31) [default 1]: ")
        sys.stdout.flush()
        day_input = sys.stdin.readline().strip() or "1"
        if not day_input.isdigit() or not (1 <= int(day_input) <= 31):
            print(f"{RED}[ERROR] Invalid day number. Use 1-31.{RESET}")
            sys.exit(1)
        day_val = day_input
        
    sys.stdout.write("Enter run time in HH:MM format (24-hour clock, e.g. 13:30) [default 00:00]: ")
    sys.stdout.flush()
    time_input = sys.stdin.readline().strip() or "00:00"
    
    # Validate time format
    try:
        parts = time_input.split(":")
        if len(parts) != 2:
            raise ValueError()
        hour = int(parts[0])
        minute = int(parts[1])
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError()
    except ValueError:
        print(f"{RED}[ERROR] Invalid time format. Use HH:MM.{RESET}")
        sys.exit(1)
        
    # 4. Save Task
    if sys.platform == "win32":
        # Windows schtasks
        freq_str = "daily"
        if freq_choice == "2":
            freq_str = "weekly"
        elif freq_choice == "3":
            freq_str = "monthly"
            
        # Build command args manually to call the appropriate helper
        wrapped_cmd = f'"{sys.executable}" "{os.path.abspath(__file__)}" run-job {name} \\"{cmd}\\"'
        task_path = f"shell-kit\\{name}"
        
        cmd_args = ["schtasks", "/create", "/tn", task_path, "/tr", wrapped_cmd, "/sc", freq_str, "/st", time_input]
        if freq_choice == "2":
            cmd_args.extend(["/d", day_val[:3]]) # MON-SUN
        elif freq_choice == "3":
            cmd_args.extend(["/d", day_val]) # 1-31
        cmd_args.append("/f")
        
        try:
            res = subprocess.run(cmd_args, capture_output=True, text=True, errors="ignore")
            if res.returncode == 0:
                print(f"{GREEN}[SUCCESS] Scheduled task '{name}' added to Windows Task Scheduler.{RESET}")
            else:
                print(f"{RED}[ERROR] Failed to create task: {res.stderr}{RESET}")
        except Exception as e:
            print(f"{RED}[ERROR] Failed to execute schtasks: {e}{RESET}")
            
    else:
        # Linux/Mac Crontab
        # Translate to cron expression
        cron_min = str(minute)
        cron_hour = str(hour)
        
        if freq_choice == "1": # Daily
            cron_expr = f"{cron_min} {cron_hour} * * *"
        elif freq_choice == "2": # Weekly
            days_map = {"SUN": "0", "MON": "1", "TUE": "2", "WED": "3", "THU": "4", "FRI": "5", "SAT": "6"}
            cron_expr = f"{cron_min} {cron_hour} * * {days_map[day_val]}"
        elif freq_choice == "3": # Monthly
            cron_expr = f"{cron_min} {cron_hour} {day_val} * *"
            
        add_cron_task(name, cmd, cron_expr)

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print_help()
        sys.exit(0)
        
    cmd = sys.argv[1]
    
    if cmd == "--cleanup":
        if os.path.exists(HISTORY_LOG):
            try:
                os.remove(HISTORY_LOG)
            except Exception:
                pass
        if os.path.exists(TASK_LOG_DIR):
            try:
                shutil.rmtree(TASK_LOG_DIR)
            except Exception:
                pass
        sys.stderr.write(f"{GREEN}[CLEANUP] schedmgr history and logs deleted.{RESET}\n")
        sys.exit(0)
        
    if cmd == "list":
        do_list()
    elif cmd == "add":
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument("--name")
        parser.add_argument("--cmd")
        parser.add_argument("--schedule")
        parser.add_argument("--time", default="00:00")
        args, _ = parser.parse_known_args(sys.argv[2:])
        
        if args.name and args.cmd and args.schedule:
            if sys.platform == "win32":
                add_windows_task(args.name, args.cmd, args.schedule, args.time)
            else:
                add_cron_task(args.name, args.cmd, args.schedule)
        else:
            run_wizard()
            
    elif cmd in ("pause", "disable"):
        if len(sys.argv) < 3:
            sys.stderr.write(f"{RED}[ERROR] Task name required. Usage: schedmgr pause <name>{RESET}\n")
            sys.exit(1)
        name = sys.argv[2]
        if sys.platform == "win32":
            change_windows_task_state(name, enable=False)
        else:
            change_cron_task_state(name, enable=False)
            
    elif cmd in ("resume", "enable"):
        if len(sys.argv) < 3:
            sys.stderr.write(f"{RED}[ERROR] Task name required. Usage: schedmgr resume <name>{RESET}\n")
            sys.exit(1)
        name = sys.argv[2]
        if sys.platform == "win32":
            change_windows_task_state(name, enable=True)
        else:
            change_cron_task_state(name, enable=True)
            
    elif cmd in ("remove", "delete"):
        if len(sys.argv) < 3:
            sys.stderr.write(f"{RED}[ERROR] Task name required. Usage: schedmgr remove <name>{RESET}\n")
            sys.exit(1)
        name = sys.argv[2]
        if sys.platform == "win32":
            remove_windows_task(name)
        else:
            remove_cron_task(name)
            
    elif cmd == "run":
        if len(sys.argv) < 3:
            sys.stderr.write(f"{RED}[ERROR] Task name required. Usage: schedmgr run <name>{RESET}\n")
            sys.exit(1)
        name = sys.argv[2]
        if sys.platform == "win32":
            run_windows_task(name)
        else:
            run_job_manually(name)
            
    elif cmd == "logs":
        if len(sys.argv) < 3:
            sys.stderr.write(f"{RED}[ERROR] Task name required. Usage: schedmgr logs <name>{RESET}\n")
            sys.exit(1)
        name = sys.argv[2]
        display_logs(name)
        
    elif cmd == "run-job":
        # Internal wrapper execution call
        if len(sys.argv) < 4:
            sys.exit(1)
        name = sys.argv[2]
        # Reconstruct full command line if split by the OS scheduler
        command = " ".join(sys.argv[3:])
        run_job(name, command)
        
    else:
        sys.stderr.write(f"{RED}[ERROR] Unknown command: '{cmd}'{RESET}\n")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
