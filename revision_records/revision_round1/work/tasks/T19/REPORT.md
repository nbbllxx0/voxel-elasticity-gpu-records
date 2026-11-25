# T19 report: reference-change identity and the weighted eight-cell patch

This task serves R1.3, R2.4, R3.1, R3.2 and R3.3. It is not prespecified. It made no language-model calls and ran one
GPU job.

## What was done

* **Exact element matrix.** I derived the exact unit element matrix in rational arithmetic and checked the authors'
  FP32 element matrix $Q$ against it: $QT$, symmetry, the 48 cube symmetries, $PQ-QP$, and the skew of the element
  reference operators. The results are in `coefficients.json`.
* **Stencil blocks.** I extracted the production stencil blocks $W_r(n)$ by unit-vector application of the authors'
  FP32 and rounded-coefficient kernels in four layouts, and checked:
  * agreement between the two kernels;
  * an FP32 emulation of the coefficient formation;
  * opposite weights $W_r$ against $W_{-r}$ by node class;
  * global and reflection symmetry;
  * row sums.
* **Patch actions.** On the free 2×2×2-cell patch I applied the following to 61 input fields (16 translations; 9
  gradients, 3 strains and 3 rotations, each in three placements) in four layouts (uniform; planar 8:1 interface through
  the centre; both at modulus scale 0.7):
  * the exact matrix, in exact rational arithmetic and in FP64;
  * the rounded coefficients applied in FP64: original, corner and mean element forms, and original, difference and
    self-block-corrected stencil forms;
  * the production FP32 kernels (`stencil`, `stencil_diff`, `stencil_selfcorr`, `elem_atomic`, `elem_ref`,
    `elem_mean`), all on identical FP32-represented inputs.

  The outputs are recorded separately in four files:
  * `affine.csv`: raw forces, same-input FP64 forces, excess over FP64 and excess over the exact force on the same
    input, by node and node class. The exact excess is filled for every row: the coefficient forms evaluated exactly,
    the FP64 and FP32 outputs minus the exact force with the difference taken exactly, and 0 for the exact-force rows
    themselves (`K0_exact`), whose excess over the exact force is identically zero;
  * `local_contributions.csv`: per-element contributions with their excess over the `ke_unit` FP64 contribution of the
    same element, from FP64 coefficients and from FP32 single-cell kernel runs. The analysis writes the values from
    memory with round-trip formatting, and the summary reads them with round-trip parsing and does not rewrite the
    file, so every FP32 local value is the raw kernel output exactly;
  * `node_class_summary.csv`: maxima by node class;
  * `summary.json`: the checks.
* **Write-up.** The derivation and every conclusion are in `derivation.md`.

**GPU job** (`out/run1/monitor.json`):

| item | value |
|---|---|
| admission | nvidia-smi free 22.6 GB against a predicted peak of 1 GiB plus the 1.5 GiB margin |
| guard.require_budget (in process) | ok |
| pool cap | 22.5 GB |
| watch | covered from the first sample that held the job process with both counters. Before that sample the job had created its CUDA context and one one-element array; the pool cap and the budget check followed it. A final sample was checked after the job reported done |
| shared usage at the first covered sample (baseline) | 77,594,624 B |
| shared-memory growth from that baseline | 2 MiB (limit 256 MiB) |
| status | ok, valid, no spill |

## Results against the acceptance statement

* **The identity agrees at FP64 accuracy.** In exact rational arithmetic there are 0 mismatches in 79,056 component
  checks. In FP64 the largest deviation is $8.8\times10^{-15}$, or $4.4\times10^{-16}$ of the term scale.
  $QT=cT$ holds exactly with $c=-9/2^{30}=-8.381903171539307\times10^{-9}$. Since $QP=cP$, $PQ-QP=0$ exactly.
* **The axial example reproduces the verified values exactly.** For $u=(x,0,0)$ at the uniform interior node:
  * the corner excess is $-3.3527612686\times10^{-8}=4c$;
  * the mean excess is exactly 0.

  At the 8:1 interface:
  * the physical force is $2.355769230769231$;
  * the mean excess is $+2.745610590\times10^{-8}$.
* **The translation guarantee holds in the raw output.** For `elem_ref`, `elem_mean` and `stencil_diff`, all 62,208 raw
  FP32 entries are exactly zero: 16 translations up to amplitude $1.2345\times10^7$, four layouts, every repeat, no
  negative zeros. The original forms give nonzero translation forces. At unit amplitude the FP32 original stencil gives
  up to $3.95\times10^{-7}$ and the original element kernel $1.28\times10^{-7}$.
* **Every node class and discrepancy is reported.** The node classes are listed in `node_class_summary.csv`; the
  discrepancies are in `derivation.md` §8 and below.
* **Cancellations that survive weighted assembly** (`derivation.md` §6):
  * Translations cancel algebraically in every reference form, at every node.
  * The mean-reference affine cancellation happens at assembly. Equal moduli in all eight cells are sufficient for it,
    not necessary: equal weights within each inversion-related pair of cells (the two cells opposite across the node)
    also suffice, because the two cells of such a pair give opposite forces at the centre. In exact rational arithmetic,
    four pairs with four different weights give exactly 0 for all nine gradients (`out/fix_r8/checks.json` →
    `inversion_pair_weights_mean_reference_centre`). Individual cells carry up to $1.1\times10^{-8}$, and the uniform
    interior sum is exactly 0 at coefficient level, by the reflection invariance of $Q$. At an 8:1 interface every
    inversion pair joins the two moduli; the excess follows an exact selection rule and is nonzero.
  * The corner term $c(\sum E)Bd$ is coherent and never cancels.
  * The difference form's affine excess is the difference between the first moments of its rounded and exact blocks.
    At the homogeneous interior node, where the exact first moment is zero, it cancels affine fields where the first
    moment of the rounded blocks vanishes. Coinciding opposite weights are sufficient for that, not necessary. At the
    uniform centre the moment is exactly 0 at $E=1$ and reaches $1.60\times10^{-9}$ at $E=0.7$ (`summary.json` →
    `uniform_centre_difference_first_moment`). At an interface or boundary node, zero affine excess needs the rounded
    and exact first moments to agree. In the axial interface row they do not: the rounded action is $2.3557692729$,
    a coefficient excess of $4.21244\times10^{-8}$ (`summary.json` → `axial_example`; `out/fix_r8/checks.json`).
  * All of these cancellations are exact for the rounded coefficients in rational arithmetic on exactly affine inputs.
    Applying the coefficients in FP64 leaves a rounding residue, up to $9.7\times10^{-17}$ ($E=1$) and
    $1.1\times10^{-16}$ ($E=0.7$) for the mean reference at the uniform centre (`uniform_centre_exact_vs_fp64_application`).
* **Rotations (R2.4)** (`summary.json` → `rotations`; `derivation.md` §6):
  * The physical force (the exact matrix applied to the input actually used) is exactly zero where that input is an
    exact rotation: P0 and P1, and in the offset placement P2 the FP32 `rot_x` field. FP32 representation does not
    destroy every rotation in P2: the P2 $x$-axis rotation stays rigid, with zero exact physical force in all 108
    node-layout cases. The $y$- and $z$-axis rotations of P2 are changed by the rounding and give all 216 nonzero cases
    of the 324, up to $2.29\times10^{-8}$, for example a $y$ force of $2.2924863\times10^{-8}$ for `rot_z` at the
    uniform centre (`out/fix_r8/checks.json` → `p2_u32_rotation_physical_force_by_axis`). That force belongs to the
    input and is kept apart from the operator excess.
  * No tested form preserves every rotation across the patch: every form's maximum excess is nonzero.
  * Individual fields and nodes do cancel exactly:
    * At coefficient level the mean reference is exactly zero at the uniform interior node for all rotations at both
      moduli; the difference form is exactly zero there at $E=1$.
    * The mean reference is also exactly zero for `rot_x` at the 8:1 interface centre, and in 72 of 288 boundary-face
      cases (for example `rot_x` at face node 4).
    * The production FP32 difference kernel returns the zero vector for `rot_x` at the uniform centre ($E=1$, P0).
  * The largest FP32 rotation excess over the exact force at the uniform centre ($E=1$, P0) ranges by form from
    $7.5\times10^{-9}$ (difference kernel) to $4.8\times10^{-7}$ (self-block correction). At P2 the reference and difference forms stay within $0.7$–$5.3\times10^{-10}$ of the
    physical force, against $4.7\times10^{-8}$ (original element kernel), $6.3\times10^{-8}$ (original stencil) and
    $1.4\times10^{-7}$ (self-block correction).

## Discrepancies found

1. **Production FP32.** No FP32 form cancels every affine field at the uniform interior node. Application rounding
   leaves up to $1.2\times10^{-7}$ for the corner and mean references, $1.5\times10^{-7}$ for the original element
   kernel, $8.2\times10^{-8}$ for the difference form, $3.1\times10^{-7}$
   for the original stencil and $9.5\times10^{-7}$ for the self-block correction. Single cases do cancel exactly: 32 of
   540 field-form cases, 19 of them from the difference kernel (`summary.json` →
   `fp32_uniform_centre_exact_cancellation`). The reference forms' advantage appears when the input carries a translation part: in the offset
   placement the uniform interior node gives about $1.4$–$1.6\times10^{-9}$ for the reference forms, against
   $7.0\times10^{-8}$ (original element kernel) and $1.7\times10^{-7}$ (original stencil). "Zero to calculation
   precision" in the plan holds at coefficient level only.
2. **Opposite weights at E = 0.7.** The submitted premise that equal weights round to equal values fails at $E=0.7$:
   3 of 13 opposite pairs at the uniform interior node differ, by up to $1.6\times10^{-9}$. The cause is the residue of
   exactly-zero entries formed from opposite-sign groups under fused multiply-add contraction. The difference-form
   coefficient excess there is $1.6\times10^{-9}$ instead of 0. At $E=1$ all 13 pairs are bitwise equal.
3. **8:1 interface.** At the interior interface node the largest coefficient excess over the 15 unit-gradient, strain
   and rotation fields depends on the form and on the absolute moduli (`summary.json` →
   `interface_centre_coef_max_by_form`):

   | form | moduli $1\,\vert\,1/8$ | moduli $0.7\,\vert\,0.0875$ |
   |---|---|---|
   | original element | $3.77\times10^{-8}$ | $2.64\times10^{-8}$ |
   | corner reference | $3.76\times10^{-8}$ | $2.63\times10^{-8}$ |
   | mean reference | $3.76\times10^{-8}$ | $2.63\times10^{-8}$ |
   | difference form | $4.21\times10^{-8}$ | $6.02\times10^{-8}$ |
   | original stencil | $8.61\times10^{-8}$ | $1.10\times10^{-7}$ |
   | self-block correction | $1.68\times10^{-7}$ | $7.06\times10^{-7}$ |

   The element and reference forms scale with the moduli. The three stencil forms do not, because the kernel forms their
   rounded weights in FP32 for each modulus value. The maximising field depends on the form (for example $g_{yy}$ for
   three forms at $1\,|\,1/8$; $g_{xz}$ for the original stencil and the self-block correction at $0.7\,|\,0.0875$).
   The physical force 2.356 is that of the axial field alone ($1\,|\,1/8$). Its $x$ excesses are $+2.75\times10^{-8}$
   (mean), $+8.60\times10^{-9}$ (corner), $+4.41\times10^{-9}$ (original element), $+4.21\times10^{-8}$ (difference)
   and $-1.75\times10^{-8}$ (original stencil). Its physical $y$ and $z$ forces are exactly 0. Its transverse excesses
   are exactly 0 for the original element, corner, mean and difference forms. They are not 0 for the original stencil
   ($z$: $-1.862645\times10^{-9}$) or the self-block correction ($y$: $-1.303852\times10^{-8}$, $z$:
   $+1.862645\times10^{-9}$). These come from off-diagonal entries of the kernel's rounded row sums. In the uniform patch
   ($E=1$) the self-block correction also gives a $y$ excess of $-4.47\times10^{-8}$ for this field
   (`summary.json` → `axial_example`). The stencil kernel's rounded weights break the layout's $y/z$ reflection symmetry,
   by up to $7.45\times10^{-9}$ at moduli $1\,|\,1/8$; at $0.7\,|\,0.0875$ the $y$-reflection discrepancy reaches
   $2.07566\times10^{-8}$ (`coefficients.json` → `stencil_blocks.<layout>.centre_reflection_symmetry`). The stencil
   forms' excesses therefore appear in components the selection rule sets to zero.
4. **Corner minus mean in FP32.** Within one FP32 action this difference does not follow the coefficient identity: the
   median deviation is 1.9 times the predicted term.
5. **FP64 element matrix.** `ke_unit` in FP64 is not bitwise symmetric (81 pairs, $\le2.8\times10^{-17}$). The FP32
   rounding $Q$ is bitwise symmetric and invariant under all 48 cube symmetries.
6. **The original stencil has its own terms.** Its excess is the row-sum term $R_nu_n$ plus the difference-form excess
   (exact: 0 mismatches in 79,056 checks). At $E=1$, $R_n=8cI$ at the uniform centre, so it matches the element form's
   $8Ec\,u(x_n)$. At $E=0.7$ it does not. For $u=(x,0,0)$ the element form gives $-4.69387\times10^{-8}$ (exactly
   $8Ec\,u$). The original stencil gives $(-1.825392\times10^{-7},\ -1.99\times10^{-9},\ -3.8\times10^{-10})$
   (`summary.json` → `uniform_centre_original_forms`).
7. **FP32 rounding of the original forms scales with $|u|$.** The original forms multiply absolute displacements, so
   their application rounding is of order $\varepsilon_{32}|W||u|$ and is present for a pure translation. At unit
   translation the FP32 original stencil gives $3.95\times10^{-7}$ against a coefficient defect of $6.71\times10^{-8}$.
   Relative to the term scale, the FP32 translation excess is up to $1.1\times10^{-7}$ (stencil) and
   $7.5\times10^{-8}$ (element kernel). Only the reference and difference forms have a rounding term of order
   $\varepsilon_{32}|W||G|h$.
8. **Exact-excess records.** The earlier summary left the FP64 baseline's exact-excess entries empty, counted them as
   nonzero, and wrote NaN tokens into `summary.json`. All three are corrected:
   * the entries are now filled;
   * the FP64 baseline's zero share is computed from them, for example 0.1328125 for translations at the uniform
     boundary corners;
   * `summary.json` is written with NaN refused.

   The only other change is in the FP32 maxima of the excess over the exact force. That difference is now taken exactly,
   which moved those maxima by at most $5\times10^{-7}$ relative, in 7 of 4,000 class rows. No other value in
   `node_class_summary.csv` changed.
9. **Corrections of the last check** (CPU only; analysis and summary rerun from the saved GPU record, no GPU job):
   * The axial example no longer claims that every form's transverse force is exactly zero. It records the $y$ and $z$
     excesses of all six coefficient forms and lists the forms for which they are exactly zero (item 3).
   * The interface maxima are given for both tested moduli pairs (item 3).
   * Exact cancellation is stated for the rounded coefficients in rational arithmetic on exactly affine inputs. Their
     FP64 application leaves a residue of up to $1.1\times10^{-16}$ (`derivation.md` §4 and §8).
   * Equal opposite weights are stated as sufficient for the difference form's affine cancellation. The condition for
     every gradient is a vanishing first moment of the rounded blocks at the homogeneous interior node (item 10). The
     original stencil's translation force is its
     row-sum action $R_nt$, not $c\sum E\,t$ (`derivation.md` §3.1 and §5).
   * The `K0_exact` rows of `affine.csv` (13,176) now carry their exact excess, 0, instead of blanks. No cell of
     `affine.csv` is blank in the exact-excess columns. All other cells are unchanged byte for byte.
   * `local_contributions.csv` is written once by the analysis, with the excess columns, and is no longer rewritten by
     the summary. All 140,544 FP32 local values equal the raw kernel outputs in `out/run1/gpu_raw.npz` exactly.
   * The corner operator's asymmetry is stated as $\max|A_c-A_c^{\mathsf T}|=8.38\times10^{-9}$, and its skew-symmetric
     part $(A_c-A_c^{\mathsf T})/2$ as $4.19\times10^{-9}$ (`coefficients.json` → `projection`).

   `node_class_summary.csv` is unchanged byte for byte. The summary now reads the CSV files with round-trip parsing, so
   some `summary.json` values moved in the last digits. Most moved by at most $4.2\times10^{-15}$ relative. The
   local-contribution excesses (`element_vs_assembled_interior_node`) moved by up to $9.4\times10^{-7}$ relative, at
   values near $9\times10^{-11}$. The FP32 scatter-versus-local-sum maximum moved by $1.7\times10^{-9}$ relative. Two
   quoted deviations now come out smaller. The corner closed form holds to $2.7\times10^{-16}$ relative, where the earlier summary gave
   $1.0\times10^{-15}$. The original element form equals $8Ec\,u$ with zero deviation at $E=0.7$, where it gave
   $1.9\times10^{-16}$. No conclusion changed.
10. **Corrections of the second check** (wording only; no GPU job, no value of `affine.csv`, `coefficients.json`,
    `summary.json`, `local_contributions.csv` or `node_class_summary.csv` changed). `t19_fix_r8_checks.py` reads
    `affine.csv` and writes `out/fix_r8/checks.json`, which holds the new counts and checks quoted below.
    * Equal moduli in all eight cells are sufficient for the mean-reference affine cancellation, not necessary. Equal
      weights within each inversion-related pair of cells also suffice, because the two cells give opposite forces at
      the centre (exact check with four distinct pair weights, all nine gradients, every component 0;
      `derivation.md` §4).
    * A zero first moment of the rounded stencil is the difference form's criterion at the homogeneous interior node,
      where the exact first moment is zero. At an interface or boundary node, zero affine excess needs the rounded and
      exact first moments to agree. The axial interface row is an example: the rounded action is $2.3557692729$ against
      the physical $2.355769230769231$, a coefficient excess of $4.21244\times10^{-8}$ (`derivation.md` §5).
    * FP32 representation does not destroy every rigid rotation in placement P2. The FP32 `rot_x` input of P2 is
      exactly affine (zero second differences) and skew, and its exact physical force is zero in all 108 node-layout
      cases; `rot_y` and `rot_z` give all 216 nonzero cases. The total (216 of 324) and the maximum
      ($2.29\times10^{-8}$) are unchanged (`derivation.md` §6).
    * The opposite-weight mismatch is not confined to mixed-modulus and boundary nodes: at $E=0.7$ the homogeneous
      interior node also has three unequal opposite pairs and a first-moment entry of $1.60474\times10^{-9}$
      (`derivation.md` §5).
    * The interface reflection discrepancy is given with its moduli: $7.45\times10^{-9}$ at $1\,|\,1/8$, and up to
      $2.07566\times10^{-8}$ for the $y$ reflection at $0.7\,|\,0.0875$ (item 3).

## Outcome

The acceptance statement is met: the identity holds exactly, the axial values are reproduced, the guarantee is checked
on raw output, all node classes are reported, and the surviving cancellations are identified. The discrepancies above
narrow the wording that the plan and the submitted Sec. 3.2 used for the uniform-region cancellations. The patch shows
per-node magnitudes only. Whether the coherent corner term or the FP32 application rounding accumulates in solved
compliance is left to T21/T33.
