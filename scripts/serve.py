#!/usr/bin/env python3
"""Preview server that refuses to be cached.

The browser's memory cache made three verification passes report stale CSS as
if it were the current build, which cost more time than the bugs did. Every
response here says no-store, so what you measure is what is on disk.

    python3 scripts/serve.py [port]
"""
import functools, http.server, socketserver, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765


class NoStore(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    handler = functools.partial(NoStore, directory=str(ROOT))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", PORT), handler) as httpd:
        print(f"serving {ROOT} at http://127.0.0.1:{PORT} (no-store)")
        httpd.serve_forever()
