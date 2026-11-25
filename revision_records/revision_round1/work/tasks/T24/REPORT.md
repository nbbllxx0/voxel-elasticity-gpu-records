# T24 — Paired 8.2M bridge optimizations at state-solve tolerances 1e-5 and 1e-6

Serves R3.4 (Reviewer 3, point (3): whether the discrepancies accumulate) and A.4 (comparison of native-precision
fields on the 8.2M mesh). Frozen plan: `ANALYSIS_PLAN.md`, unchanged (sha256 0f4b22e5…2d17). Deviations:
`DEVIATIONS.md` (D1, written before the confirmatory jobs). No language-model calls.

**Scope of every statement below.** The pair measures what one decade of tightening does (1e-5 → 1e-6). It does not
measure the accumulated distance from a tight-solve trajectory; that is T34's question. The comparison is between
fields at the same update stage, over iterations 1…S = 79, and the fields are native FP32 (not FP16 as in S24).

## 1. What was run

The setup was identical in all runs except for the tolerance τ:
- the authors' driver, copied byte for byte from `code/src/voxfem` (file hashes match the E32 code manifest);
- the problem `PROBLEMS["bridge"](160)`: 320 × 160 × 160 elements, 8,192,000 elements, no padding;
- the configuration `Config(volfrac=0.20, solver="mg64", op32="stencil_diff", tol=τ)`, every other field at its
  default. This means FP64 outer PCG and the repaired FP32 V-cycle, the uniform 0.20 start, the R2 continuation,
  warm starts, OC, and the driver's own stopping rules.

| run | τ | role |
|---|---|---|
| A | 1e-5 | primary leg (production tolerance) |
| B | 1e-6 | primary leg |
| A′ | 1e-5 | replicate of A: run-to-run floor |

The fields were captured through the driver's `log` callback, which is read-only and runs after the iteration timer.
At every iteration the callback saves the post-update physical field P_i and the raw design ρ_i. It saves the state
field R_i at i = 1, 16, 41, 66 and wherever R_i ≠ P_{i−1}, and it records the FP64 true residual of the accepted
state. Endpoints are E (the retained field), the accepted displacement, and a tight FP64 re-solve (PCG with the run's
own V-cycle, to ≤ 1e-10) followed by an independent residual from the element-by-element `elem_colored` FP64
operator. All of this lies outside the driver's timers.

Jobs ran one at a time through T26's guarded launcher (copied as `t24_launch.py`). The launcher self-test passed
(`out/launch_selftest.json`, 11/11 cases) before the first GPU job. Development smoke jobs at k = 16
(`out/runs/dev16_*`) tested the job and the analysis and enter no endpoint. From the start of the first GPU job to the
end of the last, about 21 min of wall-clock time passed, well inside the 5 h budget. The three confirmatory jobs took
196 s, 239 s and 193 s of launcher wall time (`out/course_summary.json` → `monitors.*.wall_s`).

## 2. Gate G (acceptance condition): passed

Source: `out/endpoints.json` → `gate`, `gate_Aprime`; `out/verdicts.json` → `gate_G`.

| | A | B | A′ |
|---|---|---|---|
| termination, N | bounded_oscillation, 79 | bounded_oscillation, 79 | bounded_oscillation, 79 |
| SolveFailed / spill / allocation failure | none | none | none |
| watch covered from go, final sample checked | yes, yes | yes, yes | yes, yes |
| all P_i (i ≤ N) and E saved and read back | yes | yes | yes |
| tight re-solve: ρ (PCG explicit FP64) | 8.387e-11 | 9.876e-11 | 9.917e-11 |
| independent ρ^ind (elem_colored) | 8.387e-11 | 9.876e-11 | 9.917e-11 |
| tight PCG iterations (one attempt, no restart) | 663 | 560 | 573 |

Memory, for information (`out/course_summary.json` → `monitors`; `out/endpoints.json` → `E4.*.memory`):
- admission: 3.5 GiB predicted peak + 1.5 GiB margin against 22,497,198,080 B driver-reported free memory;
  `guard.require_budget` answered ok;
- WDDM process dedicated peak 2,923,757,568 B in every run;
- largest shared growth 79,691,776 B, below the 256 MiB stop rule;
- driver pool peak reserved 2,490,864,640 B.

Because G passed, the fallback (T23's k = 80 result) is not used.

## 3. Results

### E2 / H1 — tight endpoint compliance: **inconclusive**

Source: `out/endpoints.json` → `E2`; `out/verdicts.json` → `H1`.

| | A (1e-5) | B (1e-6) |
|---|---|---|
| tight FP64 compliance C* | 0.08798177019731981 | 0.08798234933099887 |
| accepted final compliance (at τ) | 0.08798177029441809 | 0.08798234933454846 |
| accepted final residual | 9.537e-6 | 8.546e-7 |
| ε = \|u*·r*\|/C* | 1.245e-13 | 3.787e-14 |

- The signed difference is ΔC = C*_B − C*_A = **+5.791e-7**, and the relative difference is **δC = +6.582e-6**.
  B's retained design has the higher tight compliance.
- The resolution is U = 1.624e-13, so 10 U = 1.624e-12 and the difference is resolved.
- The difference is attributed to the tolerance: the A–A′ floor is δC_AA′ = −3.082e-10 (`E6.E2`).
- Verdict: support needs max(|δC|, 10U) ≤ 1e-6, and contradiction needs |δC| > 1e-4. The measured 6.58e-6 lies
  between the two, so **H1 is inconclusive** under the frozen rule.
- The prediction (about 1e-9, by analogy with k = 80's +1.78e-9) was too small by more than three orders of magnitude.

### E1 / H2 — retained native FP32 fields: **supported**

Source: `out/endpoints.json` → `E1.E_B_vs_E_A`; `out/verdicts.json` → `H2`.

Both runs stop at iteration 79, so E^B against E^A is also the P_S companion, and the two are identical.

| statistic (8,192,000 elements) | E^B vs E^A | floor E^A′ vs E^A |
|---|---|---|
| mean \|Δρ\| | **8.506e-7** | 6.496e-9 |
| max \|Δρ\| | **0.99999970** | 0.01350 |
| entries that differ (bitwise) | 64,382 | 11,882 |
| \|Δρ\| > 1e-6 / 1e-3 / 1e-2 / 0.1 / 0.5 | 7,590 / 39 / 11 / 8 / 6 | 339 / 11 / 1 / 0 / 0 |
| strict ρ > 0.5 crossings (up / down) | **7** (3 / 4) | 0 |
| ties: = 0.5, within 1e-6 of 0.5 (either field) | 0, 0 | 0, 0 |

- Support needs mean ≤ 1e-4 and crossings ≤ 819. Both hold, so **H2 is supported**.
- Mean and crossings are both attributed: the floor mean is 6.5e-9 and the floor has 0 crossings.
- The maximum is O(1). A few elements are fully solid in one design and void in the other.

Endpoint location (E7, `out/endpoints.json` → `E7_endpoint`):
- 11 elements differ by more than 0.01 between E^A and E^B.
- 5 of them (45 %) are among A's 6 final-step movers (|P_79 − P_78| > 0.01), and 4 (36 %) among B's 4.
- So about half of the large endpoint differences sit in the elements that are still oscillating when the
  bounded-oscillation rule stops the run.

### E3 / H3 — course of the field difference: **persistent**

Source: `out/pair.csv` (D, M, X per iteration); `out/verdicts.json` → `H3`; `out/course_summary.json`.

- **Rule inputs.** L1 = mean D_i over 66–70 = 8.501e-7, and L2 = mean D_i over 75–79 = 8.021e-7, so L2/L1 = 0.944.
  The class is **persistent**: neither decaying (≤ 0.1) nor growing (≥ 10).
- **Attribution.** The floor over the same window is L2(A,A′) = 3.233e-9. Since L2(A,B) > 10 L2(A,A′), the class
  stands.

Shape of the course:
- **Iteration 1.** The difference starts at the first update: D_1 = 5.49e-8, with 5,645,003 entries differing.
- **Phases 1–40.** D grows slowly to 7.48e-7 by iteration 40.
- **Phase 41–65 (β = 16).** D falls back to 1.92–3.73e-7 from iteration 44 on.
- **Iteration 66.** At the β = 32 continuation step D drops to 5.81e-8 (jump ratio 0.264).
- **Iterations 67–68.** D jumps by 9.20 at 67 and reaches its maximum 1.572e-6 at iteration 68.
- **Iterations 71–79.** D stays between 7.40e-7 and 8.51e-7.
- **Maximum difference.** M_i passes 0.5 first at iteration 68 and stays near 1 to the end (largest 0.99999982 at
  iteration 77).
- **Crossings.** At most 15 strict crossings at any shared iteration (iteration 24). Iterations with crossings: 42 of
  79.
- **Phase maxima of D.** 1.31e-7 (1–15), 7.48e-7 (16–40), 6.42e-7 (41–65), 1.57e-6 (66–79).

Checkpoints (`out/endpoints.json` → `E7_endpoint.checkpoints`). The R_i companion series is the field the compliance
c_i belongs to; DR is its mean difference.

| i | D_i | M_i | X_i | DR_i |
|---|---|---|---|---|
| 16 | 1.657e-7 | 2.99e-5 | 0 | 1.021e-7 |
| 41 | 6.417e-7 | 0.0519 | 4 | 7.112e-7 |
| 66 | 5.811e-8 | 0.0662 | 0 | 8.247e-9 |
| 67 | 5.344e-7 | 0.352 | 2 | 5.811e-8 |
| 79 = S | 8.506e-7 | 0.99999970 | 7 | 8.385e-7 |

The plan's wording rule for *persistent*: the field difference between the runs **persists at a mean of about
8e-7 after the jump at iterations 67–68** (L2 = 8.0e-7; maximum 1.57e-6 at iteration 68). It neither decays nor grows
over the final phase.

### E5 — accepted (pre-update) compliance course

Source: `out/pair.csv` → `c_ref`, `c_other`, `dc_rel_preupdate`; `out/course_summary.json`.

These are pre-update compliances c_i, one per design iteration.
- Through iteration 70 the relative difference (c_i^B − c_i^A)/c_i^A stays within ±1.8e-6 (largest 1.75e-6 at
  iteration 70).
- It reaches −7.80e-6 at iteration 71.
- From iteration 73 on it stays at +6.04e-6 to +7.34e-6, ending at +6.58e-6 at iteration 79. That matches the tight
  endpoint difference.
- The accepted residuals stay below each run's τ: A 9.53e-6 and B 9.10e-7 at iteration 79.
- The first-order indicators e_i = |u_i·r_i|/c_i stay at or below 6.47e-8 (A) and 7.99e-9 (B) at every iteration.

### E4 — work and stopping

Source: `out/endpoints.json` → `E4`.

| | A (1e-5) | B (1e-6) | B/A |
|---|---|---|---|
| design iterations, termination | 79, bounded_oscillation | 79, bounded_oscillation | — |
| PCG iterations, loop + final | 3,789 + 9 = 3,798 | 5,817 + 16 = 5,833 | **1.536** |
| matrix-vector products (FP64) | 3,988 | 6,078 | 1.524 |
| V-cycle applications | 3,798 | 5,833 | 1.536 |
| solve time, loop + final (s) | 88.995 | 135.605 | 1.524 |
| V-cycle setup time, loop + final (s) | 3.316 | 3.208 | 0.967 |
| sum of per-iteration `t_iter_s` (s) | 94.87 | 141.20 | — |
| tight re-solve iterations / time (s) | 663 / 15.51 | 560 / 13.06 | — |
| capture (hook) time, outside production timers (s) | 47.37 | 46.84 | — |

- The Krylov ratio 1.54 lies inside the predicted 1.2–1.8 range (k = 80: 1.39).
- B's Krylov count is at least A's at every shared iteration.
- Per-phase sums are in `E4.*.phases`.

### E6 — run-to-run floor (A′ against A)

Source: `out/endpoints.json` → `E6`; `out/pair_AAprime.csv`; `out/course_summary.json` → `floor`.

- A′ is **not** bit-identical to A. Every saved field and scalar agrees through iteration 28, and the first
  difference is at iteration 29.
- The Krylov counts agree at every iteration. Both runs stop at 79.
- The floor stays small:
  - F_i (mean |Δρ|, A′ vs A) is at most 6.50e-9 (at iteration 79);
  - there are 0 crossings at every shared iteration;
  - the endpoint maximum is 0.0135;
  - the tight-compliance floor is δC_AA′ = −3.08e-10.
- Where F_i > 0 (iterations 29–79), D_i/F_i ≥ 131, and D_i exceeds 10 F_i at every iteration.
- The A–B differences of E1, E2 and E3 are therefore all attributed to the tolerance.

### Overall statement class

Source: `out/verdicts.json` → `overall`, `no_accumulation_wording_allowed` = false.

- The verdicts are G passed, H1 inconclusive, H2 supported and H3 persistent.
- Under the frozen rule the paper reports the measured values with their class, and **may not say "does not
  accumulate"** for the 8.2M bridge.
- Wording consistent with the rule: on the 8.2M bridge, tightening the state tolerance from 1e-5 to 1e-6 changes the
  retained design's tight FP64 compliance by +6.6×10⁻⁶ (relative). It also changes the native-FP32 field by a mean
  |Δρ| of 8.5×10⁻⁷, with a maximum of 1.0 in a few elements and 7 strict 0.5 crossings.
- The field difference arises at the first update. It persists at a mean of about 8×10⁻⁷ after a jump at the final
  continuation step (iterations 67–68) and neither grows nor decays over the final phase. Both runs stop at
  iteration 79.
- A repeat of the 1e-5 run differs from the first by at most 6.5×10⁻⁹ in mean |Δρ|, with no crossings.
- This measures one decade of tightening, compared at the same update stage.

## 4. Checks (qualify, do not gate)

Source: `out/endpoints.json` → `checks`.

| check | result |
|---|---|
| C1 E = P_N bit for bit | pass (A, B, A′; in the job and from the files) |
| C2 hook residual = driver `rel_true` | pass at every iteration of A, B, A′ (max difference 0) |
| C3 k = 16 hook on/off bit-identical | **fail** — first difference at iteration 16. Two hook-off repeats also differ from each other (iterations 18, 19), so the driver is not bit-reproducible run to run and C3 cannot hold for any hook (DEVIATIONS.md D1) |
| C4 R_i = P_{i−1} where (β, r_min) unchanged | pass (75 iterations checked per run; R_i differs from P_{i−1} only at 16, 41, 66) |
| C5 A against the published E32 history | c and `rel_true` agree bit for bit through iteration 74 and first differ at 75; Krylov counts agree at all 79 iterations; N_A = 79 = N_E32; final accepted compliance 0.08798177029441809 against 0.08798177029441485 (relative +3.7e-14) |

The plan's own expectation is confirmed: bit-reproducibility of the 8.2M trajectory does not hold. Against E32, A
first differs at iteration 75, and A′ first differs from A at 29. The replicate therefore carries the attribution.

## 5. Files

- Scripts:
  - `t24_job.py`: the GPU job;
  - `t24_launch.py` and `t24_launch_selftest.py`: the launcher and its self-test, copied from T26;
  - `t24_common.py`: shared definitions;
  - `t24_analyse.py`: the analysis, CPU only;
  - `t24_summary.py`: the descriptive figures, CPU only;
  - `src/voxfem`: the authors' code, copied byte for byte.
- Outputs:
  - `out/pair.csv` and `out/pair_AAprime.csv`;
  - `out/endpoints.json` and `out/verdicts.json`;
  - `out/course_summary.json`;
  - `out/launch_selftest.json`;
  - `analyse_run.log`.
- Per run (`out/runs/<run>/`): `result.json` (the full driver record with history, the hook records and the
  endpoint), `monitor.json` (admission, watch samples, coverage) and `child_stdout.txt`.
- Native fields (`out/fields/<run>/`, 4.18 GB in total):
  - `P_it###.npz` and `rho_it###.npz` for every iteration;
  - `R_it###.npz` at 1, 16, 41 and 66;
  - `E_final.npz`;
  - `u_accepted.npy` and `u_tight.npy` (FP64).
  - The FP32 fields are stored losslessly with `savez_compressed`, under the key `field`.
- Development (labelled, no endpoint): `out/runs/dev16_*`, `out/fields/dev16_*`, `out/dev_analysis_*`.

## 6. Notes for T34 and the response

- T34 can reuse A's and B's per-iteration FP32 fields and both tight endpoints. A′ provides the floor at 1e-5:
  - mean |Δρ| at most 6.5e-9;
  - tight δC −3.1e-10;
  - first divergence at iteration 29.
- The size of H1 (6.6e-6, three orders above the prediction) comes from a handful of elements that end on opposite
  sides of 0.5 in the two designs. It is not a resolution artefact (10U = 1.6e-12).
- For A.4: these fields are native FP32. S24's k = 80 fields were stored in FP16.
