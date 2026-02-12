#!/bin/bash
# pwm_run.sh - PWM CPU Throttler for Jules Swarm
# Usage: ./pwm_run.sh <pid_or_command> [duty_cycle_on_sec] [duty_cycle_off_sec]

ON_SEC=${2:-45}
OFF_SEC=${3:-15}

if [[ $1 =~ ^[0-9]+$ ]]; then
    TARGET_PID=$1
else
    # Launch command in background
    "$@" &
    TARGET_PID=$!
    echo "[PWM] Launched command with PID: $TARGET_PID"
fi

trap "kill $TARGET_PID 2>/dev/null; exit" SIGINT SIGTERM

echo "[PWM] Throttling PID $TARGET_PID (On: ${ON_SEC}s, Off: ${OFF_SEC}s)"

while kill -0 $TARGET_PID 2>/dev/null; do
    # ON cycle
    kill -CONT $TARGET_PID 2>/dev/null
    sleep $ON_SEC
    
    # OFF cycle
    if kill -0 $TARGET_PID 2>/dev/null; then
        kill -STOP $TARGET_PID 2>/dev/null
        sleep $OFF_SEC
    fi
done

echo "[PWM] Target process $TARGET_PID exited."
