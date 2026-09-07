# Research material

Working material behind the study. Nothing here is needed to read the paper
or run the code; it is kept because the project's decisions are recorded in
it.

| path | what it is |
|---|---|
| `THESIS.md` | the one-sentence thesis the project is organised around, and the standing rules |
| `notes/HANDOFF.md` | hand-off written 2026-09-05 for a collaborator joining mid-project |
| `notes/roadmap.md`, `notes/phase3.md`, `notes/overnight_plan.md`, `notes/friday.md` | plans, pre-registered decision trees, weekly paragraphs |
| `notes/gap.md`, `notes/reading.md`, `notes/reading_notes/` | the reading program: gap statement and four per-thread reading notes (58 papers) |
| `notes/related_table.md` | draft related-work difference table |
| `notes/paper.md`, `notes/workshop_cut.md`, `notes/repro.md`, `notes/task2_arms.md`, `notes/results_matrix.md` | the earlier "lag excess" manuscript draft, its cut plan, its reproducibility manifest, the grid arm definitions and results matrix |
| `paper_archive/` | the manuscript as it stood before the hardware rewrite (`main_before_hardware_rewrite.tex/.pdf`), its figures, and the CoRL template files |
| `figures/` | dataset-analysis plots and the seed-0 hardware trajectory diagnostic figure |
| `portfolio/` | a standalone browsable gallery of showcase clips; refresh with `python scripts/update_portfolio.py` |

The lab record itself, `docs/findings.md`, stays in `docs/` because code and
scripts reference it, as do the hardware pre-registration and diagnostics
notes the paper relies on.

Figure scripts for the archived manuscript (`scripts/fig_*.py`,
`scripts/corpus_delta_outcome.py --fig`, `scripts/appendix_d_stats.py --fig`)
write into `paper_archive/figures/`.
