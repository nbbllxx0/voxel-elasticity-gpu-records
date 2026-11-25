# T24 analysis plan: paired 8.2M bridge optimizations at state-solve tolerances 1e-5 and 1e-6

Status: frozen when the pipeline records this file's hash (2026-11-24). Nothing in this file changes afterwards.
A departure found later goes to `tasks/T24/DEVIATIONS.md`, dated and placed in time relative to the data: before any
confirmatory job, or after it.

Serves: R3.4 (Reviewer 3, point (3): "whether these discrepancies accumulate") and A.4 (native-precision field
comparison on the 8.2M mesh). The tight-reference trajectory (target 1e-8) belongs to T34 and is outside this plan.
T34 may reuse the fields saved here.

---

## 1. Question

On the 320 × 160 × 160 bridge (8,192,000 elements), the mesh where the submitted paper found a 15–17 % sensitivity
error at design iteration 67, run two complete optimizations that differ only in the true-residual acceptance
tolerance of the state solve (τ = 1e-5, the production value, and τ = 1e-6). Then:

- Q1 (endpoint compliance). Does one decade of tightening change the tight-FP64 compliance of the retained design?
  Signed difference, both values, and their resolution.
- Q2 (endpoint field). How far apart are the two retained native-FP32 physical density fields? Mean and maximum
  |Δρ|, strict ρ > 0.5 crossings.
- Q3 (course). Over the iterations both runs share, does the field difference between the runs grow, decay or
  persist? This is where "does (not) accumulate" is decided.
- Q4 (work). What does the tighter tolerance cost in Krylov iterations, V-cycle applications and solve time, and
  when does each run stop?

Scope of the answer, whatever the outcome: this pair measures what one decade of tightening does. It does not
measure the accumulated distance from the trajectory of the tight solve against which the 17 % was measured. That
distance is T34's question. Every statement derived from this plan says so.

## 2. Data and the role of each part

There are no learned models or data splits. The roles are as follows.

| Part | What it is | Role | Status |
|---|---|---|---|
| D-dev-1 | `results/E30/tol_bridge_k80_mg64_stencil_diff_tol1e-0{3,4,5,6}.{json,npz}` and T23's re-reading of them (`tasks/T23/out/tolerance.csv`) | sets expected magnitudes and thresholds; also the fixed fallback | already published (S24), inspected |
| D-dev-2 | `results/E32/simp_bridge_k160_mg64_stencil_diff.json` (the published 8.2M bridge run at 1e-5, no audits, per-iteration history) and `results/E30/audit_bridge_k160_mg64_stencil_diff.json` (same configuration, audited) | sets the expected run length, memory and time; serves as reference for the reproducibility check C5 | already published, inspected |
| D-dev-3 | development smoke runs at small grids (§6.2), produced after freezing | function checks of the job only; never used for any endpoint | produced later, not sealed |
| **Run A** | new 8.2M bridge optimization, τ = 1e-5 | primary leg | **sealed**: does not exist yet |
| **Run B** | new 8.2M bridge optimization, τ = 1e-6 | primary leg | **sealed**: does not exist yet |
| **Run A′** | new 8.2M bridge optimization, τ = 1e-5, an exact repeat of A | control: run-to-run floor | **sealed**: does not exist yet |

Facts from development data that the plan relies on (inspected for planning only):
- E32 1e-5 run: 79 design iterations, termination `bounded_oscillation`, final accepted compliance
  0.08798177029441485, 3,789 PCG iterations in the loop plus 9 in the final solve, loop wall time 120.7 s. Process
  peak device memory 3,925,344,256 B against a baseline of 1,612,185,600 B, so about 2.31 GB for the job.
  The per-iteration largest physical change is still 0.335 at iteration 79, with 7 elements moving by more than
  0.01. The run stops on a bounded oscillation of a few elements, not on a small maximum change.
- E30 audited 1e-5 run against E32: the two published 1e-5 trajectories with the same `voxfem` code agree bit for
  bit in the accepted true residuals and Krylov counts up to iteration 42, and differ in the 7th–8th significant digit
  of the residual from audited iteration 50 on, with equal Krylov counts. Both stop at 79. Whether this comes from the audit's side effects or
  from run-to-run variation is unknown. Either way, bit-reproducibility of an 8.2M trajectory is not established,
  and this plan therefore includes the replicate A′.
- Tight FP64 re-solves to 1e-10 at k = 160 took 13 to 3,189 PCG iterations (E30 audit) and are not
  bit-reproducible (T23: 1,388 against 1,380 at iteration 67).
- k = 80 bridge, 1e-6 against 1e-5 (T23 `tolerance.csv`): same stopping iteration (82); relative tight-compliance
  difference +1.78e-9; mean |Δρ| of FP16-stored fields 3.40e-9, maximum 4.88e-4; 2,724 changed stored entries;
  0 strict crossings; Krylov ratio 1.39. Against 1e-3 instead: +3.62e-5, mean 8.99e-5, 92 crossings.

No file of runs A, B or A′ is opened, and nothing is computed on them, before the hash is recorded. They do not
exist at the time of writing.

## 3. Fixed protocol (identical in A, B and A′ except τ)

- Code: byte-identical copies of the authors' `code/src/voxfem` and of the problem definition, placed in
  `tasks/T24/src/`. The authors' tree is not modified. The CuPy kernel cache lives in the task folder.
- Problem: `PROBLEMS["bridge"](160)`. Grid 320 × 160 × 160 on [0,2]×[0,1]×[0,1], 8,320,641 nodes and 24,961,923
  DOFs. Bottom edge at x = 0 pinned, at x = 2 a roller; total load −1 in y on the top centre strip of width 0.1. No
  padding (the solver grid equals the design grid).
- Configuration: `Config(volfrac=0.20, solver="mg64", op32="stencil_diff", tol=τ)`, all other fields at their
  defaults. That means FP64 operator `node_hoist`; FP64 PCG with the FP32 Galerkin V-cycle whose fine level is the
  repaired difference-form stencil; `pcg_maxit` 20,000; `mg_nu` 2; `max_coarse_dofs` 2,500; E_min 1e-9, E_0 1;
  raw lower bound 0; η 0.5; the R2 continuation schedule (p, β, move, r_min) = (1.5, 1, 0.20, 1.50) to iteration 15,
  (3.5, 4, 0.15, 1.35) to 40, (4.5, 16, 0.08, 1.25) to 65 and (4.5, 32, 0.05, 1.20) after that; `max_outer` 300.
- Starting design: uniform 0.20 in every run. Warm starts: each state solve starts from the previous accepted state
  and resets to zero when that is worse than zero (the driver's `reset_if_worse`). The smoother weights are
  refreshed every 5 setups and at each continuation step. OC uses the driver's bisection with its warm-started
  multiplier bracket.
- Stopping: the driver's own rules, unchanged. After iteration 75, the run stops when the spread of the last 10
  compliances is ≤ 1e-4 and either max |Δρ_phys| ≤ 0.01 (`max_change`) or at most ⌊1 ppm × 8,192,000⌋ = 8
  elements move by more than 0.01 (`bounded_oscillation`). The change is measured against the previous field as the
  driver stores it (FP16). The retained design is the final iterate, re-solved once after the last update at τ.
- Per-iteration capture (the only addition). The job installs its own function as the driver's `log` callback. The
  driver calls it once per design iteration, after its iteration timer has stopped and before its spill check and
  stopping test. The callback only reads solver and optimizer state. It writes nothing that the driver reads, calls
  no driver method that has scratch state (no `physical`, `oc`, `sensitivities` or V-cycle), and allocates only its
  own buffers. At iteration i it does the following:
  1. Copies to the host, as native FP32: the post-update physical field P_i (the driver's `w2` after `oc`, which is
     the physical field of the new design at β_i and r_min,i, the field whose volume OC fixed), the new raw design
     ρ_i (`rho`), and the state field R_i (`rho_phys`, the field whose compliance c_i is).
  2. Saves P_i and ρ_i at every iteration. It saves R_i in full at i ∈ {1, 16, 41, 66} and at every i where R_i is
     not bit-identical to P_{i−1}. At every other i it records only the bitwise-equality flag against a
     device copy of P_{i−1} that the job keeps.
  3. Computes the FP64 true residual r_i = f − K(E_i) u_i of the accepted state into its own buffer, using the
     driver's FP64 operator (read-only), and records ‖r_i‖/‖f‖, which must equal the driver's `rel_true`, and the
     first-order compliance indicator e_i = |u_i · r_i| / c_i.
  4. Records its own wall time (`hook_s`).
  Device-to-host copies of the 32,768,000 B fields are below the 32 MiB piece limit. Any larger copy (the
  displacement vectors) goes in pieces of at most 32 MiB.
- Endpoint: after `run()` returns, the job saves the retained field E^X (the driver's final `rho_phys`) and checks it
  bit for bit against P_{N_X}. It saves the accepted final displacement u_X. It then performs the tight re-solve (§4,
  E2), saves the tight displacement and computes the independent residual. All of this is outside the driver's
  timers.
- Production timing is the driver's `totals` (solve, setup, sensitivities, OC, filter) and its per-iteration
  `t_iter_s`. These exclude the capture and the endpoint work, whose times are reported separately.
- Storage: `tasks/T24/out/fields/<run>/P_it###.npz`, `rho_it###.npz`, `R_it###.npz`, `E_final.npz`,
  `u_accepted.npy`, `u_tight.npy`. FP32 fields go through `numpy.savez_compressed`, which is lossless.
  Scalars go to `out/runs/<run>/result.json`, monitors to `out/runs/<run>/monitor.json`.

### GPU guards (binding rules of 2026-11-23, applied unchanged)

The launcher is a copy of T26's guarded launcher. It keeps the atomic lock with no stale-lock deletion, the
exclusivity check, admission computed with no CUDA context, a watch that fails closed (the carrier PID must be in
the sample with both counters), the final sample before disarm, and the time cap. Its self-test is run before the
first GPU job, and a failing self-test stops the task.

- Admission: predicted peak 3.5 GB. That is the measured 2.31 GB, plus 0.20 GB for the residual buffer, 0.03 GB for
  the P_{i−1} copy, 0.80 GB for the tight re-solve's own PCG work vectors and cast buffers, and a rounding allowance.
  A job is admitted when 3.5 GB + 1.5 GB ≤ the driver-reported free memory (nvidia-smi, no CUDA context).
  `guard.require_budget`'s answer and the other processes' dedicated usage are recorded beside it, for information.
- The CuPy pool is capped with `set_limit` at the driver-reported free memory at start minus 1.5 GB.
- The spill sampler runs every few seconds. Shared usage more than 256 MiB above its start stops the job at once,
  and the job is recorded as refused for memory. It is never rerun at this size. An allocation failure is a refusal,
  not a result.
- Time cap: 45 min per job (expected 5–15 min). The task budget is 5 h of wall-clock compute from the first GPU
  job. All compute ends by 2026-11-26 18:00.

## 4. Endpoints

Notation: X ∈ {A, B, A′}. N_X is the stopping iteration. S = min(N_A, N_B) is the last shared iteration. All field
statistics are taken over the 8,192,000 elements. Each difference is formed exactly as float64(a) − float64(b) of
the FP32 values and summed in FP64.

Field statistics for a pair of fields (a, b):
- mean |Δρ|
- max |Δρ|
- number of entries that differ (bitwise)
- number with |Δρ| > 1e-6, 1e-3, 1e-2, 0.1 and 0.5
- strict crossings: entries where (a > 0.5) ≠ (b > 0.5), split into up (b > 0.5 ≥ a) and down
- ties: entries equal to 0.5, and entries within 1e-6 of 0.5, in each field

**Primary**
- **E1 – retained designs.** Field statistics of E^B against E^A, each run at its own stopping iteration (N_B and
  N_A are both stated). Secondary companion: the same statistics for P_S^B against P_S^A.
- **E2 – tight compliance.** From the accepted final displacement of each run, FP64 PCG with the run's own FP32
  V-cycle (as E30's `reference_solve`) is run to a true relative residual ‖f − Ku‖₂/‖f‖₂ ≤ 1e-10, with at most
  20,000 iterations. If that stops above 1e-10, one restart follows from the last iterate with the same settings;
  no further restart. Results:
  - C*_X = f · u*_X;
  - its residual ρ_X, from the PCG's own explicit FP64 residual;
  - an independent residual ρ^ind_X, recomputed with the element-by-element `elem_colored` FP64 operator (a
    different summation order, deterministic);
  - the first-order indicator ε_X = |u*_X · r*_X| / C*_X.

  Reported quantities:
  - the signed difference ΔC = C*_B − C*_A and the relative δC = ΔC / C*_A;
  - both C* values and both residuals;
  - the accepted final compliances of both runs;
  - the resolution U = ε_A + ε_B. This is a first-order estimate, since C_exact − f·u = u·r + r·K⁻¹r, not a bound.

  δC is *resolved* when |δC| ≥ 10 U.
- **E3 – course.** For every shared iteration i = 1 … S, the field statistics of P_i^B against P_i^A. Their series are
  D_i (mean |Δρ|), M_i (max |Δρ|) and X_i (crossings). Values at the named checkpoints 16, 41, 66, 67 and S are
  reported in the text. The same-state companion series is the field statistics of R_i^B against R_i^A. R_i is the
  field the compliance c_i belongs to. Where R_i is bit-identical to P_{i−1} in both runs, the R series at i is the
  P series at i − 1. At i = 16, 41 and 66 it is computed from the saved R_i.

**Secondary**
- **E4 – work and stopping.** For each run: N_X and termination; PCG iterations, matrix-vector products and V-cycle
  applications summed over the loop plus the final solve; `solve_s` and `setup_s`; per-phase sums; the iterations of
  the tight re-solve. The ratios B/A for the work figures, and the times of the capture and the endpoint work.
- **E5 – accepted compliance course.** c_i^X, the relative difference (c_i^B − c_i^A)/c_i^A at each shared i (a
  pre-update compliance, labelled as such), the accepted residuals and the indicators e_i^X.
- **E6 – run-to-run floor.** E1, E2 (ΔC_AA′ = C*_A′ − C*_A), E3 (F_i = D_i of A′ against A) and E5 for A′ against A.
  Also whether A′ equals A bit for bit at every saved field and scalar.
- **E7 – descriptive.**
  - Field statistics of the raw designs ρ_i^B against ρ_i^A.
  - Each run's own per-iteration change (the driver's `drho_phys`, `n_elem_drho_gt_tol`).
  - At the endpoints: the share of the elements with |E^B − E^A| > 0.01 that are also among each run's own
    final-step movers (|P_N − P_{N−1}| > 0.01 in that run), which tests whether the endpoint difference sits in the
    oscillating elements of the bounded-oscillation stop.
  - Phase maxima of D_i (1–15, 16–40, 41–65, 66–S) and the jump ratios D_i/D_{i−1} at i = 16, 41, 66 and 67.

## 5. Hypotheses, thresholds and decision rules

The predictions below were made before any data, from D-dev-1 and D-dev-2.

### Gate G (validity; acceptance condition of the task)

G holds when all of the following hold for both A and B:
- termination is `max_change` or `bounded_oscillation` with N < 300;
- no `SolveFailed`, no spill, no allocation failure, and watch coverage passes;
- every P_i for i ≤ N_X and E^X were saved and read back;
- in E2, ρ_X ≤ 1e-10 and ρ^ind_X ≤ 1e-9. The independent gate is an order looser, because two FP64 operators
  with different summation orders differ by rounding. Both values are reported.

If G fails, no rerun of the trajectory follows, except a job that an operator stopped with no output. Such a job is
rerun once and recorded as a rerun after an operator stop. A spill or allocation failure is never rerun. The task
then reports its fixed fallback: T23's verified k = 80 result (1e-6 against 1e-5: +1.78e-9 relative tight
compliance, mean stored |Δρ| 3.40e-9, 0 crossings; 1e-3 against 1e-5: +3.62e-5, 92 crossings, fields stored in
FP16). The refined 8.2M question is reported as explicitly unresolved, with the reason. H1–H3 are then not
evaluated.

Checks that qualify but do not gate the result (each reported as passed or failed, with details):
- C1: E^X = P_{N_X} bit for bit.
- C2: the hook's ‖r_i‖/‖f‖ equals the driver's `rel_true` at every i.
- C3: the k = 16 smoke run with and without the hook agrees bit for bit in every per-iteration c, `rel_true` and
  Krylov count (§6.2).
- C4: R_i = P_{i−1} bit for bit wherever (β, r_min) did not change.
- C5: run A against the E32 history. Reports the first iteration at which c, `rel_true` or the Krylov count differ,
  or that none does, plus N_A against 79 and the final accepted compliance against 0.08798177029441485.

C3 failing before the confirmatory jobs means the hook is fixed first (an implementation fix, recorded in
DEVIATIONS.md). C1, C2 or C4 failing after the jobs is reported beside the verdicts.

### Run-to-run attribution (applies to H1–H3)

- If A′ equals A bit for bit in every saved field and scalar, the floor is zero, and every A–B difference is
  attributed to the tolerance.
- Otherwise, an A–B quantity is attributed to the tolerance only where it exceeds 10 × the same A–A′ quantity
  (for a zero floor value, any nonzero A–B value is attributed). A contradiction verdict of H1, H2 or H3 requires
  this attribution. Without it the verdict is *inconclusive (tolerance effect not separated from run-to-run
  variation)*.
- If A′ did not complete, contradiction verdicts are reported with the qualifier "run-to-run floor not measured".
  Support verdicts do not need the floor.

### H1 – endpoint compliance (Q1)

Prediction: |δC| ≈ 1e-9 (k = 80 analogue +1.78e-9), with U near 1e-13. The scaling is linear: E30's accepted 1e-5
states give compliance errors of about 4e-9.
- Support: max(|δC|, 10 U) ≤ 1e-6.
- Contradiction: |δC| > 1e-4 (the optimizer's own compliance stopping resolution), resolved, and attributed.
- Inconclusive: otherwise.

Report the sign of ΔC in every case.

### H2 – retained fields (Q2)

Prediction: mean |Δρ| ≤ 1e-6. The maximum |Δρ| may reach O(1) in a few elements, because the runs stop on a
bounded oscillation in which up to 8 elements still move. Crossings are expected to be few.
- Support: mean |Δρ|(E^B, E^A) ≤ 1e-4 and crossings ≤ 819 (1e-4 × 8,192,000).
- Contradiction: mean > 1e-3 or crossings > 8,192 (1e-3 × n), attributed.
- Inconclusive: otherwise.

The maximum |Δρ| is reported in every case and never hidden behind the mean.

### H3 – course of the difference (Q3; the accumulation rule)

The decision uses the final continuation phase (β = 32, from iteration 66), where the 17 % was found.
- L1 = arithmetic mean of D_i over i = 66 … 70; L2 = arithmetic mean of D_i over i = S − 4 … S. Since S ≥ 76,
  the two windows do not overlap.
- *identical*: D_i = 0 for every i ≤ S.
- *decaying*: L2 ≤ 0.1 L1, with L1 > 0.
- *growing*: L2 ≥ 10 L1, or L1 = 0 < L2.
- *persistent*: otherwise. A difference that jumps at a continuation step and then stays within a factor of 10 is
  persistent.

The whole-window shape (phase maxima, jump ratios, the iteration of max D_i) is reported beside the class in every
case.

The words "does not accumulate" may be used for the 8.2M bridge only when H3 is *identical* or *decaying* and H2
is supported. For *persistent*, the text gives the level and the iteration of the jump ("persists at about D after
iteration j"). For *growing*, it says the difference grows over the final phase, by the factor L2/L1. H3 is
inconclusive under the attribution rule when L2(A,B) ≤ 10 L2(A,A′) and A′ is not bit-identical to A.

### Q4 (work)

Descriptive, no hypothesis. Prediction: Krylov ratio B/A between 1.2 and 1.8 (k = 80: 1.39). N_B may differ from
N_A, and both are stated.

### Overall statement for R3.4 / A.4

- With G, H1 and H2 supported and H3 identical or decaying, the paper may say: on the 8.2M bridge, tightening the
  state tolerance from 1e-5 to 1e-6 changes the retained design's tight compliance by δC and its native-FP32 field
  by mean D (maximum M, X crossings), and the difference does not accumulate.
- With any other combination, the paper reports the measured values with their class and no "no accumulation"
  wording.
- In all cases it states that the pair measures one decade of tightening, that the comparison is at the same update
  stage over iterations 1 … S only, and that the fields are native FP32 (not FP16 as in S24).

## 6. Procedure and order

1. Copy the code into `tasks/T24/src`, and write `t24_job.py`, `t24_launch.py` (a copy of T26's launcher),
   `t24_launch_selftest.py` and `t24_analyse.py`. The analysis is CPU-only: numpy reads the saved files.
2. Development, which uses no sealed data. Run the launcher self-test, which must pass. Then run the smoke jobs:
   bridge k = 16 at τ = 1e-5 and 1e-6, and k = 16 at τ = 1e-5 with the hook disabled (check C3). Run
   `t24_analyse.py` on the smoke outputs to test the analysis code. These outputs are labelled development and
   enter no endpoint.
3. Confirmatory jobs, one GPU job at a time, in this order: A (τ = 1e-5), B (τ = 1e-6), A′ (τ = 1e-5). Each job
   consists of the trajectory, the capture, the endpoint saving, the tight re-solve and the independent residual.
4. Stopping rule:
   - Each confirmatory job runs once. A failed A or B (gate G) is not repeated, apart from the operator-stop
     exception, and the fallback applies.
   - A′ runs after A and B even if one of them failed, because it still measures the floor for T34. It is skipped
     only if the 5 h budget is reached. In that case no job is started, and the report names A′ as not run.
   - No job is repeated to change a number.
5. Analysis: `t24_analyse.py` writes the outputs below, then REPORT.md. Every number in REPORT.md comes from one of
   these files.
   - `out/pair.csv`, one row per shared iteration, with the E3, E5 and E7 columns and the A′ floor columns;
   - `out/endpoints.json` (E1, E2, E4, E6, checks C1–C5);
   - `out/verdicts.json` (G, H1–H3, attribution, overall statement class);
   - `out/pair_AAprime.csv`.
6. Figure data: the series D_i, M_i, X_i, F_i and the relative c_i difference are columns of `pair.csv`. No figure is
   drawn in this task.

## 7. What is not done

There are no sensitivity audits inside the trajectories, because E30 audits may perturb the path (§2). There is no
1e-8 trajectory (T34), no other problem or mesh, and no FP16 storage. Nothing is re-analysed under another rule
after the data are seen. Any additional analysis is labelled exploratory and does not change a verdict.
