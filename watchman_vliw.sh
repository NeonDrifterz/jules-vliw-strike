#!/bin/bash
# VLIW NIGHT WATCHMAN: Real-Time Logic Harvesting
# Based on Penfield Memory: 7e85ad88-b820-474b-baaf-793cd0c08188

STRIKE_ZONE="/Users/granite/jules_vliw_strike"
LOG_FILE="$STRIKE_ZONE/WATCHMAN_HARVEST.log"

echo "VLIW WATCHMAN ONLINE. Monitoring fleet for NeonDrifterz/jules-vliw-strike..."

while true; do
  TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
  
  # Get all active sessions for this repo
  SESSIONS=$(jules remote list --session --repo NeonDrifterz/jules-vliw-strike)
  
  # Identify IDs (excluding header)
  IDS=$(echo "$SESSIONS" | grep -v "ID" | awk '{print $1}')
  
  for ID in $IDS; do
    echo "[$TIMESTAMP] Harvesting Logic from Agent $ID..." >> $LOG_FILE
    # Pull diff without full apply to avoid local merge mess, 
    # but capture the patch in a vault
    yes | jules remote pull --session $ID >> $LOG_FILE 2>&1
    
    # Also perform a HEAD pull to the main file for 'Real-Time Synthesis'
    # yes | jules remote pull --session $ID --apply >> $LOG_FILE 2>&1
  done
  
  echo "[$TIMESTAMP] Cycle Complete. Logic Vested." >> $LOG_FILE
  sleep 300 # Poll every 5 minutes
done
