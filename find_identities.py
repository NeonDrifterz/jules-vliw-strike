
import random
import sys

HASH_STAGES = [
    ("+", 0x7ED55D16, "+", "<<", 12),
    ("^", 0xC761C23C, "^", ">>", 19),
    ("+", 0x165667B1, "+", "<<", 5),
    ("+", 0xD3A2646C, "^", "<<", 9),
    ("+", 0xFD7046C5, "+", "<<", 3),
    ("^", 0xB55A4F09, "^", ">>", 16),
]

def r(x):
    return x % (2**32)

def run_stage(a, stage_idx):
    op1, val1, op2, op3, val3 = HASH_STAGES[stage_idx]

    v1 = val1
    v3 = val3

    if op1 == "+": t1 = r(a + v1)
    elif op1 == "^": t1 = r(a ^ v1)

    if op3 == "<<": t2 = r(a << v3)
    elif op3 == ">>": t2 = r(a >> v3)

    if op2 == "+": res = r(t1 + t2)
    elif op2 == "^": res = r(t1 ^ t2)

    return res

def myhash(a):
    for i in range(6):
        a = run_stage(a, i)
    return a

def check_identities():
    # Test 1: Check if S1 and S2 commute
    # S1: (a ^ C1) ^ (a >> 19)
    # S2: a * 33 + C2

    print("Checking if S1 and S2 commute...")
    for _ in range(100):
        a = random.randint(0, 2**32-1)

        # Original: S1 then S2
        s1 = run_stage(a, 1)
        s2 = run_stage(s1, 2)

        # Swapped: S2 then S1
        # But we need to be careful, S1 depends on input 'a'.
        # If we swap, we apply S2 to 'a', then S1 to result?
        # That would mean S1' is different.

        # Let's just check raw swap
        s2_first = run_stage(a, 2)
        s1_second = run_stage(s2_first, 1)

        if s2 != s1_second:
            print("S1 and S2 do NOT commute")
            break
    else:
        print("S1 and S2 DO commute")

    # Test 2: Check if S3 and S4 commute
    print("Checking if S3 and S4 commute...")
    for _ in range(100):
        a = random.randint(0, 2**32-1)
        s3 = run_stage(a, 3)
        s4 = run_stage(s3, 4)

        s4_first = run_stage(a, 4)
        s3_second = run_stage(s4_first, 3)

        if s4 != s3_second:
            print("S3 and S4 do NOT commute")
            break
    else:
        print("S3 and S4 DO commute")

    # Test 3: Check composition of linear stages
    # S0: a * 4097 + C0
    # S2: a * 33 + C2
    # S4: a * 9 + C4

    # Check if we can simplify S1: (a ^ C1) ^ (a >> 19)
    # This is a ^ (a >> 19) ^ C1.
    # In VLIW:
    # t1 = a >> 19
    # t2 = a ^ C1  (can be precomputed? No, a varies)
    # res = t2 ^ t1

    # Or:
    # t1 = a >> 19
    # t2 = a ^ t1
    # res = t2 ^ C1

    # Can we merge C1 with previous stage?
    # Previous stage S0 returns res0 = a * 4097 + C0
    # S1 input is res0.
    # res1 = res0 ^ (res0 >> 19) ^ C1

    # What if we did:
    # res1 = (res0 ^ C1) ^ (res0 >> 19)? No that's the same.

    # Is there a relation between C1 and C0?

    pass

if __name__ == "__main__":
    check_identities()
