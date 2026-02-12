# Jules REST API Reference (v1alpha)

This document provides the technical grounding for autonomous agents to manage Jules sessions without the binary CLI.

## Base URL
`https://jules.googleapis.com/v1alpha`

## Authentication
All requests require the following header:
`x-goog-api-key: <JULES_API_KEY>`

---

## 1. Create a New Session
**Endpoint:** `POST /sessions`
**Payload:**
```json
{
  "repo": "NeonDrifterz/jules-vliw-strike",
  "mission": "MISSION: [Task Name]. 1) [Instructions] 2) [Command]"
}
```
*Note: The exact JSON schema may vary; use the `jules` CLI output as a reference for field names.*

## 2. List All Sessions
**Endpoint:** `GET /sessions`
**Example Response:**
```json
{
  "sessions": [
    {
      "name": "sessions/8418192054172552451",
      "status": "AWAITING_APPROVAL",
      "description": "..."
    }
  ]
}
```

## 3. Approve a Plan
**Endpoint:** `POST /sessions/{id}:approvePlan`
*Note: Requires `Content-Length: 0` if sending an empty body.*

## 4. Delete/Recycle a Session
**Endpoint:** `DELETE /sessions/{id}`

---

## Autonomous Spawning Strategy (Synapse V2)
To spawn a worker node programmatically:
1. `POST /sessions` with the mission details.
2. Poll `GET /sessions` until the new ID appears with `status == "AWAITING_APPROVAL"`.
3. `POST /sessions/{id}:approvePlan` to begin execution.
