# T30: four-load lifting-bracket counterpart, implementation and correctness gate (serves R1.4)

**Outcome: the correctness gate passes at 96 cells along the longest edge, and larger-grid feasibility is reported
separately.** Every check fixed in `out/acceptance_rules.json` before the first GPU job passes (`out/gate.json`,
`correctness_passed: true`). The gate combines 13 top-level pass flags (`gate_flags`). A volume-gradient check is
recorded beside the objective-gradient check and also passes, but it is informational and does not enter the gate.
The memory of one full four-load design iteration was measured at n = 96, 192, 384 and
576 cells along the longest edge, with no spill. The workspace model fitted on 96 to 384 predicts the n = 576 peak to
within 0.31 % (`out/workspace.json`).

No language model was called. GPU work ran in six guarded jobs between 08:43 and 08:59 on 2026-11-24 (about 16 min
of the 8 h budget). Each job ran under the launcher's watch, which T30 took over from T21 without change; its CPU
self-test passes (`out/launch_selftest.json`).

## 1. What was built

**Geometry** (`t30_common.py`, `out/spec.json`). The bracket is a parametric counterpart of a lifting (engine)
bracket. It has four bolted interfaces and a two-arm clevis. Its dimensions were chosen in this run; no third-party
CAD file was used. All dimensions are in inches:
- **Base plate:** 7.2 × 4.5 × 0.75 (x < 7.2, y < 4.5, z < 0.75).
- **Riser:** a sloped riser over x ∈ [1.2, 4.5], y ∈ [0.6, 3.9], whose top rises from z = 0.75 to z = 3.0.
- **Clevis tower:** x ∈ [4.5, 7.2], y ∈ [0.6, 3.9], z ≤ 3.0, with two arms at y ∈ [0.6, 1.65] and [2.85, 3.9].
  The arm tops are rounded (radius 0.9) beyond the pin. The slot between the arms is void for z > 1.35.
- **Pin bore:** radius 0.375, axis parallel to y through (x, z) = (6.0, 2.1).
- **Bolt holes:** four holes of radius 0.1875 at (0.6, 0.6), (0.6, 3.9), (3.9, 0.6) and (3.9, 3.9), each with a
  clearance column of radius 0.4875 above its boss.

Every axis-aligned plane face, the pin axis, the clevis midplane and the bolt axes lie at multiples of 0.15 in. At
n = 96·m cells along x (h = 7.2/n in), they therefore lie on node planes or node lines. The other boundaries do not:
- the curved ones (pin bore, lug eyes, rounded arm tops, bolt holes, bosses and clearance columns);
- the sloped riser top.

Their radii run from 0.1875 to 0.9 in; at n = 96 the bolt-hole and boss radii are 2.5 and 6.5 cells. These
boundaries are voxelized by the element-centre test: an element belongs to a feature when its centre lies inside it.
The radii stated here and the element counts measured at each size are those of this voxelization.

**Box enlargement.** When the box is enlarged for the multigrid (section 3), the added elements are exterior only.
`host_checks` verifies this at every size (section 6).

**Frame and units.** Lengths are in inches, forces in lbf and moments in lbf·in.
- **x:** horizontal, along the bracket; +x is "outward", from the bolt end towards the clevis.
- **y:** parallel to the pin axis.
- **z:** vertical; +z is "upward", away from the mounting face z = 0.

**Element classes** (one byte per element). There are three:
- **Exterior** (0): the material outside the envelope, the pin bores, the bolt holes, the clearance columns and the
  slot. Modulus and density are 0.
- **Designable** (1).
- **Protected solid** (2): the bolt bosses (annulus 0.1875 to 0.4875, z ≤ 0.75) and the lug eyes (annulus 0.375 to
  0.675 in the arms). Density is 1.

**Supports.** The bolted interfaces are rigid: every node of a boss on z = 0, and every node of a bolt bore inside a
boss, is clamped.

**Load cases.** All four act about C = (6.0, 2.25, 2.1), the pin centreline at the clevis midpoint. Each is applied
alone, giving four independent states:

| case | prescribed |
|---|---|
| LC1 | F = (0, 0, +8000) lbf (upward) |
| LC2 | F = (+8500, 0, 0) lbf (horizontally outward, normal to the pin) |
| LC3 | F = 9500 (sin 42°, 0, cos 42°) lbf: 42° from vertical in the x–z plane normal to the pin axis, tilted outward |
| LC4 | M = (+5000, 0, 0) lbf·in about the horizontal x axis through C, F = 0 (a couple) |

The moment vector of LC4 is horizontal and normal to the pin axis, because a pin transmits no moment about its own
axis. The outward sense of "horizontal" and the plane of the 42° load are interpretations made in this run, stated
in `out/spec.json`. They were not checked against an external source in this task.

**Traction transfer.** An equal-weight distributing coupling (RBE3 type) carries each load from C to every node of
the two pin bores. Those are the nodes shared by a lug-eye element and a bore element: 1,200 nodes at n = 96. Each
node gets f_i = F/N + ω × (x_i − x̄), with J ω = M − (x̄ − C) × F. The discretized targets are therefore the
prescribed (F, M) themselves.

**Material.** The authors' trilinear hexahedron (ν = 0.3), with normalized E0 = 1 and Emin = 1e-9. Compliances are
given in code units; physical compliance = 2 C_code / (E h).

**Driver** (`t30_driver.py`, class `MultiSIMP`). It is built on an unchanged copy of the authors' `voxfem` package
(`src/`) and follows `voxfem.simp.SIMP` step by step. It adds the following:
- **Exterior-only DOFs** are eliminated. Exterior elements have modulus exactly 0, so the multigrid's zero-diagonal
  rule fixes every node with no active incident element; this is the authors' padding mechanism. The supports alone
  are passed to the hierarchy, so coarse levels are not over-constrained near holes.
- **Masked cone filter.** It computes ρ̄_i = Σ_j w_ij a_j ρ_j / D_i, where a is the active indicator and D is stored
  (4 B per element). Its transpose is a_j Σ_i w_ij g_i / D_i. Both directions cost O(R³) per element; the authors'
  transpose recomputes row sums per neighbour, O(R⁶). The output is 0 on exterior elements.
- **Densities.** The physical density is the projection on designable elements, 1 on protected and 0 on exterior.
  The volume is the mean over designable elements.
- **States.** One FP64 displacement is kept per load case (warm starts). The cases are solved one after another with
  the shared multigrid hierarchy, which is rebuilt once per design iteration.
- **Objective.** J = Σ_k w_k c_k / c0_k with w_k = 1/4, where c0_k is the compliance of the fully solid bracket. The
  element sensitivities are accumulated load by load, dc += (w_k/c0_k) u_kᵀKE u_k, before the SIMP, projection and
  filter chain is applied once.

The production solver is the authors' repaired mixed-precision path: FP32 `stencil_diff` operator, FP32 V-cycle-PCG
corrections, and FP64 iterative refinement accepted on the FP64 true residual ≤ 1e-5.

## 2. Correctness at n = 96 (`out/gate.json` → `correctness`)

The grid at n = 96 has 96 × 64 × 40 = 245,760 allocated elements: 113,318 active, of which 104,070 are designable
and 9,248 protected. 372,687 DOFs are free after supports and exterior-only nodes (`out/host_checks_96.json`).

| check | rule (fixed before the runs) | result |
|---|---|---|
| Force and moment resultants, all four cases | ≤ 1e-10 of each case's load scale max(\|F\|, \|M\|/1 in), absolute: 8e-7, 8.5e-7, 9.5e-7 and 5e-7 for LC1 to LC4 (lbf for force, lbf·in for moment) | largest error 7.3e-11 lbf and 2.5e-10 lbf·in at n = 96; at most 2.1e-9 and 2.8e-9 at n = 384 and 7.4e-9 and 3.3e-9 at n = 576. Every case passes; every error is also below 5e-7, the strictest of the four tolerances. Also passes at n = 192 (`out/host_checks_*.json`) |
| Load set | symmetric about the clevis midplane and the pin axis; centroid at C | symmetric in x, y and z; centroid (6.000, 2.250, 2.100) |
| Connectivity | one face-connected active component that contains the supports | 1 component |
| Exterior-DOF elimination | fixed set on the device = supports ∪ exterior-only nodes | identical: 134,276 nodes on both sides |
| FP64 operator against the CPU assembly | ≤ 1e-12 of the largest entry | 7.6e-16 (solid state), 6.4e-16 (iteration-1 state) |
| Masked filter against an FP64 CPU reference, rmin 1.5 and 2.5 | forward ≤ 1e-6 abs; transpose ≤ 1e-5 rel; dot test ≤ 1e-5; partition of unity ≤ 1e-6; zero on exterior | forward 5.0e-7; transpose 4.6e-7; dot test 6.7e-8; partition of unity 0; exterior 0 |
| Protected regions and masks: initial field, after the OC step, updated design | ρ and ρ_phys exactly 1 on protected and 0 on exterior; E exactly 1 and 0 there; designable values in [0, 1] | all three states pass exactly |
| Coarse compliance: 4 loads × 3 states (fully solid, iteration 1, after one update) | \|c_GPU − c_direct\| / c_direct ≤ 1e-3 | largest 2.9e-7 (LC3, iteration 1) |
| Equilibrium of the production solves | FP64 true residual ≤ 1e-5, also recomputed in the assembled matrix | largest reported 5.46e-6; recomputed 5.46e-6; largest relative energy-norm error 8.8e-7 |
| Centred directional gradient of J (p = 3, β = 4, rmin = 2.5, seeded random design) | h = 1e-3: \|analytic − FD\| / \|FD\| ≤ 1 % for d1 ~ U[0, 1] and d2 ~ N(0, 1) | d1: 1.29e-5; d2: 4.76e-4 |
| Volume gradient (same directions; informational, not a gate flag) | ≤ 1 % | 1.3e-6 and 2.0e-4 |
| Single-load regression: authors' `SIMP` against `MultiSIMP` (one load, no mask, weight 1); authors' cantilever k = 16; 30 iterations | same iteration count; per-iteration compliance ≤ 1e-6 relative | 30 and 30 iterations; largest compliance difference 1.54e-11; final density bitwise identical |
| One production update | four solves at the target; updated physical volume within 1e-4 of 0.5 | volume 0.49999999 (error 5.7e-9) |
| No spill, coverage | watch from 'go' to the final sample; shared growth ≤ 256 MiB | covered over that window; growth 14.7 MB (verify job) and 2.1 MB (regression job). The window starts at 'go', the first complete sample of the job's process. That sample comes after the job has created its CUDA context and made a one-element probe allocation, so the CUDA initialization and the probe lie before it. All six jobs had complete samples from that baseline through the final check |

**Coarse compliances**, GPU production path against the FP64 direct solve (MKL PARDISO), for LC1 to LC4:

| state | c_GPU (LC1, LC2, LC3, LC4) | largest relative difference |
|---|---|---|
| fully solid (c0) | 1.168501e7, 7.741721e6, 3.817800e6, 9.393795e5 | 1.42e-7 |
| iteration 1 | 2.772241e7, 1.876180e7, 8.441053e6, 2.222059e6 | 2.89e-7 |
| after one update | 1.952505e7, 1.357480e7, 6.032079e6, 1.686334e6 | 2.24e-7 |

The normalized objective J fell from 2.3431 at iteration 1 to 1.6999 after one update.

**Gradient check at other step sizes** (for information): d1 gives 1.22e-3 at h = 1e-2 and 3.1e-6 at h = 1e-4; d2
gives 2.8e-5 and 6.5e-3. The finite differences from GPU FP64 PCG states (tolerance 1e-10) agree with the
direct-solve differences to the digits shown. J from the GPU states and J from the direct solves differ by 2.2e-13.

**Not bitwise in the regression.** The per-iteration compliances of the two drivers differ by at most 1.54e-11, while
the final densities are bitwise identical. The cause was not investigated.

**Model and timing notes.**
- With the projection at β = 1, the initial physical volume is 0.50297, above the 0.5 target, because protected
  neighbours raise ρ̄ near the bosses and eyes. The first OC step restores the target.
- In the verify job, the first production design iteration at n = 96 took 1.19 s, including first-use kernel
  compilation. The four solves took 0.59 s and the multigrid rebuild 0.34 s (`out/runs/verify_n96/gpu_meta.json`).
  The memory job's iteration at the same size took 0.67 s (section 3).

## 3. Larger-grid feasibility (reported separately; `out/workspace.json`)

Each memory job ran one production design iteration, with the four fully solid reference solves before it, in one
driver instance. The physical filter length was held fixed at 1.5 cells of the n = 96 grid. The pool peak is the
CuPy pool's reserved high-water mark, taken at every allocation. The process peak is the largest sampled WDDM
dedicated value; the sampling interval can miss short peaks, which is why at n = 576 it is lower than the pool peak.

| n | allocated box | allocated / active elements | pool peak | process dedicated peak (sampled) | B per allocated / active element | shared growth | one iteration, 4 cold-start solves |
|---|---|---|---|---|---|---|---|
| 96 | 96×64×40 | 245,760 / 113,318 | 0.283 GB | 0.514 GB | 1152 / 2499 | 6.3 MB | 0.67 s |
| 192 | 192×128×80 | 1,966,080 / 903,548 | 0.710 GB | 0.956 GB | 361 / 786 | 16.8 MB | 1.47 s |
| 384 | 384×256×160 | 15,728,640 / 7,232,600 | 4.220 GB | 4.549 GB | 268 / 583 | 102.8 MB | 9.9 s |
| 576 (extension) | 576×384×256 | 56,623,104 / 24,411,796 | 14.582 GB | 14.504 GB | 258 / 597 | 86.0 MB | 47.2 s |

Every production solve in these jobs met the 1e-5 FP64 equilibrium target, and no job spilled.

**Fitted model** (96, 192 and 384 only): pool peak = 254.5 B × N_alloc + 216 MB. The 216 MB term does not depend on the
grid size. The CUDA context and other process memory add 330 MB. Residuals of the fit are
−1.8 %, +0.8 % and −0.01 %. **Out of sample:** at n = 576 the model predicts 14.63 GB against 14.58 GB measured
(+0.31 %).

**Exterior voxels cost memory.** The box layout stores every allocated element, but only part of the box is active:
- **Fitted grids (n = 96, 192 and 384):** 46.1 %, 46.0 % and 46.0 %.
- **n = 576:** 43.1 % (24,411,796 of 56,623,104), because the box is enlarged from 240 to 256 cells in z with
  exterior elements.

The values are given per size in `out/workspace.json`, `rows[].active_fraction_of_allocated`. The cost per active
element is therefore about 583 to 597 B at n ≥ 384, against 255 B per allocated element. The
four stored FP64 states account for 96 B per node. Keeping one state (cold start per load) would save 72.9 B per
allocated element.

**Predictions.** These use nvidia-smi free memory of 22.60 GB when the file was written, less the 1.5 GiB margin:

| n | allocated box | N_alloc | predicted process peak | admissible | without stored states | admissible |
|---|---|---|---|---|---|---|
| 480 | 512×320×256 | 41.9 M | 11.22 GB | yes | 8.16 GB | yes |
| 576 | 576×384×256 | 56.6 M | 14.96 GB | yes (measured) | 10.83 GB | yes |
| 672 | 704×448×320 | 100.9 M | 26.23 GB | no | 18.87 GB | yes |
| 768 | 768×512×320 | 125.8 M | 32.57 GB | no | 23.40 GB | no |

The largest admissible allocated box under this model is 80.3 M elements with four stored states, and 112.6 M
without. Sizes above n = 576 are extrapolations, not measurements.

**Grid constraint.** Only n = 96·2^k coarsens to the 12 × 8 × 5 coarsest grid with the box as defined. Other n need a
box enlarged with exterior elements to a multiple of 2^(L−1) (`t30_common.mg_box`), which raises N_alloc: n = 480
becomes 512 × 320 × 256. Since fix round 1 the base plate is bounded at x = 7.2 in, so the enlargement adds exterior
elements only (section 6). Before that fix, an enlargement along x would have extended the base plate. The measured
sizes were not affected: 96, 192 and 384 are not enlarged, and 576 is enlarged in z only. The predictions above
depend on N_alloc alone and are unchanged.

**Cost notes for T31 and T35.** With a fixed physical filter length, R grows with n (R = 8 at n = 576). The masked
filter's O(R³) transpose keeps that affordable: one iteration at n = 576 took 47 s, of which the four cold-start
solves took 43.9 s. Later iterations start warm, so these single-iteration times do not by themselves give the cost
of a complete optimization.

## 4. Against the acceptance statement

- **Resultants:** they equal the prescribed targets within the recorded tolerance (1e-10 relative) for every case at
  n = 96, 192, 384 and 576.
- **Protected regions:** they survive the filter, projection and OC exactly.
- **Coarse compliances:** all twelve agree with independent FP64 direct solves within 2.9e-7 (rule 1e-3).
- **Summed gradient:** it agrees within 1.29e-5 and 4.76e-4 for the two directions (rule 1 %).
- **Coarse run:** it met its equilibrium target (5.46e-6 ≤ 1e-5) without spill.
- **Separation of results:** correctness and feasibility are recorded separately in `out/gate.json`.
- **Replacement geometry:** the parametric counterpart is the geometry, and it passed its own checks.

**Outcome: supports.**

## 5. Files

- **Specification and rules:** `out/spec.json` (geometry, frame, load cases, transfer, supports, classes);
  `out/acceptance_rules.json` (rules fixed before the first GPU job).
- **Host checks:** `out/host_checks_{96,192,384,576}.json` (counts and checks per resolution).
- **Gate and workspace:** `out/gate.json` (correctness, with feasibility kept apart); `out/workspace.json` (measured
  memory, fit, out-of-sample check and predictions).
- **Job records:** `out/runs/<job>/monitor.json` (admission, watch, coverage) and `gpu_meta.json` (results) for
  `regress_k16`, `verify_n96` and `mem_n{96,192,384,576}`. `out/launch_selftest.json` is the CPU self-test of the
  launcher.
- **Code:**
  - `t30_common.py` (geometry, loads, checks, multigrid box, admission estimate);
  - `t30_driver.py` (MultiSIMP, masked filter);
  - `t30_cpu.py` (independent FP64 assembly, PARDISO, CPU filter reference);
  - `t30_job.py`, `t30_launch.py` and `t30_launch_selftest.py` (guarded jobs);
  - `t30_spec.py`, `t30_workspace.py` and `t30_gate.py` (CPU-only writers);
  - `src/voxfem` (unchanged copy of the authors' package; hashes in `src/voxfem_copy.sha256`).

**Admission.** Each job was admitted when its predicted peak plus 1.5 GiB was below nvidia-smi free memory:
- the first five jobs used a flat 320 B per allocated element allowance;
- the n = 576 job used T30's own measured model plus 5 % (15.69 GB predicted, 22.60 GB free).

guard.require_budget's answer is recorded in each `gpu_meta.json`; it was `ok` for the verify job. Every CuPy pool
was capped at the driver's free memory less 1.5 GiB.

**Fix round 1:** `t30_fix_r1.py` and `out/fix_r1/` (the checks, the element-class hashes before the fix, and the
earlier `spec.json`, `host_checks_*.json`, `gate.json` and `workspace.json`).

## 6. Fix round 1 (checker's review; CPU only, no GPU job)

1. **Base plate bounded in x.** The base mask had no upper x bound, so a box enlarged along x for the multigrid would
   have made its padding designable. `t30_fix_r1.py` evaluates the old classifier with the base unbounded again:
   - 480,000 non-exterior padded elements at n = 480 and 940,800 at n = 672;
   - 0 at n = 576, which is enlarged in z only.

   The base is now bounded at x < 7.2 in. `host_checks` gains a padding check: every element beyond the nominal
   7.2 × 4.8 × 3.0 in box must be exterior, and `host_checks.passed` requires it. With the fix, the check passes at
   n = 96, 192, 384, 480, 576, 672 and 768.

   At the four measured sizes, the element-class arrays are bitwise identical to those recorded before the edit
   (SHA-256), so every measurement stands. At the unmeasured n = 480 and 672, the active counts fall from 14,611,220
   to 14,131,220 and from 39,717,342 to 38,776,542. The workspace predictions, which depend on N_alloc only, do not
   change. `out/fix_r1/checks.json` holds these checks.
2. **Voxelization wording.** Section 1 and the `t30_common.py` docstring now say that only the axis-aligned plane faces
   and the axes lie on node planes, and that curved boundaries and the sloped riser top are voxelized by the
   element-centre test. The radii and the measured counts are kept.
3. **Resultant tolerances.** They are given per case: 8e-7, 8.5e-7, 9.5e-7 and 5e-7 for LC1 to LC4.
4. **Active fraction.** It is given per size, and is 43.1 % at n = 576.
5. **Gate and coverage wording.**
   - The gate has 13 flags, and the volume-gradient check is informational. `gate.json` now lists `gate_flags` and
     `informational_checks`.
   - Coverage runs from the first complete sample after CUDA initialization and the probe allocation. This is
     `no_spill_coverage.coverage_window`.

**Regenerated files.** These were written again: `out/spec.json` (adds `base.x1`; otherwise identical),
`out/host_checks_{96,192,384,576}.json` (add `padding`; otherwise identical), `out/workspace.json` and
`out/gate.json`. `workspace.json` adds the per-row active fraction and reuses the free memory recorded when the file
was first written; it is otherwise identical. `gate.json` adds the gate-flag list, the informational checks and the
coverage window; it is otherwise identical. No measured value changed.
