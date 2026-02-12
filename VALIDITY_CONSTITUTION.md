# Jules Fleet Validity Constitution: VLIW Strike Zone

To ensure "Verified Reality," every logic strike must adhere to the following validity rules. Any optimization that violates these is considered "Hollow Success" and will be rejected.

---

## 🚫 Forbidden "Cheat" Categories
1. **Full Answer Precomputation (The Oracle Path)**: 
   - *Rule*: You cannot pre-calculate the final output values during `build_mem_image`. 
   - *Reason*: This bypasses the actual VLIW computation. The kernel must perform the traversal.
2. **Lossy State Truncation (The 12-bit LUT Path)**:
   - *Rule*: You cannot truncate the 32-bit hash state to a smaller bit-width if it results in bit-imperfect outputs.
   - *Exception*: You MAY use lossy LUTs as "prefetch hints" ONLY if the actual hash is still computed and verified for bit-perfection.
3. **Parameter-Specific Hardcoding**:
   - *Rule*: Optimizations must work for the defined parameter ranges (Tree height 8-10, Rounds 8-20, Batch 128-256). Hardcoding for a single seed or tree instance is prohibited.

---

## ✅ Allowed Optimization Categories
1. **Instruction Fusion**: Collapsing hash stages into fewer VALU ops using mathematical identities.
2. **Engine Offloading**: Moving non-critical path logic (like direction extraction) from VALU to ALU or FLOW.
3. **Software Pipelining**: Interleaving groups to hide Load/Store latency.
4. **Register Scavenging**: Reusing scratch space to enable deeper prefetching or fusion.
5. **Valid Structural Precomputation**: Pre-loading static tree nodes or structure into scratch memory (already proven valid in L0-L3 preloading).

---

## 🕵️ The Auditor's Mandate
Jules must verify bit-perfection using `tests/submission_tests.py` before completion. Every `WORKLOG.md` must include a statement: *"This optimization is bit-perfect and does not utilize forbidden precomputation."*
