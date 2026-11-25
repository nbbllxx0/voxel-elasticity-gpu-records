# T27 report: matched comparison with the released Hou et al. code, and single-card capacity

Every number below is read from a file under `tasks/T27/`. The main tables are:
- `hou_matched.csv`: confirmatory Hou-system rows, with `endpoint_status` and `note` per row;
- `hou_exploratory.csv`: the exploratory re-measurements made after the implementation check;
- `capacity.json`: capacity entries;
- `predictions.json`: prediction outcomes and gates;
- `residual_histories/*.csv`: residual histories.

Each per-run record is `out/<name>.json`. Historical values are quoted from project files and labelled as such.
Departures from the frozen plan are in `DEVIATIONS.md` (D1–D23). Runs labelled EXPLORATORY lie outside the plan's
rules. They never enter a confirmatory outcome.

## 0. Corrections after the implementation checks

### 0.0000 Sixth check (operator note of 2026-11-23 15:25; D23)

Reporting corrections only. No measurement was repeated or added, and no class, prediction outcome, gate, capacity
entry or confirmatory value changed.
1. **The three k = 80 original-stencil IR memory runs** agree in pool used, pool reserved and process-dedicated
   peaks (163,632,640, 178,890,752 and 576,897,024 B). Their device-wide peaks above baseline differ as measured:
   622,854,144 B in the first run and 576,716,800 B in the later two (`out/X_MEM_k80_mgir_orig__v1_watcher_gap.json`,
   `out/X_MEM_k80_mgir_orig__v2_no_gap_check.json`, `out/X_MEM_k80_mgir_orig.json`). Earlier text said all three
   gave the same peaks.
2. **Coverage of the k = 80 memory run** runs from the watcher's first sampler baseline onward, not over the whole
   process. That baseline already held 77,594,624 B shared.
3. **Hou setup in `hou_matched.csv`.** The six `hou_cg32` rows had setup timers whose boundaries differ from the
   frozen endpoint (D16). Their setup columns are now marked exploratory (`setup_status`, `endpoint_status`). They
   hold the separately labelled exploratory measurements with the plan's boundaries (`out/X_SETUP_k*.json`, named in
   `setup_source_file`). The recorded values are kept in `setup_*_recorded_offboundary_s`.
4. **P5b.** The k = 160 `mg64` ratio, 0.953, is exploratory. Its action check comes from the exploratory replacement
   checker, outside the system-identity gate. P5b is decided by the k = 80 IR ratio, 0.103 (Section 2.4).
5. **Sampler spacing.** The probe's printed median was the upper of the two middle intervals. The intervals were not
   saved, so the median is dropped; the minimum and maximum stay (D23).

### 0.000 Fifth check (D22)

1. **Baseline of the live spill watcher.** `guard.SpillWatch` fills an absent counter with 0. The launcher handed
   its start sample to the watcher, so an empty counter response would have armed the watcher with a zero
   baseline. The watcher now takes its baseline from its own first published WDDM sample. That sample must hold
   this process's dedicated and shared counters. Otherwise arming fails closed and the job does not start
   (coverage lost). `guard.SpillWatch`'s start sample is kept in the record for information only.
2. **Continuity of coverage.** Consecutive checked samples, the baseline included, may now be at most 3 s apart.
   While the watcher is armed, the last checked sample may be at most 5 s old. A larger gap, or a sample whose
   timestamp cannot be read, stops the job at once with coverage lost. This also applies to the post-job check.
   The limits come from a CPU-only probe of the sampler (`logs/sampler_spacing_probe.out`): 37 samples spaced
   1.004–1.156 s. Every checked sample's timestamp, shared usage and dedicated usage is now kept in the record, so
   continuity can be checked independently.

Eleven CPU-only cases (`logs/test_xmem_p6_watcher_v3.py`, `.out`) give the expected stop or pass. The baseline
cases run the launcher's own arming step with the production `guard.SpillWatch`.

| case | expected exit | result |
|---|---|---|
| checker's case: empty counter response, zero-filled guard start sample | 5 | 5, at arming |
| no published sample | 5 | 5, at arming |
| baseline without a shared counter | 5 | 5, at arming |
| checker's replay: 29 s gap, then a valid post-job sample | 5 | 5 |
| no new sample for more than 5 s | 5 | 5 |
| the D21 case: late shared counter, 300 MiB growth | 4 | 4 |
| missing shared counter | 5 | 5 |
| unrelated process only | 5 | 5 |
| no spill | 0 | 0, covered |
| spill in the post-job sample | 4 | 4 |
| no post-job sample | 5 | 5 |

The k = 80 `mgir_orig` memory run was repeated once more with the revised watcher. It took 29 s, and no other GPU
job was active.
- The baseline was 77,594,624 B, equal to `guard.SpillWatch`'s start sample.
- After the baseline, 14 samples were checked, the last one taken after the job ended.
- The largest gap was 1.069 s, and shared growth was 12.6 MB. Coverage held from the first sampler baseline onward,
  not over the whole process; that baseline already held 77,594,624 B shared (D23).
- Pool used, pool reserved and process-dedicated peaks equal those of both earlier runs to the byte. So do the
  iterations and the in-solver residual. The device-wide peak minus baseline, 576,716,800 B, equals the D21 run's;
  the first run measured 622,854,144 B (D23).
- The D21 record is kept as `out/X_MEM_k80_mgir_orig__v2_no_gap_check.json` and is not used.

No class, prediction outcome or confirmatory value changes. The D21 test (`logs/test_xmem_p6_watcher_v2.py`) was
written for the earlier watcher interface and is kept as a record; v3 replaces it.

### 0.00 Fourth check (D21)

1. **Spill watcher of the k = 80 memory run.** The earlier watcher of `drivers/xmem_p6.py` marked a sample as
   checked as soon as its dedicated counter arrived. A shared counter of the same timestamp that arrived later was
   never checked. The WDDM sampler now publishes a timestamp only once all of its counters are in, that is, when a
   later timestamp arrives. The watcher reads published samples only. A sample without this process's dedicated
   and shared counters stops the job at once with coverage lost. A final sample taken after the job ends is
   checked before the watcher disarms. Seven CPU-only cases (`logs/test_xmem_p6_watcher_v2.py`, `.out`) give the
   expected stop or pass:
   - the checker's case: dedicated counter first, then 300 MiB shared growth at the same timestamp;
   - a missing shared counter;
   - a sample with only an unrelated process;
   - an empty baseline;
   - no spill;
   - a spill in the post-job sample;
   - no post-job sample.

   The run was then repeated once (28 s, no other GPU job). The revised watcher checked 15 samples, the last one
   taken after the job ended, and coverage held from its first sampler baseline onward (D23). Its pool and
   process-dedicated peaks equal the earlier run's to the byte. The earlier record is kept as `out/X_MEM_k80_mgir_orig__v1_watcher_gap.json` and is not used.
2. **Pool peaks without a pool measurement** are now missing, not 0. This covers the three reference solves, the
   two original-stencil IR breakdowns, the Hou setup re-measurements and the refused capacity records, none of
   which enabled the pool hook (`hou_matched.csv`, `hou_exploratory.csv`, `capacity.json`).
3. **Reference resolution.** The solve table in Section 2.2 and `hou_matched.csv` now carry the checker's flags.
   A compliance error below 10 × the reference residual is not resolved by the reference.
4. **Exploratory density archives.** Four designs were saved: three at k = 384 (repaired IR, repaired recursive
   control and original-stencil recursive control) and one at k = 320 (`mg64`). All are exploratory (Section 3.2).

### 0.0 Third check (operator note of 2026-11-23; D20)

No measurement was repeated. One short exploratory memory run was added (item 7).
1. **P5a and P4.** P5a now applies the system-identity gate as P3a does. At k = 160 the G2 action gate rests on
   the exploratory replacement checker, so the k = 160 ratio is exploratory. P5a's criterion covers every k, so
   P5a is **inconclusive (unresolved)**; before, it was supported. P4 also reads its k = 160 value as exploratory,
   and P4 stays inconclusive (unresolved).
2. **P1.** P1 keeps the plan's denominator: every k with a completed Hou solve, k = 160 included. The confirmatory
   independent residual is missing at k = 160, so P1 is **inconclusive (unresolved)**; before, it was supported.
   The exploratory k = 160 result is listed beside it.
3. **Historical optimizations** no longer carry class 9 or 8. None meets T27's class rule: there is no independent
   check of the final state, and spill was not sampled continuously. They are labelled historical completions, and
   they still carry the paper-wide maximum (Section 3.1).
4. **Exploratory Hou setup times.** The G4 activity during setup is unknown, because each process has only a
   process-wide mean. The differences between versions are no longer attributed to run-to-run variation
   (Section 2.2).
5. **Hou's 8.2, 65.8 and 287.5 ms** are solve-start overheads: load and support construction, survivor indexing,
   residual formation and garbage collection. They are not residual formation alone. Their achieved recursive
   residuals are now given (Section 2.2).
6. **P5b** is stated by its ratios and the ±15 % band. The report no longer says the repair costs nothing per solve.
7. **Memory.** P6 stays inconclusive. The original-stencil IR single-build peak at k = 80 was measured in one short
   guarded exploratory run and added to Section 2.3. (Its watcher had a gap; the run was repeated under the
   revised watcher; see 0.00, item 1.) At k = 160 and 256 it is missing, because that path breaks
   down there.
8. **Capacity.** The first k = 384 IR admission evaluation overlapped another job. It stays without evidential
   weight, and the confirmatory bounds stay as the frozen rule left them. The exploratory k = 384 designs are
   reported as exploratory, with their admission and cap (Section 3.2).

### 0.1 Second check

The second check's eight findings changed the following. Details are in D10, D16, D17 and D19.

1. **P7 is now inconclusive (unresolved).** Its support criterion requires d_S(repaired) < d_S(original) at every
   k, without a "with data" qualifier. The confirmatory values hold at k = 80 and 256, and the exploratory k = 160
   value agrees, but there is no confirmatory d_S at k = 160. The driver no longer returns support from two grids.
2. **k = 160 solve classes.** `mg64_orig`, `mg64_rep` and `mgir_rep` at k = 160 no longer carry class 9 in
   `hou_matched.csv`. Their in-process acceptance stands, but class 9 needs an independent confirmation, and the
   only one is exploratory (D9). The confirmatory class is blank, and `exploratory_class` = 9. P8 stays
   contradicted on the class-5 breakdowns, which the solve processes recorded.
3. **One timing standard for P4 and P5a.** The k = 160 application timings had been called descriptive for P4
   but were used for P5a. Both predictions now use all application timings as recorded under G4, with the same
   caveat, which applies at every k: G4 cannot detect foreign activity during an application timing that is much
   shorter than its 10 s sampling interval. P4 stays inconclusive because its k = 160 value falls in the gap
   between the thresholds (D12). P5a stays supported, with the caveat attached. (Superseded by 0.0, item 1: P5a
   is now inconclusive, and the k = 160 values of P4 and P5a are exploratory.)
4. **Hou setup (a) boundary.** The first exploratory setup records timed the allocation and filling of the FP32
   density grid inside (a). The density grid is now created before the timer, and the three setup processes were
   rerun (Section 2.2; the first records are kept as `out/X_SETUP_k*__v1_density_in_a.json`). Setup (b) and P3a
   were unaffected.
5. **C1's first admission evaluation.** It ran while the k = 256 Hou application process was still running,
   which breaks the one-GPU-job rule. Its reading is not an isolated memory availability and now counts as no
   evidence (`capacity.json` → `admission_evaluations`, `isolated: false`). C1's class 2 rests on the
   session-2 and session-3 refusals (D10, D19).
6. **Hou's single-build excess.** It is 134,218,240 B, that is, one survivor index (134,217,728 B) plus
   512 B, not "exactly one index" (Section 2.3).
7. **Spilled historical records.** The two class-4 records (E12, E23: `mg64` at k = 384) keep their
   classification in `capacity.json`, but none of their measurements are exported any more.
8. **Sources and wording.** Paired key numbers now cite both records. P5b is contradicted by the completed k = 80
   IR time ratio (0.103, IQRs disjoint). The k = 160 and 256 breakdowns contradict P8 and give no P5b ratio.

### 0.2 First check

The first check's eight findings changed the following. Details are in D6, D8, D9 and D11–D18.

1. **Solve memory (P6).** The H3 process peaks retained workspaces of two builds. In our processes the timing
   wrapper held the first multigrid hierarchy while a second one was built. In Hou's process the driver held a
   survivor index while their CG built its own. P6 is now **inconclusive**; it was a contradiction before.
   Single-build, single-solve peaks were re-measured as exploratory runs (Section 2.3).
2. **k = 160 checker.** The values of the replacement checker are now **exploratory** (D9). This covers d_R, d_S,
   the independent residuals and the compliance and energy errors at k = 160. P1 and P3a are decided on k = 80 and
   256. Their criteria cover every k with a completed solve, and the G2 gate rule, respectively. P7's criterion
   does not, so after the second check P7 is unresolved (0.1, item 1). (Superseded for P1 by 0.0, item 2: k = 160
   has a completed Hou solve, so P1 is unresolved. P3a keeps its two-grid decision under the G2 gate rule.)
3. **G2.** G2 was evaluated after the solves; the confirmation is retrospective (D13). Hou's application process
   at k = 256 copied two 406.6 MB vectors to the host for the capture, outside the transfer protocol (D15). An
   in-protocol rerun is in Section 2.3.
4. **Timing gate.** G4 cannot establish foreign activity during the 0.07 s application timings. The low SM clocks
   were read only in later diagnostic processes. P4 is unresolved (D6, D11, D12). After the second check, the
   k = 160 timings are no longer singled out as descriptive: P4 and P5a use them under the same standard (0.1,
   item 3).
5. **Hou setup timings.** The confirmatory Hou setup (a) included staging of the source tree, and setup (b)
   included a `gc.collect`. They were re-measured (D16, Section 2.2); the boundary of (a) was corrected again after
   the second check (0.1, item 4). P3a is unaffected, because it uses our setup (b).
6. **Histories.** The continuation was tested at 201, 201 and 41 checkpoints only (D18). The breakdown
   trajectories of the original-stencil IR were re-recorded as exploratory runs.
7. **Exploratory capacity.** The wording is corrected: bytes per element from one grid do not establish a
   requirement at 10⁹ elements, and mg64 at k = 352 exceeds the observed admission budgets, not the card (D8).
8. **Recursive controls.** The repaired and original counts are now cited from their own files. The native final
   solve is included in the counts. The checker's displacement is the post-certification state (Section 3.2).

## 1. Gates

| Gate | Result | Source |
|---|---|---|
| G1 code identity | pass. All 11 `voxfem` files and the 4 copied helpers match the `code_files` manifest of `results/E32/simp_cantilever_k384_mg_ir_stencil_diff.json`. The Hou tree matches `git ls-files -s` at d8dca7a. The instrumented CG with hooks disabled equals `FE.FE` at k = 16 (327 iterations each, iterate difference 0.0). | `out/V_G1_static.json`, `out/V_G1_cg16.json` |
| G2 system identity | pass at k = 80 and 256 (confirmatory). At k = 160, system identity passes (confirmatory, from the H2 Hou process); d_R passes, but on the exploratory replacement checker (D9). Results: fixed-DOF sets identical (12 DOFs); loads identical entry by entry (8 entries, sum 8); their initial iterate zero; d_R = 7.56×10⁻⁸ (Hou), 1.00×10⁻⁷ (original stencil) and 9.3×10⁻⁸ (repaired stencil) at every k. Evaluated after the solves, not before them (D13). | `out/H5_check_k{80,160,256}.json`, `out/H2_apply_k{k}_hou_cg32.json`, `predictions.json` |
| G3 checker validity (k = 16) | pass: relative difference 4.5×10⁻¹⁰ | `out/V_G3_k16.json` |
| G4 hook overhead (k = 80) | −0.48 % (Hou application), +0.13 % (repaired stencil); < 2 % | `out/H2_apply_k80_{hou_cg32,stencil32_rep}.json` |
| G4 foreign activity | No timed run exceeded 5 %, so none was excluded or repeated. Flagged (1–5 %): the k = 160 `stencil32_orig`/`stencil32_rep` applications and the k = 160 `mg64_orig`/`mg64_rep` solves. For the short application timings the gate measures activity near the timing, not during it (D6). | `hou_matched.csv` (`timing_flag`) |

No reported confirmatory measurement spilled. The first k = 160 checker run (`out/H5_check_k160__attempt1.json`)
met the spill criterion through transfer staging and is excluded. Its replacement lies outside the plan's repeat
conditions, so the endpoints that come from it are exploratory (D9).

## 2. Hou system (Q1, Q2): k = 80, 160, 256 (1,024,000 / 8,192,000 / 33,554,432 elements)

Paths and precision labels (`hou_matched.csv`, columns `operator_precision`, `residual_precision`,
`iterate_precision`, `native_stop`):
- `hou_cg32`: operator stored in FP32 (the generated kernels multiply FP32 entries by double literals and round
  each of the 24 row-kernel sums to FP32), recursive FP32 residual, FP32 iterate. Stops at ‖r‖ < 10⁻³‖r₀‖ or
  10,000 iterations.
- `mg64_*`: FP64 operator, FP32 V-cycle, FP64 true residual ≤ 10⁻⁵.
- `mgir_*`: inner FP32 PCG with an FP64-arithmetic outer residual ≤ 10⁻⁵.
- Every iterate starts from zero.

The reference is `mgir_rep` to 10⁻⁹. Its independent residual was 7.2×10⁻¹¹ at k = 80 and 8.0×10⁻¹⁰ at k = 256
(`out/H5_check_k*.json`), so it is named "10⁻⁹". At k = 160 the value is 1.8×10⁻¹⁰, which is exploratory (D9).

### 2.1 Operator application: median ms, IQR in `hou_matched.csv`; field R; E10 protocol (D7)

| k | Hou `honorAb` | stencil, original | stencil, repaired | FP64 `node_hoist` |
|---|---|---|---|---|
| 80 | 8.076 | 0.0481 | 0.0511 | 5.536 |
| 160 | 63.73 | 4.013 (flagged) | 4.182 (flagged) | 24.50 |
| 256 | 264.16 | 1.221 | 1.305 | 30.73 |

Sources: `out/H2_apply_k{k}_{path}.json`.

The k = 160 times of our stencils and of the FP64 operator are slower per element than at k = 256, so they are
not physical per-element rates. Their cause is not established for these timings.
- An EXPLORATORY diagnostic repeated the four timings in fresh processes (D11, `out/X_H2_apply_k160_*.json`).
  The stencil times came out again at 4.04 ms (original) and 3.97 ms (repaired). In those later processes the SM
  clock read 390 MHz and 555 MHz (P-state P5).
- The clock was not read in the confirmatory processes. Low clocks are a plausible explanation, not a measured
  condition of the confirmatory timings.
- G4 cannot establish whether foreign activity overlapped these 0.07 s timings (D6).

The k = 160 values are kept as recorded. P4 and P5a use them under the same standard as the other k. G4's
limitation applies to every application timing, not only at k = 160 (Section 2.4, D6).

Action accuracy against the FP64 reference on the smooth FP64 solution S, rounded to FP32 (d_S,
`out/H5_check_k*.json`; the k = 160 row is exploratory, D9):

| k | Hou | stencil, original | stencil, repaired |
|---|---|---|---|
| 80 | 6.45×10⁻⁴ | 3.88×10⁻³ | 7.57×10⁻⁶ |
| 160 (exploratory) | 1.30×10⁻³ | 1.10×10⁻² | 1.04×10⁻⁵ |
| 256 | 2.10×10⁻³ | 2.24×10⁻² | 1.53×10⁻⁵ |

### 2.2 State solves (`hou_matched.csv`, `out/H3_solve_k{k}_{path}.json`, checker `out/H5_check_k{k}.json`)

At k = 160 the last three columns are exploratory (D9). For the same reason three k = 160 rows have no
confirmatory class. Their in-process FP64 acceptance stands, but class 9 also needs the independent confirmation,
which here is exploratory. In `hou_matched.csv` their `outcome_class` is blank, and `exploratory_class` = 9.

| k | path | class | iterations | solve s (median) | setup (a) / (b) s | Krylov step ms (median) | independent ‖b−Ku‖/‖b‖ | compliance error | energy error |
|---|---|---|---|---|---|---|---|---|---|
| 80 | hou_cg32 | 8 native stop | 1591 | 12.56 | see below | 7.82 | 5.76×10⁻² | 7.6×10⁻⁵ | 2.8×10⁻³ |
| 80 | mg64_orig | 9 | 17 | 0.0872 | 0.253 / 0.108 | 4.94 | 5.01×10⁻⁶ | 9.3×10⁻¹⁰ | 7.0×10⁻⁷ |
| 80 | mg64_rep | 9 | 17 | 0.0865 | 0.250 / 0.110 | 4.92 | 5.01×10⁻⁶ | 2.4×10⁻¹⁰ ‡ | 7.0×10⁻⁷ |
| 80 | mgir_orig | 9 | 18 outer (240 inner) | 0.934 | 0.194 / 0.064 | 3.89 | 6.69×10⁻⁶ | 3.5×10⁻⁴ | 3.6×10⁻⁴ |
| 80 | mgir_rep | 9 | 4 outer (25 inner) | 0.0960 | 0.195 / 0.062 | 3.55 | 8.62×10⁻⁶ | 2.2×10⁻⁸ | 1.3×10⁻⁶ |
| 160 | hou_cg32 | 8 native stop | 2458 | 164.84 | see below | 66.9 | (0.160) | (6.8×10⁻⁴) | (8.9×10⁻³) |
| 160 | mg64_orig | – (in-process acceptance; exploratory class 9) | 19 | 0.477 (flagged) | 1.06 / 0.315 | 24.2 | (6.07×10⁻⁶) | (4.3×10⁻¹⁰) ‡ | (1.29×10⁻⁶) |
| 160 | mg64_rep | – (in-process acceptance; exploratory class 9) | 19 | 0.455 (flagged) | 0.92 / 0.309 | 22.9 | (6.07×10⁻⁶) | (5.8×10⁻¹⁰) ‡ | (1.29×10⁻⁶) |
| 160 | mgir_orig | **5 numerical breakdown** | – | – | 0.93 / 0.298 | – | – | – | – |
| 160 | mgir_rep | – (in-process acceptance; exploratory class 9) | 4 outer (22 inner) | 0.329 | 0.86 / 0.337 | 12.8 | (9.87×10⁻⁶) | (5.3×10⁻⁷) | (7.1×10⁻⁶) |
| 256 | hou_cg32 | 8 native stop | 3930 | 1088.54 (one timed solve) | see below | 276.8 | 0.387 | 2.6×10⁻³ | 1.86×10⁻² |
| 256 | mg64_orig | 9 | 21 | 1.945 | 1.46 / 0.748 | 89.3 | 5.96×10⁻⁶ | 7.1×10⁻¹¹ ‡ | 2.33×10⁻⁶ |
| 256 | mg64_rep | 9 | 21 | 1.954 | 1.55 / 0.732 | 89.7 | 5.96×10⁻⁶ | 1.3×10⁻⁹ ‡ | 2.33×10⁻⁶ |
| 256 | mgir_orig | **5 numerical breakdown** | – | – | 1.50 / 0.744 | – | – | – | – |
| 256 | mgir_rep | 9 | 5 outer (28 inner) | 1.581 | 1.35 / 0.749 | 48.7 | 2.44×10⁻⁶ | 1.1×10⁻⁷ | 4.3×10⁻⁷ |

‡ The compliance error is below the checker's resolution limit, 10 × the reference residual: 7.15×10⁻¹⁰ at
k = 80, 1.82×10⁻⁹ at k = 160 and 7.97×10⁻⁹ at k = 256 (`out/H5_check_k{k}.json` → `reference.resolution_limit`
and `paths.*.at_reference_resolution`; `hou_matched.csv` → `compliance_at_reference_resolution`). Such an error is
at the resolution of the reference. Two consequences:
- The ordering of two flagged errors is no difference in accuracy. At k = 256 the original and repaired FP64-PCG
  values, 7.09×10⁻¹¹ and 1.27×10⁻⁹, both lie below 7.97×10⁻⁹. The same holds for both exploratory FP64-PCG values
  at k = 160.
- At k = 80, `mg64_orig`'s 9.3×10⁻¹⁰ lies above the limit and `mg64_rep`'s 2.4×10⁻¹⁰ below it. The data show
  only that the repaired value is at the reference's resolution, not by how much it is smaller.

No energy error and no other compliance error is flagged.

Hou setup times (D16, D23). There is no confirmatory Hou setup time. The values recorded in the confirmatory solve
processes, 2.40/0.104, 2.65/0.083 and 3.07/0.321 s at k = 80, 160 and 256 (`out/H3_solve_k*_hou_cg32.json`), have
timer boundaries that differ from the frozen endpoint: they include the staging of the source tree in (a) and a
`gc.collect` in (b). They are not quoted as setup times and are kept in `hou_matched.csv` only as
`setup_*_recorded_offboundary_s`. The EXPLORATORY values with the plan's boundaries (`out/X_SETUP_k{80,160,256}.json`)
are below. They fill the setup columns of the `hou_cg32` rows of `hou_matched.csv`, labelled exploratory in
`setup_status`, and every setup comparison with Hou uses them. Setup (a) is timed from after the
staging and after the FP32 density grid has been allocated and filled. It covers exactly autowrite, import, killer
and survivor.

| k | setup (a): autowrite + import + killer + survivor | of which autowrite + import | setup (b): killer + survivor |
|---|---|---|---|
| 80 | 2.313 s | 2.131 s | 0.137 s |
| 160 | 2.538 s | 2.125 s | 0.0766 s |
| 256 | 2.974 s | 2.131 s | 0.315 s |

- G4 activity during these setup intervals is unknown. Each process received one activity sample and has no timed
  window, so only a process-wide mean exists: 3.1 %, 1.6 % and 2.5 %, which places each process in the 1–5 %
  flag band. None spilled.
- The first exploratory version (`out/X_SETUP_k*__v1_density_in_a.json`) timed the density grid inside (a). It
  gave 2.438, 2.580 and 2.985 s for (a), and 0.0958, 0.0770 and 0.314 s for (b). Its timing boundary was not the
  one stated, so it is superseded.
- The two versions differ beyond the boundary change. At k = 256 the killer + survivor part took 0.786 s before
  and 0.844 s now. Setup (b) at k = 80 is 0.137 s now, against 0.096 s before. The cause of these differences is
  not established; with the activity during setup unknown, they are reported as measured.
- Their autowrite contains a fixed `time.sleep(2)` as released (D5).

Notes on the solves:
- `mgir_orig` failed at k = 160 and 256 with "ir_lean: correction rejected with inner tolerance 1e-07". At k = 80
  it needed 18 outer steps instead of 4 (`residual_histories/80_mgir_orig.csv`).
- The failing confirmatory processes saved no trajectory (D18). An EXPLORATORY history solve reproduced the same
  exception at both sizes (`out/X_IRHIST_k{160,256}_mgir_orig.json`, `residual_histories/X_{160,256}_mgir_orig.csv`):
  - two corrections are accepted (FP64 true residual 1 → 0.927 → 0.781 at k = 160; 1 → 0.838 → 0.676 at
    k = 256);
  - every later correction raises the residual (to about 1.226 at k = 160 and 1.395 at k = 256) and is undone;
  - after each rejection the inner tolerance is cut tenfold. After six rejected corrections, computed at inner
    tolerances 10⁻¹ to 10⁻⁶, it reaches 10⁻⁷, below the floor, and the solver stops;
  - every inner FP32 solve used two operator applications, whatever its tolerance. Its exit reason was not
    recorded.
- The outer FP64 residual evaluation of `mgir_rep` costs 0.99, 7.7 and 31.1 ms per outer step
  (`outer_residual_ms_mean_per_outer`).
- Hou's solve-start overhead was 8.2, 65.8 and 287.5 ms in the median timed solve (`start_overhead_ms`,
  `out/H3_solve_k*_hou_cg32.json`). It is the time from the solve call to the start of the first CG iteration in
  their released `FE.FE`/`CG.CG`. That covers load and support construction, survivor indexing, residual formation
  (one operator application) and a `gc.collect`, not residual formation alone.
- Hou's achieved recursive residual ‖r_m‖/‖r_0‖, the FP32 quantity of their stopping test, comes from the H4
  continuation (`out/H4_cont_k*.json`; `recursive_rel_residual_*` in `hou_matched.csv`). At the native stop it is
  9.95×10⁻⁴, 9.89×10⁻⁴ and 9.95×10⁻⁴ (iterations 1591, 2458, 3930). At iteration 10,000 it is 1.97×10⁻¹⁸,
  9.52×10⁻¹³ and 1.28×10⁻⁷. Over the same runs the FP64 true residual stays at or above 3.97×10⁻², 2.53×10⁻² and
  2.07×10⁻² at every checkpoint (below). The recursive residual therefore does not measure the attained
  equilibrium accuracy of their FP32 iterate.

Hou's continuation to 10,000 iterations (`out/H4_cont_k*.json`; FP64 checkpoints in-process at k = 80 and 160;
snapshots checked by `out/H5_check_k256.json`; histories in `residual_histories/{k}_hou_cg32.csv`):
- Their native test first holds at iterations 1591, 2458 and 3930.
- The true residual was evaluated at 201, 201 and 41 checkpoints: every 50 iterations (k = 80, 160) or every 250
  (k = 256), plus the native-stop iterate. It was at or below 10⁻⁵ at none of them. The smallest checkpoint values
  are 3.97×10⁻² (iteration 1100), 2.53×10⁻² (iteration 100) and 2.07×10⁻² (iteration 250). Iterates between
  checkpoints were not tested (D18).
- At iteration 10,000 it is 5.95×10⁻² at k = 80 and 0.206 at k = 160.
- The in-process value at k = 160 at the native-stop iterate (0.1597, `out/H4_cont_k160.json`) is a separate
  measurement from the exploratory checker's 0.160.

So there is no common-accuracy time for Hou.

### 2.3 Memory (three separately defined peaks)

**Confirmatory H3 records: not single-solve peaks (D14).** The H3 values in `hou_matched.csv` are process-life
peaks as defined, but each covers a second build.
- In our processes the timing wrapper kept the first preconditioner and multigrid hierarchy alive while the history
  pass built a second one, and the history buffer (8 B/DOF) was added.
- In Hou's process the driver held a survivor index while their CG built its own.

Subtracting the history buffer does not recover a single-solve value. These peaks are therefore not used for any
comparison, and P6 is inconclusive. The confirmatory values at k = 256 are pool used 4.88 GB (Hou), 8.86 GB
(`mg64_rep`) and 6.83 GB (`mgir_rep`); process-dedicated peaks are 6.26, 10.22 and 8.18 GB. The single-build
re-measurement quantifies the excess:
- Hou's pool used peak falls by 134,218,240 B, from 4,875,235,840 B (`out/H3_solve_k256_hou_cg32.json`) to
  4,741,017,600 B (`out/X_MEM_k256_hou_cg32.json`). One int32 survivor index of 33.55 M elements is
  134,217,728 B, so the fall is one index plus 512 B. The 512 B were not attributed.
- `mg64_rep`'s pool used peak falls by 2,396,397,568 B (2.40 GB), from 8,858,811,904 B
  (`out/H3_solve_k256_mg64_rep.json`) to 6,462,414,336 B (`out/X_MEM_k256_mg64_rep.json`).

**EXPLORATORY single-build, single-solve peaks** (`out/X_MEM_k{k}_{path}.json`, `hou_exploratory.csv`; D17). Each
row is one fresh process: one build, one solve from zero, the hook on throughout and no history buffer. Hou runs
their released `FE.FE` unmodified, with the caller holding what their `main.py` holds. No run spilled (shared
growth ≤ 80 MB). The first twelve runs used the same protective pool cap, E_free − 1.5 GiB = 16.80 GB, with other
processes holding 6.99–7.00 GB.

The `mgir_orig` row at k = 80 was added after the third check (D20). It comes from one short guarded process under
the authors' GPU-memory rule:
- admission: predicted peak 0.577 GB plus 1.5 GiB, against 24.15 GB cudaMemGetInfo free; `guard.require_budget`
  also admitted it;
- pool cap: driver free − 1.5 GiB = 22.54 GB;
- other processes held 6.30 GB (6.28 GB in the D21 run);
- a live stop-on-spill watcher was active on complete samples only (D21). It took its baseline from its own
  measured sample and allowed at most 3 s between checked samples (D22). It checked 14 samples after the baseline,
  the last one taken after the job ended, with a largest gap of 1.069 s. Shared growth was 12.6 MB. Coverage held
  from the watcher's first sampler baseline onward, not over the whole process: that baseline already held
  77,594,624 B shared (D23).
- Two earlier runs of this row had watcher faults (Sections 0.00 and 0.000) and were repeated. The three runs agree
  in pool used, pool reserved and process-dedicated peaks, to the byte. Their device-wide peaks above baseline, as
  measured, are 622,854,144 B in the first run and 576,716,800 B in the later two (D23).

The cap did not bind at this size. At k = 160 and 256 `mgir_orig` has no single-build peak, because the path
breaks down there (class 5); it is marked missing. Units are GB.

| k | path | pool used peak | pool reserved peak | process-dedicated peak | device-wide peak − baseline |
|---|---|---|---|---|---|
| 80 | hou_cg32 | 0.148 | 0.448 | 0.850 | 0.849 |
| 80 | mg64_orig | 0.218 | 0.230 | 0.642 | 0.642 |
| 80 | mg64_rep | 0.218 | 0.230 | 0.642 | 0.654 |
| 80 | mgir_orig (added, D20; repeated, D21, D22) | 0.164 | 0.179 | 0.577 | 0.577 |
| 80 | mgir_rep | 0.164 | 0.179 | 0.577 | 0.575 |
| 160 | hou_cg32 | 1.164 | 3.977 | 4.379 | 4.386 |
| 160 | mg64_orig | 1.632 | 1.665 | 2.089 | 2.089 |
| 160 | mg64_rep | 1.632 | 1.665 | 2.089 | 2.088 |
| 160 | mgir_orig | missing (class 5 breakdown) | – | – | – |
| 160 | mgir_rep | 1.132 | 1.166 | 1.584 | 1.576 |
| 256 | hou_cg32 | 4.741 | 16.256 | 16.660 | 16.667 |
| 256 | mg64_orig | 6.462 | 6.627 | 7.049 | 7.056 |
| 256 | mg64_rep | 6.462 | 6.627 | 7.049 | 7.045 |
| 256 | mgir_orig | missing (class 5 breakdown) | – | – | – |
| 256 | mgir_rep | 4.429 | 4.594 | 5.015 | 5.014 |

What the exploratory comparison shows:
- **Repair and memory at k = 80.** The original-stencil IR (18 outer steps, 240 inner) and the repaired IR (4 outer,
  25 inner) have identical pool used, pool reserved and process-dedicated peaks, to the byte (163,632,640,
  178,890,752 and 576,897,024 B). The device-wide readings are 0.577 and 0.575 GB above baseline. For the
  original-stencil IR that is 576,716,800 B, as in the second run; the first run read 622,854,144 B. This quantity
  includes other processes' activity.
- **Process-resident memory.** By the plan's P6 measure (process-dedicated peak), and by device-wide use, both of
  our solvers stay below Hou's process at every k. At k = 256 the values are 7.05 GB (`mg64_rep`) and 5.02 GB
  (`mgir_rep`), against 16.66 GB.
- **Live allocation.** By pool *used* peak, the ranking differs. `mg64_rep` holds more live memory than Hou at every
  k: 0.218/0.148, 1.632/1.164 and 6.462/4.741 GB. `mgir_rep` holds less at k = 160 and 256 (1.132/1.164 and
  4.429/4.741 GB) but more at k = 80 (0.164/0.148 GB).
- **Why Hou's resident memory is high.** Hou's process peak comes from the pool's *reserved* memory, not its live
  data. At k = 80 and 160 the setup-only processes (`out/X_SETUP_k{80,160}.json`: their index construction, killer
  + survivor, no solve) reach the same process-dedicated peaks as the full solve processes (0.850 and 4.379 GB).
  At k = 256 the setup-only process reaches 16.66 GB (the rerun setup processes, with a slightly lower cap of
  16.48–16.54 GB, gave the same three values to the byte), and so does the application process
  (`out/X_APPLY_k256_hou_cg32.json`, pool used 2.71 GB, reserved 16.26 GB).
  - The reserved pool of their index construction grew to within 0.55 GB of the 16.80 GB cap. Its size at
    k = 256 therefore depends on the cap and on CuPy's block caching. It is not a fixed requirement of their
    solve.
  - The confirmatory processes ran with a 16.16 GB cap. Their process-dedicated readings at k = 256 were 6.26 GB
    (solve) and 11.06 GB (application). The device-wide readings were 11.07 and 12.18 GB above baseline. These
    cannot be compared across caps.
- **Wording consequence.** "Uses less memory than Hou's code" holds for process-resident and device memory in
  these exploratory runs, at every k. It does not hold for live allocated bytes with `mg64`. Any statement should
  name the measure.

Hou application process at k = 256 with in-protocol transfers (D15; `out/X_APPLY_k256_hou_cg32.json`,
`out/X_G2_k256.json`, EXPLORATORY):
- System identity holds in-process: fixed sets identical, loads identical, zero initial iterate.
- d_R = 7.56×10⁻⁸, evaluated immediately after the application, the same as the confirmatory value.
- Application median 267.5 ms, against 264.16 ms in the confirmatory process.
- Peaks: pool used 2.71 GB, process-dedicated 16.66 GB. The confirmatory application-process peak of 11.06 GB
  (`out/H2_apply_k256_hou_cg32.json`) included the out-of-protocol staging and ran under a different cap. Neither
  is an application-alone figure. The historical E10 note of 15.5 GiB for Hou's application at k = 256 was a
  shared-process value, and it is not reproduced or replaced here.

### 2.4 Predictions P1–P8 (`predictions.json`)

| id | outcome | values |
|---|---|---|
| P1 Hou native-stop residual > 10⁻⁵ | **inconclusive (unresolved)** | Confirmatory: 5.76×10⁻² (k = 80), 0.387 (k = 256). The plan's denominator is every k with a completed Hou solve, and k = 160 has one (2458 iterations, class 8), but no confirmatory independent residual. Beside it, exploratory: 0.160 from the replacement checker (D9), and 0.1597 from the in-process continuation at the native-stop iterate. Both agree with the prediction. |
| P2 Hou does not attain 10⁻⁵ in 10,000 iterations | **support** | smallest checkpoint values 3.97×10⁻², 2.53×10⁻², 2.07×10⁻² over 201, 201 and 41 checkpoints; iterates between checkpoints not tested |
| P3a Hou native solve / `mg64_rep` (setup b + solve) > 1 | **support** (k = 80, 256) | 63.8, 405.3. This is elapsed time at unequal accuracy (Hou 5.8×10⁻² and 0.39; ours 5.0×10⁻⁶ and 6.0×10⁻⁶), not a speed-up at equal accuracy. At k = 160: 215.9, exploratory (D9). |
| P3b time to common accuracy | **inconclusive**: Hou reaches 10⁻⁵ at no checkpoint | – |
| P4 Hou application / repaired stencil ≥ 100 | **inconclusive (unresolved)** | Confirmatory: 157.9 (k = 80), 202.5 (k = 256). The k = 160 ratio is 15.2, exploratory, because its G2 action gate rests on the exploratory replacement checker (D9). It would also lie between the support and contradiction thresholds (D12). The cause of the slow k = 160 stencil timings is not established (D11). Same timing standard and gate as P5a. |
| P5a repaired / original application ≤ 1.15 | **inconclusive (unresolved)** | Confirmatory: 1.062 (k = 80; IQR bounds 1.060–1.079), 1.069 (k = 256; 1.040–1.091). The system-identity gate is applied as in P3a, and at k = 160 the G2 action gate is exploratory (the first checker run spilled; D9). The k = 160 ratio, 1.042 (0.943–1.080), is therefore exploratory, and the criterion requires every k. The G4 caveat applies at every k (D6). |
| P5b repaired / original solve time in [0.85, 1.15] | **contradiction** | Ratios of median solve times, repaired / original, against the ±15 % band [0.85, 1.15]. Decided by mgir at k = 80: 0.103, outside the band with disjoint IQRs; the original-stencil IR needed 18 outer steps against 4. The contradiction is in the direction of a faster repaired solve. Confirmatory mg64: 0.991 (k = 80) and 1.005 (k = 256), inside the band. The k = 160 mg64 ratio, 0.953, is exploratory: its action check comes from the exploratory replacement checker (D9), outside the system-identity gate, which is applied as in P3a and P5a (D23). No mgir ratio exists at k = 160 and 256, where the original IR breaks down; that bears on P8. |
| P6 our process-dedicated peak lower than Hou's | **inconclusive** | The recorded process peaks retain workspaces of two builds (D14). The single-build comparison is exploratory (Section 2.3). |
| P7 d_S(repaired) < d_S(original) | **inconclusive (unresolved)** | Holds at k = 80 and 256 (ratios d_S(orig)/d_S(rep) 512 and 1459). There is no confirmatory value at k = 160, and the criterion requires every k. The exploratory k = 160 value agrees (1062, D9). |
| P8 our four paths reach class 9 | **contradiction** | `mgir_orig` class 5 at k = 160 and 256, from the solve processes; these decide it. The other three paths are class 9 at k = 80 and 256. At k = 160 they have no confirmatory class: in-process acceptance, with exploratory independent confirmation only (exploratory class 9). |

Flags for the authors' wording:
- P8/P5b: the original-stencil IR path is not a working solver on Hou's system at k ≥ 160. Two corrections are
  accepted, then every correction is rejected until the inner-tolerance floor.
- The memory comparison with Hou at k = 256 cannot be worded from the confirmatory record (P6 inconclusive). The
  exploratory single-build values in Section 2.3 are the available evidence.

## 3. Capacity (Q3): authors' cantilever, repaired FP32 operator (`capacity.json`)

### 3.1 Confirmatory outcomes

E_free (`guard.effective_free_bytes()`) was 16.55–17.20 GiB in every evaluation. Other processes held about 7 GiB
of WDDM dedicated memory (desktop compositor about 4.3 GB). Records are in `logs/admission_evals.json` and
`out/C*.json`.

| entry | size | class | detail |
|---|---|---|---|
| C1 `mg_ir` k = 384 | 113,246,208 | **2 guard prediction** | W = 18,448,734,655 B (17.18 GiB; β 146.1 B/element prior, τ = 4 N_d, ω 0.5 GiB). Needs 18.68 GiB with margin. Refused in session 2 (E_free 16.61 GiB) and session 3 (16.61 GiB); class 2 rests on these two. The session-1 evaluation (logged as 16.55 GiB) ran while the k = 256 Hou application process was still running. It is not an isolated reading and counts as no evidence (D10, D19). |
| C2 `mg32_rec` k = 384 | 113,246,208 | **2 guard prediction** | the same W; E_free 16.61, 16.61, 17.20 GiB (sessions 2–4) |
| C3 `mg64` k = 320 | 65,536,000 | **3 allocation failure** | Admitted: W 13.85 GiB, E_free 16.61 GiB, pool cap 16,221,745,152 B. Out of memory in design iteration 3 when allocating 1,585,183,232 B (one FP64 nodal vector, a temporary of `cupy.dot` in `pcg64`) with 14,716,451,840 B allocated. Not repeated: class 3 is a result. |
| C4 / C4b `mg64` k = 352 / 384 | – | 1 not run | mg64 ladder stopped at k = 320 (plan 7) |
| C5 / C5b `mg_ir` k = 416 / 448 | – | 1 not run | mg_ir ladder stopped at k = 384 |
| C6a `mg32_rec` original stencil k = 384 | 113,246,208 | **2 guard prediction** | the same W; three evaluations |
| C6b | – | 1 not run | requires C5 verified |

Per configuration (`capacity.json` → `configurations`), no T27 lower bound was demonstrated. The next tested
outcomes are:
- `mg_ir`: k = 384, class 2;
- `mg64`: k = 320, class 3;
- `mg32_rec` (repaired): k = 384, class 2;
- `mg32_rec` (original): k = 384, class 2.

There is no fit interval. These confirmatory bounds stay as the frozen rule left them: C1's class 2 rests on its
two isolated refusals. Its first evaluation overlapped another GPU job and carries no weight either way (D10, D19).

The historical development records are quoted unchanged under `historical`. Each has a T27 class only if it meets
T27's class rule (plan 4.8); `historical[*].T27_class_rule` lists the conditions:
- **Historical completions, with no T27 class:**
  - E32 and E7: `mg_ir` at k = 384;
  - E32: `mg64` at k = 320;
  - E14 and E12: `mg32_rec` at k = 320.

  Every state solve of the `mg_ir` and `mg64` records was accepted in-process at ≤ 10⁻⁵, and they terminated with
  `max_change` or `bounded_oscillation`. They still miss two conditions of class 9 (class 8 for the recursive
  control): an independent check of the final state, and continuous spill sampling. Their SpillWatch sampled at
  the start, every 10 design iterations and at the end. E32 `mg64` k = 320 also saved no final design.
- E12/E23: `mg64` at k = 384 spilled (class 4; the classification is kept, but none of their measurements are
  exported). E12b: out of memory (class 3).

Their pool peaks were sampled at iteration ends, so they are not isolated full-run peaks in the T27 sense.

**Paper-wide maximum.** It stays at 113,246,208 elements (not updated; `capacity.json` → `paper_wide_maximum`). It
is carried by the historical completions at k = 384 (`results/E32/simp_cantilever_k384_mg_ir_stencil_diff.json`,
`results/E7/simp_cantilever_k384_mg_ir_stencil.json`), which are historical completions, not T27 class 9. No T27
confirmatory entry is larger. The exploratory k = 384 completions (Section 3.2) are the same size, and they are
exploratory.

Predictions:
- C-A (`mg32_rec`, k = 384): **contradiction** under the plan's table (class 2).
- C-B (`mg64`, k = 352): **inconclusive** (class 1, not run because the ladder stopped at k = 320).
- C-C (`mg_ir`, k = 416): **inconclusive** (class 1, not run).

### 3.2 EXPLORATORY capacity runs (D8; never confirmatory)

These runs bypassed the plan's admission rule. Their pool cap was raised to cudaMemGetInfo free − 1.5 GiB
(about 21 GiB), above the plan's cap of E_free − 1.5 GiB. For `mg64` at k = 320 this came after its confirmatory
allocation failure under the plan's cap. Records are `out/X_*.json` and `capacity.json` → `exploratory`. Their
four saved designs are exploratory designs: three at k = 384 (`designs/X_C1_mg_ir_k384.npz`,
`designs/X_C2_mg32_rec_k384.npz`, `designs/X_C6a_mg32_rec_orig_k384.npz`) and one at k = 320
(`designs/X_C3_mg64_k320.npz`). They are no capacity entry, lower bound or
paper-wide maximum.

Admission and cap of each exploratory run, read in its own process (`capacity.json` → `exploratory.entries`):

| run | W (plan 4.6) | E_free | plan's admission (recorded, not applied) | cudaMemGetInfo free | W + 1.5 GiB ≤ cudaMemGetInfo free | pool cap | others' dedicated at start |
|---|---|---|---|---|---|---|---|
| X `mg_ir` k = 384 | 17.18 GiB | 16.61 GiB | refuse | 22.49 GiB | yes | 20.99 GiB | 7.58 GB |
| X `mg32_rec` k = 384 | 17.18 GiB | 17.40 GiB | refuse | 22.49 GiB | yes | 20.99 GiB | 6.72 GB |
| X `mg64` k = 320 | 13.85 GiB | 17.20 GiB | admit | 22.49 GiB | yes | 20.99 GiB | 6.94 GB |
| X `mg32_rec` original stencil k = 384 | 17.18 GiB | 17.20 GiB | refuse | 22.49 GiB | yes | 20.99 GiB | 6.94 GB |

The column "W + 1.5 GiB ≤ cudaMemGetInfo free" is given for information. It is the admission test of the authors'
GPU-memory rule of 2026-11-23, which was written after these runs and cites them. It changes no class.

| run | exploratory class | design iterations / termination | final compliance (native final state) | independent final residual | pool used / reserved peak | process-dedicated | device-wide (baseline) | compute s |
|---|---|---|---|---|---|---|---|---|
| X `mg_ir` k = 384 | 9 | 76 / bounded_oscillation | 0.1236620430 (4.1×10⁻⁸ from E32) | 4.61×10⁻⁷ | 17.67 / 19.97 GiB | 20.38 GiB | 23.05 GiB (3.38) | 192.4 |
| X `mg32_rec` k = 384 | 8 | 76 / bounded_oscillation | 0.1236620369 | 1.40×10⁻⁸, of the post-certification state | 17.67 / 19.97 GiB | 20.38 GiB | 23.01 GiB | 156.0 |
| X `mg64` k = 320 | 9 | 76 / bounded_oscillation | 0.1480662466 (1.5×10⁻¹³ from E32 r1–r3) | 5.12×10⁻⁶ | 13.29 / 15.18 GiB | 15.57 GiB | 18.41 GiB | 138.9 |
| X `mg32_rec` original stencil k = 384 | 8 | 76 / bounded_oscillation | 0.1236172336 | 1.89×10⁻⁸, of the post-certification state | 17.67 / 19.97 GiB | 20.38 GiB | 23.00 GiB | 156.1 |

Recursive FP32-Krylov / FP64-iterate control at k = 384:
- The two counts below cover the 76 design-loop solves (`n_states_above_1e-5`, `max_state_rel_true`). The separate
  native final solve has its own residual, `final_solve.rel_true`.
- **Repaired stencil** (`out/X_C2_mg32_rec_k384.json`):
  - 0 of the 76 design-loop states lie above 10⁻⁵ (max 9.86×10⁻⁶);
  - the native final state is at 3.04×10⁻⁶;
  - so 0 of 77 recorded states lie above 10⁻⁵.
- **Original stencil** (`out/X_C6a_mg32_rec_orig_k384.json`):
  - 23 of the 76 design-loop states lie above 10⁻⁵ (max 3.69×10⁻³);
  - the native final state is at 4.89×10⁻⁶;
  - so 23 of 77 lie above 10⁻⁵.
  - Its final compliance differs by 3.6×10⁻⁴ from the repaired runs.
- **Checker.** For both controls the independent checker (`out/X_C2_..._check.json`, `out/X_C6a_..._check.json`)
  reads the displacement after the control's certification solve (mg_ir to 10⁻⁷), not the native recursive-stop
  state. Its 1.40×10⁻⁸ and 1.89×10⁻⁸ therefore certify the retained designs, not the recursive solves. The
  native final states are described by the in-process `final_solve` values above.

Memory:
- The isolated continuous pool peaks of these runs exceed the accounted breakdown, which is the basis of the
  paper's "≈146 B/element":
  - `mg_ir` at k = 384: pool used 167.5 and pool reserved 189.3 B/element, against 145.8 accounted;
  - `mg64` at k = 320: 217.7 and 248.7, against 194.5 accounted.
- The historical iteration-end samples (E32: 16.39 GB pool used at k = 384) did not capture these within-iteration
  maxima.
- These are two allocator quantities, each measured on one grid. They describe those runs only. They do not
  establish what 10⁹ elements would need, and they do not replace the historical 146 GB extrapolation of the
  historical single-load configuration. They do show that the accounted 146 B/element understates this run's
  own pool high-water mark by 15 % (used) to 30 % (reserved).

Next sizes (prediction only; plan 4.6 formula with these exploratory anchors; `capacity.json` →
`exploratory_next_size_predictions`):
- `mg_ir` at k = 416: W = 24.58 GiB (26.08 GiB with margin). This exceeds both the observed E_free (16.55–17.20
  GiB) and the card's 23.99 GiB.
- `mg64` at k = 352: W = 20.15 GiB (21.65 GiB with margin). This exceeds the observed E_free, so it would not be
  admitted on this desktop. It is below the card's 23.99 GiB total, so the prediction does not exclude it on a card
  with less memory held by other processes.
- For information only: the authors' GPU-memory rule of 2026-11-23 admits against cudaMemGetInfo free, which read
  22.49 GiB in these processes. Under that test `mg64` at k = 352 (21.65 GiB with margin) would fit and `mg_ir` at
  k = 416 (26.08 GiB) would not. Neither was run. The plan's ladder had stopped both configurations, and the
  operator note of 2026-11-23 allowed no new capacity measurement.

Shared-usage growth: the k = 384 runs ended with 220–230 MB of shared-usage growth, under the 256 MiB spill limit.
All but about 74 MB of it arose after the optimization's last spill check, while the final state was being saved.

## 4. Acceptance against the task statement

- "Each configuration has a demonstrated lower bound for its named workload and the next tested outcome where
  available": **met for the Hou-system state-solve workloads, not met confirmatorily for the optimization
  capacity.**
  - Hou-system lower bounds (largest class 8 or 9, confirmatory at k = 256):
    - `hou_cg32` k = 256 (native stop only; nothing larger tried, per the plan);
    - `mg64_orig` and `mg64_rep` k = 256;
    - `mgir_rep` k = 256;
    - `mgir_orig` k = 80, with next tested k = 160 class 5.
  - Optimization capacity: every configuration's next tested outcome is class 2 or 3, with no T27 lower bound.
    The exploratory runs at k = 320/384 complete, but outside the plan's admission rule, and they are reported as
    exploratory with their admission and cap. The historical completions (E32, E7, E14, E12) have no T27 class.
- Classification into guard prediction, allocation failure, spill, numerical breakdown, native stop and verified
  acceptance: done for every entry (`hou_matched.csv`, `capacity.json`). The exception is three k = 160 state
  solves (`mg64_orig`, `mg64_rep`, `mgir_rep`). Their independent confirmation is exploratory (D9), so they have no
  confirmatory class; the exploratory class is 9. No lower bound rests on them.
- No shared-process historical peak or short probe is used as an isolated full-run peak. Historical entries are
  labelled. The confirmatory H3 process peaks are marked as not single-solve (D14), and the single-solve peaks come
  from separate exploratory processes.
- No spilled measurement is reported. The two historical spill records keep their class 4 in `capacity.json`, with
  no measurements exported. The paper-wide maximum is not updated: no confirmatory optimization larger than
  113,246,208 elements was run. The maximum stays carried by the historical k = 384 `mg_ir` completions.
- Prediction outcomes after the third check (`predictions.json`):
  - support: P2 and P3a;
  - contradiction: P5b, P8 and C-A;
  - inconclusive: P1, P4, P5a and P7 (unresolved at k = 160), P3b, P6, C-B and C-C.
