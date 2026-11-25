# T21 deviations from ANALYSIS_PLAN.md

The plan file is unchanged. Entries D1–D6 were written after the development runs (k = 4) and before any
confirmatory or extension solve. Later entries (D7, D8) are added below them with their timing.

**D1 — development grid V-cycle (development set only).** On the k = 4 beam (Grid(32, 4, 4), 2,475 DOFs) the
authors' automatic level choice (`choose_levels`, at most 2,500 coarse DOFs) gives one level, and `GMG` refuses a
one-level hierarchy. The development jobs therefore pass `levels=2`. Every grid of the study (k ≥ 8) uses the
automatic choice, as E29 does. Effect on the endpoints: none (the development set is not part of any series or test).

**D2 — reading of "continues to the tightened iterate" (plan 3.3.3).** The tightened iterate u_F⁺ of GMRES-DC and
MINRES-DC is the first outer iterate *after* the target iterate with ρ ≤ 10⁻¹¹. If none is reached before the cap or
stagnation, u_F⁺ is the smallest-residual iterate, and that level is marked failed, as the plan says. Effect: when the
target iterate itself already has ρ ≤ 10⁻¹¹, the tightened iterate is a later one, not the same vector.

**D3 — the tightening estimate at the FP64 evaluation floor (found on the development set; sensitivity analysis
added).** On the development grid (uniform layout), GMRES-DC's outer step reduced the residual by many orders of
magnitude. The first iterate below 5×10⁻¹⁰ therefore already sat at the evaluation floor of the rounded operator:
ρ = 5.8×10⁻¹² for the stencil, 2.1×10⁻¹² for the difference form. Every later iterate stayed there (6.0×10⁻¹² and
2.0×10⁻¹²). The plan's estimate needs r⁺ ≤ 0.5·r, so it cannot be established. G-coef then fails, even though the
direct-solve comparison (`out/dev_check.json`) shows the compliance correct to 10⁻¹¹. The interface layout's target
iterates landed at 1–3×10⁻¹⁰ and their estimates were established. A rerun of the uniform development job showed that
the landing point varies from run to run (the mean form's target landed at 3.4×10⁻¹⁰ in the second run). The atomic
FP64 element kernels are not bitwise reproducible. Whether G-coef passes would then depend on where one outer step
happens to land, not on the accuracy of the solve.
* The **frozen plan's rule stays the primary analysis**: `beam_interface.csv`, `uniform_controls.csv`, and the
  `frozen_plan` part of `verdicts.json` apply §6 unchanged.
* A **sensitivity analysis**, defined here before any confirmatory solve, is reported separately
  (`*_sensitivity_D3.csv`, `verdicts.json → sensitivity_D3`). It is never merged with the primary analysis. In it, a
  coefficient solve whose plan estimate is not established gets the plan's own proportional-residual model, applied to
  the pair (iterate before the target, target iterate). The formula is
  U = |C(u_pre) − C(u_F)|/C_ref · r_F/(r_pre − r_F), and the energy form likewise. It counts as established if
  r_F ≤ 0.5·r_pre. Everything else is unchanged: the residual gate, the selection rule, the resolution rule, the
  thresholds and every hypothesis. A solve whose plan estimate is established keeps it.
* Code change: GMRES-DC and MINRES-DC also save the iterate before the target (`coef_<form>_<solver>_pretarget.npy`).
  The evaluation adds its residuals and its K0-energy distance to the target. The iteration itself is unchanged.

**D4 — admission estimate.** The predicted peak is the largest part of the job from T20's workspace counts, as the
plan says. T20's measured CUDA context (354,570,240 B) is added on top. This is more conservative than the plan and
changes no endpoint.

**D5 — H2E support clause.** The plan applies "the H2 rule" to the energy error and sets "no absolute threshold" for
it. H2E is therefore supported only through g_hi(32→64) ≤ 1.5 (or g_hi(64→128) in the extension). The alternative
B ≤ 10⁻⁷ of H2, which is an absolute threshold, is not used for the energy error.

**D7 — reference solver breakdown past the floor (recorded after the confirmatory jobs; no rule changed).** The
authors' `pcg64` replaces the recursive residual with the true one every 50 iterations but keeps the search
direction. Once the iterate sits at the evaluation floor, the replaced residual is many orders of magnitude larger
than the recursive one. The next β then explodes and the iteration diverges: NaN curvature, or true residuals of
10¹⁸–10³² at the 20,000-iteration cap. As a result:
* Every tightened reference solve (target 10⁻¹¹) except the k = 8 interface one ended in such a breakdown or cap with a
  diverged final iterate. The plan keeps the final iterate, so the tightening estimate of the reference is not
  established at those grids. At k ≤ 64 the reference uncertainty is then the residual bound B_C, B_E alone, as §6
  allows.
* At k = 64, uniform layout, the **target** solve itself did not pass 5×10⁻¹⁰ before it broke down at iteration
  1,839. Its final iterate is a diverged vector (K0-ind residual 3.7×10³⁹). G-ref fails on that grid. Following §13
  ("no fallback reference procedure is added"), no other reference was computed, and every k = 64 uniform endpoint is
  reported without a reference compliance. The solves, compliances and residuals of that grid are published.
* The plan foresaw a reference that cannot reach 10⁻⁹, but not a breakdown with a non-finite or negative
  reference compliance. The analysis was changed after the confirmatory outputs were opened, and only so that it
  forms no relative error against such a vector. A reference counts as unusable if fᵀu_ref ≤ 0, it is
  non-finite, or its residual is ≥ 1; an unusable reference has G-ref failed and no D or e values. This changes no
  value on any other grid and no rule.

**D6 — H1 per form.** H1's support condition is stated for both forms jointly. The primary verdict is "per form:
support if H1 and H2 are both supported". H1 is therefore also classified per form, with the same clauses restricted
to that form. The joint H1 class is reported beside it.

**D8 — corrections after the first check (CPU only; no solve rerun, no rule changed; recorded after the
confirmatory and extension outputs).**
* *Failed coefficient solves now report the iterate the plan names.* Plan §3.3.5 reports the smallest-residual
  iterate of a failed solve. The analysis had taken the smallest residual among the solvers' *target* iterates. It now
  ranks every saved iterate (pre-target, target, and the later iterate, which is the solver's smallest-residual
  iterate whenever its level failed) by the residual recomputed against its own operator. In all 36 failed solves of
  the frozen pass, the chosen iterate is the minimum of the solver's own residual history. In 32 of them it is a later
  iterate than the target: 23 of the 24 failures at k = 8–64 with a usable reference (the exception is the k = 16
  interface difference form), the uniform k = 64 corner, mean and difference solves, and 6 of the 8 at k = 128. These
  rows are added with level "smallest residual (…)" and `reported = True`; the target rows stay, labelled as not
  the reported result. The largest change of D against the target iterate is 3.4×10⁻¹² (`summary.json →
  failed_reports_frozen`). The failure count (24 of 28) and every verdict are unchanged: failed values enter no test.
* *Residual columns.* Reference rows now carry all six residuals. Every kept vector (pre-target, target and later
  coefficient iterates; the 10⁻⁵, 10⁻⁶ and 10⁻⁷ control iterates; both reference iterates) is listed with all six
  residuals in the new `terminal_residuals.csv`.
* *Descriptive additions, no rule:* the term that sets U_ref per grid (`U_ref_C_source`, `U_ref_E_source`); the margin of
  each resolved value against a smaller λ_lb (`summary.json → lambda_sensitivity`); and a comparison of the D3
  estimate with the observed change from the target to the later saved iterate (`summary.json → D3_model_check`).
* The interface-to-uniform ratio now pairs rows of the same level, so the added rows do not displace the target rows'
  ratios.
* Before-fix copies of the outputs are in `out/before_fix_r1/`.

**D9 — corrections after the second check (CPU only; no solve rerun, no rule changed; recorded after the
confirmatory and extension outputs).**
* *E29 comparison.* `summary.json → e29_reproduction → diff_coefficient_bias` compared E29 with T21's GMRES target
  iterate. Where the coefficient solve failed (uniform difference form at k = 8, 16 and 32), the frozen rule reports the
  smallest-residual iterate instead. The comparison now uses the reported iterate (`T21_iterate`). The differences
  become 2.12×10⁻¹⁵, 6.66×10⁻¹⁶ and 4.24×10⁻²². The target-iterate comparison is kept, labelled
  `abs_difference_target_iterate`.
* *Solver label of E29's FP64-arithmetic control.* The `historical_E29` rows labelled every control `pcg32 mg32_x64`.
  E29's script ran the `fp64_arith_node` control as `mg32_op64` (FP64-arithmetic node operator, common V-cycle). That
  label is now used. No value changed.
* *REPORT wording.* The control iterates' interface K0 residuals are now given per form: the repaired controls and the
  original stencil separately.
* Before-fix copies of the outputs are in `out/before_fix_r2/`.

**D10 — corrections after the third check (operator note of 2026-11-24 08:25; CPU only; no solve rerun, no rule
changed; recorded after the confirmatory and extension outputs).**
* *Energy-error orders.* Plan §5.5 defines the observed order log₂ g for D and for e. The analysis had exported it for
  D only (`order_prev_D`). It now also exports `order_prev_e`, computed from the saved adjacent ratios `ratio_prev_e`.
  This adds one column to the four result CSVs; no other cell changed (`out/fix_r3_check.json`).
* *REPORT wording.* The k = 16 target-iterate difference from E29 is corrected to 7.98695×10⁻¹⁵; the 2.9×10⁻⁶ compliance
  bound is restricted to the mean and difference controls, and the corner control's compliance error is given
  separately. Table E gains the target-iterate column; table O gives the orders.
* Before-fix copies of the outputs are in `out/before_fix_r3/`.
