import sys
import time
import random
from perf_takehome import do_kernel_test, Tree, Input, build_mem_image

def main():
    print("Starting Marathon...", flush=True)
    results = []

    # Pre-build memory image to save time
    print("Pre-building memory image...", flush=True)
    random.seed(123)
    forest = Tree.generate(10)
    inp = Input.generate(forest, 256, 16)
    mem = build_mem_image(forest, inp)
    print("Memory image built.", flush=True)

    # Define variations
    variations = []

    # 1. Vary n_groups (offset=1, n_iters=100, seed=42)
    for ng in [16, 32, 8, 4, 2, 1]:
        variations.append({"n_groups": ng, "offset": 1, "n_iters": 100, "scheduler_seed": 42})

    # 2. Vary offset (n_groups=16, n_iters=100, seed=42)
    for off in [0, 2, 3, 4]:
        variations.append({"n_groups": 16, "offset": off, "n_iters": 100, "scheduler_seed": 42})

    # 3. Vary n_iters (n_groups=16, offset=1, seed=42)
    for ni in [10, 50, 200, 500]:
        variations.append({"n_groups": 16, "offset": 1, "n_iters": ni, "scheduler_seed": 42})

    # 4. Vary scheduler_seed (n_groups=16, offset=1, n_iters=100)
    for seed in range(36):
        variations.append({"n_groups": 16, "offset": 1, "n_iters": 100, "scheduler_seed": seed})

    print(f"Total variations: {len(variations)}", flush=True)

    # Run variations
    best_cycles = float('inf')
    best_params = {}

    log_file = open("marathon_log.txt", "w")

    for i, params in enumerate(variations):
        print(f"Running variation {i+1}/{len(variations)}: {params}", flush=True)
        try:
            cycles = do_kernel_test(
                forest_height=10,
                rounds=16,
                batch_size=256,
                seed=123, # Fixed problem instance
                n_groups=params["n_groups"],
                offset=params["offset"],
                n_iters=params["n_iters"],
                scheduler_seed=params["scheduler_seed"],
                prebuilt_mem=mem,
                prebuilt_forest=forest,
                prebuilt_inp=inp
            )

            log_line = f"Variation {i+1}: {params} => {cycles} cycles"
            print(log_line, flush=True)
            log_file.write(log_line + "\n")
            log_file.flush()

            if cycles < best_cycles:
                best_cycles = cycles
                best_params = params

        except Exception as e:
            err_msg = f"Variation {i+1} failed: {e}"
            print(err_msg, flush=True)
            log_file.write(err_msg + "\n")
            log_file.flush()
            pass

    log_file.close()

    print("\n" + "="*50, flush=True)
    print("MARATHON COMPLETE", flush=True)
    print(f"Best Result: {best_cycles} cycles", flush=True)
    print(f"Parameters: {best_params}", flush=True)
    print("="*50, flush=True)

if __name__ == "__main__":
    main()
