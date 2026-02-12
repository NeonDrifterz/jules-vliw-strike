#!/usr/bin/env python3
import os
import sys
import time
import argparse
import subprocess
import json
import csv
import datetime
import functools
import traceback

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from penfield_link import PenfieldClient
except ImportError:
    PenfieldClient = None

try:
    from jules_core import JulesCore
except ImportError:
    JulesCore = None

# --- Constants ---
TASK_FILE = "TASK_QUEUE.txt"
STATE_FILE = "CURRENT_STATE.md"
HEARTBEAT_FILE = ".heartbeat"
ADMIRAL_SCRIPT = "fleet_admiral.py"

# --- Utilities ---

def retry(max_attempts=3, delay=2, backoff=2, exceptions=(Exception,)):
    """Decorator for robust retries with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    print(f"[WARN] Attempt {attempts}/{max_attempts} failed: {e}")
                    if attempts == max_attempts:
                        print(f"[ERROR] All {max_attempts} attempts failed.")
                        raise
                    time.sleep(current_delay)
                    current_delay *= backoff
        return wrapper
    return decorator

class Commander:
    def __init__(self):
        self.penfield = self._init_penfield()
        self.core = self._init_core()

    def _init_penfield(self):
        if PenfieldClient:
            try:
                return PenfieldClient()
            except Exception as e:
                print(f"[WARN] Penfield connection failed: {e}")
                return None
        return None

    def _init_core(self):
        if JulesCore:
            try:
                return JulesCore()
            except Exception as e:
                print(f"[WARN] JulesCore initialization failed: {e}")
                return None
        return None

    def status(self):
        """Report system health and status."""
        print("\n=== SWARM STATUS REPORT ===")
        print(f"Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 1. Check Fleet Admiral
        try:
            # Check for python process running fleet_admiral.py
            # pgrep -f might match the editor or this script, so we refine
            res = subprocess.run(["pgrep", "-f", ADMIRAL_SCRIPT], capture_output=True, text=True)
            pids = res.stdout.strip().split('\n')
            pids = [p for p in pids if p] # Filter empty strings

            # Filter out self (commander.py might be running) if it matches regex?
            # Actually pgrep -f "fleet_admiral.py" is specific enough usually.

            if pids:
                print(f"[OK] Fleet Admiral is RUNNING (PID: {', '.join(pids)})")
            else:
                print(f"[ALERT] Fleet Admiral is NOT RUNNING.")
        except Exception as e:
            print(f"[ERROR] Failed to check Admiral process: {e}")

        # 2. Check Heartbeat
        if os.path.exists(HEARTBEAT_FILE):
            try:
                mtime = os.path.getmtime(HEARTBEAT_FILE)
                age = time.time() - mtime
                status = "OK" if age < 120 else "STALE"
                print(f"[{status}] Heartbeat Age: {age:.1f}s")
            except Exception as e:
                print(f"[ERROR] Failed to check heartbeat: {e}")
        else:
            print("[WARN] No heartbeat file found.")

        # 3. Check Task Queue
        if os.path.exists(TASK_FILE):
            try:
                with open(TASK_FILE, 'r') as f:
                    reader = csv.DictReader(f)
                    tasks = list(reader)
                    counts = {'PENDING': 0, 'RUNNING': 0, 'COMPLETED': 0, 'FAILED': 0}
                    for t in tasks:
                        s = t.get('Status', 'UNKNOWN').upper()
                        counts[s] = counts.get(s, 0) + 1

                    print(f"\nTask Queue Summary:")
                    for k, v in counts.items():
                        print(f"  - {k}: {v}")
            except Exception as e:
                print(f"[ERROR] Failed to read Task Queue: {e}")
        else:
            print("[WARN] No Task Queue found.")

        # 4. Penfield Connectivity
        if self.penfield:
            print(f"\n[OK] Penfield Link: Active")
        else:
            print(f"\n[WARN] Penfield Link: Inactive (API Key missing or connection failed)")

        print("===========================\n")

    @retry(max_attempts=3, delay=2)
    def spawn(self, mission, repo="NeonDrifterz/jules-vliw-strike"):
        """Spawn a new worker with retries."""
        if not self.core:
            print("[ERROR] JulesCore not available. Cannot spawn.")
            return

        print(f"Initiating Spawn Sequence for mission: {mission[:50]}...")
        try:
            session_id = self.core.spawn(mission, repo)
            print(f"[SUCCESS] Worker Spawned. Session ID: {session_id}")

            # Log to Penfield if possible
            if self.penfield:
                self.penfield.store_memory(
                    content=f"Commander manually spawned worker {session_id} for mission: {mission}",
                    tags=["commander", "spawn", "manual"],
                    importance=0.8
                )
            return session_id
        except Exception as e:
            print(f"[ERROR] Spawn failed: {e}")
            raise

    def sync_penfield(self, message):
        """Manually push a message to Penfield."""
        if not self.penfield:
            print("[ERROR] Penfield not connected.")
            return

        try:
            res = self.penfield.store_memory(
                content=f"[COMMANDER] {message}",
                tags=["commander", "manual_log"],
                importance=0.5
            )
            print(f"[SUCCESS] Synced to Penfield: {res}")
        except Exception as e:
            print(f"[ERROR] Sync failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="Swarm Commander CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Status
    subparsers.add_parser("status", help="Show swarm health and status")

    # Spawn
    spawn_parser = subparsers.add_parser("spawn", help="Spawn a new worker")
    spawn_parser.add_argument("mission", help="Mission description for the worker")
    spawn_parser.add_argument("--repo", default="NeonDrifterz/jules-vliw-strike", help="Target repository")

    # Sync
    sync_parser = subparsers.add_parser("sync", help="Sync a message to Penfield")
    sync_parser.add_argument("message", help="Message content")

    args = parser.parse_args()

    commander = Commander()

    if args.command == "status":
        commander.status()
    elif args.command == "spawn":
        try:
            commander.spawn(args.mission, args.repo)
        except Exception as e:
            print(f"[FATAL] Failed to spawn worker after retries: {e}")
            sys.exit(1)
    elif args.command == "sync":
        commander.sync_penfield(args.message)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
