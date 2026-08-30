#!/usr/bin/env python3
import os
import sys
import shutil
import tempfile
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
    sys.stderr.write(f"""{CYAN}{BOLD}ngutil — Nginx Web Server Utility{RESET}
Manage Nginx configurations, tail filtered error logs, and request SSL certificates.

{BOLD}Usage:{RESET}
  ngstat              Validate configurations and display Nginx status
  ngerr               Tail error logs while filtering benign noise (favicon, bots, etc.)
  ngconf create <domain> <port>
                      Generate a reverse proxy config block in sites-available
  ngconf ssl <domain> Request SSL certificates via Certbot Nginx plugin
  ngutil --cleanup    Self-cleanup compliance flag (no-op)

{BOLD}Options:{RESET}
  -h, --help          Show this help message and exit
""")

def run_cmd(cmd_list, capture_output=True, text=True, input_str=None):
    global USE_SUDO
    cmd = cmd_list[:]
    if USE_SUDO:
        cmd = ["sudo"] + cmd
        
    try:
        res = subprocess.run(cmd, capture_output=capture_output, text=text, errors="ignore", input=input_str)
        if res.returncode != 0:
            err = res.stderr.lower() if res.stderr else ""
            if "permission denied" in err or "connect:" in err or "cannot open" in err or "access denied" in err:
                if not USE_SUDO:
                    sys.stdout.write(f"\n{YELLOW}{BOLD}[WARN] Command requires root permissions. Run with sudo? (y/N): {RESET}")
                    sys.stdout.flush()
                    choice = sys.stdin.readline().strip().lower()
                    if choice in ("y", "yes"):
                        USE_SUDO = True
                        cmd = ["sudo"] + cmd_list
                        res = subprocess.run(cmd, capture_output=capture_output, text=text, errors="ignore", input=input_str)
                    else:
                        sys.stderr.write(f"{RED}[ERROR] Permission denied.{RESET}\n")
                        sys.exit(res.returncode)
        return res
    except Exception as e:
        sys.stderr.write(f"{RED}[ERROR] Command execution failed: {e}{RESET}\n")
        sys.exit(1)

def do_stat():
    print(f"{CYAN}Validating Nginx Configuration...{RESET}")
    res_t = run_cmd(["nginx", "-t"])
    if res_t.returncode == 0:
        print(f"{GREEN}[OK] Configuration is valid.{RESET}")
    else:
        print(f"{RED}[ERROR] Configuration validation failed:{RESET}")
        print(res_t.stderr)
        
    print(f"\n{CYAN}Nginx System Status...{RESET}")
    if shutil.which("systemctl"):
        res_s = run_cmd(["systemctl", "status", "nginx"], capture_output=False)
    else:
        res_s = run_cmd(["service", "nginx", "status"], capture_output=False)

def do_err():
    print(f"{CYAN}Tailing Nginx error log (filtering benign noise: favicon, robots, common bots)...{RESET}")
    print(f"{YELLOW}Press Ctrl+C to exit...{RESET}\n")
    
    # Check permissions by trying a dry run tail first
    run_cmd(["tail", "-n", "1", "/var/log/nginx/error.log"])
    
    # Benign noise filter strings (case-insensitive)
    filters = [
        "favicon.ico",
        "robots.txt",
        "ahrefs",
        "semrush",
        "crawler",
        "search-bot",
        "wp-admin",
        "setup.cgi",
        ".php",
    ]
    
    cmd = ["tail", "-f", "/var/log/nginx/error.log"]
    if USE_SUDO:
        cmd = ["sudo"] + cmd
        
    try:
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="ignore")
        while True:
            line = p.stdout.readline()
            if not line:
                break
            
            # Check filter matches
            matched_noise = False
            lower_line = line.lower()
            for f in filters:
                if f in lower_line:
                    matched_noise = True
                    break
                    
            if not matched_noise:
                sys.stdout.write(line)
                sys.stdout.flush()
    except KeyboardInterrupt:
        print(f"\n{GREEN}Tailing stopped.{RESET}")
        p.terminate()

def do_create(domain, port):
    print(f"{CYAN}Generating Nginx Reverse Proxy Config for: {GREEN}{BOLD}{domain} -> Port {port}{RESET}...")
    
    config_template = f"""server {{
    listen 80;
    server_name {domain};

    location / {{
        proxy_pass http://127.0.0.1:{port};
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""

    temp_fd, temp_path = tempfile.mkstemp()
    try:
        with os.fdopen(temp_fd, "w") as f:
            f.write(config_template)
            
        dest_available = f"/etc/nginx/sites-available/{domain}.conf"
        dest_enabled = f"/etc/nginx/sites-enabled/{domain}.conf"
        
        # 1. Copy config block to sites-available
        print(f"Writing Nginx server block to: {dest_available}")
        res_cp = run_cmd(["cp", temp_path, dest_available])
        
        # 2. Link config to sites-enabled
        print(f"Creating symlink in sites-enabled: {dest_enabled}")
        res_ln = run_cmd(["ln", "-sf", dest_available, dest_enabled])
        
        # 3. Validate configuration
        print(f"Testing Nginx configuration...")
        res_test = run_cmd(["nginx", "-t"])
        if res_test.returncode == 0:
            print(f"{GREEN}[OK] Nginx configuration test succeeded.{RESET}")
            # Ask to reload Nginx
            sys.stdout.write(f"\n{CYAN}{BOLD}Reload Nginx to apply changes? (y/N): {RESET}")
            sys.stdout.flush()
            reload_choice = sys.stdin.readline().strip().lower()
            if reload_choice in ("y", "yes"):
                if shutil.which("systemctl"):
                    run_cmd(["systemctl", "reload", "nginx"])
                else:
                    run_cmd(["service", "nginx", "reload"])
                print(f"{GREEN}[SUCCESS] Nginx configuration reloaded successfully.{RESET}")
        else:
            print(f"{RED}[WARN] Nginx configuration test failed. Reverting configuration reload.{RESET}")
            print(res_test.stderr)
            
    finally:
        os.remove(temp_path)

def do_ssl(domain):
    print(f"{CYAN}Setting up SSL for: {GREEN}{BOLD}{domain}{RESET}...")
    
    dest_available = f"/etc/nginx/sites-available/{domain}.conf"
    if not os.path.exists(dest_available):
        # Check standard config directories
        sys.stderr.write(f"{YELLOW}[WARN] Configuration file {dest_available} not found. Proceeding anyway.{RESET}\n")
        
    # Check if certbot is installed
    if not shutil.which("certbot"):
        sys.stderr.write(f"{RED}[ERROR] 'certbot' is not installed.{RESET}\n")
        sys.stderr.write(f"Please install certbot to obtain Let's Encrypt certificates:\n")
        sys.stderr.write(f"  Ubuntu/Debian: sudo apt update && sudo apt install certbot python3-certbot-nginx\n")
        sys.stderr.write(f"  CentOS/RHEL:   sudo dnf install epel-release && sudo dnf install certbot python3-certbot-nginx\n")
        sys.exit(1)
        
    sys.stdout.write(f"Request SSL certificate via certbot --nginx for {domain}? (y/N): ")
    sys.stdout.flush()
    choice = sys.stdin.readline().strip().lower()
    
    if choice not in ("y", "yes"):
        print("SSL setup cancelled.")
        return
        
    print(f"{CYAN}Running certbot to acquire certificates...{RESET}")
    res = run_cmd(["certbot", "--nginx", "-d", domain], capture_output=False)
    if res.returncode == 0:
        print(f"\n{GREEN}[SUCCESS] SSL certificate successfully acquired and configured for {domain}.{RESET}\n")
    else:
        print(f"\n{RED}[ERROR] Certbot failed to configure SSL.{RESET}\n")

def main():
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help"):
        print_help()
        sys.exit(0)
        
    cmd = sys.argv[1]
    
    if cmd == "--cleanup":
        sys.stderr.write(f"{GREEN}[CLEANUP] ngutil requires no cleanup operations.{RESET}\n")
        sys.exit(0)
        
    # Verify Nginx availability first
    if not shutil.which("nginx"):
        sys.stderr.write(f"{RED}[ERROR] 'nginx' executable was not found in PATH.{RESET}\n")
        sys.exit(1)
        
    if cmd == "stat":
        do_stat()
    elif cmd == "err":
        do_err()
    elif cmd == "conf":
        if len(sys.argv) < 3:
            sys.stderr.write(f"{RED}[ERROR] Action required for conf command (create or ssl).{RESET}\n")
            print_help()
            sys.exit(1)
            
        action = sys.argv[2]
        if action == "create":
            if len(sys.argv) < 5:
                sys.stderr.write(f"{RED}[ERROR] Domain and port required. Usage: ngconf create <domain> <port>{RESET}\n")
                sys.exit(1)
            domain = sys.argv[3]
            port = sys.argv[4]
            do_create(domain, port)
        elif action == "ssl":
            if len(sys.argv) < 4:
                sys.stderr.write(f"{RED}[ERROR] Domain required. Usage: ngconf ssl <domain>{RESET}\n")
                sys.exit(1)
            domain = sys.argv[3]
            do_ssl(domain)
        else:
            sys.stderr.write(f"{RED}[ERROR] Unknown conf action: '{action}'{RESET}\n")
            sys.exit(1)
    else:
        sys.stderr.write(f"{RED}[ERROR] Unknown command: '{cmd}'{RESET}\n")
        print_help()
        sys.exit(1)

if __name__ == "__main__":
    main()
