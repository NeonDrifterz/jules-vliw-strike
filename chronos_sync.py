import time
import requests
import os
import sys
from penfield_link import PenfieldClient

def get_external_time():
    """Fetch UTC seconds from an external source to bypass VM clock freezes."""
    try:
        # Using a reliable, fast API
        res = requests.get("https://worldtimeapi.org/api/timezone/Etc/UTC", timeout=10)
        if res.status_code == 200:
            return res.json().get("unixtime")
    except Exception:
        pass
    return None

def main():
    client = PenfieldClient()
    node_id = os.getenv('JULES_SESSION_ID', 'unknown')
    
    start_internal = time.time()
    start_external = get_external_time()
    
    if not start_external:
        print("[CHRONOS] External time unavailable. Falling back to internal.")
        start_external = start_internal

    print(f"[CHRONOS] Initialized. Node: {node_id}")
    print(f"[CHRONOS] Internal Start: {start_internal}")
    print(f"[CHRONOS] External Start: {start_external}")
    sys.stdout.flush()

    while True:
        time.sleep(60) # Passive wait (will be frozen)
        
        now_internal = time.time()
        now_external = get_external_time() or now_internal
        
        elapsed_internal = now_internal - start_internal
        elapsed_external = now_external - start_external
        
        # Pause Detection
        # If external time moved significantly more than internal time
        pause_delta = elapsed_external - elapsed_internal
        
        status_msg = (
            f"[Node: {node_id}] CHRONOS HEARTBEAT | "
            f"Wall-Clock: {elapsed_external/3600:.2f}h | "
            f"Compute-Clock: {elapsed_internal/3600:.2f}h | "
            f"Total Pause: {pause_delta:.1f}s"
        )
        
        print(status_msg)
        sys.stdout.flush()
        
        # Log to Penfield every 15 mins or if a large pause occurred
        if int(elapsed_internal) % 900 < 60 or pause_delta > 30:
            client.store_memory(status_msg, "fact", tags=["chronos", "heartbeat", node_id])

if __name__ == "__main__":
    main()
