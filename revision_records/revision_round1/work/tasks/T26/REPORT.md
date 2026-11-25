# T26: Bridge compliance change from k = 160 to k = 320 (A.3, R2.5)

**Status: done. Outcome against the acceptance statement: supports.**

The bridge's physical compliance rises by 7.84 % from k = 160 to k = 320. With fixed archived fields, the same SIMP
law and FP64 equilibrium at true residual ≤ 1e-10, that rise splits into two parts:
- a fixed-field mesh contribution of +1.0026 in 2kc (+3.56 % of C_A);
- a fine-grid design contribution of +1.2053 (+4.28 %).

The two parts sum to the re-solved endpoint change of +2.2079 (+7.84 %), both at 4 decimals of 2kc and at 0.01 %.
The re-solved change differs from the native-record change by 3.8e-7 in 2kc, which is the difference of the two
endpoint offsets. Every stability check lies more than 6 orders of magnitude below the reported precision.

The k = 320 solves come from the approved rerun k320_r2 (§4). The first k = 320 job, k320_r1, stays refused for
memory, and no value from it is used.

## 1. Protocol (as specified; nothing tuned)

**Fields.**
- The difference-form designs of the corrected Figure 4: results/E32/simp_bridge_k160_mg64_stencil_diff.npz and
  ..._k320_... (T25's panels b2 and b5).
- Each archive is the float16 cast of its run's final FP32 physical density. It is decoded to float32 exactly
  (`decode_exact` true for all six solves).
- Subdivision (solve B): each k = 160 element becomes 2×2×2 elements of the same density. The field mean stays
  0.20000000056473072 (solve_A.json and solve_B.json, `field_info`; same archive digest).

**SIMP law.**
- E = Emin + (E0 − Emin)ρ^p with each record's final p = 4.5, Emin = 1e-9 and E0 = 1, formed by the authors'
  modulus kernel. The law is the same for A, B and C (checks.json, `same_simp_law`).
- No filter and no projection is applied.

**Problem.** voxfem.core.bridge(k) on each solve grid. The physical supports are the bottom edges at x = 0 (pinned)
and x = 2 (roller). The total strip load is −1 on |x − 1| ≤ 0.05, y = 1, over the full depth. Both are discretized
by core.py on each grid (§5). B and C carry identical problem data (checks.json, `same_physical_load_and_supports`).

**Equilibrium.**
- The authors' FP64 PCG (krylov.pcg64) with the FP64 node-owned operator of every accepted state solve, and the FP32
  difference-form V-cycle as preconditioner (solver family mg64), started from zero.
- Stages to 1e-8, 1e-9 and 1e-10. The reported state is the one with terminal true residual ≤ 1e-10.
- Physical compliance C = 2kc.

**Checks on each reported state.**
- u·r and c − uᵀKu.
- The residual and energy recomputed with a second FP64 operator (element-owned, coloured).
- The element-energy sum Σ E_e u_eᵀK u_e.
- Zero displacement at the fixed DOFs.
- A continuation to 1e-11 that is recorded but does not replace the reported state.

**Code.** The voxfem copy equals the authors' code/src/voxfem and the per-file hashes of both E32 bridge records
(out/inputs.json, `code`).

## 2. Re-solved compliances (out/compliance_scaling.csv, out/summary.json)

| Solve | Field | Grid | C = 2kc re-solved | True residual | PCG its | Native record 2kc | Offset (re-solved − native) |
|---|---|---|---|---|---|---|---|
| A | difference form, k = 160 | k = 160 | 28.154166326392712 | 9.40e-11 | 706 | 28.154166494212753 | −1.678e-7 (−5.96e-9 rel.) |
| B | A's field subdivided 2×2×2 | k = 320 | 29.156748227496205 | 9.97e-11 | 758 | – | – |
| C | difference form, k = 320 | k = 320 | 30.36207324903513 | 8.24e-11 | 119 | 30.362073034759515 | +2.143e-7 (+7.06e-9 rel.) |
| A_xprec (check) | as A, original-stencil V-cycle as preconditioner | k = 160 | 28.154166326389092 | 9.57e-11 | 596 | – | – |
| D (supplementary) | original stencil, k = 160 (submitted figure, results/E6b) | k = 160 | 28.154166447471848 | 9.35e-11 | 663 | 28.154166516739892 | −6.93e-8 (−2.46e-9 rel.) |
| E (supplementary) | original stencil, k = 320 (submitted figure, results/E7) | k = 320 | 30.362029320557586 | 8.22e-11 | 119 | 30.362029244082574 | +7.65e-8 (+2.52e-9 rel.) |

Sources: A, A_xprec and D are in out/runs/k160_r1/solve_*.json; B, C and E are in out/runs/k320_r2/solve_*.json.
The native values are the records' own endpoints (out/inputs.json, `fields`).

## 3. Decomposition and reconciliation

**Decomposition** (summary.json; C = 2kc; percentages relative to C_A):

| Contribution | Definition | Δ(2kc) | Rounded | % of C_A | Share of total |
|---|---|---|---|---|---|
| mesh | C_B − C_A | 1.0025819011034933 | 1.0026 | 3.5610 % (3.56 %) | 45.41 % |
| design | C_C − C_B | 1.2053250215389255 | 1.2053 | 4.2812 % (4.28 %) | 54.59 % |
| total | C_C − C_A | 2.207906922642419 | 2.2079 | 7.8422 % (7.84 %) | 100 % |

**Closure** (checks.json):
- Unrounded: (mesh + design) − total is zero to floating-point rounding (`sum_closes_exactly_unrounded`).
- At 4 decimals of 2kc: 1.0026 + 1.2053 = 2.2079, the rounded total (`sum_closes_at_reported_precision_C`).
- At 0.01 %: 3.56 % + 4.28 % = 7.84 %, the rounded total (`sum_closes_at_reported_precision_pct`).
- Rounding caveat (`differences_of_rounded_C_match`: false). Differences formed from the rounded compliances
  28.1542, 29.1567 and 30.3621 give 1.0025 and 1.2054, one unit off in the last place each, while their total 2.2079
  agrees. The contributions must therefore be quoted from the unrounded values, as above, and not recomputed from
  4-decimal compliances.

**Native endpoints and offsets, reported separately.**
- Native-record change, difference form: 30.362073034759515 − 28.154166494212753 = 2.2079065405467624, i.e. +7.842202 %.
- Re-solved change: 2.207906922642419, i.e. +7.842203 %.
- The two differ by −3.82e-7 in 2kc. That difference equals offset_A − offset_C (−1.678e-7 − 2.143e-7): the identity
  closes to floating-point rounding (`reconciliation_closes`).
- The offsets have two possible sources: the float16 storage of each field, and the native state solve's stopping at
  true residual ≤ 1e-5. The records do not allow them to be split between these, and they are not split here. Both
  offsets are below 1e-8 relative, at least 230 times smaller than the 5e-5 half unit of the 4-decimal precision.

**Reconciliation with the submitted ≈ 7.84 %.**
- Submitted figure (original-stencil records E6b/E7), native: +7.842046 %.
- Original-stencil archived fields re-solved (D, E; supplementary): +7.842047 %.
- Difference-form records of the corrected figure, native: +7.842202 %.
- Difference-form archived fields re-solved (A, C): +7.842203 %.
- All four round to 7.84 %. The step from the submitted to the corrected figure's fields changes the endpoint change
  by 1.6e-4 percentage points. At k = 320 the two stencil forms' designs differ by 4.39e-5 in 2kc (C − E), and at
  k = 160 by −1.21e-7 (A − D).

**What the contributions contain.**
- The mesh contribution (C_B − C_A) keeps the physical density fixed and changes only the discretization. It
  therefore includes the finer displacement approximation and the discrete representation of the line supports and
  of the strip load on the finer grid (§5). These effects are not separated from one another.
- The design contribution (C_C − C_B) holds every difference between the two retained designs on the same k = 320
  grid. It is not split further and not attributed to any cause. Its sign is positive: the k = 320 optimized field is
  more compliant on the k = 320 grid than the subdivided k = 160 field. Both have mean density 0.2 (B
  0.20000000056473072, C 0.19999999998511522).

## 4. Numerical stability and run records

**Stability at the quoted precision** (summary.json, `stability`; checks.json, `numerical_stability_at_reported_precision`):
- For A, B and C, every check differs from the reported 2kc by at most 4.41e-11 (B, the 1e-9 → 1e-10 stage change).
  The checks are the stage change, the 1e-11 continuation, u·r, c − uᵀKu, the second operator and the element-energy
  sum. The bound for A is 5.71e-12 and for C 2.04e-12.
- The supplementary D and E stay below 4.36e-12.
- The preconditioner changes A's 2kc by 3.62e-12 (A_xprec − A).
- The fixed DOFs carry exactly zero displacement in all six solves.
- The largest deviation, 4.41e-11, is about 1.1e6 times smaller than the half unit 5e-5 of the 4-decimal precision.

**Finding: B stagnates near 1e-10.** Solve B needed 758 PCG iterations to reach 9.97e-11, against 119 for C on the
same grid. Its 1e-11 continuation stopped at its 1,500-iteration bound with true residual 8.98e-11, having changed c
by −4.68e-13 relative (solve_B.json, `extension`). The reported state meets the 1e-10 criterion, and the stagnation
is 7 orders of magnitude below the quoted precision. Its cause (the FP32 V-cycle on the subdivided field) was not
investigated.

**Run-to-run reproducibility at k = 160 (finding).**
- The repeat job (out/runs/k160_r2_v2check, transfer-chunked job version 2) reproduces A_xprec and D bit for bit.
- A differs by −3.23e-12 in 2kc (−1.15e-13 relative), with 596 instead of 706 PCG iterations. The moduli of the two
  runs are identical (same hash).
- The first stage (1e-8) is bitwise equal in both runs. The difference arises in the warm-restarted stages and was not
  traced further. It is far below the reported precision.
- The reported k = 160 values are those of k160_r1. They were made with job version 1, which differs from version 2
  only in how host-device transfers are made.

**The k = 320 refusal and the approved rerun.**
- k320_r1 (out/runs/k320_r1/monitor.json) is **refused for memory**. At 12.7 s, before any solve, its shared usage
  stood 337,641,472 B above its baseline, over the 268,435,456 B limit. Of that growth, 262,144,000 B came from one
  unchunked host-to-device copy of the subdivided field. No value from it is kept.
- Diagnosis (out/runs/diag_r1/diag.json): each unchunked host-to-device copy raised the process's shared usage by its
  own size, persisting after freeing; copies in pieces of 32 MiB or less added nothing.

  | Step | Shared usage above baseline |
  |---|---|
  | unchunked 64 MiB host-to-device copy | 67,108,864 B |
  | plus an unchunked 128 MiB copy | 201,326,592 B |
  | after freeing both arrays | 201,326,592 B (persists) |
  | 262,144,000 B moved to the device and back in 32 MiB pieces | no further growth |

- Job version 2 (t26_job.py) makes every host-device transfer in pieces of at most 32 MiB and forms the fixed-DOF
  check on the device. Its numerical steps are unchanged. At k = 160 it reproduced the per-process shared growth of
  79,691,776 B of T25's production job.
- The authors approved one rerun of B, C and E at k = 320 with version 2 and every guard unchanged, including the
  256 MiB spill sampler. This is a single exception to the last clause of GPU rule (c), granted because the cause had
  been found and fixed. The rerun is k320_r2 (checks.json, `k320_rerun`).

**k320_r2 records** (out/runs/k320_r2/monitor.json and gpu_meta.json):
- Admission: predicted peak 16,656,356,864 B. That is the bridge k = 320 record's measured peak pool of
  16,301,786,624 B plus the CUDA context. With the 1.5 GiB margin it fit in the 22,664,970,240 B that nvidia-smi
  reported free. Other processes held 6,471,901,184 B dedicated, recorded and not counted. guard.require_budget
  answered ok, with effective free memory 18,930,225,152 B. The pool cap was 22,542,286,848 B.
- Watch: covered from the first sample containing the job (`covered_from_go` true), 195 samples, final sample
  checked, no stop. Shared growth 79,691,776 B above the baseline of 77,594,624 B, against the 268,435,456 B limit.
  The job's process-dedicated peak was 15,013,937,152 B.
- In-process watch: no spill, maximum shared growth 79,691,776 B. Peak pool reservation 14,597,676,032 B, below the
  prediction. There was no allocation failure.
- Status ok, valid, not spilled. All three solves completed.

**GPU rule records of the other kept runs.**
- k160_r1: covered from the first sample containing the job; final sample checked; shared growth 113,246,208 B; no
  spill. guard.require_budget answered ok, with effective free memory 18,930,225,152 B.
- At k = 160 the pool peak was 2,645,843,456 B. That is 46,200,320 B above the predicted 2,599,643,136 B, because
  two V-cycle hierarchies briefly coexisted when the job switched to the A_xprec preconditioner. The overshoot was
  inside the 1.5 GiB margin, with no spill and no allocation failure. The k = 320 job reused one hierarchy for all its
  solves.

## 5. Discrete load and support representation (out/inputs.json, `discretization`)

These are the discretization differences that the fixed-field mesh contribution C_B − C_A contains, beyond the finer
displacement approximation:

| | k = 160 | k = 320 |
|---|---|---|
| loaded nodes (x-lines × z-lines) | 2,737 (17 × 161) | 10,593 (33 × 321) |
| share per node of the total −1 | −3.6536e-4 | −9.4402e-5 |
| share on one end x-line (x = 0.95 or x = 1.05) | 5.88 % | 3.03 % |
| (consistent trapezoid share of one end line, for comparison) | 3.125 % | 1.5625 % |
| load second central moment in x | 9.375e-4 | 8.854e-4 |
| pinned / roller support nodes (lines along z) | 161 / 161 | 321 / 321 |

The total load (−1), its x-centre (x = 1) and the strip's physical extent [0.95, 1.05] are the same on both grids. The
equal nodal shares put more weight on the strip edges than a consistent nodal load would, and that excess halves
from k = 160 to k = 320. The supports are lines, so their discrete representation also changes with the mesh. The
k = 320 solves record 10,593 loaded DOFs, each with −9.440196e-5, and a total of −1 (solve_B.json, `load`). None of
these effects is separated from the others; the mesh contribution holds all of them.

## 6. Acceptance

| Acceptance point | Result |
|---|---|
| The two differences sum to the re-solved saved-field endpoint change at reported precision | yes: 1.0026 + 1.2053 = 2.2079 in 2kc; 3.56 % + 4.28 % = 7.84 % |
| Offsets from the native JSON endpoints reported separately | yes: A −1.678e-7, C +2.143e-7 (supplementary D −6.93e-8, E +7.65e-8) |
| Reconciliation with the submitted ≈ 7.84 % | yes: submitted native 7.842046 %, original-stencil re-solved 7.842047 %, difference-form native 7.842202 %, re-solved 7.842203 % |
| Numerical stability at the quoted precision | yes: largest deviation 4.41e-11 in 2kc against a half unit of 5e-5 |
| The mesh contribution includes the discrete load representation | yes: B uses core.py's k = 320 load and supports on A's fixed field (§5) |
| No unsupported causal allocation of the design contribution | holds: C − B is reported as the difference between the two retained designs, not split |

## 7. Compute and files

**Compute.** GPU wall time used was about 13 min of the 3 h budget, which counts from the first job at 12:07:

| Run | Wall time | Status |
|---|---|---|
| k160_r1 | 114 s | ok (reported k = 160 values) |
| k320_r1 | 16 s | refused for memory |
| diag_r1 | 44 s | ok (transfer diagnostic, no solve) |
| k160_r2_v2check | 104 s | ok (version 2 check, reproducibility only) |
| k320_r2 | 490 s | ok (approved rerun; reported k = 320 values) |

Nothing was run outside the guarded launcher. The launcher self-test passed before k160_r1, diag_r1,
k160_r2_v2check and k320_r2 (out/launch_selftest.json).

**Scripts.**
- t26_common.py: configuration.
- t26_inputs.py: CPU-only input, code and discretization checks.
- t26_job.py: version 2, which ran k160_r2_v2check and k320_r2. Version 1, which ran k160_r1 and k320_r1, is kept as
  t26_job_v1.py and t26_common_v1.py.
- t26_diag.py: the transfer test.
- t26_launch.py and t26_launch_selftest.py: T25's watch rules, unchanged. The only addition is the job-to-script map.
- t26_analyse.py: CPU only. After k320_r2 it also writes the k = 160 reproducibility rows, D/E stability and the
  rerun record in the complete branch; no computed quantity changed.

**Outputs.**
- out/compliance_scaling.csv: one quantity per row, with its definition and source.
- out/summary.json
- out/checks.json
- out/inputs.json
- out/launch_selftest.json
- out/runs/{k160_r1, k320_r1, diag_r1, k160_r2_v2check, k320_r2}/

**Release (A.3).** Every T26 script is data-only and draws nothing, so it may be released. No figure was made.

**Notes for the writer.**
- The main text needs only the split: fixed-field mesh +3.56 %, design +4.28 %, total +7.84 %. The FP64 re-solve of
  the stored fields reproduces the native endpoints to below 1e-8 relative. Job names, the transfer chunking and the
  refusal belong in the repository, not in the paper.
- Quote the contributions from the unrounded values (§3, rounding caveat).
- decision_request.json is answered by the authors' approval and kept as a record.
