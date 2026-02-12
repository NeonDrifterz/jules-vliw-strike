#!/bin/bash
# verify_generality.sh - VLIW Generality Watchdog
# Tests the kernel against various forest heights and batch sizes.

TARGET="/Users/granite/perf_takehome.py"

echo "=== 🧪 VLIW Generality Sweep ==="

configs=(
    "8 128"
    "8 256"
    "10 128"
    "10 256"
)

failed=0

for config in "${configs[@]}"; do
    read -r depth batch <<< "$config"
    echo -n "Testing Depth $depth, Batch $batch... "
    
    # Modify the do_kernel_test call in the script temporarily or use a wrapper
    # For now, we'll use a python one-liner to call the specific test
    OUTPUT=$(python3 -c "from perf_takehome import do_kernel_test; do_kernel_test(forest_height=$depth, rounds=16, batch_size=$batch, n_groups=16, offset=1)" 2>&1)
    
    if [[ $? -eq 0 ]]; then
        CYCLES=$(echo "$OUTPUT" | grep "✅" | awk '{print $2}')
        echo "PASS ($CYCLES cycles)"
    else
        echo "FAIL"
        echo "$OUTPUT" | tail -n 10
        failed=1
    fi
done

if [ $failed -eq 0 ]; then
    echo "=== ✅ ALL GENERALITY TESTS PASSED ==="
    exit 0
else
    echo "=== ❌ SOME TESTS FAILED ==="
    exit 1
fi
