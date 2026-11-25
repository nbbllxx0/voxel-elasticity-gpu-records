# T22: skew and lowest symmetric-part eigenvalues of the fixed rounded operators (clamped uniform beam)

Serves A.2 and R3.3 (Reviewer 3, point (2)). Frozen plan: `ANALYSIS_PLAN.md` (unchanged). Deviations: `DEVIATIONS.md`
(D1–D13). No language model is called anywhere in this study.

## Outcome against the acceptance statement

| acceptance clause | result | source |
|---|---|---|
| reproduce E29's raw FP64 λmin through k = 64 to 1e-4 relative | **met at every k**: relative differences 2.5e-11 (k = 8), 2.7e-10 (16), 4.5e-10 (32), 3.1e-9 (64) | `verdicts.json` → G0 |
| a resolved Ritz sign needs consistent starts and ‖Sv − λv‖/‖v‖ < 0.05\|λ\| | every wanted pair (6 forms × 3 pairs × k = 32, 64, 128) is consistent across starts A and B. The largest residual is 9.9e-6\|θ\| | `spectrum.csv` |
| positive values describe resolved modes only | stated so throughout; P3 below means "three lowest resolved positive" and nothing more | — |
| a verified negative Rayleigh quotient establishes a negative direction | at k = 128 the original stencil and the atomic element matrix each have verified negative directions. Four Ritz vectors per form pass the exact-summation rule; each Ritz vector has q/‖w‖² = −3.612e-8 against a bound of about 8e-12 | `witnesses.json` |
| publish unresolved estimates and any adverse repair result | the repaired forms' shifts are unresolved and are published with their bounds. There is no adverse repair result: no H1 contradiction, and no negative FP32 energy from either repaired kernel. The FP32 self-block correction, which is a comparator and not the paper's repair, gives negative measured energies (below) | `spectrum.csv`, `action_checks.csv` |

**Outcome: supports.** Every prespecified hypothesis has the class *support* under its frozen rule: H1, H2, H2a, H4
and the k = 128 extension H5 (`verdicts.json`). One prespecified part is missing. The k = 128 coefficient-skew job was
refused for memory and has not been rerun (D9, `decision_request.json`). Because of that, the full-matrix skew s_F and
its transposed-probe cross-check are missing at k = 128 for all six forms, the symmetry endpoint is open there, and the
k = 128 extension of H1 is inconclusive. Zero skew is measured at k = 32 and 64 only. The loss came from a departure
of the skew code from the plan's transfer rule (D11). All other k = 128 endpoints were completed.

## What was computed

Clamped 8×1×1 beam, `Grid(8k, k, k)`, E = 1, ν = 0.3. The confirmatory grids are k = 32 (839,619 DOFs) and k = 64
(6,502,275 DOFs). The extension is k = 128 (51,171,075 DOFs). The development grids are k = 4, 8 and 16. Three kinds of
object are kept apart:

* **Coefficient level:** the six fixed rounded matrices of T20, applied in FP64 on the free DOFs. They are `ref` (the
  FP64 production operator), `stencil` (the original FP32-coefficient stencil), `diff` (the stencil difference form),
  `atomic` (Σ E P^T fl32(K0) P), `corner` (the corner reference) and `mean` (the element-mean reference).
  S_F = (A_F + A_F^T)/2.
* **Measured FP32 actions:** the production FP32 kernels, each paired with its coefficient matrix. `stencil_selfcorr`
  (the self-block correction) and `stencil_diff` share the matrix `diff`.
* **Preconditioning aid:** E29's common V-cycle. It shapes only the eigensolver's search space. Every Ritz value,
  residual and Rayleigh quotient below is an FP64 evaluation with the matrices themselves.

The coefficient skew comes from 27-colour × 3-component probes. These recover every 3×3 block of the free-DOF matrix,
2,268 forward applications per form. A transposed-probe cross-check agreed for every form at every grid from k = 4 to
64 (`checks.json` → `block_recovery_cross_checks`). At k = 128 neither s_F nor the cross-check exists (D9). The
spectra come from an in-place block LOBPCG with block size 6 and two seeded starts. All 24 solves at k = 32 and 64
(six forms × two starts × two grids), and all 12 at k = 128, reached the stop target (all three wanted relative
residuals ≤ 1e-5) in 12–13 iterations, with no basis drops (`summary.json` → `n_solves`, `drops_total_max`). The acceptance definitions are those of plan 6.2.

Validation before any confirmatory job passed (`out/dev_check.json`):
1. The probe-recovered blocks at k = 4 equal T20's independent CPU assembly. The stencil forms agree bit for bit and the
   element forms within 1e-15 of the largest entry.
2. Eigenvalues agree with dense `eigvalsh` (k = 4) and with shift-invert `eigsh` (k = 8) within 1e-6.
3. On the shifted k = 4 stencil, the negative degenerate pair was found and verified. Both planted cases were rejected.
4. The direction-recording copies of E29's `pcg_energy` and E8's `pcg32` reproduce the unmodified copies bit for bit
   at k = 16.
5. G0 held at k = 8 and 16.

The analysis script was run on the development outputs, with every rule exercised on planted values, before the
confirmatory outputs were opened (`out/dev_analysis/`, `verdicts.json` → `planted_rule_tests`).

## Results

### Coefficient skew s_F = ‖A − A^T‖_F / ‖A‖_F (`spectrum.csv`, kind `matrix`)

| form | k = 32 | k = 64 | k = 128 |
|---|---|---|---|
| ref | 2.64e-17 (symmetric to FP64 assembly rounding) | 2.62e-17 | missing (D9) |
| stencil | 0 | 0 | missing |
| diff | 0 | 0 | missing |
| mean | 0 | 0 | missing |
| atomic | 0 | 0 | missing |
| corner | 7.43e-9 (coefficient skew) | 7.38e-9 | missing |

At k = 32 and 64 the measured skew of the stencil, difference, element-mean and atomic matrices on the free DOFs of
this uniform beam is zero: they are exactly symmetric there. The ref value comes from K0 not being bitwise symmetric.
Only the corner reference carries a coefficient skew, and its size matches T20's k = 4 value (8.2e-9). At k = 128 the
full-matrix skew was not measured for any form (D9), so exact symmetry is not established at that grid. The k = 128
results below rest on the eigensolves, on forward and transposed actions applied to the Ritz vectors (the low-mode skew
κ) and on the witnesses, none of which uses s_F.

### Lowest eigenvalues of S_F and shifts against the FP64 operator (`spectrum.csv`, kind `ritz`, start A)

σ_i = θ_i(F)/θ_i(ref) − 1, with uncertainty U_σ. "res." means |σ| ≥ 10 U_σ (plan 6.2).

| k | form | θ1 = θ2 | θ3 | σ1 (U_σ) | σ3 (U_σ) | class |
|---|---|---|---|---|---|---|
| 32 | ref | 4.524883e-7 | 1.553419e-5 | — | — | P3 |
| 32 | stencil | 3.899417e-7 | 1.547172e-5 | −0.1382 (9.5e-6), res. | −4.02e-3 (3.4e-6), res. | P3 |
| 32 | atomic | 3.899417e-7 | 1.547172e-5 | −0.1382 (9.5e-6), res. | −4.02e-3 (3.2e-6), res. | P3 |
| 32 | diff | 4.524879e-7 | 1.553418e-5 | −1.06e-6 (8.6e-6), unres. | −1.9e-7 (3.2e-6), unres. | P3 |
| 32 | mean | 4.524857e-7 | 1.553417e-5 | −5.85e-6 (1.0e-5), unres. | −1.1e-6 (3.5e-6), unres. | P3 |
| 32 | corner | 4.522433e-7 / 4.522436e-7 | 1.553395e-5 | −5.41e-4 (7.8e-6), res. | −1.56e-5 (3.2e-6), unres. | P3 |
| 64 | ref | 1.170264e-7 | 4.020183e-6 | — | — | P3 |
| 64 | stencil | 5.228071e-8 | 3.955480e-6 | −0.5533 (4.8e-6), res. | −1.61e-2 (3.5e-6), res. | P3 |
| 64 | atomic | 5.228071e-8 | 3.955480e-6 | −0.5533 (3.9e-6), res. | −1.61e-2 (3.5e-6), res. | P3 |
| 64 | diff | 1.170263e-7 | 4.020182e-6 | −1.05e-6 (1.0e-5), unres. | −1.9e-7 (5.5e-6), unres. | P3 |
| 64 | mean | 1.170257e-7 | 4.020178e-6 | −5.85e-6 (1.0e-5), unres. | −1.1e-6 (5.6e-6), unres. | P3 |
| 64 | corner | 1.169003e-7 / 1.169004e-7 | 4.020061e-6 | −1.08e-3 (1.1e-5), res. | −3.02e-5 (5.4e-6), unres. | P3 |
| 128 | ref | 2.976626e-8 | 1.022898e-6 | — | — | P3 |
| 128 | stencil | **−3.611995e-8** | 9.570345e-7 | −2.213 (5.5e-6), res. | −6.44e-2 (2.3e-6), res. | **N** |
| 128 | atomic | **−3.611995e-8** | 9.570345e-7 | −2.213 (5.4e-6), res. | −6.44e-2 (2.3e-6), res. | **N** |
| 128 | diff | 2.976623e-8 | 1.022898e-6 | −1.04e-6 (4.2e-6), unres. | −1.9e-7 (2.5e-6), unres. | P3 |
| 128 | mean | 2.976608e-8 | 1.022897e-6 | −5.84e-6 (5.0e-6), unres. | −1.1e-6 (2.4e-6), unres. | P3 |
| 128 | corner | 2.970220e-8 / 2.970233e-8 | 1.022838e-6 | −2.15e-3 (4.7e-6), res. | −5.94e-5 (2.3e-6), res. | P3 |

The value uncertainties U(θ) are at most 9.9e-6 |θ| on every grid. The two starts agree to that level, and every k = 128
row converged in both starts, so every k = 128 row counts as *added* (plan 9.6). As expected, λ1 = λ2 for every form,
with the degenerate bending pair split only for the corner form. The original stencil and the atomic element matrix
agree to all printed digits.

**Repaired forms (H1).** For `mean` and `diff`, |σ_i| + U_σ is at most 2.18e-5 (mean) and 1.70e-5 (diff) over
i = 1..3 at k = 32 and 64, and 1.09e-5 and 6.9e-6 at k = 128 (`summary.json` → `repaired_max_sigma_bound`). Their shifts
are below the resolution of the eigen-solves. The dense k = 4 shifts (−1.02e-6 for diff, −5.68e-6 for mean;
`summary.json` → `k4_dense_sigma1`) are consistent with those unresolved estimates. **H1: support** at k = 32 and 64 for both forms, so overall support. At
k = 128 the repaired forms are again P3 with bounds below 1e-4. The k = 128 extension of H1 is nevertheless
inconclusive, only because s_F is missing there (D9).

**Original stencil (H2) and atomic element matrix (H2a).** The depression of the lowest eigenvalue is resolved and grows
under refinement: σ1 = −0.138 at k = 32, −0.553 at k = 64 and −2.213 at k = 128, where the symmetric part becomes
indefinite. **H2: support; H2a: support** (growth clause). In absolute terms the lowest eigenvalue drops by
6.25e-8 (k = 32), 6.47e-8 (k = 64) and 6.59e-8 (k = 128) (`summary.json` → `lowest_eigenvalue_drop_abs`). That is
close to the constant downward shift that plan 9.7 expected. At k = 4 the dense drop is σ1 = −2.08e-3
(`summary.json` → `k4_dense_sigma1`).

**k = 128 (H5).** The stencil and atomic matrices each give a degenerate negative pair, −3.611995e-8, with converged and
consistent Ritz pairs. Every negative Ritz vector (pairs 1 and 2, both starts) is verified negative by exact host
summation in both the forward and the transposed action. The numbers are q_f/‖w‖² = q_t/‖w‖² = −3.612e-8 against
ε of 7.9e-12 to 8.7e-12, and an energy ratio q/ε₀ of −1.2135. The first search direction of E29's `pcg_energy` on the
stencil matrix enters in two forms, which are different vectors (`checks.json` → `k128_first_direction.vectors`):
* the FP64 direction as E29's code forms it: its energy ratio, −1.1385383514247778, reproduces E29's recorded value
  digit for digit;
* the same direction scaled to unit maximum and rounded to FP32 (vector st1), which the exact-summation witness rule
  verifies as negative: q_f = −0.14202 against ε = 3.2e-5, energy ratio −1.1385382176691647, 1.17e-7 relative from E29's
  value (`witnesses.json`).

Both have negative energy on their own vector; only the first is the digit-for-digit reproduction. **H5: support.** The
original rounded stencil has an established negative direction on the free DOFs of the k = 128 beam.

### Skew on the low-mode scale (H3, descriptive; `spectrum.csv`, `kappa_rel`)

κ_i/|θ_i| = ‖(A − A^T)x_i‖/(2‖x_i‖|θ_i|), largest over the three wanted modes and both starts:

| form | k = 32 | k = 64 | k = 128 |
|---|---|---|---|
| ref | 1.6e-10 | 6.3e-10 | 2.5e-9 |
| stencil, diff, mean, atomic | ≤ 9.0e-10 | ≤ 3.5e-9 | ≤ 1.4e-8 |
| corner | 1.34e-2 | 3.74e-2 | **0.105** |

All forms except `corner` have skew far below the low-mode scale. The corner reference's skew, s_F ≈ 7.4e-9 of the
largest-scale norm, reaches 1.3 %, 3.7 % and 10.5 % of its lowest eigenvalue at k = 32, 64 and 128. At k = 128 this
is *comparable to the low-mode scale* (≥ 0.05). This is where R3.3's one-sided-projection concern shows up for a
concrete operator. At k = 128 the corner form's lowest modes of S_corner are approximate eigenvectors of A_corner
itself only to within about 10 % of the eigenvalue (residual bound ρ + κ). The element-mean form also applies its
projection on one side, but here it has s_F = 0 at k = 32 and 64 (not measured at k = 128) and a low-mode skew κ/|θ| of
at most 3.4e-10, 1.3e-9 and 5.3e-9 at k = 32, 64 and 128 over the three wanted modes and both starts (at k = 128,
3.23e-9 for the first mode of start A and 5.32e-9 at most; `spectrum.csv`), far below the frozen 0.05 threshold.

### Measured FP32 actions on general inputs (H4, A.2; `action_checks.csv`)

η(x) = x^T fl32(A₃₂ x₃₂)/ε₀(x) on selected vectors (repeat 1). The low-mode vectors are the FP64 operator's Ritz
vectors; st1 is the first PCG search direction.

| k | action | low1 | low2 | low3 | sm1 | sm3 | st1 |
|---|---|---|---|---|---|---|---|
| 32 | stencil_selfcorr | −0.0446 | −0.0609 | 0.970 | 1.0000 | 0.994 | −0.0299 |
| 32 | stencil_diff | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| 32 | stencil (original) | 0.862 | 0.863 | 0.996 | 1.0000 | 0.999 | 0.867 |
| 64 | stencil_selfcorr | −3.33 | −3.36 | 0.876 | 0.9999 | 0.972 | −3.22 |
| 64 | stencil_diff | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| 64 | stencil (original) | 0.449 | 0.449 | 0.984 | 1.0000 | 0.996 | 0.465 |
| 128 | stencil_selfcorr | −16.6 | −16.7 | 0.494 | 0.9998 | 0.893 | −16.1 |
| 128 | stencil_diff | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 | 1.0000 |
| 128 | stencil (original) | −1.215 | −1.214 | 0.936 | 1.0000 | 0.987 | −1.123 |

* **H4: support.** On the smooth and low-mode set, the median energy defect m = median |η − 1| is 1.82e-2 (k = 32) and
  7.61e-2 (k = 64) for the FP32 self-block correction, against 2.50e-7 and 3.41e-7 for the FP32 difference form. The
  ratios are 7.3e4 and 2.2e5 (`summary.json` → `H4_ratio_selfcorr_over_diff`). Both actions are paired with the same coefficient matrix, and their
  coefficient-level energies are identical (`eta_coef_identical`, η_coef = 0.999999 on these vectors). The difference
  is therefore entirely a general-input evaluation effect, invisible in unit-vector (basis-column) matrices.
* **Negative measured FP32 energies.** These are a property of the measured action on the vector, not an eigenvalue
  statement. They count only where η < 0 in all three repeats with |x^T A₃₂ x₃₂| above the product-rounding bound.
  * The FP32 self-block correction is negative on 10 vectors at k = 32, 7 at k = 64 and 9 at k = 128. These include the
    lowest bending modes and the first search direction at every k. At k = 32 the ten include the three T21 vectors,
    which are solutions there. At k = 128 two of the nine (u_ref and e_coef) are built from the diverged T21 iterate
    (D10); without them the count is 7 (`summary.json` → `actions` → `negative_vectors_diverged_t21`).
  * The FP32 original stencil and the FP32 atomic element kernel are negative on 7 vectors each at k = 128, following
    their coefficient matrices. They are negative on none at k = 32 and 64.
  * The two repaired FP32 kernels (`stencil_diff`, `elem_mean`), the corner-reference kernel and the FP64-arithmetic
    control are negative on no vector at any k.
* **Energy defects of the repaired FP32 kernels.** The largest |η − 1| over every vector is 2.3e-6, 1.5e-6 and 2.9e-6
  for `stencil_diff` at k = 32, 64 and 128. For `elem_mean` it is 9.0e-6, 1.1e-5 and 2.7e-5.
* **Bilinear defects of the repaired FP32 kernels.** The largest normalised bilinear skew β is 1.9e-6, 6.6e-7 and
  4.6e-7 for `stencil_diff`, and 2.8e-6, 4.4e-6 and 1.3e-5 for `elem_mean`. The largest bilinear defect δ against the
  FP64 reference energy is at most 1.5e-5.
* **Bilinear defects of the original kernels.** For the FP32 original stencil and the self-block correction, β reaches
  4.3e-3 and 5.4e-3. The largest δ, 0.29 and 2.34, belong to the pair u_ref | e_coef at k = 128, which is built from
  the diverged T21 iterate (D10). On the other pairs δ reaches 0.21 (stencil, st1 | st2 at k = 64) and 1.63
  (self-block correction, p32_1 | p32_2 at k = 64). At coefficient level, the symmetric stencil forms have
  β ≤ 2.2e-12; the remaining FP32 β is application rounding.
* **Repeats.** The median and range of η, |η − 1|, β and δ over the three repeats are in `action_repeats.csv`. The
  stencil kernels and the FP64-arithmetic control were bitwise identical across the three repeats (range 0). The
  element kernels (atomic, corner and element-mean) were not, as T20 found: their largest η range is 8.2e-8 (atomic),
  4.0e-8 (corner) and 1.3e-7 (element mean), and their largest β range 4.7e-7.
* **T21 vectors.** At k = 64 and 128 the rows of u_ref, e_coef and e_ctrl are labelled in `action_checks.csv`
  (`origin`, `t21_reference_status`) as the diverged reference iterate and differences from it, not as a solution and
  solution errors (relative K0 residuals 3.71e39 and 5.11e39). They enter no test.

### Aid and setup checks (`checks.json`)

Every setup check passed in every job: moduli all 1, load −1, K0 equal to `ke_unit(0.3)`, the free mask, and the six
forward/transpose dot tests with a largest relative error of 8.9e-18 (`summary.json` →
`dot_test_max_rel_all_valid_runs`). x^T T x > 0 held for every random and smooth
vector at every k. The aid's symmetry defect is 6.8e-7 or smaller at k = 16–128 and 1.95e-5 at k = 4. That is expected,
because the cycle rounds its input to FP32. The aid enters no reported value.

## Memory, admission and coverage (`checks.json` → `runs`, `out/runs/*/monitor.json`)

* **Admission.** Each job was admitted on the plan 8.2 rule, with the per-phase fit of D2. The k = 128 gate predicted
  20.24 GB for J_eig with b = 6, against 22.66 GB that nvidia-smi reported free; that fits with the 1.5 GiB margin
  (`out/k128_gate.json`). The stricter `guard.require_budget`, which counts the desktop's dedicated memory, said *no*
  for the six k = 128 J_eig jobs. Under the authors' decision of 2026-11-23 this is recorded for information only.
* **Peaks and spill.** The measured dedicated peaks of the k = 128 J_eig jobs were 18.99 GB. Shared-memory growth was
  115 MB in every completed k = 128 job and at most 48 MB at k ≤ 64. Coverage is stated from the first complete watch
  sample. Two guard details of the job version that ran differed from plan 8.2 (D12): the child created its context
  with a one-element allocation before the first complete sample and set its pool cap only after it, and it wrote its
  in-process `guard.require_budget` answer only at normal completion. That answer is therefore missing for the refused
  k = 128 J_skew job (and for the two crashed development runs); the launcher's own admission record exists for every
  job. Every retained job has a passing monitor record from the first complete sample onward.
* **Refusal.** The k = 128 J_skew job was refused for memory (384 MB shared growth) and was not rerun (D9). The skew
  code copied three node-index arrays of 136,456,200 B each to the device in single transfers, against plan 8.1's rule
  of copies in pieces (D11).
* **Compute time.** All GPU work, development included, ran from 13:08 to 14:02 on 2026-11-24, within the 6 h budget.

## Limitations

* The results cover this clamped uniform beam on voxel grids, and nothing else. They say nothing about other layouts,
  contrasts or distorted elements.
* P3 describes the three lowest *resolved* modes. A block method can miss a lower mode, so P3 does not establish that
  S_F is positive definite, that PCG on A_F is well defined, or that any preconditioner is SPD.
* The repaired forms' shifts (|σ| of about 1e-6 to 6e-6) are not resolved by these solves. They are bounded by 2.2e-5.
* The k = 128 coefficient skew and its cross-check are missing for all six forms (D9, D11), and with them the
  k = 128 symmetry endpoint and the k = 128 H1 extension. Exact symmetry is measured at k = 32 and 64 only.
* T21's saved reference vectors at k = 64 and 128 are diverged iterates, not solutions (D10). The u_ref, e_coef and
  e_ctrl rows at those k describe one diverged vector, and they enter no test. The first search direction is the same
  preconditioned load vector in all three direction families, so st1, K1 and p32_1 coincide up to FP32 rounding.
* The development J_act records at k = 8 and 16 predate the p^st verification field (D7, D8).

## Notes for the manuscript and the response (wording for the writers; no file names or run detail)

* Fixed rounded matrices on the clamped uniform beam's free DOFs, applied in FP64:
  * The original FP32-coefficient stencil, and the element kernel with FP32-rounded element matrix, are exactly
    symmetric at the two grids where the skew was measured (k = 32 and 64).
  * The lowest eigenvalue of their symmetric part falls below the FP64 operator's by 14 % (k = 32) and 55 % (k = 64).
  * At k = 128 they have a verified negative direction (a degenerate pair at −3.61e-8 against +2.98e-8 for the FP64
    operator).
  * The first PCG search direction on that matrix already has negative energy, −1.14 times its FP64 energy.
* The two repairs (element-mean reference and stencil difference form) are exactly symmetric at k = 32 and 64. Their
  three lowest eigenvalues are resolved, positive, and equal to the FP64 operator's within 2.2e-5 relative at every
  grid up to k = 128. At k = 128 the symmetry of the full matrices was not measured; only their low-mode skew is
  known there (at most 1.4e-8 of the eigenvalue).
* The corner reference is the one form with a coefficient skew (7.4e-9). On its lowest modes that skew grows to 10 %
  of the eigenvalue at k = 128.
* Measured FP32 actions:
  * The self-block correction and the difference form share one coefficient matrix and coincide on unit vectors.
  * On general inputs the FP32 self-block correction is far less accurate: on the lowest bending modes its measured
    energy is negative already at k = 32 (−0.04 to −0.06 of the FP64 energy) and reaches −17 at k = 128.
  * The FP32 difference form reproduces the FP64 energy within 3e-6, and the FP32 element-mean kernel within 3e-5.
* These are statements about fixed matrices and measured actions on one beam. They do not establish that the
  production PCG iteration is symmetric or that the V-cycle is SPD.

## Fix round 1 (checker's review; CPU only, no GPU job, no measured value changed)

1. *Symmetry at k = 128.* Exact symmetry is now stated for k = 32 and 64 only. The k = 128 skew and its cross-check are
   reported as missing for all six forms, and the k = 128 symmetry endpoint as open (outcome, coefficient skew,
   limitations, notes for the writers).
2. *k = 128 first direction.* The FP64 PCG direction (−1.1385383514247778, E29's value exactly) and the FP32-rounded
   unit-maximum witness vector (−1.1385382176691647, verified negative) are reported as two vectors
   (`checks.json` → `k128_first_direction.vectors`).
3. *Element-mean low-mode skew.* The bound is corrected to 5.3e-9 at k = 128 (3.23e-9 for the first mode of start A).
4. *T21 vectors.* `t22_analyse.py` labels the k = 64 and 128 T21 rows from the recorded K0 residual as the diverged
   iterate and differences from it (`origin`, new column `t21_reference_status`). `t22_job.py` labels them the same
   way for any future run. The report now says which negative-energy count and which largest δ come from these
   vectors.
5. *Repeat summaries.* `action_repeats.csv` gives median, minimum, maximum and range over the three repeats for every
   FP32 action, vector and pair, from the saved records.
6. *Transfer rule.* Recorded as D11. The probe colouring now forms its index arrays on the device, and the moduli are
   uploaded in pieces. The free-DOF mask upload inside T20's operator class stays as T20 verified it and is named in D11.
7. *Guard details.* Recorded as D12. The child now creates its context through the driver's free-memory query, with
   no allocation, sets its pool cap before it reports the context, allocates nothing before 'go', and writes its
   in-process budget answer to `admission_in_process.json` at once.

`t22_fix_r1_test.py` tests points 6 and 7 on the CPU (`out/fix_r1/code_tests.json`). The device-side indices and
colours equal the first version's for five node shapes. No grid-sized one-shot `cp.asarray` is left in the T22 code.
With a recording stand-in for CuPy, the child makes no allocation before 'go', sets its cap before 'ctx' and writes
the admission file before its first setup step. The first version's code, restored, fails both checks as planted-fault
controls. A diff against `out/before_fix_r1/` shows that `spectrum.csv`, `witnesses.json` and `verdicts.json` are
unchanged. `action_checks.csv` differs only in the three relabelled `origin` texts and the added status column, and
`checks.json` and `summary.json` gain only added fields.

## Files

* Endpoints: `spectrum.csv`, `action_checks.csv`, `action_repeats.csv`, `witnesses.json`, `checks.json`,
  `verdicts.json`, `summary.json`.
* Records: `DEVIATIONS.md`, `decision_request.json`, `out/fix_r1/code_tests.json`, `out/before_fix_r1/` (outputs before
  fix round 1).
* Code: `t22_common.py`, `t22_gpu.py`, `t22_job.py`, `t22_launch.py`, `t22_launch_selftest.py`, `t22_queue.py`,
  `t22_cpu.py`, `t22_dev_check.py`, `t22_analyse.py`, `t22_summary.py`, `t22_fix_r1_test.py`; copies of the authors'
  and T20's code in `src/`.
* Raw outputs: `out/data/k*/` (skew, eigen and action records, start-A Ritz vectors), `out/witness_*.npy`, `out/runs/`
  (monitors), `out/dev/`, `out/dev_check.json`, `out/dev_analysis/`, `out/launch_selftest.json`, `out/budget.json`,
  `out/k128_gate.json`, `out/queue.log`.
