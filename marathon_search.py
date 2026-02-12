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

def get_external_time():
    """Fetch UTC seconds from an external source."""
    try:
        import requests
        res = requests.get("https://worldtimeapi.org/api/timezone/Etc/UTC", timeout=15)
        if res.status_code == 200:
            return res.json().get("unixtime")
    except Exception:
        pass
    return None

def main():
    client = PenfieldClient()
    
    start_wall = get_external_time() or time.time()
    start_cpu = time.time()
    last_heartbeat = start_cpu
    
    best_cycles = float('inf')
    best_config = {}
    
    node_id = os.getenv('JULES_SESSION_ID', 'unknown')
    print(f"Starting Chronos-Aware Marathon Search...")
    print(f"Node ID: {node_id}")
    print(f"Start Wall-Clock: {start_wall}")
    sys.stdout.flush()
    
    client.store_memory(f"[Node: {node_id}] Chronos Marathon Starting (4h Wall-Clock Duration).", "strategy")
    
    # 4-HOUR WALL-CLOCK LOOP
    while True:
        now_wall = get_external_time() or (start_wall + (time.time() - start_cpu))
        elapsed_wall = now_wall - start_wall
        
        if elapsed_wall >= DURATION_SECONDS:
            break

        now_cpu = time.time()
        # 1. Heartbeat & Pause Detection
        if now_cpu - last_heartbeat > 900:
            pause_duration = elapsed_wall - (now_cpu - start_cpu)
            msg = (
                f"[Node: {node_id}] Marathon Heartbeat | "
                f"Elapsed: {elapsed_wall/3600:.2f}h / 4.0h | "
                f"Pause Tax: {pause_duration:.1f}s"
            )
            client.store_memory(msg, "fact")
            print(msg)
            last_heartbeat = now_cpu
            sys.stdout.flush()

        # 2. Strategy: Focus on legal sweet spot
        if random.random() < 0.8:
            alu_vecs = 0
            n_groups = random.choice([8, 16, 20, 32, 64, 128])
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
