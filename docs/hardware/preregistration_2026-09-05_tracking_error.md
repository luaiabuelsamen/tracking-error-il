# Raw delta hardware screen — 2026-09-05

Written before training real50_delta_v3_s0 or observing its hardware outcomes.

Compare checkpoints/real50_base_v2 with checkpoints/real50_delta_v3_s0.
Both use data/real/pickplace_real_v0, stationary-prefix trimming, 96 px,
6,000 steps, batch 8, learning rate 0.0001, seed 0. Base provenance is its
saved training summary and the historical run_v2.sh (defaults supply LR/size).
Delta saves all CLI arguments. This is a one-checkpoint-per-arm screen, not
an estimate across training seeds or evidence of superiority over history.

Gate: offline training/deployment observation parity must pass. Recorded
commands must be interpreted cautiously until collection-time clipping is
known. Deployment now feeds back the command returned by send_action, after
the relative-target limit, and saves requested and applied commands separately.
This changes the execution protocol from the earlier excess session; report
that session separately, without retrospectively invalidating its outcome.

Run 20 matched pairs (40 total rollouts), with AB then BA order alternating
across pairs; reset the object and arm identically within each pair. Use
jumpstart episode 0, 115 frames, max_steps 400, relative target limit 8.0,
the same camera and setup. Success means adapter placed in the tape roll.
Do not stop early based on outcomes. Technical failures are documented with
their reason, never discarded because the policy fails. If a technical failure
leaves an incomplete pair, retain its record and exclude the pair from the
paired test; report the reduced denominator. Abort a session if pipeline
integrity is uncertain and label it incomplete rather than pooling silently.

Primary: paired delta-minus-base success difference and exact two-sided
McNemar p-value from discordant pairs. Report all four paired outcome counts
and a paired bootstrap 95% interval (20,000 resamples, seed 0) for the difference.
Claim a checkpoint-level improvement only with positive difference and p<0.05.
Five unanimous discordances give p=0.0625; six give p=0.03125. A null is
inconclusive, not equivalence. Positive results require independent training
seed replication before a general method claim. No post-hoc threshold changes.

Prepared command (only after training completes and operator is ready):

```bash
/home/jetson3/projects/clean_env/venv/bin/python scripts/real/trial_runner.py --arms base_v2,delta_v3 --paired --trials 40 --jumpstart 115 --max-steps 400 --out results/hardware/real_delta_v3_trials.json
```

Open provenance: yesterday's versus today's baseline success shift, and whether
collection enabled relative-target clipping. Neither is explained by current
trial records, which lack checkpoint hashes and applied commands.

Operator follow-up, 2026-09-05: the operator reports nothing changed between
yesterday's and today's sessions. This is reported setup consistency, not an
explanation of the success-rate shift. Collection-time command limiting has
not been established by this response.
