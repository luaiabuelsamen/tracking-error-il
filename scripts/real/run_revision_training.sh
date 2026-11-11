#!/usr/bin/env bash
# Serial offline training for the November 2026 revision; no hardware access.
# Cells, in order: base and tracking error at seed 3 (preregistration_2026-11_seed_replication.md),
# then grasp bit and tracking error + grasp bit at seed 1 (preregistration_2026-11_grasp_bit.md).
# Recipe identical to run_real_delta_replication.sh. Refuses to start if the GPU is busy.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
PY="${SO101_VENV_PYTHON:-python}"
OUT=results/hardware/real_revision_training
mkdir -p "$OUT"
CELLS=("base 3 real50_base_v3_s3" "delta 3 real50_delta_v3_s3" "gbit 1 real50_gbit_v3_s1" "delta_gbit 1 real50_delta_gbit_v3_s1")
for cell in "${CELLS[@]}"; do
  set -- $cell
  if [[ -e "checkpoints/$3" ]]; then
    echo "Refusing existing checkpoint directory: checkpoints/$3" >&2
    exit 1
  fi
done
# The GPU is shared with other sessions on this device: refuse if it is already loaded.
if command -v tegrastats >/dev/null; then
  load=$(timeout 4 tegrastats --interval 1000 2>/dev/null | head -2 | sed -n 's/.*GR3D_FREQ \([0-9]*\)%.*/\1/p' | sort -n | tail -1)
  if [[ -n "${load:-}" && "$load" -gt 15 ]]; then
    echo "GPU already at ${load}% (another session's job?); not starting the queue" >&2
    exit 1
  fi
fi
if [[ ! -e "$OUT/manifest.json" ]]; then
  "$PY" scripts/real/record_real_replication_manifest.py --out "$OUT/manifest.json" \
    --queue scripts/real/run_revision_training.sh \
    --plan docs/hardware/preregistration_2026-11_seed_replication.md docs/hardware/preregistration_2026-11_grasp_bit.md
fi
for cell in "${CELLS[@]}"; do
  set -- $cell
  arm=$1; seed=$2; name=$3
  echo "start $(date -u +%FT%TZ) $name" >> "$OUT/queue.log"
  "$PY" -u scripts/real/train_act_real.py \
    --arm "$arm" --root data/real/pickplace_real_v0 \
    --out "checkpoints/$name" \
    --steps 6000 --batch 8 --lr 0.0001 --image-size 96 --seed "$seed" \
    > "$OUT/${name}.log" 2>&1
  echo "done  $(date -u +%FT%TZ) $name" >> "$OUT/queue.log"
done
echo "audit $(date -u +%FT%TZ)" >> "$OUT/queue.log"
"$PY" scripts/real/audit_real_observations.py > "$OUT/audit.log" 2>&1 || echo "AUDIT FAILED" >> "$OUT/queue.log"
echo "finished $(date -u +%FT%TZ)" >> "$OUT/queue.log"
