# Map of Dead Ends (REJECTED_HYPOTHESES)

These paths have been explored and proven mathematically or architecturally impossible. **DO NOT RE-IMPLEMENT.**

## 1. The "Oracle" Path (Precomputation)
- **Hypothesis**: Precalculate the hash for all node/value combinations.
- **Result**: **FORBIDDEN/IMPOSSIBLE**. 
- **Reason**: Violates the "No Oracle" rule in the VALIDITY_CONSTITUTION. Memory limits (1536B scratch) make caching 1M+ combinations impossible.

## 2. Affine Fusion of S4+S5 (XOR/Shift Stages)
- **Hypothesis**: Represent `(x ^ (x >> 16)) + K` as a simple linear operation `Ax + B` over GF(2) or Z2^32.
- **Result**: **FAILED**.
- **Reason**: Shift-right operations are non-linear transformations in these rings. Fusion requires bit-slicing which consumes more VALU slots than the individual ops.

## 3. High-Level Scalar Caching (L0-L6)
- **Hypothesis**: Cache nodes down to Level 6 in scalar scratch registers.
- **Result**: **FAILED**.
- **Reason**: 1,536 bytes of scratch is ~384 words. Level 6 contains 64 nodes. Level 7 contains 128. Caching beyond Level 4 consumes the entire scratch space, leaving zero room for vector indices and values.

## 4. Simple ALU Loop for L4+ Fetch
- **Hypothesis**: Use a scalar loop to load Level 4-10 nodes.
- **Result**: **CYCLE FLOOR HIT (1,216)**.
- **Reason**: The scalar ALU loop is too slow. The engine stalls waiting for `load` results. You MUST use vector-parallel fetching or Flow-engine trees.

## 5. CP-SAT Global Optimization
- **Hypothesis**: Run CP-SAT on the entire 7,000-op program at once.
- **Result**: **TIMEOUT**.
- **Reason**: Complexity is O(2^N). Must use "Windowed Refinement" (e.g., 160-cycle windows).
