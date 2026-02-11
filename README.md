# Project: VLIW Strike (NeonDrifterz)

## 🎯 Purpose
This repository is a high-performance compute environment dedicated to the hyper-optimization of VLIW (Very Long Instruction Word) compute kernels. The primary objective is to achieve bit-perfect execution with the absolute minimum clock-cycle makespan for DAG-based hashing and search algorithms.

## 🧱 The Safety Scaffold
This project uses a mandatory operational framework to manage agent "Amnesia" and "Context Drift":

1.  **AGENTS.md**: The Project Constitution. Contains your binding operational directives.
2.  **CURRENT_STATE.md**: The Session RAM. Read this to understand the current task status and last known-good state.
3.  **TASKS.md**: The Job Queue. Decouples planning from execution. Work the list.
4.  **safe_run.sh**: The Black-Box Recorder. All performance-critical tests must run through this wrapper to archive failure forensics.

## 🛠️ Performance Architecture
- **Hardware**: VLIW Scalar/Vector ALU (4-8 lanes).
- **Target**: Sub-100 cycle / Sub-1000 cycle world records.
- **Constraints**: 4 vCPUs per agent. Use `-j4` for all build and verification tasks.

---
*Refer to [AGENTS.md](file:///Users/granite/jules_vliw_strike/AGENTS.md) for execution rules.*
