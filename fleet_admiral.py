#!/usr/bin/env python3
import time
import os
import subprocess
import sys
import datetime
import csv
import threading
import hashlib
import argparse

# --- Constants ---
TASK_FILE = "TASK_QUEUE.txt"
STATE_FILE = "CURRENT_STATE.md"
STEALTH_RUN = "./stealth_run.sh"
HEARTBEAT_FILE = ".heartbeat"

# --- No-Sleep Protocol ---
def active_sleep(seconds):
    """
    Simulate activity to prevent hypervisor from freezing the VM.
    Tickles CPU, forces I/O, and flushes stdout.
    """
    target = time.time() + seconds
    while time.time() < target:
        # 1. CPU Tickle: Tiny calculation
        _ = 2**10
        
        # 2. I/O Tickle: Sync filesystem (if on Linux)
        try:
            os.sync()
        except AttributeError:
            pass # os.sync not available on all platforms
            
        # 3. Terminal Tickle: Clear buffer
        sys.stdout.flush()
        
        # 4. Low-latency sleep to avoid 100% CPU throttle
        time.sleep(1)

# --- Modules ---
try:
    from penfield_link import PenfieldClient
except ImportError:
    PenfieldClient = None # Graceful degrade if module not found

try:
    from jules_core import JulesCore
except ImportError:
    JulesCore = None

# --- Logic ---

def load_tasks():
    tasks = []
    if os.path.exists(TASK_FILE):
        with open(TASK_FILE, 'r') as f:
            reader = csv.DictReader(f)
            tasks = list(reader)
    return tasks

def save_tasks(tasks):
    if not tasks: return
    fieldnames = list(tasks[0].keys())
    with open(TASK_FILE, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(tasks)

def update_state(message, penfield=None):
    """
    Update local state and sync with Penfield if connected.
    """
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    role = os.getenv("JULES_ROLE", "Admiral")
    log_msg = f"[{role}] {timestamp} - {message}"
    
    # 1. Console
    print(log_msg)
    
    # 2. Local File
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'a') as f:
                f.write(f"\n{log_msg}\n")
        except Exception as e:
            print(f"Failed to write to state file: {e}")

    # 3. Penfield Sync (The Hive Mind)
    if penfield:
        try:
            # Only sync critical events to save API calls
            if "started" in message.lower() or "finished" in message.lower() or "failed" in message.lower() or "pause" in message.lower() or "spawn" in message.lower():
                penfield.store_memory(
                    content=message,
                    memory_type="fact", 
                    tags=["admiral", "orchestration", role.lower()],
                    importance=0.7
                )
        except Exception as e:
            print(f"[ADMIRAL] Penfield Sync Error: {e}")

def check_process(pid):
    """Check if process is running."""
    try:
        os.kill(int(pid), 0)
        return True
    except OSError:
        return False
    except ValueError:
        return False

def run_task(task, penfield=None):
    cmd = task['Command']
    task_id = task['ID']
    update_state(f"Initiating recursive spawn for {task_id}: {cmd}", penfield)
    
    try:
        # Use JulesCore for Hybrid CLI/API Spawning (Parity+)
        if JulesCore:
            core = JulesCore()
            # Construct mission prompt (Hardened)
            worker_mission = (
                f"MISSION: BENCHMARK RUNNER {task_id}.\n"
                f"1) DO NOT modify the codebase. You are a runner, not a developer.\n"
                f"2) Export PENFIELD_API_KEY='{os.getenv('PENFIELD_API_KEY')}'\n"
                f"3) Run the following command exactly: {cmd}\n"
                f"4) REPORT the final cycle count to Penfield memory using penfield_link.py.\n"
                f"5) Terminate immediately after reporting. DO NOT submit a PR."
            )
            
            session_id = core.spawn(worker_mission)
            
            task['Status'] = 'RUNNING'
            task['PID'] = session_id
            task['LogPath'] = "remote_session"
            
            update_state(f"Recursive Worker Active. Session ID: {session_id}", penfield)
            return task
        else:
            # Fallback to local execution if wrapper missing
            update_state("JulesCore missing. Falling back to local execution.", penfield)
            result = subprocess.run([STEALTH_RUN, cmd], capture_output=True, text=True, check=True)
            task['Status'] = 'RUNNING'
            return task

    except Exception as e:
        update_state(f"Recursive spawn failed for {task_id}: {e}", penfield)
        task['Status'] = 'FAILED'
        return task

def touch_heartbeat(timestamp=None):
    if timestamp is None:
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    with open(HEARTBEAT_FILE, 'w') as f:
        f.write(timestamp)
    return timestamp

def heartbeat_loop(penfield=None):
    """Runs a heartbeat loop to prevent idle timeouts and detect VM pauses."""
    print("[ADMIRAL] Heartbeat thread started.")
    
    while True:
        start_time = time.time()
        
        # 1. Update Heartbeat
        ts_str = touch_heartbeat()
        
        # 2. Simulate CPU Activity
        h = hashlib.sha256(ts_str.encode()).hexdigest()
        
        # 3. Active Wait & Detect VM Pauses
        sleep_duration = 60
        active_sleep(sleep_duration)
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # If elapsed time is significantly greater than sleep_duration + overhead (e.g., > 65s)
        if elapsed > (sleep_duration + 5):
            pause_duration = elapsed - sleep_duration
            msg = f"VM PAUSE DETECTED! System slept for {elapsed:.2f}s (Expected ~{sleep_duration}s). Pause: ~{pause_duration:.2f}s."
            print(f"[HEARTBEAT] {msg}")
            update_state(msg, penfield) # Critical event -> Sync to Penfield
            
            # Immediately touch heartbeat to prevent stale check
            touch_heartbeat()

def monitor_tasks(keep_alive=False, penfield=None):
    if keep_alive:
        t = threading.Thread(target=heartbeat_loop, args=(penfield,), daemon=True)
        t.start()

    while True:
        try:
            tasks = load_tasks()
            if not tasks:
                active_sleep(5)
                continue
            
            active_task_idx = -1
            pending_task_idx = -1
            
            # Find active task (first one running)
            for i, task in enumerate(tasks):
                if task['Status'] == 'RUNNING':
                    active_task_idx = i
                    break
            
            # Find pending task (first one pending)
            if active_task_idx == -1:
                for i, task in enumerate(tasks):
                    if task['Status'] == 'PENDING':
                        pending_task_idx = i
                        break
            
            if active_task_idx != -1:
                # Check status of active task
                task = tasks[active_task_idx]
                pid = task['PID']
                if pid and check_process(pid):
                    # Still running
                    pass
                else:
                    # Process finished
                    update_state(f"Task {task['ID']} finished.", penfield)
                    task['Status'] = 'COMPLETED'
                    save_tasks(tasks)
            
            elif pending_task_idx != -1:
                # Start pending task
                task = tasks[pending_task_idx]
                updated_task = run_task(task, penfield)
                tasks[pending_task_idx] = updated_task
                save_tasks(tasks)
            
            else:
                # No tasks running or pending
                pass
                
        except Exception as e:
            update_state(f"Error in monitoring loop: {e}", penfield)
        
        active_sleep(5) # Poll every 5 seconds using active wait

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Fleet Admiral Orchestrator")
    parser.add_argument("--keep-alive", action="store_true", help="Enable heartbeat to prevent idle timeouts")
    parser.add_argument("--penfield-sync", action="store_true", help="Enable sync with Penfield API (requires PENFIELD_API_KEY)")
    args = parser.parse_args()

    if not os.path.exists(STEALTH_RUN):
        print(f"Error: {STEALTH_RUN} not found.")
        sys.exit(1)

    penfield_client = None
    if args.penfield_sync:
        if PenfieldClient:
            try:
                penfield_client = PenfieldClient()
                print("[ADMIRAL] Connected to Penfield Hive Mind.")
            except ValueError:
                print("[ADMIRAL] Error: PENFIELD_API_KEY not found. Sync disabled.")
        else:
            print("[ADMIRAL] Error: penfield_link module not found. Sync disabled.")
        
    print(f"Fleet Admiral Online. Monitoring tasks... (Keep-Alive: {args.keep_alive}, Penfield Sync: {bool(penfield_client)})")
    monitor_tasks(keep_alive=args.keep_alive, penfield=penfield_client)
