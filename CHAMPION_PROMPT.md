# Mission: VLIW Champion Kernel - Hyper-Optimization Phase

## 🛡️ Phase 1: Context & Bedrock Restore
1. Read `AGENTS.md`. These are your binding operational directives.
2. Read `CURRENT_STATE.md`. This is your session memory.
3. Read `JULES_LONGEVITY.md`. Understand the Token Economics and Circuit Breaker protocols.
4. Read `perf_takehome.py`. This is the production kernel implementation.

## 🧠 Phase 2: Technical Objective & Seed Insight
**Objective**: Optimize the `build_kernel` method to achieve < 1000 cycles for the VLIW take-home challenge.

**The Breakthrough**: A fleet sandbox run achieved **771 cycles** using a **Google OR-Tools CP-SAT Rolling Horizon Scheduler**. 
- **Strategy**: Solve the scheduler in windows (suggested: `window_cycles=80`, `max_windows=2`) using the CP-SAT solver.
- **Goal**: Port this windowed solver into `SemanticScheduler` and optimize the VLIW instruction stream.

## 📏 Phase 3: Generality Constraints
Your solution must be general. **DO NOT** hardcode for specific values. It must pass `do_kernel_test()` for:
- Tree Depths: 8-10
- Rounds: 8-20
- Batch Sizes: 128-256 (e.g., 16-32 vectors)

## 🔄 Phase 4: Operational Loop (SATURATION)
1. Initialize `TASKS.md` in the repo:
   - [ ] Implement Rolling Horizon CP-SAT in `build_kernel`.
   - [ ] Verify Depth 10 / Rounds 16 / Batch 256 benchmark.
   - [ ] Verify generality across all 4 test cases (Depth 8-10).
2. Enter **Worker State**:
   - Pick the top task from `TASKS.md`.
   - Execute using `./safe_run.sh "python3 perf_takehome.py" &`.
   - Immediately return the PID and log path. Do NOT wait for completion.

## 🔋 Phase 5: Longevity & Error Handling
- **Rule of Two**: If a fix fails twice, REVERT. Explain the root cause in `WORKLOG.md` before another attempt.
- **Concurrency**: Use `-j4` for all build/test commands.
- **Persistence**: Save a progress summary to `CURRENT_STATE.md` after every successful task completion.

**AWAKEN AND BEGIN.**
