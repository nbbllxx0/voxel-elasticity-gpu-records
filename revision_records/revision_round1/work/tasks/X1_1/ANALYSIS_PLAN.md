# X1_1 analysis plan: one prospective bracket study at n = 384 (R1.4)

Written on 2026-11-25 under the authors' decision of 2026-11-25 07:30, before any GPU job of X1_1. Its SHA-256 goes
into `plan_hash.json` and the report before the first job. This file is not changed after the run starts. Any
departure goes to `DEVIATIONS.md`, with its reason.

## 1. Why this study, and what the records showed when the setting was chosen

The X0_2 records (`tasks/X0_2/REPORT.md` §4; `out/runs/R_adaptive_n384/history.json`) show the following.
- **The damped n = 384 run reached the 300-update guard.** It ran T31's configuration R with X0_2's per-element
  damped OC step in the last phase.
- **The large reversals of the fixed step are gone.** Two-update sign reversals: 0–78 per update over iterations
  200–300.
- **About 100 interface voxels still move.** Between 43 and 211 voxels change by more than 0.01 per update (allowance
  7), and the count does not fall over iterations 201–300 (median 104, then 123.5).
- **What drives the motion.** Over iterations 200–300:
  - only 10–316 design steps per update sit at their move limit;
  - only 510–647 of the 6,629,528 designable limits are below 1e-3;
  - 43,621 → 24,324 design steps per update exceed 1e-3, a slow decline;
  - J still falls by about 2.9e-7 relative per update.

  The remaining motion is the optimizer's own slow descent. The move limit does not bound it, and the steep β = 32
  projection (slope up to 16) turns design steps of about 1e-3 at the interface into ρ_phys changes above 0.01.
- **A longer cap alone predicts nothing.** Nothing recorded says that more updates under the same rule would bring the
  count down to 7.

This setting was therefore chosen **after the earlier n = 384 runs (T31's fixed step and X0_2's damped step) had
failed to stop**, from the records of those runs. The manuscript and the response must say so.

## 2. The one setting (both elements of the authors' example: a longer update cap from the retained state, and stronger final-phase damping)

The study continues the retained state of X0_2's damped n = 384 run `R_adaptive_n384`. It uses that run's design
variable after 300 updates, copied into `study/inputs_X0_2/R_adaptive_n384/` and hash-checked. The study runs for at
most **300 further updates (iterations 301–600)**. The final continuation phase stays as it was (p = 4.5, β = 32,
phase move 0.05, filter radius 1.20 × n/96 cells of the n = 96 grid). It adds **one change: a decaying cap on the
per-element move limits** (`study/x11_driver.py`, `X11SIMP`).
- **The cap.** Update k of the restart (k = 0 at iteration 301) uses c_k = max(0.05 · 0.98^k, 1e-4). Before the
  update every limit is clipped, m_e ← min(m_e, c_k).
- **The limits otherwise follow X0_2's rule unchanged.** m_e ← max(0.7 m_e, 1e-4) on a reversed step;
  m_e ← min(1.2 m_e, c_k) on a repeated direction.
- **What the restart resets.** The per-element limits start at 0.05 (they were not saved), the previous steps at 0,
  and the four warm-started states at zero. The OC multiplier search starts from its wide bracket.
- **The fidelity check.** The first restarted ρ_phys is compared bit for bit with X0_2's retained ρ_phys, and the
  result is recorded.

**What the cap implies, stated before the run.**
- The filter is a normalised average and the projection slope is at most 16. One update with cap c therefore changes
  ρ_phys by at most 16 c.
- The driver compares ρ_phys with an FP16 copy of the previous field, which adds at most 2^-12 ≈ 2.4e-4.
- Once c_k ≤ c* = 6.0e-4 (16 c* + 2.4e-4 ≈ 0.0098 < 0.01), the max-change test holds by construction. That happens
  from k = 219, so for the change tested at iteration t ≥ 521.
- The J-spread test is the only other condition of `max_change`. A stop is therefore expected by iteration 531 at the
  latest, unless the J spread exceeds 1e-4, a solve fails, or a guard stops the job.

The plan therefore separates two kinds of stop (section 5). The interesting question is whether the design settles
**while the cap still allows changes above 0.01** (iterations ≤ 520). For iterations 301 to about 380 the cap stays
above 0.01 (k ≤ 79). That part is close to the longer update cap alone, with the limits reset; the damping tightens
after it.

## 3. Unchanged

- **Model and optimization.** T31's configuration R and X0_2's code otherwise (copied unchanged into `study/`; hashes
  in `study/logs/copied_hashes.txt`):
  - geometry, element classes, supports and the four load cases;
  - J = Σ ¼ c_k / c0_k with T31's c0_n384 (`study/out/c0_n384.json`);
  - volume fraction 0.5 over the designable voxels;
  - the physical filter;
  - the production solver `mg_ir` with `stencil_diff` at tolerance 1e-5;
  - four stored states;
  - the retained design is the final iterate after the final production re-solve.
- **The authors' stopping rule.** The tests start after iteration 75; here they need 10 restarted iterations, so the
  earliest stop is at iteration 310. The run stops when the relative spread of J over the last 10 iterations is
  ≤ 1e-4 and either:
  - max |Δρ_phys| ≤ 0.01 (`max_change`), or
  - at most max(1, 1 ppm of 7,232,600) = **7** voxels change by more than 0.01 (`bounded_oscillation`).

  Reaching iteration 600 is the guard (not stopped).
- **Volume target** |V − 0.5| ≤ 1e-4.
- **The four tight FP64 endpoint checks.** These are T31's / X0_2's AUDIT, unchanged:
  - moduli rebuilt from the saved ρ_phys and hash-checked against the OPT job, and the fixed set checked;
  - four `mg64` solves from zero to FP64 true residual ≤ 1e-8 (`mg_ir` fallback);
  - each `node_hoist` equilibrium residual ≤ 1e-8.
- **Guards** (X0_2's launcher, copied, with T30's watch functions unchanged):
  - the atomic lock (checked against every task folder);
  - refusal while another Python process holds GPU memory;
  - the WDDM sampler, which stops the job when shared usage grows more than 256 MiB above its start (refused for
    memory, never rerun at this size);
  - the final checked sample;
  - the CuPy pool capped at the driver's free memory less 1.5 GiB.

  The launcher self-test is rerun before the first job and must pass.
- **Admission.** X0_2's predictions, with predicted peak + 1.5 GiB ≤ nvidia-smi free memory: OPT 5.16 GB, AUDIT
  5.73 GB at n = 384. guard.require_budget's answer and the other processes' usage are recorded beside each
  admission.

## 4. Jobs (one GPU job at a time; no other size and no other variant)

| # | job | content | time cap |
|---|---|---|---|
| 1 | `C_n384` | the continuation of section 2 (phase `continue`) | 2 h |
| 2 | `A_C_n384` | AUDIT of its retained design (only if job 1 returned a design) | 1 h |

No job starts after 11:30 on 2026-11-25, the end of X1_1's 4-hour budget from its start at about 07:30.
- **An infrastructure fault** (a launcher or host fault, not a spill, allocation failure or solve failure) may be
  rerun once, recorded in DEVIATIONS.md.
- **A spill or an allocation failure** is a refusal and is not rerun.

## 5. Outcomes (fixed now)

**E1, the completed-design test, as in X0_2.** The run passes when all of the following hold:
- (a) termination `max_change` or `bounded_oscillation` at iteration ≤ 600;
- (b) |V − 0.5| ≤ 1e-4;
- (c) every production solve ≤ 1e-5;
- (d) the audit is valid (moduli hash and fixed set match) and all four equilibrium checks are ≤ 1e-8;
- (e) no spill and no allocation failure in either job over the monitored interval.

**Reading:**
- **Stopped, settled.** E1 passes, and the tested change at the stop was produced by an update with c_k > c*
  (stop iteration ≤ 520). The design settled under the unchanged rule while the cap still allowed changes above 0.01.
- **Stopped at the step bound.** E1 passes with a stop at iteration ≥ 521. The design meets the unchanged rule, but
  the stop follows from the decaying cap. It shows the iterate was frozen by the damping, not that the optimizer's
  motion had died out. D4 measures how far it is from a point the undamped OC update leaves unchanged.
- **Not stopped.** The guard at 600, a solve failure, a failed (b)–(e), a refusal, or a time-cap stop. R1.4 then keeps
  its stated scale limit, and this is reported as it is.

**Verdict for the task.** Supports for "stopped, settled", partly supports for "stopped at the step bound",
inconclusive for "not stopped". In every case the report says that the setting was chosen after the earlier n = 384
runs failed to stop, from their records.

**Reported for every returned design** (descriptive; no further threshold):
- **D1, both density-change measures.**
  - At the stopping test: max |Δρ_phys| and the count above 0.01, with the cap c_k in force.
  - For the retained update (retained field against the FP16 snapshot of the stop iteration): the same two
    measures, and whether the count meets the allowance of 7.
  - The J spread over the last 10 iterations.
- **D2, counts and volume.** Allocated, active, designable and protected voxels; V; MND; the solid fraction of active
  voxels.
- **D3, tight endpoints.** c_k^tight, J^tight, c_k^tight / c0_k, the four residuals and solvers, and the
  production-to-tight differences.
- **D4, end check.** The trial OC update that is not committed:
  - undamped, with the phase move 0.05: voxels with ρ_phys change > 0.01, and the largest change;
  - with the current limits: the same two measures.
- **D5, against the start.** Against X0_2's damped retained field (J^tight 1.2038890560) and T31's R_n384
  (J^tight 1.2040870254):
  - the relative J^tight difference;
  - the voxels with |Δρ_phys| > 0.01 and > 0.5, and those on the other side of 0.5 (all over designable voxels).
- **D6, cost.** Iterations, the optimization time (entering `run()` to the end of the final re-solve), the median
  update, the pool peak, the process-dedicated peak, and the audit time. X0_2's 2,359 s is the cost of the first 300
  updates; the total from the uniform start is the sum of the two.
- **Trajectory.** Per iteration: the cap, the count above 0.01, max |Δρ_phys|, J, and the design steps above 1e-3.

## 6. Figure

After the jobs, the n = 384 field is rendered with T37's renderer, unchanged, beside the completed damped n = 192
design and the problem panel. The new field is shown if E1 passes, otherwise X0_2's retained field. The label carries
its stopping status and the kind of stop. FOR_WRITER.md gives the text.

No language model is called.
