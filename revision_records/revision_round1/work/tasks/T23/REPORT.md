# T23: reproduction of the E30 tolerance rows and the k = 160 bridge localization

This was a CPU-only analysis of the saved records. It used no GPU job and no language-model calls. The inputs are byte-identical copies of `results/E30` in `inputs/E30` (`inputs/MANIFEST.json`). The authors' scripts it reads against are copied to `inputs/authors_code`.

The reader is `t23_reader.py`. It is standalone and needs only numpy:

```
python -I t23_reader.py --data inputs/E30 --out out --printed-table inputs/manuscript/tab_tolerance_runs.tex
```

The run log is `reader_run.log`: 25 of 25 checks pass, exit 0. Outputs are in `out/`: `tolerance.csv`, `localization.csv`, `localization_populations.csv`, `historical_proxies.json`, `checks.json` and `audit_run_agreement.json`. The mask, denominator, precision and solve stage of every column are in `statistics.md`.

## 1. The twelve k = 80 tolerance rows (`out/tolerance.csv`)

The recomputed rows reproduce all 72 printed cells of the submitted Table S24 (`checks.json`, "all 12 rows reproduced cell by cell"). Those cells are design iterations, Krylov iterations, solve-plus-setup time, compliance difference, mean |Δρ| and crossings.

**Bridge, 10⁻³ against 10⁻⁵:**
- Krylov work: 593 against 1,510 iterations; design iterations 77 against 82.
- Loop solve-plus-setup time: 5.4 against 10.4 s.
- Tight FP64 compliances: 0.16309835568 and 0.16309244473, a signed difference of **+0.003624 %**. The true relative residuals ‖f − Ku‖₂/‖f‖₂ of these re-solves, computed in FP64, were 7.62×10⁻¹¹ and 8.82×10⁻¹¹.
- Stored-field mean |Δρ|: **8.98547×10⁻⁵**, with **92** strict ρ > 0.5 crossings (46 up, 46 down).

**10⁻⁶ against 10⁻⁵ (stored FP16 fields):**

| problem | changed entries | mean \|Δρ\| | crossings |
|---|---|---|---|
| cantilever | 3,914 | 6.11×10⁻⁹ | 0 |
| bridge | 2,724 | 3.40×10⁻⁹ | 0 |
| torsion | 4,449 | 1.25×10⁻⁹ | 0 |

Of the 2,724 changed bridge entries, 1,342 differ by one FP16 step. The largest bridge difference is 4.88×10⁻⁴.

**Krylov work and time at 10⁻³** (`krylov_ratio_to_base`, `time_ratio_to_base`):
- 10⁻³ needs 36.5 %, 39.3 % and 33.2 % of the Krylov iterations of 10⁻⁵ (cantilever, bridge, torsion). This matches the supplement's "33–39 %".
- It needs 62.5 %, 52.2 % and 63.1 % of the loop solve-plus-setup time, because V-cycle setup (1.6–1.8 s per run) does not shrink with the tolerance.

**Solve stage.** Krylov work and time are the design-loop solves only. They exclude two solves:
- the solve of the retained design after the loop, which the driver does not add to `totals` or `solver_iters_total`;
- the tight re-solve.

The tight compliance is computed in FP64 on the retained design before the FP16 storage cast.

### Storage findings for A.4 (new; they refine the plan's key text)

1. **The crossing counts hold before the cast.** No stored entry in any of the twelve fields equals 0.5, and none lies within one FP16 step of it (`entries_eq_05_*`, `entries_within_1step_of_05_*` are all 0). FP32 → FP16 round-to-nearest is monotone, so every stored value lies on the same side of 0.5 as the FP32 value it came from. The strict-threshold crossing counts (92, 8, 0, …) are therefore exactly those of the FP32 fields before storage (`crossings_equal_prestorage`, true for all 12 rows).
   The plan's sentence "zero stored-field crossings do not prove zero crossings before the cast" is therefore wrong for these fields. The 0 crossings of the 10⁻⁶ pairs hold for the unrounded FP32 fields as well.
2. **The stored fields bound the pre-storage means from both sides.** Each stored FP16 value fixes the interval of [0, 1] values that round to it. Each entry's |x − y| is then bounded by its two intervals, and the entries are independent. So the pre-storage mean lies in a range whose ends are the means of the per-entry extremes (`prestorage_mean_min`, `prestorage_mean_max`). The range is sharp: FP32 fields that round to the stored ones reach both ends to within 4.7×10⁻¹³ (`prestorage_extremes_attained_gap`).
   - All ranges below are rounded outward: lower ends down, upper ends and "at most" figures up.
   - Bridge, 10⁻³ against 10⁻⁵: the pre-storage mean lies in [8.98285×10⁻⁵, 1.38696×10⁻⁴]. It departs from the stored mean 8.98547×10⁻⁵ by at most 4.885×10⁻⁵ (4.88411×10⁻⁵ unrounded), less than the stored mean itself. So the pre-storage mean is positive and of the same order. The stored mean is within 0.03 % of the lower end, and the pre-storage mean is at most 1.55 times the stored mean (1.54356 unrounded).
   - The other 10⁻³ pairs: torsion [5.077×10⁻⁵, 1.119×10⁻⁴], at most 2.21 times the stored mean (2.20219 unrounded); cantilever [2.342×10⁻⁵, 9.670×10⁻⁵], at most 4.13 times (4.12674 unrounded).
   - The 10⁻⁶ pairs: the pre-storage means are not resolved. The ranges are [1.33×10⁻⁹, 4.89×10⁻⁵] for the bridge, [4.44×10⁻⁹, 7.33×10⁻⁵] for the cantilever and [9.93×10⁻¹⁰, 6.11×10⁻⁵] for torsion. Their upper ends lie about four orders of magnitude above the stored means.
   - In the nine rows that compare two different runs, the upper end exceeds the stored mean by an almost constant amount for each problem (`prestorage_mean_max_departure`): 4.884×10⁻⁵ to 4.886×10⁻⁵ for the bridge, 7.326×10⁻⁵ to 7.327×10⁻⁵ for the cantilever and 6.105×10⁻⁵ to 6.106×10⁻⁵ for torsion. The excess comes from solid elements stored as 1.0, which make up 20.0 % of the bridge entries. Their FP32 values can lie anywhere in [1 − 2.44×10⁻⁴, 1].
   - The three 10⁻⁵ rows compare the baseline run with itself. One FP32 field lies behind both sides, so the pre-storage mean is exactly 0, as is the stored mean. Their range and departure are 0 (checked in `checks.json`).
   - The earlier version of this report gave 9.77×10⁻⁵, 1.47×10⁻⁴ and 1.22×10⁻⁴ as the largest possible departures. Those were loose triangle-inequality bounds and are withdrawn.
   - The means are exact statements about the stored fields. About the FP32 fields before the cast they say only what the ranges above give.
3. **The changed-entry counts are lower bounds.** A differing stored value implies a differing FP32 value, so the 3,914, 2,724 and 4,449 counts are lower bounds on the entries where the FP32 fields differ.

## 2. The seven k = 160 bridge snapshots (`out/localization.csv`, `out/localization_populations.csv`)

At iteration 67:
- The 2-norm sensitivity error is **0.169616**.
- The ten largest |e| carry **95.24 %** of the squared error (Σe² over all 8,192,000 elements).
- The intermediate class (0.01 ≤ ρ_phys ≤ 0.99) has **75** elements, which carry **88.07 %**.
- Medians over two explicit populations:
  - top 100 by |e|: median relative error **17.96 %** (median ρ_phys 0.0767);
  - the 75 intermediate elements: median **0.32 %** (median ρ_phys 0.0372).
  - The two populations share 32 elements.
- The top-10 and top-100 sets have no ties at their boundary (`tie_gap_*` > 0).
- The OC update difference in the audit record is 0.0.

The submitted supplement gave the 18 % median and the distances to the 75 intermediate elements. The record computes them over the top 100 (`E30_dump_analysis.py:25-34`).

The other six snapshots range from **8.60×10⁻⁶** (iteration 70) to **3.95×10⁻³** (iteration 60). The intermediate class carries 74.5–90.0 % of the squared error at five of them. At iteration 66 the solid class carries **43.3 %**, more than the intermediate class's **40.4 %**. That snapshot has 22 intermediate elements.

Every recomputed 2-norm error agrees with the dump run's audit record to within 1.1×10⁻⁷ relative. The squared-error shares, the top-100 medians and the proxy medians equal `dump_bridge_k160_mg64_analysis.json` to within 10⁻¹² (asserted in the reader).

**Dump run against the first audit run** (`out/audit_run_agreement.json`):
- The first audit run saved only scalar summaries per audit, not vectors. So the comparison covers those scalars, the iteration count and the final compliance.
- The two runs agree in what the records hold for the production path:
  - accepted true residuals and production PCG iteration counts are equal at all 19 audited iterations;
  - both runs ran 79 design iterations and reached the same final compliance, 0.08798177029441806.
  - The OC-update differences are equal at all 19 audits. The sensitivity-error summaries are equal at all audits except iteration 65.
- This is consistent with an identical production trajectory but does not establish one. The sensitivity vectors were never saved in the first run, so their identity is not verified. Nor is equality at the 60 unaudited iterations.
- The tight reference re-solves are not bit-reproducible. At iteration 67 they took 1,388 against 1,380 iterations, and they also differ at iterations 60 and 65.
- The iteration-65 sensitivity-error summaries therefore differ in the seventh digit (2-norm error 3.869569×10⁻⁴ against 3.869561×10⁻⁴).
- The supplement says "the run is deterministic and reproduces the audit". The records support only this: the production scalars agree at the audited iterations, the run has the same length and the same final compliance. The reference re-solves do not agree bit for bit.

## 3. Historical distance proxies (`out/historical_proxies.json`; not for the revision)

The submitted medians 0.570 (supports) and 0.881 (load) are reproduced exactly. They come from integer-index proxies, not physical distances:
- The element position is the integer index (ex, ey), not the element centre.
- The "supports" are the index points (0, 0) and (nx−1, 0), standing in for the support lines at node indices 0 and nx on y = 0.
- The "load" is (nx/2, ny−1), standing in for the top-centre strip at node index ny. The strip's width and z are ignored.
- Distances are divided by ny = 160. The supplement called them "depth units".
- They are computed over the top 100 by |e|. Over the 75 intermediate elements, the same proxies give 0.558 and 0.893.

As planned, the revision omits the distance sentence. No physical distance was computed.

## Acceptance

Every number named in the acceptance statement is reproduced from the saved records (`out/checks.json`, all pass):
- k = 80 bridge: +0.003624 %, 8.985×10⁻⁵ and 92;
- the three tighter-pair changed-entry counts: 3,914, 2,724 and 4,449;
- k = 160 iteration 67: the 95.24 % and 88.07 % shares and the 17.96 % and 0.32 % medians with their populations;
- the six-snapshot range 8.60×10⁻⁶ to 3.95×10⁻³, with the iteration-66 exception.

`statistics.md` states the mask, denominator, precision and solve stage of each statistic.

## Notes for the writer and later tasks

- **A.4 key text:** replace "zero stored-field crossings do not prove zero crossings before the cast". The crossing counts hold for the FP32 fields too (finding 1). Finding 2 gives the sharp ranges of the pre-storage means. For the bridge 10⁻³ pair the pre-storage mean is between 8.98×10⁻⁵ and 1.39×10⁻⁴, at most 1.55 times the stored mean. The 10⁻⁶ means are not resolved. The changed-entry counts are lower bounds (finding 3).
- **R2.2:** the 10⁻³ saving is 61 % of the Krylov iterations but 48 % of the loop solve-plus-setup time for the bridge. The fraction of iterations is not the fraction of time, which is the risk the plan names.
- **T32** can stage `t23_reader.py` with `inputs/E30` as a data-only script. It draws no figure.

## Corrections after the first check

1. **Pre-storage mean.** The bound in the first version, 9.77×10⁻⁵ for the bridge, was a loose upper bound and is withdrawn. The reader now gives the sharp range of each pre-storage mean (`prestorage_mean_min`, `prestorage_mean_max`) and checks that FP32 fields which round to the stored ones reach both ends.
   - For the bridge 10⁻³ pair the range is [8.98285×10⁻⁵, 1.38696×10⁻⁴], rounded outward. The pre-storage mean departs from the stored mean by at most 4.885×10⁻⁵, which is less than the stored mean.
   - Finding 2 is rewritten accordingly. No stored-field value changed.
2. **Dump run against the first audit run.** The first run saved only scalar summaries. The report now claims only the agreement those scalars show:
   - residuals, production iteration counts and update differences agree at the 19 audits;
   - both runs have 79 iterations and the same final compliance.
   - Identity of the sensitivity vectors, and equality at unaudited iterations, are stated as unverified.
3. **Residual definition.** `statistics.md` now gives the tight compliance (f·u, not normalized) and the true relative residual ‖f − Ku‖₂/‖f‖₂ on separate rows, each with its denominator and solve stage. The snapshot residuals (accepted ≤ 1e-5, reference ≤ 1e-10) have the same definition.

The reader was rerun: 24 of 24 checks pass, including two new checks on the pre-storage range. Every value in `tolerance.csv` and `localization.csv` that the first version reported is unchanged.

## Corrections after the second check

1. **Baseline rows.** The three 10⁻⁵ rows compare the baseline run with itself, but the reader had treated the two sides as independent FP32 fields. It therefore reported possible pre-storage means of up to 7.32639×10⁻⁵ (cantilever), 4.88531×10⁻⁵ (bridge) and 6.10577×10⁻⁵ (torsion) where the true value is exactly 0.
   - The reader now uses one field for both sides when the run is the same: range [0, 0], departure 0, attained gap 0. It asserts that the density files are the same.
   - A new check confirms that these three rows are exactly 0.
   - Only the `prestorage_mean_max`, `prestorage_mean_max_departure` and `prestorage_extremes_attained_gap` cells of these three rows changed (`prev_r1/` holds the previous outputs). The other nine rows, `localization.csv` and `localization_populations.csv` are identical.
2. **Rounding of bounds.** Finding 2 and correction 1 above now round every bound outward. The bridge departure is at most 4.885×10⁻⁵ and the upper ratios are 1.55 (bridge), 2.21 (torsion) and 4.13 (cantilever). The lower ends are rounded down (bridge 8.98285×10⁻⁵, cantilever 1e-6 pair 4.44×10⁻⁹) and the upper ends up (torsion 1.119×10⁻⁴, cantilever 9.670×10⁻⁵).

The reader was rerun: 25 of 25 checks pass (`reader_run.log`). No value outside the three baseline cells changed.
