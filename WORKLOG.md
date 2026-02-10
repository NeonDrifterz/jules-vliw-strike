# Optimization Worklog

## Baseline
- **Date**: 2024-05-23
- **Cycle Count**: 1271 cycles
- **VALU Ops**: 7427 ops
- **Status**: Baseline confirmed.

## Optimization 1: Fuse S2 and S3
- **Description**: Fused Stage 2 and Stage 3 of Jenkins hash.
- **Goal**: Reduce VALU ops by 1 per hash.
- **Expected Cycle Count**: ~1186 cycles.
- **Actual Cycle Count**: 1239 cycles.
- **Status**: Successful. Sub-1250 goal achieved.
