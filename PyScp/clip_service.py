#!/usr/bin/env python3
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

# Add the script directory to sys.path to ensure clip_helper can be imported
script_dir = os.path.dirname(os.path.abspath(__file__))
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

import clip_helper

class ClipboardHTTPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Suppress logging to keep execution silent in the background
        pass

    def do_GET(self):
        if self.path in ("/", "/clip"):
            content = clip_helper.paste()
            content_bytes = content.encode("utf-8", errors="ignore")
            
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(content_bytes)))
            self.end_headers()
            
            self.wfile.write(content_bytes)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

    def do_POST(self):
        if self.path in ("/", "/clip"):
            content_len = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_len)
            text = post_data.decode("utf-8", errors="ignore")
            
            if clip_helper.copy(text):
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"SUCCESS")
            else:
                self.send_response(500)
                self.send_header("Content-Type", "text/plain")
                self.end_headers()
                self.wfile.write(b"ERROR: Failed to write to system clipboard.")
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b"Not Found")

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--cleanup":
        # Terminate any running clipboard service process on uninstallation
        pid_file = os.path.expanduser("~/.config/shell-kit/clip_service.pid")
        if os.path.exists(pid_file):
            try:
                with open(pid_file, "r") as f:
                    pid = int(f.read().strip())
                import signal
                os.kill(pid, signal.SIGTERM)
                sys.stderr.write(f"[CLEANUP] Stopped running clipboard service (PID: {pid}).\n")
            except Exception:
                pass
            try:
                os.remove(pid_file)
            except Exception:
                pass
        sys.exit(0)
        
    host = "127.0.0.1"
    port = 9999
    
    server = HTTPServer((host, port), ClipboardHTTPHandler)
    # Print start marker for automated status checks
    sys.stdout.write(f"Clipboard service listening on http://{host}:{port}\n")
    sys.stdout.flush()
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == "__main__":
    main()
