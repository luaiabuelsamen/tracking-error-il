#!/usr/bin/env bash
# Paired hardware evaluation of the grasp-bit policies; see
# docs/hardware/preregistration_2026-11_grasp_bit.md. Records video for blind labels.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
which="${1:-1}"
if [[ $# -gt 0 ]]; then shift; fi
case "$which" in
  1) arms="base_s1,gbit_s1"; out="results/hardware/real_grasp_bit_s1_trials.json" ;;
  2) arms="delta_s1,delta_gbit_s1"; out="results/hardware/real_grasp_bit_delta_s1_trials.json" ;;
  *) echo "Usage: bash scripts/bench/run_hw_grasp_bit.sh [1|2]  (1: base vs grasp bit, 2: tracking error vs tracking error + grasp bit)" >&2; exit 1 ;;
esac
exec "${SO101_VENV_PYTHON:-python}" scripts/real/trial_runner.py \
  --arms "$arms" --paired --trials 40 \
  --jumpstart 115 --max-steps 400 --video \
  --out "$out" "$@"
