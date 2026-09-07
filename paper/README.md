# Publication draft

The current manuscript is `main.tex`, compiled to `main.pdf`: four pages of
main text, one page of references, and three pages of supplementary details.
It is a standalone empirical paper, not a report of development sessions.
The prior manuscript, its PDF and figures, and the CoRL template files are
preserved under `research/paper_archive/`.

The main hardware table focuses on the two completed comparisons. A brief
main-text disclosure points to the full table in the appendix, which includes
the interrupted third comparison. Seed 2 has six labeled pairs
and one additional unlabeled rollout. That outcome must remain missing unless
the operator supplies it; do not infer it from the trajectory. The early
compensated-policy result and unsuccessful additional simulation runs are
retained in the appendix. No across-seed significance or calibrated hardware
force estimate is claimed.

Rebuild from the repository root:

```bash
MPLCONFIGDIR=/tmp/so101-matplotlib /home/jetson3/projects/clean_env/venv/bin/python scripts/build_paper_evidence.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
python scripts/check_paper_numbers.py
```

The figure and table are generated from trial/grid JSON rather than manually
entered. `generated/evidence.json` records the inputs to those displays.
The old manuscript's numerical checks remain in
`scripts/check_legacy_paper_numbers.py`; they are not the gate for this rewrite.

The five cited works were checked against primary records during the rewrite:

- Hwang et al.: https://www.mdpi.com/1424-8220/18/11/3856
- FACTR 2: https://arxiv.org/abs/2606.12406
- Wong et al.: https://arxiv.org/abs/2607.14578
- ACT: https://arxiv.org/abs/2304.13705
- Copycat agents: https://arxiv.org/abs/2010.14876

Before external submission, confirm the author affiliation/contact details
(retained from the existing manuscript), choose the venue's final format and
anonymization requirements, and supply a public artifact URL if releasing the
code/data. The current PDF uses preprint formatting and has not been submitted.
