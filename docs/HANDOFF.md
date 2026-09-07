# Handoff: so101-bench

Written 2026-09-05 for a new collaborator joining mid-project. Assumes no prior
context. Numbers here are verified against the files named beside them.

---

## 1. The idea, from the start

The SO-100/SO-101 is a ~$300 5-DoF arm with a parallel gripper, driven by
Feetech STS3215 hobby servos. It has **no force sensor**, and the standard
imitation-learning stack (LeRobot + ACT) feeds a policy **joint positions
only**. So a learned policy closes the gripper open-loop against contact: it
cannot tell "jaws closed on the object" from "jaws closed on air".

But a position-controlled servo holding against a load sits at an offset from
where it was commanded. That offset

```
delta[t] = a[t-1] - s[t]        # commanded minus measured, encoder counts
```

is a contact signal that is **already present in every recorded log**,
computable retrospectively, needing no sensor, no calibration rig, and no
re-collection. Current stacks compute it nowhere and discard it.

The project asks three things:
1. What does this signal physically measure, and where does it break?
2. Does a policy that observes it do better than one that does not?
3. Is it recoverable from the archived public corpus?

**Verified motivating fact:** of 123 readable archived SO-100/101 datasets
(`research/proprio-residual/data/raw`), **123 record `observation.state` as
6 joint positions only** — no load, no current.

---

## 2. Where the paper stands

`paper/main.tex`, 18 pages, builds to `paper/main.pdf`.
Title: *A Retroactive Contact Channel for Behavior Cloning on Low-Cost Arms*.

### Established (survived a two-day adversarial audit)

| result | numbers | file |
|---|---|---|
| Channel-bearing beats channel-free | **E−A = +20.4**, t=4.68, CI [+11.6,+29.0] | `results/grid_*_s?.json` |
| …and the raw form alone also clears | **C−A = +15.6**, t=3.1, CI [+5.6,+25.2] | same |
| Must be *observed*, not predicted | **D−A = +0.4**, t=0.1 (information-matched) | same |
| δ and `Present_Load` are one signal | `Load = −4.70δ + 0.1`, R²=0.976 [0.969,0.982], n=60 | `appendix_d_stats.py` |
| The register clips at contact, δ doesn't | Load pins at 500 in **16.5%** of frames, all 50 episodes | `real_channel_saturation.py` |
| The cap is stack-wide | addr 48 = 1000 on joints 1–5, **500 on gripper**; LeRobot writes it | `vendor/.../so_follower.py:172-175` |
| Sim envelope | κ = 2.00 N/count, held-out RMSE 4.3 N over 4–78 N | `results/delta_characterization.json` |

**Resolution rule (pre-registered):** a difference is claimable only if it
exceeds `15·sqrt(3/n)` points — **11.62 at n=5, 15.00 at n=3**. Implemented in
`scripts/fig_grid.py:65`, committed 2026-08-18, before any of these cells ran.

### Not established — and this is the honest core

- **δ is not shown to be special.** Arm G observes `[s[t], s[t−8]]` — joint
  history only, from which δ is not computable even in principle — and reaches
  **20.3** against the raw channel arm's 21.8. `G−C = −1.5` (t = −0.29).
  `E−G = +6.3` needs ~18 seeds to resolve; we have 3.
- **All learning results are simulation.** One task, one operating point
  (280 demos, 96 px, 12k steps).
- **At a larger budget the channel's edge is untested.** The one scale cell
  (600 demos, 224 px, 50k steps) compared C against B and they tied (57% vs
  60%, 2 seeds). E has never run there. `results/h100_eval.json`.
- **Hardware policy test failed, on a broken feature** — see §5.

### Reported negatives (deliberate, and in the paper)

- Corpus study: pre-registered prediction that successful grasps carry *higher*
  δ **failed** — high δ at grasp accompanies failure. 16 datasets, 546
  episodes. `results/corpus_delta_outcome.json`.
- Runtime guard: cuts crush events 85→3 of 180 (96%) but removes **every**
  success it had, 12/270 → 0/270 across all nine cells.
  `results/guard_ab.json`, `scripts/guard_pareto.py`.

---

## 3. What to read, in order

1. **`README.md`** — 5 min orientation.
2. **`docs/findings.md`** — the lab record, ~60 dated entries, newest at the
   bottom. This is the single most valuable file in the repo. Every number in
   the paper traces to an entry here.
3. **`paper/main.tex`** — read §Limitations first. It is the most honest part
   and tells you what is actually in doubt.
4. **`docs/task2_arms.md`** — the pre-registered arm definitions, frozen before
   implementation (git tag `prereg-grid` → `d4077d5`).
5. **`docs/roadmap.md`** — open experiments and the pre-submission gate.
6. **`docs/related_table.md`** — positioning against prior work, every cell now
   verified against primary sources.

### Code map

| what | where |
|---|---|
| Sim env + scripted expert | `src/so101_bench/` |
| Sim training / eval (all arms) | `scripts/train_act.py` |
| Arm definitions live here | `train_act.py:118-232` (dataset) and `:428-462` (rollout) |
| Real-arm training | `scripts/train_act_real.py` |
| Real-arm rollout | `scripts/run_policy_real.py` |
| Real-arm paired trials | `scripts/trial_runner.py` |
| Runtime guard | `src/so101_bench/guard.py` |
| Hardware characterisation | `scripts/appendix_d_stats.py`, `real_channel_saturation.py` |
| Corpus study | `scripts/corpus_delta_outcome.py` |

### Data

| dataset | size | what |
|---|---|---|
| `data/demos_v3` | 791 M | the 280-demo sim collection the grid is trained on |
| `data/demos_v4` | 5.4 G | 600-demo sim collection (scale runs) |
| `data/real` | 724 M | **50 real teleop episodes**, 21,476 frames, logs 6 positions + 6 `Present_Load` |

Results are JSON in `results/`, one file per cell, never overwritten.

### Verification tooling — use these before trusting any number

- `python scripts/check_paper_numbers.py` — recomputes 15 load-bearing claims
  from `results/` and fails if `main.tex` no longer matches.
- `python scripts/check_paper_actions.py` — reconciles `docs/findings.md`
  conclusions against the paper; catches the case where the lab record says
  something the paper never absorbed. That happened three times.

---

## 4. Working norms that matter here

These are not bureaucracy; each was bought with a real error.

1. **Pre-register before running.** Decision rules go in a doc, frozen, before
   the cell exists. `docs/task2_arms.md` and `docs/real_trial_prereg.md` are
   the templates. Failed predictions get reported as failures.
2. **Never accept a summariser on presence or absence.** Save the source text
   to disk and grep it literally. An *absence* claim additionally requires
   showing your search terms could have matched the phrasing — I asserted a
   false absence yesterday because my eight patterns could not have matched
   "does not include".
3. **Every citation exported, never typed.** Six bibliography entries were
   found with invented author given names ("Sirui Liu" in three papers that
   have no such author). All fixed; verify any new one against arXiv or
   Crossref.
4. **Attributions get checked, not just quotations.** All three
   misattributions found were paraphrases, not quoted strings.
5. **Recompute independently before endorsing.** Two sessions disagreed four
   times; each was settled by running the data, and each of us was wrong once.

---

## 5. The live situation, and the decision on the table

### What happened tonight

First real-arm paired trial, 20 alternating trials, `--jumpstart 115`:

```
base    7/10
excess  0/10        McNemar exact, two-sided p = 0.0156, favouring base
```

Significant, against the channel. But the diagnostic says it is not a test of
the channel:

`k_hat` is a free-motion **lag coefficient** — the fraction of a commanded step
that appears as tracking error. Physically it must be < 1.

```
simulation        0.79 0.76 0.84 0.84 0.74 0.80    max 0.84
real50_excess_s0  2.28 2.95 3.04 2.20 2.44 1.53    max 3.04   <-- what ran
real50_excess_v2  1.55 0.89 1.07 3.04 1.61 0.24    max 3.04
```

Every joint out of physical range. With k_hat ≈ 3, `excess = δ − 3·rate` is
dominated by command acceleration, not load. The rollouts show the policy
freezing (final-100-step motion 15° vs base's 39°). `docs/real_trial_prereg.md`
named this failure mode **before** the run: *"If excess underperforms, the
k_hat fit is a live alternative explanation before the channel is."* The
free-motion labelling is contaminated — the jaw sits near-closed most of the
time, so ~66% of frames are labelled free-motion including gripping ones.

### The proposed reframe — this is the decision

**Make raw δ the subject of the paper; demote the lag excess to a variant that
did not pay off.**

Rationale: nearly every open problem routes through the lag-excess arm E.

| problem | cause | under raw δ |
|---|---|---|
| k_hat 2.28–3.04, tonight's failure | E needs a fitted lag baseline | **gone** — δ is arithmetic, no fit |
| `a[t−2]` confound in the headline | E's rate term reaches back 2 frames | **gone** — C sees only s[t], a[t−1] |
| resolution-bar awkwardness | E−B sits near the bar | C−A = +15.6 vs bar 11.62 |
| G matching C | genuine | unchanged — remains a specificity limitation |

`delta` is already a supported arm in `train_act_real.py` and
`run_policy_real.py`, and `k_hat` is computed only inside the excess branch —
so a real-arm δ policy needs none of the machinery that broke.

Second half of the reframe: **lead with the measurement, not the policy
result.** The hardware characterisation (§2 table rows 4–6) is the most certain
evidence in the project and nothing that failed touches it, because none of the
failures are about measurement.

### Concrete next steps

1. **Train `real50_delta`** on `data/real` — no k_hat, no refit.
   `python scripts/train_act_real.py --arm delta ...`
2. **Run 20 paired trials** `base_v2` vs `delta` via `scripts/trial_runner.py`
   (needs a human: physical resets and outcome calls). Add a `delta` entry to
   the `CKPT` dict at `trial_runner.py:42`.
3. **`docs/workshop_cut.md`** holds the 4-page plan: one claim, one figure.
   `THESIS.md` rule 6 is the standing instruction — ship workshop/arXiv sized.
4. Running now: 600-demo A-vs-E cells (`results/grid600_*`), ~21 h, the first
   test of channel-versus-channel-free above 280 demos.

### Open questions worth a fresh pair of eyes

- Is the raw-δ reframe right, or is it giving up a real result too easily?
- `E−G` needs ~18 seeds to resolve and nobody has run it. Is it worth ~24 h of
  Orin time, or is the specificity question better left open in Limitations?
- Base scored 7/10 tonight against 2/18 recorded a day earlier. **Nobody knows
  why.** That should be understood before either number is published.
