# T28 analysis plan: same-card comparison with the released OpenMP-offload multigrid code (Träff et al.)

Status: frozen when the pipeline records this file's hash. Every procedure, threshold and decision rule below
binds the run. A change after the freeze goes into `tasks/T28/DEVIATIONS.md` with its reason. Any endpoint it
affects is then reported as exploratory, not confirmatory.

Serves: R1.1 (a released external implementation compared at matched accuracy on one card).
Prerequisite: T12's gate (`tasks/T12/gate.json`: `gate_passed`, `numerical_result_admitted`,
`guard_current_passed` and `t28_cleared` all true when this plan was written). If the guard self-tests of step G0
fail, T28 runs no GPU job and R1.1 takes the T27/T29 fallback.
No language model is called by any step of this task.

---

## 1. Questions

Q1 (fixed state). Four solver paths get one free-DOF system: the released cantilever of TopOpt-in-OpenMP-GPU
(its element matrix, supports, load, modulus law and densities) at a fixed design state, with one starting iterate.
On the RTX 4090, how do the paths compare at k = 64, 128, 160, 256, 320 and 384? The comparison covers:
- setup time;
- synchronized Krylov-step time;
- native-stop convergence and solve time;
- the FP64 equilibrium accuracy reached, checked independently, and the time to a common accuracy of 10⁻⁵ where
  a path reaches it;
- memory;
- the largest completed size of each path.

The four paths:
- the released OpenMP-offload multigrid PCG;
- our FP64 PCG with the FP32 V-cycle, original stencil;
- the same, repaired stencil;
- our repaired iterative refinement.

Q2 (design workload). Can the released design update rule be reproduced in our driver? The test is one complete
step from the same inputs: the filtered fields, the updated field and the next stiffness action must agree within
tolerances fixed from the declared arithmetic. Do the following states then stay within a drift tolerance? Only
where both checks hold are design-step and design-iteration times compared as matched workloads. Otherwise the
fixed-state comparison stands alone, and the two native optimizations are reported as distinct workloads.

## 2. Data, splits and their roles

There are no statistical training/test splits. The data fall into four roles.

| Role | Content | Use |
|---|---|---|
| Development (already opened) | T12 records at 128×64×64 (k = 64): `tasks/T12/dumps_v2`–`v4`, `compare.json`, `native_iterations.csv`, `gate.json` (measured job memory, action differences, residuals, run-to-run differences); T27 exploratory single-build peaks and step times (`tasks/T27/hou_exploratory.csv`, `hou_matched.csv`); the released sources (`tasks/T12/src_TopOpt-in-OpenMP-GPU`, `src_patched`) | Priors for admission (Section 4.7), the wall-time predictions (Section 7) and the predictions of Section 5.2. They are never altered and never mixed into a T28 endpoint. |
| Verification (k = 16, 32) | New runs of every T28 driver and build on small grids | Code-correctness gates (Section 6, step V). They are never reported as results. |
| Calibration (inside the confirmatory block) | The released fixed-state runs at k = 64 and 128, and the first two measured sizes of each of our paths | Their measured peaks enter the next-size admission by the fixed rule of Section 4.7. They are also endpoints in their own right. |
| Confirmatory | Every other T28 measurement at k ∈ {64, 128, 160, 256, 320, 384} | Endpoints of Sections 4–5 |

Sealed until the plan is frozen: every T28 output. No T28 driver, build, log or result exists yet. No GPU job of
this task runs before the hash is recorded. T29's outputs are not opened by T28. The development records are
never re-read to tune a threshold after T28 outcomes have been seen.

## 3. Workloads, paths and precision labels

### 3.1 Grids and multigrid depth
- Domain: nelx = 2k, nely = nelz = k, k ∈ {64, 128, 160, 256, 320, 384}. That gives 524,288, 4,194,304, 8,192,000,
  33,554,432, 65,536,000 and 113,246,208 elements. k = 64 is the released README grid and T12's grid.
- The released code pads y to a multiple of its stencil block (128) plus a halo. Its allocated padded node counts
  are 1,141,010, 8,753,682, 13,583,442, 51,486,610, 80,167,954 and 153,365,778. The padded and the active counts
  are both recorded.
- Released multigrid depth: the smallest nl ≥ 3 for which k/2^(nl−1) is an integer ≤ 12. That gives nl = 4, 5, 5,
  6, 6, 6, with coarsest grids 16×8×8, 16×8×8, 20×10×10, 16×8×8, 20×10×10 and 24×12×12.
  - This keeps the coarsest grid within the released defaults' size class (README: 12×6×6 coarse, example 16×8×8).
  - It keeps the CPU direct solve small at every k, and it equals T12's nl = 4 at k = 64.
  - Rationale: levels ≥ 2 of the released V-cycle are assembled and run on the host. With a fixed nl = 4, the
    CHOLMOD factorization at k = 384 would cover a 96×48×48 grid (about 7×10⁵ DOFs) in every design iteration.
  - nl ≥ 3 is required: the released code assembles coarse matrices only for levels ≥ 2.
  - If nl = 6 fails verification (step V), nl is capped at 5 for k ≥ 256 (coarsest 32×16×16, 40×20×20,
    48×24×24). This is the only fallback, and it is recorded as a deviation.
- Our multigrid keeps its own native configuration: voxfem `GMG`, coarsened until its dense coarsest level holds
  at most 20,000 DOFs.

### 3.2 The common system
- Element matrix: the released level-0 matrix (`KE0`, a 10×10×10 midpoint rule on the released element), mapped
  to our local node order by the T12 permutation. Every path uses it.
- Supports: all DOFs of the x = 0 nodes with y index 0…⌊k/4⌋ and k−⌊k/4⌋…k, for all z. These are the released
  "new cantilever" strips.
- Load: z force, total −1, spread over the four nodes of every z = 0 element face whose (i, j) lies within radius
  (k+1)/5 of (2k, (k−1)/2).
  - The right-hand side of every path, residual and compliance is the released FP32 load, widened to FP64.
  - Where no released dump exists at a k, the formula rebuild rounded to FP32 is used. It is verified equal to the
    dump at every k where a dump exists.
- Modulus law: E = Emin + x³(E0 − Emin), with E0 = 1, Emin = 10⁻⁶ and x³ formed in FP32 as in the released
  `elementScale`. Our FP64 operator gets this E in FP64; our FP32 V-cycle and stencils get it in FP32.
- Free system: K_ff u_f = f_f. A returned vector has its fixed DOFs set to zero before any residual or compliance
  is formed.
- Layout maps: the T12 maps between the released padded layout (node i·wy·wz + k·wy + j, halo of one) and our
  numbering, copied verbatim from `tasks/T12/t12_compare.py`.

### 3.3 Fixed states and starting iterates
- **S1:** the released iteration-1 state, with xPhys = volfrac = 0.2 on every real element. It is generated from
  the formula at every k and checked against the released dump where one exists. Starting iterate: zero for every
  path.
- **S5:** the density the released optimizer passes to its fifth state solve, `x_it5`. It is dumped by the
  released record run R (Section 6) after four released design steps. Starting iterate: the released U of
  iteration 4, with fixed DOFs zeroed, for every path. The released code's own iteration-5 solve therefore runs
  exactly as in its native loop. At k = 64 this is the state where T12 found the released solver at its
  1000-step cap.
- S5 exists only at a k where R completed its fourth design step.

### 3.4 Paths and precision labels

| Path id | Code | Operator | Preconditioner | Krylov vectors / residual | Iterate | Native stop |
|---|---|---|---|---|---|---|
| `traeff` | released TopOpt-in-OpenMP-GPU, T12 build (cc89, libgomp shim, five `nowait` clauses removed), nvc 26.11 | 27-point stencil, FP32 input and output, FP64 element-matrix arithmetic | released V-cycle: damped Jacobi (ω = 0.6, 4 sweeps), levels 0–1 matrix-free on the GPU, levels ≥ 2 assembled on the host, coarsest level CHOLMOD on the host | FP32 r, p, q, z and FP32 scalars; recursive FP32 residual | FP64 | ‖r‖/‖b‖ < 10⁻⁵ (FP32, recursive) or 1000 steps (released `maxIter`) |
| `mg64_orig` | voxfem `pcg64` | FP64 `node_hoist` | FP32 Galerkin V-cycle, fine level `stencil` | FP64 | FP64 | FP64 true ‖b−Ku‖/‖b‖ ≤ 10⁻⁵, maxit 5000 |
| `mg64_rep` | as above | as above | fine level `stencil_diff` | FP64 | FP64 | as above |
| `mgir_rep` | voxfem `ir_lean` (inner tolerance 0.1, inner maxit 300, outer ≤ 60) | inner FP32 PCG with `stencil_diff` | V-cycle with fine level `stencil_diff` | outer FP64-arithmetic residual | FP64 | outer ≤ 10⁻⁵ |

The released step count is its printed `cgiter` + 1 (zero-based loop index).

## 4. Endpoints and definitions

### 4.1 System identity (gate G2, at each k)
- The mapped fixed-DOF set is identical to the formula rebuild.
- The mapped load equals the FP32-rounded rebuild entry by entry.
- `KE0` is bitwise equal to the k = 64 dump.
- The S1 dump equals volfrac on the real elements.
- Action agreement: d = ‖y_rel − y_ref‖₂/‖y_ref‖₂ over free DOFs. Here y_rel is the released GPU action
  `applyStateOperator_stencil` and y_ref is the FP64 checker operator (Section 4.4). The action is taken on the
  dumped test vector (uniform(−1, 1) on free DOFs) at S1 and S5, and on the released U at S5.
- Required: d ≤ 10⁻⁵. T12 measured ≤ 3.67×10⁻⁸ at k = 64.

### 4.2 Time
- **Released setup:**
  - (a) process setup: from program start through `enter_data`, which covers the grid context, element matrices,
    allocation, CHOLMOD initialization and device mapping;
  - (b) per-solve setup: from entry of `solveStateMG_halo` to the start of its CG loop, which covers coarse
    assembly, inverse diagonals and the factorization.
  - Both are wall-clock intervals (`omp_get_wtime`). Every released target region is synchronous in the T12
    build, so the boundaries are synchronized.
- **Our setup:**
  - (a) the first build, including compilation: load and mask, operators, `GMG(...)` and the first `mg.update(E)`;
  - (b) a second identical build in the same process, timed between device synchronizations, after the first
    hierarchy has been freed.
- **Krylov-step time:**
  - Released: the interval between consecutive iteration ends. A timer mark is taken after each iteration's
    `taskwait`, which follows a host reduction and is therefore a synchronization point. This is the only change
    of the released timing build.
  - Ours: CUDA events recorded once per iteration through a wrapper around the preconditioner that only records
    an event (T27 protocol). For `mgir_rep` this gives the inner FP32 PCG step; its outer FP64 residual
    evaluation is reported separately as a mean per outer step.
  - Reported as the median and IQR over all steps of the timed solve.
- **Solve time:**
  - Released: from entry of `solveStateMG_halo` to its return, including the per-solve setup.
  - Ours: setup (b) plus the solver call, between device synchronizations.
  - Repeats:
    - ours: median of 3 solves from the stated start, with the hierarchy fixed;
    - released: median of 3 solves in one process when the first takes ≤ 120 s, otherwise that one solve. Each
      repeat restarts from the stated iterate.
- **Design-step time:**
  - Released: the interval from the return of the state solve to the end of `target update to(xPhys)`. That
    covers compliance and sensitivity, the volume, the sensitivity filter, the OC update, the change and the
    density filter with its transfers.
  - Ours: the same operations, between device synchronizations.
  - Design-iteration time is the solve plus the design step.
- **Native versus instrumented.** Native performance comes from the timing build, which adds no other work. The
  record run's per-iteration intervals count as native only if gate G6 passes. Every true-residual history comes
  from separate, untimed processes (Section 4.3), and no time is read from them.

### 4.3 Accuracy and convergence
- Native stop: the step count, the stop reason (tolerance or cap) and the in-solver residual at the stop.
- Independent FP64 equilibrium accuracy: ‖f_f − K_ff u_f‖₂/‖f_f‖₂, from a separate checker process (Section 4.4).
- **Released continuation (H runs).** A continuation build of the released solver:
  - its stopping test is disabled, and the first iteration at which it holds is recorded;
  - it runs to the released cap of 1000 steps;
  - it writes FP64 iterate snapshots of the real-node DOFs at C = {0, 1, …, 16, 24, 32, 48, 64, 96, 128, 192, 256,
    384, 512, 640, 768, 896, 1000} ∪ {the native-stop iterate};
  - its arithmetic is otherwise identical to the timing build (G1).
- **Common accuracy (10⁻⁵):**
  - Released: attained at the first snapshot in C whose independent residual is ≤ 10⁻⁵. That gives an upper
    bound on the iterations, at the resolution of C. Time to 10⁻⁵ = released per-solve setup + (that iteration)
    × the median Krylov-step time of the timed native solve of the same (k, state).
  - Without a passing snapshot the result is "not attained", reported with the smallest residual reached and its
    iteration.
  - Ours: attained when the independent residual of the native-stop iterate is ≤ 10⁻⁵. The time to 10⁻⁵ is then
    the solve time.
- **Our histories (H runs, untimed):**
  - the FP64 true residual at every Krylov step (`mg64_*`) or every outer step (`mgir_rep`, with inner counts);
  - recorded through a read-only wrapper with a separate buffer, which leaves the iteration unchanged (T27).
- **Compliance:** F·u in FP64 at every native-stop iterate. The difference between paths is reported
  descriptively; there is no reference solve and no threshold.

### 4.4 Independent checker
- A CuPy process rebuilds the system from the formulas and the released `KE0`. It applies the FP64 `node`
  operator mapping, which differs from the `node_hoist` mapping our solvers use.
- It evaluates every returned iterate, every released snapshot and the actions of Section 4.1. Released FP64
  vectors are read from the padded layout through the T12 maps.
- Its validity is gate G3.

### 4.5 Memory
- **M1, job dedicated peak** (the comparison measure):
  - released (WSL): the peak growth of the WSL VM worker's dedicated GPU memory over its pre-launch baseline, as
    sampled by `t12mon.py` revision 4.3;
  - ours: the process's dedicated peak, sampled by `cupy_guard` revision 4.3. The process is absent at the
    baseline.
  - Both include the job's CUDA context.
- **M2, device-wide peak:** the device-wide peak minus the device baseline (nvidia-smi), for both. It includes
  other processes' fluctuation, and is reported beside M1.
- **M3, pool peaks** (ours only): CuPy pool used and reserved, read by a `MemoryHook` during the memory solve.
- **M4, host peak** (released only): `VmHWM` read by the driver from `/proc/self/status` at exit.
- **Which solve the peaks cover:**
  - Ours: each M value comes from the single build and single solve of the memory pass (Section 6, step T). It is
    read before any second build. A peak from a process that held a second hierarchy, or that ran another path,
    never counts.
  - Released: M1 and M4 come from the fixed-state timing run, which makes one build.
- **Spill:** shared usage more than 256 MiB above its value at the start, in any checked sample, stops the job at
  once. The run is refused for memory. Under the authors' rule it is never kept and never rerun at the same size.

### 4.6 Design-step check and drift (Q2)
- **Matched update rule.** Our matched-rule driver implements the released design step operation by operation:
  - sensitivity dc_e = −3(E0−Emin)·x_e²·u_eᵀKE u_e, and compliance Σ(Emin + x_e³(E0−Emin))·u_eᵀKE u_e;
  - the sensitivity filter v ← H(v/H_s) and the density filter xPhys = H x/H_s, with weights max(0, r_min − dist),
    r_min = 1.5, and the released in-domain neighbourhood bounds;
  - dv = H(1/H_s), formed once;
  - OC by bisection with l1 = 0, l2 = 10⁹, move 0.2 and relative bracket 10⁻⁶, with bounds [0, 1];
  - change = max|x_new − x|;
  - the loop stops at change ≤ 10⁻² or at the iteration count of the released run;
  - warm start from the previous state's solution, as the released loop does;
  - volfrac 0.2.
- **Declared arithmetic:**
  - released: FP32 design arrays and an FP32 OC bisection with an FP32 volume reduction; element energies in
    FP64 accumulated into FP32 (8 roundings); filters accumulated in FP64 over FP32 inputs and stored in FP32;
  - ours: FP64 throughout, with x and xPhys stored in FP32 between steps.
- **Step check** at N = 1, at every k with an R run. Inputs from the released dumps: x₁, xPhys₁ and U₁. Our step is
  computed from them and compared with the released outputs. Let u = 2⁻²⁴, the FP32 unit roundoff. The
  tolerances are fixed now:

  | Field | Measure | Tolerance | Basis |
  |---|---|---|---|
  | dv (filtered) | ‖Δ‖₂/‖ref‖₂ and max\|Δ\|/max\|ref\| | 10⁻⁶ | positive-weight filter, FP64 sums, one FP32 rounding of the quotient and one of the result (≈ 2u, with a 8× allowance) |
  | raw dc | both measures | 10⁻⁵ | 8 FP32 accumulations (γ₈ ≈ 4.8×10⁻⁷) with a cancellation allowance of 20 |
  | filtered dc | both measures | 10⁻⁵ | positive weights do not amplify the raw error; plus 2u |
  | x₂ (updated field) | max\|Δ\| over elements; dv-weighted mean \|Δ\| / mean x | 10⁻⁴; 10⁻⁵ | the dc error gives ≤ x·10⁻⁵/2 ≤ 5×10⁻⁶; the bisection bracket gives ≤ 5×10⁻⁷; the FP32 volume reduction (≈ 27u relative over 10⁸ terms) can move the root where few elements are unclamped, which bounds the weighted mean but not the maximum, hence a looser maximum |
  | change₁ | \|Δ\| | 10⁻⁴ | as x₂ |
  | xPhys₂ (filtered field) | as x₂ | 10⁻⁴; 10⁻⁵ | positive-weight filter of x₂ |
  | next stiffness action | ‖K(xPhys₂ᵒᵘʳ)v − K_rel(xPhys₂ʳᵉˡ)v‖/‖K_rel v‖ on free DOFs, v the dumped test vector | 10⁻³ | operator agreement ≤ 10⁻⁵ (G2) plus ΔE/E = 3Δx/x, with Δx ≤ 10⁻⁴ on stiff elements of density ≥ 0.3 |

  The same comparisons at N = 2, 3, 4 (again from released inputs) are reported descriptively and decide nothing.
- **Drift check.** For each of our paths p, the matched-rule loop runs from S1 with its own solver and gives
  states 2…5 (and up to 20 at k = 64). These are compared with the released record run's states:
  - D_N = max|xPhys_N^p − xPhys_N^rel| over real elements;
  - C_N = |c_N^p − c_N^rel|/c_N^rel, with both compliances in FP64 (F·U);
  - the released self-difference S_N and S^c_N between the record run R and its replicate R′ (Section 6), at
    the same k.

  State N is matched when three conditions hold:
  - D_N ≤ max(10⁻³, 10·S_N);
  - C_N ≤ max(10⁻⁴, 10·S^c_N);
  - every released solve that led to it (iterations 1…N−1) met its native stop.

  A design iteration N is a matched workload when states N and N+1 are both matched; state 1 is matched by
  construction. The basis for 10⁻³: the released stop leaves FP64 true residuals of 2.3–5.4×10⁻⁴ (T12), so
  per-step density differences of order 10⁻⁴ are expected from solve accuracy alone. The factor 10 on the
  released self-difference accepts differences up to one order above the released code's own run-to-run
  variation.
- **Matched claims at k** require that the step check passes at k and that the iterations compared are matched
  workloads. Design-step and design-iteration times are then compared over those iterations only. Otherwise the
  released loop and our loops are reported as distinct workloads, with their own per-iteration records and no
  ratio.

### 4.7 Admission (authors' GPU-memory rule of 2026-11-23)
- A job is admitted when its predicted peak plus 1.5 GiB fits in the free memory the CUDA driver reports at its
  start:
  - our processes: `cudaMemGetInfo` inside the watched process (`cupy_guard`);
  - WSL jobs: `memfree` inside WSL under the armed watch (`t12mon.py`).
- Other applications' dedicated memory is not counted. `guard.require_budget`'s answer and the other processes'
  usage are recorded beside each admission, for information.
- **Released prediction:**
  - Notation: A(k) is the source inventory of device arrays: 128.5 B per padded node, 24 B per padded element, and
    the mapped element matrices Σ_l 576·8^l·8 B.
  - k = 64: 1.10 × 1,713,545,216 B (T12's measured growth).
  - k = 128: 1.10 × the k = 64 growth × the padded-node ratio (7.67). This is conservative, because it treats all
    growth as proportional.
  - From k = 160 on: 1.10 × (a + b·N_pad(k) + KE(nl(k))). Here a and b are fitted through the two largest
    measured T28 released sizes below k, after their KE bytes are subtracted.
- **Our prediction:**
  - From the two largest measured T28 sizes of the same path below k: 1.10 × (a + b·n_elem(k)), fitted on M1.
  - Before two exist, the T27 single-build fit at k = 160 and 256 is used:
    - `mg64_*`: 0.487 GB + 195.6 B/element;
    - `mgir_rep`: 0.476 GB + 135.3 B/element;
    - in both cases × 1.10.
  - H runs of `mg64_*` add 8 B/DOF for the history buffer.
- **Host memory (WSL jobs):**
  - Admitted when the predicted VmHWM × 1.25 + 4 GiB ≤ `MemAvailable` inside WSL.
  - The predicted VmHWM is a linear fit on N_pad through the two largest measured sizes. At k = 64 there is no
    prior, and the check is MemAvailable ≥ 8 GiB.
- **Pool cap:** every CuPy process caps its default pool with `set_limit` at the driver's free memory at its start
  minus 1.5 GiB.
- **Refusal:** a refused job allocates nothing. It records the prediction, the free memory and the other usage,
  and is class 2. The next smaller size is not tried again for the same run type: the ladder has already passed
  it.

### 4.8 Outcome classes (mutually exclusive; the first that applies)
1. Not run: the budget or the date was reached, a prerequisite failed (for example S5 missing), or the wall
   prediction exceeded the cap (Section 7).
2. Guard refusal: GPU or host admission (Section 4.7).
3. Allocation failure: a CuPy `OutOfMemoryError` under the cap; a released exit with an out-of-memory message
   (`t12guard.job_status`); or a WSL out-of-memory kill.
4. Spill: stopped by the spill sampler. The run is invalid, and no number from it is kept.
5. Numerical breakdown: `SolveFailed`, a non-finite residual, or a rejected IR correction at the inner floor.
6. Wall cap.
7. Iteration cap: the solve stopped at its cap without meeting its native stop. This applies to the released
   1000 steps and to our maxit.
8. Native stop met, but the independent residual of the returned iterate is > 10⁻⁵, or missing.
9. Verified: native stop met, independent residual ≤ 10⁻⁵, no spill, and coverage held.

A job is invalid, and none of its outputs count, unless three things hold:
- its status is `completed`;
- its coverage is `covered`;
- for WSL jobs, `t12mon.validate` gives clean = true with carrier_is_watched = true.

A stop recorded with `linux_process_ended_confirmed = false` ends all T28 GPU work until the survivor has been
accounted for (T12's note for T28).

### 4.9 Capacity bounds (`capacity.json`)
Per path and workload:
- Workloads: the fixed-state solve at S1, the fixed-state solve at S5, and (released) the record run's design
  loop.
- Three lower bounds:
  - run completed: the largest k in classes 7–9;
  - native stop met: the largest k in classes 8–9;
  - verified: the largest k in class 9.
- Each bound has the next tested k above it and that k's class. Active and allocated element counts are given
  for both codes.

Admission refusals are labelled as predictions, never as measured limits. The paper-wide maximum (113,246,208
elements, T27) is not changed by T28, which runs no complete optimization of the authors' problem.

## 5. Gates, predictions and decision rules

### 5.1 Gates (a failed gate makes the affected endpoints inconclusive, and the report says so)
- **G0, guards:**
  - re-run `tasks/T12/test_t12guard_v4.py` (51 cases, no GPU) and `tasks/T12/test_t12kill_v4_3.py` (real WSL, no
    GPU);
  - if either fails, T28 stops before any GPU job and records the blocking reason; R1.1 takes the T27/T29
    fallback;
  - all WSL jobs run through `t12mon.py` revision 4.3 and all CuPy processes through `t12guard.cupy_guard`
    revision 4.3, closed with `close_watch(stream, stop, t_end)` before `stream.stop()`. Both take
    `gpu_job.lock`. They are used in place and unchanged.
- **G1, code identity:**
  - The released library sources are T12's `src_patched`, file for file. They differ from the released tree only
    by `patch_nowait.diff`.
  - The T28 timing build adds only timer marks. The continuation build adds only the disabled stop test with
    its first-hold record and the snapshot writes.
  - The T28 harness differs from `tasks/T12/harness/t12_harness.c` only by added dumps, the timing read-out and
    the VmHWM read. The fixed-state driver repeats `top3dmgcg`'s setup statement for statement.
  - Each diff is saved.
  - The copied voxfem files are byte-identical to `tasks/T27/src/voxfem`.
  - At k = 32, the timing and continuation builds must give the plain build's step count and the iterate at the
    native stop within 10⁻⁶ relative. A bitwise test is not possible, because the released first solve is not
    bitwise reproducible (T12).
- **G2, system identity:** Section 4.1, at each k where released dumps exist. A failure makes every endpoint at
  that k that involves the released path inconclusive.
- **G3, checker validity:** at k = 64 and on states S1 and S5:
  - the checker's residual agrees with an independent CPU FP64 element loop (the T12 `cpu_apply`) to within 1% of
    its value;
  - on a `mg64_rep` state it agrees with the in-solver true residual to within 1%.
- **G4, timing validity:**
  - The mean foreign 3D-engine use (all processes other than the job and its carrier) is sampled every ≤ 10 s
    over each timed section.
    - A mean above 5% excludes that section's times, and the run is repeated once.
    - A mean of 1–5% is flagged.
  - The SM clock is sampled with the device-wide sampler. A timed section of ≥ 1 s whose median SM clock is below
    1500 MHz is flagged "low clock" and repeated once; if the repeat is also low, the repeat is reported flagged.
  - Memory and accuracy endpoints are kept in all cases.
- **G5, timing-build overhead:** at k = 64, S1, the timing build's solve time is compared with the plain build's
  (harness marks around `solveStateMG_halo`). They must agree within 3%. Otherwise every released step time is
  flagged.
- **G6, dumps outside the intervals:** at k = 64, the record run R (timing build with dumps) is compared with a
  native run N (plain build, no dumps, 5 iterations) on the median solve and design-step intervals of iterations
  1–4.
  - Within ±10%: R's intervals are released native loop times at every k.
  - Otherwise: an N run supplies the native loop times at every k, and R's are labelled instrumented.

### 5.2 Confirmatory predictions and what counts as support, contradiction or inconclusive
"With data" means a valid measurement with its gates passed. Each decision uses every (k, state) with data; the
(k, state) pairs without data are listed. No subset is chosen after the fact.

| id | Endpoint | Prediction (development basis) | Support | Contradiction | Inconclusive |
|---|---|---|---|---|---|
| P1 | Independent residual of the released iterate at its native stop | > 10⁻⁵ wherever the stop is met (T12: 2.3–5.4×10⁻⁴ at k = 64, iterations 1–4) | > 10⁻⁵ at every (k, state) where the stop is met | ≤ 10⁻⁵ at any | the stop is met nowhere with an independent check |
| P2 | Released common accuracy within its 1000 steps (H runs) | not attained anywhere (FP32 recursive residual and FP32 Krylov vectors) | not attained at every (k, state) with a completed continuation | attained at any (the time to 10⁻⁵ and its ratio are then computed there) | no continuation completes |
| P3 | Released S5 solve at k = 64 (warm start U₄) | reaches the 1000-step cap without its native stop, class 7 (T12: all three runs) | class 7 | stop met | not run or invalid |
| P4a | Krylov-step time ratio, `traeff` / `mg64_rep`, at S1 | > 1 at every k with both (T12: 92–99 ms per step at k = 64; T27: 4.9 ms at k = 80) | > 1 at every k | < 1 at any k with non-overlapping IQRs | G4 or G5 fails at every k |
| P4b | Krylov-step time ratio, `traeff` / `mgir_rep` inner step, at S1 | > 1 at every k with both | as P4a | as P4a | as P4a |
| P5 | Native-stop solve-time ratio, `traeff` / `mg64_rep`, at S1 and S5 | > 1 at every (k, state) with both | > 1 at every one | < 1 at any with non-overlapping IQRs | otherwise |
| P6 | M1: `traeff` against each of our three paths | `traeff` higher at every k with both (T12: 1.71 GB at k = 64; T27: 0.58–0.64 GB at k = 80) | higher at every k for all three | lower at any k for any path | no released M1 |
| P7 | Our three paths verified (class 9) | at every admitted (k, state) | all class 9 | any class 5, 7 or 8 | none admitted |
| P8 | Step check at N = 1 (Section 4.6) | passes at every k with an R run (the same formulas; arithmetic bounded as tabulated) | passes at every such k | fails at any | no R run |
| P9 | Drift at k = 64: are states 2–5 matched for every one of our paths? | not matched at some state ≤ 5 (T12: a 3.7×10⁻⁸ difference in U₁ grew to 4.5–5.3×10⁻⁵ in xPhys₅ between released runs, an amplification of about 10³; the released–ours difference in U is of the order of the released true residual) | some state ≤ 5 is unmatched for some path | states 2–5 matched for all three paths | R, R′ or a loop missing at k = 64 |
| P10 | Fixed-state capacity at S1, run completed | `traeff`: admitted through k = 320, refused at k = 384 (inventory about 25 GB with T12's fixed part); `mg64_*`: refused at k = 384 (T27 fit 22.6 GB); `mgir_rep`: completes at k = 384 (T27 fit 15.8 GB) | each path's bound and next class as predicted | any path differs by at least one ladder step | the ladder is not reached (class 1) |
| P11 | Repair cost per Krylov step, `mg64_rep` / `mg64_orig`, at S1 | ≤ 1.15 at every k (T27: 4.92/4.94 ms at k = 80, 89.7/89.3 ms at k = 256) | ≤ 1.15 at every k | > 1.15 at any k with non-overlapping IQRs | the 1.15 boundary lies within the IQR interval at the deciding k |

Rules applied to every endpoint:
- Ratios are point values of medians, given with the IQRs of their components. There is no pooling across k or
  states.
- Every ratio between the released path and ours is stated with both accuracies reached (native and independent).
- An elapsed-time ratio is called a speed-up at equal accuracy only where both paths attained 10⁻⁵.
- Contradictions are reported as fully as supports. A contradiction of a statement in the submitted manuscript is
  flagged for the authors' wording decision, never removed.

## 6. Procedure (exact order; one GPU job at a time)

Environment and isolation:
- CuPy work: `<user-home>/anaconda3/python.exe` (Python 3.11.5, CuPy 13.4.1), with `PYTHONDONTWRITEBYTECODE=1`
  and `CUPY_CACHE_DIR=tasks/T28/_cupy_cache`.
- WSL work: Ubuntu-24.04 with the NVIDIA HPC SDK 26.11 and `tasks/T12/env_run.sh` (libgomp shim,
  `OMP_NUM_THREADS=12`, `OMP_TARGET_OFFLOAD=MANDATORY`).
- Copies:
  - voxfem and the T27 protocol helpers (step-event wrapper, history wrapper, `node` checker) go to
    `tasks/T28/src/`;
  - the released library (T12 `src_patched`), the T28 timing and continuation edits, the T28 harness and the
    fixed-state driver go to `tasks/T28/released/`, built into `tasks/T28/build/`;
  - outputs go to `tasks/T28/out/`, and vectors and snapshots to `tasks/T28/scratch/`.
- A snapshot set is deleted from scratch after the checker has written its record.
- Nothing is written to the authors' folder.
- Device↔host transfers of whole vectors are chunked to ≤ 256 MiB.

**G0**, then **V (verification, not endpoints):**
- k = 16 and 32: every build, the harness, the fixed-state driver at S1 and S5, our paths, the checker, the step
  check and the matched-rule loop.
- nl = 6 is exercised at k = 64 (coarsest 4×2×2), in a verification process.
- G1's behavioural checks, then G3.
- A driver that fails is fixed, the check is rerun, and the fix is logged. No confirmatory job starts before V
  passes.

**Per k, in ascending order; within each k in this order:**
1. **R, the released record run** (WSL, timing build plus dumps outside every timed interval):
   - k = 64: 20 design iterations, the released benchmark length;
   - k ≥ 128: 4 design iterations, which give states 1–5 without the fifth solve;
   - dumps: F, fixed DOFs, `KE0`, dv, the test vector v; xPhys at states 1–5 (1–20 at k = 64); x and U at states
     1–4; raw and filtered dc, x_new, the change and the FP32 compliance at steps 1–4; K v at states 1–5; K U at
     states 1 and 5;
   - VmHWM at exit.
2. **R′, the released replicate:** the same binary for 4 design iterations, with xPhys dumps at states 1–5 only.
   It gives S_N.
3. **N, the native run** (k = 64 only, for G5 and G6): plain build, no dumps, 5 iterations.
4. **Checker K1:** G2 at this k, using R's dumps.
5. **F-S1** (WSL, timing build, fixed-state driver): S1 from zero, with repeats as in Section 4.2. Gives M1, M4, the
   setups, the step times and the native stop.
6. **T-S1 for each of our paths**, one process each, in the order `mg64_orig`, `mg64_rep`, `mgir_rep`:
   - build (setup a);
   - one memory solve with the pool hook on (M1–M3);
   - free the hierarchy;
   - second build (setup b);
   - three timed solves with the hook off and per-step events.
7. **H-S1, released continuation**, subject to the wall prediction (Section 7).
8. **H-S1 for our paths:** history solves, untimed.
9. **F-S5, T-S5, H-S5:** as steps 5–8, at S5 with the released U₄ as start (only where R completed four steps).
10. **Step check** (guarded CuPy, FP64): N = 1 (decisive) and N = 2–4 (descriptive).
11. **L, the matched-rule loop for each of our paths:** the released iteration count of R, with timed solve and
    step intervals and state dumps outside them.
12. **Checker K2:** independent residuals of every returned iterate and snapshot of this k, and the drift
    measures. Our timed solves' first iterate is saved for this.

A path stops ascending as Section 7 states. Later steps at a k run even if an earlier released step failed,
wherever their inputs exist.

**Outputs (after all runs; no GPU):**
- `tasks/T28/comparison.csv`: one row per (k, state, path, workload). Columns:
  - k, active and allocated elements, free DOFs, state, start, path, nl or our levels;
  - operator, residual and iterate precision, native stop rule;
  - class, steps, stop reason, in-solver residual, independent residual;
  - attained-10⁻⁵ flag, iterations and time to 10⁻⁵, smallest residual and its iteration;
  - setup (a) and (b), solve median and IQR, Krylov-step median and IQR, outer-residual mean (IR);
  - compliance;
  - M1–M4, spill growth, admission inputs (prediction, driver free, `require_budget` answer, other usage), pool
    cap;
  - G4 activity and clock flags, valid flag, source file.
- `tasks/T28/update_checks.json`: per k, the step-check measures against their tolerances (N = 1 decisive, N = 2–4
  descriptive); the drift measures D_N, C_N, S_N and S^c_N with matched flags; the matched iterations; and the
  resulting claim status per k ("matched" or "distinct workloads").
- `tasks/T28/design_workload.csv`: per k, code and iteration: solve and design-step times, steps, in-solver
  residual, change, compliance and matched flag.
- `tasks/T28/residual_histories/{k}_{state}_{path}.csv`: iteration, inner iterations where applicable, independent
  FP64 residual, in-solver or recursive residual where available.
- `tasks/T28/capacity.json`: Section 4.9.
- `tasks/T28/REPORT.md`: every endpoint with its source file, the gates, the outcome of each prediction and the
  deviations. Every number comes from a file under `tasks/T28/`.

No figure is drawn by this task (`figure_files` is empty). The CSV and JSON hold the data a figure needs.

## 7. Stopping rules

- **Wall caps per process:**
  - 90 min for a released WSL job;
  - 30 min for one of our solver or loop processes;
  - 30 min for a checker;
  - 20 min for verification.

  A cap ends the job with class 6.
- **Wall prediction for released jobs.** Before R (k ≥ 128), R′, F-S5 and every H run, the wall time is predicted
  from measured inputs at the same k:
  - R and R′: four times the F-S1 solve plus four design-step intervals at the next smaller k scaled by the
    padded-node ratio;
  - F-S5: per-solve setup + 1000 × the F-S1 median step time;
  - H: the same plus snapshot writing at 1 GB/s.

  A job whose prediction exceeds its cap is class 1 ("predicted wall cap") and is not launched.
- **Disk.** Before an H run, the predicted snapshot bytes must be ≤ free disk − 50 GB. Otherwise the snapshot set
  is reduced to the powers of two in C plus 1000 and the native-stop iterate, and this is recorded.
- **Ladder.** A path stops ascending for a workload at its first class 2, 3 or 4 at that workload. Released S5
  workloads stop with R. A class 6 or a class 1 by wall prediction stops that released run type from ascending.
- **Repeats:**
  - a valid measurement is never repeated to obtain a different number;
  - an invalid run may be repeated once: coverage lost without a spill, foreign activity above 5%, a low clock
    (G4), or a start refused because another process held the GPU. Both records are kept, and only the valid one
    is reported;
  - a spill is never rerun at the same size;
  - classes 3, 5 and 7 are results and are not repeated.
- **Budget:** about 14 GPU hours, in the priority order of Section 6 by ascending k. Within a k, steps 1–8 come
  before 9–12. Any item not started by the end of December 10, 2026 is class 1. The numerical freeze is
  December 11.
- **Early termination:** only a failed G0 or G1, or an unconfirmed WSL stop whose survivor cannot be accounted
  for, ends T28's GPU work. The report then states what was measured before.

## 8. Reporting rules

- Every reported number is read from a file in `tasks/T28/` and cited with it. Development values are cited with
  their T12 or T27 file and labelled as development. They never enter a T28 ratio.
- Spilled and invalid measurements are excluded from every table and ratio, and their class is listed.
- Every row states the precision of the operator, residual and iterate, the native stop, the timing boundary and
  the memory definition (Sections 3.4, 4.2 and 4.5).
- **Common accuracy:**
  - Where the released path does not reach 10⁻⁵, the report says "common accuracy not attained by the released
    code". It gives the smallest residual reached and makes no equal-accuracy time ratio.
  - Native-stop ratios are labelled as ratios at unequal accuracy, with both accuracies.
- **Design-step and design-iteration comparisons** are reported as matched only for the iterations and k that
  Section 4.6 admits. Otherwise the report gives each code's native loop as its own workload, without a ratio. A
  failed match never removes a valid fixed-state result.
- Released findings carried from T12 (the build adaptations, the iteration-5 cap and run-to-run
  non-reproducibility) are restated as findings about the released code under nvc 26.11 on this card. They are
  not presented as properties of its published A100 configuration, which stays attributed separately.
- Paths and sizes that were not run, were refused or did not attain a criterion are reported with their class,
  never left blank.
