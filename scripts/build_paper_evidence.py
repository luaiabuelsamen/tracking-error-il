"""Generate paper tables and figure directly from frozen trial/grid records."""
import json
import math
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]


def collect():
    hardware = []
    for seed, filename, arms in (
        (0, "real_delta_v3_trials.json", ("base_v2", "delta_v3")),
        (1, "real_delta_v3_s1_trials.json", ("base_s1", "delta_s1")),
        (2, "real_delta_v3_s2_trials.json", ("base_s2", "delta_s2")),
    ):
        rows = json.loads((ROOT / "results" / filename).read_text())
        pairs = defaultdict(dict)
        for r in rows:
            key = (r["session"], r["pair"])
            assert r["arm"] not in pairs[key]
            pairs[key][r["arm"]] = int(r["success"])
        paired = [v for v in pairs.values() if set(v) == set(arms)]
        c = Counter((v[arms[0]], v[arms[1]]) for v in paired)
        b, d = c[1, 0], c[0, 1]
        n = b + d
        p = min(1., 2 * sum(math.comb(n, k) for k in range(min(b, d) + 1)) / 2**n) if n else 1.
        diff = np.array([v[arms[1]] - v[arms[0]] for v in paired])
        ci = np.quantile(np.random.default_rng(0).choice(diff, (20000, len(diff))).mean(1), [.025, .975])
        hardware.append(dict(seed=seed, pairs=len(paired), base=sum(v[arms[0]] for v in paired),
                             delta=sum(v[arms[1]] for v in paired), base_only=b, delta_only=d,
                             both=c[1, 1], neither=c[0, 0], p=p,
                             effect=float(diff.mean()), bootstrap_ci=ci.tolist(),
                             shutdown_errors=sum(bool(r.get("shutdown_error")) for r in rows),
                             missing_trajectories=sum(not (ROOT / "results" / r["traj"]).exists() for r in rows)))
    grids = {}
    for name, pattern in (("Position", "grid_A_base_s*.json"),
                          ("Action history", "grid_B_base_hist_s*.json"),
                          ("Tracking error", "grid_C_delta_s*.json"),
                          ("Auxiliary target", "grid_D_resid_s*.json"),
                          ("Lag excess", "grid_E_excess_s*.json"),
                          ("Seat token", "grid_F_token_s*.json"),
                          ("Position history", "grid_G_ghist_s*.json")):
        vals = []
        for file in sorted((ROOT / "results").glob(pattern)):
            rows = json.loads(file.read_text())["results"]
            r = next(r for r in rows if r["crush"] == -1)
            vals.append(100 * r["success"] / r["episodes"])
        grids[name] = vals
    return dict(hardware=hardware, simulation=grids)


def main():
    data = collect()
    out = ROOT / "paper/generated"
    out.mkdir(exist_ok=True)
    (out / "evidence.json").write_text(json.dumps(data, indent=2) + "\n")
    rows = []
    for r in data["hardware"]:
        status = "Complete" if r["pairs"] == 20 else "Interrupted"
        p = f"{r['p']:.4f}" if r["seed"] != 2 else "---"
        rows.append(f"{r['seed']} & {status} & {r['base']}/{r['pairs']} & {r['delta']}/{r['pairs']} & "
                    f"{r['delta_only']} / {r['base_only']} & {p} " + r"\\")
    (out / "hardware_rows.tex").write_text("\n".join(rows) + "\n")
    (out / "hardware_table.tex").write_text(
        "\\begin{tabular}{llrrrr}\n\\toprule\n"
        + "Seed & Evaluation & Base & Tracking error & Discordances & $p$ \\\\\n\\midrule\n"
        + "\n".join(rows) + "\n\\bottomrule\n\\end{tabular}\n")
    all_table = (out / "hardware_table.tex").read_text()
    (out / "hardware_table_all.tex").write_text(all_table)
    completed_rows = [row for row, r in zip(rows, data["hardware"]) if r["pairs"] == 20]
    (out / "hardware_table.tex").write_text(
        all_table.replace("\n".join(rows), "\n".join(completed_rows)))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                         "axes.spines.top": False, "axes.spines.right": False})
    fig, axes = plt.subplots(1, 2, figsize=(8.1, 2.5), gridspec_kw={"width_ratios": [1.4, 1]})
    order = ["Position", "Position history", "Action history", "Tracking error", "Lag excess"]
    colors = ["#777777", "#aaa08c", "#aaa08c", "#167e83", "#7eb8b4"]
    for i, name in enumerate(order):
        vals = data["simulation"][name]
        axes[0].barh(i, np.mean(vals), color=colors[i], height=.6)
        axes[0].scatter(vals, np.full(len(vals), i), s=13, color="#222222", zorder=3)
    axes[0].set_yticks(range(len(order)), order)
    axes[0].invert_yaxis()
    axes[0].set_xlim(0, 40)
    axes[0].set_xlabel("Placement success (%)")
    axes[0].set_title("Simulation: mean and training seeds", fontsize=10)
    for r in data["hardware"]:
        if r["pairs"] != 20:
            continue
        x = r["seed"]
        for dx, key, color in ((-.18, "base", "#777777"), (.18, "delta", "#167e83")):
            rate = 100*r[key]/r["pairs"]
            axes[1].bar(x+dx, rate, width=.33, color=color)
            axes[1].text(x+dx, rate+2, f"{r[key]}/{r['pairs']}", ha="center", fontsize=8)
    axes[1].set_xticks([0, 1], ["Seed 0", "Seed 1"])
    axes[1].set_ylim(0, 85)
    axes[1].set_ylabel("Placement success (%)")
    axes[1].set_title("Hardware: gray base, teal tracking error", fontsize=10)
    fig.tight_layout(pad=.7)
    path = ROOT / "figures/paper/fig_observation_evidence.pdf"
    fig.savefig(path, bbox_inches="tight")
    fig.savefig(path.with_suffix(".png"), dpi=200, bbox_inches="tight")
    print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
