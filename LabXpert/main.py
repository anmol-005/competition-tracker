#!/usr/bin/env python3
"""
Simple HTTP server for serving the LapXpert static site.
Run this after building the project with: npm run build

Usage:
    python3 main.py

The server will start on http://localhost:8000
"""

import http.server
import socketserver
import os
from pathlib import Path

PORT = 8000
DIRECTORY = "dist/public"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # Enable CORS for local development
        self.send_header('Access-Control-Allow-Origin', '*')
        super().end_headers()
    
    def do_GET(self):
        # Serve index.html for all routes (SPA routing support)
        if not Path(DIRECTORY + self.path).exists() and not self.path.startswith('/assets'):
            self.path = '/index.html'
        return super().do_GET()

def main():
    # Check if build directory exists
    if not os.path.exists(DIRECTORY):
        print(f"❌ Error: '{DIRECTORY}' directory not found!")
        print("Please build the project first with: npm run build")
        return
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        print(f"✅ LapXpert server running at http://localhost:{PORT}")
        print(f"📁 Serving files from: {DIRECTORY}")
        print("Press Ctrl+C to stop the server")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n👋 Server stopped")

if __name__ == "__main__":
    main()
