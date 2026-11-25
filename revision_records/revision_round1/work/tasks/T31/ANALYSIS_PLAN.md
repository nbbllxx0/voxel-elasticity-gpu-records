# T31 analysis plan: four-load bracket optimization with the repaired mixed-precision path (serves R1.4)

This plan is frozen before any T31 job runs. Nothing in `tasks/T31/` exists except this file. No T31 outcome has
been computed or read. Any departure from it is recorded in `tasks/T31/DEVIATIONS.md`, with the reason. This file is
never edited.

## 1. Question

Can the authors' repaired mixed-precision path complete a multi-load stiffness design on a realistic, non-box
geometry? The path is the difference-form FP32 stencil (`stencil_diff`), FP32 V-cycle-PCG corrections, and FP64
iterative refinement accepted on the FP64 true residual ≤ 1e-5 per load case. The geometry is T30's lifting-bracket
counterpart, with four independent load cases. Each retained design must meet:
- the prescribed volume;
- the prescribed stopping rule;
- four final FP64 equilibrium checks at ≤ 1e-8.

The second question is what the original stencil (`stencil`) does on the same problem. It starts from the same initial
state, with the same timing and peak-memory boundaries, at the first production size.

The study is a demonstration and an audited comparison. The design is a stiffness design, not a stress-qualified
engineering part. No statistical inference is made: every run is a single deterministic optimization (uniform
initial field, no random numbers), so there is no power calculation. The thresholds below are decision rules for
single runs.

## 2. Material reused and data roles

**Code (copied from `tasks/T30`, unchanged).** These files are copied into `tasks/T31/` and their SHA-256 values
recorded in `tasks/T31/code_hashes.json`:
- `t30_common.py`: geometry, element classes, supports, the RBE3 load transfer, host checks, multigrid box;
- `t30_driver.py`: `MultiSIMP` and the masked filter;
- `t30_cpu.py`;
- the launcher `t30_launch.py` and its self-test `t30_launch_selftest.py`;
- `src/voxfem`: the unchanged copy of the authors' package.

New T31 code goes into new files only:
- `t31_job.py`: the job phases of section 4;
- `t31_analyse.py`: CPU only; it reads the job outputs and writes `out/summary.json`;
- `t31_figdata.py`: CPU only; it writes the figure data.

The driver, the geometry and the voxfem copy are not modified. Per-iteration persistence uses the driver's `on_iter`
hook.

**Development data (open, used for planning only).**
- **T30's outputs** (`tasks/T30/out/spec.json`, `acceptance_rules.json`, `host_checks_*.json`, `workspace.json`,
  `gate.json`, `runs/*`). They give:
  - the geometry and load cases;
  - the element counts per size;
  - the correctness gate at n = 96;
  - one production design iteration at n = 96, 192, 384 and 576, with memory and time;
  - the workspace model: pool peak = 254.5 B × N_alloc + 216 MB, plus about 330 MB of context and other process
    memory.
- **The authors' production configuration** of the E32 optimizations (`results/E32/*.json`, field `config`).

No complete bracket optimization exists anywhere: T30 ran single iterations only.

**Sealed data.** These are every output of the T31 jobs of section 4:
- the optimization histories;
- the retained designs;
- the tight re-solves;
- the comparison;
- the measured memory and time of complete runs.

None of these exists when this plan is frozen. None is computed before the plan's hash is recorded.

**Element counts** (`tasks/T30/out/host_checks_*.json`; fixed by the geometry, not outcomes). "Box" is the allocated
grid of n × (2n/3) × (5n/12) elements.

| n (cells along x, 7.2 in) | allocated (box) | active | designable | protected | free DOFs |
|---|---|---|---|---|---|
| 96 | 245,760 | 113,318 | 104,070 | 9,248 | 372,687 |
| 192 | 1,966,080 | 903,548 | 827,324 | 76,224 | 2,839,977 |
| 384 | 15,728,640 | 7,232,600 | 6,629,528 | 603,072 | 22,214,871 |

Each job's host checks recompute these counts. The report takes them from the job outputs, not from this table.

## 3. Frozen problem and optimizer settings

**Geometry, supports, loads.** Exactly T30's (`out/spec.json`):
- the bracket counterpart, with protected bolt bosses and lug eyes (class 2) and exterior voids (class 0);
- four rigid bolted interfaces;
- four load cases about C = (6.0, 2.25, 2.1) in, each transferred by the equal-weight RBE3 coupling to the pin-bore
  nodes and solved as an independent state:
  - LC1: 8,000 lbf up;
  - LC2: 8,500 lbf outward;
  - LC3: 9,500 lbf at 42° in the x–z plane;
  - LC4: a 5,000 lbf·in couple about x.

**Material.**
- The authors' trilinear hexahedron, ν = 0.3, E0 = 1, Emin = 1e-9, SIMP modulus.
- Exterior elements have modulus 0, and their nodes are eliminated by the multigrid zero-diagonal rule.

**Objective.**
- J = Σ_k ¼ · c_k / c0_k over the four load cases.
- c0_k is the compliance of the fully solid bracket:
  - every designable element has ρ_phys = 1;
  - protected elements have ρ_phys = 1;
  - exterior elements have ρ_phys = 0.
- c0_k is computed once per grid size in the reference job (section 4, phase C0) by FP64 PCG with the FP32 V-cycle
  (`mg64`, `stencil_diff` fine level), from zero, to FP64 true residual ≤ 1e-8.
- The four FP64 values are written to `out/c0_n{n}.json`. Every optimization at that size reads them from this file,
  so the original-stencil and repaired runs optimize the identical objective.

**Volume.** The constraint is mean ρ_phys over designable elements = 0.5 (`volfrac = 0.5`; author decision (5)).

**Physical filter length.** The authors' continuation schedule gives the radius in cells of the n = 96 grid. It is
applied at every size with `rmin_scale = n/96`, as in T30's memory jobs. The physical cone radius is therefore
r(it) = r_96(it) × 0.075 in, independent of n:

| design iterations | penalty p | projection β | move | r_96 (cells at n = 96) | physical radius (in) |
|---|---|---|---|---|---|
| 1–15 | 1.5 | 1 | 0.20 | 1.50 | 0.1125 |
| 16–40 | 3.5 | 4 | 0.15 | 1.35 | 0.10125 |
| 41–65 | 4.5 | 16 | 0.08 | 1.25 | 0.09375 |
| 66 onward | 4.5 | 32 | 0.05 | 1.20 | 0.09 |

At n = 192 the radius is 3.0 → 2.4 cells, and at n = 384 it is 6.0 → 4.8 cells.

**Other settings.** All other settings are the authors' E32 production configuration (`voxfem.simp.Config`
defaults):
- `eta = 0.5`, `rho_lb = 0`;
- `tol = 1e-5`, `inner_tol = 0.1`, `inner_maxit = 300`;
- `mg_nu = 2`, `mg_omega = None`, `max_coarse_dofs = 2500`, `op64 = node_hoist`;
- `max_outer = 300`, `min_outer = 0`;
- `conv_drho = 0.01`, `conv_dc_rel = 1e-4`, `conv_window = 10`, `conv_moving_ppm = 1.0`;
- `spill_check_every = 10`.

States:
- four stored FP64 states, warm-started from the previous design iteration (`store_states = True`);
- weights ¼ each.

**Initial state.** The design variable is 0.5 on designable elements, 1 on protected and 0 on exterior elements. The
displacements start at zero, and there is no OC multiplier yet. This is identical for every run at a given size.

**Stopping rule (the authors' rule, unchanged).**
- **Earliest test.** The stopping tests apply only in the last continuation phase and only after design iteration
  65 + 10 = 75. Iteration 76 is the earliest possible stop.
- **Max-change stop.** The run stops with termination `max_change` when both hold:
  - the relative spread of J over the last 10 iterations is ≤ 1e-4;
  - max |Δρ_phys| ≤ 0.01.
- **Bounded-oscillation stop.** The run stops with `bounded_oscillation` when both hold:
  - the spread is ≤ 1e-4;
  - at most max(1, 1 ppm of active elements) elements still change by more than 0.01.
- **Guard.** A run that reaches 300 design iterations is not converged.
- **Retained design.** The retained design is the final iterate, re-solved once more by the production path after
  the last update (`MultiSIMP.run`).

**Solver configurations.**
- **R (repaired, production):** `solver = mg_ir`, `op32 = stencil_diff`, used both in the IR corrections and as the
  V-cycle fine level.
- **O (original stencil):** identical except `op32 = stencil` in both places. This is the authors' original
  configuration.

## 4. Procedure

**Before the first GPU job.**
1. Run the launcher self-test and record it in `out/launch_selftest.json`. If it fails, stop and launch no GPU job.
2. Write `code_hashes.json`.
3. Run the CPU host checks at n = 96, 192 and 384 (`out/host_checks_{n}.json`). The study proceeds only if each
   passes T30's rule:
   - resultants within 1e-10;
   - symmetric load set;
   - one connected component;
   - padding exterior only.

**Guard and admission (every GPU job).** The authors' GPU-memory rule of 2026-11-23 applies through T30's guarded
launcher:
- **One job at a time.** One GPU job runs at a time, under an atomic lock.
- **Admission.** A job is admitted when its predicted process peak plus 1.5 GiB fits in the driver-reported free
  memory at launch:
  - the prediction is 1.05 × (254.5 B × N_alloc + 216 MB) + 330 MB;
  - for the audit and reference jobs, the prediction is the same model with the FP64 PCG workspace in place of the IR
    workspace (+3 × 8 B and +2 × 4 B per DOF);
  - `guard.require_budget`'s answer and the other processes' usage are recorded beside the admission, for
    information.
- **Pool cap.** The CuPy pool is capped at the driver's free memory less 1.5 GiB.
- **Spill sampler.** It stops the job and marks it refused for memory when shared usage grows more than 256 MiB above
  its start.
- **Consequences.**
  - A spill or an allocation failure is a refusal, not a result.
  - No result at that size is kept or rerun.
  - A size whose prediction does not fit is not launched, and the refusal is recorded.

**Job order.** Each job writes `out/runs/<job>/` with:
- `monitor.json`: admission, watch, coverage;
- `gpu_meta.json`: results and timings;
- `history.json`: rewritten after every design iteration, so a failed run keeps its history;
- `fields.npz`, where named below.

| # | job | content |
|---|---|---|
| 1 | `c0_n192` | Phase C0 at n = 192: the four fully solid tight solves, giving `out/c0_n192.json` and their work (iterations, time, pool peak) |
| 2 | `R_n192` | Phase OPT, configuration R, n = 192 (**primary run**) |
| 3 | `A_R_n192` | Phase AUDIT of R_n192's retained design |
| 4 | `O_n192` | Phase OPT, configuration O, n = 192 (original-stencil comparison) |
| 5 | `A_O_n192` | Phase AUDIT of O_n192's retained design (only if O_n192 returned a design) |
| 6 | `c0_n384` | Phase C0 at n = 384 (only if admitted) |
| 7 | `R_n384` | Phase OPT, configuration R, n = 384 (only if admitted) |
| 8 | `A_R_n384` | Phase AUDIT of R_n384's retained design |

**Fallback.** If n = 192 is refused for memory, run jobs 1–3 at n = 96 instead and report them at their actual
resolution. This is the acceptance's coarse fallback, and it is not expected (T30 measured 0.71 GB at n = 192). An
n = 96 run is not made otherwise.

R_n384 runs whatever R_n192's outcome is, when admitted and within budget, and is reported under its own label. The
original stencil is compared at n = 192 only.

**Phase OPT** (timing and memory boundaries identical for R and O):
1. Build the geometry and run the host checks.
2. Read `out/c0_n{n}.json`.
3. **Memory boundary.** Install the pool-peak hook (reserved and used high-water marks, taken at every allocation),
   then construct `MultiSIMP`. The pool-peak boundary runs from here until `run()` returns.
4. Record the SHA-256 of three arrays, which must be identical between R_n192 and O_n192. This is the
   matching-initial-state check:
   - the initial design variable;
   - the iteration-1 physical density;
   - the iteration-1 FP32 moduli (taken in `on_iter` at iteration 1).
5. **Timing boundary.** Call `run(on_iter=...)`. The optimization time is the wall time from entering `run()` to its
   return. It includes every design iteration (multigrid rebuilds, state solves, sensitivities, filter, OC) and the
   final production re-solve. It excludes:
   - driver construction;
   - reading c0;
   - I/O after return;
   - every tight solve.

   The driver's per-iteration times and per-solve statistics are recorded: outer and inner iterations, achieved FP64
   true residual, wall time, setup time.
6. **On normal return,** save:
   - `fields.npz`: the element classes (uint8), the final design variable ρ and the final physical density ρ_phys
     (float32, native resolution);
   - the SHA-256 of the final FP32 moduli;
   - the final production compliances;
   - termination, iterations, volume, MND;
   - the totals and the memory record.
7. **On a solve failure** (`SolveFailed` from the production path, i.e. a load case that cannot reach 1e-5), record:
   - the design iteration, the load case and the message;
   - the continuation phase;
   - the history up to that point.

   The run has then stopped without a design. It is not restarted and not given other settings.

**Phase AUDIT (tight audit work, measured separately; one job per retained design).**
1. Load `fields.npz` and rebuild the moduli from the saved ρ_phys with the driver's modulus kernel and the class mask,
   at the final continuation step's penalty.
2. Require the SHA-256 of the rebuilt FP32 moduli to equal the value saved by the OPT job. If it does not, the audit
   is invalid and is recorded as such.
3. Require the device's fixed set after the multigrid update to equal supports ∪ exterior-only nodes, as in T30.
4. For each load case k = 1..4, solve from zero by `mg64` (FP64 PCG, FP32 V-cycle with the `stencil_diff` fine
   level, `pcg_maxit = 20000`) to an FP64 true residual ≤ 1e-8.
   - If `mg64` raises `SolveFailed`, solve once more from zero by `mg_ir` (`stencil_diff`) with `tol = 1e-8`.
   - Each case records which solver produced the state, its iterations and its time.
5. **Equilibrium check, per load case.** The relative residual ‖b_k − K u_k‖₂ / ‖b_k‖₂ over the free DOFs is
   recomputed after the solve with the FP64 `node_hoist` operator. That operator matched the CPU-assembled FP64
   matrix to 7.6e-16 in T30. Check k passes when this value is ≤ 1e-8.
6. **Informational checks** (they do not enter the gate):
   - At n ≤ 192 the same residual is also recomputed in the CPU-assembled FP64 matrix (`t30_cpu.assemble`). If the
     host cannot assemble it, that is recorded as not done.
   - The support reactions (K u at the clamped DOFs) are summed with the applied loads to the force and moment
     resultants about C.
7. **Recorded endpoints:**
   - the tight compliances c_k^tight and J^tight;
   - the relative differences |c_k^prod − c_k^tight| / c_k^tight;
   - per-case iterations and wall time;
   - total audit time (four solves plus the multigrid setup);
   - the audit job's pool peak.

**Phase C0.** As in the AUDIT steps 3–5, on the fully solid field. It writes the four c0_k values with their achieved
residuals; each must be ≤ 1e-8. If one fails, no optimization at that size is launched.

**Figure data** (`t31_figdata.py`, CPU only). This step writes `out/figdata_n{n}.npz` and a JSON sidecar for every
retained design:
- element classes and the final ρ_phys;
- clamped-node coordinates;
- pin-bore node coordinates;
- C and the four (F, M) vectors;
- the frame.

The figure itself is drawn by the figure maker, so T31's `figure_files` stays empty.

**Analysis** (`t31_analyse.py`, CPU only). It reads only the job outputs above and writes `out/summary.json` and the
tables of `REPORT.md`. Every reported number names its source file.

## 5. Endpoints

**Primary endpoint (E1), per retained R design.** A design passes ("complete four-load design") when all of the
following hold:
- (a) the run returned a design with termination `max_change` or `bounded_oscillation` (not the 300-iteration
  guard);
- (b) |V − 0.5| ≤ 1e-4 for the retained design's volume over designable elements;
- (c) every production solve of the run met the FP64 true residual ≤ 1e-5;
- (d) all four AUDIT equilibrium checks pass (≤ 1e-8) and the AUDIT job is valid (moduli hash and fixed set
  match);
- (e) no spill and no allocation failure in its OPT and AUDIT jobs, with the launcher's coverage complete from its
  first sample.

**Secondary endpoints (reported for every run that returned a design).**
- **S1, production accuracy.** The largest |c_k^prod − c_k^tight| / c_k^tight over the four cases.
  - Prediction: ≤ 1e-4.
  - T30 measured at most 2.9e-7 against a direct solve at n = 96, and the paper's audited states stayed below
    2.1e-6.
- **S2, memory model over a complete run.** The R runs' pool peak against T30's model (254.5 B × N_alloc +
  216 MB). Prediction: within ±5 %.
- **S3, cost (descriptive).** For each run:
  - the optimization time and the time of iterations 2 to the end;
  - per-iteration median;
  - the totals for solve, setup, sensitivity, OC and filter;
  - the summed outer and inner IR iterations per load case;
  - pool peak and sampled process-dedicated peak;
  - bytes per allocated and per active element;
  - the tight audit work (iterations, time, pool peak) separately;
  - the C0 work.

  No runtime prediction is made.
- **S4, design description.** For each run:
  - final J^tight and c_k^tight;
  - c_k^tight / c0_k;
  - iterations and termination;
  - MND;
  - the solid fraction over active elements;
  - per-iteration histories of J, every c_k, volume, MND and max |Δρ_phys|.

**Comparison endpoints (O_n192 against R_n192).**
- **C1, outcome category of O_n192** (exactly one):
  - `completed-verified`: the run passes E1 (a)–(e) itself;
  - `completed-unverified`: the run returned a design but fails (b) or (d);
  - `not-converged`: it reached the 300-iteration guard;
  - `solve-failure at iteration i, load case k`: no design;
  - `refused`: a spill or allocation failure.
- **C2, matching-state check.** Whether the three initial-state hashes of section 4 are identical. If they are not,
  the comparison is invalid. This is recorded, and C3–C5 are not interpreted.
- **C3, design outcome (only when both runs return designs).**
  - |J^tight_O − J^tight_R| / J^tight_R, and the same per load case;
  - the two iteration counts and terminations;
  - the mean |Δρ_phys| over designable elements;
  - the fraction of designable elements with |Δρ_phys| > 0.5.
- **C4, cost ratios O/R (only when both runs return designs).** Each ratio is given beside its two values:
  - optimization time;
  - time of iterations 2 to the end;
  - median iteration time;
  - median solve time per load case;
  - pool peak.
- **C5, path divergence.** The first design iteration at which the two runs' J differ by more than 1e-6 relative.
  - If O fails, the history up to the failure is given against R's at the same iterations.
  - For a failure, the message, the phase (p, β) and the last accepted residuals are given.

## 6. Thresholds and decision rules

**H1 (primary; n = 192):**
- **Supported** when R_n192 passes E1.
- **Contradicted** when R_n192 ends in a production solve failure, or returns a design whose AUDIT equilibrium check
  fails for a valid audit job. Either is a correctness failure of the repaired path on this application. The
  application is then reported as unresolved at that size, and R1.4 stays outstanding unless another size passes.
- **Inconclusive** in the remaining cases:
  - R_n192 reaches the 300-iteration guard;
  - it fails (b);
  - it is refused for memory;
  - its run or audit is invalid for a reason outside the method (for example a launcher or host fault, or a moduli
    hash mismatch from a bookkeeping error);
  - the budget ends before it completes.

  An infrastructure failure may be rerun once at the same size. The rerun is recorded in DEVIATIONS.md; spills and
  allocation failures are never rerun.

**H2 (extension; n = 384).** The same rule for R_n384. If R_n384 is not admitted or not reached within the budget, H2
is "not run". That is not a failure of the task; the largest completed size is reported as the demonstrated result.

**Application status for R1.4.**
- **Resolved (supported)** when at least one R design (n = 192, n = 384, or the n = 96 fallback if it was needed)
  passes E1. The size of each such design, with its active, designable and allocated counts, is reported.
- **Unresolved** when H1 is contradicted and no other R design passes.
- **Inconclusive** otherwise.

**S1.**
- Holds when the largest production-to-tight compliance difference is ≤ 1e-4 for every R design that passes E1.
- If it exceeds 1e-4, this is reported as a contradiction of S1. It does not change H1.

**S2.**
- Holds when |pool peak / model − 1| ≤ 0.05 for each R run that returned a design.
- Otherwise it is reported as not holding, with the ratio. It does not change H1.

**Original stencil (no directional hypothesis).** C1's category is reported whatever it is. When both runs are
`completed-verified`:
- **Equal design outcome** is stated only when |ΔJ^tight| / J^tight_R ≤ 1e-4, the optimizer's own stopping
  resolution on J.
- **Otherwise** the difference is reported as a different design outcome. The plan does not attribute it to the
  operator beyond what C5 shows.

When O ends without a verified design and R passes, the report states that the original stencil did not complete
this problem at n = 192 and how it ended.

**Cost ratios (C4).**
- These are single runs, and the authors' repeated optimizations lay within 2.2 % of each other.
- A time ratio within [0.95, 1.05] is reported as no difference measurable at single-run resolution.
- Outside that band the ratio is reported as measured, with the iteration counts beside it. When the two runs take
  different numbers of design iterations, the per-iteration and per-solve ratios are the comparable figures.

**Interference.** Timings are taken on a shared display card. The launcher records other processes' GPU memory at
admission. No activity-exclusion rule is applied, and no claim is made that no other GPU activity occurred.

## 7. Stopping rule of the study

**Budget.** T31's compute budget is 10 h of wall clock, counted from its first GPU job, and no job starts after
2026-11-26 18:00.
- Jobs run in the order of section 4, one at a time.
- When the budget is reached, no new job starts; a running job is finished or stopped between jobs.
- The completed part is reported, and the sizes and jobs not run are named.
- Reruns that change no reported number are not made.

**Per-run limits.** Each OPT run is bounded by the 300-iteration guard. AUDIT solves are bounded by `pcg_maxit` and
by the IR fallback's own limit.

**Stops on failure.**
- **Self-test.** A failing launcher self-test stops all GPU work.
- **c0.** A failing C0 check stops the optimizations at that size.
- **Spill.** A spill stops the job and refuses the size.

## 8. Outputs

All outputs are written in `tasks/T31/`:
- `ANALYSIS_PLAN.md` (this file), `DEVIATIONS.md`, `REPORT.md`, `code_hashes.json`;
- `out/launch_selftest.json`, `out/host_checks_{n}.json`, `out/c0_n{n}.json`;
- `out/runs/<job>/{monitor.json, gpu_meta.json, history.json, fields.npz}`;
- `out/figdata_n{n}.npz` and `.json`;
- `out/summary.json`.

Every number in REPORT.md comes from one of these files and names it.

No language model is called.
