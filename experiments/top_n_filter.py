import pandas as pd
import sys

def main(csv_path, n=10):
    try:
        df = pd.read_csv(csv_path)
        # Sort by cycles (ascending) and take top N
        top_n = df.sort_values(by='cycles').head(n)
        print(f"--- TOP {n} SEEDS FOUND ---")
        print(top_n.to_string(index=False))
        
        # Output as a Python list of seeds for Sigma
        seeds = top_n['seed'].tolist()
        print(f"
PROPOSED SEEDS FOR SYNTHESIS: {seeds}")
    except Exception as e:
        print(f"Error processing CSV: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 top_n_filter.py <path_to_csv> [n]")
    else:
        n_val = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        main(sys.argv[1], n_val)
