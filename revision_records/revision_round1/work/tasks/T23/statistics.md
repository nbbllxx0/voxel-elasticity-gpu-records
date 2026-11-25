# T23 statistic definitions: mask, denominator, precision, solve stage

The definitions are those of `t23_reader.py`. Source records: copies of `results/E30` in `inputs/E30`.

## k = 80 tolerance rows (`out/tolerance.csv`; 3 problems × 4 acceptance tolerances, 1,024,000 elements each)

The problems are cantilever, bridge and torsion on the 160×80×80 grid. Each run uses FP64 PCG with the FP32 V-cycle and the difference-form FP32 operator. The run is accepted at a true relative residual of 1e-3, 1e-4, 1e-5 or 1e-6. Each row is compared with the 1e-5 run of the same problem.

**True relative residual (every residual in this file).** The FP64 PCG driver computes ‖f − Ku‖₂ / ‖f‖₂ (`pcg64` in `voxfem/krylov.py`):
- f is the load vector and u the displacement iterate;
- K is the run's FP64 operator: element moduli held in FP32, the action in FP64;
- fixed DOFs are identity rows with zero load, and the iterates are zero there. Their residual entries are therefore zero, and the 2-norms run in effect over the free DOFs;
- the denominator ‖f‖₂ is computed in FP64 from the load values;
- the residual is "true" because it is recomputed from f − Ku, not taken from the PCG recursion. The driver recomputes it whenever the recursive residual meets the tolerance, and every 50 iterations; the solve stops when the true residual meets the tolerance.

| column | stage | mask / population | denominator | precision |
|---|---|---|---|---|
| `design_iterations`, `termination` | the run's own stopping rule | – | – | record |
| `krylov_iterations_loop` | sum of PCG iterations over the design-loop solves (iterations 1…N). Excludes the solve of the retained design after the loop and the tight re-solve. | – | – | integer count from the record (`solver_iters_total`) |
| `solve_s_loop`, `setup_s_loop`, `solve_plus_setup_s_loop` | the same loop solves: solve wall time without V-cycle setup, plus V-cycle setup (driver totals) | – | – | seconds, as recorded |
| `krylov_ratio_to_base`, `time_ratio_to_base` | as above | – | the same quantity of the 1e-5 run | FP64 |
| `compliance_final_accepted` | f·u after the solve of the retained design at the run's own tolerance | load DOFs | – (not normalized) | FP64 |
| `compliance_tight_fp64` | f·u, with u from the tight re-solve of the retained design: FP64 PCG with the FP32 V-cycle, started from the final accepted state and run to a true relative residual ≤ 1e-10. Computed before, and independently of, the FP16 storage cast. | load DOFs (f is nonzero only there) | – (not normalized) | FP64 |
| `tight_rel_true_residual` | the true relative residual at the end of that tight re-solve | all DOFs (in effect the free DOFs) | ‖f‖₂ | FP64 |
| `rel_compliance_diff_pct` | tight compliances | – | tight compliance of the 1e-5 run | FP64, signed, in percent |
| `mean_abs_drho_fp16_stored` | stored final physical density: the projection of the retained design variables (after the last OC update) at the final projection steepness, cast FP32 → FP16 for storage | all 1,024,000 elements | 1,024,000 | FP16 values subtracted exactly in FP64 |
| `mean_abs_drho_fp32_generator` | the same fields, computed as the submitted table generator does | all elements | 1,024,000 | FP16 → FP32, subtraction and mean in FP32 |
| `max_abs_drho_fp16_stored` | the same fields | all elements | – | exact |
| `changed_entries` | the same fields | entries whose stored FP16 values differ | – | count. Because rounding is a function, it is a lower bound on the entries where the FP32 fields differ. |
| `changed_entries_one_fp16_step`, `max_fp16_steps` | the same fields | changed entries | – | FP16 bit-pattern distance |
| `strict_gt05_crossings` (`_up`, `_down`) | the same fields | entries with (ρ > 0.5) ≠ (ρ_base > 0.5) | – | count on the stored values |
| `entries_eq_05_*`, `entries_within_1step_of_05_*` | each stored field | stored value = 0.5, or within one FP16 step of 0.5 | – | count |
| `crossings_equal_prestorage` | – | – | – | true if no stored entry equals 0.5. Round-to-nearest is monotone, so each stored value then lies on the same side of 0.5 as the FP32 value it came from, and the crossing count is exactly that of the FP32 fields before the cast. |
| `prestorage_mean_min`, `prestorage_mean_max` | the FP32 final physical densities before the cast. They are unknown, and are bounded only by the stored values. | all elements | 1,024,000 | Sharp range of mean \|x − y\| over all fields x, y in [0, 1] that round (round to nearest) to the two stored FP16 fields. Each entry's \|x − y\| is bounded by its two closed rounding intervals, and the entries are independent, so the ends are the means of the per-entry extremes. Computed in FP64. In the three 10⁻⁵ baseline rows both sides are the same run, so one FP32 field lies behind both and the range is exactly [0, 0]. |
| `prestorage_mean_max_departure` | as above | – | – | max(stored mean − min, max − stored mean): the largest possible difference between the pre-storage and the stored-field mean |
| `prestorage_extremes_attained_gap` | as above | – | – | Sharpness check: FP32 fields that round to the stored ones are built at both ends of the range. The value is the largest gap between their mean and the range end. |

## k = 160 bridge snapshots (`out/localization.csv`, `out/localization_populations.csv`; 320×160×160, 8,192,000 elements)

The run is the bridge with FP64 PCG, the FP32 V-cycle and the difference form, accepted at 1e-5. It was repeated with dumps at audited design iterations 50, 60, 65, 66, 67, 70 and 76.

At each dump, inside that iteration's solve and before its OC update, the record holds three vectors:
- `dc`: the filtered sensitivity vector passed to the OC update, from the accepted production state. That state is the production FP64 PCG solve (FP32 V-cycle), accepted at a true relative residual ‖f − Ku‖₂/‖f‖₂ ≤ 1e-5; the achieved values are 7.76×10⁻⁶ to 9.95×10⁻⁶.
- `dc_ref`: the same chain from an FP64 PCG re-solve of the same design. The re-solve uses the FP32 V-cycle, starts from the accepted state and runs to a true relative residual ‖f − Ku‖₂/‖f‖₂ ≤ 1e-10; the achieved values are 8.60×10⁻¹¹ to 9.80×10⁻¹¹.
- Both residuals are defined as in the k = 80 section: the FP64 operator, the 2-norm in effect over the free DOFs, and the denominator ‖f‖₂.
- `rho_phys`: the physical density on which the state was solved.

All three are stored in FP32. Every statistic is computed in FP64 from them, with e = dc − dc_ref per element.

| column | mask / population | denominator | notes |
|---|---|---|---|
| `rel_err_2` | all elements | ‖dc_ref‖₂ | ‖e‖₂ / ‖dc_ref‖₂ |
| `rel_err_2_audit_record` | – | – | the GPU value in the dump run's audit record (FP32 arrays, CuPy norms). Agrees to within 1.1×10⁻⁷ relative. |
| `share_void`, `share_intermediate`, `share_solid` | ρ_phys < 0.01; 0.01 ≤ ρ_phys ≤ 0.99; ρ_phys > 0.99. The three classes partition the elements. | Σ e² over all 8,192,000 elements | squared-error share. Masks follow the submitted script, applied to the dumped physical density. |
| `n_void`, `n_intermediate`, `n_solid` | the same masks | – | counts |
| `n_grey_strict_audit` | 0.01 < ρ_phys < 0.99, the audit table's grey mask | – | equal to `n_intermediate` at all seven snapshots |
| `share_top10/100/1000` | the n elements of largest \|e\| (stable sort) | Σ e² over all elements | `tie_gap_topn` = \|e\|₍ₙ₎ − \|e\|₍ₙ₊₁₎. A positive gap means the set is unambiguous: both top-10 and top-100 at iteration 67. Ties at a boundary do not change the share. |
| `accepted_rel_true_residual`, `reference_rel_true_residual` | all DOFs (in effect the free DOFs) | ‖f‖₂ | true relative residuals ‖f − Ku‖₂/‖f‖₂ of the accepted production solve and of the reference re-solve. Stage: the end of each solve, before that iteration's OC update. FP64, from the audit record. |
| `update_max_abs_diff_audit_record`, `update_n_diff_gt_1e-3_audit_record` | OC update from the accepted state against the update from the re-solved state | – | from the audit record. The dumps do not hold the updated fields, so this is not recomputed. |
| populations: `median_rel_err` | `top100_abs_error`: the 100 largest \|e\|. `intermediate_0.01_0.99`: the intermediate mask above. | – | median over the population of \|e_i\| / max(\|dc_ref_i\|, 1e-300) |
| populations: `median_rho_phys`, `share_sq_error`, `overlap_with_other_population` | as above | Σ e² over all elements (share) | overlap = number of elements in both populations |

`historical_proxies.json` reproduces the submitted script's distance medians and describes them. They are integer-index proxies and are not for the revised paper.
