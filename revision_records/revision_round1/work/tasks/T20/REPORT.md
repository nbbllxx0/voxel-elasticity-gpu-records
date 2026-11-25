# T20 report: FP64 forward and transpose actions of the fixed rounded operators

This task serves A.2, R1.3, R3.1, R3.2 and R3.3. It is not prespecified. It made no language-model calls and ran three
GPU jobs, all under the guard. Outputs: `adjoint_checks.json`, `small_spectrum.csv`, `workspace.json`, plus
`s22_reproduction.json` (the basis-column diagnostic). The third job and the CPU tests `mask_test.json` and
`gate_test.json` belong to the fix round described at the end. A second fix round, CPU only, corrected the largest
restart and block figures in `workspace.json`. A third fix round, also CPU only, made the operator's two corrections of
2026-11-24: the form of the S22 gate and the label of a maximum below the measured range. No measured value changed.

## What was built

`t20_ops.FreeOperator(grid, form, fixed)` gives the FP64 forward and transpose actions of six operators on the free
DOFs ($A_{ff}=DAD$, with $D$ the 0/1 diagonal of the free DOFs). $D$ is formed per component from the production
node mask, in which bit $c$ fixes DOF $3n+c$, so a roller node keeps its free components. All six use FP32-stored moduli. They are matrix-free
CuPy kernels, and each transpose stores nothing beyond its output vector.

| form | forward (FP64 arithmetic) | transpose |
|---|---|---|
| `ref` | production FP64 operator (`node_hoist`, $K_0$) | same kernel with $K_0^{\mathsf T}$ ($K_0$ is symmetric only to rounding) |
| `atomic` | production `elem_atomic` kernel with $Q=\mathrm{fl}_{32}(K_0)$ | same kernel with $Q^{\mathsf T}$ |
| `corner` | production `elem_ref` kernel with $Q$: $Q(I-TS_0)$ | new kernel: $Q^{\mathsf T}v_e$, then the sum of the eight nodal blocks is subtracted at local node 0 |
| `mean` | production `elem_mean` kernel with $Q$: $Q(I-P)$, pairwise mean | new kernel: $(I-P)Q^{\mathsf T}v_e$. The projection is applied after the multiplication, with the kernel's pairwise sums |
| `stencil` | production `stencil_c32` kernel: FP32 coefficients $W_r(n)$ applied in FP64 | generated kernel: output node $m$ forms $W_r(m-r)$ with the forward kernel's expression text and compile options, and applies $W_r(m-r)^{\mathsf T}$ |
| `diff` | production `stencil_diff_c32` kernel: $\sum_{r\ne0}W_r(n)(u_{n+r}-u_n)$ | generated: $\sum_{r\ne0}W_r(m-r)^{\mathsf T}v_{m-r}-\sum_{r\ne0}W_r(m)^{\mathsf T}v_m$ |

**Independent CPU assembly (`t20_cpu.py`).** The element forms are assembled with SciPy from the element DOF table.
For the stencil forms, I emulated the FP32 coefficient formation on the CPU with correctly rounded FP32 operations,
following the generated expression text.

The NVRTC compiler contracts some of the group additions into fused multiply-adds, and which ones it contracts differs
between expressions. In a test kernel, a product that two coefficients share was not fused. The emulation therefore
carries one contraction order per expression. All 107 multi-group expressions have exactly one matching order on the
S22 grid. The orders found independently on the `asym` grid are identical. With the S22 orders, the emulation equals
the production kernel's coefficients bit for bit (`adjoint_checks.json` → `coefficient_emulation`):
* on S22, where the orders were identified: 258,750 coefficients, 0 differing;
* on the layouts not used to identify them: 480,114 coefficients, 0 differing. These are the three $k=4$ beams
  (3 × 142,974), `asym` (29,952; it also served the independent cross-identification) and the roller layout of the
  fix round (21,240). The four layouts of the main run alone give 458,874.

**Test layouts** (all clamped at $x=0$):
* `s22`: the Table S22 grid, $16\times8\times8$, with E29's moduli (3888 free DOFs).
* The slender beam at $k=4$ ($32\times4\times4$, 2400 free DOFs) in three layouts: uniform; T21's 8:1 interface at
  $x=4$; T33's three enclosed voids at $10^{-9}$.
* `asym`: a $6\times5\times4$ grid with random moduli, so that an axis mix-up cannot cancel.
* `roller` (fix round): the same grid with other random moduli and per-component masks: the $x=0$ face clamped,
  the $x=n_x$ face on rollers (mask 6: $y$ and $z$ fixed, $x$ free) and 15 % of the other nodes with one of the
  masks 1–6. It has 438 free DOFs; the earlier all-or-nothing rule would have left 369.

The ordinary vectors are three uniform random fields and one smooth field, all zero on the clamped DOFs.

## GPU jobs

Both jobs used T19's launcher protocol (`t20_launch.py`):
* lock created with O_CREAT|O_EXCL;
* the other Python GPU processes checked;
* admission against nvidia-smi free memory with no CUDA context in the launcher;
* the WDDM watch armed before the job's CUDA context;
* the job creates its CUDA context and one one-element array, then waits; it allocates nothing else until a sample
  holds its PID with both counters, and that sample sets the shared-memory baseline;
* a final sample checked before release.

**Coverage.** The spill watch covers each job from that first complete sample to the final check, not the whole
process. The CUDA context and the one-element array were created before the baseline (the process does not appear in
the counters before it has a context); the job's dedicated usage at the baseline was 354,570,240 B in each run. The
largest shared growth is measured from that baseline.

| item | run1 (main) | run2_repeat (atomic kernels ×3) | run3_fix (fix round) |
|---|---|---|---|
| admission | nvidia-smi free 22,604,152,832 B against predicted peak 4 GiB + 1.5 GiB margin: admitted | same values: admitted | free 22,604,152,832 B against 10 GiB + 1.5 GiB: admitted |
| other processes' dedicated usage (information) | 6,374,780,928 B | 6,374,776,832 B | 6,374,780,928 B |
| guard.require_budget (in process, information) | ok (effective free 19,027,341,312 B, need 3 GiB + margin) | ok | ok (effective free 19,027,341,312 B, need 8 GiB + margin) |
| pool cap | 22,542,286,848 B | 22,542,286,848 B | 22,542,286,848 B |
| watch | from the first complete sample to the final check, which was taken | same | same |
| shared baseline / largest growth from it | 77,594,624 B / 115,343,360 B (limit 256 MiB) | 77,594,624 B / 2,097,152 B | 77,594,624 B / 117,440,512 B |
| status | ok, valid, no spill | ok, valid, no spill | ok, valid, no spill |

Inside run1, each beam size $k$ was admitted from 8 × the measured workspace at $k/2$ plus the margin, checked
against `cudaMemGetInfo`. No size was refused (`out/run1/memory.json`).

## Results against the acceptance statement

1. **Dot tests and explicit actions ≤ 10⁻¹² on ordinary vectors: met.** These cover 6 layouts × 6 forms (the five
   of the main run and the roller layout of the fix round), forward and transpose, in `adjoint_checks.json`.
   * Largest explicit-action error against the CPU assembly: $1.05\times10^{-15}$.
   * Largest dot-test defect: $1.70\times10^{-16}$.
   * Largest entry difference of the full free-DOF matrices, built from every unit vector: $2.4\times10^{-16}$ of the
     largest entry on the five layouts of the main run, $4.2\times10^{-16}$ on the roller layout.
   * The stencil forms are bitwise equal to the CPU assembly, and their transposes are bitwise equal to the transposed
     forward matrices.
   * The element forms differ only at FP64 rounding. Their FP64 atomics make them nondeterministic at that level.
   * Every output is exactly zero on the fixed DOFs, including the single fixed components of the roller layout.
   * On the slender beam with the interface layout, $k=8,\dots,128$ (51.2M DOFs at $k=128$), the GPU dot tests of all
     six forms are ≤ $5.4\times10^{-18}$.
2. **The lowest three algebraic eigenvalues of each symmetric part are within 1% of the dense solution: met.** These
   cover 36 matrices in `small_spectrum.csv`.
   * Dense: `eigvalsh` of $(A+A^{\mathsf T})/2$ from the CPU assembly.
   * Iterative: LOBPCG on $(A_{\rm fwd}+A_{\rm T})/2$, with both matrices built from the GPU kernels' unit columns.
     Block size 6, two random starts, and an exact FP64 factorization of the reference operator as SPD preconditioner.
   * Largest relative difference: $3.8\times10^{-6}$ (`beam4_voids`, `diff`, a cluster of three nearly equal void
     modes).
   * Largest $\|Sv-\lambda v\|/(\|v\||\lambda|)$: $4.1\times10^{-4}$.
   * No symmetric part has a non-positive eigenvalue on these grids.
3. **The existing fixed rounded stencil actions are reproduced exactly.** On the S22 grid:
   * The T20 forward matrices of `stencil` and `diff` equal the basis columns of the production `stencil_c32` and
     `stencil_diff_c32` kernels bit for bit.
   * The E29 metrics of those kernels are reproduced identically: symmetry error, $\lambda_{\min}$, the number of
     negative eigenvalues, the ten lowest relative eigenvalue errors, and the largest relative eigenvalue error
     ($3.946865900394947\times10^{-5}$ and $1.2510857446690338\times10^{-6}$).
   * The matrix error differs at $2.7\times10^{-16}$ relative, the summation order of the Frobenius norm
     (`s22_reproduction.json`).
   * This comparison is part of the exported gate: `small_grid_gate_passed` in `adjoint_checks.json` requires the
     ordinary-vector and eigenvalue tests and `s22_gate`. In its corrected form (third fix round), `s22_gate`
     requires:
     * the bitwise equality of the stencil columns above (exact);
     * for the six deterministic kernels, the identical symmetry error and the matrix error within $10^{-14}$
       relative;
     * for the same kernels, the identical number of non-positive eigenvalues, and the derived eigensolver figures
       within the task's 1 % eigenvalue tolerance. This applies to $\lambda_{\min}$ (relative difference ≤ 0.01)
       and to the eigenvalue errors $\lambda/\lambda_K-1$ (maximum and ten lowest; difference ≤ 0.01 in units of
       $\lambda_K$);
     * the identities below (exact);
     * the negative count of the atomic kernels.
   * In the saved records, every derived difference is 0, so all are within tolerance and the gate passes
     (`adjoint_checks.json` → `s22_gate.derived_differences`). A planted fault in any of the nine items turns the
     gate false. The thread-order differences of the eigenvalues leave it true (`gate_test.json`).
4. **k=128:** nothing was refused. The operator step at $k=128$ peaked at 1,279,278,592 B of pool, and the V-cycle
   build at 1,532,286,976 B. The small-grid gate therefore stands without a memory caveat. The workspace estimates
   below show which $k=128$ solves fit.

## Basis-column diagnostic (Table S22), reproduced separately

`s22_reproduction.json` repeats E29 part R3: nine operators, each applied to every unit vector of the 3888 free DOFs.
* **Deterministic kernels.** The FP64 node kernel, the FP32 original, difference and self-corrected stencils, and the
  two rounded-coefficient kernels reproduce E29's symmetry error, $\lambda_{\min}$, negative count and eigenvalue
  errors identically. The eigenvalue figures match identically only with the default LAPACK thread count; see
  Limitations.
* **Identities claimed in the supplement.** They hold bit for bit:
  * the self-block correction equals the difference form on unit vectors;
  * the FP32 original stencil equals its rounded-coefficient kernel;
  * the rounded difference and original kernels agree outside the nodal self blocks.
* **Atomic FP32 element kernels.** The original element, corner and mean kernels are not bitwise reproducible from run
  to run:
  * Within one later process, the three repeats of each kernel differ pairwise in 459 to 735 entries (nine
    comparisons). Each repeat differs from the main run in 731 to 978 entries (nine comparisons). The differences
    reach $6.3\times10^{-8}$ of the largest entry.
  * Their rounding-level metrics vary accordingly: for example, the element kernel's symmetry error ranges from
    $4.54$ to $5.16\times10^{-9}$ over four runs, against E29's $4.64\times10^{-9}$. E29's values lie within or next to
    this spread. The corner kernel's matrix error, $5.4504\times10^{-8}$, is just above the four-run range of
    $5.4220$–$5.4331\times10^{-8}$.
  * No run has a negative eigenvalue, as in E29. Only the conclusions of Table S22 (no non-positive eigenvalue;
    symmetry at about $10^{-8}$) are reproducible for these kernels, not their last digits.

## Findings for A.2 and R3.3 (coefficient level, small grids)

* **Skew** $\|A-A^{\mathsf T}\|_F/\|A\|_F$ (`small_spectrum.csv`):
  * The atomic element form and the element-mean form are symmetric to FP64 assembly rounding (≤ $2.6\times10^{-17}$).
    The mean form is symmetric because $PQ=QP$ (T19).
  * The corner form has skew $7.9$–$10\times10^{-9}$ on every grid, uniform included.
  * The original and difference stencils have skew 0 on the uniform beam, $3.3$ and $4.1\times10^{-10}$ at the 8:1
    interface, $6.7$ and $7.7\times10^{-12}$ with the voids, $5.9$ and $7.2\times10^{-9}$ on S22, and $1.0$ and
    $1.3\times10^{-8}$ on the roller layout.
* **Uniform beam, $k=4$, lowest eigenvalue of the symmetric part** against FP64's $1.936846\times10^{-5}$:

  | form | lowest eigenvalue | relative difference from FP64 |
  |---|---|---|
  | original stencil | $1.932812\times10^{-5}$ | $-2.1\times10^{-3}$ |
  | atomic element | $1.932812\times10^{-5}$ | $-2.1\times10^{-3}$ |
  | corner | $1.936709\times10^{-5}$ | $-7.1\times10^{-5}$ |
  | mean | $1.936835\times10^{-5}$ | $-5.7\times10^{-6}$ |
  | difference | $1.936844\times10^{-5}$ | $-1.0\times10^{-6}$ |

  At this size every form stays positive. The negative direction of the original stencil appears only on finer grids
  (T22).

## Workspace (`workspace.json`)

**Measured at every $k$, including $k=128$ (run1):**
* the job process's dedicated usage at its first complete sample, 354,570,240 B (CUDA context and one one-element
  array);
* the build peak and live bytes of the common V-cycle;
* the operator step.

**Measured solve peaks (run3_fix, `out/run3_fix/solvemem.json`).** The four solves of E29 part R2 were run as E29 runs
them, with every array allocated inside the measurement, at $k=64$ and $k=128$:
* the FP64 reference PCG (`krylov.pcg64` with the common V-cycle);
* the curvature-logging PCG (`pcg_energy`) beside the kept reference solution;
* the FP32 control (`pcg32`, mode `mg32_x64`) with the common V-cycle, and with the operator's own V-cycle built
  while the common one is live, each followed by the compliance and residual checks of the returned iterate.

The iteration counts were capped (60 for the two FP64 solves, past the first true-residual replacement; E29's 400 for
the control), which leaves the set of live arrays unchanged. The copied functions reproduce E29's recorded control
results to the last printed digit, for example the true residual 0.1993168519306156 at the first pass at $k=128$
(`results/E29/beam_controls.json`).
The library solvers of `cupyx.scipy.sparse.linalg` were measured on a T20 operator with the common V-cycle at $k=32$
and $k=64$, GMRES at $m=10$ and $20$, LOBPCG at $b=3$ and $6$. Above their fixed parts, MINRES used 12 FP64 vectors,
GMRES($m$) $m+9$ and LOBPCG($b$) $15b$, the same at both sizes, plus at most 27,536 B of small arrays.

**Counted, per solve:** every full-size array the cited implementation holds at its peak, temporaries included
(`workspace.json` → `inventories`, with source lines), plus the context, the FP32 moduli, the node mask and the
V-cycle build peak, which the pool keeps cached. Compared with the earlier count:
* the FP32 control now counts the FP32 right-hand side `b32` and the two simultaneous FP64 casts of `b32` in E8's
  norm (6 FP64 and 5 FP32 vectors, earlier 5 and 4);
* the curvature-logging PCG now counts the temporary of `x += a_ * p` (8 FP64 vectors in E29's form, 9 with a T20
  operator, whose masked input copy is one more);
* MINRES, GMRES and LOBPCG use the measured library coefficients plus the right-hand side, the kept reference
  solution and a residual vector where the solve needs them. Their small arrays are counted from the CuPy source
  beside a 1 MiB allowance: GMRES keeps an FP64 Hessenberg matrix of $(m+1)\times m$ entries and two vectors of
  at most $m$ entries; LOBPCG's dense Rayleigh–Ritz step (Gram blocks, the $3b\times3b$ matrices, the Cholesky
  factor, two inverses, the eigenvectors and the dense eigensolver's workspace) is bounded by $32(3b)^2$ FP64
  entries, plus two $b$-entry history arrays per iteration, counted for 2,000 iterations;
* each count holds only on the code path it describes. CuPy caps the GMRES restart at the system dimension $n$, and
  LOBPCG switches to a dense eigensolver of the full $n\times n$ matrix when $5b>n$; the largest restart and block
  are therefore searched only up to these limits (`limited_by_solver_path` marks a value that the limit, not
  memory, sets);
* the in-place block eigensolver remains a planned count ($10b+3$ vectors, which include the operator's masked
  input copy, plus 2 for elementwise temporaries, plus the LOBPCG small-array bound) for an implementation not yet
  written. It is not a bound until that implementation is measured.

Each counted estimate of an existing implementation is at or above its measured pool peak: by factors of 1.06 to
1.19 at $k=128$ and 1.23 to 1.39 at $k=64$ (`workspace.json` → `inventory_checks`, all true). The capacity figures
use the free memory at run1's launch, 22,604,152,832 B, minus 1.5 GiB, which leaves 20,993,540,096 B. A later job is
admitted against the free memory at its own launch.

Slender beam at $k=128$: 51,171,075 DOFs, 409 MB per FP64 vector. The V-cycle has 6 levels, a build peak of
1,532,286,976 B and 866,661,888 B live afterwards.

| solve at $k=128$ | measured peak (pool) | estimate (context included) | fits |
|---|---|---|---|
| FP64 reference PCG as E29 runs it | 3,365,300,224 B | 4.02 GB | yes |
| FP64 reference PCG with T21's stored previous solution and independent residual | – | 4.84 GB | yes |
| curvature-logging PCG, E29 form / on a T20 operator | 4,593,407,488 B / – | 5.66 / 6.12 GB | yes |
| FP32 control, common V-cycle | 4,798,092,800 B | 5.45 GB | yes |
| FP32 control, own V-cycle beside the common one | 5,581,739,520 B | 6.98 GB | yes |
| MINRES (library) on a symmetric rounded matrix | – | 8.98 GB | yes |
| GMRES($m$) (library) on a rounded matrix | – | $m=10$: 11.85 GB; $m=30$: 20.04 GB | largest restart that fits: **$m=32$** (above the measured $m\le20$) |
| LOBPCG($b$) (library) on $(A+A^{\mathsf T})/2$ | – | $b=2$: 15.13 GB; $b=3$: 21.27 GB | largest block **$b=2$** |
| in-place block eigensolver (planned count, not a bound) | – | $b=4$: 20.86 GB; $b=6$: 29.04 GB | largest block $b=4$ |

At $k=128$ the largest GMRES restart, 32, lies above the measured restarts (10 and 20). It rests on the measured
per-vector coefficient and the source count of the Hessenberg matrix, and a job that uses it measures its workspace
before admission. The library LOBPCG block $b=2$ lies below the measured blocks (3 and 6). It is a downward
extrapolation by the same count, not a value within the measured range. The estimate stays 2.

At $k=64$ the largest GMRES restart is 375 and the largest block is 25 (library LOBPCG) or 38 (planned in-place).
These are extrapolations of the same kind, well above the measured parameters. At $k\le32$ the
largest values (`workspace.json` → `rows`) are extrapolations still further from the measurements and are not
admission figures. At $k=8$ ($n=15{,}795$) the GMRES maximum is CuPy's cap $m=n$, and the LOBPCG maximum, 2,585,
is set by the dense Rayleigh–Ritz arrays, on the iterative path ($5b\le n$). Each maximum states its position
relative to the measured parameters (`relation_to_measured_range`: within, above, or below). For every grid,
`*_within_measured_range` gives the largest fitting value between the smallest and the largest measured parameter
(GMRES 10–20, LOBPCG 3–6). It is null where the largest fitting value lies below that range, which is only the case
for library LOBPCG at $k=128$.

A $k=128$ symmetric-part eigensolver with three wanted and three guard vectors ($b=6$) does not fit with either
solver. Three wanted vectors with no guard ($b=3$) do not fit with the library LOBPCG. Three wanted vectors plus one
guard ($b=4$) would fit with the planned in-place solver, which must be measured first. The previous planned block of
3 counted the operator's masked input copy twice. The restart and block searches now include the small dense arrays
and stop at CuPy's path limits. This lowers the earlier figures at small $k$ (for example GMRES at $k=16$ from 22,766
to 19,400). The values at $k=64$ and $128$ are unchanged, apart from the in-place block.

For planning, one $k=128$ application takes 15–19 ms forward and 15–27 ms transposed (`diff` is the slowest
transpose). These times are informational, with no interference rule applied.

## Limitations

* The iterative eigenvalue check runs on the CPU, on sparse matrices that are exact representations of the GPU
  actions, with an exact FP64 factorization as preconditioner. The matrix-free GPU eigensolver with a V-cycle aid
  belongs to T22.
* The contraction orders of the stencil coefficients are identified from kernel output on one layout and confirmed on
  the others. They describe this compiler (CuPy 13.4.1 NVRTC, CUDA runtime 12.8) with the production compile options.
* The library solver coefficients were measured at $k=32$ and $64$ and applied at $k=128$; the measured peaks of the
  existing implementations reach $k=128$. They were measured at GMRES $m=10,20$ and LOBPCG $b=3,6$. Largest restarts
  and blocks outside these, above or below (the $k=128$ LOBPCG $b=2$), are extrapolations by the source count, not
  measured capacities.
* The derived eigensolver figures of the S22 comparison depend on LAPACK's thread order. They reproduce E29 exactly
  only with the default thread count (32). With 1 and 4 OpenBLAS threads, $\lambda_{\min}$ moves by up to
  $4.57\times10^{-6}$ relative (`out/thread_probe.jsonl`). The difference stencil's largest relative eigenvalue error
  then reads $3.8\times10^{-7}$ and $2.3\times10^{-6}$, against $1.25\times10^{-6}$ at 32 threads. That figure is
  therefore not resolved above the eigensolver's own rounding (note for T21, T22, T33 and the response).
* Spill coverage of each GPU job starts at its first complete counter sample, after the CUDA context and a
  one-element array exist; see "GPU jobs".

## Fix round (checker's six points)

1. **Workspace inventories.** Recounted from the cited implementations, temporaries included, and checked against
   measured peaks of those implementations at $k=64$ and $128$ (run3_fix). The capacity figures changed: GMRES
   $m\le32$ (was 38), library LOBPCG $b\le2$ (unchanged), planned in-place eigensolver $b\le3$ (was 4; the second
   fix round restores 4, see below).
2. **Atomic-kernel repeat ranges.** All nine repeat-versus-main comparisons are now reported (731–978 entries); the
   earlier 810–932 used only the first repeat. The within-process range 459–735 is unchanged.
3. **Coefficient emulation counts.** S22, on which the orders were identified (258,750), is separated from the
   layouts that were not used for identification (458,874 in the main run; 480,114 with the roller layout).
4. **GPU coverage.** Stated as from the first complete sample after the context and the one-element array, with the
   growth measured from that baseline ("GPU jobs").
5. **Per-component masks.** `t20_common.free_mask` now reads bit $c$ of the node mask as DOF $3n+c$, as
   `voxfem.core.Problem.fixed_dof_mask` does, and `FreeOperator` uses it. CPU test (`mask_test.json`, passed): equal to
   the production rule for all eight mask values, the roller layout and the production bridge; mask 6 leaves $x$
   free; on the five earlier layouts (masks 0 and 7 only) the new rule equals the old one, so their results stand.
   GPU test: the six operators on the roller layout pass every action, dot, matrix and eigenvalue test.
6. **Gate.** `small_grid_gate_passed` now includes `s22_gate`; `gate_test.json` (passed) shows the saved results
   pass and each of six planted S22 faults fails the gate.

## Second fix round (checker's three points; CPU only, `t20_workspace.py` rerun)

1. **In-place eigensolver count.** The operator's masked input copy belongs to its $10b+3$ vectors and is no longer
   added again. At $k=128$, $b=4$ the planned estimate is 20,856,283,220 B, including the small-array bound, under
   the 20,993,540,096 B allowance, so the planned largest block is 4 (was 3). Actual capacity is unmeasured.
2. **GMRES restart.** The search now counts the $(m+1)\times m$ Hessenberg matrix and the two short vectors, and
   stops at CuPy's cap $m\le n$. The exported $k=16$ restart is 19,400 (was 22,766), and the $k=8$ restart is the
   cap $n=15{,}795$ (was 161,301, above the system dimension).
3. **LOBPCG block.** The search now counts the quadratic Rayleigh–Ritz arrays and the per-iteration histories, and
   stays on the iterative path ($5b\le n$). Each maximum states whether it lies within the measured blocks (3, 6) and
   whether the path limit sets it. The $k=8$ maximum is 2,585 (was 10,754, which lay in CuPy's dense path). Values
   above the measured parameters are labelled as extrapolations, not admission figures.

The inventory checks against the measured library workspaces still hold with the source-counted small arrays
(`inventory_checks`, all true). No other result changed. The previous `workspace.json` is kept as
`out/workspace_before_fix_r2.json`.

## Third fix round (operator's two corrections of 2026-11-24; CPU only, no GPU job)

1. **Form of the S22 gate.** This is the operator's correction of the gate's form, decided from this task's own
   criterion.
   * The bit-for-bit check of the stencil columns stays exact, and so do the symmetry error and the identities.
   * The derived eigensolver figures of the six deterministic kernels ($\lambda_{\min}$, the maximum and the ten
     lowest relative eigenvalue errors) are now compared with E29's values under the 1 % relative tolerance of the
     task's eigenvalue comparisons, not by exact equality. The thread order changes them: the checker's example is
     $5.57677303\times10^{-11}$ against $5.57674753\times10^{-11}$, a relative difference of $4.57\times10^{-6}$.
   * The CPU probe `out/thread_probe.py` reproduces that difference. It recomputes the stencil kernels' figures from
     the saved basis columns with 1, 4 and 32 OpenBLAS threads (`out/thread_probe.jsonl`):
     * 4 threads give the stencil's $\lambda_{\min}$ $5.576773\times10^{-11}$, $4.57\times10^{-6}$ from E29;
     * 32 threads give E29's values exactly;
     * the symmetry and matrix errors are the same at every thread count.
   * Each derived difference is reported with its tolerance and result in `adjoint_checks.json` →
     `s22_gate.derived_differences`. In the saved records all are 0 and within tolerance, and the gate passes.
   * `t20_regate.py` re-forms the gate from the saved records and recomputes no value. It asserts that only
     `s22_gate` differs from the previous file, which is kept as `out/adjoint_checks_before_fix_r3.json`.
     `small_grid_gate_passed` stays true.
   * `gate_test.json` (passed; the previous one is kept as `out/gate_test_before_fix_r3.json`):
     * the saved results pass;
     * each of nine planted faults fails the gate: different basis columns, $\lambda_{\min}$ off by 2 %, eigenvalue
       errors off by 0.02 $\lambda_K$ (maximum, ten lowest), matrix error, symmetry error, identity, and the negative
       counts of a deterministic kernel and of an atomic kernel;
     * the checker's example and the 1-, 4- and 32-thread probe values pass.
2. **Workspace: both endpoints of the measured range.** `t20_workspace.py` now checks both endpoints. A maximum
   below the smallest measured parameter is labelled a downward extrapolation (`relation_to_measured_range`,
   `within_measured_range` false), and `*_within_measured_range` is null there. The only such maximum is the $k=128$
   library LOBPCG block $b=2$ (measured blocks 3 and 6). Its estimate stays 2. Rerun output against
   `out/workspace_before_fix_r3.json`:
   * no estimate, byte count or other maximum changed;
   * that row's label changed;
   * every library maximum gained its `relation_to_measured_range` (above the range at every other $k$);
   * the wording of one note and of the `basis` fields changed.

## Files

* Code:
  * `t20_common.py`: layouts and exact FP32 rounding;
  * `t20_ops.py`: GPU operators;
  * `t20_cpu.py`: CPU assembly and coefficient emulation;
  * `t20_gpu.py`: GPU job; `t20_gpu_fix.py`: GPU job of the fix round (roller layout, solve memory);
  * `t20_launch.py`: guarded launcher;
  * `t20_analyse.py`, `t20_workspace.py`: analysis;
  * `t20_mask_test.py`, `t20_gate_test.py`: CPU tests of the fix rounds;
  * `t20_regate.py`: re-forms the S22 gate from the saved records (third fix round);
  * `out/thread_probe.py`: CPU probe of the thread-order dependence of the S22 eigenvalue figures.
* `src/voxfem`: the authors' code, copied unchanged.
* `out/run1`, `out/run2_repeat`, `out/run3_fix`: raw GPU outputs, monitor records, and the PTX and source of the generated kernels.
