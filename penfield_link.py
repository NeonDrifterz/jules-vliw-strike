import os
import sys
import json
import time
import requests

class PenfieldClient:
    BASE_URL = "https://api.penfield.app/api/v2"

    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("PENFIELD_API_KEY")
        if not self.api_key:
            raise ValueError("Penfield API Key is required. Set PENFIELD_API_KEY env var.")
        self.jwt_token = None
        self.token_expiry = 0

    def _get_headers(self):
        if not self.jwt_token or time.time() > self.token_expiry:
            self._authenticate()
        return {
            "Authorization": f"Bearer {self.jwt_token}",
            "Content-Type": "application/json"
        }

    def _authenticate(self):
        """Exchange API Key for JWT Token"""
        url = f"{self.BASE_URL}/auth/token"
        try:
            # According to docs: POST /auth/token with Bearer API_KEY
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            data = response.json().get("data", {})
            self.jwt_token = data.get("access_token")
            expires_in = data.get("expires_in", 3600)
            self.token_expiry = time.time() + expires_in - 60 # Buffer
            # print(f"[Penfield] Authenticated. Token expires in {expires_in}s.")
        except Exception as e:
            print(f"[Penfield] Authentication Failed: {e}")
            raise

    def store_memory(self, content, memory_type="fact", tags=None, importance=0.5):
        """Store a memory in Penfield."""
        url = f"{self.BASE_URL}/memories"
        payload = {
            "content": content,
            "memory_type": memory_type,
            "tags": tags or [],
            "importance": importance
        }
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[Penfield] Store Memory Failed: {e}")
            return None

    def search_memories(self, query, limit=5, source_type="memory"):
        """Search memories in Penfield."""
        url = f"{self.BASE_URL}/search/hybrid"
        payload = {
            "query": query,
            "limit": limit,
            "source_type": source_type
        }
        try:
            response = requests.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"[Penfield] Search Failed: {e}")
            return None

    def save_context_checkpoint(self, state_content, tags=None):
        """Save a 'checkpoint' memory for handoff."""
        return self.store_memory(
            content=f"CHECKPOINT: {state_content}",
            memory_type="insight", # Or strategy/fact
            tags=["checkpoint", "handoff"] + (tags or []),
            importance=1.0
        )

# CLI Wrapper for easy use in shell scripts
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 penfield_link.py <command> [args]")
        print("Commands: store <content> [type] [tag1,tag2], search <query>")
        sys.exit(1)

    cmd = sys.argv[1]
    client = None
    try:
        client = PenfieldClient()
    except ValueError:
        print("Error: PENFIELD_API_KEY not set.")
        sys.exit(1)

    if cmd == "store":
        content = sys.argv[2]
        m_type = sys.argv[3] if len(sys.argv) > 3 else "fact"
        tags = sys.argv[4].split(",") if len(sys.argv) > 4 else []
        res = client.store_memory(content, m_type, tags)
        print(json.dumps(res, indent=2))
    elif cmd == "search":
        query = sys.argv[2]
        res = client.search_memories(query)
        print(json.dumps(res, indent=2))
    else:
        print(f"Unknown command: {cmd}")
