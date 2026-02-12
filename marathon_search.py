import time
import random
import subprocess
import sys
import json
import os
from penfield_link import PenfieldClient

# Configuration
DURATION_SECONDS = 4 * 3600  # 4 hours
RESULTS_FILE = "search_results.json"
REPO_DIR = os.getcwd()

def run_iteration(n_groups, offset, alu_vecs):
    """Run one configuration and return cycle count."""
    cmd = [
        "python3", "perf_takehome.py",
        "--n_groups", str(n_groups),
        "--offset", str(offset),
        "--alu_vecs", str(alu_vecs),
        "--seed", "123"
    ]
    try:
        # Unbuffered output to keep hypervisor happy
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode == 0:
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
    last_heartbeat = start_time
    best_cycles = float('inf')
    best_config = {}
    
    node_id = os.getenv('JULES_SESSION_ID', 'unknown')
    print(f"Starting Industrial Marathon Search for {DURATION_SECONDS} seconds...")
    print(f"Node ID: {node_id}")
    sys.stdout.flush()
    
    client.store_memory(f"[Node: {node_id}] Industrial Marathon Search Starting (4h Duration).", "strategy")
    
    # BLOCKING FOREGROUND LOOP
    while time.time() - start_time < DURATION_SECONDS:
        now = time.time()
        # 1. Heartbeat every 15 mins (more frequent to prevent suspension)
        if now - last_heartbeat > 900:
            client.store_memory(f"[Node: {node_id}] Marathon Heartbeat. Uptime: {(now-start_time)/3600:.1f}h", "fact")
            last_heartbeat = now
            print(f"Heartbeat sent. Uptime: {(now-start_time)/3600:.1f}h")
            sys.stdout.flush()

        # 2. Strategy: Focus on legal sweet spot
        if random.random() < 0.8:
            alu_vecs = 0
            n_groups = random.choice([8, 16, 20, 32, 64])
            offset = random.choice([1, 2, 4])
        else:
            alu_vecs = random.choice([2, 4])
            n_groups = random.choice([16, 32])
            offset = random.choice([1, 2])
        
        print(f"Testing: groups={n_groups}, offset={offset}, alu_vecs={alu_vecs}")
        sys.stdout.flush()
        cycles = run_iteration(n_groups, offset, alu_vecs)
        
        if cycles and cycles < best_cycles:
            best_cycles = cycles
            best_config = {"groups": n_groups, "offset": offset, "alu_vecs": alu_vecs}
            print(f"NEW BEST: {best_cycles} cycles with {best_config}")
            sys.stdout.flush()
            msg = f"[Node: {node_id}] NEW BEST: {best_cycles} cycles. Config: {best_config}"
            client.store_memory(msg, "insight", tags=["vliw", "marathon", "best"])

    print(f"Search complete. Final Best: {best_cycles} with {best_config}")
    final_msg = f"[Node: {node_id}] MARATHON COMPLETE. Best Result: {best_cycles} cycles. Config: {json.dumps(best_config)}"
    client.store_memory(final_msg, "fact", tags=["vliw", "marathon", "result"], importance=0.9)
    sys.stdout.flush()

if __name__ == "__main__":
    main()
