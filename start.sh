#!/bin/bash
# Portfolio Dashboard — one command to run everything
# Usage: ./start.sh

cd "$(dirname "$0")"

# Kill any previous dashboard still running on port 4444
lsof -ti:4444 | xargs kill -9 2>/dev/null

# Build index.html from src/
echo "Building index.html..."
python3 build.py

# Start dashboard
echo ""
echo "Dashboard:  http://localhost:4444"
echo "Portfolio:  open index.html in browser"
echo "Admin:      open admin.html in browser (or yoursite.vercel.app/admin.html)"
echo ""
python3 dashboard.py
