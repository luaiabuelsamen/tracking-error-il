# Addendum to the 2026-09-07 position-history pre-registration — 2026-11-10

The 2026-09-07 document is kept as written. It is silent on whether pairs from an interrupted session
may be pooled with a later session. This addendum fixes that before the next session.

**Decision: no pooling.** The nine pairs of 2026-09-07 (1/9 tracking error, 0/9 position history,
19 rollouts, four gripper overloads, one displaced camera) stay a separate interrupted record with no
confirmatory test, exactly as the paper reports them. The confirmatory comparison is a fresh 20-pair
session in one sitting, recorded as `results/hardware/real_history_control_s1_trials_v2.json`
(`bash scripts/bench/run_hw_history_control.sh 1 --video --out results/hardware/real_history_control_s1_trials_v2.json`).
`scripts/paper/history_records.py` already enforces this: a confirmatory $p$ requires the exact
planned budget in one session, and versioned records are never merged.

**Reason.** The interrupted session ran on a servo that was faulting and a camera that had moved.
Pooling would mix two plant states inside one paired test, and the nine pairs carry one discordance,
so they could not change the conclusion of a 20-pair test in either direction.

**Before the session.**
- Verify `checkpoints/real50_ghist_v3_s1` and `checkpoints/real50_ghist_v3_s0` against the hashes
  in the 2026-09-07 trial manifests (`results/hardware/real_history_control_s1_trials_*_manifest.json`)
  and rerun the offline observation audit.
- Re-aim the overhead camera against `figures/paper/fig_real_teaser.png`.
- Record a finding in `docs/hardware/overload_diagnosis_2026-11.md`.
- Labels come from the per-trial video by code (`--video`, `scripts/real/label_trials.py`).

The seed-0 secondary comparison (`base_v2` against `ghist_s0`) is unchanged: 20 pairs, one session,
`bash scripts/bench/run_hw_history_control.sh 0 --video`.
