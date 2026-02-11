"""
VERIFICATION EXTREME: High-Fidelity Performance Audit
Designed for the Red Team to find flaws in Sigma's kernel.
"""
import time
from perf_takehome import KernelBuilder, do_kernel_test

def run_extreme_audit(kernel_logic_file):
    print(f"--- INITIATING EXTREME AUDIT: {kernel_logic_file} ---")
    
    # 1. Sensitivity Test: Run across 100 random forest configurations
    results = []
    for seed in range(100):
        try:
            cycles = do_kernel_test(forest_height=10, rounds=16, batch_size=256, seed=seed)
            results.append(cycles)
        except Exception as e:
            print(f"CRITICAL FAILURE at Seed {seed}: {e}")
            return
            
    avg = sum(results) / len(results)
    print(f"
AUDIT COMPLETE:")
    print(f"  Best Case:  {min(results)} cycles")
    print(f"  Worst Case: {max(results)} cycles")
    print(f"  Average:    {avg:.2f} cycles")
    
    if avg > 1000:
        print("
RED TEAM VERDICT: FAILURE. Kernel remains above 1000-cycle threshold.")
    else:
        print("
RED TEAM VERDICT: SUCCESS. 1000-cycle floor breached.")

if __name__ == "__main__":
    run_extreme_audit("perf_takehome.py")
