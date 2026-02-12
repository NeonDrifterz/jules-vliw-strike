#!/bin/bash
# bootstrap_admiral.sh - Initialize Fleet Admiral Environment
# Usage: bash bootstrap_admiral.sh

echo "[BOOTSTRAP] Initializing Admiral V5 (Synapse Enabled)..."

# 1. Install Dependencies
echo "[BOOTSTRAP] Installing Python dependencies..."
if ! python3 -c "import requests" 2>/dev/null; then
    pip3 install requests
fi

# 2. Install REAL Jules CLI (Migration Path)
echo "[BOOTSTRAP] Installing Jules CLI v0.1.42 (Linux AMD64)..."
JULES_URL="https://storage.googleapis.com/jules-cli/v0.1.42/jules_external_v0.1.42_linux_amd64.tar.gz"
curl -sL "$JULES_URL" -o jules.tar.gz
tar -xzf jules.tar.gz
chmod +x jules
export PATH=$PATH:$(pwd)

# 3. Verify Keys
if [ -z "$PENFIELD_API_KEY" ]; then
    echo "[BOOTSTRAP] WARNING: PENFIELD_API_KEY not set."
else
    echo "[BOOTSTRAP] PENFIELD_API_KEY detected. Synapse Link Active."
fi

# 4. Identify Node
if [ -z "$JULES_SESSION_ID" ]; then
    export JULES_SESSION_ID=$(hostname)
    echo "[BOOTSTRAP] Node ID set to: $JULES_SESSION_ID"
fi

# 5. Ensure Executable
chmod +x fleet_admiral.py safe_run.sh stealth_run.sh jules_core.py

# 6. Launch Admiral
echo "[BOOTSTRAP] Launching Fleet Admiral (Unbuffered)..."
python3 -u fleet_admiral.py --keep-alive --penfield-sync

