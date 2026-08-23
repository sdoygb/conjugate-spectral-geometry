#!/bin/bash
set -e
cd "$(dirname "$0")/../src/pyqpanda"
mkdir -p ../../results

echo "=== Generic Grover ==="
python3 grover_search.py | tee ../../results/grover_generic.txt

echo "=== SVP Grover Demo ==="
python3 svp_grover_demo.py | tee ../../results/svp_grover.txt

echo "=== MLWE Grover Demo ==="
python3 mlwe_grover_demo.py | tee ../../results/mlwe_grover.txt

echo "Done. Results saved under results/."
