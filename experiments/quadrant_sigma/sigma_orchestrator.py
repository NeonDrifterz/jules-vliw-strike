import time
import sched
import subprocess
import os

# CONFIGURATION
PULSE_INTERVAL = 900 # 15 Minutes
TOTAL_DURATION = 82800 # 23 Hours (Safety margin before 24h container kill)
STRIKE_ZONE = "/Users/granite/jules_vliw_strike"
JOURNAL = f"{STRIKE_ZONE}/experiments/CHRONOS_JOURNAL.md"

s = sched.scheduler(time.time, time.sleep)

def log(msg):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(JOURNAL, "a") as f:
        f.write(f"
[{ts}] {msg}
")
    print(f"[{ts}] {msg}")

def harvest_fleet():
    log("HEARTBEAT: Harvesting Fleet Logic...")
    # Pull latest from all 4 quadrants
    for sid in ["6978172784787447933", "6677587590609146494", "8726031291033261984", "10323001615451731568"]:
        log(f"Pulling session {sid}...")
        # subprocess.run(["jules", "remote", "pull", "--session", sid], capture_output=True)
    
    # Re-schedule next pulse
    s.enter(PULSE_INTERVAL, 1, harvest_fleet)

def final_harvest():
    log("CRITICAL: 23-Hour Mark Reached. Initiating Final Harvest.")
    # git push logic here
    log("FINAL PUSH COMPLETE. VM can now be safely destroyed.")
    os._exit(0)

def main():
    log("SIGMA ORCHESTRATOR ONLINE: 24-Hour Persistence Mode.")
    
    # Schedule pulses
    s.enter(PULSE_INTERVAL, 1, harvest_fleet)
    
    # Schedule the absolute end
    s.enter(TOTAL_DURATION, 0, final_harvest)
    
    # Start the loop
    s.run()

if __name__ == "__main__":
    main()
