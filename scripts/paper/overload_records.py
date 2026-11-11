"""Gripper overload incidents per policy, read from the frozen hardware records.

The trial runner records a failed rollout exit in two places: the ``shutdown_error`` flag of the
labeled outcome row and an ``*_incident.json`` sidecar with the subprocess return code. A gripper
overload raised by the servo library while torque is being disabled aborts the process (return code
-6, SIGABRT); any other non-zero code is a different failure, such as the logging fault in the
history-control session. A rollout whose outcome was never entered leaves a ``*_pending.json``
incident and no outcome row; it is counted as a rollout with a missing outcome, not dropped.

Reviewer bA2d (CoRL 2026 WEBP, item 6) asked for these counts per policy rather than per session.
"""

from __future__ import annotations

import json
import math
from collections import defaultdict
from pathlib import Path

OVERLOAD_RETURNCODE = -6

# One entry per evaluation record that carries the shutdown-status field. The 2026-09-04 residual
# comparison (real_trials.json) predates the field and is not listed; the seed-0 record predates it
# too but is listed because its runner wrote trajectories only after torque release, so a shutdown
# fault would have left a missing trajectory, and all 40 are present (docs/hardware/diagnostics.md).
RECORDS = (
    dict(key="seed0", label="Tracking error vs.\\ position, seed 0", source="real_delta_v3_trials.json",
         arms={"base_v2": "Position only", "delta_v3": "Tracking error"}),
    dict(key="seed1", label="Tracking error vs.\\ position, seed 1", source="real_delta_v3_s1_trials.json",
         arms={"base_s1": "Position only", "delta_s1": "Tracking error"}),
    dict(key="seed2", label="Tracking error vs.\\ position, seed 2 (interrupted)", source="real_delta_v3_s2_trials.json",
         arms={"base_s2": "Position only", "delta_s2": "Tracking error"}),
    dict(key="history_s1", label="Tracking error vs.\\ position history, seed 1 (interrupted)",
         source="real_history_control_s1_trials.json",
         arms={"delta_s1": "Tracking error", "ghist_s1": "Position history"}),
)


def _fisher_two_sided(a, b, c, d):
    """Exact two-sided Fisher test for the 2x2 table [[a, b], [c, d]] without SciPy."""
    row1, row2, col1 = a + b, c + d, a + c
    n = row1 + row2
    lo, hi = max(0, col1 - row2), min(row1, col1)
    probs = {k: math.comb(row1, k) * math.comb(row2, col1 - k) / math.comb(n, col1) for k in range(lo, hi + 1)}
    observed = probs[a]
    return min(1.0, sum(p for p in probs.values() if p <= observed + 1e-12))


def collect_overloads(root: Path) -> dict:
    out = dict(records=[], by_design={})
    totals = defaultdict(lambda: dict(rollouts=0, overloads=0, other_exits=0, missing_outcomes=0))
    for spec in RECORDS:
        path = root / spec["source"]
        rows = json.loads(path.read_text())
        has_field = any("shutdown_error" in r for r in rows)
        trials = {(r["session"], r["trial"]): r for r in rows}
        incidents = {}
        for inc_path in sorted(root.glob(path.stem + "_*_incident.json")):
            inc = json.loads(inc_path.read_text())
            incidents[(inc["session"], inc["trial"])] = inc
        pending_path = root / (path.stem + "_pending.json")
        pending = []
        if pending_path.exists():
            inc = json.loads(pending_path.read_text())
            if (inc["session"], inc["trial"]) in trials:
                raise ValueError(f"pending incident duplicates a labeled trial: {pending_path.name}")
            pending.append(inc)
        sessions = {r["session"] for r in rows}
        for inc in list(incidents.values()) + pending:
            if inc["session"] not in sessions or inc["arm"] not in spec["arms"]:
                raise ValueError(f"incident outside its record: {inc}")
        per_arm = []
        for arm, design in spec["arms"].items():
            arm_rows = [r for r in rows if r["arm"] == arm]
            arm_pending = [p for p in pending if p["arm"] == arm]
            arm_incidents = [inc for key, inc in incidents.items() if key in trials and trials[key]["arm"] == arm]
            flagged = sum(bool(r.get("shutdown_error")) for r in arm_rows)
            if has_field and flagged != len(arm_incidents):
                raise ValueError(f"{spec['source']} {arm}: {flagged} flagged rows but {len(arm_incidents)} incidents")
            overloads = sum(inc["returncode"] == OVERLOAD_RETURNCODE for inc in arm_incidents + arm_pending)
            other = sum(inc["returncode"] != OVERLOAD_RETURNCODE for inc in arm_incidents + arm_pending)
            if any(not inc.get("rollout_complete") for inc in arm_incidents + arm_pending):
                raise ValueError("an incident interrupted a rollout before its horizon; revise the table caption")
            entry = dict(arm=arm, design=design, rollouts=len(arm_rows) + len(arm_pending), labeled=len(arm_rows),
                         overloads=overloads, other_exits=other, missing_outcomes=len(arm_pending))
            per_arm.append(entry)
            t = totals[design]
            for k in ("rollouts", "overloads", "other_exits", "missing_outcomes"):
                t[k] += entry[k]
        rec = dict(key=spec["key"], label=spec["label"], source=spec["source"], shutdown_field_recorded=has_field,
                   sessions=sorted(sessions), arms=per_arm)
        if spec["key"] == "history_s1":
            a, b = per_arm[0], per_arm[1]
            rec["within_session_fisher_p"] = _fisher_two_sided(
                a["overloads"], a["rollouts"] - a["overloads"], b["overloads"], b["rollouts"] - b["overloads"])
        out["records"].append(rec)
    out["by_design"] = dict(totals)
    return out


def overload_table(data: dict) -> str:
    lines = []
    for rec in data["records"]:
        for i, arm in enumerate(rec["arms"]):
            label = rec["label"] if i == 0 else ""
            missing = str(arm["missing_outcomes"]) if arm["missing_outcomes"] else "0"
            lines.append(f"{label} & {arm['design']} & {arm['rollouts']} & {arm['overloads']} & "
                         f"{arm['other_exits']} & {missing} \\\\")
        lines.append("\\addlinespace")
    lines.pop()
    lines.append("\\midrule")
    for design in ("Position only", "Tracking error", "Position history"):
        t = data["by_design"][design]
        lines.append(f"All records & {design} & {t['rollouts']} & {t['overloads']} & {t['other_exits']} & {t['missing_outcomes']} \\\\")
    return ("\\begin{tabular}{llrrrr}\n\\toprule\n"
            "Evaluation record & Policy & Rollouts & Overload at shutdown & Other failed exit & Outcome missing \\\\\n\\midrule\n"
            + "\n".join(lines) + "\n\\bottomrule\n\\end{tabular}\n")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2] / "results/hardware"
    data = collect_overloads(root)
    print(json.dumps(data, indent=1))
    print(overload_table(data))
