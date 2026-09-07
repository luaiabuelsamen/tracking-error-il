# scripts/

Every result in `results/` and every number in the paper comes from one of
these. Run them from the repository root.

## Design names

The paper names observation designs by what they contain; the code and the
result files use short identifiers.

| paper | `--arm` | observation | grid prefix |
|---|---|---|---|
| Position (base) | `base` | $q_t$ | `grid_A_base` |
| Action history | `base_hist` | $[q_t, g_{t-1}]$ | `grid_B_base_hist` |
| Tracking error | `delta` | $[q_t, g_{t-1}-q_t]$ | `grid_C_delta` |
| Auxiliary target | `resid` | $q_t$, with tracking error as a training target | `grid_D_resid` |
| Compensated residual | `excess` | $[q_t, \delta_t - \hat K (g_{t-1}-g_{t-2})]$ | `grid_E_excess` |
| Seat token | `token` | $q_t$ plus a latched contact token | `grid_F_token` |
| Position history | `ghist` | $[q_t, q_{t-8}]$ | `grid_G_ghist` |
| Two-command history | `base_hist2` | $[q_t, g_{t-1}, g_{t-2}]$ | `grid_H_base_hist2` |

Suffix `_sN` is the training seed. The `*g_*` prefixes are the guarded
variants of the same designs and are not in the paper. On hardware the
checkpoints are `real50_{base,delta}_v3_s{0,1,2}`; `base_v2` is the seed-0
position-only checkpoint.

## sim/

| script | role |
|---|---|
| `collect.py`, `collect_guarded.py` | scripted-expert demonstrations as a LeRobotDataset; the guarded variant produced the 280-episode set used in the paper |
| `evaluate.py`, `render_demo.py`, `resolution_sweep.py` | scripted-expert evaluation, video, and the observation-quantum sweep |
| `train_act.py` | train ACT on the demonstrations for one design and seed, then evaluate closed-loop on 100 shared-seed episodes |
| `run_grid.sh`, `grid_spec.json`, `modal_grid.py`, `modal_train.py` | the full design grid, locally or on Modal, from the committed spec |
| `eval_crush_tier.py`, `analyze_crush_tier.py` | post-hoc crush-threshold screen of trained checkpoints and its pre-registered analysis |
| `eval_guard.py` | the runtime jaw guard comparison |

## real/

| script | role |
|---|---|
| `train_act_real.py` | train ACT on the 50 teleoperated demonstrations for one design and seed |
| `run_policy_real.py` | execute a checkpoint on the arm: fixed replay, then policy control under a relative-target limiter; the only script that commands the robot |
| `trial_runner.py` | paired evaluation sessions with alternating order, operator-entered outcomes, incident and resume manifests |
| `analyze_real_delta_trials.py` | paired statistics and descriptive trajectory diagnostics for the seed-0 session |
| `audit_real_observations.py` | offline replay check that training and inference state vectors agree |
| `record_real_replication_manifest.py`, `run_real_delta_replication.sh` | hash manifest and training queue for seeds 1 and 2, written before those seeds were evaluated |
| `real_channel_saturation.py` | how often the gripper load register sits at its configured limit in the demonstrations |

## corpus/

| script | role |
|---|---|
| `corpus_delta_outcome.py` | tracking error at grasp onset versus episode outcome across public SO-100/101 datasets |
| `offset_sweep.py` | the same analysis under assumed command offsets of 0 to 5 frames |

## paper/

| script | role |
|---|---|
| `build_paper_evidence.py` | hardware tables, simulation means, the two main figures, `paper/generated/evidence.json` |
| `supplementary_analysis.py` | stratified hardware statistics, jaw-trace taxonomy, power table, corpus and measurement figures, simulation contrasts; `paper/generated/supplementary.json` |
| `check_paper_numbers.py` | asserts every value and required disclosure in `main.tex` against the generated evidence |
| `appendix_d_channels.py`, `appendix_d_stats.py` | static-bench relation between tracking error, load and current registers, and applied mass |

## bench/

Hardware setup and operation; see [`bench/README.md`](bench/README.md).

## Environment

Scripts that need the patched LeRobot install read `SO101_VENV_PYTHON` (the
interpreter it is installed in) and `LEROBOT` (the checkout). Without them
they fall back to `python` and `~/projects/clean_env/lerobot`.
