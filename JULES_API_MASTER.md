# Jules API Master Reference (Unified Swarm)

This document is the "Ground Truth" for the Jules Swarm. It defines how nodes should communicate, spawn, and manage each other.

---

## 🛠️ Method 1: The Jules CLI (Hand-Heavy)
The CLI is superior for repository management and context preservation.

**Installation (Headless):**
```bash
curl -sL https://storage.googleapis.com/jules-cli/v0.1.42/jules_external_v0.1.42_linux_amd64.tar.gz -o jules.tar.gz
tar -xzf jules.tar.gz
export PATH=$PATH:$(pwd)
```

**Core Commands:**
- `jules remote list --session`: Monitor the swarm.
- `jules remote pull --session ID --apply`: Ingest sibling work.
- `jules remote new --repo <REPO> "MISSION: ..." `: Spawn child node.

---

## 🌐 Method 2: The REST API (Logic-Heavy)
The API is superior for automated flow control and bypassing manual prompts.

**Base URL:** `https://jules.googleapis.com/v1alpha`
**Auth Header:** `x-goog-api-key: $JULES_API_KEY`

**Core Endpoints:**
- `POST /sessions`: Create a new session.
- `POST /sessions/{id}:approvePlan`: **CRITICAL.** Use this to kick off a node that is stuck in "Awaiting Plan A".
- `GET /sessions`: List all nodes.

---

## 🧩 Method 3: The Synapse Wrapper (Hybrid)
Use `jules_core.py` to get the best of both worlds.

```python
from jules_core import JulesCore
core = JulesCore()
# Spawns AND Approves in one go
session_id = core.spawn("MISSION: Optimize. 1) Derive math. 2) Run script.")
```

---

## 🧠 Collective Memory (Penfield)
Every node MUST identify itself and log progress to Penfield.

**Uplink:**
`python3 penfield_link.py store "Task Finished" fact [role]`

---

## 🚁 Chairlift Ops
If the user provides single-character commands:
- `?` -> Status Report.
- `+` -> Spawn 5 workers.
- `-` -> Stop fleet.
