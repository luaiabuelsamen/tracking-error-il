#!/usr/bin/env bash
# Serial offline training of the matched position-history checkpoints; no hardware access.
# Recipe identical to run_real_delta_replication.sh (see docs/hardware/preregistration_2026-09-07_history_control.md).
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
PY="${SO101_VENV_PYTHON:-python}"
mkdir -p results/hardware/real_delta_replication
for seed in 1 0; do
  target="checkpoints/real50_ghist_v3_s${seed}"
  if [[ -e "$target" ]]; then
    echo "Refusing existing checkpoint directory: $target" >&2
    exit 1
  fi
done
for seed in 1 0; do
  echo "start $(date -u +%FT%TZ) seed ${seed}" >> results/hardware/real_delta_replication/ghist_queue.log
  "$PY" -u scripts/real/train_act_real.py \
    --arm ghist --ghist-k 8 --root data/real/pickplace_real_v0 \
    --out "checkpoints/real50_ghist_v3_s${seed}" \
    --steps 6000 --batch 8 --lr 0.0001 --image-size 96 --seed "$seed" \
    > "results/hardware/real_delta_replication/ghist_s${seed}.log" 2>&1
  echo "done  $(date -u +%FT%TZ) seed ${seed}" >> results/hardware/real_delta_replication/ghist_queue.log
done
echo "Both history-control checkpoints finished."
