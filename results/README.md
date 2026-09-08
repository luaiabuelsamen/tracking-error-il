# results/

Frozen records. Nothing here is edited by hand; the paper's tables and figures
are regenerated from these files by `scripts/paper/`.

## simulation/

`grid_<letter>_<arm>_s<seed>.json`: one trained policy per file, evaluated on
100 shared-seed episodes with the crush threshold disabled (`crush: -1`).
The letter-to-design mapping is in `scripts/README.md`. `grid600_*` are the
600-demonstration screen saved at 26,000 steps; `h100_eval.json` is the
earlier 600-demonstration comparison at 224 pixels and 50,000 steps;
`crush_*` are the post-hoc crush-tier screen; `guard_ab.json` is the runtime
guard comparison; `resolution_sweep.json` and `expert_rigid_block.json` are the
scripted-expert quantum sweep and its no-limit row (`scripts/sim/resolution_sweep.py`).
`h100_eval.json` was written by the cloud evaluation of the two 600-demonstration
checkpoints (`scripts/sim/modal_train.py`).

## hardware/

| file | contents |
|---|---|
| `real_delta_v3_trials.json` | seed 0: 40 rollouts, 20 pairs, `base_v2` vs `delta_v3` |
| `real_delta_v3_s1_trials.json` | seed 1: 40 rollouts, 20 pairs |
| `real_delta_v3_s2_trials.json` | seed 2: 12 labeled rollouts, 6 pairs, interrupted |
| `real_delta_v3_s2_trials_pending.json` | the thirteenth seed-2 rollout, completed but never labeled |
| `real_trial_traj/*.npz` | per-rollout trajectories: `pos`, `action` (requested), `applied_action` (after the limiter), `observation_state`, `elapsed_s` |
| `*_manifest.json`, `*_incident.json` | session arguments and hashes at recording time; shutdown incidents |
| `real_delta_v3_*summary.json`, `real_delta_v3_diagnostics.json` | paired counts and the seed-0 trajectory diagnostics |
| `real_observation_audit.json` | offline replay check of training and inference state vectors |
| `real_trials.json` | the earlier position-only vs compensated-residual comparison (2026-09-04 and 05 sessions) |
| `real_delta_replication/` | training logs (seeds 1 and 2, and the position-history checkpoints `ghist_s0`, `ghist_s1`), the pre-evaluation hash manifest, and `validation.json` (offline check of the replication checkpoints) |
| `real_history_control_s1_trials.json` (+ manifests, incident) | the interrupted seed-1 position-history session of 2026-09-07: 19 rollouts, 9 complete pairs |
| `checkpoint_sensitivity.json` | offline teacher-forcing error and tracking-error input sensitivity of the six evaluated checkpoints (`scripts/real/checkpoint_sensitivity.py`) |
| `demonstration_summary.json` | per-episode length, grasp-closure frame and post-replay travel fraction of the 50 demonstrations, cached for builds without the raw dataset |
| `real_delta_v3_*summary.json`, `*_interrupted_summary.json` | paired counts per session, written at the end of each bench session by the operator tooling; the paper recomputes them from the trial rows |

Each trial row records `session`, `trial`, `pair`, `arm`, `checkpoint`,
`success` (operator-entered), `jumpstart` (replayed commands) and `traj`
(path relative to this directory). Seeds 1 and 2 add `shutdown_error`,
`recovered_outcome` and `trajectory_missing`.

## corpus/

`corpus_delta_outcome.json`: per-dataset rows with `episodes`, `success_rate`,
`cohen_d`, `d_ci` and the medians behind them; rows without `cohen_d` failed
an inclusion gate and carry the reason. `offset_sweep.json`: `cohen_d_by_k`
for assumed command offsets $k=0..5$.

## calibration/

`staircase_channel_j2.npz`: twelve hanging masses at five poses on one
shoulder-lift servo, with `Present_Load`, `Present_Current`, position and goal
logged together (`scripts/bench/staircase_cal.py`).
`demonstration_load_vs_delta.npz`: 2-D histogram and summary statistics of the
gripper load register against jaw tracking error over the demonstration
frames, cached so the measurement figure rebuilds without the raw dataset.

## showcase/

Trajectory records of the showcase rollouts featured in `media/`. Videos are
not tracked except the one under `media/`.
