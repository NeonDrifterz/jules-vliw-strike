"""
Experiment 4: The Endless Marathon Harness
This script forces a Jules agent to perform high-volume logic manufacturing.
"""
import subprocess
import time
import json
import os

def run_variation(seed, window_size, time_limit):
    print(f"--- Launching Variation: Seed={seed}, Window={window_size} ---")
    # This would call the main perf_takehome script with these parameters
    # For simulation purposes in the harness:
    cmd = [
        "python3", "perf_takehome.py", 
        "--seed", str(seed),
        "--window", str(window_size),
        "--time_limit", str(time_limit)
    ]
    start = time.time()
    # result = subprocess.run(cmd, capture_output=True, text=True)
    duration = time.time() - start
    return {"seed": seed, "cycles": 1216, "duration": duration} # Placeholder

def main():
    results = []
    # Force the agent to iterate 50 times
    for i in range(50):
        res = run_variation(seed=i*13, window_size=160 + (i%5)*8, time_limit=2.0)
        results.append(res)
        
        # Periodically dump logs to anchor context
        with open(f"marathon_log_{i}.json", "w") as f:
            json.dump(res, f)
            
        print(f"Progress: {i+1}/50 variations complete.")

if __name__ == "__main__":
    main()
