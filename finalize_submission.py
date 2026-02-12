import sys
import os

TEMPLATE_PATH = "jules_vliw_strike/perf_takehome.py"
OUTPUT_PATH = "submission_final.py"

def generate(n_groups, offset, alu_vecs, seed=123):
    if not os.path.exists(TEMPLATE_PATH):
        print(f"Error: {TEMPLATE_PATH} not found.")
        return

    with open(TEMPLATE_PATH, 'r') as f:
        content = f.read()

    # 1. Remove Argument Parsing
    import re
    # Look for the if __name__ == "__main__": block
    main_pattern = r'if __name__ == "__main__":.*'
    replacement = f"""if __name__ == "__main__":
    # Hardcoded Winning Parameters (Industrial Clean Room)
    do_kernel_test(10, 16, 256, seed={seed}, n_groups={n_groups}, offset={offset}, alu_vecs={alu_vecs})
"""
    new_content = re.sub(main_pattern, replacement, content, flags=re.DOTALL)

    # 2. Hardcode default parameters in build_kernel signature just in case
    signature_pattern = r'def build_kernel\(self, forest_height: int, n_nodes: int, batch_size: int, rounds: int, n_groups: int = 16, offset: int = 1, alu_vecs: int = 0\):'
    sig_replacement = f'def build_kernel(self, forest_height: int, n_nodes: int, batch_size: int, rounds: int, n_groups: int = {n_groups}, offset: int = {offset}, alu_vecs: int = {alu_vecs}):'
    new_content = re.sub(signature_pattern, sig_replacement, new_content)

    with open(OUTPUT_PATH, 'w') as f:
        f.write(new_content)
    
    print(f"✅ Submission file generated: {OUTPUT_PATH}")
    print(f"Config: groups={n_groups}, offset={offset}, alu_vecs={alu_vecs}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 finalize_submission.py <groups> <offset> <alu_vecs>")
        sys.exit(1)
    
    generate(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]))
