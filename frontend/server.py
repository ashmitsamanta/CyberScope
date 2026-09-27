#!/usr/bin/env python3
"""
CyberScope Local Intelligence Server & NVIDIA NIM API Proxy
Solves browser CORS restrictions by proxying /api/chat to NVIDIA NIM.
"""

import os
import sys
import json
import urllib.request
import urllib.error
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))
NVIDIA_ENDPOINT = "https://integrate.api.nvidia.com/v1/chat/completions"


def load_env():
    """Load environment variables from .env file into os.environ if not set."""
    search_paths = [
        os.path.join(DIRECTORY, "..", ".env"),
        os.path.join(DIRECTORY, ".env"),
        os.path.abspath(".env"),
    ]
    for env_path in search_paths:
        if os.path.isfile(env_path):
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or "=" not in line:
                            continue
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip().strip("'\"")
                        if key and key not in os.environ:
                            os.environ[key] = val
            except Exception:
                pass
            break


load_env()


class CyberScopeHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_POST(self):
        if self.path.startswith("/api/chat") or self.path.startswith("/api/test"):
            content_length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(content_length)

            auth_header = self.headers.get("Authorization")
            if not auth_header or not auth_header.strip():
                api_key = os.environ.get("NVIDIA_API_KEY", "")
                if api_key:
                    auth_header = f"Bearer {api_key}"

            req = urllib.request.Request(
                NVIDIA_ENDPOINT,
                data=body,
                headers={
                    "Authorization": auth_header,
                    "Content-Type": "application/json",
                    "User-Agent": "CyberScope-Proxy/1.0"
                },
                method="POST"
            )

            try:
                with urllib.request.urlopen(req, timeout=30) as response:
                    res_body = response.read()
                    self.send_response(response.status)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(res_body)
            except urllib.error.HTTPError as e:
                err_body = e.read()
                self.send_response(e.code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(err_body)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_server(port=PORT):
    # Try preferred port, or fall back to 8080/8888 if 8000 is occupied
    for p in [port, 8080, 8888, 5000]:
        try:
            server = HTTPServer(("0.0.0.0", p), CyberScopeHandler)
            has_key = bool(os.environ.get("NVIDIA_API_KEY"))
            key_status = "Loaded from .env" if has_key else "NOT SET in .env"
            print(f"==================================================")
            print(f"  CyberScope AI Server & Proxy Active")
            print(f"  URL: http://localhost:{p}/CyberScope.html")
            print(f"  API Proxy: http://localhost:{p}/api/chat")
            print(f"  NVIDIA NIM Key: {key_status}")
            print(f"==================================================")
            server.serve_forever()
            break
        except OSError as e:
            if "Address already in use" in str(e):
                continue
            else:
                raise

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else PORT
    run_server(port)
