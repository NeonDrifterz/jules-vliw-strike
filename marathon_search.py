import time
import random
import subprocess
import sys
import json
import os
from penfield_link import PenfieldClient

# Configuration
DURATION_SECONDS = 2 * 3600  # 2 hours
RESULTS_FILE = "search_results.json"
REPO_DIR = os.getcwd()

def run_iteration(n_groups, offset, alu_vecs):
    """Run one configuration and return cycle count."""
    cmd = [
        "python3", "perf_takehome.py",
        "--n_groups", str(n_groups),
        "--offset", str(offset),
        "--alu_vecs", str(alu_vecs),
        "--seed", "123" # Standard validation seed
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode == 0:
            # Extract cycle count from output like "✅ 1248 cycles"
            import re
            match = re.search(r"✅ (\d+) cycles", result.stdout)
            if match:
                return int(match.group(1))
    except Exception as e:
        print(f"Iteration failed: {e}")
    return None

def main():
    client = PenfieldClient()
    start_time = time.time()
    best_cycles = float('inf')
    best_config = {}
    
    print(f"Starting marathon search for {DURATION_SECONDS} seconds...")
    
    while time.time() - start_time < DURATION_SECONDS:
        # Sample parameters
        n_groups = random.choice([8, 10, 16, 20, 32])
        offset = random.choice([1, 2, 4])
        alu_vecs = random.choice([0, 2, 4, 8, 12, 16])
        
        print(f"Testing: groups={n_groups}, offset={offset}, alu_vecs={alu_vecs}")
        
        cycles = run_iteration(n_groups, offset, alu_vecs)
        
        if cycles and cycles < best_cycles:
            best_cycles = cycles
            best_config = {"groups": n_groups, "offset": offset, "alu_vecs": alu_vecs}
            print(f"NEW BEST: {best_cycles} cycles with {best_config}")
            
            # Report progress to Penfield immediately
            msg = f"[Node: {os.getenv('JULES_SESSION_ID', 'unknown')}] NEW BEST: {best_cycles} cycles. Config: {best_config}"
            client.store_memory(msg, "insight", tags=["vliw", "marathon", "best"])

    print(f"Search complete. Final Best: {best_cycles} with {best_config}")
    # Final high-importance report
    final_msg = f"[Node: {os.getenv('JULES_SESSION_ID', 'unknown')}] MARATHON COMPLETE. Best Result: {best_cycles} cycles. Config: {json.dumps(best_config)}"
    client.store_memory(final_msg, "fact", tags=["vliw", "marathon", "result"], importance=0.9)

if __name__ == "__main__":
    main()
