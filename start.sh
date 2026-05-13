#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  LeadFlow AI — Quick Start Script
#  Run this any time to start the dashboard
# ─────────────────────────────────────────────────────────────
set -e

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo ""
echo "  🏠 LeadFlow AI — Starting..."
echo ""

# Check venv exists
if [ ! -f ".venv/bin/python" ]; then
  echo "  ⚠️  Virtual environment not found. Running setup..."
  uv venv .venv
  uv pip install --python .venv/bin/python -r requirements.txt
fi

# Check if DB has any data
DB_COUNT=$(.venv/bin/python -c "import sqlite3,os; conn=sqlite3.connect('database/leads.db') if os.path.exists('database/leads.db') else None; print(conn.execute('SELECT COUNT(*) FROM leads').fetchone()[0] if conn else 0)" 2>/dev/null || echo "0")

if [ "$DB_COUNT" = "0" ]; then
  echo "  📊 No leads yet — loading demo data..."
  .venv/bin/python seed_demo.py
fi

echo "  ✅ Starting server on http://localhost:8080"
echo "  📌 Press Ctrl+C to stop"
echo ""

# Open browser after short delay
(sleep 2 && open http://localhost:8080) &

# Start the server
.venv/bin/python app.py
