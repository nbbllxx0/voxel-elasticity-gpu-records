# T22 analysis plan: skew and lowest symmetric-part eigenvalues of the fixed rounded operators, uniform clamped beam k = 32, 64 (k = 128 extension)

Serves A.2 and R3.3 (Reviewer 3's point (2)). This plan is written and frozen before any T22 computation. T22 has run
no operator application, eigensolve, probe, memory measurement or vector evaluation on any grid. The study calls no
language model, so the rule on model identifiers does not apply.

Data inspected for planning (all already open, none produced by T22):
* `results/E29/beam_conditioning.json` (R4): λmin and λmax of the constrained FP64 node operator on the uniform beam,
  k = 8–64, from inverse iteration with FP64 PCG solves (`experiments/E29_review.py`, `part_r4`).
* `results/E29/beam_controls.json` (R2): the rounded-coefficient PCG runs (`pcg_energy`) of the original stencil and
  the difference form, k = 8–128, with their compliance errors and the smallest search-direction energy ratios
  (0.992, 0.967, 0.866, 0.465 at k = 8–64; −1.1385 for the first direction at k = 128).
* T20 (`tasks/T20/REPORT.md`, `small_spectrum.csv`, `workspace.json`, `t20_ops.py`): the six FP64 forward and transpose
  free-DOF operators, their dense spectra on the k = 4 beam, and the workspace counts and apply times at k = 32–128.
* T21's saved uniform-beam vectors (`tasks/T21/out/data/k{32,64,128}_uniform/`): file names and sizes only.
* The submitted text (main.tex Sec. 3.2 and 5.2, supplementary S17 and Table S22).

## 1. Question

**Primary (R3.3, A.2).** On the clamped uniform 8×1×1 beam at k = 32 and 64, what are the coefficient skew
‖A−Aᵀ‖_F/‖A‖_F and the three smallest algebraic eigenvalues of the symmetric part S = (A+Aᵀ)/2 on the free DOFs for
each fixed rounded operator of T20? Specifically:
* (Q1, after the repair) Are the two repaired forms, the element kernel with a mean reference (`mean`) and the stencil
  difference form (`diff`), symmetric to rounding, with three lowest symmetric-part eigenvalues that are resolved,
  positive and equal to the FP64 operator's within 10⁻⁴?
* (Q2, before the repair) Is the lowest symmetric-part eigenvalue of the original rounded stencil (`stencil`) pushed
  below the FP64 operator's, and does that depression grow relative to λmin under refinement from k = 32 to 64?

**Secondary.**
* (S-a) The same table for the atomic element form (`atomic`), the corner reference (`corner`) and the FP64
  reference (`ref`); the skew of each form on the low-mode scale (R3.3's one-sided projection concern).
* (S-b, A.2) On the actual FP32 actions: bilinear skew and Rayleigh energies on general, smooth, low-mode and search
  directions, normalised by FP64 reference energies; in particular, do the FP32 self-block correction and the FP32
  difference form, whose unit-vector matrices are identical, differ on general inputs?

**Extension.** k = 128, with the same procedure, only if the full block workspace (block size 6) passes the guard.
Its rows count as added only where the eigensolver converged (§9). The question it answers is whether the original
stencil's loss of definiteness at k = 128 can be shown by a verified negative Rayleigh quotient. Its failure or
refusal leaves the primary questions answered.

## 2. Problem (frozen)

| item | definition |
|---|---|
| geometry, mesh | beam [0,8]×[0,1]×[0,1]; `Grid(8k, k, k)` of unit-cube voxels, h = 1/k; confirmatory k ∈ {32, 64}; extension k = 128 |
| element | trilinear hexahedron, `ke_unit(0.3)`; the job asserts `t20_common.K0` equals `ke_unit(0.3)` bit for bit |
| constraint | every node on x = 0 fixed in all three components (mask 7), `E28_verification.slender(k)`; free DOFs from `t20_common.free_mask` |
| load (search directions and T21 vectors only) | consistent unit transverse end traction of `slender(k)` |
| moduli | E = 1 in every cell, one FP32 array per k, used by every operator, V-cycle and FP32 kernel of that k |
| sizes | k = 32: 839,619 DOFs (6.7 MB per FP64 vector); k = 64: 6,502,275 (52.0 MB); k = 128: 51,171,075 (409.4 MB) |
| inner product | Euclidean on the free DOFs; every vector is zero on the fixed DOFs, checked exactly before use |
| FP64 reference energy | ε₀(x) = xᵀK0x and ε₀(x, y) = xᵀK0y with K0 the form `ref` (forward action) |

## 3. Operators

### 3.1 Fixed rounded matrices (coefficient level, FP64 arithmetic)

The six T20 forms (`t20_ops.FreeOperator(grid, form, fixed)`, forward and transpose, FP32-stored moduli):

| form | matrix | role here |
|---|---|---|
| `ref` | production FP64 node kernel with K0 | FP64 reference; its eigenvalues are compared with E29 |
| `atomic` | Σ_e E_e P_eᵀ Q P_e, Q = fl32(K0) | original element kernel ("before", element level) |
| `corner` | Σ_e E_e P_eᵀ Q (I − T S₀) P_e | corner reference (one-sided projection) |
| `mean` | Σ_e E_e P_eᵀ Q (I − P) P_e | repaired element form ("after") |
| `stencil` | 27-point stencil with FP32 coefficients W_r(n) | original stencil ("before") |
| `diff` | Σ_{r≠0} W_r(n)(u_{n+r} − u_n) | repaired stencil form ("after") |

S_F = (A_F + A_Fᵀ)/2 is applied as `FreeOperator.symmetric_part` (forward plus transpose, halved).

### 3.2 Actual FP32 actions

The production FP32 kernels as E29 R2 applies them (`Operator(g, ke_unit(0.3), variant, float32).apply(x, E32, y,
fixed=fixed)`), each paired with the T20 form that is its coefficient matrix:

| FP32 action | coefficient matrix |
|---|---|
| `stencil` | `stencil` |
| `stencil_diff` | `diff` |
| `stencil_selfcorr` (self-block correction) | `diff` (same matrix on unit vectors, Table S22) |
| `elem_atomic` | `atomic` |
| `elem_ref` | `corner` |
| `elem_mean` | `mean` |
| FP64-arithmetic control (`MixedOperator`) | `ref` |

### 3.3 Preconditioning aid

E29's common V-cycle: `GMG(grid, fixed, ke_unit(0.3), fine_variant="stencil")`, `update(E32)`, applied to FP64
vectors through `CastPrecond`, with its output masked to the free DOFs. This is the preconditioner E29 used for the
λmin it reports. In exact arithmetic it is a fixed symmetric linear operator (damped Jacobi with the same weight
before and after, exact transfers, Cholesky on the coarsest level). Its positivity is checked in each job
(§8.1). It enters only the search space of the eigensolver. Every Ritz value, residual and Rayleigh quotient is
computed with the FP64 actions of §3.1, so a reported eigenvalue does not depend on the aid being exactly SPD.

The authors' code is used from copies in `tasks/T22/src`: voxfem as copied in T20; `E8_precision_floor.py`,
`E28_verification.py`, `E29_review.py`; T20's `t20_common.py`, `t20_ops.py`, `t20_cpu.py`, `t20_launch.py`. No
authors' file and no file of another task is changed. A T22 function that extends a copied function is a new function
in a T22 file.

## 4. Data, roles and sealing

| set | content | role | status |
|---|---|---|---|
| development | uniform beam k = 4 (T20's `beam4_uniform`, 2400 free DOFs), k = 8 and k = 16 | validation of every T22 code path against dense and CPU-sparse eigensolvers (§10); measured workspace and iteration counts for admission and time planning; the k = 8 and 16 reference values also enter the E29 reproduction check G0 | open: computed after the freeze, before any confirmatory job, and may be read |
| historical | E29 R4 λmin (k = 8–64), E29 R2 `pcg_energy` records (k = 8–128), T20's k = 4 dense spectra | reproduction targets and expectations; always carried under their own label | open (submitted or completed) |
| inputs | T21's saved uniform-beam vectors (`ref_target.npy`, `coef_stencil_gmres_target.npy`, `ctrl_stencil_r1_1e-05.npy` where present) at k = 32, 64, 128 | members of the search-direction set (§6.4) | open files; no T22 quantity has been computed on them |
| confirmatory | k = 32 and 64, all six forms, all endpoints of §7 | the tests of §9 | sealed: nothing computed before the freeze |
| extension | k = 128 | the same endpoints, classified separately (§9.6) | sealed: nothing computed before the freeze |

No endpoint of the confirmatory or extension sets is read before every confirmatory job has finished. The exceptions
are records a job needs in order to proceed: admission and memory records, exit status, and the Ritz vectors one job
passes to the next job of the same k as inputs. The analysis script is written and run end to end on the
development outputs before the confirmatory outputs are opened.

## 5. Coefficient skew from assembled free-DOF blocks

**Block recovery.** Colour every node by c(n) = (i_x mod 3, i_y mod 3, i_z mod 3). That gives 27 colours, and no two
nodes of one colour lie in a common 3×3×3 neighbourhood. For colour c and component j, the probe p_{c,j} is 1 on
every free DOF (m, j) with c(m) = c and 0 elsewhere. For a free row DOF (n, i), the forward output y = A p_{c,j}
holds exactly one matrix entry, A[(n,i),(m,j)], where m is the unique node of colour c with m − n = r ∈ {−1,0,1}³.
The forward probes therefore recover every 3×3 block B_r(n) = A_{n,n+r} of the assembled free-DOF matrix, each
entry as one evaluation of the kernel and not as a sum over columns.

**Skew.** ‖A−Aᵀ‖_F² = Σ_n Σ_r ‖B_r(n) − B_{−r}(n+r)ᵀ‖_F² and ‖A‖_F² = Σ_n Σ_r ‖B_r(n)‖_F², both accumulated in
FP64. The pairing needs the probe of colour c(n) and the probe of colour c(n+r). The job therefore loops over the
node colour c and, for each offset r, recomputes the three probes of colour c + r instead of storing all 81 outputs.
At most 27·(3 + 27·3) = 2,268 forward applications per form are needed, with at most 8 full vectors live.
* Endpoint: s_F = ‖A−Aᵀ‖_F/‖A‖_F per form and k. Also ‖A‖_F, and the row and column absolute-sum norms ‖A‖_∞ and
  ‖A‖_1 from the same blocks (reported).
* Cross-check, using the transpose kernel: s_F^T = (Σ_{c,j} ‖(A − Aᵀ)p_{c,j}‖²)^½ / (Σ_{c,j} ‖A p_{c,j}‖²)^½ from
  the 81 forward and 81 transposed probes. It must agree with s_F within 10⁻³ relative or 10⁻¹⁵ absolute, whichever
  is larger. A disagreement is recorded, and s_F stays the endpoint.
* Labels: s_F ≤ 10⁻¹⁴ means *symmetric to FP64 assembly rounding*; above that, *coefficient skew* with its value.
  The element forms use FP64 atomics, so their skew below about 10⁻¹⁶ is assembly noise (T20).

## 6. Eigensolver, vectors and action measures

### 6.1 Block eigensolver (all forms, all k)

A T22 in-place block LOBPCG for the smallest algebraic eigenvalues of the symmetric (possibly indefinite) S_F with
B = I. It is written for T22 in FP64 CuPy and validated per §10.

* **Block and wanted pairs:** block size b = 6 at every k (three wanted pairs and three guard vectors; the uniform
  beam has degenerate y/z bending pairs, λ1 = λ2 and λ3 = λ4 at k = 4). No smaller block is used anywhere.
* **Basis:** Z = [X, W, P], with X the current Ritz block, W = T·R the masked preconditioned residuals (T the aid of
  §3.3) and P the implicit previous-direction block (absent in the first iteration). Z is orthonormalised by SVQB
  (Gram matrix eigendecomposition in FP64), applied twice. Columns of W and P whose scaled Gram eigenvalue is below
  10⁻¹² are dropped for that iteration, and the drop counts are recorded.
* **Rayleigh–Ritz:** G = Zᵀ S_F Z, symmetrised as (G+Gᵀ)/2, solved by host `numpy.linalg.eigh`. The lowest b pairs
  are kept. SX, SW and SP are carried by the same linear combinations. X, SX, P and SP are updated in row chunks of
  at most 2²⁰ DOFs, so no extra full block is stored. SX is recomputed by fresh FP64 application every 50 iterations.
* **Residuals:** r_i = S_F x_i − θ_i x_i for the three wanted pairs.
* **Stop:** all three wanted pairs have ‖r_i‖/‖x_i‖ ≤ 10⁻⁵·|θ_i| (*stop target*). The other stops are a cap of 1,500
  iterations; stagnation, meaning no new minimum of max_i ‖r_i‖/(‖x_i‖|θ_i|) in 200 consecutive iterations; and a
  wall cap of 20 min per solve at k ≤ 64 and 45 min at k = 128. On a cap or stagnation the current pairs are kept
  and reported as not converged.
* **Two starting subspaces per (form, k):** start A is a seeded standard-normal 6-vector block (seed 2201), masked to
  the free DOFs; start B is the same with seed 2202. For every form at a given k the starts are the same.
* **Final evaluation (after the solve, fresh FP64 applications):** for each wanted pair i, θ_i, the recomputed residual
  ρ_i = ‖S_F x_i − θ_i x_i‖/‖x_i‖ with θ_i the Rayleigh quotient of x_i, iterations, drop counts and stop reason.
  The guard values θ_4..θ_6 are recorded as gap estimates.

### 6.2 Per-pair definitions

* **Consistent starts:** θ_i^A and θ_i^B have the same sign and |θ_i^A − θ_i^B| ≤ 0.01·max(|θ_i^A|, |θ_i^B|).
* **Sign-resolved (acceptance criterion):** consistent, with ρ_i^A < 0.05|θ_i^A| and ρ_i^B < 0.05|θ_i^B|. S_F is
  symmetric, so an eigenvalue lies within ρ_i of θ_i, and it has the sign of θ_i.
* **Converged:** both starts met the stop target, and the recomputed ρ_i ≤ 10⁻⁴|θ_i| in both.
* **Value uncertainty:** U(θ_i) = max(ρ_i^A, ρ_i^B, |θ_i^A − θ_i^B|) (absolute). The reported value is θ_i^A. The
  quadratic bound ρ_i²/gap_i (gap_i the distance from θ_i to the nearest other Ritz value of the block that is not
  within U of it) is reported beside it, for information only.
* **Shift against the FP64 reference:** σ_i(F) = θ_i(F)/θ_i(ref) − 1, with
  U_σ = U(θ_i(F))/|θ_i(ref)| + |θ_i(F)|·U(θ_i(ref))/θ_i(ref)². σ is *resolved* if |σ| ≥ 10·U_σ, otherwise it is
  reported with its bound |σ| + U_σ.
* **Low-mode skew:** for each wanted Ritz vector, κ_i = ‖(A_F − A_Fᵀ)x_i‖/(2‖x_i‖), reported as κ_i/|θ_i|. Label:
  < 0.05 means *skew below the low-mode scale* (x_i is then also an approximate eigenvector of A_F itself, with
  residual below ρ_i + κ_i); ≥ 0.05 means *skew comparable to the low-mode scale*. Also the bilinear skew among the
  three wanted vectors, max_{i<j} |x_iᵀA_F x_j − x_jᵀA_F x_i| / (ε₀(x_i)ε₀(x_j))^½, and the energy ratio
  x_iᵀA_F x_i / ε₀(x_i).

### 6.3 Negative Rayleigh witnesses (coefficient level)

A candidate w is any wanted or guard Ritz vector with θ < 0, or any vector of §6.4 whose coefficient-level energy
under some form F is negative. It is **verified negative for F** if both of these hold:
* q_f = Σ_i w_i·fl(A_F w)_i and q_t = Σ_i w_i·fl(A_Fᵀ w)_i are both negative. Each is computed from the forward or
  transposed FP64 action, copied to the host in chunks, with elementwise FP64 products summed exactly by
  `math.fsum`.
* |q_f| > ε_f and |q_t| > ε_t, where ε = γ₂₅₆·b_F·‖w‖_∞·‖w‖_1 + u·Σ_i |w_i·fl(Aw)_i|. Here u = 2⁻⁵³,
  γ₂₅₆ = 256u/(1 − 256u), and b_F = 64·max(E)·max(‖K0‖_∞, ‖K0ᵀ‖_∞, ‖Q‖_∞, ‖Qᵀ‖_∞)·1.001, a bound on the absolute
  sum of the elementary products behind one output entry of any of the six forms (at most 8 elements, projection
  and difference factors at most 8). The first term bounds the FP64 rounding of the action and the second the
  rounding of the products.

Each verified witness is reported with q_f/‖w‖², q_t/‖w‖², ε, ε₀(w), the energy ratio q_f/ε₀(w), its origin and
form, and is saved (`out/witness_*.npy`). A verified negative witness establishes that S_F, and therefore A_F, has a
negative direction on the free DOFs. A candidate that fails verification is reported as unverified and establishes
nothing. Positive values verified the same way (q > ε) are labelled *verified positive* and describe only that
direction.

### 6.4 Vector sets for the action measures (per k)

Each vector is scaled to max-abs 1 and rounded to FP32 (x₃₂). Its exact FP64 cast x is the vector every FP32 and
FP64 evaluation uses, so all of them act on the same vector.
* **General** V_gen: three uniform random fields on [−1, 1] (seed 2203), zero on the fixed DOFs.
* **Smooth** V_sm: s1 = E29's `smooth_field`; s2 = the field (sin 2πx̂·cos πẑ, sin πx̂·sin πŷ, cos 2πŷ·sin πx̂);
  s3 = (0, x̂², x̂²), a bending-like field. Here x̂, ŷ, ẑ are the node coordinates scaled to [0,1], and every field is
  masked to the free DOFs.
* **Low-mode** V_low: the three wanted Ritz vectors of `ref` (start A). V_own(F): the three wanted Ritz vectors of form
  F (start A), used for F and for the FP32 actions whose coefficient matrix is F.
* **Search directions** V_dir:
  * p^st_1..p^st_5: the first five search directions of E29's `pcg_energy` (T22 copy that records the directions,
    otherwise unchanged) on A_stencil with the common V-cycle, x0 = 0. If it stops earlier at a non-positive
    direction, as E29 recorded at k = 128, only the directions up to the stop are available.
  * p^K_1..p^K_5: the same on K0 (Ac = A64 = K0).
  * p^32_1..p^32_5: the first five search directions of E8's `pcg32`, mode `mg32_x64`, with the FP32 original
    stencil and the common V-cycle, x0 = 0, 400-iteration cap, as E29 runs it (T22 copy that records p at
    iterations 1–5, otherwise unchanged).
  * From T21 where the file exists: the FP64 reference solution u_ref; the stencil coefficient error
    e_coef = u_coef,stencil − u_ref; the FP32 stencil control error e_ctrl = u_ctrl,stencil(10⁻⁵ pass) − u_ref.
    Integrity check before use: correct length, finite, zero on the fixed DOFs, and ‖f − K0 u_ref‖/‖f‖ within
    1 % of the K0 residual T21 recorded for that vector. A file that fails is excluded and recorded.
* **Pairs for bilinear measures:** all pairs within V_gen, V_sm, V_low and V_own(F); consecutive pairs within each
  direction family; (u_ref, e_coef) and (u_ref, e_ctrl); and the six cross pairs of the first members of V_gen, V_sm,
  V_low and V_dir (p^st_1).

### 6.5 Action measures

For each vector x (or pair x, y), each FP32 action A₃₂ of §3.2 (three repeats; the atomic kernels are not bitwise
reproducible) and each coefficient form A_F of §3.1:
* **FP32 Rayleigh energy:** η(x) = xᵀ·fl₃₂(A₃₂x₃₂) / ε₀(x), with the FP32 output cast exactly to FP64 and the dot
  product formed in FP64. Also the coefficient-level η_coef(x) = xᵀA_F x/ε₀(x) of the paired matrix. The FP32
  application part is η − η_coef.
* **FP32 bilinear skew:** β(x, y) = |xᵀA₃₂y₃₂ − yᵀA₃₂x₃₂| / (ε₀(x)ε₀(y))^½; the same at coefficient level with A_F.
* **FP32 bilinear defect:** δ(x, y) = |xᵀA₃₂y₃₂ − ε₀(x, y)| / (ε₀(x)ε₀(y))^½, and the energy defect |η(x) − 1|; the
  same at coefficient level.
* **Negative FP32 energy:** η(x) < 0 in all three repeats, with |xᵀA₃₂x₃₂| above the FP64 product-rounding bound
  u·Σ_i |x_i(A₃₂x₃₂)_i| (exact host summation). This is a property of the measured FP32 action on that vector, not
  an eigenvalue statement, and it is reported in its own column.
* Repeats: median and range of the three. For the stencil kernels and the FP64-arithmetic control, whether the
  repeats are bitwise equal.

## 7. Endpoints

* **Matrix level, per (form, k):** s_F (§5) with its cross-check; class of §9.1.
* **Spectrum, per (form, k, start, i = 1..3):** θ_i, ρ_i, ρ_i/|θ_i|, iterations, stop reason, consistent,
  sign-resolved, converged, U(θ_i), shift σ_i with U_σ and resolution, κ_i/|θ_i|, energy ratio; guard values θ_4..θ_6.
* **Witnesses:** every candidate with its verification result.
* **Action checks, per (k, vector or pair, action, repeat):** η, η_coef, β, δ and the negative-energy flag.
* **Reproduction:** θ_1(ref) against E29's λmin at k = 8, 16 (development) and 32, 64 (confirmatory). At k = 128,
  q(p^st_1)/ε₀(p^st_1) against E29's recorded −1.1385383514247778.

## 8. Procedure

### 8.1 Order

1. **CPU, before any GPU job:** the launcher self-test (§8.3); the CPU parts of the validation (§10).
2. **Development GPU jobs:** k = 4, 8, 16, each running everything of a confirmatory job. This gives the validations of
   §10, measured pool peaks per phase, and iteration counts and times per solve.
3. **Confirmatory jobs, one at a time:** k = 32 then k = 64. Each k has three jobs:
   * **J_skew:** setup checks, then §5 for the six forms.
   * **J_eig:** for each form in the order ref, stencil, diff, mean, atomic, corner, both starts (§6.1). The final
     evaluation, the low-mode skew and the witness verification of Ritz candidates follow. The start-A wanted Ritz
     vectors and every candidate are saved.
   * **J_act:** generation of the search directions, loading of the T21 vectors, then §6.5 for all vectors and
     actions, and witness verification of all candidates from the vector sets.

   Setup checks in every job:
   * moduli all 1 in FP32; load total −1;
   * K0 equal to `ke_unit(0.3)`;
   * the mask equal to `free_mask(slender(k).fixed)`;
   * forward against transpose dot test of each form on one seeded pair (≤ 10⁻¹² relative, T20's criterion);
   * aid checks: xᵀTx > 0 on three seeded random vectors and V_sm, and the symmetry defect
     |xᵀTy − yᵀTx|/(|xᵀTy| + |yᵀTx|) on three pairs (reported). A failed positivity check is recorded and does not
     stop the job (§3.3).
4. **Extension at k = 128**, after every confirmatory job and only if admitted (§8.2), in this order:
   * J_skew;
   * one J_eig per form in the order ref, stencil, diff, mean, atomic, corner;
   * J_act, which runs only if J_eig(ref) completed, because its low-mode set needs it.

   Each J_eig at k = 128 saves only the start-A wanted vectors and the candidates.
5. **CPU analysis:** CSVs, `checks.json`, `witnesses.json`, `verdicts.json`, report.

Host↔device copies go in pieces of E8's `CHUNK` (one-shot large copies create pinned staging buffers that count as
shared GPU memory).

### 8.2 Admission and memory (authors' rule of 2026-11-23)

* **Predicted peak per job:** at k = 32 and 64, from the measured pool peaks of the same phases at k = 8 and 16 (a
  fixed part plus a per-DOF coefficient fitted through the two points). At k = 128, the same fit through the
  measured peaks at k = 32 and 64. Expected sizes from T20's counts: the in-place solver with b = 6 holds 36 FP64
  block vectors plus about 4 working vectors, the V-cycle and the context. That is about 2.9 GB at k = 64 and about
  18.6 GB at k = 128 (40 × 409.4 MB, the V-cycle build peak of 1.53 GB, the 0.35 GB context and small arrays).
* **Rule:** admit when the predicted peak plus 1.5 GiB fits in the free memory nvidia-smi reports, read with no CUDA
  context in the launcher. Record `guard.require_budget`'s answer (computed in the job process) and the other
  processes' dedicated usage beside it, for information.
* **k = 128 gate:** if the predicted J_eig peak with b = 6 does not fit, nothing at k = 128 is run. The refusal is
  recorded with the numbers, and no smaller block is substituted. If J_eig(ref) fits but a later form's job is
  refused at its own launch, that form is recorded as refused.
* **Pool cap:** `set_limit` at the driver's free memory at start minus 1.5 GiB.
* **Spill watch:** T20's launcher protocol:
  * lock created with O_CREAT|O_EXCL, with no stale-lock deletion;
  * no CUDA context before arming;
  * no allocation until a sample holds the job PID with both counters;
  * a sample without the PID, or with a missing counter, stops the job and sets coverage false;
  * shared usage more than 256 MiB above the first watched value stops the job at once as refused for memory;
  * a final sample is checked before release.

  Coverage is stated from the first complete sample. One GPU job at a time; WSL is not used.

### 8.3 Launcher self-test

Before the first GPU job, a CPU-only test of the copied launcher, in four cases:
* an existing lock refuses the launch and names its owner;
* an empty baseline stops the job with coverage false;
* a sample with only an unrelated PID does the same;
* a sample with a missing counter does the same.

If any case fails, no GPU job starts until the launcher is fixed and the test passes.

## 9. Classification, hypotheses and outcome classes

Thresholds are fixed here. A value on a grid where a setup check failed is labelled with the failed check, is
published, and enters no test.

### 9.1 Class per (form, k)

* **N, negative direction established:** at least one verified negative witness for F at k.
* **P3, three lowest resolved positive:** no verified negative witness for F at k, and θ_1..θ_3 sign-resolved and
  positive. This describes the resolved modes only. It does not establish that S_F is positive definite, that a PCG
  on A_F is well defined, or that any preconditioner is SPD; a block method can miss a lower mode.
* **U, unresolved:** otherwise. A sign-resolved negative θ whose Ritz vector fails witness verification is U, with a
  note.

### 9.2 G0: reproduction of E29 (acceptance gate)

At each k ∈ {8, 16, 32, 64}: G0 passes if |θ_1(ref) − λ_E29|/λ_E29 ≤ 10⁻⁴, with U(θ_1)/λ_E29 reported beside it.

Where it fails, the discrepancy is investigated by this fixed procedure:
1. Check whether θ_1(ref) is converged and its Weyl interval excludes λ_E29.
2. Run a copy of E29's `part_r4` unchanged at that k in one guarded job and compare it with E29's record and with
   θ_1(ref).
3. Report which value the evidence supports and why.

The other endpoints at that k stay in the tables with the G0 label.

### 9.3 H1 (primary, Q1): the repaired matrices

For F ∈ {mean, diff}, k ∈ {32, 64}:
* **support:** at both k, s_F ≤ 10⁻¹², class P3, and |σ_i| + U_σ ≤ 10⁻⁴ for i = 1, 2, 3.
* **contradiction:** at either k, any of: class N, a sign-resolved negative θ_i, a resolved |σ_i| > 10⁻², or
  s_F > 10⁻⁸ (skew of the corner form's size).
* **inconclusive:** otherwise.

Verdict per form; overall support if both forms are supported, contradiction if either is contradicted, otherwise
inconclusive. A contradiction is an adverse repair result and is reported as such (§12).

### 9.4 H2 (primary, Q2): the original rounded stencil

The depression is σ_1(stencil, k).
* **support:** either σ_1 is resolved and negative at both k with |σ_1(64)| − U_σ(64) > |σ_1(32)| + U_σ(32) (growth
  under refinement), or class N at k = 64.
* **contradiction:** σ_1(64) is resolved and either σ_1(64) ≥ −0.01, or |σ_1(64)| < |σ_1(32)| with σ_1(32) also
  resolved (the depression shrinks).
* **inconclusive:** otherwise.

**H2a (secondary).** The same rule applied to `atomic`.

### 9.5 Secondary

* **H3 (skew on the low-mode scale, descriptive with fixed labels).** κ_i/|θ_i| for every sign-resolved pair, with
  the labels of §6.2. Each form's s_F is reported beside its low-mode label, `corner` in particular. No verdict.
* **H4 (FP32 self-block correction against FP32 difference form, A.2).** m_A(k) is the median over x ∈ V_sm ∪ V_low
  (six vectors) of |η_A(x) − 1|, each vector's η taken as the median of its three repeats.
  * support: m_selfcorr(k) ≥ 10·m_diff(k) at both k = 32 and 64;
  * contradiction: m_selfcorr(k) ≤ m_diff(k) at either k;
  * inconclusive: otherwise.

  η_coef is identical for the two by construction (one matrix). That identity is checked and reported, and it is
  what makes the difference a general-input effect.
* **Descriptive, no test:** the classes of `ref`, `atomic` and `corner`; the shifts of every form; every action
  measure of §6.5 for every action, including the negative FP32 energies; the repeat spreads; the aid checks.

### 9.6 Extension (k = 128)

Rows at k = 128 are *added* for a form only if its eigensolve converged in both starts (§6.2). The estimates of
forms that did not converge are published with the label *extension, not converged* and enter no test. A verified
witness counts in every case, because verification does not depend on convergence.
* **H5 (the submitted claim of lost definiteness at k = 128).**
  * support: class N for `stencil` at k = 128;
  * contradiction: class P3 for `stencil` at k = 128, with every available p^st direction verified positive;
  * inconclusive: otherwise.

  If k = 128 is not run, H5 is *not tested in T22*, and the submitted statement rests on E29's record under its
  historical label.
* H1 is applied at k = 128 alone for `mean` and `diff`, as an extension outcome. The class of every form at k = 128
  is reported. None of these changes a k = 32–64 verdict.

### 9.7 Pre-registered expectations (not thresholds)

* **λ1 = λ2 for every form** (degenerate y/z bending), and λ3 = λ4 (T20, k = 4: λ3/λ1 ≈ 34).
* **The original stencil and the atomic form** shift every low eigenvalue down by about the same absolute amount. At
  k = 4 they are identical to seven digits, and both λ1 and λ3 drop by 4.0×10⁻⁸. E29's compliance ratios, read
  through the lowest mode, give about −5.0, −5.7, −6.1 and −6.4×10⁻⁸ at k = 8, 16, 32, 64.
* **Hence σ_1(stencil)** ≈ −0.13 at k = 32 (θ_1 ≈ 3.9×10⁻⁷) and ≈ −0.55 at k = 64 (θ_1 ≈ 5.3×10⁻⁸). A degenerate
  negative pair near −3.5×10⁻⁸ is expected at k = 128.
* **The diff and mean forms:** σ ≈ −1.0×10⁻⁶ and −5.7×10⁻⁶ (k = 4), unchanged with k.
* **The corner form:** a skew of about 8–10×10⁻⁹ and a growing negative shift (−7.1×10⁻⁵ at k = 4).
* **Skew:** the stencil forms exactly 0 and the element forms symmetric to rounding on this uniform beam.
* **The FP32 self-block correction** behaves like the original stencil on smooth inputs (E29 R1).

## 10. Validation before any confirmatory outcome (development set only)

1. **Block recovery:** at k = 4, against T20's CPU assembly (`t20_cpu`), all six forms. The blocks equal the assembled
   entries (stencil forms bit for bit, element forms within 10⁻¹⁵ of the largest entry); s_F and ‖A‖_F equal the
   dense values within 10⁻¹⁰ relative or 10⁻¹⁵ absolute; and the transpose cross-check agrees.
2. **Eigensolver:** against dense `eigvalsh` at k = 4 and SciPy `eigsh` (shift-invert about 0 on the CPU-assembled
   sparse S_F) at k = 8, all six forms, both starts. |θ_i − λ_i|/|λ_i| ≤ 10⁻⁶ for i = 1..3, and the stop target
   met.
3. **Indefinite capability and witness rule:** the k = 4 stencil matrix shifted by σ = (λ_1 + λ_3)/2 has a negative
   degenerate pair. The eigensolver must return its two negative eigenvalues within 10⁻⁶ of the dense values, and
   both must pass witness verification. Two planted cases must not verify: a positive vector, and the shifted matrix
   with σ = λ_1(1 + 10⁻¹⁴), whose negative quotient lies below ε.
4. **Recording copies:** the `pcg_energy` and `pcg32` copies that record directions reproduce the iterate histories
   of the unmodified copies at k = 16 bit for bit.
5. **G0 at k = 8 and 16** (part of the acceptance; §9.2).
6. **Analysis script** on the development outputs: every column filled, and every rule of §9 exercised on planted
   values, each giving the class this plan defines. The planted values are: a resolved and an unresolved shift, a
   verified and an unverified witness, inconsistent starts, a non-converged solve, a failed setup check, and the
   k = 128 not-run case.

A failure of items 1–4 is a code error. It is fixed before any confirmatory job and recorded in `DEVIATIONS.md`. The
parameters of §5, §6 and §9 do not change. If the frozen parameters converge slowly on the development grids, that
is not a reason to change them; the confirmatory solves then report what they reach.

## 11. Stopping rules

* **Solves:** the caps of §6.1. A capped or stagnated solve is reported as not converged and is not rerun.
* **Jobs:** a job stopped from outside (operator stop, or a crash with no output) may be rerun once from the start,
  recorded as such. A spill or allocation failure is a refusal for memory: the result is not kept, and the job is
  not rerun at the same size and configuration. At k ≤ 64 there is no smaller configuration, so the affected
  endpoints are reported missing.
* **Budget (compute rules):** T22 has 6 h of wall-clock compute, counted from its first GPU job (development
  included), and every experiment ends by Thursday 2026-11-26 18:00. When the budget is reached, no new job starts;
  a running job is finished or stopped between solves. The confirmatory k = 32 and 64 jobs run before any extension
  job. Sizes and forms not reached are named in the report. Not reaching them is not a failure of the task.
* **Study:** complete when every prespecified job has completed, failed or been refused, or the budget is reached. No
  grid, form, vector, block size, tolerance or threshold is added or changed after outcomes are seen.

## 12. Outputs (in `tasks/T22/`)

* **`spectrum.csv`:** rows of kind `matrix`, one per (k, form): s_F, s_F^T, ‖A‖_F, ‖A‖_∞, ‖A‖_1, skew label,
  class. Rows of kind `ritz`, one per (k, form, start, i): θ, ρ, ρ/|θ|, iterations, stop reason, drop counts,
  consistent, sign-resolved, converged, U(θ), quadratic bound, σ with U_σ and resolution, κ/|θ| with label, energy
  ratio, guard values. Labels: development, confirmatory or extension, and the G0 flag.
* **`action_checks.csv`:** one row per (k, vector or pair, action or form, repeat): vector set and origin, kind
  (`fp32_action` or `coefficient`), η, η_coef, η − η_coef, β, δ, |η − 1|, ε₀, the negative-energy flag, repeat
  identity.
* **`witnesses.json`:** every candidate with q_f, q_t, ε, ε₀, its verification result and the saved file.
* **`checks.json`:** setup checks, aid checks, the block-recovery cross-checks, T21 vector integrity, G0 and the
  k = 128 first-direction reproduction, admission and refusal records, and the spill-watch record per job.
* **`verdicts.json`:** G0, H1, H2, H2a, H4, H5 and the k = 128 H1, each with its inputs, its class and the rule clause
  that decided it.
* **`REPORT.md`, `DEVIATIONS.md`:** code in the task folder and `src/`, raw job outputs in `out/`. No figure is drawn
  here; the CSVs hold the data a figure needs.

## 13. Reporting rules

* Publish every estimate, including unresolved and unconverged ones (labelled), every witness candidate, and every
  adverse repair result (an H1 contradiction or a negative FP32 energy of a repaired kernel) in the same detail as
  favourable ones.
* A positive resolved eigenvalue is stated as a property of the resolved modes only. A verified negative Rayleigh
  quotient is stated as an established negative direction of that fixed rounded matrix. Neither is stated as a
  property of the FP32 action, the production solver or the V-cycle.
* Keep the kinds apart in every table and sentence:
  * coefficient-level results (fixed rounded matrices applied in FP64);
  * measured FP32 actions;
  * the FP64 production reference;
  * the preconditioning aid, which is never described as part of the result.

  The basis-column results of Table S22 and the general-input results of §6.5 are named separately: the
  self-block correction and the difference form share one coefficient matrix and differ only in evaluation.
* Positive symmetric-part energies alone do not establish symmetry of the PCG iteration or an SPD preconditioner.
* The results cover this uniform clamped beam on voxel grids. They say nothing about other layouts, contrasts or
  distorted elements. The bridge direction of A.2 comes from earlier records and is only cross-referenced.
* For the manuscript, no file names, tool names or run labels enter the main text, and no clock times, seeds, digests
  or run counts enter any text.

## 14. Feasibility and resolution (from data already open)

* **Smallest effect to resolve:** the stencil depression at k = 32, expected |σ_1| ≈ 0.13. With converged pairs,
  U(θ) ≤ 10⁻⁴|θ|, so U_σ ≤ 2×10⁻⁴, far below it. The repaired forms' expected shifts (about 10⁻⁶) are below the
  10⁻⁵ residual target. H1 is therefore decided by the bound |σ| + U_σ ≤ 10⁻⁴, which a converged pair meets.
* **Residual floor:** FP64 action rounding on a smooth unit vector is about u·‖S‖ ≈ 10⁻¹⁵ to 10⁻¹⁴ absolute,
  against |θ| ≥ 3×10⁻⁸ at k ≤ 128. That is at most 3×10⁻⁷ relative, below the 10⁻⁵ target.
* **Witness bound:** for a smooth unit vector, ‖w‖_∞‖w‖_1 is of order 1–10, so ε is about 10⁻¹² to 10⁻¹¹ against an
  expected |θ| of about 3.5×10⁻⁸ for the stencil at k = 128. A negative pair of that size is verifiable.
* **Memory:** see §8.2. k = 128 with b = 6 is predicted at about 18.6 GB plus the 1.5 GiB margin, against the
  22.6 GB driver-free memory T20 saw. Whether it is admitted is decided by the measured fit at launch.
* **Time:**
  * One S_F application is about 4.3 ms at k = 64 and 34–44 ms at k = 128 (T20, forward plus transpose). The V-cycle
    time and iteration counts come from the development jobs.
  * Skew: 2,268 applications per form, about 5 s at k = 64 and about 40 s at k = 128.
  * At k = 128, 12 solves at the 45 min cap would exceed the budget. The order of §8.1 runs the forms most relevant
    to A.2 and R3.3 first (ref, stencil, diff, mean) and the budget rule of §11 governs the rest.

## 15. Deviations

Any departure from this plan is recorded in `DEVIATIONS.md` with its reason and its effect on the endpoints. That
covers a code fix after the validation of §10, a refusal, a rerun after an outside stop, an excluded input vector,
or a budget stop. This file is not edited after freezing.
