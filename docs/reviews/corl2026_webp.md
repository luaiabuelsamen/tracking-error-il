# CoRL 2026 Workshop on Everything Beneath the Policy: reviews of submission 6

OpenReview forum `r6N6ZxAIPl`. Decision 2026-10-26: reject, 20 of 92 accepted. Both reviews scored the
paper above threshold; the programme committee cut for capacity, not quality.

| reviewer | score | confidence |
|---|---|---|
| uazA | 8, clear accept | 3 |
| bA2d | 6, marginally above threshold | 4 |

**Status of this file.** The text below is a digest written from memory of the reviews on 2026-10-26
(`~/Desktop/life/work/RESEARCH.md`). OpenReview blocks scripted access, so the verbatim reviews are
not yet here. Luai replaces this digest with the pasted reviews; until then, every item is a
paraphrase and should be read as such.

## Reviewer bA2d: requested changes

The numbering is ours and is used by `docs/revision_2026-11.md` and the commit messages.

1. **A binary grasp-state input on hardware.** Separate memory about the grasp phase from contact
   information by training policies with a one-bit grasp indicator and comparing them with the
   position-only and tracking-error policies. Needs the arm. Pre-registration:
   `docs/hardware/preregistration_2026-11_grasp_bit.md`.
2. **More hardware trials, so that seed 1 does not carry the result.** Seed 0 is not significant on
   its own and seed 2 was interrupted. Needs the arm. Pre-registration:
   `docs/hardware/preregistration_2026-11_seed_replication.md`.
3. **Move into the main text:** the interrupted position-history session (1 of 9 against 0 of 9),
   the grasp (seat) token from the simulation grid, and the compensated residual's hardware failure
   (7 of 10 against 0 of 10). These were in the appendix of the 4-page workshop version.
4. **Seed count and the order of the statistics.** Say that three seeds were trained rather than
   "both seeds"; lead with the per-seed paired McNemar results and present the pooled stratified
   test as the post hoc secondary analysis it is.
5. **Related work.** Cite and contrast Aractingi et al., *Controlling the Solo12 quadruped robot with
   deep reinforcement learning* (Scientific Reports 13, 11945, 2023), whose policy observes a
   three-step history of joint target errors, and contrast more explicitly with the submission's
   reference [11], Xu et al., *Mind the Gap* (arXiv 2602.08776), which conditions on the mismatch
   between leader command and follower execution.
6. **Report gripper overloads per policy.** The paper reported overload counts per session; the
   reviewer asked for them broken down by policy, so a reader can see whether one observation design
   provokes more faults.

## Reviewer uazA

Positive on the controlled design, the pre-registration record and the disclosed null result. No
requested changes recorded in the digest.

## Disposition

Items 3 to 6 are text and generated-table changes and are applied in Phase A of
`docs/revision_2026-11.md` (arXiv v1). Items 1 and 2 need bench time with the operator present and are
Phase B.
