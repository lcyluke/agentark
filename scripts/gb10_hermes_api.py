#!/usr/bin/env python3
"""
GB10 Hermes API Bridge — HTTP → Hermes Agent
═══════════════════════════════════════════════
Tiny HTTP wrapper that lets Macs call GB10 Hermes via REST API.

Usage on GB10:
  python3 gb10_hermes_api.py --port 8989

Usage on Mac:
  curl http://gb10:8989/chat -d '{"message":"写一个快排"}'
"""

import json
import subprocess
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

HERMES_BIN = "/home/pm02/.local/bin/hermes"
TIMEOUT = 300  # 5 min max for 70B models


class HermesHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path == "/chat":
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length))
            message = body.get("message", "")
            model = body.get("model", "")
            
            cmd = [HERMES_BIN, "chat", "-q", message, "--quiet"]
            if model:
                cmd.extend(["-m", model])
            
            try:
                r = subprocess.run(cmd, capture_output=True, text=True, 
                                   timeout=TIMEOUT)
                # Extract only the response (skip session_id etc.)
                output = r.stdout.strip().split("\n")[-1] if r.stdout else r.stderr
                self._json({"ok": r.returncode == 0, "response": output[:5000]})
            except subprocess.TimeoutExpired:
                self._json({"ok": False, "error": "timeout"}, 504)
            except Exception as e:
                self._json({"ok": False, "error": str(e)}, 500)
        elif self.path == "/health":
            self._json({"ok": True, "model": "qwen2.5:32b"})
        else:
            self._json({"ok": False, "error": "not found"}, 404)

    def _json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # Silent


if __name__ == "__main__":
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 8989
    server = HTTPServer(("0.0.0.0", port), HermesHandler)
    print(f"🚀 GB10 Hermes API on port {port}")
    server.serve_forever()
