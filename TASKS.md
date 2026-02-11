# TASKS.md - VLIW Strike Job Queue

- [ ] [High] [VLIW: VECTOR-0 REPAIR] Debug 'Vector 0 Offload' in `perf_takehome.py`. OBJECTIVE: Bit-perfect match with baseline while maintaining < 1250 cycles. CONSTRAINT: Pass `do_kernel_test()`.
- [ ] [Med] [VLIW: HYPER-SCHEDULER] Tune CP-SAT parameters (window_cycles, max_windows, timeout) to break 1200 cycles.
- [ ] [Med] [VLIW: OPERATOR FUSION] Identify 2-3 instruction sequences for fusion into custom ALUs. TARGET: < 1150 cycles.
- [ ] [Low] Audit `safe_run.sh` logs for performance bottlenecks.
- [ ] [Low] Update `CURRENT_STATE.md` with mission progress.
