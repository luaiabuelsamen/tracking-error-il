# Pre-registration: a third completed training seed — 2026-11-10

Written before the seed-3 checkpoints were trained and before anything in this plan touched the
arm. Committed to the repository before the training queue started; the queue log under
`results/hardware/real_revision_training/queue.log` records start times.

## Why

Reviewer bA2d (`docs/reviews/corl2026_webp.md`, item 2): seed 1 carries the hardware result. Seed 0
is 9/20 against 5/20 (exact McNemar $p=0.29$, not significant under its registered rule), seed 1 is
14/20 against 1/20 ($p=0.001$), and seed 2 was stopped by the gripper fault after six all-failure
pairs. A third completed seed is the cheapest way to show whether seed 1 is typical.

## Decision: new seed, not a seed-2 continuation

Seed 2's checkpoints exist, but its six pairs were recorded on a servo that was faulting (three
overloads in thirteen rollouts; the jaw never closed in eight of twelve rollouts). Continuing seed 2
after a repair would mix two plant states in one comparison. Seed 2's record stays as it is,
reported as interrupted. The replication is a fresh seed:

- `checkpoints/real50_base_v3_s3` and `checkpoints/real50_delta_v3_s3`, trained by
  `scripts/real/run_revision_training.sh` with exactly the seeds 1 and 2 recipe: same
  50-demonstration recording, stationary-prefix trimming (18,549 frames), 96 px, 6,000 steps,
  batch 8, learning rate 0.0001, default ACT architecture, final checkpoint only, `--seed 3`.
- Eligibility: training completes and the offline observation audit
  (`scripts/real/audit_real_observations.py`) passes. No selection on training loss or on any
  hardware outcome.

## Comparison

Seed 3, `base_s3` against `delta_s3`, 20 complete pairs in one session, AB/BA order alternating
between pairs, 115-command replay from demonstration 0, 400-step horizon, relative-target limit 8,
the same runner (`scripts/real/trial_runner.py`) and launcher
(`bash scripts/bench/run_hw_replication.sh 3`). Outcomes are recorded from the per-trial video by a
labeller who sees only the trial code (`--video`, then `scripts/real/label_trials.py`); the
operator's live label is kept alongside and any disagreement is reported.

## Registered prediction and decision rule

Prediction: tracking error places more often than position only. Criterion: exact two-sided McNemar
on the discordant pairs, positive effect and $p<0.05$. A non-significant positive result is reported
as "direction reproduced, not significant at 20 pairs"; a negative point estimate is reported as a
failed replication. Either way, the paper reports all four seeds separately with their equal-weight
mean and does not pool episodes across seeds as if they were independent replicates.

## Rules carried over

- Outcomes are never used for selection. Every trained checkpoint is evaluated.
- Technical failures are recorded with a reason and never dropped; a shutdown overload after a
  completed horizon keeps its operator and video labels (Table of overloads per policy in the paper).
- Missing outcomes stay missing.
- Before the session: `docs/hardware/overload_diagnosis_2026-11.md` must have a finding. If the fix
  changes the plant (torque limit, jaw stop, servo replacement), the session is a new plant version
  and is reported as such; seeds 0 to 2 are not re-run.
- If the session is interrupted, the record is kept as interrupted and a clean 20-pair session is a
  new versioned record (`_v2`), as for the history control; records are never merged.

## Bench cost

40 rollouts of about 14 s plus manual resets, roughly 2 hours with setup.
