# Hardware seed-0 result and trajectory audit — 2026-09-05

Session 2026-09-05T18:50:04: 40 recorded rollouts, 20 complete matched pairs,
all 400 steps long, all trajectories present. Base_v2 succeeds 5/20 and
delta_v3 succeeds 9/20. Paired counts: both 3, neither 9, base only 2,
delta only 6. Delta minus base = +20 percentage points; exact two-sided
McNemar p=0.2890625; paired percentile bootstrap 95% interval [-5,+45]
points (20,000 resamples, seed 0). This does not meet the registered rule.

Reproduce with scripts/analyze_real_delta_trials.py. Outputs:
results/real_delta_v3_diagnostics.json and research/figures/real_delta_v3_diagnostics.png.
These diagnostics are exploratory, computed after outcomes were known.

## Integrity checks

- All 11 source/checkpoint hashes match the session manifest.
- Saved normalized positions reproduce from positions and checkpoint stats.
- Every delta observation after the first saved step exactly reproduces from
  the preceding applied command, current position and divisor 8. The first
  handoff command was not saved, so that step is not covered by this check.
- Median achieved rates are 28.7–28.8 Hz across arm/outcome groups; no large
  arm-level timing disparity appears in the saved timestamps.
- First/second-in-pair successes: base 3/10 and 2/10; delta 5/10 and 4/10.
  These small descriptive counts do not establish absence of order effects.

## What the motion shows

Delta successes settle into a consistent final jaw position near 2 recorded
units, while failures finish between approximately 10 and 31. The median
total motion over the final 100 steps is 14.3 joint units on delta successes
and 93.6 on failures. These are mixed joint-coordinate units, not physical
path lengths. Delta failures therefore do not reproduce a universal frozen
tail. A stationary successful endpoint is not a failure to act.

Command limiting is substantial: median fraction of affected steps is 26%
for successful delta trials, 5.75% for failed delta trials, 35% for successful
base trials and 29.25% for failed base trials. This verifies why requested
versus applied command accounting matters. It does not show that clamping
causes success: longer task progression can itself create more clamping.
The controller plus limiter is the system being evaluated.

The traces do not contain video, object pose or force. They cannot establish
whether a failure was a missed grasp, premature release, slip, failed transport
or a placement miss. The separation of final jaw positions is a post-hoc
correlate on these trials, not a new success detector.

## Decision

Keep the seed-0 hardware result as an inconclusive positive point estimate.
Run matched base/delta training seeds 1 and 2 with the recipe unchanged,
following real_delta_replication.md. Do not tune on these 40 trials or reinterpret
the excess failure as invalid. No additional hardware session is running.
The raw-delta versus excess contrast changes checkpoint, training preprocessing
and deployment command feedback, so it cannot isolate compensation as the cause.

## Trial-level record of interruptions (moved from the paper appendix, 2026-09-07)

Seed 1 (session 2026-09-06T104356): trials 35 (tracking error) and 37 (base)
completed their 400-step control horizons but reported a gripper overload while
torque was being disabled; both are operator-labeled failures. Trial 35's
outcome was recovered from the operator after the process stopped, but its
trajectory was lost because the cleanup path at the time saved data only after
disconnecting. Saving was moved before disconnect, without changing policy
observations or commanded actions, and trial 37's trajectory was retained.
Evaluation resumed with the original pair identifiers and order (resume
manifests under `results/`).

Seed 2 (session 2026-09-06T165544): twelve labeled rollouts, all failures,
forming six complete pairs; shutdown overloads on trials 8, 10 and 12
(incident files under `results/`). Trial 13 completed its control horizon and
has a trajectory and shutdown-failure record, but its outcome was never
entered (`results/real_delta_v3_s2_trials_pending.json`); the remaining planned
trials were not run. Neither a diagnosis of the recurring overload nor random
missingness has been established.
