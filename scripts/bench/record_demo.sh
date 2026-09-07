#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
mkdir -p results/showcase
tag="$(date +%Y%m%dT%H%M%S)"
echo "Showcase only: raw delta, seed 1. Fixed replay start, then 400 policy steps."
read -r -p "Reset the adapter and tape roll; press Enter when ready beside the arm. "
exec "${SO101_VENV_PYTHON:-python}" scripts/real/run_policy_real.py \
  --checkpoint checkpoints/real50_delta_v3_s1 --arm delta \
  --home data/real/pickplace_real_v0 --jumpstart 115 --max-steps 400 \
  --out-traj "results/showcase/${tag}_delta_s1.npz" \
  --out-video "results/showcase/${tag}_delta_s1.mp4"
