#!/usr/bin/env bash
# Sahaay — offline presentation launcher (macOS / Linux)
# Run ONCE while online first (installs Python packages); afterwards works with no internet.
set -e
cd "$(dirname "$0")/backend"

if [ ! -d .venv ]; then
  echo "First run: creating Python environment and installing packages (needs internet once)..."
  python3 -m venv .venv
  ./.venv/bin/pip install -r requirements.txt
fi

./.venv/bin/python seed.py          # loads demo providers into the local database (skips if already there)
echo ""
echo "Sahaay is starting at  http://localhost:8001  (press Ctrl+C to stop)"
( sleep 2; (open http://localhost:8001 || xdg-open http://localhost:8001) >/dev/null 2>&1 ) &
./.venv/bin/python server.py
