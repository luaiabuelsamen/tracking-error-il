# Hardware seed-0 result and trajectory audit — 2026-09-05

Session 2026-09-05T18:50:04: 40 recorded rollouts, 20 complete matched pairs,
all 400 steps long, all trajectories present. Base_v2 succeeds 5/20 and
delta_v3 succeeds 9/20. Paired counts: both 3, neither 9, base only 2,
delta only 6. Delta minus base = +20 percentage points; exact two-sided
McNemar p=0.2890625; paired percentile bootstrap 95% interval [-5,+45]
points (20,000 resamples, seed 0). This does not meet the registered rule.

Reproduce with scripts/real/analyze_real_delta_trials.py. Outputs:
results/hardware/real_delta_v3_diagnostics.json and figures/diagnostics/real_delta_v3_seed0.png.
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
entered (`results/hardware/real_delta_v3_s2_trials_pending.json`); the remaining planned
trials were not run. Neither a diagnosis of the recurring overload nor random
missingness has been established.

## Position-history control, seed 1 — 2026-09-07 (interrupted)

Two sessions (13:18 and 14:10 local) against the pre-registration of the same
day, 19 rollouts in total, before the operator stopped. Four rollouts ended
with a gripper overload error at torque disable (trials 7, 8 and 11 of the
first session and trial 3 of the second); in
trials 4, 8 and 13 the applied jaw command reached about 6 units while the
measured jaw stayed at the 12.4-unit handoff value for 40 steps, so the servo
was not following its command. Trial 9's rollout completed normally but its
trajectory file was not saved because the analyst moved the trajectory
directory during the session (recorded in the incident file; not a servo
fault). A frame captured from the overhead camera at 13:57 is displaced about
30 px vertically and panned right relative to the frame of the 11:35 showcase
rollout that placed the adapter with the same tracking-error checkpoint. All
outcomes are retained; the comparison is reported as interrupted and no
confirmatory test is assigned. Before the next attempt: cool and power-cycle
the gripper servo or replace it, and re-aim the camera against
`figures/paper/fig_real_teaser.png`.
