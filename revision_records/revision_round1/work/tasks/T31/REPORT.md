# T31: four-load bracket optimization with the repaired mixed-precision path (R1.4)

The frozen plan is `tasks/T31/ANALYSIS_PLAN.md` (sha256 0a154a83…c5a697, unchanged). Departures are in
`DEVIATIONS.md` (D1–D6); none touches a rule of the plan. Section 8 records the first fix round. Every number below comes from the file named beside it.
`summary.json` is `out/summary.json`, written by `t31_analyse.py` from the job outputs alone.

## 1. Outcome against the plan

| item | result | source |
|---|---|---|
| H1 (n = 192, primary) | **inconclusive**: R_n192 reached the 300-iteration guard | summary.json `hypotheses.H1` |
| H2 (n = 384, extension) | **inconclusive**: R_n384 also reached the 300-iteration guard | summary.json `hypotheses.H2` |
| Application status for R1.4 | **inconclusive** (no R design passes E1; no correctness check failed) | summary.json `application_status_R1_4` |
| C1, original stencil O_n192 | **not-converged** (300-iteration guard, every production solve accepted) | summary.json `C1_O_n192_category` |

All three optimizations (R and O at n = 192, R at n = 384) did everything except stop.
- **Volume.** Each returned a design at the prescribed volume (|V − 0.5| ≤ 3.1e-10).
- **Production solves.** All 1,204 production solves of each run met the FP64 true residual ≤ 1e-5.
- **Tight checks.** All four tight FP64 equilibrium checks of each retained design passed at ≤ 1e-8.
- **Stopping.** None of the three runs met the authors' stopping rule within 300 design iterations. E1 (a) therefore
  fails, and by the frozen rule no complete four-load design exists at either size.
- **Memory coverage.** No job spilled and none met an allocation failure over its monitored interval. That interval
  starts at the launcher's third sample, not its first, so E1 (e) as worded is not established (section 2). This adds
  a second unmet item to (a); it changes no verdict.

The reason the runs did not stop is the same in every run. In the final continuation phase, J settles (10-iteration
spread 1.1e-5 at n = 192, 1.2e-6 at n = 384), but thousands of elements keep changing at every iteration. At
n = 192, J alternates up and down from one iteration to the next, and about 10,100 elements move by more than 0.01 at
each iteration. At n = 384, about 80,000 elements still move. Sections 4.2 and 5 give the details.

## 2. Setup actually run

- **Problem.** T30's bracket counterpart: four load cases about C = (6.0, 2.25, 2.1) in, J = Σ ¼ c_k / c0_k, a
  designable volume of 0.5, and the authors' E32 configuration and continuation. The physical filter radius falls from
  0.1125 in to 0.09 in (`rmin_scale = n/96`). Details are in plan section 3; the driver configuration is recorded in
  `out/runs/R_n192/gpu_meta.json` `driver.config`.
- **Code.** T30's code and the voxfem copy were reused byte for byte (`code_hashes.json`,
  `all_copies_identical: true`).
- **Checks before the first GPU job.**
  - The launcher self-test passed (`out/launch_selftest.json`, 11 of 11 cases).
  - The host checks passed at n = 96, 192 and 384 (`out/host_checks_{n}.json`).
- **Element counts.** From `out/host_checks_{n}.json`, `counts`; the OPT jobs recomputed them in
  `gpu_meta.json` `driver.counts`.

| n | allocated (box) | active | designable | protected | free DOFs |
|---|---|---|---|---|---|
| 192 | 1,966,080 | 903,548 | 827,324 | 76,224 | 2,839,977 |
| 384 | 15,728,640 | 7,232,600 | 6,629,528 | 603,072 | 22,214,871 |

**Jobs.** All ran under the guarded launcher, one at a time, admitted by the plan's prediction. Every job record has
`status: ok` and a checked final sample (`out/runs/<job>/monitor.json`).

**Coverage start** (summary.json `runs.<job>.monitor.coverage_start`, `c0.<n>.monitor.coverage_start`).
- In all eight jobs, the launcher's first sample does not yet hold the job's process. The second holds it, but its
  dedicated-memory counter is missing.
- Coverage is complete from the third sample, the one at which the launcher confirms coverage ("go"), 12.6 to 13.6 s
  after launch. At that sample the process already held 354,570,240 B dedicated and 77,594,624 B shared memory.
- Before that sample the job had created its CUDA context and made a one-element probe allocation (`t31_job.py`
  lines 52–56). The job did no other GPU work before the "go" signal.
- From the third sample to the final checked sample, no monitored interval exceeded the 256 MiB spill threshold
  (growth table below).
- The plan's E1 (e) asks for coverage complete from the launcher's first sample. That is not established for any
  job, so (e) is recorded as not met (summary.json `E1.*.e_coverage_from_launcher_first_sample: false`).

| job | shared growth (MiB, limit 256) | job wall (s) |
|---|---|---|
| c0_n192 | 18 | 42 |
| R_n192 | 16 | 583 |
| A_R_n192 | 18 | 37 |
| O_n192 | 18 | 578 |
| A_O_n192 | 18 | 37 |
| c0_n384 | 98 | 35 |
| R_n384 | 98 | 4154 |
| A_R_n384 | 98 | 76 |

## 3. Normalising references (phase C0)

`out/c0_n192.json`, `out/c0_n384.json` and `out/runs/c0_n{n}/gpu_meta.json`. Fully solid bracket, mg64 from zero.

| n | c0 (LC1, LC2, LC3, LC4; code units) | node_hoist relative residual | PCG iterations | four solves + setup (s) | pool peak (B) |
|---|---|---|---|---|---|
| 192 | 5.80014e6, 3.85930e6, 1.89567e6, 4.71440e5 | 7.59e-9, 6.79e-9, 8.87e-9, 9.01e-9 | 76, 75, 71, 71 | 7.28 | 734,402,560 |
| 384 | 2.94205e6, 1.93904e6, 9.59490e5, 2.37416e5 | 6.55e-9, 9.42e-9, 9.80e-9, 9.65e-9 | 108, 107, 98, 104 | 17.58 | 5,143,906,304 |

- **Time column.** It is the sum of the four recorded solve times and the multigrid setup (summed in summary.json
  `c0.<n>.audit_time_four_solves_plus_setup_s`). The job's wider timed interval also holds the equilibrium checks,
  the reaction sums and the host transfers: 7.49 s at n = 192 and 18.23 s at n = 384 (`broader_interval_s`).
- Each check is ≤ 1e-8, and the device's fixed set equals supports ∪ exterior-only nodes at both sizes.
- At n = 192 the residuals recomputed in the CPU-assembled FP64 matrix agree to three digits
  (`gpu_meta.json` `cpu_check`).
- Informational: applied load plus support reactions balance to ≤ 2.2e-9 (force) and ≤ 1.2e-8 (moment) relative
  (summary.json `c0.*.reactions_informational`).

## 4. The primary run R_n192 and the original-stencil run O_n192

### 4.1 E1, item by item (summary.json `E1.R_n192`, `O_n192_E1_items`)

| item | R_n192 | O_n192 |
|---|---|---|
| (a) stopped by `max_change` or `bounded_oscillation` | **no**, `guard` after 300 iterations | **no**, `guard` after 300 |
| (b) \|V − 0.5\| ≤ 1e-4 | yes, 1.4e-12 | yes, 3.0e-12 |
| (c) every production solve ≤ 1e-5 | yes, 1,204 solves, max 9.997e-6, no solve failure | yes, max 9.93e-6 |
| (d) audit valid, four checks ≤ 1e-8 | yes | yes |
| (e) no spill, no allocation failure, coverage complete from the launcher's first sample | **not established**: no spill or allocation failure, but coverage only from the third sample (section 2) | same |
| E1 | **fails on (a)**; (e) not established | **fails on (a)**; (e) not established |

### 4.2 Why the stopping rule did not fire (descriptive; summary.json `runs.R_n192.end_state_descriptive`)

- **The J-spread test alone holds from iteration 78.** Over the last 10 iterations the relative spread of J is
  1.11e-5, against a limit of 1e-4.
- **The other two tests never hold after iteration 75.**
  - Max-change test: max |Δρ_phys| never falls below 0.351 (limit 0.01).
  - Bounded-oscillation test: at least 9,731 elements move by more than 0.01 (limit max(1, 1 ppm of 903,548) = 1).
- **J alternates at the end.** Over iterations 289–300, J goes up and down from one iteration to the next, between
  about 1.203752 and 1.203739 (summary.json `runs.R_n192.end_state_descriptive.J_last12`). In each of these
  iterations, 10,098 to 10,105 elements move by more than 0.01 (`out/runs/R_n192/history.json`).
- **What the record does not show.** The history holds only scalars per iteration, and only the final density field
  was saved. It cannot show which elements moved, or whether the density field returns to the same state after two
  iterations. A period-2 cycle of the design is consistent with the record but not established by it.
- **O_n192 behaves the same way** (first spread-only iteration 78; J also alternates over its last 12 iterations;
  summary.json `runs.O_n192.end_state_descriptive`).

The retained design is the final iterate after the final production re-solve, as the plan defines it. J of
consecutive end iterations differs by about 1.1e-5, so the retained J depends on the iteration at which the guard
stopped.

### 4.3 Retained designs and the tight audits (S1, S4)

`out/runs/A_R_n192/gpu_meta.json`, `out/runs/A_O_n192/gpu_meta.json` (`endpoints`, `tight`).

| | R_n192 | O_n192 |
|---|---|---|
| J^tight | 1.2037514324 | 1.2037513102 |
| c_k^tight / c0_k (LC1–LC4) | 1.17016, 1.23798, 1.13972, 1.26715 | 1.17016, 1.23798, 1.13972, 1.26715 |
| equilibrium (node_hoist) | 9.62e-9, 8.65e-9, 9.60e-9, 9.72e-9 | 9.16e-9, 9.58e-9, 7.98e-9, 9.76e-9 |
| same in the CPU-assembled matrix | 9.62e-9, 8.65e-9, 9.60e-9, 9.72e-9 | 9.16e-9, 9.58e-9, 7.98e-9, 9.76e-9 |
| solver per case | mg64 (no fallback) | mg64 (no fallback) |
| moduli hash and fixed set | match | match |
| S1: max \|c^prod − c^tight\| / c^tight | 2.15e-8 | 1.96e-8 |
| MND | 0.00158 | 0.00158 |
| solid fraction of active elements (ρ_phys > 0.5) | 0.5420 | 0.5420 |

- **S1** holds as a measurement: 2.15e-8 against the prediction ≤ 1e-4. The plan states the S1 rule for designs that
  pass E1, and this one does not, so the value is reported against the prediction only.
- **Reactions** (informational): they balance the applied loads to ≤ 2.3e-9 (force) and ≤ 1.3e-8 (moment) relative
  (summary.json `runs.A_R_n192.reactions_informational`).

### 4.4 Original stencil against repaired (C2–C5; summary.json `comparison_O_vs_R_n192`)

- **C2, matching initial state.** All three hashes are identical: the initial design variable, the iteration-1
  ρ_phys and the iteration-1 FP32 moduli. The comparison is valid.
- **C5, path divergence.** J of the two runs first differs by more than 1e-6 relative at iteration 101. The largest
  difference over 300 iterations is 2.19e-6. Through the continuation (iterations 1–75) the largest difference is
  6.03e-8, at iteration 4 (summary.json `C5_path_divergence.max_J_rel_diff_iterations_1_75`).
- **C3, design outcome.**
  - |ΔJ^tight| / J^tight_R = 1.02e-7; per load case 0.49e-6 to 2.11e-6.
  - Mean |Δρ_phys| over designable elements is 2.03e-5. The fraction of designable elements with |Δρ_phys| > 0.5 is
    9.67e-6.
  - The plan's equal/different label applies only when both runs are completed-verified, so no label is given.
- **C4, cost.** Every ratio lies in [0.95, 1.05], so no difference is measurable at single-run resolution.

| quantity | O | R | O/R |
|---|---|---|---|
| optimization time (s) | 561.4 | 566.4 | 0.991 |
| from iteration 1's callback entry to the end (s)¹ | 559.3 | 556.0 | 1.006 |
| median iteration (s) | 1.502 | 1.488 | 1.010 |
| median solve per case (s) | 0.399, 0.385, 0.359, 0.307 | 0.394, 0.384, 0.354, 0.309 | 1.012, 1.004, 1.013, 0.996 |
| pool peak (B) | 710,394,880 | 710,394,880 | 1.000 |
| summed IR outer steps per case | 1212, 1221, 1193, 1210 | 1210, 1222, 1191, 1208 | |
| summed inner V-cycle-PCG iterations per case | 29263, 28690, 25568, 24684 | 28660, 28303, 25182, 24343 | |

¹ The job's "iterations 2 to the end" timer starts when iteration 1's `on_iter` callback is entered, before the
initial-state hashes and the first history write, so it holds iterations 2 to the end plus that callback. Both runs
used the same boundary. The callback is not timed on its own, but it is one of the 300 callbacks summed in
`on_iter_io_s` (3.18 s for O, 3.30 s for R), so the plan's quantity lies in [556.1, 559.3] s for O and [552.7, 556.0] s
for R, and its O/R ratio in [1.000, 1.012], inside the ±5 % band (summary.json
`C4_cost_ratios.iterations_2_to_end_s.plan_quantity_ratio_bounds`).

The summed outer and inner counts cover the 300 design iterations and the final production re-solve: the plan's
optimization boundary includes that re-solve. The median solve times are taken over the 300 design-iteration solves of
each case (summary.json `runs.<run>.history_summary`).

At n = 192 the original stencil completed every production solve on this bracket, and it followed the repaired path
to within the optimizer's own resolution. It reached the same non-converged end state.

### 4.5 Cost and memory of R_n192 (S2, S3; summary.json `runs.R_n192.cost`, `history_summary`, `S2`)

- **Optimization time.** 566.4 s for 300 design iterations and the final re-solve.
  - From entry to iteration 1's callback to the end took 556.0 s, so iterations 2 to the end took between 552.7 and
    556.0 s (the callback is at most the 3.3 s of all callbacks; summary.json `cost.iterations_2_to_end_s`). The
    median iteration took 1.488 s.
  - The time splits into solves 464.8 s, multigrid setup 15.8 s, sensitivities 1.2 s, OC 7.2 s and filter 0.35 s.
    The solve and setup totals include the final production re-solve (1.47 s of solves, 0.22 s of setup). The driver's
    own totals cover the design iterations only (summary.json `cost.totals_design_iterations_only`).
  - The per-iteration persistence (`on_iter`) inside the boundary took 3.3 s.
- **S2.** The pool peak was 710,394,880 B against T30's model of 716,025,067 B, a ratio of 0.992, so S2 holds.
  - That is 361 B per allocated element and 786 B per active element.
  - The sampled process-dedicated peak was 1,136,848,896 B (monitor).
- **Tight audit work, measured separately** (`A_R_n192`; summary.json `runs.A_R_n192`).
  - The four solves plus the setup (0.49 s) took 5.64 s, with 195, 194, 187 and 189 PCG iterations, and a pool peak
    of 734,402,560 B.
  - The job's wider audit interval, which also holds the equilibrium checks, reaction sums and host transfers, was
    5.76 s.
  - For the original-stencil design (`A_O_n192`) the four solves plus setup took 5.58 s (wider interval 5.67 s).

## 5. n = 384 (H2)

R_n384 was admitted with a predicted peak of 4,759,430,005 B against 22,601,007,104 B free
(`out/runs/R_n384/monitor.json`). It ran to the end, and so did its audit.

| item | R_n384 | source |
|---|---|---|
| (a) stopping rule | **no**, `guard` after 300 iterations | summary.json `E1.R_n384` |
| (b) \|V − 0.5\| | 3.1e-10 | same |
| (c) production solves ≤ 1e-5 | yes, 1,204 solves, max 9.976e-6, no solve failure | same |
| (d) audit | valid (moduli hash and fixed set match); equilibrium 9.92e-9, 9.39e-9, 9.34e-9, 8.49e-9 | `out/runs/A_R_n384/gpu_meta.json` |
| (e) spill and coverage | **not established**: no spill (shared growth 98 MiB) or allocation failure, but coverage only from the third launcher sample (section 2) | `out/runs/R_n384/monitor.json`, `out/runs/A_R_n384/monitor.json`, summary.json |
| E1 | **fails on (a)**; (e) not established | summary.json |

**Why the rule did not fire** (descriptive; summary.json `runs.R_n384.end_state_descriptive`).
- The J-spread test alone holds from iteration 76. The spread over the last 10 iterations is 1.18e-6.
- The other two tests never hold after iteration 75: max |Δρ_phys| stays at or above 0.449, and at least 52,705
  elements move by more than 0.01. The bounded-oscillation limit is 7 elements (1 ppm of 7,232,600).
- At the end, about 80,200 to 80,500 elements still move by more than 0.01 at every iteration, and that count grows
  slowly over the last 10 iterations. J does not alternate here: it drifts slowly downward, in pairs of nearly equal
  values (summary.json `runs.R_n384.end_state_descriptive.J_last12`). As at n = 192, the record does not show which
  elements move.

**Retained design** (`out/runs/A_R_n384/gpu_meta.json` `endpoints`; summary.json `runs.R_n384.result`).
- J^tight = 1.2040870254, and c_k^tight / c0_k = 1.17007, 1.23561, 1.14053, 1.27014.
- S1: the largest production-to-tight difference is 4.98e-8. This is a measurement only, because the design does not
  pass E1.
- MND is 0.0050, and the solid fraction of active elements is 0.5416.
- Reactions (informational) balance the applied loads to ≤ 3.5e-9 (force) and ≤ 1.5e-8 (moment) relative.

**Cost and memory** (summary.json `runs.R_n384.cost`, `history_summary`, `S2`).
- **Optimization time.** 4,136.0 s.
  - From entry to iteration 1's callback to the end took 4,125.2 s, so iterations 2 to the end took between 4,122.0
    and 4,125.2 s (the callback is at most the 3.2 s of all callbacks). The median iteration took 13.59 s.
  - The time splits into solves 3,969.9 s, setup 21.1 s, sensitivities 12.4 s, OC 52.8 s and filter 3.0 s. The solve
    and setup totals include the final production re-solve (13.4 s of solves, 0.37 s of setup).
- **Solver work** (design iterations plus the final re-solve, except the medians).
  - The median solve times per case, over the 300 design-iteration solves, were 3.35, 3.57, 2.84 and 3.47 s.
  - The summed IR outer steps per case were 1427, 1418, 1203 and 1415.
  - The summed inner iterations were 48004, 49195, 40355 and 48844.
- **S2.** The pool peak was 4,410,662,912 B against a model of 4,218,875,480 B, a ratio of 1.045, so S2 holds, near
  the edge of its ±5 % band.
  - That is 280 B per allocated element and 610 B per active element.
  - The sampled process-dedicated peak was 4,651,872,256 B.
- **Tight audit** (`A_R_n384`; summary.json `runs.A_R_n384`).
  - The four solves plus the setup (0.99 s) took 53.4 s, with 300, 292, 284 and 297 PCG iterations, and a pool peak
    of 5,143,906,304 B.
  - The job's wider audit interval, which also holds the equilibrium checks, reaction sums and host transfers, was
    54.4 s.

## 6. Figure data

`t31_figdata.py` wrote one npz and JSON pair for each retained design. Each holds:
- the element classes and the final ρ_phys at native resolution;
- the clamped-node and pin-bore node coordinates;
- C and the four (F, M) vectors, and the frame;
- the per-iteration histories of J, every c_k, the volume, MND, max |Δρ_phys| and the moving-element count.

The files are `out/figdata_n192.{npz,json}` (R_n192), `out/figdata_O_n192.{npz,json}` (O_n192) and `out/figdata_n384.{npz,json}` (R_n384). The figure itself is
left to the figure maker.

## 7. What this means for R1.4

- **No R1.4 resolution yet.** Under the frozen plan, no complete four-load design exists at n = 192 or 384. Every
  retained design reached the 300-iteration guard of the authors' stopping rule. The application status is
  therefore **inconclusive**, not unresolved.
- **Correctness held throughout.** The repaired path met every production residual (2,408 R solves at two sizes). All
  eight tight FP64 equilibrium checks of the two retained R designs passed at ≤ 1e-8, and the original-stencil
  design's four passed too.
- **The open item is the optimizer's stopping behaviour, not the solver.** In the final continuation phase (β = 32,
  move 0.05), the OC update keeps thousands of elements moving by more than 0.01 while J stays flat to 1e-5
  (n = 192) or 1e-6 (n = 384). This affects both stencils alike.
- **Memory coverage.** No job spilled or met an allocation failure over its monitored interval. That interval starts
  at the launcher's third sample, after each job's CUDA context and probe allocation, so E1 (e) as worded is also not
  established. Had a run met the stopping rule, it would still not have passed E1 under the frozen wording.
- **Original stencil at n = 192.** It completed every solve and tracked the repaired path to ≤ 2.2e-6 in J. Its tight
  J agrees to 1.0e-7, and its cost is the same within single-run resolution. On this problem, at this size, the
  original stencil showed no failure.
- **Sizes demonstrated** (not verified-converged designs, by the plan's rule):
  - n = 384: 7,232,600 active, 6,629,528 designable and 15,728,640 allocated elements, in 300 design iterations
    (4,136 s) with a 4.41 GB pool peak;
  - n = 192: 903,548 active, 827,324 designable and 1,966,080 allocated elements.
- **Budget.** All eight planned jobs ran. The compute took about 1 h 34 min, from 09:18 to 10:52, within the 10 h
  budget. No size or job was left out. The stopping rule and settings were not changed after the results; whether a
  different stopping or continuation rule should be adopted is the authors' decision.

## 8. Fix round 1 (CPU only; no GPU job, no measured value changed)

The checker's five points were corrected in `t31_analyse.py` and this report. `out/summary.json` was regenerated from
the unchanged job outputs. The previous versions are in `out/fix_r1/` (`summary_before.json`, `REPORT_before.md`,
`t31_analyse_before.py`, `DEVIATIONS_before.md`), and `out/fix_r1/summary_diff.txt` lists every changed field.

1. **Early divergence bound (C5).** Over iterations 1–75 the largest |J_O − J_R| / |J_R| is 6.03e-8, at
   iteration 4. The earlier report gave 4.7e-8. The first crossing of 1e-6 (iteration 101) and the full-history
   maximum (2.19e-6) are unchanged.
2. **Production work.** The solve and setup totals and the summed outer and inner iterations now include the four
   final production re-solves, which lie inside the plan's optimization boundary (sections 4.4, 4.5 and 5). At
   n = 384 these are 3,969.9 s of solves, 21.1 s of setup, and outer totals of 1427, 1418, 1203 and 1415. The driver's
   design-iteration-only totals are kept under their own label. The optimization wall times were already correct.
3. **Audit and C0 time.** The plan's endpoint is the four solve times plus the multigrid setup: 5.64 s (A_R_n192),
   5.58 s (A_O_n192), 53.42 s (A_R_n384), 7.28 s (c0_n192) and 17.58 s (c0_n384). The job's wider interval, which
   also holds the equilibrium checks, reaction sums and host transfers, is reported beside each.
4. **Coverage.** Coverage is complete from the launcher's third sample in all eight jobs, not from its first
   (section 2). E1 (e) is now recorded as not established; `e_no_spill_covered` is false for all three designs. No
   spill or allocation failure occurred over the covered interval. H1, H2, C1 and the application status are
   unchanged (inconclusive, inconclusive, not-converged, inconclusive); H1 and H2 now name both unmet items.
5. **End state at n = 192.** The report no longer calls the end state a period-2 design cycle. The record shows an
   alternating J and about 10,100 elements moving by more than 0.01 per iteration. It cannot show which elements
   moved or whether the field repeats, because only scalar histories and the final field were saved.

## 9. Fix round 2 (CPU only; no GPU job, no measured value changed)

The checker's two points were corrected in `t31_analyse.py` and this report, and `out/summary.json` was regenerated
from the unchanged job outputs. The job script `t31_job.py` was left as it ran. The previous versions are in
`out/fix_r2/`, and `out/fix_r2/summary_diff.txt` lists every changed field.

1. **Audit endpoint in the summary.** The job stored its wider timed interval under the endpoint name
   `audit_time_s_solves_plus_setup` (`t31_job.py:420`), and the summary copied it. The summary now gives the plan's
   endpoint under that name, the four solves plus the multigrid setup: 5.6423 s (A_R_n192), 5.5792 s (A_O_n192) and
   53.4236 s (A_R_n384). The wider interval is exported beside it as `broader_interval_s` (5.7597, 5.6658 and
   54.3562 s), with a note that the job's `gpu_meta.json` field of that name holds the wider interval. This report
   already gave the right values.
2. **"Iterations 2 to the end".** The job's timer starts at entry to iteration 1's `on_iter` callback
   (`t31_job.py:330`), before the initial-state hashes and the first history write, not at the callback's end as its
   note says (`t31_job.py:360`). The summary now exports the measured value under
   `measured_from_iteration1_callback_entry_s` and bounds the plan's quantity by subtracting at most the summed
   duration of all callbacks (`on_iter_io_s`): R_n192 552.7–556.0 s, O_n192 556.1–559.3 s, R_n384 4,122.0–4,125.2 s.
   Both stencils used the same boundary, so the measured O/R ratio (1.006) stands. The plan quantity's ratio lies in
   [1.000, 1.012], inside the ±5 % band, so the C4 reading is unchanged. The full optimization times were correct
   and are unchanged.

No verdict changed: H1, H2 and the R1.4 application status stay inconclusive, and C1 stays not-converged.
