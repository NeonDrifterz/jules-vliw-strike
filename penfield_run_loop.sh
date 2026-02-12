#!/bin/bash
# Penfield Run Loop (formerly stealth_run.sh)
# Purpose: Bidirectional Memory Sync for Jules Agents
# Usage: ./penfield_run_loop.sh "My Task Description"

API_URL="https://api.penfield.app/api/v2"
API_KEY="${PENFIELD_API_KEY}" # Must be set in env

if [ -z "$API_KEY" ]; then
    echo "Error: PENFIELD_API_KEY not set."
    exit 1
fi

# 1. AUTHENTICATE (Get JWT)
echo "[Synapse] Authenticating..."
JWT=$(curl -s -X POST "$API_URL/auth/token" 
  -H "Authorization: Bearer $API_KEY" 
  -H "Content-Type: application/json" | jq -r '.data.access_token')

if [ "$JWT" == "null" ]; then
    echo "Error: Authentication failed."
    exit 1
fi

# 2. READ (Recall relevant memories)
TASK_QUERY="$1"
echo "[Synapse] Recalling context for: $TASK_QUERY"
CONTEXT=$(curl -s -X POST "$API_URL/search" 
  -H "Authorization: Bearer $JWT" 
  -H "Content-Type: application/json" 
  -d "{"query": "$TASK_QUERY", "limit": 3, "source_type": "memory"}" | jq -r '.data.items[].content')

echo "---------------------------------------------------"
echo "EXTRACTED MEMORY:"
echo "$CONTEXT"
echo "---------------------------------------------------"

# 3. COMPUTE (Execute the actual workload)
# In a real run, this would invoke the solver. For now, we simulate.
echo "[Soma] Executing task with augmented context..."
# RESULT=$(python3 optimize.py) # Placeholder

# 4. WRITE (Store the result back to Penfield)
# echo "[Axon] Storing result..."
# curl -X POST "$API_URL/memories" ...
