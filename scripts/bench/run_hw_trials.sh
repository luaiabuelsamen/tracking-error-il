#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.."
exec "${SO101_VENV_PYTHON:-python}" scripts/real/trial_runner.py \
  --arms base_v2,delta_v3 --paired --trials 40 \
  --jumpstart 115 --max-steps 400 \
  --out results/hardware/real_delta_v3_trials.json
