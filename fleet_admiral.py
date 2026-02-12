import subprocess
import time
import os
import re

# Configuration
TASK_QUEUE = "/Users/granite/jules/icarus-experiment/TASK_QUEUE.txt"
APPROVER_SCRIPT = "/Users/granite/jules/icarus-experiment/jules_approver.sh"
POLL_INTERVAL = 300  # 5 minutes
MAX_WORKERS = 3

def run_cmd(cmd):
    try:
        print(f"[ADMIRAL] Executing: {cmd}")
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[ADMIRAL] Command failed: {result.stderr.strip()}")
        return result.stdout.strip()
    except Exception as e:
        print(f"[ADMIRAL] Exception during command: {str(e)}")
        return f"Error: {str(e)}"

def get_active_sessions():
    output = run_cmd("jules remote list --session")
    # Parse the mission descriptions to see which tasks are already active
    return output

def parse_queue():
    tasks = []
    if not os.path.exists(TASK_QUEUE):
        return tasks
    with open(TASK_QUEUE, "r") as f:
        for line in f:
            if line.strip():
                # Parse format: branch:name mission:text
                match = re.search(r"branch:(\S+) mission:(.+)", line)
                if match:
                    tasks.append({"branch": match.group(1), "mission": match.group(2).strip()})
    return tasks

def main():
    # Setup internal logging
    log_file = open("admiral_execution.log", "a", buffering=1)
    import sys
    sys.stdout = log_file
    sys.stderr = log_file
    
    print(f"\n[ADMIRAL] --- Fleet Admiral Wake Sequence: {time.strftime('%Y-%m-%d %H:%M:%S')} ---")
    
    # Environment Check
    jules_check = run_cmd("which jules")
    if not jules_check:
        print("[ADMIRAL] WARNING: 'jules' command not found in PATH.")
    else:
        print(f"[ADMIRAL] 'jules' found at: {jules_check}")

    while True:
        print(f"\n[ADMIRAL] Starting orchestration cycle: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 0. Sync logic and queue
        print("[ADMIRAL] Syncing with remote repository...")
        run_cmd("git pull origin master")
        
        # 1. Run Approver
        print("[ADMIRAL] Running plan approval cycle...")
        run_cmd(f"bash {APPROVER_SCRIPT}")
        
        # 2. Check current status
        active_output = get_active_sessions()
        queue = parse_queue()
        
        # Count currently active/completed workers from the queue
        running_count = 0
        unassigned_tasks = []
        
        for task in queue:
            # Check if this specific branch+mission is already running on the TARGET REPO
            # We look for the branch name and the repo name in the same block of the listing
            # Using a regex to find the task in the list output specifically for the correct repo
            task_pattern = fr"\[VLIW SWARM: {task['branch']}\].+NeonDrifterz/jules-vliw-strike"
            if re.search(task_pattern, active_output):
                running_count += 1
            else:
                unassigned_tasks.append(task)
        
        print(f"[ADMIRAL] Active Swarm Count (jules-vliw-strike): {running_count}/{MAX_WORKERS}", flush=True)
        
        # 3. Launch new workers if slots available
        while running_count < MAX_WORKERS and unassigned_tasks:
            task = unassigned_tasks.pop(0)
            branch = task["branch"]
            mission = task["mission"]
            
            launch_mission = f"[VLIW SWARM: {branch}] MISSION: {mission}"
            print(f"[ADMIRAL] Launching worker for branch: {branch}")
            
            # Note: We append the branch name to the mission to track it in listings
            launch_cmd = f"jules remote new --repo NeonDrifterz/jules-vliw-strike --session \"{launch_mission}\""
            run_cmd(launch_cmd)
            
            running_count += 1
            time.sleep(10) # Avoid rate limits
            
        print(f"[ADMIRAL] Orchestration cycle complete. Sleeping for {POLL_INTERVAL}s...")
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    # Ensure all prints are flushed for real-time logging
    import functools
    print = functools.partial(print, flush=True)
    main()
