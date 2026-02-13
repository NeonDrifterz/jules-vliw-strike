import time
import os
import datetime
import subprocess
import sys
import argparse

# PERSISTENCE PROTOCOL ALPHA: FOREGROUND ENTRAPMENT
# 1. No backgrounding (&) allowed.
# 2. No early submission.
# 3. Active I/O and CPU tickling.

parser = argparse.ArgumentParser()
parser.add_argument("--interval", type=int, default=60, help="Heartbeat interval in seconds")
args = parser.parse_args()

DURATION_HOURS = 4.0
START_TIME = datetime.datetime.utcnow()
END_TIME = START_TIME + datetime.timedelta(hours=DURATION_HOURS)

def log(msg):
    now = datetime.datetime.utcnow().isoformat()
    print(f"[{now}] [INDUSTRIAL_GUARD] {msg}")
    sys.stdout.flush()
    with open("MISSION_LOG.md", "a") as f:
        f.write(f"[{now}] {msg}\n")

def tickle_system():
    # CPU Tickle: Simple math
    _ = [x**2 for x in range(1000)]
    # I/O Tickle: Sync and Disk check
    subprocess.run(["sync"], check=True)
    subprocess.run(["df", "-h", "/"], capture_output=True)

log(f"MISSION INITIALIZED: 4-Hour Foreground Siege (Interval: {args.interval}s).")
log(f"Target End Time (UTC): {END_TIME.isoformat()}")

try:
    while datetime.datetime.utcnow() < END_TIME:
        current_time = datetime.datetime.utcnow()
        elapsed = (current_time - START_TIME).total_seconds() / 3600
        remaining = (END_TIME - current_time).total_seconds() / 3600
        
        log(f"STATUS: In Progress. Elapsed: {elapsed:.2f}h | Remaining: {remaining:.2f}h")
        
        # Perform system tickle
        tickle_system()
        
        # Stay in the foreground.
        time.sleep(args.interval)

    log("MISSION COMPLETE: 4-Hour Persistence Mark Reached.")
    log("SAFE TO CONCLUDE.")

except Exception as e:
    log(f"CRITICAL FAILURE: {str(e)}")
    sys.exit(1)
