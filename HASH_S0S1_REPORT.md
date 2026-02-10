# HASH S0S1 Fusion Report

## Strategy
The primary optimization strategy was "Hash Fusion", specifically targeting the fusion of Stage 2 and Stage 3 (referred to as S0+S1 in the context of pair-wise fusion opportunities). Additionally, scalar ALU operations in the fetch phase (L1/L2 index calculation) were replaced with vector VALU operations to alleviate the ALU bottleneck. Finally, the scheduler parameters were tuned for tighter packing.

## Mathematical Identity
The identity fuses Stage 2 and Stage 3 of the hash function:

**Stage 2:** $y = 33x + K_2$
**Stage 3:** $z = (y + K_3) \oplus (y \ll 9)$

Substituting $y$:
$z = (33x + K_2 + K_3) \oplus ((33x + K_2) \ll 9)$

Using the distributive property of left shift over addition ($A+B \ll k = A \ll k + B \ll k$):
$(33x + K_2) \ll 9 = 33(x \ll 9) + (K_2 \ll 9)$

Since $33 = 1 + 2^5$:
$33(x \ll 9) = (1 + 2^5)(x \ll 9) = (x \ll 9) + (x \ll 14)$
$33(x \ll 9) = x \cdot (2^9 + 2^{14}) = x \cdot 16896$

**Fused Identity:**
$z = (33x + (K_2 + K_3)) \oplus (16896x + (K_2 \ll 9))$

This reduces the operation count from 4 VALU ops (Stage 2: 1, Stage 3: 3) to 3 VALU ops (2 multiply_adds + 1 XOR) and breaks the dependency chain for the second term.

## Implementation Details
1.  **S2+S3 Fusion:**
    - Precomputed fused constants $C_A = K_2 + K_3$, $C_B = 16896$, $C_C = K_2 \ll 9$.
    - Implemented fused logic in `emit_hash` for `hi=2`, skipping `hi=3`.
    - **Register Scavenging:** Reused existing vector constant registers `v_h1[2]`, `v_h3[2]`, `v_h1[3]` to store the fused constants, avoiding new allocations.

2.  **L1/L2 Fetch Optimization:**
    - Replaced scalar ALU loops for calculating `idx - 1` (L1) and `idx - 3` (L2) with single vector VALU subtractions.
    - **Register Scavenging:** Reused `v_h3[0]` (unused by Stage 0) to store the constant `3` needed for L2 fetch optimization, aliased as `v_three`.

3.  **Scheduler Tuning:**
    - Increased `max_windows` to 10 and `window_cycles` to 200 in `_refine_tail_cpsat` to improve instruction packing.

## Results
- **Cycle Count:** 1216 cycles (Goal: < 1220 cycles).
- **Cycle Delta:** -55 cycles (1271 -> 1216).
- **Scratch Usage:** 1386/1536 words.
- **Scratch Delta:** -7 words (1393 -> 1386). (Improved due to removal of scalar constants and temporaries).

## Verification
- Identity verified on 1,000,000 random inputs using `verify_fusion.py`.
- Kernel correctness and cycle count verified using `perf_takehome.py`.
