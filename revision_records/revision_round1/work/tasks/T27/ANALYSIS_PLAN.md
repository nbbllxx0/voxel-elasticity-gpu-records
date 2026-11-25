# T27 analysis plan: matched comparison with the released Hou et al. code and single-card capacity

Status: frozen when the pipeline records this file's hash. Every procedure, threshold and decision rule below
binds the run. A change after the freeze is recorded in `tasks/T27/DEVIATIONS.md` with its reason. Any endpoint
it affects is then reported as exploratory, not confirmatory.

Serves: R1.1 (matched external comparison), R1.2 (cost of the repair on a common system), R1.4 (scale
premise and the paper-wide maximum) and A.3 (released records that a reviewer can recompute).
No language model is called by any step of this task.

---

## 1. Questions

Q1 (R1.1, common system). The three solver paths are given the same system: Hou et al.'s element matrix,
supports, load, DOF indexing and zero starting state on their solid 2k×k×k domain. The paths are the released
code of Hou et al. (CuPy-for-TO, upstream commit d8dca7a), our original-stencil path and our repaired
(difference-form) path. On one RTX 4090, the questions are:
- how do these paths compare in operator-application time, setup time and synchronized Krylov-step time;
- how do they compare in convergence, both at their native stopping rule and at an independently verified
  FP64 equilibrium accuracy of 10⁻⁵;
- how do they compare in memory under three separately defined peaks (pool, process-dedicated, device-wide)?

Q2 (R1.2). On that common system, what does the repaired FP32 operator cost relative to the original one, per
application and per complete state solve? Two solvers are tested: FP64 PCG with the FP32 V-cycle (mg64) and
iterative refinement (mg_ir).

Q3 (R1.4, A.3). On the authors' cantilever, what is the largest complete, verified optimization each solver
configuration achieves on the 24 GB card? What is the next tested outcome above it? Does any configuration
complete a verified optimization larger than the present paper-wide maximum of 113,246,208 elements?
The configurations are:
- FP64 iterative refinement with FP32 corrections (mg_ir);
- FP64 PCG (mg64);
- the recursive-stop control, which runs FP32 Krylov with an FP64 iterate (mg32_rec).

## 2. Data, splits and their roles

There are no statistical training/test splits. The data fall into four roles.

| Role | Content | Use |
|---|---|---|
| Development (historical, already opened) | Records in the project folder: `results/E10/hou_k{16..256}.json`; `results/E7/memory_k{160,320,384}_{mg64,mg_ir}.json` and `simp_cantilever_k384_mg_ir_stencil.json`; `results/E12/simp_cantilever_k384_mg64_stencil.json` and `simp_cantilever_k320_mg32_rec_stencil.json`; `results/E12b/simp_cantilever_k384_mg64_stencil_poollimit.json`; `results/E14/simp_cantilever_k320_mg32_rec_stencil_diff.json`; `results/E23/simp_cantilever_k384_mg64_stencil_asyncpool.json`; `results/E32/simp_cantilever_k{320,384}_*_stencil_diff*.json`; the claims ledger `evidence/NUMBERS.md` | Feasibility, run-time and memory priors, and the predictions stated in Section 5. Historical entries in `capacity.json` are quoted from these records with their source, and are never re-derived or altered. |
| Verification (k = 16, 32) | New runs of the task drivers on small grids | Gate on code correctness only (Section 6, step V). They are not endpoints and are never reported as results. |
| Calibration (within the confirmatory block) | The T27 anchor runs mg_ir k=384 and mg64 k=320 (Section 6, C1/C3), plus the Hou k=160 solve | Their measured peaks enter the next-size admission formula (Section 4.6) by a fixed rule. They are also endpoints in their own right. |
| Confirmatory | Every other new T27 measurement: the Hou-system blocks at k = 80, 160, 256 and the capacity ladder | Endpoints of Sections 3–4 |

Sealed until the plan is frozen: every T27 output. No GPU job of this task runs before the freeze. No T27
driver, script, log or result exists yet, and none will be written before the hash is recorded. These files are
not opened and not used, now or later:
- `results/_superseded/E10_capacity/hou_k320.json`, a superseded spill record;
- the outputs of T29, T31 and T35.

The historical development records stay as they are. They are never read to tune a threshold after T27 outcomes
are seen.

## 3. Workloads, paths and precision labels

### 3.1 Hou system (Q1, Q2)
- Domain: solid 2k×k×k, nelx = 2k, nely = nelz = k, k ∈ {80, 160, 256}. These have 1,024,000, 8,192,000 and
  33,554,432 elements.
- Element matrix: Hou's `materialInfo(1, 0.3)`, cast to FP64. It is used unchanged by every path, including
  their λ = Eν/((1+ν)(1−ν)).
- Supports and load: the same as in their `FE.py`. There are 12 fixed DOFs, and the load is a unit z load on
  the end patch with r = 1. Their DOF order (x fastest) is mapped to ours (z fastest) by the E10 mapping
  functions `to_ours` and `dof_to_ours`, copied verbatim.
- Starting state: a zero iterate for every solve. All densities are 1 (struct = ones), so the moduli are E = 1 in
  FP32.

| Path id | Code | Operator / preconditioner | Residual used to stop | Iterate | Native stop |
|---|---|---|---|---|---|
| `hou_cg32` | released CuPy-for-TO, `FE.FE` → `CG.CG`, unpreconditioned | 24 generated element-row kernels (`SpMV.honorAb`), FP32 | recursive FP32 residual | FP32 | ‖r_k‖ < 10⁻³‖r_0‖ or 10,000 iterations (their values) |
| `mg64_orig` | voxfem `pcg64` | FP64 operator (`node_hoist`, FP32 moduli); FP32 Galerkin V-cycle with fine level `stencil` | FP64 true residual | FP64 | true ‖b−Ku‖/‖b‖ ≤ 10⁻⁵ |
| `mg64_rep` | as above | fine level of the V-cycle `stencil_diff` | FP64 true residual | FP64 | as above |
| `mgir_orig` | voxfem `ir_lean` (inner tol 0.1, inner maxit 300, outer ≤ 60) | inner FP32 PCG with operator `stencil` and the V-cycle with fine level `stencil` | outer FP64-arithmetic residual (fused kernel) | FP64 | outer ≤ 10⁻⁵ |
| `mgir_rep` | as above | `stencil_diff` in both places | as above | FP64 | as above |

Application-only rows add `stencil32_orig`, `stencil32_rep` (FP32 27-point stencil, original or difference
form) and `hoist64_ref` (the FP64 `node_hoist` operator, the reference action).

### 3.2 Authors' cantilever optimization (Q3)
The problem is `voxfem.core.cantilever(k)`: a 2k×k×k grid with the face x = 0 clamped, a −y load on a patch of
0.1 × 0.1, volume fraction 0.30 and the R2 continuation schedule. It is run by the authors' SIMP driver with its
default configuration (tol 10⁻⁵, inner tol 0.1, max_outer 300, Emin 10⁻⁹). The FP32 operator is
`stencil_diff` (repaired) and the FP64 operator is `node_hoist`. Configurations: `mg_ir`, `mg64`, and
`mg32_rec` (the control, whose true residual is recorded and never tested).

## 4. Endpoints and definitions

### 4.1 Action agreement ("matched nontrivial displacement actions")
Each action is compared with `hoist64_ref` applied to the same field. The metric is
d = ‖y_X − y_ref‖₂ / ‖y_ref‖₂ over free DOFs, with fixed DOFs zeroed in both. It is computed for X ∈
{`hou_cg32` operator, `stencil32_orig`, `stencil32_rep`} on two nontrivial fields:
- (R) a seeded standard-normal FP32 field (CuPy RandomState(3), as in E10), with fixed DOFs set to zero;
- (S) the FP64 reference solution of the Hou system at the same k (Section 4.5), rounded once to FP32 for the
  FP32 operators.

Field R is the system-identity gate (Section 5, G2). Field S measures how accurately each operator acts on a
smooth physical displacement.

### 4.2 Time
- Application time is the median of 11 synchronized CUDA-event intervals of one operator call, after 3
  warm-up calls, with the IQR. This is the protocol of `E10_external_hou.t_median`. Each path is timed in its
  own process. Hou's call includes its own per-call allocations, as released.
- Setup time is measured twice:
  - (a) Including compilation, on the first build. Hou's setup is `autowrite` + module import + `killer` +
    `survivor`. Ours is load and mask + operators + `GMG(...)` + the first `mg.update(E)`.
  - (b) Excluding compilation: a second, identical build in the same process, timed between synchronizations.
    For Hou this is `killer` + `survivor` only; their kernel source is generated for a fixed grid.
- Solve time is the wall time between device synchronizations around the solver call, excluding setup. For
  our paths it is the median of 3 cold solves from zero, with the hierarchy fixed. For `hou_cg32` it is the
  median of 3 solves at k = 80 and 160, and one solve at k = 256.
- Krylov-step time is measured with CUDA events recorded once per iteration, without extra synchronization,
  inside timed runs. These runs do no other extra work:
  - ours: the interval between consecutive preconditioner calls, through a wrapper around M or M32 that only
    records an event;
  - Hou: the interval between iteration starts, in the instrumented copy (Section 6).

  It is reported as the median and IQR over the iterations of the timed solve. For mg_ir the outer FP64
  residual evaluations are reported separately as a mean per outer step.
- Optimization time (Q3) uses the authors' definition: compute time is the sum of the per-iteration times,
  excluding process start, compilation and guard checks. Total wall time is also recorded.

### 4.3 Accuracy and convergence
- Native stop: the iteration count, the stop reason and the in-solver residual at the stop.
- Independent FP64 equilibrium accuracy. A separate checker process loads the returned iterate. It rebuilds
  the system from scratch and computes ‖b − K u‖₂/‖b‖₂ in FP64 with the FP64 `node` mapping, which differs
  from the `node_hoist` mapping that the solvers use. T1 verifies both against the CPU assembly. Hou's FP32
  iterate is cast exactly to FP64 first.
- Attainment of 10⁻⁵. A path attains the common accuracy when the independent true residual at a recorded
  iterate is ≤ 10⁻⁵. Our paths attain it at their native stop unless they fail. For `hou_cg32` it is read
  from the continuation history (Section 6, step H4) as the first checkpoint ≤ 10⁻⁵, up to their own limit of
  10,000 iterations. Time to 10⁻⁵ for Hou is (iterations to the first passing checkpoint) × (median Krylov-step
  time of the timed native run) + their measured solve-start overhead (r₀ formation, from the timed run).
  Without a passing checkpoint the result is "not attained", with the smallest true residual reached and its
  iteration.
- True-residual history:
  - ours: the FP64 true residual at every Krylov step (mg64) or every outer step (mg_ir, with the inner
    iteration counts), recorded in a separate untimed history solve;
  - Hou: the true residual at the native-stop iterate, every 50 iterations (k = 80, 160) or every 250
    iterations (k = 256), and at iteration 10,000.
- Errors against the reference: the relative compliance error |bᵀu − c_ref|/|c_ref| and the relative energy
  error ‖u − u_ref‖_K/‖u_ref‖_K, both computed in FP64 by the checker.

### 4.4 Memory (three separately defined peaks, with a spill record)
- Pool peak: the CuPy default-pool `used_bytes` and `total_bytes` (reserved), read at every device allocation
  by a `cupy.cuda.MemoryHook`. The hook is disabled inside timed sections and enabled in the paired untimed
  pass of the same workload in the same process. In capacity runs it is enabled throughout (Section 6, C).
- Process-dedicated peak: the maximum of the WDDM counter `GPU Process Memory(pid_*)\Dedicated Usage` for this
  process, from a continuous PowerShell `Get-Counter -Continuous -SampleInterval 1` sampler that runs for the
  whole life of the process. The same sampler records `Shared Usage`.
- Device-wide peak: the maximum of `nvidia-smi --query-gpu=memory.used -lms 200` over the life of the process.
  The device baseline is read before the process allocates. Other processes' dedicated usage at launch is
  also recorded.
- Spill: shared usage growing by more than 256 MiB above its value at start, at any sample of the continuous
  sampler or at any `guard.SpillWatch` check, marks the measurement as spilled.

A peak taken in a process that also ran another path, or in a probe shorter than the full workload, never
counts as the isolated full-run peak of a configuration. Historical values of that kind are quoted only as
development data.

### 4.5 Hou-system reference
For each k, `mgir_rep` is solved with outer tolerance 10⁻⁹ and outer ≤ 200 steps. The reference is named by the
tolerance its independent checker actually attains. If 10⁻⁹ is not attained, the best attained value names it,
and any error below 10 × that value is reported as "at the resolution of the reference".

### 4.6 Capacity prediction ("full live-workspace prediction") and admission
For configuration c on a grid with n elements (allocated, here equal to active) and N_d DOFs:

W_c(n) = β_c · n + τ_c(N_d) + ω

The terms are:
- β_c: the larger of the accounted bytes per element (`voxfem.memory.breakdown` total) and the peak pool
  `used` bytes per element, both from the anchor of c.
  - The anchor for mg_ir is the T27 run at k = 384 (C1).
  - The anchor for mg64 is the T27 run at k = 320 (C3).
  - For mg32_rec it is the mg_ir anchor, since the two configurations allocate the same workspace class
    (LeanIRWorkspace).
  - Before an anchor exists, the prior is the development value: mg_ir 146.1 B/element
    (`results/E7/memory_k320_mg_ir.json`) and mg64 194.5 B/element (`results/E7/memory_k320_mg64.json`).
- τ_c: the largest single transient allocation. It is one FP64 nodal vector (8 N_d) for mg64 and one FP32
  nodal vector (4 N_d) for mg_ir and mg32_rec. This is the request size that failed in E12b.
- ω: the non-pool process overhead, measured in the anchor as the process-dedicated peak minus the pool
  reserved peak, with a floor of 0.5 GiB.

Admission requires W_c(n) + 1.5 GiB ≤ E_free. Here 1.5 GiB is the default margin of `guard.require_budget`,
and E_free is `guard.effective_free_bytes()` read inside the run process before any problem allocation. Every
admitted run then sets `CUPY_GPU_MEMORY_LIMIT` = E_free − 1.5 GiB. The pool then frees its cache and fails with
an allocation error instead of oversubscribing the device. The spill guards stay active in addition.

A refusal writes a record with W_c, E_free and the other processes' usage, allocates nothing more, and is
classified as a guard prediction. While the queue is still running, a refused size may be re-evaluated at most
twice, at the start of a later queue session. Every evaluation is logged. Re-evaluation reads no outcome
data; only the admission inputs can change.

### 4.7 Size ladder for Q3
The authors' multigrid factorizes the coarsest level densely and refuses more than 20,000 coarsest DOFs. The
grids 2k×k×k admissible without padding between k = 320 and 448 are therefore k ∈ {320, 352, 384, 416, 448}.
These have 65,536,000, 87,228,416, 113,246,208, 143,982,592 and 179,830,784 elements. Sizes in between (for
example k = 336, 360 or 400) either fail that check or need padding to the next ladder size, which allocates
the same grid. The resolution of every fit interval is therefore one ladder step. No padded size is run.

### 4.8 Outcome classes (mutually exclusive; the first that applies)
1. not run: the budget or freeze date was reached, or a prerequisite failed;
2. guard prediction: refused by Section 4.6 before allocation;
3. allocation failure: a CuPy `OutOfMemoryError` under the pool cap;
4. spill: Section 4.4. This class applies even if the run completed, and the run is invalid;
5. numerical breakdown: `SolveFailed` (non-positive or non-finite curvature, non-finite residual, IR
   correction rejected at the inner floor), or a Krylov iteration limit reached without a pass;
6. wall cap: the process was stopped at its wall-time cap (Section 7);
7. design-iteration guard: an optimization reached max_outer = 300 without converging;
8. native stop: completed under its native rule, but the path has no FP64 acceptance test (`hou_cg32`,
   `mg32_rec`), or the independent check of the returned state exceeds 10⁻⁵;
9. verified acceptance: completed, and every state solve was accepted in-process on an FP64 true residual
   ≤ 10⁻⁵. The independent checker confirms the returned (final) state at ≤ 10⁻⁵. There is no spill, and for
   optimizations the termination is `max_change` or `bounded_oscillation` and the final design is saved.

A capacity entry counts as a demonstrated lower bound only in class 9, or in class 8 for the mg32_rec control
(labelled "complete design, native recursive stop"). Optimization-capacity entries additionally require the
complete final design (the saved density field).

## 5. Gates, predictions and decision rules

### 5.1 Gates (a failed gate makes the affected endpoints inconclusive and is reported as such)
- G1 Code identity:
  - every copied `voxfem` file and experiment helper has the same SHA-256 (16 hex) as the `code_files` manifest
    of `results/E32/simp_cantilever_k384_mg_ir_stencil_diff.json`;
  - the copied Hou tree matches `git ls-files -s` of `external/CuPy-for-TO` at d8dca7a;
  - the instrumented Hou CG with its hooks disabled matches `FE.FE` at k = 16: the same iteration count and an
    iterate difference ≤ 10⁻⁶ relative.
- G2 System identity at each k:
  - the mapped fixed-DOF sets are identical;
  - the mapped load vectors are identical, entry by entry;
  - all initial iterates are zero;
  - d_R ≤ 10⁻⁵ for `hou_cg32`, `stencil32_orig` and `stencil32_rep`. E10 measured 1.3 × 10⁻⁷.
- G3 Checker validity at k = 16: on a mg64 state, the checker's true residual agrees with the in-solver true
  residual to within 1% of its value.
- G4 Timing validity: the mean foreign 3D-engine use is logged by a T27 sampler every 10 s over each timed run.
  - A run with a mean above 5% has its times excluded, and it is repeated once.
  - A run between 1% and 5% is reported with a flag. Memory and accuracy endpoints are kept in all cases.
  - Inside timed sections the hook overhead must stay under 2%. This is checked once at k = 80 by timing the
    Hou application and our stencil application with the hook enabled and disabled. If the difference is 2% or
    more, every timing is taken with the hook disabled; this is already the design for timed sections.

### 5.2 Confirmatory predictions (from the development data) and what counts as support, contradiction or inconclusive

| id | Endpoint | Prediction (development basis) | Support | Contradiction | Inconclusive |
|---|---|---|---|---|---|
| P1 | Independent true residual of `hou_cg32` at its native stop, k = 80, 160, 256 | > 10⁻⁵ at every k (E10: 5.8 × 10⁻² and 0.16 at k = 80, 160) | > 10⁻⁵ at every k with a completed solve | ≤ 10⁻⁵ at any k | no Hou solve completes at any k |
| P2 | `hou_cg32` attains 10⁻⁵ within its 10,000-iteration limit | not attained at any k (an FP32 unpreconditioned floor) | not attained at every k with a continuation run | attained at any k (then P3b is computed at that k) | no continuation run completes |
| P3a | Solve-time ratio: Hou native solve time / `mg64_rep` (setup excl. compilation + solve) | > 1 at every k (E10, solve only: 142× and 342× at k = 80, 160) | > 1 at every k with both solves | < 1 at any k | a gate fails at every k |
| P3b | Time to the common accuracy: Hou / `mg64_rep`, only where Hou attains 10⁻⁵ | > 1 | > 1 | < 1 | Hou does not attain 10⁻⁵ (reported as "no common-accuracy time for Hou") |
| P4 | Application-time ratio: `hou_cg32` operator / `stencil32_rep` | ≥ 100 at k = 80, 160, 256 (E10: 197, 223, 250 against the original stencil) | ≥ 100 at all three k ("two orders of magnitude") | < 10 at any k | any G2 failure |
| P5a | Repair cost per application: `stencil32_rep` / `stencil32_orig`, ratio of medians | ≤ 1.15 at every k (+7.6% at 65.5 M elements in the paper) | ≤ 1.15 at every k | > 1.15 at any k with non-overlapping IQRs | the 1.15 boundary lies inside the interval of the two IQRs at the deciding k |
| P5b | Repair cost per solve: (`mg64_rep` / `mg64_orig`) and (`mgir_rep` / `mgir_orig`) solve time | within [0.85, 1.15] at every k | within the band at every k for both solvers | outside the band at any k with non-overlapping solve IQRs | otherwise |
| P6 | Memory: process-dedicated peak of `mg64_rep` and `mgir_rep` against `hou_cg32` (solve) | ours lower at every k (E10: Hou application alone reached 15.5 GiB dedicated at k = 256) | lower at every k with both solves | higher at any k | no Hou solve |
| P7 | Smooth-field action error d_S: `stencil32_rep` against `stencil32_orig` | d_S(rep) < d_S(orig) at every k | at every k | d_S(rep) ≥ d_S(orig) at any k | G2 fails |
| P8 | Our four Hou-system paths reach verified acceptance (class 9) | all, at every k | all | any class 5 (breakdown) | budget prevents runs |
| C-A | mg32_rec (repaired) at k = 384: a complete design | completes (class 8); some states may exceed 10⁻⁵ (E14 at k = 320: max 1.01 × 10⁻⁵) | class 8, design saved | class 2–5 or 7 | class 1 or 6 |
| C-B | mg64 (repaired) next size k = 352 | depends on E_free: β ≈ 194.5 B/element gives W ≈ 18.3 GiB, admitted only if E_free ≥ 19.8 GiB | class 9 → lower bound 87.2 M elements | class 3–5 or 7 → fit interval (65.5 M, 87.2 M] | class 2 → interval (65.5 M, 87.2 M] by prediction only, stated as such |
| C-C | mg_ir (repaired) at k = 416 | W ≈ 21.7 GiB (β ≈ 146 B/element, τ ≈ 1.6 GiB, ω 0.5 GiB), so admitted only if E_free ≥ 23.2 GiB; refusal (class 2) is the likely outcome on this display-driving card | class 9 → the new paper-wide maximum of 143,982,592 elements | class 3–5 or 7 → fit interval (113.2 M, 144.0 M] | class 2 → interval by prediction only |

Rules applied to every endpoint:
- Ratios are reported as point values with the IQRs of their components. There is no pooling across k.
- A prediction is not supported by a subset of k selected after the fact. The decision uses every k at which the
  measurement exists and the gates pass. The k values without data are listed.
- Contradictions are reported as fully as supports. A contradiction of a statement in the submitted manuscript
  is flagged for the authors' wording decision. It is never removed from the record.

### 5.3 Paper-wide maximum
The paper-wide maximum of complete optimizations is updated only if a capacity entry larger than 113,246,208
elements reaches class 9, with a saved design. A class-8 mg32_rec entry never updates it. The maximum is the
active element count, which equals the allocated count on this ladder; both are recorded.

## 6. Procedure (exact order; one GPU job at a time)

Environment and isolation:
- Interpreter `<user-home>/anaconda3/python.exe` (Python 3.11.5, CuPy 13.4.1) with `PYTHONDONTWRITEBYTECODE=1`
  and `CUPY_CACHE_DIR=tasks/T27/_cupy_cache`.
- `voxfem` and the needed experiment helpers are copied into `tasks/T27/src/`. A T27 boot module is copied from
  `_boot.py` with its root, results and cache paths pointing into `tasks/T27/`. It records the same environment
  fields and per-file manifest.
- The Hou code is copied into `tasks/T27/_work/hou_k{k}/` per k; their `autowrite` writes `ker.py` there.
- Nothing is written to the project's `results/`, `external/`, `runtime/`, `figures/` or `tables/`.
- Every process calls `guard.require_exclusive()` at start, so it refuses to start while another Python process
  holds GPU memory. It runs the continuous memory and activity samplers (Section 4.4, G4) and writes one JSON
  record into `tasks/T27/out/`.
- Device↔host transfers of whole vectors are chunked to ≤ 256 MiB, following the fix the authors recorded for
  false spill triggers.

V (verification, not endpoints): G1, then G2, G3 and the k = 16 instrumented-CG equivalence check. Also k = 32
smoke runs of each driver. If a gate fails, the driver is fixed, the check is rerun, and the fix is logged; no
confirmatory run starts before V passes.

H (Hou system), for k = 80, then 160, then 256:
1. H1 reference (Section 4.5): one process. It writes the FP64 reference iterate to `tasks/T27/scratch/`.
2. H2 applications: four processes (`hou_cg32` operator, `stencil32_orig`, `stencil32_rep`, `hoist64_ref`).
   Each measures fields R and S, the application time and setup (a) and (b). G2 is evaluated after these.
3. H3 solves: five processes (`hou_cg32`, `mg64_orig`, `mg64_rep`, `mgir_orig`, `mgir_rep`). Each does the timed
   solves (Section 4.2), then one untimed history solve with the hook enabled for the pool peak. Our history
   solve records the true residual per Krylov or outer step through the read-only wrapper around M, which uses
   a separate buffer and leaves the iteration unchanged. The returned iterates go to scratch.
   - Admission for `hou_cg32` at k = 256 uses Section 4.6, with β taken from T27's own k = 160 `hou_cg32` pool
     peak per DOF and τ equal to one FP32 nodal vector. A refusal is class 2, and the Hou state-solve lower
     bound is then k = 160.
4. H4 Hou continuation: one untimed process. It runs the instrumented copy of `CG.CG` (arithmetic identical;
   G1) with the stopping test disabled to 10,000 iterations. It records the iteration at which the native test
   first holds.
   - At k = 80 and 160, FP64 true residuals at the checkpoints of Section 4.3 are computed in-process if the
     guard admits the extra FP64 buffers.
   - At k = 256, or if the guard refuses, FP32 iterate snapshots are written to scratch at those checkpoints.
5. H5 checker: one process per k. It computes the independent true residuals, the compliance and energy
   errors against the reference, and the residuals of every saved snapshot.

C (capacity, authors' cantilever, repaired FP32 operator), in this order:
1. C1 `mg_ir` at k = 384: the anchor and lower-bound check. It sets β, τ and ω for mg_ir and mg32_rec.
2. C2 `mg32_rec` at k = 384.
3. C3 `mg64` at k = 320: the anchor and lower-bound check for mg64.
4. C4 `mg64` at k = 352, by admission (Section 4.6). If it is verified, `mg64` at k = 384 is evaluated by
   admission only. Historically that size spilled without a cap and ran out of memory under a 21.5 GiB cap
   (E12, E12b, E23, with the original stencil and the same workspace). It is run only if admitted.
5. C5 `mg_ir` at k = 416, by admission. If it is verified, `mg_ir` at k = 448 follows, by admission.
6. C6, secondary, run only after C1–C5 and inside the budget:
   - `mg32_rec` with the original stencil at k = 384;
   - `mg32_rec` (repaired) at k = 416, by admission, only if C5 at k = 416 was verified.

Each C run uses a T27 copy of `run_simp.py` that changes nothing in the optimization. It adds only:
- the samplers and the hook;
- saving the final FP32 physical density and the FP64 final displacement, chunked to scratch after the last
  spill check, plus the authors' FP16 design `.npz`;
- the admission step.

A separate checker process then rebuilds E from the saved density and the final penalty, and recomputes the
final state's true residual with the FP64 `node` mapping. It also records the relative difference of the final
compliance from the historical record at the same k and configuration, where one exists (for example E32 at
k = 384). This is descriptive only, with no threshold.

O (outputs, after all runs; no GPU):
- `tasks/T27/hou_matched.csv`: one row per (k, path, workload). The columns are k, n_elem, ndof, path,
  workload, operator, residual and iterate precision, op variant, outcome class, d_R, d_S, application median
  and IQR, setup (a) and (b), native stop rule, native iterations, solve median and IQR, Krylov-step median and
  IQR, independent true residual at the native stop, compliance and energy error, attained-10⁻⁵ flag,
  iterations and time to 10⁻⁵, smallest true residual, pool used and reserved peak, process-dedicated peak,
  device-wide peak and baseline, other processes' usage at start, spill growth, valid flag, mean foreign
  activity, and source file.
- `tasks/T27/capacity.json`: one entry per (configuration, size). It holds the class, n_elem active and
  allocated, the admission inputs (W_c, β, τ, ω, E_free, pool cap), the four memory peaks, spill, iterations,
  termination, final compliance, the in-process and independent final true residuals, the counts of states
  above 10⁻⁵ (mg32_rec), compute and wall time, the design file and the source record. Each configuration
  also gets:
  - `lower_bound`: its largest class-9 entry (class 8 for mg32_rec);
  - `next_tested`: the smallest larger size attempted and its class;
  - the fit interval.

  The historical entries quoted from development data are marked `historical`, with their file. The file also
  holds the paper-wide maximum (Section 5.3).
- `tasks/T27/residual_histories/{k}_{path}.csv`: iteration, inner iterations where applicable, FP64 true
  residual, recursive residual where available, and cumulative Krylov-step time.
- `tasks/T27/REPORT.md`: every endpoint with its source file, the gate results, the outcome per prediction
  (support, contradiction or inconclusive), and the deviations. Every number in it comes from a file under
  `tasks/T27/`.

No figure is drawn by this task (`figure_files` is empty). The CSV and JSON hold the data a figure would need.

## 7. Stopping rules

- Wall-time caps per process:
  - 120 min for H4 at k = 256;
  - 60 min for any other Hou process;
  - 60 min for a capacity run;
  - 20 min for any other process.

  A cap ends the process with class 6.
- Ladder stopping: a configuration stops ascending at its first outcome in classes 2–7. It also stops at the
  top of the ladder (k = 448).
- Hou: the CG stops at their own limit of 10,000 iterations, and no larger limit is used. If `hou_cg32` at
  k = 256 is refused, nothing larger is tried for Hou.
- Repeats: a valid measurement is never repeated to obtain a different number. Only an invalid run may be
  repeated, once: a spill caused by foreign activity, foreign activity above 5% (G4), or a start refused
  because a foreign process held GPU memory. Both records are kept in the repository, and only the valid one is
  reported. A class-3, 5 or 7 outcome is a result, not an invalid run, and is not repeated.
- Budget: about 10 GPU hours in total, in the priority order H (k = 80, 160, 256), then C1–C5, then C6. Any
  item not started before the end of December 10, 2026 is class 1. The numerical freeze is December 11.
- Early termination of the whole task occurs only if G1 cannot be met. Then nothing confirmatory runs, and the
  report states it.

## 8. Reporting rules

- Every reported number is read from a file in `tasks/T27/` and cited with that file. Historical values are
  cited with their project file and labelled historical. They are never mixed into a T27 ratio.
- Spilled measurements are excluded from every table and ratio. Their class is listed.
- Ratios between Hou and our paths are always stated with the two accuracies achieved (native and independent).
  An elapsed-time ratio is never presented as a speed-up at equal accuracy unless both paths attained 10⁻⁵
  (P3b).
- The precision of the operator, residual and iterate, the native stop, the timing boundary and the memory
  definition accompany every row (Section 3.1, Section 4).
- Paths that were not run or not attained are reported with their class, never left blank.
- The submitted E10 rows (k = 16–256, original stencil, shared-process measurements) remain historical. The
  T27 rows supersede them for k = 80, 160 and 256 only where the gates pass. The historical 114–648 range is
  not recomputed here.
