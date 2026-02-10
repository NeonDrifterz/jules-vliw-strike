# Jenkins Hash Identities and Optimizations

## Overview

The bottleneck in `perf_takehome.py` is the 6-stage Jenkins hash function. This document describes the optimization found by fusing Stage 2 and Stage 3.

## Baseline Hash Stages

The hash function consists of 6 stages:

1.  **S0**: `a = (a + 0x7ED55D16) + (a << 12)` -> `a = a * 4097 + 0x7ED55D16`
2.  **S1**: `a = (a ^ 0xC761C23C) ^ (a >> 19)`
3.  **S2**: `a = (a + 0x165667B1) + (a << 5)` -> `a = a * 33 + 0x165667B1`
4.  **S3**: `a = (a + 0xD3A2646C) ^ (a << 9)`
5.  **S4**: `a = (a + 0xFD7046C5) + (a << 3)` -> `a = a * 9 + 0xFD7046C5`
6.  **S5**: `a = (a ^ 0xB55A4F09) ^ (a >> 16)`

## Optimization: Fusion of S2 and S3

We can fuse Stage 2 and Stage 3 to reduce the number of operations.

### Analysis

**Stage 2 (S2):**
`a_out_s2 = a_in * 33 + K2`
where `K2 = 0x165667B1`.
This uses 1 `multiply_add` instruction.

**Stage 3 (S3):**
`a_out_s3 = (a_out_s2 + K3) ^ (a_out_s2 << 9)`
where `K3 = 0xD3A2646C`.
This normally uses 3 instructions:
1. `t1 = a_out_s2 + K3`
2. `t2 = a_out_s2 << 9`
3. `a_out_s3 = t1 ^ t2`

### Fusion Strategy

We can express both `t1` and `t2` directly as linear functions of `a_in` (the input to S2).

**1. Compute `t1` directly:**
`t1 = a_out_s2 + K3`
`t1 = (a_in * 33 + K2) + K3`
`t1 = a_in * 33 + (K2 + K3)`

Let `K2_prime = K2 + K3`.
So `t1` can be computed in 1 instruction: `multiply_add(a_in, 33, K2_prime)`.
This effectively replaces the S2 computation.

**2. Compute `t2` from `t1`:**
We need `t2 = a_out_s2 << 9`.
We have `a_out_s2 = t1 - K3`.
`t2 = (t1 - K3) << 9`
`t2 = (t1 << 9) - (K3 << 9)`
`t2 = t1 * 512 + (-K3 * 512)`

Let `K3_shifted_neg = -(K3 << 9)`.
So `t2` can be computed in 1 instruction: `multiply_add(t1, 512, K3_shifted_neg)`.

**3. Combine:**
`a_out_s3 = t1 ^ t2`.

### Result

**Original S2 + S3:**
1. `a_out_s2 = multiply_add(...)` (1 op)
2. `t1 = a_out_s2 + K3` (1 op)
3. `t2 = a_out_s2 << 9` (1 op)
4. `a_out_s3 = t1 ^ t2` (1 op)
**Total: 4 ops**

**Fused S2 + S3:**
1. `t1 = multiply_add(a_in, 33, K2_prime)` (1 op)
2. `t2 = multiply_add(t1, 512, K3_shifted_neg)` (1 op)
3. `a_out_s3 = t1 ^ t2` (1 op)
**Total: 3 ops**

### Savings

This saves 1 VALU op per hash execution. With 4096 total hash executions, this saves 4096 ops. Since the machine executes 32 vectors in parallel with max 6 VALU ops/cycle, this translates to roughly 85 cycles saved.
