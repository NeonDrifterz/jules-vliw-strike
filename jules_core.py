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
        RECURSIVE+: Create session via direct REST API and approve it.
        Bypasses the CLI to avoid pathing/parsing issues.
        """
        print(f"[JulesCore] Spawning session (REST) for: {mission[:50]}...")
        
        # 1. Create Session via REST API
        payload = {
            "repo": repo,
            "mission": mission
        }
        
        try:
            session_data = self._api_post("sessions", payload)
            # The 'name' field in the response is the session ID (e.g., "sessions/123...")
            # We strip the "sessions/" prefix for internal consistency if needed
            session_full_name = session_data.get("name")
            session_id = session_full_name.split("/")[-1]
            print(f"[JulesCore] Session {session_id} created via REST.")
        except Exception as e:
            raise Exception(f"REST Spawn failed: {e}")

        # 2. Wait for 'Awaiting Approval' state
        # The API is fast, but the backend needs a moment to initialize the plan
        print(f"[JulesCore] Polling for Plan A...")
        time.sleep(15) 
        
        # 3. Approve via API
        print(f"[JulesCore] Approving Plan for {session_id}...")
        try:
            self._api_post(f"sessions/{session_id}:approvePlan")
        except Exception as e:
            # If it fails, maybe it's not ready yet. One retry.
            print(f"[JulesCore] Approval failed, retrying in 10s: {e}")
            time.sleep(10)
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
