#!/usr/bin/env python3
import os
import sys
import re
import subprocess
import argparse

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

class SqlCompleter:
    def __init__(self, keywords, tables):
        self.keywords = keywords
        self.tables = tables
        self.all_words = keywords + tables

    def complete(self, text, state):
        response = None
        if state == 0:
            if text:
                self.matches = [w for w in self.all_words if w.lower().startswith(text.lower())]
            else:
                self.matches = self.all_words[:]
        try:
            response = self.matches[state]
        except IndexError:
            response = None
        return response

def find_env_file(filename=".env", start_dir=None):
    if start_dir is None:
        start_dir = os.getcwd()
    current = os.path.abspath(start_dir)
    while True:
        target = os.path.join(current, filename)
        if os.path.isfile(target):
            return target
        if os.path.isdir(os.path.join(current, ".git")):
            break
        parent = os.path.dirname(current)
        if parent == current:
            break
        current = parent
    return os.path.join(os.getcwd(), filename)

def parse_db_config_from_env(env_filepath):
    config = {}
    if not os.path.exists(env_filepath):
        return config
        
    env_vars = {}
    with open(env_filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = re.match(r"^\s*([A-Za-z0-9_]+)\s*=\s*(.*)$", line)
            if match:
                key = match.group(1)
                val = match.group(2).strip()
                if val.startswith('"') and val.endswith('"'):
                    val = val[1:-1]
                elif val.startswith("'") and val.endswith("'"):
                    val = val[1:-1]
                env_vars[key] = val
                
    # Parse DATABASE_URL
    db_url = env_vars.get("DATABASE_URL")
    if db_url:
        if db_url.startswith("postgres://") or db_url.startswith("postgresql://"):
            config["db_type"] = "postgres"
            m = re.match(r"postgres(?:ql)?://(?:([^:]+):([^@]+)@)?([^:/]+)(?::(\d+))?/([^?]+)", db_url)
            if m:
                config["user"] = m.group(1) or ""
                config["password"] = m.group(2) or ""
                config["host"] = m.group(3) or ""
                config["port"] = int(m.group(4)) if m.group(4) else 5432
                config["dbname"] = m.group(5) or ""
        elif db_url.startswith("mysql://"):
            config["db_type"] = "mysql"
            m = re.match(r"mysql://(?:([^:]+):([^@]+)@)?([^:/]+)(?::(\d+))?/([^?]+)", db_url)
            if m:
                config["user"] = m.group(1) or ""
                config["password"] = m.group(2) or ""
                config["host"] = m.group(3) or ""
                config["port"] = int(m.group(4)) if m.group(4) else 3306
                config["dbname"] = m.group(5) or ""
        elif db_url.startswith("sqlite://"):
            config["db_type"] = "sqlite"
            path = db_url.replace("sqlite:///", "").replace("sqlite://", "")
            config["sqlite_path"] = path

    # Fall back to standalone variables
    if not config.get("db_type"):
        conn_var = env_vars.get("DB_CONNECTION", env_vars.get("DB_TYPE", "")).lower()
        if "post" in conn_var or "pg" in conn_var:
            config["db_type"] = "postgres"
        elif "my" in conn_var:
            config["db_type"] = "mysql"
        elif "sqlite" in conn_var:
            config["db_type"] = "sqlite"
            
    if not config.get("db_type"):
        db_name = env_vars.get("DB_DATABASE", env_vars.get("DB_NAME", ""))
        if db_name.endswith(".db") or db_name.endswith(".sqlite") or db_name.endswith(".sqlite3"):
            config["db_type"] = "sqlite"
            config["sqlite_path"] = db_name
            
    if config.get("db_type") in ("postgres", "mysql"):
        config["host"] = env_vars.get("DB_HOST", config.get("host", "localhost"))
        config["port"] = env_vars.get("DB_PORT", config.get("port", ""))
        if config["port"]:
            config["port"] = int(config["port"])
        else:
            config["port"] = 5432 if config["db_type"] == "postgres" else 3306
            
        config["dbname"] = env_vars.get("DB_DATABASE", env_vars.get("DB_NAME", config.get("dbname", "")))
        config["user"] = env_vars.get("DB_USERNAME", env_vars.get("DB_USER", config.get("user", "")))
        config["password"] = env_vars.get("DB_PASSWORD", env_vars.get("DB_PASS", config.get("password", "")))
        
    elif config.get("db_type") == "sqlite" and not config.get("sqlite_path"):
        config["sqlite_path"] = env_vars.get("DB_DATABASE", env_vars.get("DB_NAME", "database.sqlite"))
        
    return config

def run_query(db_config, sql_query):
    db_type = db_config["db_type"]
    sudo_user = db_config.get("sudo_user")
    
    if db_type == "sqlite":
        try:
            import sqlite3
            conn = sqlite3.connect(db_config["sqlite_path"])
            cursor = conn.cursor()
            cursor.execute(sql_query)
            if cursor.description:
                headers = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
            else:
                conn.commit()
                headers, rows = [], []
            conn.close()
            return headers, rows
        except Exception as e:
            raise RuntimeError(f"SQLite error: {e}")
            
    elif db_type == "postgres":
        cmd = []
        if sudo_user:
            cmd.extend(["sudo", "-u", sudo_user])
        cmd.extend(["psql"])
        if not sudo_user:
            if db_config.get("host"):
                cmd.extend(["-h", db_config["host"]])
            if db_config.get("port"):
                cmd.extend(["-p", str(db_config["port"])])
            if db_config.get("user"):
                cmd.extend(["-U", db_config["user"]])
        if db_config.get("dbname"):
            cmd.extend(["-d", db_config["dbname"]])
        cmd.extend(["-A", "-F", "|", "-c", sql_query])
        
        env = os.environ.copy()
        if db_config.get("password"):
            env["PGPASSWORD"] = db_config["password"]
            
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, env=env, errors="ignore")
            if res.returncode != 0:
                raise RuntimeError(res.stderr.strip())
                
            lines = res.stdout.strip().splitlines()
            if not lines:
                return [], []
                
            headers = lines[0].split("|")
            rows = []
            for line in lines[1:]:
                if line.startswith("(") and line.endswith(")") and ("row" in line or "rows" in line):
                    continue
                rows.append(tuple(line.split("|")))
            return headers, rows
        except Exception as e:
            raise RuntimeError(f"PostgreSQL error: {e}")
            
    elif db_type == "mysql":
        cmd = []
        if sudo_user:
            cmd.extend(["sudo", "-u", sudo_user])
        cmd.extend(["mysql"])
        if not sudo_user:
            if db_config.get("host"):
                cmd.extend(["-h", db_config["host"]])
            if db_config.get("port"):
                cmd.extend(["-P", str(db_config["port"])])
            if db_config.get("user"):
                cmd.extend(["-u", db_config["user"]])
        if db_config.get("dbname"):
            cmd.extend(["-D", db_config["dbname"]])
        cmd.extend(["-B", "-e", sql_query])
        
        env = os.environ.copy()
        if db_config.get("password"):
            env["MYSQL_PWD"] = db_config["password"]
            
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, env=env, errors="ignore")
            if res.returncode != 0:
                raise RuntimeError(res.stderr.strip())
                
            lines = res.stdout.strip().splitlines()
            if not lines:
                return [], []
                
            headers = lines[0].split("\t")
            rows = []
            for line in lines[1:]:
                rows.append(tuple(line.split("\t")))
            return headers, rows
        except Exception as e:
            raise RuntimeError(f"MySQL error: {e}")
            
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

def get_tables(db_config):
    db_type = db_config["db_type"]
    if db_type == "sqlite":
        sql = "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    elif db_type == "postgres":
        sql = "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name;"
    elif db_type == "mysql":
        sql = "SHOW TABLES;"
    else:
        return []
    
    try:
        _, rows = run_query(db_config, sql)
        return [row[0] for row in rows if row]
    except Exception:
        return []

def get_table_schema(db_config, table):
    db_type = db_config["db_type"]
    if db_type == "sqlite":
        headers, rows = run_query(db_config, f"PRAGMA table_info({table});")
        formatted_rows = []
        for r in rows:
            nullable = "YES" if int(r[3]) == 0 else "NO"
            pk = "PRI" if int(r[5]) > 0 else ""
            formatted_rows.append((r[1], r[2], nullable, pk))
        return ["Column", "Type", "Nullable", "Key"], formatted_rows
        
    elif db_type == "postgres":
        sql = f"""
        SELECT column_name, data_type, is_nullable, 
               (SELECT 'PRI' FROM information_schema.table_constraints tc 
                JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_name = '{table}' AND tc.constraint_type = 'PRIMARY KEY' AND kcu.column_name = c.column_name LIMIT 1) as key
        FROM information_schema.columns c
        WHERE table_name = '{table}'
        ORDER BY ordinal_position;
        """
        headers, rows = run_query(db_config, sql)
        formatted_rows = []
        for r in rows:
            pk = r[3] if len(r) > 3 and r[3] else ""
            formatted_rows.append((r[0], r[1], r[2], pk))
        return ["Column", "Type", "Nullable", "Key"], formatted_rows
        
    elif db_type == "mysql":
        headers, rows = run_query(db_config, f"DESCRIBE `{table}`;")
        formatted_rows = []
        for r in rows:
            formatted_rows.append((r[0], r[1], r[2], r[3]))
        return ["Column", "Type", "Nullable", "Key"], formatted_rows

def format_ascii_table(headers, rows, max_col_width=40):
    if not headers:
        return "No headers / empty query response."
        
    str_headers = [str(h) for h in headers]
    str_rows = []
    for r in rows:
        str_rows.append([str(cell) if cell is not None else "NULL" for cell in r])
        
    try:
        term_width = os.get_terminal_size().columns
    except Exception:
        term_width = 80
        
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

def start_interactive_shell(db_config):
    print(f"\n{CYAN}{BOLD}dbcli — Interactive Database Shell{RESET}")
    print(f"Connected to: {GREEN}{db_config['db_type']}{RESET}")
    if db_config["db_type"] == "sqlite":
        print(f"File Path:    {GREEN}{db_config['sqlite_path']}{RESET}")
    else:
        print(f"Database:     {GREEN}{db_config.get('dbname', '')}{RESET}")
        print(f"Host/User:    {GREEN}{db_config.get('host', 'localhost')}:{db_config.get('port', '')} as {db_config.get('user', '')}{RESET}")
        
    print("\nType 'help' for instructions, 'tables' to list tables, or enter SQL directly.")
    print("Press Ctrl+C or type 'exit' to quit.\n")
    
    tables = get_tables(db_config)
    
    # Configure tab autocomplete
    if "readline" in sys.modules:
        keywords = ["SELECT", "FROM", "WHERE", "LIMIT", "ORDER BY", "DESC", "ASC", "tables", "desc", "exit", "quit", "help", "select"]
        completer = SqlCompleter(keywords, tables)
        readline.set_completer(completer.complete)
        readline.parse_and_bind("tab: complete")
        
    while True:
        try:
            prompt = f"dbcli ({db_config['db_type']}) ❯ "
            cmd_line = input(prompt).strip()
            
            if not cmd_line:
                continue
                
            if cmd_line.lower() in ("exit", "quit"):
                break
                
            elif cmd_line.lower() == "help":
                print(f"""
{BOLD}Available Commands:{RESET}
  {GREEN}help{RESET}             Display this guide
  {GREEN}tables{RESET}           List all tables in the database
  {GREEN}desc <table>{RESET}     Show the schema details of a table
  {GREEN}select <table> [where] [limit]{RESET}
                   Quickly select rows from a table.
                   Example: select users status='active' 5
  {GREEN}<sql-statement>{RESET}  Execute raw SQL statement directly
  {GREEN}exit / quit{RESET}      Close this session
""")
                continue
                
            elif cmd_line.lower() == "tables":
                tables = get_tables(db_config)
                if tables:
                    print(f"\n{BOLD}Tables:{RESET}")
                    for t in tables:
                        print(f"  {t}")
                    print(f"({len(tables)} tables total)\n")
                else:
                    print(f"{YELLOW}No tables found.{RESET}")
                continue
                
            elif cmd_line.lower().startswith("desc "):
                parts = cmd_line.split()
                if len(parts) < 2:
                    print(f"{RED}[ERROR] Table name required. E.g. desc users{RESET}")
                    continue
                table = parts[1]
                try:
                    headers, rows = get_table_schema(db_config, table)
                    print(format_ascii_table(headers, rows))
                except Exception as e:
                    print(f"{RED}[ERROR] Failed to get schema: {e}{RESET}")
                continue
                
            elif cmd_line.lower().startswith("select "):
                # Custom quick select parser
                # format: select <table> [where] [limit]
                # E.g. select users id=5 10
                parts = cmd_line.split(maxsplit=3)
                table = parts[1]
                where_clause = ""
                limit_val = 10
                
                # Check remaining args
                if len(parts) > 2:
                    # Let's see if the last part is a number (limit)
                    last_part = parts[-1].strip()
                    if last_part.isdigit():
                        limit_val = int(last_part)
                        if len(parts) == 4:
                            where_clause = parts[2]
                    else:
                        # No trailing limit, join remaining parts as WHERE
                        where_clause = " ".join(parts[2:])
                        
                sql = f"SELECT * FROM {table}"
                if where_clause:
                    sql += f" WHERE {where_clause}"
                sql += f" LIMIT {limit_val};"
                
                print(f"{CYAN}Executing: {sql}{RESET}")
                try:
                    headers, rows = run_query(db_config, sql)
                    print(format_ascii_table(headers, rows))
                except Exception as e:
                    print(f"{RED}[ERROR] Query failed: {e}{RESET}")
                continue
                
            # If it's a raw SQL query
            else:
                # Append semicolon if missing
                if not cmd_line.endswith(";"):
                    cmd_line += ";"
                try:
                    headers, rows = run_query(db_config, cmd_line)
                    if headers:
                        print(format_ascii_table(headers, rows))
                    else:
                        print(f"{GREEN}[SUCCESS] Query executed successfully.{RESET}")
                except Exception as e:
                    print(f"{RED}[ERROR] Query failed: {e}{RESET}")
                    
        except KeyboardInterrupt:
            print("\nUse 'exit' or Ctrl+D to quit.")
        except EOFError:
            print("\nExiting.")
            break

def main():
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        # We manually print custom help to explain arguments
        sys.stderr.write(f"""{CYAN}{BOLD}dbcli — Interactive SSH Database Client{RESET}
Zero-dependency connection utility to Postgres, MySQL, and SQLite.

{BOLD}Usage:{RESET}
  dbcli                        Start interactive explorer (auto-detects .env)
  dbcli query "<sql>"          Execute a raw SQL query directly
  dbcli tables                 List all tables
  dbcli schema <table>         Describe table schema details
  dbcli select <table> [where] Run custom select query
  dbcli --cleanup              Self-cleanup compliance flag (no-op)

{BOLD}Arguments:{RESET}
  -t, --type TYPE              Database type: 'postgres', 'mysql', or 'sqlite'
  -d, --database DBNAME        Database name or SQLite file path
  -H, --host HOST              Connection host address
  -P, --port PORT              Connection port number
  -U, --user USERNAME          Database username
  -p, --password PASSWORD      Database password
  -u, --sudo-user USERNAME     Sudo username to prefix database calls (e.g. postgres)
  --env ENV_FILE               Custom path to .env file
""")
        sys.exit(0)
        
    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        sys.stderr.write(f"{GREEN}[CLEANUP] dbcli requires no cleanup operations.{RESET}\n")
        sys.exit(0)
        
    # Manual argument parse to avoid conflicts with positional commands
    # We parse known arguments manually or using argparse with mixed operands
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-t", "--type")
    parser.add_argument("-d", "--database")
    parser.add_argument("-H", "--host")
    parser.add_argument("-P", "--port", type=int)
    parser.add_argument("-U", "--user")
    parser.add_argument("-p", "--password")
    parser.add_argument("-u", "--sudo-user")
    parser.add_argument("--env")
    
    # Extract only DB arguments and let the rest fall to positional commands
    db_args, remaining_args = parser.parse_known_args()
    
    # Determine which env file to use
    env_file = db_args.env if db_args.env else find_env_file()
    
    # Load configuration from environment
    config = parse_db_config_from_env(env_file)
    
    # Override configuration with CLI arguments if provided
    if db_args.type:
        config["db_type"] = db_args.type
    if db_args.database:
        if config.get("db_type") == "sqlite":
            config["sqlite_path"] = db_args.database
        else:
            config["dbname"] = db_args.database
    if db_args.host:
        config["host"] = db_args.host
    if db_args.port:
        config["port"] = db_args.port
    if db_args.user:
        config["user"] = db_args.user
    if db_args.password:
        config["password"] = db_args.password
    if db_args.sudo_user:
        config["sudo_user"] = db_args.sudo_user
        
    # If type is SQLite but database name was loaded into dbname
    if config.get("db_type") == "sqlite" and not config.get("sqlite_path"):
        config["sqlite_path"] = config.get("dbname", "database.sqlite")
        
    # Validation
    if not config.get("db_type"):
        print(f"{YELLOW}[WARN] Database connection type could not be auto-detected from .env.{RESET}")
        sys.stdout.write("Enter database type (postgres/mysql/sqlite): ")
        sys.stdout.flush()
        config["db_type"] = sys.stdin.readline().strip().lower()
        if not config["db_type"]:
            print(f"{RED}[ERROR] Database type is required.{RESET}")
            sys.exit(1)
            
    if config["db_type"] == "sqlite":
        if not config.get("sqlite_path"):
            sys.stdout.write("Enter SQLite file path [database.sqlite]: ")
            sys.stdout.flush()
            path = sys.stdin.readline().strip()
            config["sqlite_path"] = path if path else "database.sqlite"
    else:
        if not config.get("dbname"):
            sys.stdout.write("Enter database name: ")
            sys.stdout.flush()
            config["dbname"] = sys.stdin.readline().strip()
            
    # Commands logic
    if not remaining_args:
        # Start interactive mode
        start_interactive_shell(config)
        
    else:
        cmd = remaining_args[0]
        
        if cmd == "tables":
            tables = get_tables(config)
            if tables:
                for t in tables:
                    print(t)
            else:
                sys.exit(1)
                
        elif cmd == "schema":
            if len(remaining_args) < 2:
                print(f"{RED}[ERROR] Table name required. E.g. dbcli schema users{RESET}")
                sys.exit(1)
            table = remaining_args[1]
            try:
                headers, rows = get_table_schema(config, table)
                print(format_ascii_table(headers, rows))
            except Exception as e:
                print(f"{RED}[ERROR] {e}{RESET}")
                sys.exit(1)
                
        elif cmd == "query":
            if len(remaining_args) < 2:
                print(f"{RED}[ERROR] SQL query string required. E.g. dbcli query \"SELECT * FROM users;\"{RESET}")
                sys.exit(1)
            sql = remaining_args[1]
            try:
                headers, rows = run_query(config, sql)
                if headers:
                    print(format_ascii_table(headers, rows))
                else:
                    print(f"{GREEN}[SUCCESS] Query executed successfully.{RESET}")
            except Exception as e:
                print(f"{RED}[ERROR] {e}{RESET}")
                sys.exit(1)
                
        elif cmd == "select":
            if len(remaining_args) < 2:
                print(f"{RED}[ERROR] Table name required. E.g. dbcli select users [where] [limit]{RESET}")
                sys.exit(1)
            table = remaining_args[1]
            where = remaining_args[2] if len(remaining_args) > 2 else ""
            limit = 10
            
            # Simple check if last arg is numeric limit
            if len(remaining_args) > 3:
                try:
                    limit = int(remaining_args[3])
                except ValueError:
                    where = f"{where} {remaining_args[3]}"
                    
            sql = f"SELECT * FROM {table}"
            if where:
                sql += f" WHERE {where}"
            sql += f" LIMIT {limit};"
            
            try:
                headers, rows = run_query(config, sql)
                print(format_ascii_table(headers, rows))
            except Exception as e:
                print(f"{RED}[ERROR] {e}{RESET}")
                sys.exit(1)
        else:
            # Fallback to direct query if it looks like sql
            sql_line = " ".join(remaining_args)
            if not sql_line.endswith(";"):
                sql_line += ";"
            try:
                headers, rows = run_query(config, sql_line)
                if headers:
                    print(format_ascii_table(headers, rows))
                else:
                    print(f"{GREEN}[SUCCESS] Query executed.{RESET}")
            except Exception as e:
                print(f"{RED}[ERROR] Unknown command or invalid SQL: {e}{RESET}")
                sys.exit(1)

if __name__ == "__main__":
    main()
