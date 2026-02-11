# Mission: VLIW Champion Kernel - Hyper-Optimization Phase

## 🛡️ Phase 1: Context & Bedrock Restore
1. Read `AGENTS.md`. These are your binding operational directives.
2. Read `CURRENT_STATE.md`. This is your session memory.
3. Read `JULES_LONGEVITY.md`. Understand the Token Economics and Circuit Breaker protocols.
4. Read `perf_takehome.py`. This is the production kernel implementation.
5. **Log Start Time**: Open `CHRONOS.md` and add your session start timestamp immediately. You MUST log your duration and results before session end.

## 🧠 Phase 2: Technical Objective & Space Mapping
**Objective**: Map the entire VLIW cycle space and achieve record-breaking counts across multiple tiers (1001 range, 1100 range, etc.).

**The Goal**: Do not just aim for a single "world record" (e.g., 771). Document any configuration that breaks a ceiling (e.g., 1487, 1200, 1100).
- **Strategy**: Tiered verification. If you find a 1050-cycle solution, document it in `WORKLOG.md` before pushing to the 700 range.
- **Doubt**: The 771-cycle CP-SAT result is under investigation for acceptability. Verify it deeply. If it fails, map the highest stable tier.

## 📏 Phase 3: Generality & Rigor
Your solution must be general. **DO NOT** hardcode for specific values. It must pass `do_kernel_test()` across:
- Tree Depths: 8-10
- Rounds: 8-20
- Batch Sizes: 128-256

## 🔄 Phase 4: Operational Loop (SATURATION)
1. Initialize `TASKS.md` with "Tiered Mapping" goals.
2. Commit results to `WORKLOG.md` frequently. **Do not wait for completion to commit logic.** 
3. Execute using `./safe_run.sh "python3 perf_takehome.py" &`.
   - Immediately return the PID and log path. Do NOT wait for completion.

## 🔋 Phase 5: Longevity & Error Handling
- **Rule of Two**: If a fix fails twice, REVERT. Explain the root cause in `WORKLOG.md` before another attempt.
- **Concurrency**: Use `-j4` for all build/test commands.
- **Persistence**: Save a progress summary to `CURRENT_STATE.md` after every successful task completion.

**AWAKEN AND BEGIN.**
