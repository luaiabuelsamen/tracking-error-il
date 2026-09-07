#!/usr/bin/env bash
# Serial offline training only; no hardware access.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
mkdir -p results/hardware/real_delta_replication
for seed in 1 2; do
  for arm in base delta; do
    target="checkpoints/real50_${arm}_v3_s${seed}"
    if [[ -e "$target" ]]; then
      echo "Refusing existing checkpoint directory: $target" >&2
      exit 1
    fi
  done
done
"${SO101_VENV_PYTHON:-python}" scripts/real/record_real_replication_manifest.py
for seed in 1 2; do
  for arm in base delta; do
    "${SO101_VENV_PYTHON:-python}" -u scripts/real/train_act_real.py \
      --arm "$arm" --root data/real/pickplace_real_v0 \
      --out "checkpoints/real50_${arm}_v3_s${seed}" \
      --steps 6000 --batch 8 --lr 0.0001 --image-size 96 --seed "$seed" \
      > "results/hardware/real_delta_replication/${arm}_s${seed}.log" 2>&1
  done
done
echo "All four replication checkpoints finished."
