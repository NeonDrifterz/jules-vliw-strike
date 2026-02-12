# Swarm Tools

This directory contains the tooling for managing the Jules VLIW Swarm. The primary entry point is the `swarm` command (a wrapper around `commander.py`) located in the root of the repository.

## Usage

Run the `swarm` command from the root of the repository.

### Check Status

Reports the health of the Fleet Admiral, the state of the Task Queue, and Penfield connectivity.

```bash
./swarm status
```

### Spawn a Worker

Spawns a new worker agent with a specific mission. This uses `JulesCore` to safely create a remote session and approve the plan.

```bash
./swarm spawn "MISSION: Optimize the VLIW kernel for reduced latency."
```

Optional arguments:
- `--repo`: Specify a different repository (default: `NeonDrifterz/jules-vliw-strike`).

### Sync to Penfield

Manually log a message to the Penfield Hive Mind.

```bash
./swarm sync "Manual checkpoint: Kernel optimization phase complete."
```

## Architecture

- **`commander.py`**: The core logic for the CLI. It includes:
  - **Robust Error Handling**: Retries for network operations and process checks.
  - **Penfield Integration**: Direct link to the Hive Mind for status updates.
  - **Process Monitoring**: Checks for the existence of `fleet_admiral.py` and the freshness of the heartbeat.

## Troubleshooting

- If `swarm` fails to run, ensure you have execution permissions: `chmod +x swarm`.
- If Penfield sync fails, verify `PENFIELD_API_KEY` is set in your environment.
- If spawning fails, ensure `jules` CLI is installed and configured.
