
import random

K2 = 0x165667B1
K3 = 0xD3A2646C

def r(x):
    return x % (2**32)

def original_s2_s3(a):
    # Stage 2
    a2 = r(a * 33 + K2)
    # Stage 3
    # ("+", 0xD3A2646C, "^", "<<", 9)
    # t1 = a + K3
    # t2 = a << 9
    # res = t1 ^ t2
    t1 = r(a2 + K3)
    t2 = r(a2 << 9)
    a3 = r(t1 ^ t2)
    return a3

def optimized_s2_s3(a):
    K2_prime = r(K2 + K3)
    K3_shifted_neg = r(-(K3 << 9))

    # Combined S2+S3
    # 1. a2_prime = a * 33 + (K2 + K3)
    a2_prime = r(a * 33 + K2_prime)

    # 2. t2 = a2_prime * 512 - K3 * 512
    # Note: -K3*512 is constant
    t2 = r(a2_prime * 512 + K3_shifted_neg)

    # 3. a3 = a2_prime ^ t2
    a3 = r(a2_prime ^ t2)
    return a3

def verify():
    print("Verifying S2+S3 optimization...")
    for _ in range(1000):
        a = random.randint(0, 2**32-1)
        res_orig = original_s2_s3(a)
        res_opt = optimized_s2_s3(a)
        if res_orig != res_opt:
            print(f"Mismatch for input {a}: {res_orig} != {res_opt}")
            return
    print("Verification SUCCESS!")

if __name__ == "__main__":
    verify()
