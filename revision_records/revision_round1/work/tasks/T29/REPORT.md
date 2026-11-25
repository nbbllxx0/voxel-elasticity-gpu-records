# T29 report: comparison table, cell sources and paired-timing orientation

Serves A.3, R1.1 and R1.2. CPU only: no GPU job and no language-model call. Every number below is read from a file in
this folder (`comparison.json`, `verify_sources.json`, `comparison_tables.md`, `logs/value_diff_fix1.json`,
`logs/value_diff_fix3.json`, `logs/value_diff_fix4.json`), and each of those files cites the source of every cell.

## 00. Correction after the fourth check (fix round 4)

The checker found that round 3 gave every T27 solve row the planned count of timed solves as if it had been observed.
The original-stencil IR solves at k = 160 and k = 256 broke down, and their records hold no timed solve
(`tasks/T27/out/H3_solve_k160_mgir_orig.json#/timed` and `tasks/T27/out/H3_solve_k256_mgir_orig.json#/timed`, both
empty lists).

- `build_comparison.py` now gives each T27 solve time two counts:
  - `n_timed_solves_planned` is the plan's count (`tasks/T27/ANALYSIS_PLAN.md:109-111`);
  - `n_timed_solves` is the observed count, a derived cell (`op = "len"`) equal to the length of the record's
    `timed` list.
- The builder asserts that the observed count equals the planned count wherever a solve completed, and is 0
  otherwise. For the two original-stencil IR rows the cells now hold planned 3, observed 0, and the median stays
  unavailable ("no timed solve completed (numerical breakdown); median not available").
- `sample_rule` now says that the plan fixed the count and that the observed count is `n_timed_solves`.
- `verify_sources.py` recomputes `op = "len"` cells from the record. A fourteenth planted fault, which reports the
  planned count 3 as observed at k = 160 for original-stencil IR, is caught.
- The external-table caption read "Solve: our paths, median of three solves". It now adds "(original-stencil IR: none
  timed, as its solves broke down)", and the table maker asserts the four observed counts of our k = 256 rows
  (3, 3, 3, 0).
- The fix-round-3 item 6 text below wrongly said that ours ran 3 solves at every grid. It now gives the plan's count.

Value diff against round 3 (`logs/value_diff_fix4.json`, previous outputs in `logs/fix4_prev/`):
- Two values changed: the observed count at k = 160 and at k = 256 for original-stencil IR, from 3 to 0.
- 15 `n_timed_solves_planned` cells were added.
- Wording changed in the 15 `sample_rule` texts and in the two `statistic` texts above.
- Nothing else changed in rows, pairs or largest sizes.

## 0. Corrections after the third check (fix round 3, operator note of 2026-11-24 04:40)

No new measurement. The previous outputs and scripts are kept in `logs/fix3_prev/`. `scratch/diff_values_fix3.py`
compares every cell value of the old and new `comparison.json` (`logs/value_diff_fix3.json`): **no value changed**.
There are 0 changed cells in rows, pairs and largest-size entries, and none was removed. 166 row cells and 147
largest-size cells were added, and 12 largest-size entries (27 → 39). The only changed wording in rows is the
`times/solve/statistic` text of the 15 T27 solve rows (item 6). CPU only.

1. **Starting state with each Träff capacity entry.**
   - Every S1 entry now carries `state` ("S1: the released iteration-1 state (x = 0.2), solve from zero") and its
     admission rule. In `tab_comparison_capacity` these rows now read "Träff's cantilever, state S1 (from zero)". The
     65.5M completions belong to S1 only, and the table note says so.
   - Imported the eight S5 entries (four paths × run completed / verified) from `tasks/T28/capacity.json`:
     - The released code completed up to 8.19M by reaching its iteration cap. It met its native stop at no size and
       was verified at none (class 7 at k = 64, 128 and 160, each asserted).
     - FP64 PCG (both V-cycles) and repaired IR were verified at 8.19M.
     - The next tested grid, 33.6M, is "not run": no S5 state exists there. The cell `no_s5_above` cites R's class 6
       at k = 256 and its note.
   - Imported the design-loop bounds: the released record run and our three matched-rule loops completed through
     8.19M (20 design iterations at k = 64 and 4 at k = 128 and 160, `tasks/T28/ANALYSIS_PLAN.md:432-433, 454-455`).
     The released record run at 33.6M was interrupted at its wall cap (class 6). T28's qualification is kept: the
     unchunked whole-vector transfers counted toward the cap, and the run's iterations are diagnostics, not design-loop
     results. Our loops were not run at 33.6M because no completed released loop existed to start from.
   - The capacity table has two new S5 rows and a new section, "Design loop on Träff et al.'s cantilever (each code
     its own workload)", with two rows. Note e explains why no S5 state exists at 33.6M or above.
2. **Protocol qualification at 113.2M (repaired IR) and 65.5M (FP64 PCG).** Both size cells now read "(historical
   completion)" with note c. The status cells say what the prespecified repaired cantilever run did at the same size:
   - IR at 113.2M: not admitted (prediction). The assert checks class "guard prediction" and W = 18,448,734,655 B
     above E_free.
   - FP64 PCG at 65.5M: ran out of memory under its pool cap. The assert checks class "allocation failure", an
     OutOfMemoryError, and the repaired operator `stencil_diff`.

   `t27_confirmatory` in both entries now cites the problem, the admission rule and the predicted workspace with
   E_free (IR), or the operator and pool cap (FP64).
3. **Admission rule of the recursive control.** Its `t27_confirmatory` now cites T27's rule ("admitted iff W + 1.5 GiB
   <= E_free (guard.effective_free_bytes)", `tasks/T27/capacity.json#/definitions/admission`), together with what
   that estimate is (`tasks/T27/src/voxfem/guard.py:116-126`: the smaller of the driver-reported free memory and the
   total memory less the other processes' dedicated usage and the own pool). The table cell asserts both. Note c
   states this rule for repaired IR and the recursive control at 113.2M. The driver-reported free memory rule is now
   note d and applies only to the fixed-state refusals (T28, `tasks/T28/ANALYSIS_PLAN.md:265`).
4. **E4 coefficient fields.**
   - Every E4 row now carries `coefficients` (`experiments/E4_update_cost.py:56-57, 61, 70-73, 84-88, 93`). The
     stencil is timed on field E. Each assembled matrix is built from E, refreshed to the second field E2 (same
     log-uniform distribution) and then timed, so its SpMV runs on E2.
   - Every E2 row carries `coefficients` (`experiments/E2_operators.py:83-84, 92, 103, 111-113`): one field E for
     every operator, so the coefficients are identical within each comparison.
   - The note of `tab_supp_sparse` says both. The table maker asserts the two cells before writing it.
5. **Markdown mirror.**
   - `make_tables.py` escapes every literal bar in a cell as `\|`, so `||r_0||` renders as `\|\|r_0\|\|`. It also pads
     each row whose TeX cell spans several columns with empty cells, so every row has its header's cell count.
   - `verify_sources.py` now splits each row as a GitHub-flavoured renderer does (`md_cells`): at every unescaped bar,
     with cells trimmed and `\|` unescaped. A row or delimiter row whose cell count differs from the header is a
     problem, and padding cells must be empty.
   - A thirteenth planted fault, the norm bars unescaped in the Markdown mirror, is caught.
6. **Solve sample counts in the external-table caption.** Each solve time now carries `n_timed_solves` and
   `sample_rule`.
   - T27: the number of timed solves was fixed by grid size (`tasks/T27/ANALYSIS_PLAN.md:109-111`). The plan gave
     ours 3 solves at every grid and Hou's CG 3 at k = 80 and 160 and 1 at k = 256. The statistic of the Hou k = 256
     row now reads "one timed solve". (Corrected in fix round 4: the planned count is not the observed one; see below.)
   - T28: the number was set by duration (`tasks/T28/ANALYSIS_PLAN.md:149-152`): 3 solves when the first took at most
     120 s, otherwise that one. The cell cites the CSV's `n_timed_solves`.
   - The caption states each rule for its own code: three timed solves for Hou at 8.19M (median 164.8 s) and one at
     33.6M; for the released OpenMP-offload code at 8.19M, three at S1 and one at S5. The table maker asserts these
     counts and rules against the cells.

Checks after the round: `verify_sources.py --selftest` reports 0 problems and catches 13 of 13 planted faults. The
checker's TeX-only tamper tests (`scratch/checker_test_fix2.py`: 648 → 250, "over" dropped, "(historical
completion)" dropped) still give 3, 2 and 1 problems. The eleven tables compile with pdflatex.

Note for the response (outside this round's scope, no value affected): the original-stencil IR row of the
complete-optimization block (113.2M, cantilever and torsion) is also historical but carries no "(historical
completion)" mark. The operator note named only the repaired-IR and FP64-PCG values.

## 0b. Corrections after the second check (fix round 2)

The previous outputs and scripts are kept in `logs/fix2_prev/`. `scratch/diff_values_fix2.py` compares every cell value
of the old and new `comparison.json` by row, pair and largest-size entry (`logs/value_diff_fix2.json`): **no existing
value changed**. 211 row cells, 9 pair cells and 3 largest-size cells were added. Wording fields (setup boundaries,
labels, definitions) and the tables changed as listed below. CPU only.

1. **Setup of the T27 application rows.** The application process times system construction (load, supports and the
   fixed-DOF mask), the mask copy to the device and one operator construction, including its kernel compilation, twice
   (`tasks/T27/drivers/hrun.py:157-163`; `code/src/voxfem/operators.py:595-608`). It builds no multigrid hierarchy and
   runs no update. The nine non-Hou application rows (three operators at three grids) now carry this boundary as a
   basis cell. It says the values
   (e.g. 0.0670/0.0152 s, original stencil, 1.02M) are not a hierarchy setup cost and cannot be compared with the
   solve rows' setup. The solve rows keep their own boundary (`hrun.py:295-300`: `hou_system` + `Ours(...)`, with the
   multigrid hierarchy).
2. **Hou/ours solve-time ratio at 8.19M.** At this grid both independent residuals (Hou 0.160, ours) come from the
   replacement checker outside T27's repeat conditions, and T27's prespecified every-grid test of Hou's native-stop
   residual (P1) is unresolved. The pair label now says that the accuracy relationship rests on exploratory evidence
   only, and the pair has a `qualification`. Each Hou/ours pair now carries `accuracy_evidence`: both independent
   residual cells and T27's P1 outcome. At 1.02M and 33.6M the label reads "at unequal accuracy (confirmatory
   independent residuals)".
3. **Memory.**
   - Each T27 solve row now carries `memory/comparison_status`, T27's P6 outcome ("inconclusive"). The prespecified
     comparison uses the timed processes, which retain two builds. Any ordering of the single-build peaks is
     exploratory.
   - The device-peak definition no longer says "over the process life". It now reads "over the samples taken while the
     process ran".
   - The original-stencil IR row at 1.02M has a `coverage` cell on its process-dedicated and device peaks, citing T27's
     note: sampling from the watcher's first baseline onward, not whole-process. That baseline already held shared
     memory.
   - Tables: the memory cells assert P6's outcome. The notes of `tab_comparison_external` and `tab_supp_hou_matched`
     say the column gives no confirmatory ordering. The 1.02M IR-original cell carries the mark w ("from the spill
     watcher's first baseline onward").
   - Section 8 of this report no longer says that our paths stay below Hou in dedicated memory.
4. **Residuals of solve rows.**
   - The ten E29 rounded-coefficient rows now carry `insolver_residual`: the record's `rel`, the in-solver residual of
     FP64 CG on the rounded operator. Its kind and method are cited (`experiments/E29_review.py:122-142`: recursive
     update, recomputed every 50 iterations). `achieved_true_residual` is marked missing ("no independent check").
   - The 15 T28 design-loop rows now carry `insolver_residual_per_solve`, one cited cell per design iteration, e.g.
     3.1271e-6 for the first k = 64 FP64 PCG solve (`tasks/T28/design_workload.csv:47`). Its kind is per code: the
     released code's FP32 recursive residual at its stop; our in-process FP64 true residual (FP64 PCG) or outer FP64
     residual (IR). `achieved_true_residual` is marked missing: no independent check of design-loop states is recorded.
   - These 25 cells raise the missing-cell inventory from 1,009 to 1,034.
5. **Liu et al.'s bound.** T14's unit "grid voxels (over)" now renders as "over 1,000,000,000 grid voxels". The same
   rule now keeps Hou et al.'s "(up to)": "up to 63,000,000 elements". The cell asserts the qualifier in T14's unit,
   and the verifier requires the word in the rendered cell (`must_render`).
6. **Recursive-control capacity row.** The size cell reads "65.5 × 10⁶ (historical completion)" with note c. The
   next-size cell separates the two runs at 113.2M: "prespecified run not admitted (prediction); a run outside that
   rule completed the cantilever, 23 of 76 states above 1e-5". These cells assert T27's confirmatory class "guard
   prediction", the exploratory class and the record's EXPLORATORY label. The paper-wide maximum is unchanged.
7. **The verifier checks the rendered files.** `verify_sources.py` now parses every `tables/*.tex` row by row and cell
   by cell, and does the same for the Markdown mirror `comparison_tables.md`.
   - Each rendered cell must equal its traced text, and the number and assert checks run again on the rendered text.
   - Headers must show no number (column spans and 10⁻ᵏ thresholds aside).
   - The banned-word scan now also covers the suggested caption notes.
   - Three planted faults were added: a number changed in the TeX only, a number changed in the Markdown only, and a
     bound qualifier dropped from the TeX. All 12 are caught.
   - The checker's own test (648 → 250 in the TeX input only) now gives 3 problems: text mismatch, unsourced number,
     cited value not rendered (`scratch/checker_test_fix2.py`, `logs/checker_test_fix2.out`).

## 0c. Corrections after the first check (fix round 1)

The previous outputs and scripts are kept in `logs/fix1_prev/`. `scratch/diff_values.py` compares every cell value of
the old and new `comparison.json` by row id and field (`logs/value_diff_fix1.json`). Only these values changed: steps,
per-step mean and residual factor of the six historical Hou solve rows (item 1). No pair ratio changed. The 35 E29
beam rows were renamed (`_own`, or `_common` for the FP64-arithmetic node); `scratch/diff_beam.py` compares their 315
values under the new names and finds no difference. Everything else is added fields, labels and tables.

1. **Hou CG step count (E10).** The released `CG.CG` returns the zero-based loop index `i` after the iterate update of
   its last iteration (`external/CuPy-for-TO/cupy_for_TO/CG.py:23, 29, 38`). E10 stores it unchanged
   (`experiments/E10_external_hou.py:114, 116`). Each historical Hou row now keeps that index as `released_index_i`.
   `steps` is derived as index + 1 (op `add1`), and the step mean and the residual factor use it:
   - steps at 8,192 / 65,536 / 524,288 / 1.02M / 4.19M / 8.19M elements are 327, 632, 1,262, 1,591, 1,972 and 2,458
     (were one fewer);
   - the factor at 524,288 elements is 0.9974066 (was 0.9974045); the step mean is 5.187 ms (was 5.191 ms).

   Two cross-checks agree with the corrected counts. T27's gate G1 gives 327 iterations at k = 16. T27's separate runs
   give 1,591 at 1.02M and 2,458 at 8.19M. The application ratios are unchanged. Our `pcg64` counts from 1
   (`code/src/voxfem/krylov.py:85-87`).
2. **Sparse construction limits belong to their protocols.** Both studies use the same `CSRBaseline`/`BSRBaseline`
   classes. They differ in the admission rule for the build:
   - the operator survey E2 builds only when 3 × the estimated storage fits (`experiments/E2_operators.py:97`);
   - the update-cost study E4 builds at 1.15 × (`experiments/E4_update_cost.py:65`).

   Each row and largest-size entry now carries its `admission` rule.

   | format | E2 survey: largest built / next | E4 update study: largest built / next |
   |---|---|---|
   | CSR, FP32 | 2.00M / 4.19M not built | 4.19M (SpMV 10.27 ms) / 8.19M not built |
   | BSR, FP32 | 4.19M / 8.19M not built | 8.19M (SpMV 11.03 ms) / 14.2M not built |

   Every refusal is a prediction under its own rule. The capacity table shows both rows per format. The supplementary
   sparse table adds the E4 section, and the wrong E4 note ("keeps its build workspace on the device") is replaced by
   the driver's own rule.
3. **Matched Hou table, application columns.** `tab_supp_hou_matched` now has two columns:
   - *Krylov operator*: Hou's operator for Hou; the FP64 node operator for FP64 PCG (30.7 ms at 33.6M); the inner FP32
     stencil for IR;
   - *V-cycle stencil*: the FP32 fine-level stencil, original or repaired (1.22 and 1.30 ms at 33.6M).

   Each solve row names both application rows (`applications`). Timing flags are now shown (superscript f, asserted
   against `timing_flag`) on the 8.19M stencil applications and the 8.19M FP64 PCG solve and step times, as T27
   flags them (`tasks/T27/REPORT.md:207`).
4. **T27 Krylov-step boundary.** The boundary is now cited from the drivers:
   - ours: one CUDA event at the entry of each preconditioner call; a step is the interval to the next entry, and for
     IR only within the same outer step (`tasks/T27/drivers/hsys.py:70-98`, `hrun.py:325-327`);
   - Hou: one event at the start of each iteration (`hou_instr.py:39-41`, `hrun.py:248-257`).
5. **Accuracy labels of time ratios.** Each T28 solve-ratio label is now computed from the two independent
   residuals:
   - k ≤ 160: "at unequal accuracy";
   - 33.6M and 65.5M: "accuracy relationship unresolved (no independent residual for at least one path)".

   Operator-only ratios carry no accuracy label, because they have no solve endpoint. The blanket sentence in the
   report is replaced (Section 8).
6. **T28 timing qualifications.**
   - Each fixed-state row carries its whole-solve G4 cells, scoped "whole fixed-state solves only". It also carries its
     step-level class and bound (`times/krylov_step/g4_step`).
   - Step-ratio labels are built from both rows' step classes. The released 4.19M/S1 step is cleared (2.94 %); the
     others at 0.52M and 4.19M are unresolved.
   - In `tab_supp_traeff`, only step times carry the "u" mark (asserted against the row's step class). Solve times
     carry no step-duration qualification.
   - Design-loop rows give the G4 class counts of their solves and design steps, and list the unresolved solves: the
     instrumented k = 64 record run, iterations 1–4, bounds 161.1, 121.2, 135.2 and 51.6 %. N and L solves clear the
     threshold at whole-solve resolution; L design steps at k = 128 and 160 are all ok.
   - Each workload has its own design-timer boundary. R's timer starts after the untimed transfer and dumps (T28 D36).
   - The sampler limitation (`tasks/T28/g4_activity.json#/limitation`) is attached to every T28 row, stated in
     `t28_status` and in the supplementary note.
7. **Literature kind.** The table now uses T14's own classification, the words before its first qualifier: the
   7,380 s Futhark run reads "measured", and the two OpenMP figures read "published estimate". Each cell asserts
   this against `kind`.
8. **All E29 beam controls.** All 13 controls per grid (65 rows) are now in `comparison.json`: six operators with
   their own V-cycle, the same six with the common original-stencil V-cycle, and the FP64-arithmetic node kernel
   (common only). The floor and rounded-operator residuals are included. A new supplementary table,
   `tab_supp_beam_controls`, puts own and common side by side.
9. **Setup on every row.** Every one of the 310 rows now has a `setup` field: a cited value with its boundary, or the
   reason it is missing. `build_comparison.py` stops if a row lacks one. Added where measured:
   - T27 application rows (both setups, e.g. 0.0670/0.0152 s for the k = 80 original stencil; boundary corrected in
     fix round 2, item 1: operator construction only, no hierarchy);
   - E2/E4 sparse builds;
   - optimization `setup_s` (construction before the loop) and `totals.setup_s` (multigrid updates inside the loop);
   - memory-probe `construct_s`;
   - the T28 design loops' per-solve setups.

   E10's `our_setup_s` is missing: the current driver writes it (`E10_external_hou.py:142`), but the saved records do
   not contain it.
10. **Per-cell provenance, verified.**
    - Every derived cell now has a machine-checkable `op` (div, add1, factor, two_k_cubed, count, median, mean,
      min/max, rel_change, hist over a record's `history`). `verify_sources.py` recomputes all 813 of them
      independently; a derived cell without an op is reported as a problem.
    - Every table cell is either a label, which the verifier rejects if it contains a number, or a value cell that
      points into `comparison.json` with scale and offset, or as a cited text. Status words carry asserts on cited
      cells (e.g. "verified" requires an independent residual ≤ 1e-5; "not admitted" requires the class "guard
      refusal").
    - The verifier follows each pointer to the record, parses the rendered numbers (×10^e, thousands separators, k/M
      suffixes, e-notation) and requires each to equal a cited value within half a unit of its last digit.
    - The former null-source cells (native stop, residual 0.387, capacity refusals, precision columns, section
      headers) are now sourced: T27/T28 text fields are CSV cells, and the historical native stops and Krylov
      precisions are basis cells with code locations.
    - Writing the asserts exposed one wrong value: T27's confirmatory class for the original-stencil recursive control
      at 113.2M is "guard prediction". The table wording "not admitted under the prespecified rule" was right; the
      assert value is corrected.

## 1. What was built

| File | Content |
|---|---|
| `comparison.json` | 310 rows in 10 blocks, 58 derived pairs (ratios with their orientation), 39 largest-size entries, the recursive-control summary by problem, the paired-timing orientation check (with its cells), the 24-entry literature block and an inventory of 1,034 missing cells. |
| `tables/*.tex` | Eleven LaTeX tabular bodies in the manuscript's booktabs style: three for the main text (`tab_comparison_external`, `tab_comparison_capacity`, `tab_comparison_cost`) and eight for the supplement (Hou historical, Hou matched, Träff, recursive control, precision controls, beam controls, sparse, literature). |
| `comparison_tables.md` | Markdown copy of the eleven tables, each followed by suggested caption notes. |
| `table_sources.json` | For every table cell: label, or the comparison.json cells it shows and the asserts it makes. |
| `verify_sources.json` | Result of `verify_sources.py --selftest`. |
| `build_comparison.py`, `make_tables.py`, `verify_sources.py` | The scripts. Regenerate with the three commands in Section 9. |

Inputs and their state:
- T14: final. 131/131 quotes verified (`tasks/T14/quote_check.json`). The literature block is copied as cited cells.
- T27: final (last attempt; frozen plan unchanged). Confirmatory and exploratory values are kept apart. Every T27 row
  carries its `endpoint_status` as provenance.
- T28: complete. Measurements are final, with the four reporting corrections D34–D37. The 33.6M and 65.5M
  fixed-state rows are labelled descriptive (system-identity gate and independent residual missing).
- Historical records: E2, E4, E7, E8, E10, E12, E12b, E29 and E32 under `results/`, read in place.

## 2. Cell convention and checks

Each value is one of:
- `{"v", "src": "file#/json/pointer"}` (JSON record);
- `{"v", "src": "file:line#column"}` (CSV row);
- `{"v", "formula", "op", "operands"|"params"}`, derived here and recomputable from the operands or the named record;
- `{"v": null, "missing": reason}`;
- `{"v", "basis"}`, a label fixed by code (with its location) or by a frozen plan.

`results/` paths are relative to the authors' project folder, and `tasks/` paths to the run's work folder.

`verify_sources.py --selftest` (`verify_sources.json`, `logs/verify_sources.out`) gives:
- 7,639 cells checked: 5,050 record values equal their source; 627 cells are marked missing and are also empty in
  their source; 825 derived cells recompute; 610 basis cells; 527 missing cells with no source.
- 1,763 traced table cells: 1,304 value cells, all resolved to their records with every rendered number and every
  assert confirmed; 459 labels with no number; 0 cells without a source.
- 3,526 rendered cells (the 1,763 cells in the final TeX files and again in the Markdown mirror): each equals its traced
  text, and its numbers, asserts and required qualifiers are checked again from the rendered text. Markdown rows are
  split as a renderer splits them, and every row has its header's cell count.
- 0 problems. The table text and the suggested caption notes are free of run labels, file names, dates, seeds,
  hashes and budget words.
- All thirteen planted faults are caught: an altered record value, a wrong pointer, a wrong CSV column, an altered
  ratio, an altered derived operand (the off-by-one), a run label in a table, an altered rendered digit in the source
  map, a table value with its source removed, a false status assert, a number altered in the final TeX only, a number
  altered in the Markdown mirror only, unescaped norm bars in the Markdown mirror, and a bound qualifier dropped from
  the TeX.

All eleven tables compile with pdflatex (`scratch/textest/`).

## 3. What each row specifies

Every row carries the fields `system`, `elements`/`dofs`, `start`, `code`, `operator`/`operator_precision`,
`krylov_precision`, `residual_precision`, `iterate_precision`, `native_stop`, `status`, `steps` (and `inner_steps` for
IR), `achieved_true_residual` (with its `kind`), `residual_factor_per_step`, `setup` (with its `boundary`), `times`
(each with `unit`, `denominator`, `statistic` and `boundary`) and `memory` (each with its `definition`). A field that
does not apply holds a reason. `setup` is now enforced on every row.

Timing denominators used:
- per application;
- per solve;
- per Krylov step (IR: inner step; outer residual separately, per outer step);
- per design iteration (state solve + design step);
- per design step (with the design timer of its workload);
- per optimization (sum of the per-iteration times).

The historical optimization runs and the E10 rows also get a run-mean time per step, labelled as a mean and not a
synchronized per-step time.

Step-timer boundaries:
- T27 ours: preconditioner-entry events; for IR, intervals within an outer step.
- T27 Hou: iteration-start events.
- T28: the `timing_boundary` cell of each row. Released: between consecutive iteration ends. Ours: CUDA events at
  consecutive preconditioner calls.

Memory definitions are kept apart:
- CuPy pool used/reserved: sampled at explicit points in the historical runs, from an allocation hook in T27/T28;
- process-dedicated WDDM peak;
- job dedicated peak M1 (for the released OpenMP code: growth of the WSL VM worker);
- device-wide peak (includes other processes);
- assembled-matrix storage;
- accounted bytes per element.

E10 measured no memory, and its rows say so.

## 4. Geometric-mean residual factor

The factor is (r_end/r_start)^(1/n). It is computed only when both residuals are FP64 true residuals of the same
system, both are positive and finite, and n > 0. n is the number of completed Krylov steps; for IR it is the number of
inner FP32 PCG steps. r_start = 1 exactly for a zero start. For a warm start, r_start is the recorded true residual of
the start iterate: T28 S5 from its residual history, and the historical optimizations from `rel_initial` per solve.
For an optimization the factor is exp(Σ log(r_end/r_start) / Σ n) over the design-loop solves.

The factor is not computed in these cases, each recorded with its reason:
- the released OpenMP code at 33.6M and 65.5M (no FP64 residual);
- every breakdown;
- the rounded-coefficient diagnostic (its residual belongs to the rounded operator).

At 33.6M and 65.5M our T28 paths use the in-solver FP64 residual, flagged "not independently checked". Values
(`comparison.json`):

| system | path | steps | FP64 true residual | factor per step |
|---|---|---|---|---|
| Hou, 0.52M (E10, one process) | released CuPy CG | 1,262 | 0.0377 | 0.99741 |
| Hou, 33.6M | released CuPy CG | 3,930 | 0.387 | 0.99976 |
| Hou, 33.6M | FP64 PCG, repaired | 21 | 5.96e-6 | 0.564 |
| Hou, 33.6M | IR, repaired | 5/28 | 2.44e-6 | 0.630 |
| Träff, 8.19M, S1 | released OpenMP PCG | 16 | 8.33e-4 | 0.642 |
| Träff, 8.19M, S1 | FP64 PCG, repaired | 9 | 9.11e-6 | 0.275 |
| Träff, 8.19M, S5 | released OpenMP PCG | 1,000 (cap) | 6.52 | 1.000004 (the residual rose from its start of 6.50) |
| Träff, 8.19M, S5 | FP64 PCG, repaired | 32 | 6.13e-6 | 0.648 |

A factor counts residual reduction per step. The steps differ in cost (an unpreconditioned FP32 CG step against a
V-cycle PCG step), so the factor is read together with the step time.

## 5. Paired-timing orientation (`comparison.json` → `orientation_check`)

**Order.** The nine 65.5M cantilever runs of the fine-level operator swap form three blocks by start time. Each block
contains each operator once and equals one repetition index. Each operator holds each position once (a balanced Latin
square). Pairs are formed within a repetition.

**Orientation.** The change is (t_operator − t_difference)/t_difference, so a positive value means the operator is
slower. The times, means, paired changes and their range are now also cells (`changes/<op>/cells`), recomputed by the
verifier from the records' histories.
- Original stencil: paired changes +1.48 %, +1.44 % and −0.57 %. Their mean is +0.8 %, the range −0.6 % to +1.5 %,
  and the ratio of the means is also +0.8 %.
- Atomic element kernel: paired changes +17.7 %, +17.8 % and +15.9 %. Their mean is +17.2 %, the range +15.9 % to
  +17.8 %.

The per-repetition times, the means, the signs and the ranges all equal the submitted Table `tab:swaps`. All runs take
76 design iterations.

**Applications.** The difference form takes 1.0762 times the original stencil (+7.6 %). The atomic element kernel takes
4.94 times the difference form. The element-mean kernel takes 0.987 times the atomic kernel. Each ratio states its
orientation in `pairs`. Hou ratios are given as Hou/ours (> 1: Hou slower), the released OpenMP code as
released/ours, and P11 as repaired/original.

## 6. Results that the acceptance statement names

- **The 648-fold row.** Its source is `results/E10/hou_k64.json`, at 524,288 elements: their 23.88 ms against 0.0369 ms
  for our *original* stencil with their element matrix, a ratio of 647.8. Over the seven historical rows the
  application ratios are 114.3, 185.8, 647.8, 196.8, 192.7, 223.3 and 250.3. The range is therefore 114–648, not the
  "114 to 250" of the submitted main text (main.tex, Section "Cost"). Both codes ran in one process, and their call
  includes per-call allocation as released.
- **The operator-only row.** At 33.55M elements, E10 has the application only (ratio 250.3) and no solve; its row says
  so.
- **The mixed-precision recursive control and its residuals by problem** (FP32 PCG + FP32 V-cycle, FP64 iterate,
  recursive stop at 1e-5, no FP64 test; `recursive_control_by_problem`; supplementary table
  `tab_supp_recursive_control`). States above 1e-5 among the design-loop states:

  | problem | 8.19M: above 1e-5 (largest) | 65.5M: above 1e-5 (largest) |
  |---|---|---|
  | cantilever | 22 of 77 (9.50e-4) | 22 of 76 (2.74e-3) |
  | torsion | 13 of 76 (1.84e-4) | 18 of 76 (4.97e-4) |
  | bridge | 34 of 76 (3.75e-3) | Krylov breakdown (negative curvature) after 15 design iterations; all 15 states above 1e-5 (largest 1.98e-3) |

  T27's exploratory 113.2M runs are listed with their labels: repaired 0 of 76 states above 1e-5, original 23 of 76.
- **Published figures** (`literature`, supplementary table `tab_supp_literature`). Each keeps its own device, code,
  workload and T14's own kind (measured, published estimate, demonstrated run, stated), with its T14 quote ids. No
  published figure enters a ratio. The graphical-only memory entry is marked dropped.
- **Largest sizes with their pass or refusal status** (`largest_sizes`, main table `tab_comparison_capacity`):
  - Matrix-free application: 268.4M, both precisions, no spill.
  - Assembled formats, each under its own build rule: CSR FP32 to 2.00M (survey) and 4.19M (update study); BSR FP32
    to 4.19M (survey) and 8.19M (update study). The next grid in each study was not built: a prediction under that
    study's rule.
  - Hou's system:
    - Hou's CG reaches its native stop at 33.6M with FP64 residual 0.387 and is not verified;
    - our FP64 PCG (both V-cycles) and repaired IR are verified at 33.6M;
    - original-stencil IR is verified at 1.02M and breaks down at 8.19M and 33.6M.
  - Träff's fixed state S1 (the released first design state, from zero); the 65.5M sizes hold for S1 only:
    - the released code completes to 65.5M active elements (79.6M allocated) with its native stop and is verified at
      no size; at 113.2M it was not admitted (a prediction under the driver-reported free memory rule);
    - our FP64 PCG completes to 65.5M and is verified to 8.19M; at 113.2M it was not admitted;
    - repaired IR completes to 65.5M and is verified to 8.19M; at 113.2M it was stopped by the spill sampler.
  - Träff's fixed state S5 (warm start from the released fourth solution):
    - the released code completes to 8.19M (13.4M allocated) by reaching its iteration cap at every size, so its
      native stop is met at no size and it is verified at none;
    - FP64 PCG (both V-cycles) and repaired IR are verified at 8.19M;
    - no S5 state exists at 33.6M or above: the released record run that supplies it reached its wall cap at 33.6M
      and was not run above.
  - Träff's design loops (distinct workloads, no ratio): the released record run and our three matched-rule loops
    completed through 8.19M; at 33.6M the released record run was interrupted at its wall cap (class 6, with its
    unchunked transfers counted toward the cap), and our loops were not run.
  - Complete optimizations:
    - Repaired IR: all three problems at 113.2M (historical completions). At the same size the prespecified repaired
      cantilever run was not admitted: W = 18,448,734,655 B plus 1.5 GiB above the guard's effective-free-memory
      estimate (17,832,361,984 B in the counted session). T27 exploratory: completed, with independent residual
      4.61e-7. At 144.0M the predicted need is above what the card holds.
    - Original IR: cantilever and torsion at 113.2M; the bridge returns no design at 65.5M or 113.2M.
    - FP64 PCG: 65.5M, all three problems (historical completions). At the same size the prespecified repaired
      cantilever run, under its lower pool cap, met an allocation failure (out of memory in design iteration 3). At
      113.2M (original stencil): a spill without a cap, and out of memory with a 21.5 GiB cap.
    - Recursive-stop control: 65.5M, the largest historical completion. At 113.2M the prespecified run was not
      admitted under T27's rule ("guard prediction": predicted workspace plus 1.5 GiB above the guard's
      effective-free-memory estimate, not the driver-reported free memory). An exploratory run outside that rule
      completed the cantilever with 23 of 76 states above 1e-5. It is not a lower bound.
    - The paper-wide maximum stays at 113,246,208 elements.

## 7. Main-text tables (house rules applied: no file names, run labels or lab detail)

1. `tab_comparison_external` covers the same-card fixed-state comparison at the largest verified size of each
   external system: Hou's cantilever at 33.6M, and Träff's cantilever at 8.19M for S1 and S5. Columns: native stop,
   operator/Krylov/iterate precision, steps, independent FP64 true residual, factor per step, solve, Krylov step and
   memory. The supplementary tables give every size. The rule was the largest size at which every completed path of
   that system has an independent check. I applied it after reading the T27 and T28 reports, not before.
2. `tab_comparison_capacity` gives, by workload, the largest completed size, its status and the outcome at the next
   size. The two assembled-matrix build rules are separate rows. Träff's rows name their starting state (S1, S5), and
   the design loops have their own section.
3. `tab_comparison_cost` serves R1.2. It puts together:
   - application costs (+7.6 % difference form, +15.9 % self-block correction, 4.94× atomic, 35.4× FP64-arithmetic
     node);
   - the paired 65.5M cantilever times (149.1, 150.2 and 174.6 s);
   - the beam control at 2.10M elements, 64 through the depth (119.59 % against 2.42e-6);
   - the breakdown at 16.8M;
   - the bridge outcomes (original IR: no design; original recursive control: breakdown; FP64 PCG completes in
     432.4 s original and 475.6 s repaired; repaired IR completes at 113.2M in 851.9 s);
   - the IR solve on Hou's system at 1.02M (0.934 s with 18/240 steps against 0.0960 s, a ratio of 0.103).

## 8. Notes for the writer and the response

- Correct "114 to 250 times" (main text, Cost section) to 114–648. These ratios are against the original stencil.
- If the paper cites Hou's historical iteration counts, use the completed counts (index + 1), e.g. 1,262 at 0.52M.
- Memory against Hou: the prespecified comparison is inconclusive (T27 P6), because the timed processes retain two
  builds. Do not state an ordering as a result. The single-build peaks come from separate runs outside the
  prespecified protocol. In them our paths' dedicated peaks lie below Hou's, but that ordering is exploratory. Hou's
  16.66 GB dedicated peak there is mostly reserved pool memory and depends on the pool cap (T27 Section 2.3). By live
  pool allocation at 33.6M, Hou's 4.74 GB lies between FP64 PCG's 6.46 GB and IR's 4.43 GB. The device-wide peak
  covers the samples taken while the process ran. For the original-stencil IR at 1.02M, the sampling covers the
  period from the spill watcher's first baseline onward, not the whole process. The table notes say this.
- Accuracy of the time ratios:
  - Where both sides have an independent check, every solve-time ratio against a released code is at unequal
    accuracy: Hou's system at 1.02M and 33.6M (confirmatory checks), and Träff's at 0.52M, 4.19M and 8.19M. Neither
    released code reaches 1e-5 at any checked iterate, so no equal-accuracy speed ratio exists there.
  - On Hou's system at 8.19M both independent residuals come from the replacement checker outside T27's protocol, and
    T27's prespecified every-grid test (P1) is unresolved. The unequal-accuracy reading there rests on exploratory
    evidence only, and the ratio is labelled that way.
  - On Träff's system at 33.6M and 65.5M the independent checks are missing, so the accuracy relationship is
    unresolved.
  - Operator-only (application) ratios have no solve endpoint and carry no accuracy relationship.
  - At S5 the released OpenMP code stops at its 1000-step cap: its residual is 6.52 at 8.19M and 7.09 at 4.19M.
- Interference rule (T28):
  - Whole-solve bounds cover whole fixed-state solves only: none is excludable.
  - At step duration the rule is unresolved for every row at 0.52M and every row at 4.19M except the released S1
    step (2.94 %). The step ratios there are reported as measured, not as cleared.
  - Released step times come from its timing build, which ran 10.4 % faster than the plain build (G5).
  - Design-loop solves: N and L clear the threshold at whole-solve resolution; the instrumented record-run solves of
    iterations 1–4 at 0.52M are unresolved. R's design steps have only whole-job bounds.
  - The sampler bounds cover the processes it enumerated at its start.
  - The design loops are distinct workloads with no ratio (P8 contradicts; `D2_traeff_design_workload`).
- In the 8.19M matched Hou rows, the stencil applications and the FP64 PCG solve and step times carry T27's flag
  (foreign activity 1–5 %, not excluded). The independent residuals at 8.19M come from a check outside T27's protocol.
  The tables word this without run labels.
- The beam controls with the common V-cycle hold the preconditioner fixed. With it, the difference form gives
  3.35e-6 at 4,096 elements, against 3.17e-6 with its own V-cycle (`tab_supp_beam_controls`). The original stencil's
  error is the same configuration either way.
- The submitted "17.2 %" and "+0.8 %" are means of the paired changes; the ratio of the means gives the same values.

## 9. Acceptance

| Acceptance clause | Result |
|---|---|
| Finalize after T27, T14 and T28 | Met: T27 final, T14 final, T28 complete. |
| Missing measurements marked | Met: 1,034 cells carry a reason; the verifier confirms that every cited cell marked missing is empty in its source. |
| The 648-fold original-stencil row | Included. |
| The operator-only row | Included. |
| The recursive control with its residuals by problem | Included. |
| Published figures stay with their own device and workload | Met, with T14's own kind for each figure. |
| Correct pass or refusal status for all largest sizes | Met: each status cites its record and is asserted against it. Predictions are labelled as predictions under their own admission rule (T27: the guard's effective-free-memory estimate; T28: the driver-reported free memory; E2/E4: their storage multiples), spills as spills. T27 exploratory and historical completions keep their labels, with the prespecified outcome at the same size beside each historical completion. Träff's entries name their starting state; S5 and the design loops end at 8.19M, with no S5 state at 33.6M. |

Regenerate with `python build_comparison.py`, `python make_tables.py` and `python verify_sources.py --selftest`.
`scratch/textest/` holds a compile test of the eleven tables (pdflatex, booktabs): it compiles with no error.
`scratch/checker_test_fix2.py` repeats the checker's TeX-only tampering test (read-only). `scratch/diff_values_fix3.py`
compares the cell values with `logs/fix3_prev/comparison.json`.
