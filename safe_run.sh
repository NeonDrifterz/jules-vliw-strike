#!/bin/bash
# safe_run.sh - Failure Forensics & Black Box Recorder
# Usage: ./safe_run.sh "command"

CMD="$1"
TIMESTAMP=$(date +%s)
LOG_DIR="logs"
EXEC_LOG="$LOG_DIR/execution_${TIMESTAMP}.log"

mkdir -p "$LOG_DIR"
echo "[$(date)] Running: $CMD" > "$EXEC_LOG"

# 1. Capture ALL output (stdout + stderr)
eval "$CMD" >> "$EXEC_LOG" 2>&1
EXIT_CODE=$?

# 2. IF FAILED: Snapshot the crime scene
if [ $EXIT_CODE -ne 0 ]; then
    echo "Task Failed (Code $EXIT_CODE). Archiving artifacts..."
    env > "$LOG_DIR/failure_env.txt"
    
    # Archive local state (excluding .git)
    tar -czf "$LOG_DIR/crash_state_${TIMESTAMP}.tar.gz" . --exclude=".git" --max-depth=2 2>/dev/null
    
    # Update Session RAM (CURRENT_STATE.md)
    {
        echo ""
        echo "## FAILURE EVENT - $(date)"
        echo "- **Action:** $CMD"
        echo "- **Result:** Exit Code $EXIT_CODE"
        echo "- **Forensics:** $EXEC_LOG"
        echo "- **Snapshot:** logs/crash_state_${TIMESTAMP}.tar.gz"
    } >> CURRENT_STATE.md
fi

exit $EXIT_CODE
