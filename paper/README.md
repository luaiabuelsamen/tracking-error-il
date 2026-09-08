# Publication draft

The current manuscript is `main.tex`, compiled to `main.pdf`: four pages of
main text, then references and eight pages of appendices.
It is a standalone empirical paper, not a report of development sessions.
An earlier manuscript on the same data is kept outside this repository.

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
python scripts/paper/build_paper_evidence.py
python scripts/paper/supplementary_analysis.py
latexmk -pdf -interaction=nonstopmode -halt-on-error -cd paper/main.tex
python scripts/paper/check_paper_numbers.py
```

Every table and figure is generated from the records under `results/`; nothing
is typed. `generated/evidence.json` and `generated/supplementary.json` record
the inputs to those displays, and `check_paper_numbers.py` asserts the text
against them. `make paper` from the repository root runs all four steps.

The cited works were checked against primary records during the rewrite:

- Hwang et al.: https://www.mdpi.com/1424-8220/18/11/3856
- FACTR 2: https://arxiv.org/abs/2606.12406
- Wong et al.: https://arxiv.org/abs/2607.14578
- ACT: https://arxiv.org/abs/2304.13705
- Copycat agents: https://arxiv.org/abs/2010.14876

Target venue: the CoRL 2026 workshop *Everything Beneath the Policy*
(4 pages excluding references, double blind, OpenReview, deadline
October 9, 2026, 11:59 p.m. Central). Main text ends on page 4 in both build
modes; references and appendices follow. The workshop permits concurrent
submissions if disclosed, and papers accepted to the CoRL main conference are
ineligible.

`make paper-anon` produces `main_anon.pdf` in submission mode (anonymous
author block, line numbers, anonymous PDF metadata) and checks it for
identifying strings; its footer names the workshop. The workshop specifies no
template and says nothing about appendices, so upload the paper and the
appendices separately: `python scripts/paper/split_submission.py` cuts
`main_anon.pdf` into `main_anon_paper.pdf` (main text and references) and
`main_anon_supplement.pdf` (appendices). For an anonymous code artifact, strip the author name and
handle from `CITATION.cff`, `pyproject.toml`, `NOTICE`, the README citation
block, and the Hugging Face repo id in `scripts/bench/arms.sh` and
`scripts/bench/validate_record_args.py` before uploading a copy.
