"""Protect evaluation denominators, interruption handling, and measured timing."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "paper"))
import split_submission  # noqa: E402
from history_records import collect_history  # noqa: E402
from supplementary_analysis import timestamp_summary  # noqa: E402


def history_rows(session, pairs, history_success=False):
    return [
        dict(
            session=session,
            trial=2 * pair + index,
            pair=pair,
            arm=arm,
            success=history_success if index else True,
            shutdown_error=False,
        )
        for pair in range(pairs)
        for index, arm in enumerate(("delta_s1", "ghist_s1"))
    ]


def test_incomplete_history_has_no_test_and_keeps_unpaired_outcome(tmp_path):
    rows = history_rows("interrupted", 9) + history_rows("unpaired", 1)[:1]
    (tmp_path / "real_history_control_s1_trials.json").write_text(json.dumps(rows))
    result = collect_history(tmp_path)["seed1"]["comparisons"][0]
    assert result["pairs"] == 9
    assert result["rollouts"] == 19
    assert result["unpaired_rollouts"] == 1
    assert result["first"] == 9
    assert result["mcnemar_p"] is None


def test_versioned_rerun_remains_separate_from_interrupted_record(tmp_path):
    (tmp_path / "real_history_control_s1_trials.json").write_text(
        json.dumps(history_rows("fault", 9))
    )
    (tmp_path / "real_history_control_s1_trials_v2.json").write_text(
        json.dumps(history_rows("clean", 20, history_success=True))
    )
    (tmp_path / "real_history_control_s1_trials_v10_manifest.json").write_text("{}")
    result = collect_history(tmp_path)["seed1"]
    assert result["status"] == "evaluated"
    assert [(r["pairs"], r["mcnemar_p"]) for r in result["comparisons"]] == [(9, None), (20, 1.0)]


@pytest.mark.parametrize("duplicate_kind", ["trial", "pair", "file"])
def test_duplicate_history_records_fail_closed(tmp_path, duplicate_kind):
    rows = history_rows("session", 1)
    if duplicate_kind == "trial":
        rows.append(rows[0])
    if duplicate_kind == "pair":
        rows.append(dict(rows[0], trial=2))
    (tmp_path / "real_history_control_s1_trials.json").write_text(json.dumps(rows))
    if duplicate_kind == "file":
        (tmp_path / "real_history_control_s1_trials_v2.json").write_text(json.dumps(rows))
    with pytest.raises(ValueError, match="duplicate"):
        collect_history(tmp_path)


def test_twenty_pairs_across_different_sessions_are_not_confirmatory(tmp_path):
    rows = history_rows("first", 10) + history_rows("second", 10)
    (tmp_path / "real_history_control_s1_trials_v10.json").write_text(json.dumps(rows))
    record = collect_history(tmp_path)["seed1"]["comparisons"][0]
    assert record["version"] == 10
    assert record["pairs"] == 20 and record["mcnemar_p"] is None


def test_unknown_outcome_is_not_silently_counted_as_failure(tmp_path):
    rows = history_rows("session", 1)
    rows[0]["success"] = None
    (tmp_path / "real_history_control_s1_trials.json").write_text(json.dumps(rows))
    with pytest.raises(ValueError, match="non-Boolean"):
        collect_history(tmp_path)


def test_logging_failure_is_distinct_from_servo_abort(tmp_path):
    rows = history_rows("session", 1)
    for row in rows:
        row["shutdown_error"] = True
        incident = dict(
            session="session", trial=row["trial"], returncode=-6 if row["trial"] == 0 else 1
        )
        filename = f"real_history_control_s1_trials_session_{row['trial']}_incident.json"
        (tmp_path / filename).write_text(json.dumps(incident))
    (tmp_path / "real_history_control_s1_trials.json").write_text(json.dumps(rows))
    record = collect_history(tmp_path)["seed1"]["comparisons"][0]
    assert record["shutdown_errors"] == 2
    assert record["abort_incidents"] == 1 and record["other_incidents"] == 1


def test_timestamp_summary_locates_refresh_boundaries():
    gaps = np.full(60, 0.03)
    gaps[[29, 59]] = 0.08  # Differences ending at action indices 30 and 60.
    result = timestamp_summary(np.r_[10, 10 + np.cumsum(gaps)])
    assert result["rate_hz"] == pytest.approx(60 / gaps.sum())
    assert result["boundary_ms"] == pytest.approx([80, 80])
    assert result["within_ms"] == pytest.approx([30] * 58)


@pytest.mark.parametrize("times", [[0], [0, 0], [1, 0], [0, float("nan")]])
def test_bad_timestamps_are_rejected(times):
    with pytest.raises(ValueError):
        timestamp_summary(times)


def test_overlength_submission_is_rejected_before_writing(monkeypatch):
    pages = ["main text"] * 5 + [
        "152 References",
        "A Hardware protocol and complete evaluation record",
    ]
    monkeypatch.setattr(split_submission, "page_texts", lambda _: pages)
    with pytest.raises(ValueError, match="workshop limit is 4"):
        split_submission.main("not-created.pdf")


@pytest.mark.parametrize("heading", ["References", "152   References"])
def test_split_accepts_reference_heading_with_or_without_line_numbers(monkeypatch, heading):
    pages = ["main text"] * 4 + [heading, "A Hardware protocol and complete evaluation record"]
    monkeypatch.setattr(split_submission, "page_texts", lambda _: pages)
    commands = []
    monkeypatch.setattr(
        split_submission.subprocess, "run", lambda command, **_: commands.append(command)
    )
    assert split_submission.main("not-created.pdf") == 0
    assert len(commands) == 3
