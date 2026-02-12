#!/bin/bash
# bootstrap_admiral.sh
echo "[BOOTSTRAP] Admiral initiation started."

# 1. Ensure local environment is ready
# (Jules sessions usually come with common tools, but let's be safe)

# 2. Synchronize logic
echo "[BOOTSTRAP] Pulling latest orchestrator logic..."
git pull origin master

# 3. Launch the Fleet Admiral loop in the foreground
# This keeps the Jules session ALIVE as long as the script runs.
echo "[BOOTSTRAP] Launching Fleet Admiral loop..."
# Use -u for unbuffered output so we can see logs in the UI
python3 -u /Users/granite/jules/fleet_admiral.py
