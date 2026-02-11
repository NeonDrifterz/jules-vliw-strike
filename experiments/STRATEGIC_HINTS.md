# Strategic Hints (THE SUB-1200 BREACH)

These tactics are proven to shave cycles by rebalancing engine utilization.

## 1. VALU -> ALU Offloading (The Shift Kill)
- **Target**: VALU Slots (6/cycle) are 99% busy. ALU Slots (12/cycle) are ~80% busy.
- **Tactic**: Move Stage 1 (`>> 19`) and Stage 5 (`>> 16`) shifts to the Scalar ALU.
- **Logic**: Use a 8-iteration scalar loop per vector to prepare shifted operands in scalar registers, then broadcast back or XOR directly.

## 2. Flow-Engine Level 4 Trees
- **Target**: Remove the `load` bottleneck for Level 4 (16 nodes).
- **Tactic**: Cache Level 4 nodes (16 words) and use a nested `vselect` tree on the **Flow Engine**.
- **Logic**: 15 `vselect` ops on Flow (1 slot/cycle) hide the latency that would otherwise stall the ALU/VALU during scalar loads.

## 3. S2+S3 Fusion Identity
- **Identity**: `(33x + (K2+K3)) ^ (16896x + (K2<<9))`.
- **Result**: Kills 1 VALU op per hash.
- **Status**: Implemented in 1,216 baseline, but check for "Register Scavenging" opportunities to reduce pressure.

## 4. "Work-Ahead" Fetching (idx+4)
- **Target**: Hide memory latency.
- **Tactic**: Fetch node values for the NEXT group of vectors while calculating the hash for the CURRENT group.
- **Logic**: Interleave the Fetch(Group B) with Hash(Group A).
