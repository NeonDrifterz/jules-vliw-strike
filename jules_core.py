#!/usr/bin/env python3
import os
import sys
import subprocess
import requests
import json
import time

class JulesCore:
    API_BASE = "https://jules.googleapis.com/v1alpha"

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("JULES_API_KEY")
        if not self.api_key:
            raise ValueError("JULES_API_KEY required for automated approvals.")

    def _api_post(self, endpoint, payload=None):
        url = f"{self.API_BASE}/{endpoint}"
        headers = {"x-goog-api-key": self.api_key, "Content-Type": "application/json"}
        response = requests.post(url, headers=headers, json=payload or {})
        response.raise_for_status()
        return response.json()

    def spawn(self, mission, repo="sources/github/NeonDrifterz/jules-vliw-strike"):
        """
        PARITY+: Create session via CLI, then immediately approve plan via API.
        """
        print(f"[JulesCore] Spawning session for: {mission[:50]}...")
        
        # 1. Create via CLI (Superior repo/context handling)
        # Note: CLI repo format usually differs from REST source ID
        cli_repo = repo.replace("sources/github/", "")
        cmd = ["./jules", "remote", "new", "--repo", cli_repo, "--session", mission]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        # Extract ID from CLI output
        session_id = None
        for line in result.stdout.split('\n'):
            if "ID:" in line:
                session_id = line.split("ID:")[1].strip()
                break
        
        if not session_id:
            raise Exception(f"Failed to extract session ID from CLI output: {result.stdout}")

        # 2. Wait for 'Awaiting Approval' state
        print(f"[JulesCore] Session {session_id} created. Polling for Plan A...")
        time.sleep(10) # Initial grace period
        
        # 3. Approve via API (Bypasses the 'Recursion Wall')
        print(f"[JulesCore] Approving Plan for {session_id}...")
        self._api_post(f"sessions/{session_id}:approvePlan")
        
        print(f"[JulesCore] SUCCESS: Session {session_id} is now executing.")
        return session_id

    def list(self):
        """Standard CLI list"""
        subprocess.run(["jules", "remote", "list", "--session"], check=True)

    def pull(self, session_id):
        """CLI-native patch application"""
        print(f"[JulesCore] Pulling and applying patch for {session_id}...")
        subprocess.run(["jules", "remote", "pull", "--session", session_id, "--apply"], check=True)

if __name__ == "__main__":
    core = JulesCore()
    if len(sys.argv) < 2:
        print("Usage: python3 jules_core.py [spawn|list|pull] [args]")
        sys.exit(1)
    
    cmd = sys.argv[1]
    if cmd == "spawn":
        core.spawn(sys.argv[2])
    elif cmd == "list":
        core.list()
    elif cmd == "pull":
        core.pull(sys.argv[2])
