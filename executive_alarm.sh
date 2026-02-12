#!/bin/bash
# EXECUTIVE ALARM: Breakthrough Monitor
# This script monitors the Night Watchman and alerts the CEO when sub-1200 is reached.

STRIKE_ZONE="/Users/granite/jules_vliw_strike"
LOG_FILE="$STRIKE_ZONE/WATCHMAN_HARVEST.log"

echo "EXECUTIVE ALARM ACTIVE. Go manage other fronts. I will alert you upon breakthrough."

while true; do
  # Search for cycles below 1200 in the harvest log
  BREAKTHROUGH=$(grep -E "NEW BEST [0-9]{3} cycles" $LOG_FILE | grep -vE "12[0-9]{2}" | tail -n 1)
  
  if [ ! -z "$BREAKTHROUGH" ]; then
    echo -e "

\033[1;32m#################################################"
    echo "🚨 BREAKTHROUGH DETECTED: $BREAKTHROUGH"
    echo "#################################################\033[0m
"
    # Optional: terminal bell / alert
    echo -e "\a" 
  fi
  
  sleep 60
done
