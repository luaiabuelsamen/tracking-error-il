"""Reproduce paired outcomes and descriptive trajectory diagnostics, offline."""
import hashlib
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np


def main():
    source = Path("results/real_delta_v3_trials.json")
    rows = json.loads(source.read_text())
    sessions = {r["session"] for r in rows}
    if len(sessions) != 1:
        raise ValueError("Select one session before analysis; do not pool implicitly")
    session = sessions.pop()
    manifest = source.with_name(source.stem + "_" + session.replace(":", "") + "_manifest.json")
    hashes = json.loads(manifest.read_text())["sha256"]
    mismatches = [p for p, h in hashes.items() if hashlib.sha256(Path(p).read_bytes()).hexdigest() != h]
    if mismatches:
        raise ValueError(f"Provenance mismatch: {mismatches}")
    pairs = defaultdict(dict)
    metrics = []
    traces = []
    for r in rows:
        pair, arm = r["pair"], r["arm"]
        if arm in pairs[pair]:
            raise ValueError(f"Duplicate pair/arm: {pair}/{arm}")
        pairs[pair][arm] = int(r["success"])
        z = np.load(Path("results") / r["traj"])
        p, a, applied, obs, elapsed = (z[k] for k in (
            "pos", "action", "applied_action", "observation_state", "elapsed_s"))
        assert len(p) == 400 and all(np.isfinite(x).all() for x in (p, a, applied, obs, elapsed))
        assert np.all(np.diff(elapsed) > 0)
        stats = np.load(Path(r["checkpoint"]) / "norm_stats.npz")
        np.testing.assert_allclose(obs[:, :6], (p - stats["s_mean"]) / stats["s_std"], atol=1e-6)
        if arm == "delta_v3":
            # Handoff command is not in the saved trajectory; audit t>=1.
            np.testing.assert_allclose(obs[1:, 6:], (applied[:-1] - p[1:]) / 8, atol=1e-6)
        clip = np.abs(a - applied) > 1e-3
        metrics.append(dict(pair=pair, arm=arm, success=r["success"],
                            order_in_pair=r["trial"] % 2,
                            hz=float(len(p) / elapsed[-1]),
                            path_joint_units=float(np.abs(np.diff(p, axis=0)).sum()),
                            tail_path_joint_units=float(np.abs(np.diff(p[-100:], axis=0)).sum()),
                            clipped_frame_fraction=float(clip.any(axis=1).mean()),
                            per_joint_clipped_fraction=clip.mean(axis=0).tolist(),
                            final_jaw=float(p[-1, 5])))
        traces.append((r, elapsed, p, clip))
    complete = [v for v in pairs.values() if set(v) == {"base_v2", "delta_v3"}]
    counts = Counter((v["base_v2"], v["delta_v3"]) for v in complete)
    b, d = counts[1, 0], counts[0, 1]
    n = b + d
    pvalue = min(1.0, 2 * sum(math.comb(n, k) for k in range(min(b, d) + 1)) / 2**n) if n else 1.0
    diff = np.array([v["delta_v3"] - v["base_v2"] for v in complete])
    ci = np.quantile(np.random.default_rng(0).choice(diff, (20000, len(diff))).mean(axis=1), [.025, .975])
    groups = {}
    for arm in ("base_v2", "delta_v3"):
        for outcome in (False, True):
            group = [m for m in metrics if m["arm"] == arm and m["success"] == outcome]
            groups[f"{arm}_{'success' if outcome else 'failure'}"] = dict(
                n=len(group), **{key + "_median": float(np.median([m[key] for m in group]))
                                for key in ("hz", "tail_path_joint_units", "clipped_frame_fraction", "final_jaw")})
    order = {f"{arm}_position{pos+1}": [sum(m["success"] for m in metrics if m["arm"] == arm and m["order_in_pair"] == pos),
                                         sum(m["arm"] == arm and m["order_in_pair"] == pos for m in metrics)]
             for arm in ("base_v2", "delta_v3") for pos in (0, 1)}
    report = dict(session=session, complete_pairs=len(complete), incomplete_pairs=len(pairs)-len(complete),
                  base_only=b, delta_only=d, both=counts[1, 1], neither=counts[0, 0],
                  difference=float(diff.mean()), paired_bootstrap_95_ci=ci.tolist(),
                  exact_mcnemar_p=pvalue, groups=groups, order=order,
                  provenance_hashes_verified=len(hashes), saved_observation_parity="passed; delta t>=1",
                  trials=metrics,
                  limitation="No video, object pose or force saved; joint motion cannot identify grasp/drop/crush causes.")
    Path("results/real_delta_v3_diagnostics.json").write_text(json.dumps(report, indent=2) + "\n")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(2, 2, figsize=(10, 6), sharex=True, sharey="row")
    for r, t, p, clip in traces:
        col = 0 if r["arm"] == "base_v2" else 1
        color = "#14856b" if r["success"] else "#c75d42"
        axes[0, col].plot(t, p[:, 5], color=color, alpha=.5, lw=1)
        axes[1, col].plot(t, np.cumsum(clip.any(axis=1)) / np.arange(1, len(t)+1), color=color, alpha=.5, lw=1)
    for col, title in enumerate(("Base: 5/20", "Raw delta: 9/20")):
        axes[0, col].set_title(title)
        axes[1, col].set_xlabel("Seconds after handoff")
    axes[0, 0].set_ylabel("Jaw position (recorded units)")
    axes[1, 0].set_ylabel("Cumulative fraction of steps clamped")
    fig.suptitle("Exploratory trajectories — green: success; orange: failure")
    fig.tight_layout()
    Path("figures").mkdir(exist_ok=True)
    fig.savefig("research/figures/real_delta_v3_diagnostics.png", dpi=160)
    print(json.dumps({k: v for k, v in report.items() if k != "trials"}, indent=2))


if __name__ == "__main__":
    main()
