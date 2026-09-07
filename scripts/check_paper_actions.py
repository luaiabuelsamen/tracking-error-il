"""Submission gate: reconcile findings.md against main.tex.

    python scripts/check_paper_actions.py            # report
    python scripts/check_paper_actions.py --strict   # exit 1 if anything is open

Why this exists: on 2026-09-03/04 the paper was found to be behind its own lab
record three separate times (guard 11 days, quantization 17, corpus 18), each
correct in findings.md since August and never propagated. All three were found
by accident while auditing something else. `check_paper_numbers.py` closes only
the direction where the tex quotes a number the results contradict; it is blind
to a findings.md verdict the tex answers with silence, and to a correct number
carrying a wrong claim.

Two passes:

  1. TAGGED   -- entries carrying an explicit `**PAPER ACTION:**` line. Reported
                 with their section so a human can confirm each landed.
  2. UNTAGGED -- entries with no marker whose prose contains action language
                 ("should say", "costless to fix", "before this ships", "must
                 not", "reviewer bait", ...). These are CANDIDATES, not
                 findings: the scan cannot tell a recommendation from a
                 description, so each needs a reader.

Deliberately not automatic. The gate is a checklist with an owner, and this
script only makes the list. See research/notes/roadmap.md, "Submission gate".
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

FINDINGS = Path("docs/findings.md")
TEX = Path("paper/main.tex")

# Phrases that mark a conclusion the paper may owe. Tuned on the three misses:
# the guard entry said "costless to fix", the quantization entry said "should be
# re-derived ... before it is claimed", the corpus entry stated a corrected count.
ACTION_PATTERNS = [
    r"costless to fix", r"reviewer bait", r"before (?:this|it) (?:goes|ships|is claimed)",
    r"should (?:be |not |say|read|state|carry)", r"must (?:not |be |say|carry|state)",
    r"belongs (?:in|next to)", r"worth (?:one|a) (?:clause|sentence|line|confirmation)",
    r"the paper (?:may|must|should)", r"do not (?:claim|write|say)",
    r"needs? (?:a )?(?:clause|sentence|correction)", r"not (?:yet )?claimable",
]
ACTION_RE = re.compile("|".join(ACTION_PATTERNS), re.I)


def sections(md: str):
    """Yield (heading, body) for each `## ` section, ignoring `### ` subheads."""
    parts = re.split(r"\n(?=## )", md)
    for p in parts:
        m = re.match(r"##\s+(.+)", p)
        if m:
            yield m.group(1).strip(), p


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true",
                    help="exit non-zero if any tagged action or candidate is open")
    args = ap.parse_args()

    md = FINDINGS.read_text(encoding="utf-8")
    tex = TEX.read_text(encoding="utf-8") if TEX.exists() else ""

    tagged, candidates = [], []
    for head, body in sections(md):
        acts = re.findall(r"\*\*PAPER ACTION:\*\*\s*(.+?)(?:\n\n|\Z)", body, re.S)
        if acts:
            for a in acts:
                tagged.append((head, " ".join(a.split())))
        elif ACTION_RE.search(body):
            hits = sorted({m.group(0).lower() for m in ACTION_RE.finditer(body)})
            candidates.append((head, hits[:3]))

    print(f"findings.md: {len(list(sections(md)))} sections, "
          f"main.tex: {len(tex.splitlines())} lines\n")

    print(f"=== {len(tagged)} TAGGED paper actions — confirm each landed ===")
    for head, act in tagged:
        closed = act.lower().startswith(("none",))
        print(f"  [{'closed' if closed else 'OPEN  '}] {head[:72]}")
        if not closed:
            print(f"            {act[:150]}")

    print(f"\n=== {len(candidates)} UNTAGGED sections with action language ===")
    print("    candidates only — the scan cannot tell a recommendation from a")
    print("    description. Read each, then tag it or clear it.\n")
    for head, hits in candidates:
        print(f"  ?  {head[:72]}")
        print(f"       matched: {', '.join(hits)}")

    open_n = sum(1 for _, a in tagged if not a.lower().startswith("none"))
    print(f"\n{open_n} tagged actions open, {len(candidates)} untagged candidates.")
    if args.strict and (open_n or candidates):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
