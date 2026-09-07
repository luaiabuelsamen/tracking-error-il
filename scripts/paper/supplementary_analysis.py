"""Supplementary analyses computed from the frozen records in results/.

Everything here is offline and descriptive or confirmatory on data that already
exists; nothing operates the robot or retrains a policy. Outputs go to
paper/generated/supplementary.json (every number quoted from this script),
paper/generated/*.tex (tables) and figures/paper/ (figures). The paper checker
reads supplementary.json, so numbers in the text cannot drift silently.

Sections
  hardware   per-seed Wilson intervals, stratified exact McNemar over completed
             seeds, conditional odds ratio, discordance heterogeneity, seed-level
             mean difference, order and session-half splits, limiter engagement
  traces     jaw-trace taxonomy for every recorded rollout (never closed /
             closed then reopened / closed and held), time to closure, per-trial
             jaw tracking-error magnitude after closure; figure
  power      exact McNemar power at 20 pairs against discordance structure
  corpus     per-dataset forest plot of Cohen's d with intervals; offset sweep
  measurement static bench Present_Load vs tracking error; demonstration-frame
             gripper load register vs jaw tracking error, with saturation
  simulation all pairwise design contrasts on the 280-demonstration grid with
             Welch intervals, the preregistered resolution rule, Holm adjustment

    MPLCONFIGDIR=/tmp/so101-matplotlib python scripts/paper/supplementary_analysis.py
"""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "paper/generated"
FIG = ROOT / "figures/paper"

SEEDS = (
    (0, "real_delta_v3_trials.json", ("base_v2", "delta_v3")),
    (1, "real_delta_v3_s1_trials.json", ("base_s1", "delta_s1")),
    (2, "real_delta_v3_s2_trials.json", ("base_s2", "delta_s2")),
)
JAW = 5                 # gripper joint index in the recorded 6-vector
CLOSED, REOPENED = 5.0, 8.0   # recorded jaw units; handoff pose sits at ~12.4, closed at ~2
PLAN_PAIRS = 20

plt = None


def _plt():
    global plt
    if plt is None:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as _p
        _p.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8,
                            "axes.spines.top": False, "axes.spines.right": False})
        plt = _p
    return plt


# ----------------------------------------------------------------------------- stats helpers
def wilson(k, n, z=1.959964):
    if n == 0:
        return [0.0, 0.0]
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [centre - half, centre + half]


def exact_mcnemar(b, d):
    n = b + d
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(math.comb(n, k) for k in range(min(b, d) + 1)) / 2 ** n)


def clopper_pearson(k, n, alpha=0.05):
    lo = 0.0 if k == 0 else stats.beta.ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else stats.beta.ppf(1 - alpha / 2, k + 1, n - k)
    return [float(lo), float(hi)]


def mcnemar_power(n_pairs, p_disc, q, alpha=0.05):
    """P(reject) for exact two-sided McNemar: m ~ Bin(n, p_disc) discordant pairs,
    of which d ~ Bin(m, q) favour the treatment."""
    power = 0.0
    for m in range(n_pairs + 1):
        pm = stats.binom.pmf(m, n_pairs, p_disc)
        if pm < 1e-12:
            continue
        for d in range(m + 1):
            if exact_mcnemar(m - d, d) < alpha:
                power += pm * stats.binom.pmf(d, m, q)
    return float(power)


def welch(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    diff = a.mean() - b.mean()
    va, vb = a.var(ddof=1) / len(a), b.var(ddof=1) / len(b)
    se = math.sqrt(va + vb)
    df = (va + vb) ** 2 / (va ** 2 / (len(a) - 1) + vb ** 2 / (len(b) - 1))
    t = diff / se
    p = 2 * stats.t.sf(abs(t), df)
    h = stats.t.ppf(0.975, df) * se
    return dict(diff=float(diff), t=float(t), df=float(df), p=float(p), ci=[float(diff - h), float(diff + h)])


def holm(pvals):
    order = np.argsort(pvals)
    m = len(pvals)
    adj = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * pvals[idx])
        adj[idx] = min(1.0, running)
    return adj.tolist()


# ----------------------------------------------------------------------------- hardware + traces
def classify(jaw):
    closed = np.flatnonzero(jaw < CLOSED)
    if len(closed) == 0:
        return "never_closed", None, None
    first = int(closed[0])
    reopen = np.flatnonzero(jaw[first:] > REOPENED)
    if len(reopen):
        return "closed_then_reopened", first, int(first + reopen[0])
    return "closed_and_held", first, None


def hardware():
    per_seed, trials = [], []
    for seed, filename, arms in SEEDS:
        rows = json.loads((ROOT / "results/hardware" / filename).read_text())
        pairs = defaultdict(dict)
        for r in rows:
            pairs[(r["session"], r["pair"])][r["arm"]] = int(r["success"])
            arm = "base" if r["arm"].startswith("base") else "delta"
            t = dict(seed=seed, arm=arm, pair=r["pair"], trial=r["trial"], order_in_pair=r["trial"] % 2,
                     success=int(r["success"]), shutdown_error=bool(r.get("shutdown_error")),
                     session_half=int(r["pair"] >= PLAN_PAIRS // 2))
            path = ROOT / "results/hardware" / r["traj"]
            if path.exists():
                z = np.load(path)
                pos, act, applied = z["pos"], z["action"], z["applied_action"]
                jaw = pos[:, JAW]
                cls, first, reopen = classify(jaw)
                # tracking error of the jaw, computed from the applied command exactly as the
                # policy input is (applied[t-1] - pos[t]); defined for every arm
                delta_jaw = applied[:-1, JAW] - pos[1:, JAW]
                after = delta_jaw[first:] if first is not None else delta_jaw[:0]
                clip = np.abs(act - applied) > 1e-3
                t.update(trajectory=True, jaw_class=cls, first_close_step=first, reopen_step=reopen,
                         final_jaw=float(jaw[-1]), min_jaw=float(jaw.min()),
                         tail_path_joint_units=float(np.abs(np.diff(pos[-100:], axis=0)).sum()),
                         clipped_frame_fraction=float(clip.any(axis=1).mean()),
                         mean_abs_delta_jaw_after_close=float(np.abs(after).mean()) if len(after) else None,
                         steps=int(len(pos)), seconds=float(z["elapsed_s"][-1]))
            else:
                t.update(trajectory=False, jaw_class=None)
            trials.append(t)
        paired = [v for v in pairs.values() if set(v) == set(arms)]
        c = Counter((v[arms[0]], v[arms[1]]) for v in paired)
        b, d = c[1, 0], c[0, 1]
        base = sum(v[arms[0]] for v in paired)
        delta = sum(v[arms[1]] for v in paired)
        n = len(paired)
        per_seed.append(dict(seed=seed, pairs=n, complete=n == PLAN_PAIRS, base=base, delta=delta,
                             base_wilson=wilson(base, n), delta_wilson=wilson(delta, n),
                             base_only=b, delta_only=d, both=c[1, 1], neither=c[0, 0],
                             discordant=b + d, mcnemar_p=exact_mcnemar(b, d),
                             difference=(delta - base) / n if n else 0.0))
    completed = [s for s in per_seed if s["complete"]]
    B = sum(s["base_only"] for s in completed)
    D = sum(s["delta_only"] for s in completed)
    # stratified exact McNemar: under H0 every discordant pair is 50/50 in every stratum
    strat_p = exact_mcnemar(B, D)
    q_ci = clopper_pearson(D, B + D)
    odds = dict(estimate=D / B if B else math.inf,
                ci=[q_ci[0] / (1 - q_ci[0]), (q_ci[1] / (1 - q_ci[1])) if q_ci[1] < 1 else math.inf])
    table = [[s["delta_only"], s["base_only"]] for s in completed]
    heterogeneity_p = float(stats.fisher_exact(table)[1])
    diffs_completed = [s["difference"] for s in completed]
    diffs_all = [s["difference"] for s in per_seed]
    def summarise(x):
        x = np.asarray(x, float)
        out = dict(n=len(x), mean=float(x.mean()))
        if len(x) > 1:
            sd = float(x.std(ddof=1))
            out.update(sd=sd, t=float(x.mean() / (sd / math.sqrt(len(x)))) if sd else math.inf,
                       ci=[float(v) for v in stats.t.interval(0.95, len(x) - 1, loc=x.mean(), scale=sd / math.sqrt(len(x)))] if sd else None)
        return out
    order = {}
    for seed in (0, 1):
        for arm in ("base", "delta"):
            for key, label in (("order_in_pair", "first_in_pair"), ("session_half", "second_half")):
                for val in (0, 1):
                    grp = [t for t in trials if t["seed"] == seed and t["arm"] == arm and t[key] == val]
                    order[f"seed{seed}_{arm}_{label}={val}"] = [sum(t["success"] for t in grp), len(grp)]
    limiter = {}
    for seed in (0, 1, 2):
        for arm in ("base", "delta"):
            grp = [t for t in trials if t["seed"] == seed and t["arm"] == arm and t["trajectory"]]
            limiter[f"seed{seed}_{arm}"] = dict(n=len(grp), median_clipped_frame_fraction=float(np.median([t["clipped_frame_fraction"] for t in grp])))
    taxonomy = {}
    for seed in (0, 1, 2):
        for arm in ("base", "delta"):
            for outcome in (1, 0):
                grp = [t for t in trials if t["seed"] == seed and t["arm"] == arm and t["success"] == outcome and t["trajectory"]]
                cnt = Counter(t["jaw_class"] for t in grp)
                closes = [t["first_close_step"] for t in grp if t["first_close_step"] is not None]
                dj = [t["mean_abs_delta_jaw_after_close"] for t in grp if t["mean_abs_delta_jaw_after_close"] is not None]
                taxonomy[f"seed{seed}_{arm}_{'success' if outcome else 'failure'}"] = dict(
                    n=len(grp), never_closed=cnt["never_closed"], closed_then_reopened=cnt["closed_then_reopened"],
                    closed_and_held=cnt["closed_and_held"],
                    median_first_close_step=float(np.median(closes)) if closes else None,
                    median_abs_delta_jaw_after_close=float(np.median(dj)) if dj else None,
                    median_tail_path=float(np.median([t["tail_path_joint_units"] for t in grp])) if grp else None)
    return dict(per_seed=per_seed, stratified=dict(base_only=B, delta_only=D, exact_p=strat_p,
                                                   conditional_odds_ratio=odds, heterogeneity_fisher_p=heterogeneity_p),
                seed_level=dict(completed=summarise(diffs_completed), all_three=summarise(diffs_all)),
                order=order, limiter=limiter, taxonomy=taxonomy), trials


def power_table():
    grid = {}
    for p_disc in (0.2, 0.4, 0.6, 0.8):
        for q in (0.7, 0.8, 0.9, 1.0):
            grid[f"p_disc={p_disc},q={q}"] = mcnemar_power(PLAN_PAIRS, p_disc, q)
    # observed structures: seed 0 had 8 discordant of 20 with 6 favouring; seed 1 had 15 with 14
    observed = {f"seed{seed}": mcnemar_power(PLAN_PAIRS, m / PLAN_PAIRS, d / m)
                for seed, m, d in ((0, 8, 6), (1, 15, 14))}
    return dict(pairs=PLAN_PAIRS, alpha=0.05, grid=grid, at_observed_structure=observed)


# ----------------------------------------------------------------------------- corpus
def corpus():
    rows = [r for r in json.loads((ROOT / "results/corpus/corpus_delta_outcome.json").read_text()) if r.get("cohen_d") is not None]
    sweep = {r["name"]: r for r in json.loads((ROOT / "results/corpus/offset_sweep.json").read_text())}
    rows.sort(key=lambda r: r["cohen_d"])
    shifts = [abs(sweep[r["name"]]["cohen_d_by_k"][-1] - sweep[r["name"]]["cohen_d_by_k"][0]) for r in rows if r["name"] in sweep]
    weighted = float(np.average([r["cohen_d"] for r in rows], weights=[r["episodes"] for r in rows]))
    p = _plt()
    fig, (ax, ax2) = p.subplots(1, 2, figsize=(8.1, 3.6), gridspec_kw={"width_ratios": [1.5, 1]})
    y = np.arange(len(rows))
    for i, r in enumerate(rows):
        lo, hi = r["d_ci"]
        color = "#167e83" if r["cohen_d"] > 0.5 else "#777777"
        ax.plot([max(lo, -6), min(hi, 6)], [i, i], color=color, lw=1)
        ax.scatter(np.clip(r["cohen_d"], -6, 6), i, s=10 + r["episodes"] / 4, color=color, zorder=3)
    ax.axvline(0, color="#222222", lw=.6)
    ax.axvline(0.5, color="#c75d42", lw=.8, ls="--")
    ax.set_yticks(y, [r["name"].split("__", 1)[-1][:28] for r in rows], fontsize=6)
    ax.set_xlim(-6, 6)
    ax.set_xlabel("Cohen's $d$ (successful $-$ failed episodes), clipped to $\\pm6$")
    ax.set_title("Per-dataset effect of tracking error at grasp onset", fontsize=9, loc="left")
    for r in rows:
        if r["name"] in sweep:
            ax2.plot(range(6), sweep[r["name"]]["cohen_d_by_k"], color="#777777", alpha=.6, lw=.8)
    ax2.axhline(0.5, color="#c75d42", lw=.8, ls="--")
    ax2.set_ylim(-3, 3)
    ax2.set_xlabel("Assumed command offset $k$ (frames)")
    ax2.set_ylabel("Cohen's $d$")
    ax2.set_title("Offset sweep", fontsize=9, loc="left")
    fig.tight_layout(pad=.6)
    fig.savefig(FIG / "fig_corpus.pdf", bbox_inches="tight")
    fig.savefig(FIG / "fig_corpus.png", dpi=200, bbox_inches="tight")
    p.close(fig)
    return dict(datasets=len(rows), episodes=sum(r["episodes"] for r in rows),
                above_threshold=sum(r["cohen_d"] > 0.5 for r in rows),
                negative_point_estimates=sum(r["cohen_d"] < 0 for r in rows),
                ci_excludes_zero_negative=sum(r["d_ci"][1] < 0 for r in rows),
                ci_excludes_zero_positive=sum(r["d_ci"][0] > 0 for r in rows),
                episode_weighted_mean_d=weighted, median_offset_shift=float(np.median(shifts)))


# ----------------------------------------------------------------------------- measurement context
def measurement():
    st = np.load(ROOT / "results/calibration/staircase_channel_j2.npz", allow_pickle=True)
    delta = (st["goal"] - st["position"]).ravel()
    load = st["load"].ravel()
    slope, icpt, r, *_ = stats.linregress(delta, load)
    out = dict(static=dict(measurements=int(delta.size), slope=float(slope), intercept=float(icpt), r2=float(r * r)))
    demo = None
    parquet = sorted((ROOT / "data/real/pickplace_real_v0/data").glob("**/*.parquet"))
    if parquet:
        import pandas as pd
        df = pd.concat([pd.read_parquet(f) for f in parquet]).sort_values(["episode_index", "frame_index"])
        state = np.stack(df["observation.state"].to_numpy())
        action = np.stack(df["action"].to_numpy())
        ep = df["episode_index"].to_numpy()
        same = ep[1:] == ep[:-1]
        d_jaw = (action[:-1, JAW] - state[1:, JAW])[same]
        load_jaw = state[1:, 6 + JAW][same]
        sat = np.abs(load_jaw) >= 499.5
        ep_pairs = ep[1:][same]
        demo = dict(frames=int(len(load_jaw)), episodes=int(len(np.unique(ep))),
                    saturated_fraction=float(sat.mean()),
                    episodes_touching_saturation=int(len(np.unique(ep_pairs[sat]))),
                    corr_load_delta_jaw=float(np.corrcoef(d_jaw, load_jaw)[0, 1]),
                    delta_jaw_sd_when_saturated=float(d_jaw[np.abs(load_jaw) >= 499.5].std()),
                    delta_jaw_sd_when_not_saturated=float(d_jaw[np.abs(load_jaw) < 499.5].std()))
        out["demonstrations"] = demo
    p = _plt()
    fig, axes = p.subplots(1, 2, figsize=(8.1, 3.0))
    axes[0].scatter(delta, load, s=10, color="#167e83", alpha=.7)
    xs = np.linspace(delta.min(), delta.max(), 2)
    axes[0].plot(xs, slope * xs + icpt, color="#222222", lw=.8)
    axes[0].set_xlabel("Tracking error $\\delta$ (encoder counts)")
    axes[0].set_ylabel("Present\\_Load (register units)")
    axes[0].set_title(f"Static bench, one joint: 12 masses $\\times$ 5 poses, $R^2={r*r:.3f}$", fontsize=9, loc="left")
    if demo is not None:
        axes[1].hexbin(d_jaw, load_jaw, gridsize=45, bins="log", cmap="Greys", linewidths=0)
        axes[1].axhline(500, color="#c75d42", lw=.8, ls="--")
        axes[1].axhline(-500, color="#c75d42", lw=.8, ls="--")
        axes[1].set_xlabel("Jaw tracking error (recorded units)")
        axes[1].set_ylabel("Jaw Present\\_Load")
        axes[1].set_title(f"Teleoperation frames: {100*demo['saturated_fraction']:.1f}% at the $\\pm500$ limit", fontsize=9, loc="left")
    fig.tight_layout(pad=.6)
    fig.savefig(FIG / "fig_measurement.pdf", bbox_inches="tight")
    fig.savefig(FIG / "fig_measurement.png", dpi=200, bbox_inches="tight")
    p.close(fig)
    return out


# ----------------------------------------------------------------------------- simulation contrasts
DESIGNS = [("Position", "grid_A_base_s*.json"), ("Position history", "grid_G_ghist_s*.json"),
           ("Action history", "grid_B_base_hist_s*.json"), ("Two-command history", "grid_H_base_hist2_s*.json"),
           ("Tracking error", "grid_C_delta_s*.json"), ("Compensated residual", "grid_E_excess_s*.json"),
           ("Auxiliary target", "grid_D_resid_s*.json"), ("Seat token", "grid_F_token_s*.json")]


def simulation():
    vals = {}
    for name, pattern in DESIGNS:
        v = []
        for f in sorted((ROOT / "results/simulation").glob(pattern)):
            r = next(r for r in json.loads(f.read_text())["results"] if r["crush"] == -1)
            v.append(100 * r["success"] / r["episodes"])
        vals[name] = v
    contrasts = []
    names = [n for n, _ in DESIGNS]
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            w = welch(vals[b], vals[a])   # b minus a, matching the table label
            n = min(len(vals[a]), len(vals[b]))
            rule = 15 * math.sqrt(3 / n)
            contrasts.append(dict(a=a, b=b, n_a=len(vals[a]), n_b=len(vals[b]), resolution_rule=rule,
                                  resolved=abs(w["diff"]) >= rule, **w))
    adj = holm([c["p"] for c in contrasts])
    for c, pa in zip(contrasts, adj):
        c["holm_p"] = pa
    return dict(per_seed=vals, means={k: float(np.mean(v)) for k, v in vals.items()}, contrasts=contrasts)


# ----------------------------------------------------------------------------- figures + tables
def trace_figure(trials):
    p = _plt()
    fig, axes = p.subplots(3, 2, figsize=(8.1, 6.2), sharex=True, sharey=True)
    for t in trials:
        if not t["trajectory"]:
            continue
        for seed, filename, _arms in SEEDS:
            if seed == t["seed"]:
                rows = json.loads((ROOT / "results/hardware" / filename).read_text())
                r = next(r for r in rows if r["trial"] == t["trial"])
        z = np.load(ROOT / "results/hardware" / r["traj"])
        ax = axes[t["seed"], 0 if t["arm"] == "base" else 1]
        ax.plot(z["pos"][:, JAW], color="#14856b" if t["success"] else "#c75d42", alpha=.55, lw=.9)
    per = {s["seed"]: s for s in hardware_cache["per_seed"]}
    for seed in range(3):
        for col, arm, label in ((0, "base", "Position only"), (1, "delta", "Tracking error")):
            s = per[seed]
            k = s[arm]
            title = f"Seed {seed}, {label}: {k}/{s['pairs']}" + (" (interrupted)" if not s["complete"] else "")
            axes[seed, col].set_title(title, fontsize=9, loc="left")
        axes[seed, 0].set_ylabel("Jaw position (recorded units)")
    for ax in axes[-1]:
        ax.set_xlabel("Policy step after handoff")
    axes[0, 0].axhline(CLOSED, color="#222222", lw=.5, ls=":")
    fig.tight_layout(pad=.5)
    fig.savefig(FIG / "fig_hardware_traces.pdf", bbox_inches="tight")
    fig.savefig(FIG / "fig_hardware_traces.png", dpi=200, bbox_inches="tight")
    p.close(fig)


def fmt_ci(ci, scale=100, digits=0):
    return f"[{ci[0]*scale:+.{digits}f}, {ci[1]*scale:+.{digits}f}]"


def tables(hw, power, sim):
    rows = []
    for s in hw["per_seed"]:
        status = "Complete" if s["complete"] else "Interrupted"
        p = f"{s['mcnemar_p']:.4f}" if s["complete"] else "---"
        rows.append(f"{s['seed']} & {status} & {s['base']}/{s['pairs']} {fmt_ci(s['base_wilson'])} & "
                    f"{s['delta']}/{s['pairs']} {fmt_ci(s['delta_wilson'])} & "
                    f"{s['delta_only']} / {s['base_only']} & {s['both']} / {s['neither']} & {p} \\\\")
    st = hw["stratified"]
    o = st["conditional_odds_ratio"]
    hi = f"{o['ci'][1]:.1f}" if math.isfinite(o["ci"][1]) else "$\\infty$"
    rows.append("\\midrule")
    rows.append(f"0+1 & Stratified & & & {st['delta_only']} / {st['base_only']} & & {st['exact_p']:.4f} \\\\")
    (GEN / "hardware_table_ci.tex").write_text(
        "\\begin{tabular}{llllrrr}\n\\toprule\n"
        "Seed & Evaluation & Base [95\\% CI] & Tracking error [95\\% CI] & TE / base only & both / neither & $p$ \\\\\n\\midrule\n"
        + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
    (GEN / "odds_ratio.tex").write_text(f"{o['estimate']:.1f} (95\\% CI {o['ci'][0]:.1f} to {hi})")

    tax = hw["taxonomy"]
    lines = []
    for seed in range(3):
        for arm, label in (("base", "Position only"), ("delta", "Tracking error")):
            for outcome in ("success", "failure"):
                t = tax[f"seed{seed}_{arm}_{outcome}"]
                if t["n"] == 0:
                    continue
                close = f"{t['median_first_close_step']:.0f}" if t["median_first_close_step"] is not None else "---"
                lines.append(f"{seed} & {label} & {outcome} & {t['n']} & {t['never_closed']} & "
                             f"{t['closed_then_reopened']} & {t['closed_and_held']} & {close} \\\\")
    (GEN / "trace_taxonomy.tex").write_text(
        "\\begin{tabular}{lllrrrrr}\n\\toprule\n"
        "Seed & Policy & Outcome & $n$ & never closed & closed, reopened & closed, held & median step of closure \\\\\n\\midrule\n"
        + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n")

    g = power["grid"]
    pl = []
    for p_disc in (0.2, 0.4, 0.6, 0.8):
        cells = " & ".join(f"{g[f'p_disc={p_disc},q={q}']:.2f}" for q in (0.7, 0.8, 0.9, 1.0))
        pl.append(f"{p_disc:.1f} & {cells} \\\\")
    (GEN / "power_table.tex").write_text(
        "\\begin{tabular}{lrrrr}\n\\toprule\n"
        "P(discordant) & $q=0.7$ & $q=0.8$ & $q=0.9$ & $q=1.0$ \\\\\n\\midrule\n"
        + "\n".join(pl) + "\n\\bottomrule\n\\end{tabular}\n")

    sl = []
    keep = {("Position", "Tracking error"), ("Position", "Position history"), ("Position", "Action history"),
            ("Position", "Compensated residual"), ("Position history", "Tracking error"), ("Action history", "Tracking error"),
            ("Tracking error", "Compensated residual"), ("Position history", "Compensated residual"),
            ("Two-command history", "Compensated residual"), ("Position", "Auxiliary target")}
    for c in sim["contrasts"]:
        if (c["a"], c["b"]) not in keep:
            continue
        mark = "yes" if c["resolved"] else "no"
        sl.append(f"{c['b']} $-$ {c['a']} & {c['diff']:+.1f} & [{c['ci'][0]:+.1f}, {c['ci'][1]:+.1f}] & "
                  f"{c['p']:.3f} & {c['holm_p']:.2f} & {c['resolution_rule']:.1f} & {mark} \\\\")
    (GEN / "sim_contrasts.tex").write_text(
        "\\begin{tabular}{lrlrrrl}\n\\toprule\n"
        "Contrast & Points & Welch 95\\% CI & $p$ & Holm $p$ & Rule & Clears \\\\\n\\midrule\n"
        + "\n".join(sl) + "\n\\bottomrule\n\\end{tabular}\n")


hardware_cache = None


def main():
    global hardware_cache
    GEN.mkdir(exist_ok=True)
    hw, trials = hardware()
    hardware_cache = hw
    power = power_table()
    trace_figure(trials)
    corp = corpus()
    meas = measurement()
    sim = simulation()
    tables(hw, power, sim)
    out = dict(hardware=hw, power=power, corpus=corp, measurement=meas, simulation=sim,
               thresholds=dict(closed_below=CLOSED, reopened_above=REOPENED))
    (GEN / "supplementary.json").write_text(json.dumps(out, indent=2, default=float) + "\n")
    print(json.dumps(dict(stratified=hw["stratified"], seed_level=hw["seed_level"],
                          taxonomy={k: (v["never_closed"], v["closed_then_reopened"], v["closed_and_held"]) for k, v in hw["taxonomy"].items()},
                          power=power["at_observed_structure"], corpus=corp, measurement=meas,
                          contrasts={f"{c['b']}-{c['a']}": (round(c['diff'], 1), round(c['p'], 3), round(c['holm_p'], 2), c['resolved']) for c in sim["contrasts"]}),
                     indent=1, default=float))


if __name__ == "__main__":
    main()
