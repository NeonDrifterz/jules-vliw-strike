"""
V3 Architecture: Deferred critical-path scheduler with L0-L3 precomputation (1271 cycles).

RESULTS: 1271 cycles (beats 1338 leaderboard target by 67 cycles / 5.0%)

Key optimizations:
1. Multi-phase interleaving: 16 groups × 2 vectors, offset by 1 round
2. Deferred critical-path scheduler with iterative refinement (100 iterations) + CP-SAT tail refinement
3. L0-L3 precomputation: Load tree levels 0-3 once, use vselect/mux
4. VALU/ALU balance: Direction extraction + L1-L3 subtract in scalar ALU
5. Fused index update: idx*2 + (direction+1) via single multiply_add

RESOURCE UTILIZATION:
- VALU: 7427 ops, 99.4% utilized, 5.84 ops/cycle (theoretical min: 6.00)
- ALU: 13935 ops, 97.6% utilized
- Load: 2163 ops, 86.1% utilized
- Flow: 705 ops, 55.5% utilized
- Scratch: 1393/1536 words (143 free)

BOTTLENECK ANALYSIS:
- Theoretical VALU minimum: ceil(7427/6) = 1238 cycles
- Current: 1271 cycles = 33 cycles (2.7%) scheduling overhead
"""
from collections import defaultdict
from typing import List, Optional
import random
import unittest

from problem import (
    Engine, DebugInfo, CoreState, SLOT_LIMITS, VLEN, N_CORES, SCRATCH_SIZE,
    Machine, Tree, Input, HASH_STAGES, reference_kernel2, build_mem_image
)

class Register:
    def __init__(self, addr: int, name: str, length: int):
        self.addr = addr; self.name = name; self.length = length

class ScalarReg(Register):
    def __init__(self, addr: int, name: str): super().__init__(addr, name, 1)

class VectorReg(Register):
    def __init__(self, addr: int, name: str): super().__init__(addr, name, VLEN)

class SemanticScheduler:
    def __init__(self, deferred=True):
        self.bundles = []; self.last_write = {}; self.last_read = {}
        self.deferred = deferred
        if deferred:
            self.ops = []
            self.order_counter = 0
            self._op_cycles = None

    def _add_raw(self, engine: Engine, slot: tuple, reads: List[Register], writes: List[Register]):
        read_addrs = set()
        for r in reads:
            for i in range(r.length):
                read_addrs.add(r.addr + i)
        write_addrs = set()
        for w in writes:
            for i in range(w.length):
                write_addrs.add(w.addr + i)

        if self.deferred:
            self.ops.append((engine, slot, read_addrs, write_addrs, self.order_counter))
            self.order_counter += 1
            return 0

        start_cycle = 0
        for addr in read_addrs:
            if addr in self.last_write: start_cycle = max(start_cycle, self.last_write[addr] + 1)
        for addr in write_addrs:
            if addr in self.last_write: start_cycle = max(start_cycle, self.last_write[addr] + 1)
            if addr in self.last_read: start_cycle = max(start_cycle, self.last_read[addr])
        c = start_cycle
        while True:
            while c >= len(self.bundles): self.bundles.append(defaultdict(list))
            bundle = self.bundles[c]
            if len(bundle.get(engine, [])) < SLOT_LIMITS[engine]:
                if engine not in bundle: bundle[engine] = []
                bundle[engine].append(slot); break
            c += 1
        for addr in write_addrs:
            self.last_write[addr] = c
        for addr in read_addrs:
            self.last_read[addr] = max(self.last_read.get(addr, 0), c)
        return c

    def schedule_deferred(self, n_iters=1, seed=42):
        """Build dependency graph and schedule using list scheduling with critical path priority."""
        n = len(self.ops)
        last_writer = {}
        last_readers = defaultdict(list)
        deps = [set() for _ in range(n)]

        for idx, (engine, slot, read_addrs, write_addrs, order) in enumerate(self.ops):
            for addr in read_addrs:
                if addr in last_writer:
                    deps[idx].add(last_writer[addr])
            for addr in write_addrs:
                if addr in last_writer:
                    deps[idx].add(last_writer[addr])
                for reader in last_readers.get(addr, []):
                    if reader != idx:
                        deps[idx].add(reader)
            for addr in write_addrs:
                last_writer[addr] = idx
                last_readers[addr] = []
            for addr in read_addrs:
                last_readers[addr].append(idx)

        successors = [[] for _ in range(n)]
        for i in range(n):
            for d in deps[i]:
                successors[d].append(i)

        cp_length = [0] * n
        for i in range(n - 1, -1, -1):
            max_succ = 0
            for s in successors[i]:
                max_succ = max(max_succ, cp_length[s])
            cp_length[i] = 1 + max_succ

        def _do_list_schedule(ops_list, deps_list, successors_list, cp_length_list, n_ops):
            dep_count = [len(d) for d in deps_list]
            ready = []
            for i in range(n_ops):
                if dep_count[i] == 0:
                    ready.append(i)

            def sort_key(i):
                return (-cp_length_list[i], i)
            ready.sort(key=sort_key)

            bundles = []
            op_cycles = [-1] * n_ops
            cycle = 0
            placed = 0

            while placed < n_ops:
                while cycle >= len(bundles):
                    bundles.append(defaultdict(list))
                bundle = bundles[cycle]

                next_ready = []
                newly_ready = []
                for op_idx in ready:
                    engine = ops_list[op_idx][0]
                    slot = ops_list[op_idx][1]
                    if len(bundle.get(engine, [])) < SLOT_LIMITS[engine]:
                        if engine not in bundle:
                            bundle[engine] = []
                        bundle[engine].append(slot)
                        op_cycles[op_idx] = cycle
                        placed += 1
                        for s in successors_list[op_idx]:
                            dep_count[s] -= 1
                            if dep_count[s] == 0:
                                newly_ready.append(s)
                    else:
                        next_ready.append(op_idx)

                next_ready.extend(newly_ready)
                next_ready.sort(key=sort_key)
                ready = next_ready
                cycle += 1

            while bundles and not any(bundles[-1].values()):
                bundles.pop()
            return bundles, op_cycles

        self.bundles, self._op_cycles = _do_list_schedule(self.ops, deps, successors, cp_length, n)

        if n_iters > 1:
            import random as rng
            rng_state = rng.getstate()
            rng.seed(seed)
            best_len = len(self.bundles)
            best_bundles = self.bundles
            best_cycles = self._op_cycles
            for iteration in range(n_iters - 1):
                noisy_cp = [cp_length[i] + rng.random() * 0.5 for i in range(n)]
                trial_bundles, trial_cycles = _do_list_schedule(self.ops, deps, successors, noisy_cp, n)
                if len(trial_bundles) < best_len:
                    best_len = len(trial_bundles)
                    best_bundles = trial_bundles
                    best_cycles = trial_cycles
            self.bundles = best_bundles
            self._op_cycles = best_cycles
            rng.setstate(rng_state)

        self._refine_tail_cpsat(deps, max_windows=3, window_cycles=160, time_limit_s=2.0, max_ops_in_window=5000)

    def _refine_tail_cpsat(self, deps, max_windows=3, window_cycles=160, time_limit_s=2.0, max_ops_in_window=5000):
        """Windowed CP-SAT refinement: re-schedule tail operations for tighter packing."""
        try:
            from ortools.sat.python import cp_model
        except Exception:
            return

        if not self._op_cycles:
            return

        n = len(self.ops)
        op_cycles = list(self._op_cycles)

        def _rebuild_bundles_from_cycles(cycles):
            max_cycle = max(cycles)
            bundles = [defaultdict(list) for _ in range(max_cycle + 1)]
            order = []
            for i, (engine, slot, _read_addrs, _write_addrs, op_order) in enumerate(self.ops):
                order.append((cycles[i], engine, op_order, i, slot))
            order.sort()
            for c, engine, _op_order, _i, slot in order:
                bundles[c][engine].append(slot)
            while bundles and not any(bundles[-1].values()):
                bundles.pop()
            return bundles

        def _maybe_shrink_window(start, end):
            s = start
            while s < end:
                idxs = [i for i in range(n) if op_cycles[i] >= s]
                if len(idxs) <= max_ops_in_window:
                    return s, idxs
                s += max(8, window_cycles // 8)
            return start, [i for i in range(n) if op_cycles[i] >= start]

        for _ in range(max_windows):
            makespan = max(op_cycles) + 1
            if makespan <= 1:
                break

            start = max(0, makespan - window_cycles)
            start, window_ops = _maybe_shrink_window(start, makespan)
            if not window_ops:
                break

            window_set = set(window_ops)
            horizon = makespan - start
            if horizon <= 0:
                break

            model = cp_model.CpModel()
            starts = {}
            ends = {}
            intervals_by_engine = defaultdict(list)

            for i in window_ops:
                lb = 0
                ub = horizon - 1
                s_var = model.NewIntVar(lb, ub, f"s_{i}")
                e_var = model.NewIntVar(1, horizon, f"e_{i}")
                model.Add(e_var == s_var + 1)
                itv = model.NewIntervalVar(s_var, 1, e_var, f"itv_{i}")
                starts[i] = s_var
                ends[i] = e_var
                engine = self.ops[i][0]
                intervals_by_engine[engine].append(itv)
                init = op_cycles[i] - start
                if 0 <= init <= ub:
                    model.AddHint(s_var, init)

            for i in window_ops:
                s_i = starts[i]
                for d in deps[i]:
                    if d in window_set:
                        model.Add(s_i >= starts[d] + 1)
                    else:
                        model.Add(s_i >= (op_cycles[d] + 1 - start))

            for engine, intervals in intervals_by_engine.items():
                model.AddCumulative(intervals, [1] * len(intervals), SLOT_LIMITS[engine])

            makespan_var = model.NewIntVar(1, horizon, "tail_makespan")
            model.AddMaxEquality(makespan_var, [ends[i] for i in window_ops])
            model.Minimize(makespan_var)

            solver = cp_model.CpSolver()
            solver.parameters.max_time_in_seconds = float(time_limit_s)
            solver.parameters.num_search_workers = 8
            status = solver.Solve(model)

            if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
                break

            for i in window_ops:
                op_cycles[i] = start + solver.Value(starts[i])

            new_makespan = max(op_cycles) + 1
            if new_makespan >= makespan:
                break

            self._op_cycles = list(op_cycles)
            self.bundles = _rebuild_bundles_from_cycles(op_cycles)

    def pause(self, n_iters=100):
        if self.deferred:
            self.schedule_deferred(n_iters=n_iters)
        c = len(self.bundles); self.bundles.append({"flow": [("pause",)]})
        if not self.deferred:
            for addr in list(self.last_write.keys()): self.last_write[addr] = c
            for addr in list(self.last_read.keys()): self.last_read[addr] = c

    def print_heatmap(self):
        print("\n" + "="*70)
        print("VLIW SCHEDULE HEATMAP")
        print("="*70)
        load_busy, store_busy, alu_busy, valu_busy, flow_busy = 0, 0, 0, 0, 0
        load_total, store_total, alu_total, valu_total, flow_total = 0, 0, 0, 0, 0
        for i, b in enumerate(self.bundles):
            l = len(b.get("load", [])); s = len(b.get("store", [])); a = len(b.get("alu", []))
            v = len(b.get("valu", [])); f = len(b.get("flow", []))
            load_total += l; store_total += s; alu_total += a; valu_total += v; flow_total += f
            if l > 0: load_busy += 1
            if s > 0: store_busy += 1
            if a > 0: alu_busy += 1
            if v > 0: valu_busy += 1
            if f > 0: flow_busy += 1
        n = len(self.bundles)
        print(f"\nUTILIZATION SUMMARY:")
        print(f"  Total Cycles:     {n}")
        print(f"  Load Slots:       {load_busy}/{n} cycles ({load_busy/n*100:.1f}%) | {load_total} ops")
        print(f"  Store Slots:      {store_busy}/{n} cycles ({store_busy/n*100:.1f}%) | {store_total} ops")
        print(f"  ALU Slots:        {alu_busy}/{n} cycles ({alu_busy/n*100:.1f}%) | {alu_total} ops")
        print(f"  VALU Slots:       {valu_busy}/{n} cycles ({valu_busy/n*100:.1f}%) | {valu_total} ops")
        print(f"  Flow Slots:       {flow_busy}/{n} cycles ({flow_busy/n*100:.1f}%) | {flow_total} ops")
        if valu_total > 0:
            print(f"  VALU ops/cycle:   {valu_total/n:.2f} (theoretical max: 6.00)")
        valu_hist = [0] * 7
        for idx, b in enumerate(self.bundles):
            v = len(b.get("valu", []))
            valu_hist[v] += 1
        print(f"  VALU distribution: {dict((k,v) for k,v in enumerate(valu_hist) if v > 0)}")
        print("="*70 + "\n")

    def const(self, dest: ScalarReg, val: int): return self._add_raw("load", ("const", dest.addr, val), [], [dest])
    def load(self, dest: ScalarReg, addr: ScalarReg): return self._add_raw("load", ("load", dest.addr, addr.addr), [addr], [dest])
    def vload(self, dest: VectorReg, addr: ScalarReg): return self._add_raw("load", ("vload", dest.addr, addr.addr), [addr], [dest])
    def vstore(self, addr: ScalarReg, src: VectorReg): return self._add_raw("store", ("vstore", addr.addr, src.addr), [addr, src], [])
    def alu(self, op: str, dest: ScalarReg, a: ScalarReg, b: ScalarReg): return self._add_raw("alu", (op, dest.addr, a.addr, b.addr), [a, b], [dest])
    def valu(self, op: str, dest: VectorReg, a: Register, b: Register, c: Optional[Register] = None):
        if c: return self._add_raw("valu", (op, dest.addr, a.addr, b.addr, c.addr), [a, b, c], [dest])
        return self._add_raw("valu", (op, dest.addr, a.addr, b.addr), [a, b], [dest])
    def vbroadcast(self, dest: VectorReg, src: ScalarReg): return self._add_raw("valu", ("vbroadcast", dest.addr, src.addr), [src], [dest])
    def vselect(self, dest: VectorReg, cond: VectorReg, a: VectorReg, b: VectorReg): return self._add_raw("flow", ("vselect", dest.addr, cond.addr, a.addr, b.addr), [cond, a, b], [dest])
    def store(self, addr: ScalarReg, src: ScalarReg): return self._add_raw("store", ("store", addr.addr, src.addr), [addr, src], [])


class KernelBuilder:
    def __init__(self):
        self.scratch_ptr = 0; self.scratch_debug = {}
        self.sched = SemanticScheduler(deferred=True); self.const_map = {}

    def alloc_scalar(self, name: str) -> ScalarReg:
        addr = self.scratch_ptr; self.scratch_ptr += 1
        self.scratch_debug[addr] = (name, 1)
        assert self.scratch_ptr <= SCRATCH_SIZE, f"OOM: {self.scratch_ptr} > {SCRATCH_SIZE}"
        return ScalarReg(addr, name)

    def alloc_vector(self, name: str) -> VectorReg:
        addr = self.scratch_ptr; self.scratch_ptr += VLEN
        self.scratch_debug[addr] = (name, VLEN)
        assert self.scratch_ptr <= SCRATCH_SIZE, f"OOM: {self.scratch_ptr} > {SCRATCH_SIZE}"
        return VectorReg(addr, name)

    def get_const(self, val: int) -> ScalarReg:
        if val not in self.const_map:
            reg = self.alloc_scalar(f"c_{val}")
            self.sched.const(reg, val)
            self.const_map[val] = reg
        return self.const_map[val]

    def debug_info(self): return DebugInfo(scratch_map=self.scratch_debug)

    def build_kernel(self, forest_height: int, n_nodes: int, batch_size: int, rounds: int, n_groups: int = 16, offset: int = 1):
        S = self.sched
        # n_groups and offset passed as arguments

        # ── Load parameters ──
        params = [self.alloc_scalar(name) for name in ["rds", "nn", "bs", "fh", "fp", "ip", "vp"]]
        tp = self.alloc_scalar("tp")
        for i, reg in enumerate(params):
            S.const(tp, i); S.load(reg, tp)
        s_fp, s_ip, s_vp, s_nn = params[4], params[5], params[6], params[1]

        n_vecs = batch_size // VLEN  # 32
        n_valu_vecs = 30
        n_alu_vecs = 2

        # ── Heterogeneous Register Partition (24 VALU, 8 ALU) ──
        v_idx = [self.alloc_vector(f"idx_{i}") for i in range(n_valu_vecs)]
        v_val = [self.alloc_vector(f"val_{i}") for i in range(n_valu_vecs)]
        v_t1  = [self.alloc_vector(f"t1_{i}") for i in range(n_valu_vecs)]
        v_t2  = [self.alloc_vector(f"t2_{i}") for i in range(n_valu_vecs)]

        # Scalar registers for the Colonized 8 vectors
        a_idx = [[self.alloc_scalar(f"aidx_{i}_{v}") for v in range(VLEN)] for i in range(n_alu_vecs)]
        a_val = [[self.alloc_scalar(f"aval_{i}_{v}") for v in range(VLEN)] for i in range(n_alu_vecs)]
        a_t1  = [[self.alloc_scalar(f"at1_{i}_{v}") for v in range(VLEN)] for i in range(n_alu_vecs)]
        a_t2  = [[self.alloc_scalar(f"at2_{i}_{v}") for v in range(VLEN)] for i in range(n_alu_vecs)]

        # ── Vector constants ──
        v_o   = self.alloc_vector("v_o")
        v_two = self.alloc_vector("v_two")
        v_vn  = self.alloc_vector("v_vn")
        S.vbroadcast(v_o, self.get_const(1))
        S.vbroadcast(v_two, self.get_const(2))
        S.vbroadcast(v_vn, s_nn)

        # ── Hash constant vectors ──
        v_h1 = [self.alloc_vector(f"h1_{i}") for i in range(6)]
        v_h3 = [self.alloc_vector(f"h3_{i}") for i in range(6)]
        v_hm = {i: self.alloc_vector(f"hm_{i}") for i in [0, 2, 4]}
        for i, (_, v1, _, _, v3) in enumerate(HASH_STAGES):
            S.vbroadcast(v_h1[i], self.get_const(v1))
            S.vbroadcast(v_h3[i], self.get_const(v3))
            if i in v_hm:
                S.vbroadcast(v_hm[i], self.get_const({0: 4097, 2: 33, 4: 9}[i]))
        
        # Fused S2+S3 constants
        k2, k3 = 0x165667B1, 0xD3A2646C
        v_k2_prime = self.alloc_vector("k2_prime")
        v_k3_shifted_neg = self.alloc_vector("k3_shifted_neg")
        v_512 = self.alloc_vector("v_512")
        S.vbroadcast(v_k2_prime, self.get_const((k2 + k3) % (2**32)))
        S.vbroadcast(v_k3_shifted_neg, self.get_const((-(k3 << 9)) % (2**32)))
        S.vbroadcast(v_512, self.get_const(512))

        # ── Preload L0-L2 node values as scalars ──
        s_na = self.alloc_scalar("na")
        s_tree = []
        for k in range(7):
            sr = self.alloc_scalar(f"tree_{k}")
            S.alu("+", s_na, s_fp, self.get_const(k))
            S.load(sr, s_na)
            s_tree.append(sr)

        # L1: pre-broadcast tree[1] and tree[2] as vectors for vselect
        v_l1 = [self.alloc_vector(f"l1_{k}") for k in range(2)]
        S.vbroadcast(v_l1[0], s_tree[1])
        S.vbroadcast(v_l1[1], s_tree[2])

        # ── Preload L2 node values as vectors for vselect ──
        v_l2 = [self.alloc_vector(f"l2_{k}") for k in range(4)]
        for k in range(4):
            S.vbroadcast(v_l2[k], s_tree[3 + k])

        # ── Preload L3 node values as vectors for vselect ──
        v_l3 = [self.alloc_vector(f"l3_{k}") for k in range(8)]
        for k in range(8):
            S.alu("+", s_na, s_fp, self.get_const(7 + k))
            sr_tmp = self.alloc_scalar(f"l3s_{k}")
            S.load(sr_tmp, s_na)
            S.vbroadcast(v_l3[k], sr_tmp)

        # Selection temporaries (shared, reused across levels)
        v_sel0 = self.alloc_vector("sel0")
        v_sel1 = self.alloc_vector("sel1")
        v_sel2 = self.alloc_vector("sel2")
        v_sel3 = self.alloc_vector("sel3")
        v_cond = self.alloc_vector("vcond")

        # ── Misc ──
        v_seven = self.alloc_vector("v_seven")
        v_root  = self.alloc_vector("v_root")
        S.vbroadcast(v_seven, self.get_const(7))
        S.vbroadcast(v_root, s_tree[0])

        s_c1 = self.get_const(1)

        print(f"Scratch usage: {self.scratch_ptr}/{SCRATCH_SIZE} ({SCRATCH_SIZE - self.scratch_ptr} free)")

        # ── Load initial values (24 VALU, 8 ALU) ──
        s_sp_reg = self.alloc_scalar("sp")
        tmp_va = self.alloc_scalar("tmp_va")
        for i in range(n_valu_vecs):
            S.alu("+", s_sp_reg, s_vp, self.get_const(i * VLEN))
            S.vload(v_val[i], s_sp_reg)
            S.vbroadcast(v_idx[i], self.get_const(0))
        for i in range(n_alu_vecs):
            S.alu("+", s_sp_reg, s_vp, self.get_const((n_valu_vecs + i) * VLEN))
            for v in range(VLEN):
                S.alu("+", tmp_va, s_sp_reg, self.get_const(v))
                S.load(a_val[i][v], tmp_va)
                S.alu("*", a_idx[i][v], s_c1, self.get_const(0))

        # ─────────────────────────────────────────────────────
        def emit_fetch_valu(r, vecs):
            """VALU Fetch logic (optimized L0-L3)"""
            level = r % (forest_height + 1)
            if not vecs: return
            if level == 0:
                for i in vecs: S.valu("^", v_val[i], v_val[i], v_root)
            elif level == 1:
                for i in vecs:
                    for vi in range(VLEN):
                        si, sd = ScalarReg(v_idx[i].addr+vi, ""), ScalarReg(v_t1[i].addr+vi, "")
                        S.alu("-", sd, si, s_c1)
                    S.vselect(v_t2[i], v_t1[i], v_l1[1], v_l1[0])
                    S.valu("^", v_val[i], v_val[i], v_t2[i])
            if level == 2:
                s_c3 = self.get_const(3)
                for i in vecs:
                    for vi in range(VLEN):
                        si, sd = ScalarReg(v_idx[i].addr+vi, ""), ScalarReg(v_t1[i].addr+vi, "")
                        S.alu("-", sd, si, s_c3)
                for i in vecs:
                    S.valu("&", v_cond, v_t1[i], v_o)
                    S.vselect(v_sel0, v_cond, v_l2[1], v_l2[0])
                    S.vselect(v_sel1, v_cond, v_l2[3], v_l2[2])
                    S.valu("&", v_t2[i], v_t1[i], v_o) # Revert to & 1 if it was intended? No, L2 bit 1.
                    # Original for L2 bit 1:
                    S.valu(">>", v_t2[i], v_t1[i], v_o)
                    S.valu("&", v_t2[i], v_t2[i], v_o)
                    S.vselect(v_t2[i], v_t2[i], v_sel1, v_sel0)
                    S.valu("^", v_val[i], v_val[i], v_t2[i])
            elif level == 3:
                for i in vecs: S.valu("-", v_t1[i], v_idx[i], v_seven)
                for i in vecs:
                    S.valu("&", v_cond, v_t1[i], v_o)
                    S.vselect(v_sel0, v_cond, v_l3[1], v_l3[0]); S.vselect(v_sel1, v_cond, v_l3[3], v_l3[2])
                    S.vselect(v_sel2, v_cond, v_l3[5], v_l3[4]); S.vselect(v_sel3, v_cond, v_l3[7], v_l3[6])
                    S.valu(">>", v_t2[i], v_t1[i], v_o); S.valu("&", v_cond, v_t2[i], v_o)
                    S.vselect(v_sel0, v_cond, v_sel1, v_sel0); S.vselect(v_sel2, v_cond, v_sel3, v_sel2)
                    S.valu(">>", v_t2[i], v_t1[i], v_two); S.vselect(v_t2[i], v_t2[i], v_sel2, v_sel0)
                    S.valu("^", v_val[i], v_val[i], v_t2[i])
            else:
                for i in vecs:
                    for vi in range(VLEN):
                        lp, ln, li = ScalarReg(v_t1[i].addr+vi, ""), ScalarReg(v_t2[i].addr+vi, ""), ScalarReg(v_idx[i].addr+vi, "")
                        S.alu("+", lp, s_fp, li); S.load(ln, lp)
                for i in vecs:
                    for vi in range(VLEN):
                        sv, sn = ScalarReg(v_val[i].addr+vi, ""), ScalarReg(v_t2[i].addr+vi, "")
                        S.alu("^", sv, sv, sn)

        def emit_fetch_alu(r, vecs):
            """Scalar ALU Fetch logic (for colonized 8 vectors)"""
            if not vecs: return
            for i in vecs:
                for v in range(VLEN):
                    lp, ln, li = a_t1[i][v], a_t2[i][v], a_idx[i][v]
                    S.alu("+", lp, s_fp, li); S.load(ln, lp); S.alu("^", a_val[i][v], a_val[i][v], ln)

        def emit_hash_valu(r, vecs):
            """VALU Hash logic"""
            level = r % (forest_height + 1)
            if not vecs: return
            for i in vecs:
                # S0
                S.valu("multiply_add", v_val[i], v_val[i], v_hm[0], v_h1[0])
                # S1
                S.valu("^", v_t1[i], v_val[i], v_h1[1]); S.valu(">>", v_t2[i], v_val[i], v_h3[1]); S.valu("^", v_val[i], v_t1[i], v_t2[i])
                # S2+S3 Fused
                S.valu("multiply_add", v_t1[i], v_val[i], v_hm[2], v_k2_prime)
                S.valu("multiply_add", v_t2[i], v_t1[i], v_512, v_k3_shifted_neg)
                S.valu("^", v_val[i], v_t1[i], v_t2[i])
                # S4
                S.valu("multiply_add", v_val[i], v_val[i], v_hm[4], v_h1[4])
                # S5
                S.valu("^", v_t1[i], v_val[i], v_h1[5]); S.valu(">>", v_t2[i], v_val[i], v_h3[5]); S.valu("^", v_val[i], v_t1[i], v_t2[i])
                for vi in range(VLEN):
                    sv, sd = ScalarReg(v_val[i].addr+vi, ""), ScalarReg(v_t1[i].addr+vi, "")
                    S.alu("&", sd, sv, s_c1); S.alu("+", sd, sd, s_c1)
                S.valu("multiply_add", v_idx[i], v_idx[i], v_two, v_t1[i])
                if level == forest_height:
                    for vi in range(VLEN):
                        si, st = ScalarReg(v_idx[i].addr+vi, ""), ScalarReg(v_t1[i].addr+vi, "")
                        S.alu("<", st, si, s_nn); S.alu("*", si, si, st)

        def emit_hash_alu(r, vecs):
            """Scalar ALU Hash logic (Fused S2+S3)"""
            level = r % (forest_height + 1)
            if not vecs: return
            for i in vecs:
                for v in range(VLEN):
                    sv, si = a_val[i][v], a_idx[i][v]
                    at1, at2 = a_t1[i][v], a_t2[i][v]
                    # S0
                    S.alu("+", at1, sv, self.get_const(0x7ED55D16))
                    S.alu("*", sv, sv, self.get_const(4097)); S.alu("+", sv, sv, self.get_const(0x7ED55D16))
                    # S1
                    S.alu("^", at1, sv, self.get_const(0xC761C23C))
                    S.alu(">>", at2, sv, self.get_const(19))
                    S.alu("^", sv, at1, at2)
                    # S2+S3 Fused
                    # t1 = a * 33 + K2_prime
                    # t2 = t1 * 512 + K3_shifted_neg
                    # a = t1 ^ t2
                    k2, k3 = 0x165667B1, 0xD3A2646C
                    k2_prime = (k2 + k3) % (2**32)
                    k3_shifted_neg = (-(k3 << 9)) % (2**32)
                    S.alu("*", at1, sv, self.get_const(33)); S.alu("+", at1, at1, self.get_const(k2_prime))
                    S.alu("*", at2, at1, self.get_const(512)); S.alu("+", at2, at2, self.get_const(k3_shifted_neg))
                    S.alu("^", sv, at1, at2)
                    # S4
                    S.alu("*", at1, sv, self.get_const(9)); S.alu("+", sv, at1, self.get_const(0xFD7046C5))
                    # S5
                    S.alu("^", at1, sv, self.get_const(0xB55A4F09))
                    S.alu(">>", at2, sv, self.get_const(16))
                    S.alu("^", sv, at1, at2)
                    
                    S.alu("&", at1, sv, s_c1); S.alu("+", at1, at1, s_c1)
                    S.alu("*", si, si, self.get_const(2)); S.alu("+", si, si, at1)
                    if level == forest_height:
                        S.alu("<", at1, si, s_nn); S.alu("*", si, si, at1)

        # ─────────────────────────────────────────────────────
        # Multi-phase interleaved execution
        # ─────────────────────────────────────────────────────
        groups_valu = [[] for _ in range(n_groups)]
        for i in range(n_valu_vecs): groups_valu[i % n_groups].append(i)
        groups_alu = [[] for _ in range(n_groups)]
        for i in range(n_alu_vecs): groups_alu[i % n_groups].append(i)
        
        group_offsets = [g * offset for g in range(n_groups)]
        max_offset = max(group_offsets)

        for step in range(rounds + max_offset):
            active = []
            for g in range(n_groups):
                r = step - group_offsets[g]
                if 0 <= r < rounds: active.append((g, r))
            if step % 2 == 1: active = active[::-1]
            for g, r in active:
                emit_fetch_valu(r, groups_valu[g]); emit_fetch_alu(r, groups_alu[g])
                emit_hash_valu(r, groups_valu[g]); emit_hash_alu(r, groups_alu[g])

        # ── Store results (24 VALU, 8 ALU) ──
        for i in range(n_valu_vecs):
            S.alu("+", s_sp_reg, s_ip, self.get_const(i * VLEN)); S.vstore(s_sp_reg, v_idx[i])
            S.alu("+", s_sp_reg, s_vp, self.get_const(i * VLEN)); S.vstore(s_sp_reg, v_val[i])
        for i in range(n_alu_vecs):
            S.alu("+", s_sp_reg, s_ip, self.get_const((n_valu_vecs+i) * VLEN))
            for v in range(VLEN):
                S.alu("+", tmp_va, s_sp_reg, self.get_const(v)); S.store(tmp_va, a_idx[i][v])
            S.alu("+", s_sp_reg, s_vp, self.get_const((n_valu_vecs+i) * VLEN))
            for v in range(VLEN):
                S.alu("+", tmp_va, s_sp_reg, self.get_const(v)); S.store(tmp_va, a_val[i][v])

        S.pause(n_iters=100)
        S.print_heatmap()
        self.instrs = S.bundles


def do_kernel_test(forest_height: int, rounds: int, batch_size: int, seed: int = 123, n_groups: int = 16, offset: int = 1):
    random.seed(seed)
    forest = Tree.generate(forest_height)
    inp = Input.generate(forest, batch_size, rounds)
    mem = build_mem_image(forest, inp, generate_lut=False)
    kb = KernelBuilder()
    kb.build_kernel(forest.height, len(forest.values), len(inp.indices), rounds, n_groups, offset)
    machine = Machine(mem, kb.instrs, kb.debug_info(), n_cores=N_CORES)
    machine.run()
    ref_mem = list(mem)
    for _ in reference_kernel2(ref_mem): pass
    ivp, iip = ref_mem[6], ref_mem[5]
    assert machine.mem[ivp : ivp + batch_size] == ref_mem[ivp : ivp + batch_size], "VALUES MISMATCH"
    assert machine.mem[iip : iip + batch_size] == ref_mem[iip : iip + batch_size], "INDICES MISMATCH"
    
    kb.sched.print_heatmap()
    total_valu = sum(len(b.get("valu", [])) for b in kb.instrs)
    total_alu = sum(len(b.get("alu", [])) for b in kb.instrs)
    print(f"📊 Stats: VALU={total_valu} ops, ALU={total_alu} ops")
    print(f"✅ {machine.cycle} cycles")
    return machine.cycle


class Tests(unittest.TestCase):
    def test_kernel_cycles(self):
        cycles = do_kernel_test(10, 16, 256)
        assert cycles < 2500, f"Expected < 2500, got {cycles}"


if __name__ == "__main__":
    unittest.main()
