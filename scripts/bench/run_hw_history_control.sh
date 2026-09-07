#!/usr/bin/env bash
# Paired hardware evaluation of the position-history control; see
# docs/hardware/preregistration_2026-09-07_history_control.md.
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
seed="${1:-1}"
if [[ $# -gt 0 ]]; then shift; fi
case "$seed" in
  1) arms="delta_s1,ghist_s1" ;;
  0) arms="base_v2,ghist_s0" ;;
  *) echo "Usage: bash scripts/bench/run_hw_history_control.sh [1|0]" >&2; exit 1 ;;
esac
exec "${SO101_VENV_PYTHON:-python}" scripts/real/trial_runner.py \
  --arms "$arms" --paired --trials 40 \
  --jumpstart 115 --max-steps 400 \
  --out "results/hardware/real_history_control_s${seed}_trials.json" "$@"
