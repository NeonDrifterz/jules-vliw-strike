
import random
import sys

def r(x):
    return x % (2**32)

# Stage 2 constants
K2 = 0x165667B1

# Stage 3 constants
K3 = 0xD3A2646C

def s2_s3_orig(x):
    # Stage 2: x = (x + K2) + (x << 5)
    # Actually, the implementation uses multiply_add with 33.
    # 33 = 1 + (1 << 5).
    # x + (x << 5) = 33 * x.
    # So x_new = 33 * x + K2.
    y = r(33 * x + K2)

    # Stage 3: x = (x + K3) ^ (x << 9)
    # x_final = (y + K3) ^ (y << 9)
    z = r( (r(y + K3)) ^ r(y << 9) )
    return z

def s2_s3_fused(x):
    # Fused:
    # Term 1: y + K3 = 33 * x + K2 + K3
    term1 = r(33 * x + r(K2 + K3))

    # Term 2: y << 9 = (33 * x + K2) << 9
    #        = 33 * (x << 9) + (K2 << 9)
    #        = (x << 14) + (x << 9) + (K2 << 9)
    #        = x * (2**14 + 2**9) + (K2 << 9)
    #        = x * 16896 + (K2 << 9)
    term2 = r(16896 * x + r(K2 << 9))

    z = term1 ^ term2
    return z

def main():
    print("Verifying S2+S3 Fusion Identity on 1,000,000 random inputs...")

    failures = 0
    for i in range(1000000):
        x = random.randint(0, 2**32 - 1)
        res_orig = s2_s3_orig(x)
        res_fused = s2_s3_fused(x)

        if res_orig != res_fused:
            failures += 1
            print(f"MISMATCH at x={x:08x}: orig={res_orig:08x} fused={res_fused:08x}")
            if failures >= 10:
                print("Too many failures, aborting.")
                sys.exit(1)

    if failures == 0:
        print("SUCCESS: Identity verified for 1,000,000 inputs.")
    else:
        print(f"FAILED: {failures} mismatches found.")
        sys.exit(1)

if __name__ == "__main__":
    main()
