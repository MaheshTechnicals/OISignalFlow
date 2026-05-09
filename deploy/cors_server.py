#!/usr/bin/env python3
"""
OISignalFlow — CORS Config Server
==================================
Serves config.json (written by OISignalFlow.py) over HTTP with
CORS headers so the Netlify-hosted dashboard can fetch it.

Listens on 0.0.0.0:8080 — binds to all interfaces so the
DigitalOcean VM's public IP can reach it.

Run this alongside OISignalFlow.py (both managed by systemd).
"""

import http.server
import os
import logging
import sys

# ── Configuration ───────────────────────────────────────────
PORT      = 8080
HOST      = '0.0.0.0'

# Serve files from the OISignalFlow project root
# deploy/cors_server.py is inside /deploy/, so go one level up
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Allowed origins — '*' means any origin (Netlify, local browser, etc.)
ALLOW_ORIGIN = '*'

# ── Logging ─────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [CORS] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
log = logging.getLogger(__name__)


# ── Request Handler ──────────────────────────────────────────
class CORSHandler(http.server.SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler with CORS + no-cache headers."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PROJECT_ROOT, **kwargs)

    # Inject CORS and cache-control on every response
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin',  ALLOW_ORIGIN)
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Cache-Control')
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma',        'no-cache')
        self.send_header('Expires',       '0')
        super().end_headers()

    # Handle OPTIONS preflight (browsers send this before cross-origin GET)
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    # Only allow GET of config.json — block everything else for security
    def do_GET(self):
        # Normalise path: strip query string
        path = self.path.split('?')[0].rstrip('/')

        if path == '' or path == '/config.json':
            # Allow config.json (and root → serves index.html for local test)
            super().do_GET()
        else:
            # Block all other paths
            self.send_response(403)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'403 Forbidden\n')

    # Silent logging — systemd/journald captures important messages
    def log_message(self, fmt, *args):
        # Only log errors, not every GET request
        if args and str(args[1]) not in ('200', '304'):
            log.warning(fmt % args)


# ── Entry Point ──────────────────────────────────────────────
if __name__ == '__main__':
    log.info(f'Starting CORS server on {HOST}:{PORT}')
    log.info(f'Serving files from: {PROJECT_ROOT}')
    log.info(f'Allowed origin: {ALLOW_ORIGIN}')
    log.info('Waiting for requests...')

    try:
        with http.server.ThreadingHTTPServer((HOST, PORT), CORSHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        log.info('Stopped.')
        sys.exit(0)
    except OSError as e:
        log.error(f'Failed to bind {HOST}:{PORT} — {e}')
        sys.exit(1)
