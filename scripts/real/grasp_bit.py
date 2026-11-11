"""The binary grasp-state input (CoRL 2026 WEBP review item 1).

One bit, latched: it is 0 until the measured jaw has opened past the reopen threshold and then
closed below the closure threshold, and 1 from that frame to the end of the episode. The thresholds
and the "opened, then closed" rule are the ones `scripts/paper/supplementary_analysis.py` uses to
find the grasp-closure frame of each demonstration (`demonstration_summary.json`), so the bit marks
the same event the paper already reports (median frame 331 of 400). It is a function of the measured
jaw position alone: no command, no load register, no tracking error. Appended to the observation it
tells the policy which phase of the task it is in and nothing about contact, which is what separates
grasp-phase memory from contact information.

Training and deployment call the same function on the same quantity (recorded or measured jaw
position on the 0--100 opening scale), so the offline parity audit covers it.
"""

from __future__ import annotations

import numpy as np

CLOSED = 5.0     # jaw below this counts as closed (recorded 0--100 opening units)
REOPENED = 8.0   # jaw above this counts as open; the demonstrations start closed on nothing


def grasp_bit_from_history(jaw: np.ndarray | list, closed: float = CLOSED, reopened: float = REOPENED) -> float:
    """Latched grasp bit at the last frame of ``jaw`` (all measured jaw positions so far this episode)."""
    jaw = np.asarray(jaw, dtype=np.float64).reshape(-1)
    opened = np.flatnonzero(jaw > reopened)
    if not len(opened):
        return 0.0
    return float(np.any(jaw[opened[0] + 1:] < closed))


def grasp_bits(jaw: np.ndarray, closed: float = CLOSED, reopened: float = REOPENED) -> np.ndarray:
    """Per-frame latched grasp bit for one episode's jaw trace; vectorised twin of the function above."""
    jaw = np.asarray(jaw, dtype=np.float64).reshape(-1)
    bits = np.zeros(len(jaw), np.float32)
    opened = np.flatnonzero(jaw > reopened)
    if not len(opened):
        return bits
    closes = np.flatnonzero(jaw[opened[0] + 1:] < closed)
    if len(closes):
        bits[opened[0] + 1 + closes[0]:] = 1.0
    return bits
