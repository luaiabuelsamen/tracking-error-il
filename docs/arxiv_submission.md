# arXiv submission package

The tarball itself lives in `dist/`, which is not tracked; rebuild it with `scripts/paper/make_arxiv.sh`.

Everything here is prepared. The upload needs your account, so that step is yours.

## The file to upload

`dist/arxiv-submission.tar.gz` (352 KB)

Built by `scripts/paper/make_arxiv.sh`, which stages a flat copy, rewrites the one figure path that
would not survive arXiv's single root, includes `main.bbl` so no bibtex run is needed, and then
**compiles the staged copy in isolation** to prove the tarball is complete. Last verified build: 15
pages, zero undefined references or citations.

## Title

Tracking Error as an Observation for Behavior Cloning

Changed from "... on Low-Cost Arms". The evidence is from an SO-101 and the abstract says so in its
second sentence; the signal itself exists on any position-controlled actuator that logs both the
command and the measured position, so the old title understated the scope and invited dismissal. Revert
with one sed if you disagree.

## Abstract

`docs/arxiv_abstract.txt`, plain text, ready to paste.

## Categories

Primary `cs.RO`. Cross-list `cs.LG`. The work is an observation-design study on a physical
manipulator, so robotics is the right primary; the cross-list is for the behavior-cloning audience.

## License

`CC BY 4.0` unless you have a reason otherwise. It is the most permissive of the arXiv options and
does not restrict a later conference submission.

## Comments field

Suggested: `15 pages including supplement. Code and data: <repository URL if you make it public>.`

## arXiv and the workshop are not a choice between two

They are two artifacts from one source, and both are already built:

| where | file | what it is |
|---|---|---|
| CoRL workshop | `paper/main_anon_paper.pdf` | 4 pages of body, references on 5-6, anonymous |
| CoRL workshop | `paper/main_anon_supplement.pdf` | pages 7-15, the appendix |
| arXiv | `dist/arxiv-submission.tar.gz` | the full 15 pages with authors |

Verified: zero occurrences of the author name, institution or email in the anonymous copy.

**What the call actually says.** Double-blind through OpenReview, 2-3 reviewers, 4 pages excluding
references, deadline 9 October 2026 23:59 Central, and "concurrent submissions to other venues are
permitted if disclosed". It does **not** state whether the workshop is archival, and it says **nothing**
about preprints. Those two silences are the whole of the question.

**What is not a risk.** A workshop paper does not consume the work. CoRL workshops are non-archival in
practice, so the full version remains submittable to a main venue afterwards. Posting a preprint does not
"spend" the paper either; the arXiv record and a workshop talk do different jobs.

**What is a risk, and it is small.** A named preprint is findable during a four-week double-blind review.
Most double-blind venues permit preprints explicitly and instruct reviewers not to go looking. This call
is silent, so the policy is unstated rather than permissive.

**Recommended sequencing.** Submit the anonymous four-page version by 9 October, post the preprint after.
Four weeks of delay costs nothing here: this result is not in a crowded race. If you would rather have
the arXiv date now, post it and tick the concurrent-submission disclosure on the OpenReview form, which
is within the call's own terms. One email to the organisers settles it either way.

## What a reader will push on, and where the paper answers it

| objection | where |
|---|---|
| "position history recovers the gain, so what is new?" | Stated in the abstract and Section 4; the claim is deliberately narrowed to temporal information rather than tracking error specifically |
| "the hardware history control is missing" | Disclosed verbatim: seed-1 evaluation interrupted after 9 pairs with a gripper overload and a displaced overhead camera, seed-0 trained and not evaluated. No confirmatory test is assigned to it |
| "50 demonstrations is a small budget" | True, and the claim is scoped to that budget throughout |
| "one task, one arm" | Conceded; the simulation sweep over five seeds is the only breadth claimed |
| "did anything you predicted fail?" | Yes, and it is in the abstract: the preregistered grasp-onset prediction fails at pooled d = -0.39 |

## Honest summary of what this is

A controlled observation-design study with a large paired hardware effect (23 of 40 against 6 of 40,
p = 0.0005), reproduced in simulation across five seeds, whose own control narrows the mechanism claim,
and which reports a registered prediction that failed. It is not a method paper and does not claim force
regulation, superiority over hardware position history, or transfer across tasks.
