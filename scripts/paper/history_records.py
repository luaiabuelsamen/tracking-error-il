"""Read each registered hardware-history evaluation record without pooling reruns."""

from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


def collect_history(root: Path, plan_pairs: int = 20) -> dict:
    """Keep interrupted records and versioned reruns as separate comparisons.

    An outcome is counted only when both arms have operator-entered Boolean
    labels in the same session and pair. A confirmatory p-value requires the
    exact planned budget in one session; an incomplete record has no test.
    """
    output = {}
    for seed, arms in ((1, ("delta_s1", "ghist_s1")), (0, ("base_v2", "ghist_s0"))):
        pattern = re.compile(
            rf"real_history_control_s{seed}_trials(?:_v([2-9]|[1-9][0-9]+))?\.json"
        )
        files = []
        for path in root.glob(f"real_history_control_s{seed}_trials*.json"):
            match = pattern.fullmatch(path.name)
            if match:
                files.append((int(match[1] or 1), path))
        comparisons = []
        seen_trials = set()
        for version, path in sorted(files):
            rows = json.loads(path.read_text())
            pairs = defaultdict(dict)
            for row in rows:
                key = (row["session"], row["trial"])
                if key in seen_trials:
                    raise ValueError(f"duplicate history trial across records: {key}")
                seen_trials.add(key)
                if row["arm"] not in arms or type(row["success"]) is not bool:
                    raise ValueError(f"invalid arm or non-Boolean outcome in {path.name}")
                pair = pairs[(row["session"], row["pair"])]
                if row["arm"] in pair:
                    raise ValueError(f"duplicate arm within history pair in {path.name}")
                pair[row["arm"]] = int(row["success"])
            paired = [pair for pair in pairs.values() if set(pair) == set(arms)]
            if len(paired) > plan_pairs:
                raise ValueError(f"history record exceeds the registered budget: {path.name}")
            counts = Counter((pair[arms[0]], pair[arms[1]]) for pair in paired)
            first_only, history_only = counts[1, 0], counts[0, 1]
            sessions = sorted({row["session"] for row in rows})
            complete = (
                len(paired) == plan_pairs and len(rows) == 2 * plan_pairs and len(sessions) == 1
            )
            pvalue = None
            if complete:
                n = first_only + history_only
                pvalue = (
                    min(
                        1.0,
                        2
                        * sum(math.comb(n, k) for k in range(min(first_only, history_only) + 1))
                        / 2**n,
                    )
                    if n
                    else 1.0
                )
            trial_keys = {(row["session"], row["trial"]) for row in rows}
            incidents = {}
            for incident_path in root.glob(path.stem + "_*_incident.json"):
                incident = json.loads(incident_path.read_text())
                key = (incident["session"], incident["trial"])
                if key in trial_keys:
                    incidents[key] = incident
            comparisons.append(
                dict(
                    seed=seed,
                    arms=list(arms),
                    version=version,
                    source=path.name,
                    sessions=sessions,
                    pairs=len(paired),
                    rollouts=len(rows),
                    unpaired_rollouts=len(rows) - 2 * len(paired),
                    first=sum(pair[arms[0]] for pair in paired),
                    history=sum(pair[arms[1]] for pair in paired),
                    first_only=first_only,
                    history_only=history_only,
                    mcnemar_p=pvalue,
                    shutdown_errors=sum(bool(row.get("shutdown_error")) for row in rows),
                    abort_incidents=sum(
                        incident.get("returncode") == -6 for incident in incidents.values()
                    ),
                    other_incidents=sum(
                        incident.get("returncode") != -6 for incident in incidents.values()
                    ),
                    status="evaluated" if complete else "interrupted",
                )
            )
        log = root / "real_delta_replication" / f"ghist_s{seed}.log"
        trained = log.exists() and "saved checkpoints/" in log.read_text()
        if any(record["status"] == "evaluated" for record in comparisons):
            status = "evaluated"
        elif comparisons:
            status = "interrupted"
        else:
            status = "trained, not evaluated" if trained else "checkpoint not trained"
        output[f"seed{seed}"] = dict(
            seed=seed, arms=list(arms), status=status, comparisons=comparisons
        )
    return output
