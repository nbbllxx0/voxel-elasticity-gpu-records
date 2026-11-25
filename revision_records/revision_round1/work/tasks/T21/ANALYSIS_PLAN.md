# T21 analysis plan: clamped beam with a fixed 8:1 interface, k = 8–64 (k = 128 extension)

Serves R1.3, R3.1 and R3.2 (Reviewer 3's point (1b), and (1a) where the corner and difference results bear on it).
This plan is written and frozen before any T21 computation. No solve, no operator application and no memory
measurement has been run on any T21 grid (k = 8, 16, 32, 64, 128) in either layout. The study calls no language
model, so the rule on model identifiers does not apply.

Data inspected for planning (all already open, none produced by T21):
* `results/E29/beam_controls.json` (uniform beam, k = 8–128: FP64 references at relative true residual
  1.9–5.3×10⁻⁹, FP32 controls with own and common V-cycles, rounded-coefficient PCG solves of the original stencil
  and the difference form at 10⁻⁸), `results/E29/beam_conditioning.json` (λmin, λmax of the uniform FP64 operator,
  k = 8–64), the submitted Table 5 (`input/manuscript/tables/tab_beam_controls.tex`) and the text of Sec. 3.2 and 5.2.
* `results/E8/*.json` (independent reference residuals reached by the authors' reference procedure on other
  problems, 8.9×10⁻¹¹ to 8.3×10⁻¹⁰).
* T19 (`tasks/T19/REPORT.md`, `summary.json`): patch-level coefficient and FP32 excesses, including the 8:1 interface.
* T20 (`tasks/T20/REPORT.md`, `workspace.json`, `small_spectrum.csv`): the FP64 operators of the rounded forms,
  their verification on the k = 4 beam layouts, and the workspace of every solver used here.

## 1. Question

**Primary (R3.2, (1b)).** On the clamped 8×1×1 beam with a transverse material interface at x = 4 (E = 1 to the
left, E = 1/8 to the right), do the two repaired evaluations, the element kernel with a mean reference and the
stencil difference form, keep the compliance error caused by coefficient rounding bounded and free of growth under
refinement over k = 8, 16, 32, 64, as they do on the uniform beam?

**Secondary.**
* (S-a, R3.1) Does the corner reference show the coherent growth of about a factor 2 per halving of h that the
  reference-change identity predicts (T19), at both layouts?
* (S-b) Does the original stencil keep its coefficient-rounding failure at the interface?
* (S-c) Do the FP32 controls of the four forms with the common V-cycle, stopped at the first recursive 10⁻⁵ pass,
  keep the repaired forms' compliance error small at the interface; and where the coefficient bias is resolved,
  how does the control's signed error split into coefficient bias and the rest?
* (S-d) How do interface and uniform results compare on the same grid?

**Extension.** k = 128, both layouts, with the same procedure, subject to admission and to the full reference gate.
Its failure or refusal does not leave the primary question unanswered.

## 2. Problem (frozen)

| item | definition |
|---|---|
| geometry, mesh | beam [0,8]×[0,1]×[0,1]; `Grid(8k, k, k)` of unit-cube voxels of size h = 1/k; k ∈ {8, 16, 32, 64}; extension k = 128 |
| element | trilinear hexahedron, `ke_unit(0.3)` (Poisson ratio 0.3), as in E28/E29 |
| constraint | every node on x = 0 fixed in all three components (node mask 7), `E28_verification.slender(k)` |
| load | consistent unit transverse end traction on x = 8: y-force −w/Σw at each face node, w = 1 interior, 1/2 edge, 1/4 corner (total −1), `E28_verification.slender(k)` |
| layout `uniform` | E = 1 in every cell |
| layout `interface` | E = 1 for cells whose centre has x < 4, E = 1/8 for cells whose centre has x > 4 (`t20_common.beam_moduli(k, "interface")`); the interface is the node plane x = 4 at every k |
| moduli storage | one FP32 array per (k, layout) (0.125 is exact in FP32), used unchanged by every operator, solve and V-cycle of that grid; checked byte for byte across all phases of the job |
| compliance | C(u) = 2k·fᵀu (f the load vector, u on the grid), the scaling of E29 and Table 5 |
| relative residual | ρ_A(u) = ‖f − A u‖₂ / ‖f‖₂ on the free DOFs (fixed DOFs zeroed), FP64 |
| energy norm | ‖v‖_K0 = (vᵀK0 v)^½ with the FP64 reference operator K0 |

## 3. Operators and solves

### 3.1 Operators (all on the free DOFs, FP32-stored moduli)

| name | role | implementation |
|---|---|---|
| K0 | reference operator | production FP64 node kernel `node_hoist` (T20 `FreeOperator` form `ref`), the operator of E29's references |
| K0-ind | independent residual check of K0 | new element-by-element FP64 CuPy evaluation written for T21 (gather the 24 element DOFs, multiply by `ke_unit(0.3)` in FP64 and the cell modulus, scatter-add), in slabs of cells; validated per §10 |
| A_stencil | original stencil, rounded coefficients applied in FP64 | T20 `FreeOperator` form `stencil` (`stencil_c32`) |
| A_corner | element kernel with corner reference, Q = fl32(K_e), FP64 arithmetic | T20 form `corner` |
| A_mean | element kernel with mean reference, FP64 arithmetic | T20 form `mean` |
| A_diff | stencil difference form, rounded coefficients applied in FP64 | T20 form `diff` (`stencil_diff_c32`) |
| FP32 operators | measured FP32 actions in the controls | production kernels `stencil`, `elem_ref`, `elem_mean`, `stencil_diff` (FP32) |
| common V-cycle | preconditioner of every solve | `GMG(grid, fixed, ke, fine_variant="stencil")`, `update(E32)` on the grid's moduli, as E29's common V-cycle; used through `CastPrecond` for FP64 solves |

The authors' code is used from a copy in `tasks/T21/src` (voxfem as copied in T20; `E8_precision_floor.py`,
`E28_verification.py`, `E29_review.py`; T20's `t20_common.py`, `t20_ops.py`, `t20_launch.py`). No authors' file is
changed; T21 functions that extend a copied function are new functions in T21 files.

### 3.2 Reference solve (per k and layout)

1. **Target solve.** FP64 PCG `krylov.pcg64` on K0 with the common V-cycle, x0 = 0, internal tolerance 5×10⁻¹⁰,
   true-residual replacement every 50 iterations, at most 20,000 iterations. Result u_ref; its residual is evaluated
   afterwards with K0-ind (gate value) and with K0 (reported beside it).
2. **Tightened solve.** The same solver warm-started from u_ref, tolerance 10⁻¹¹, at most 20,000 further
   iterations; on reaching the cap the final iterate is kept. Result u_ref⁺ with its K0-ind residual.
3. **Reference gate G-ref (k, layout):** ρ_K0-ind(u_ref) ≤ 10⁻⁹ and an established reference uncertainty (§6).

### 3.3 Rounded-coefficient solves (per k, layout and form F ∈ {stencil, corner, mean, diff})

1. **Symmetry test.** s_F = max over three seeded pairs of random free-DOF vectors (x, y) of
   |xᵀA_F y − yᵀA_F x| / (|xᵀA_F y| + |yᵀA_F x|). A_F counts as *verified symmetric* if s_F ≤ 10⁻¹².
   (T20 found the mean form symmetric to FP64 assembly rounding, the stencil forms symmetric on the uniform beam and
   skew at the interface, and the corner form skew on every grid; the test is repeated here on every grid.)
2. **PCG diagnostic (logged separately, never the result).** E29's `pcg_energy` (copy) on A_F with the common
   V-cycle, x0 = 0, tolerance 5×10⁻¹⁰, replacement every 50 iterations, at most 20,000 iterations. It records the
   smallest search-direction energy ratio pᵀA_F p / pᵀK0 p, and the iteration and ratio of the first direction with
   pᵀA_F p ≤ 0, at which it stops. A_F is *verified symmetric indefinite* if it is verified symmetric and the
   diagnostic met a direction with pᵀA_F p ≤ 0. The diagnostic's iterate is not used.
3. **Primary solve: residual-checked GMRES with FP64 defect correction (GMRES-DC), for every A_F.**
   Outer loop in FP64: r_j = f − A_F u_j; inner solve A_F d = r_j with `cupyx.scipy.sparse.linalg.gmres`,
   right-preconditioned by the common V-cycle, restart m = 20, inner relative tolerance 10⁻², at most 400 inner
   iterations; u_{j+1} = u_j + d. x0 = 0. The target iterate u_F is the first outer iterate with
   ρ_A_F ≤ 5×10⁻¹⁰; the run then continues to the tightened iterate u_F⁺ at ρ_A_F ≤ 10⁻¹¹. Caps: 60 outer steps;
   stop on stagnation (5 consecutive outer steps without a new smallest residual). On a cap or stagnation the iterate
   with the smallest residual is kept and the solve is marked failed for that level. (Restart 20 lies within T20's
   measured range at k = 32, 64 and its workspace estimate holds to k = 128; the outer correction makes the result
   independent of the FP32 V-cycle's rounding, which a single library GMRES call is not.)
4. **MINRES with defect correction (MINRES-DC), for verified symmetric indefinite A_F only.** The same outer loop
   with `cupyx.scipy.sparse.linalg.minres` as inner solver (common V-cycle, inner tolerance 10⁻², at most 400 inner
   iterations), same targets and caps, x0 = 0.
5. **Result selection (fixed).** The GMRES-DC iterate is the result if it passes G-coef. If it fails and MINRES-DC
   ran and passes, the MINRES-DC iterate is the result. If both ran and pass, GMRES-DC is the result and the
   K0-energy distance between the two is reported as a cross-check. If none passes: coefficient solve failed; the
   smallest-residual iterate is reported with that label and enters no test.
6. **Coefficient gate G-coef (k, layout, F):** ρ_A_F(u_F) ≤ 10⁻⁹, recomputed after the solve, and an established
   coefficient uncertainty (§6).

### 3.4 FP32 controls (per k, layout and form; three repeats each)

E8's `pcg32` in mode `mg32_x64` (FP32 Krylov and V-cycle, FP64 iterate), copied, with the common V-cycle, the FP32
operator of the form, x0 = 0, check every iteration, at most 400 iterations, exactly as E29 runs it, with one
extension that leaves the iteration unchanged: instead of stopping 8 non-improving checks after the first pass, the
run continues until the first monitored pass of 10⁻⁷ or 400 iterations or a breakdown, and keeps the iterates at
the first monitored passes of 10⁻⁵, 10⁻⁶ and 10⁻⁷.
* The **control result** is the iterate at the first recursive (monitored) pass of 10⁻⁵, as in Table 5.
* The 10⁻⁶ and 10⁻⁷ iterates form the **convergence control** used in §5.4; the K0 true-residual floor of the run is
  recorded as in E29.
* A **breakdown** is no 10⁻⁵ pass within 400 iterations or a non-positive or non-finite pᵀAp before it.
* Three repeats per form: the corner and mean FP32 kernels use atomics and are not bitwise reproducible (T20); the
  stencil and difference controls are expected to repeat bitwise, which is checked and reported.

### 3.5 Terminal residuals

For every kept vector (u_ref, u_ref⁺, every u_F and u_F⁺, every control iterate) the residual is recomputed after
the solve, in FP64, against each named operator: K0-ind and K0 (the **reference-equilibrium residual**, reported
separately) and each of A_stencil, A_corner, A_mean, A_diff. For each coefficient solve the residual against its own
operator is the gate value. For each control the monitored FP32 residual at the pass is reported beside them.

## 4. Data, roles and sealing

| set | content | role | status |
|---|---|---|---|
| development | the k = 4 beam in both layouts (T20's `beam4_uniform`, `beam4_interface`) | validation of the solve and evaluation code against direct solves (§10); not part of any series or test | open; may be computed after freezing, before the main jobs |
| historical | E29 R2 uniform records k = 8–128 and Table 5 | prediction basis and reproduction check of the uniform companion (§5.6); always carried under its own label | open (submitted) |
| confirmatory | k = 8, 16, 32, 64, layouts `interface` (primary) and `uniform` (companion) | all endpoints and the tests of §7 | sealed: nothing computed before the freeze |
| extension | k = 128, both layouts | same endpoints, reported as the extension; its outcomes are classified separately | sealed: nothing computed before the freeze |

No result of the confirmatory or extension sets is read before every job of the confirmatory set has finished,
apart from the gate and failure records that the job itself needs to proceed (admission, residual gates). The
analysis script is written and tested on the development set before the confirmatory outputs are opened.

## 5. Endpoints

For every (k, layout): compliance of the reference C_ref = C(u_ref). For every solution u (coefficient result u_F,
control iterate):

### 5.1 Primary endpoint
**Signed relative compliance difference** D(u) = (C(u) − C_ref) / C_ref.
* D_coef(F, k, L): for the rounded-coefficient result u_F (a *coefficient calculation*).
* D_tot(F, k, L, repeat): for the FP32 control at its first 10⁻⁵ pass (a *measured FP32 action*); the point value
  of the three repeats is their median, and the range is reported.

### 5.2 Secondary endpoints
* **Energy-norm error** e(u) = ‖u − u_ref‖_K0 / (fᵀu_ref)^½ (E8's `consequence` form) for every u_F and every control
  iterate; and the FP32-control discrepancy from the coefficient result, ‖u_ctrl − u_F‖_K0 / (fᵀu_ref)^½.
* **Adjacent-mesh ratios** g(k→2k) = |D(2k)| / |D(k)| and the same for e, with the observed order log₂ g.
* **Interface-to-uniform ratio** |D_int(k)| / |D_uni(k)| per form and k (descriptive).
* **Finest resolved error** per form, layout and solve type: the value at the largest k at which it is resolved.
* Iterations, solver used, PCG-diagnostic energy ratios and non-positive curvature, breakdowns, solve failures,
  refusals for memory, all residuals of §3.5.

### 5.3 Error split (signed compliance, against the same reference)
Only where D_coef(F) is resolved (§6):
* D_rest = D_tot − D_coef = (C_ctrl − C_F)/C_ref, the FP32 application and iteration part, with uncertainty U_coef.
* Where D_coef is unresolved: D_tot is reported as the total, with the bound on D_coef beside it, and no split.

### 5.4 Stopping part (only with the convergence control)
S = (C(u_1e-5) − C(u_1e-7)) / C_ref from the same control run. It is attributed to stopping error only if the
10⁻⁷ pass was reached and |C(u_1e-6) − C(u_1e-7)| ≤ 0.1·|C(u_1e-5) − C(u_1e-7)|. Then D_rest is reported as S plus
the remainder D_rest − S (FP32 application at the converged iterate); otherwise D_rest stays unsplit and S is
reported as "not attributable".

### 5.5 Kinds of result
Every row of the outputs carries its kind: `reference` (FP64 solve of K0), `coefficient` (FP64 solve of a rounded
system), `fp32_control` (measured FP32 actions), `diagnostic` (PCG diagnostic), `historical_E29`. T21 produces no
boundary-node results; those are T19's patch calculations and are only cross-referenced.

### 5.6 Uniform companion and E29 reuse
The uniform layout is recomputed on every grid because the new references must meet 10⁻⁹ (E29's: 1.9–5.3×10⁻⁹)
and the energy errors need the solution vectors, which E29 did not keep. E29's records are reused as a verified
reproduction where the configuration is identical:
* FP32 stencil and difference controls with the common V-cycle: reproduced if the 10⁻⁵ pass iteration is equal and
  |C_T21 − C_E29| / C_E29 ≤ 10⁻⁹; corner and mean controls: E29's value is reported against the range of the three
  repeats.
* The difference-form coefficient bias: E29's value (PCG to 10⁻⁸ against a 10⁻⁸ reference) is compared with D_coef
  and the absolute difference reported.
* Table 5 (own V-cycle, E29 references) appears only as the column `historical (Table 5)` next to the common-cycle
  series, never merged with it. If a uniform control cannot be rerun at some k, E29's compliance error may be shown
  there with the historical label and no energy error.

## 6. Uncertainty and the resolution rule

**Tightening estimate.** For a solve with target iterate u (residual r) and tightened iterate u⁺ (residual r⁺ < r):
the compliance uncertainty is |C(u) − C(u⁺)| / C_ref · r/(r − r⁺), and the energy uncertainty
‖u − u⁺‖_K0 / (fᵀu_ref)^½ · r/(r − r⁺) (the remaining error taken proportional to the residual). The estimate is
*established* only if r⁺ ≤ 0.5·r; otherwise it is not established.

**Residual bound for the reference (k ≤ 64 only).** K0 is symmetric positive definite, and for the reference
C* − C(u_ref) = 2k·(u_refᵀr + rᵀK0⁻¹r), so
B_C = (|u_refᵀr| + ‖r‖²/λ_lb) / (fᵀu_ref) and B_E = ‖r‖ / (λ_lb^½ (fᵀu_ref)^½), with r the K0-ind residual vector.
λ_lb = 0.5·λmin(E29, k) for the uniform layout and 0.5·λmin(E29, k)/8 for the interface layout (K0(interface) ⪰
K0(uniform)/8 because every element matrix is positive semidefinite and every modulus is at least 1/8). No λ_lb
exists at k = 128.

**Uncertainties.**
* U_ref^C = max(tightening estimate, B_C), U_ref^E likewise with B_E; at k = 128 the tightening estimate alone. The
  reference uncertainty is established if at least one of the two is available.
* U_coef^C, U_coef^E: tightening estimate of the coefficient solve.
* For D_coef: U = U_ref^C + U_coef^C. For D_tot: U = U_ref^C. For e(u_F): U_ref^E + U_coef^E; for e(u_ctrl): U_ref^E.
  For a difference of two quantities (layouts, forms): the sum of all uncertainties involved.

**Resolution.** A difference or error X with uncertainty U is *resolved* if |X| ≥ 10·U (the reference uncertainty
is below one tenth of the claimed difference); otherwise it is labelled *unresolved* and reported with its bound
B = |X| + U. A value on a grid that fails G-ref, or a coefficient value that fails G-coef, is labelled with the
failed gate, is published, and enters no test. Control-level differences between forms or layouts must also exceed
the range of the repeats involved to count as resolved.

**Ratios.** g(k→2k) is computed only between two resolved values of the same sign; a sign change between resolved
values is reported as such. Growth bounds for the tests: g_lo = (|X(2k)| − U(2k)) / (|X(k)| + U(k)) and
g_hi = (|X(2k)| + U(2k)) / max(|X(k)| − U(k), 0) (infinite when the denominator is 0).

## 7. Hypotheses, thresholds and outcome classes

Thresholds are fixed here. "All grids" means k = 8, 16, 32, 64. Each hypothesis is classified as support,
contradiction or inconclusive; a test whose inputs fail a gate on some grid can at best be inconclusive unless its
contradiction condition is met elsewhere.

**H1 (primary; bias bound at the interface).** For F ∈ {mean, diff}, layout `interface`, all grids:
* support: G-ref and G-coef pass and B(D_coef) = |D_coef| + U ≤ 1×10⁻⁵ for both forms at all four grids;
* contradiction: for either form at any grid with both gates passed, |D_coef| − U > 1×10⁻⁵;
* inconclusive: otherwise.

The threshold is the production stopping tolerance of the FP32 solver (10⁻⁵ recursive); the uniform difference
bias in E29 is 1.12–1.13×10⁻⁶.

**H2 (primary; no growth at the interface).** For F ∈ {mean, diff}, layout `interface`, on D_coef:
* contradiction: g_lo ≥ 1.5 for both pairs 16→32 and 32→64 (sustained resolved growth over the two finest pairs);
* support: not contradicted and, at k = 64, either g_hi(32→64) ≤ 1.5 or B(D_coef(64)) ≤ 1×10⁻⁷ (the bias bounded
  two orders below the H1 threshold);
* inconclusive: otherwise.

**Primary verdict.** Per form: support if H1 and H2 are both supported; contradiction if either is contradicted;
inconclusive otherwise. Overall: support if both forms are supported; contradiction if either form is contradicted
(the narrowed claim is then stated per form); inconclusive otherwise. H1 and H2 are also evaluated on the uniform
layout as the companion outcome, reported beside the interface outcome and not part of the primary verdict.

**H2E (secondary; energy norm).** The H2 rule applied to e(u_F) for F ∈ {mean, diff}, both layouts. No absolute
threshold is set for the energy error; its values are reported.

**H3 (secondary, R3.1; corner growth).** D_coef(corner), each layout:
* support: resolved at all four grids, one sign throughout, and every adjacent ratio (8→16, 16→32, 32→64) in
  [1.5, 2.5], on both layouts;
* contradiction: on either layout, a sign change between resolved values, or an adjacent ratio between resolved
  values below 1.25 or above 3.0;
* inconclusive: otherwise.

**H4 (secondary; original stencil).** D_coef(stencil), each layout:
* support: on both layouts, at k = 64 either D_coef is resolved and ≥ 0.1, or the PCG diagnostic met
  pᵀA p ≤ 0; and every ratio between resolved values from k = 8 to 64 is ≥ 2;
* contradiction: on either layout at k = 64 with gates passed, B(D_coef) < 1×10⁻²;
* inconclusive: otherwise (a solve failure without a recorded non-positive curvature is not evidence either way).

**H5 (secondary; FP32 controls of the repaired forms at the interface).** F ∈ {mean, diff}, layout `interface`,
all grids, all three repeats:
* contradiction: a breakdown of any repeat, or any repeat with |D_tot| − U_ref^C > 1×10⁻⁴, or g_lo ≥ 1.5 on the
  medians for both pairs 16→32 and 32→64;
* support: no breakdown, every repeat with |D_tot| + U_ref^C ≤ 1×10⁻⁴, and not contradicted by growth;
* inconclusive: otherwise.

**Descriptive, no test:** the error split of §5.3–5.4; the controls of the corner and original forms; the
interface-to-uniform ratios; the PCG diagnostic's energy ratios; the uniform reproduction of §5.6.

**Extension (k = 128).** H1 and H5 are applied at k = 128 alone, H2/H2E/H3 to the pair 64→128 alone (contradiction:
g_lo ≥ 1.5; support for H2: g_hi ≤ 1.5 or B ≤ 10⁻⁷; H3 support: ratio in [1.5, 2.5]; H3 contradiction as above),
H4 at k = 128. These are reported as extension outcomes and do not change the k = 8–64 verdicts.

**Pre-registered expectations (not thresholds).** From E29 (uniform): D_coef(diff) ≈ +1.13×10⁻⁶ at every k; the
corner control error about doubles per halving; D_coef(stencil) from 0.84 % to 120 % at k = 64, indefinite at
k = 128; repaired controls with the common V-cycle 4.6×10⁻⁷–8.1×10⁻⁶ at k ≤ 64 and 1.2×10⁻⁵ (mean) at k = 128. From T19: the interface adds a
coherent coefficient force excess of order 10⁻⁸ relative to the physical interface force per interface node, which
by itself predicts no growth of the interface contribution with k.

## 8. Procedure

### 8.1 Order
1. CPU, before any GPU job: the validation checks of §10 on the development set, the launcher self-test of §8.3,
   and the analysis script run end to end on the development outputs.
2. Confirmatory jobs, one at a time, k ascending, at each k first `uniform` then `interface`. Each job (k, L) runs:
   moduli, load and constraints with their checks; common V-cycle; reference target and tightened solves; for each
   form the symmetry test, PCG diagnostic, GMRES-DC (and MINRES-DC where §3.3 requires it); the twelve FP32 control
   runs; the evaluation of every kept vector (§3.5, §5). Solution vectors are saved to the job's `out/` folder;
   host↔device copies go in pieces of E8's `CHUNK` (one-shot large copies create pinned staging buffers that count
   as shared GPU memory).
3. Extension jobs at k = 128, after all confirmatory jobs, `uniform` then `interface`, each split into separate GPU
   jobs (reference; coefficient solves per form; controls; evaluation) so that each is admitted on its own peak.
4. CPU analysis: CSVs, `reference_checks.json`, verdicts, report.

### 8.2 Admission and memory (authors' rule of 2026-11-23)
* Predicted peak per job from T20's `workspace.json` counts for that k (`reference_pcg64_t21`,
  `pcg_energy_t20op`, `fp32_control_common` plus two FP64 vectors for the kept iterates,
  `gmres_library(m=20)` and `minres_library` plus one FP64 vector for the outer correction, the evaluation's three
  FP64 vectors plus K0-ind's slab workspace), taking the largest phase of the job. At k = 128 the largest is
  GMRES(20), 15,941,779,764 B + 409,368,600 B.
* Admit when the predicted peak plus 1.5 GiB fits in the free memory nvidia-smi reports, read with no CUDA context in
  the launcher; record `guard.require_budget`'s answer (computed in the job process) and the other processes'
  dedicated usage beside it, for information.
* At k = 128, if GMRES(20) does not fit, use GMRES(10) (within T20's measured range) and record the refusal of 20;
  if that does not fit either, the coefficient solves at k = 128 are refused for memory and recorded.
* Pool cap: `set_limit` at the driver's free memory at start minus 1.5 GiB.
* Spill watch: T20's launcher protocol (lock with O_CREAT|O_EXCL and no stale-lock deletion; no CUDA context before
  arming; allocation only after a sample holds the job PID with both counters; a sample without it or with a
  missing counter stops the job and sets coverage false; shared usage more than 256 MiB above the first watched
  value stops the job at once as refused for memory; a final sample checked before release). Coverage is stated
  from the first complete sample. One GPU job at a time.

### 8.3 Launcher self-test
Before the first GPU job, a CPU-only test of the copied launcher: an existing lock refuses the launch and names its
owner; an empty baseline, a sample with only an unrelated PID, and a sample with a missing counter each stop the
job with coverage false. If any case fails, no GPU job starts until it is fixed and the test passes.

## 9. Stopping rules

* **Solves:** the caps of §3 (20,000 PCG iterations per phase; 60 outer DC steps with stagnation after 5; 400
  inner iterations; 400 FP32 control iterations). A capped solve is a failure at its level and is not rerun.
* **Jobs:** wall-time cap 4 h per job; a job stopped by the cap is recorded incomplete and not rerun. A job stopped
  from outside (operator stop, crash with no output) may be rerun once from the start and is recorded as such. A
  spill or allocation failure is a refusal for memory: the result is not kept, and the job is not rerun at the same
  size and configuration (k ≤ 64 has no smaller configuration; its affected endpoints are reported missing).
* **Study:** complete when every prespecified solve of §8.1 has completed, failed or been refused. No grid, layout,
  form, solver setting, tolerance or threshold is added or changed after outcomes are seen. A failed or refused
  extension job does not stop the analysis.

## 10. Validation before any confirmatory outcome (development set only)

1. Layout: at each k the interface layout has exactly half its cells at 0.125, all with centre x > 4; the uniform
   layout is all 1; checked again inside each job on the arrays actually used.
2. Load: total −1 in y on the x = 8 face with the stated weights; identical for both layouts.
3. K0-ind against T20's CPU assembly of K0 on both k = 4 layouts (largest action error ≤ 10⁻¹³ of the largest
   entry, random and smooth vectors), and against `node_hoist` on each grid inside the job before first use
   (same bound, seeded random vector); a failure stops that job.
4. GMRES-DC, MINRES-DC, the PCG diagnostic and the reference procedure on both k = 4 layouts and all four forms
   against SciPy direct solves of T20's CPU-assembled matrices: compliance agreement ≤ 10⁻¹⁰ relative and residual
   gates met.
5. The analysis script on the development outputs: every column filled, the resolution and verdict rules exercised
   on planted values (a resolved growth, an unresolved value, a failed gate, a sign change), each giving the class
   this plan defines.

## 11. Outputs (in `tasks/T21/`)

* `beam_interface.csv`: one row per (k, form, kind, repeat) for the interface layout, with: k, n_elem, layout,
  form, kind, solver, repeat, status, iterations, C, D (signed), U^C, resolved flag, bound, e, U^E, e resolved flag,
  residuals against K0-ind, K0, A_stencil, A_corner, A_mean, A_diff, monitored residual at the pass (controls),
  PCG-diagnostic minimum energy ratio and first non-positive curvature (diagnostic rows), adjacent ratio to the
  previous k with its resolution, split columns (D_rest, S, remainder, with their labels), gate flags.
* `uniform_controls.csv`: the same columns for the uniform companion, plus `historical_E29` rows (Table 5 own-cycle
  values and E29 common-cycle values) and the reproduction checks of §5.6.
* `reference_checks.json`: per (k, layout): target and tightened reference residuals (K0-ind and K0), iterations,
  tightening changes, B_C, B_E, λ_lb, U_ref, gate result; K0-ind validation; symmetry tests s_F; per coefficient
  solve the gate inputs and tightening; MINRES/GMRES cross-checks; admission, refusal and spill-watch records per job.
* `verdicts.json`: every hypothesis with its inputs, class and the rule clause that decided it.
* `REPORT.md`, `DEVIATIONS.md`; code and raw job outputs in `src/`, `out/`. No figure is drawn here; the data a
  figure needs are in the CSVs.

## 12. Reporting rules

* Publish every value, including unresolved ones (with their bounds), failures, breakdowns and refusals; each
  adjacent-mesh trend with its resolution; the finest resolved error per series.
* State every trend only over the consecutive grids actually solved and resolved; no extrapolation beyond them.
  Coefficient trends are limited to the range in which the coefficient solves passed their gate.
* Name the reference by its achieved residual on each grid, not by the target.
* Keep the kinds apart in every table and sentence: coefficient calculations, measured FP32 actions, references;
  boundary-node statements belong to T19.
* Stopping error is named only where §5.4 attributes it; otherwise the FP32 part is "application and iteration".
* The interface result covers this one layout (a transverse 8:1 plane at x = 4) on voxel grids; it says nothing
  about other contrasts, layouts or distorted elements. T33 covers the voids at 10⁻⁹ and k = 128 as its primary.
* The historical Table 5 values keep their own label wherever they appear beside the common-cycle series.
* For the manuscript, no file names, tool names or run labels enter the main text, and no clock times, seeds,
  digests or run counts enter any text.

## 13. Feasibility and power (from development data)

* Smallest effect to resolve: the uniform difference bias, about 1.1×10⁻⁶, which needs U ≤ 1.1×10⁻⁷.
* At k = 64 and a reference residual of 10⁻⁹ (‖f‖ ≈ 0.0155, fᵀu_ref ≈ 16, λmin = 1.17×10⁻⁷ from E29), the residual
  bound gives B_E ≈ 1.6×10⁻⁸ for the uniform layout (λ_lb with the factor 0.5) and about 3×10⁻⁸ for the interface
  layout, under 1.1×10⁻⁷. B_C is far smaller. Compliance differences of the size expected for the repaired forms are
  therefore resolvable at k ≤ 64; the mean form's coefficient bias may lie below resolution, in which case H1 and H2
  are decided by its bound.
* Risk: the FP64 evaluation floor of K0 on this slender beam is not known at k = 64 and 128 (E29 stopped at its
  first check below 10⁻⁸; E8 reached 8.9×10⁻¹¹–8.3×10⁻¹⁰ on other problems). A grid whose reference cannot reach
  10⁻⁹ fails G-ref and is reported as such; no fallback reference procedure is added.
* Memory: every job at k ≤ 64 is predicted below 2.7 GB; at k = 128 the largest phase is about 16.4 GB against the
  20.99 GB T20 had available, admitted on the free memory at launch.

## 14. Deviations

Any departure from this plan (a changed cap, an added check, a rerun, a refusal, a code fix after the validation of
§10) is recorded in `DEVIATIONS.md` with its reason and its effect on the endpoints. This file is not edited after
freezing.
