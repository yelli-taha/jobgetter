#!/bin/bash
# JobGetter dashboard (Mac). Double-click to start; keep this window open while you use it.
cd "$(dirname "$0")"
echo "Starting the JobGetter dashboard. Keep this window open while you use it."
(sleep 2; open http://localhost:5050) &
.venv/bin/python app.py
