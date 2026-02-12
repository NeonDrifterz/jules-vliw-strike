#!/bin/bash
# run_benchmark.sh - Deterministic worker wrapper
# Usage: bash run_benchmark.sh <TASK_ID> "<COMMAND>"

TASK_ID="$1"
CMD="$2"

echo "[BENCHMARK] Starting Task $TASK_ID..."
echo "[BENCHMARK] Command: $CMD"

# 1. Execute and capture output
# We use script to capture everything including unbuffered prints
OUTPUT_FILE="benchmark_output.txt"
eval "$CMD" > "$OUTPUT_FILE" 2>&1
EXIT_CODE=$?

# 2. Extract Cycle Count
# Look for the line like "✅ 1252 cycles"
CYCLES=$(grep -oE "✅ [0-9]+ cycles" "$OUTPUT_FILE" | awk '{print $2}')

# 3. Report to Penfield
if [ "$EXIT_CODE" -eq 0 ] && [ ! -z "$CYCLES" ]; then
    MSG="[Node: $(hostname)] Task $TASK_ID SUCCESS. Result: $CYCLES cycles."
    python3 penfield_link.py store "$MSG" fact "result,vliw,$TASK_ID"
else
    MSG="[Node: $(hostname)] Task $TASK_ID FAILED. Exit Code: $EXIT_CODE. Check logs."
    python3 penfield_link.py store "$MSG" correction "failure,vliw,$TASK_ID"
fi

echo "[BENCHMARK] Task $TASK_ID Complete. Reported to Hive Mind."
exit $EXIT_CODE
