# X1_1 deviations from ANALYSIS_PLAN.md

ANALYSIS_PLAN.md is unchanged. Its SHA-256 `bd5780916f5112ce232549ad2fecdfdb5204d1544da39ad54acd9dcd02f9c12e` was
recorded in `plan_hash.json` at 2026-11-25 07:39:30, before the first GPU job (`C_n384`, launched 07:39:33).

No departure from the plan's setting, its jobs, its guards or its outcome rules.
- **Jobs.** Both jobs ran once, in the planned order, one at a time. Neither was rerun, refused, spilled or
  time-capped. GPU work lasted from 07:39:33 to 07:47:27, inside X1_1's 4-hour budget and before the 11:30 limit of
  plan section 4.
- **Verdict.** `study/x11_analyse.py` applies section 5 as written, with no threshold beyond the plan's.

Bookkeeping notes (no value affected):
1. The first run of `x11_study_labels.py` wrote `out/labels_study.json` and the figure data, then failed while
   printing a superscript to the Windows console. The print was set to UTF-8 and the script rerun on the CPU. The
   rerun rewrote the same files from the same records; the checks in `out/labels_study.json#/field_check` are the
   rerun's.
2. The plan's section 1 quotes X0_2's tail statistics. They were recomputed over all of iterations 200–300 before the
   plan was hashed: 0–78 reversals, 10–316 steps at the limit, 510–647 limits below 1e-3.
