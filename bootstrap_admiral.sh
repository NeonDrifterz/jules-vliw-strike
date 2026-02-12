#!/bin/bash
# bootstrap_admiral.sh - Initialize Fleet Admiral Environment
# Usage: bash bootstrap_admiral.sh

echo "[BOOTSTRAP] Initializing Admiral V5 (Synapse Enabled)..."

# 1. Install Dependencies
echo "[BOOTSTRAP] Installing Python dependencies..."
# Ensure we have requests for penfield_link.py
if ! python3 -c "import requests" 2>/dev/null; then
    pip3 install requests
fi

# 2. Verify Key
if [ -z "$PENFIELD_API_KEY" ]; then
    echo "[BOOTSTRAP] WARNING: PENFIELD_API_KEY not set. Hive Mind features will be disabled."
else
    echo "[BOOTSTRAP] PENFIELD_API_KEY detected. Synapse Link Active."
fi

# 3. Identify Node
if [ -z "$JULES_SESSION_ID" ]; then
    export JULES_SESSION_ID=$(hostname)
    echo "[BOOTSTRAP] Node ID set to: $JULES_SESSION_ID"
fi

# 4. Ensure Executable
chmod +x fleet_admiral.py safe_run.sh stealth_run.sh jules

# 4. Launch Admiral
echo "[BOOTSTRAP] Launching Fleet Admiral..."
# Use nohup to detach if running in a shell that might close, 
# but for Jules session we usually want to see the output.
# We run it directly.
python3 fleet_admiral.py --keep-alive --penfield-sync

