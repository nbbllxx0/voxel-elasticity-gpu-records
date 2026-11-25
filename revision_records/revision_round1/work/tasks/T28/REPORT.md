# T28: same-card comparison with the released OpenMP-offload multigrid code (Träff et al.)

Serves R1.1. Frozen plan: `ANALYSIS_PLAN.md`, unchanged (SHA-256 0128134b…d338e8). Deviations: `DEVIATIONS.md`, D1–D37
(D26–D30 are the corrections made after the second check, D31–D33 those after the third, D34–D37 those after the
fourth: assembly only, no GPU job, no measured value changed).
Every number below is read from a file in `tasks/T28/`. The generated tables are in `report_tables.md`
(`drivers/summary.py`). No language model was called.

## Outcome in one paragraph

On the RTX 4090, the fixed-state comparison is valid at k = 64, 128 and 160 for both states (S1, S5). At k = 256
and 320 the S1 runs are **descriptive completions**: the system-identity gate G2 and the independent residual are
missing there. The released runs built their own system at both sizes. At k = 256 our drivers read their inputs from
an invalid record run's dumps, which equal the plan's references entry by entry (D28); at k = 320 they used the
formula rebuild (D32). The released code (`traeff`, nvc 26.11 build of T12) met its own FP32 recursive stop at S1 at every k
up to 320. The independently checked iterate (first timed solve) left FP64 residuals of 2.33e-4, 6.51e-4 and
8.33e-4 at k = 64, 128 and 160.

**Common accuracy (10⁻⁵) was not attained by the released code at any checked snapshot**, so no equal-accuracy
time ratio exists. The check covers the prespecified snapshots of the six completed continuations (k ≤ 160, S1 and
S5). Accuracy between snapshots was not measured, and no continuation completed at k ≥ 256.

At S5 (warm start from the released U₄) the released solver reached its 1000-step cap at k = 64, 128 and 160.
The residuals of the checked first repeat were 0.561, 7.09 and 6.52. At k = 64 the three repeats' recursive
residuals were 0.561, 0.912 and 0.605; at k = 128 and 160 one solve was timed.

Our three paths were verified (class 9) at every (k, state) through k = 160. Native-stop solve-time ratios
`traeff`/`mg64_rep` are 9.4–50 at S1 and 706–1268 at S5, **at unequal accuracy**. At k = 256 and 320 the ratios (89.5
and 95.5) are descriptive, and their **accuracy relationship is unresolved**: neither path has an independent residual
there.

The released design update could not be reproduced: the step check failed at every k (P8), because the released
build's sensitivity filter has no effect (D14). The design loops are therefore
**distinct workloads, with no ratio**. Completed-size lower bounds at S1 are k = 320 (65,536,000 elements) for all
four paths. At k = 384 the released code and `mg64_*` were refused by admission, and `mgir_rep` was stopped by the
spill sampler.

## Gates (`gates.json`)

| Gate | Result | Source |
|---|---|---|
| G0 guard self-tests | pass. First run: 51/51 + kill test. Rerun before this session's first GPU job: 51/51 + kill test (D20) | `g0/G0.json`, `g0/resume_k160/G0.json` |
| G1 code identity | pass (k = 32: 6 steps in the plain, timing and continuation builds; iterate rel. diff 3.66e-8 and 3.72e-8) | `verification.json` |
| V verification | pass | `verification.json` |
| G2 system identity | pass at k = 64, 128, 160 (action d ≤ 2.56e-8, target 10⁻⁵). **Not evaluated at k = 256, 320, 384**: there is no valid record run R (R_k256 class 6; no R above it) | `out/K1_k*.json` |
| G3 checker validity | pass (checker vs CPU FP64: rel. diff ≤ 4.1e-10; vs in-solver: ≤ 3.4e-10; 1 % allowed) | `out/K2_k64.json` |
| G4 timing validity | revision 4 (D31, D34–D37), over every presented timed section: fixed-state, native N, record R and our loops L. **Whole fixed-state solves** (the timed rows and P5): none can be excluded. Ours: plan mean ≤ 0.066 %, strict bound ≤ 2.04 % (9 of 72 solve times at most flagged, all at k = 64). Released, clock-free: strict bound ≤ 1.73 % with no clock alignment assumed (64/S1 at most flagged). These bounds cover whole solves only. **Krylov steps** (P4, P11): at step duration the 5 % rule is unresolved for 15 of the 32 timed rows, every row at k = 64 and every row at k = 128 except `traeff` 128/S1 (released 64/S1: 14.3 %, from the job's recorded integral and the 88.2 ms median step). At k ≥ 160 every step-level bound is ≤ 2.99 % (D34). **Design-loop solves:** the native runs N and our loops L clear the 5 % threshold at whole-solve resolution; the instrumented record-run solves of iterations 1–4 at k = 64 are unresolved (bounds 161.1, 121.2, 135.2 and 51.6 %, D35). No solve is low-clock. **Setups and design steps** enter no prediction. Many are shorter than the 5-s counter interval, and the 5 % rule is undecided ("unresolved", not interference) for 10 of 16 released per-solve setups, 2 of 8 released setups (a), and the design steps of N (13 of 13), R (28 of 28) and our k = 64 loops (48 of 84). The R design steps have only their whole-job bounds: their windows do not match the driver's design timer, so they have no constant-offset reading (D36). The plan mean is ≤ 0.65 % wherever it can be located. The low-clock rule is undecided for 6 of our setups (a) (no clock series saved), for 6 released setups (a) and for 2 released per-solve setups. Released setup (a) at k = 256 and 320 is low-clock only under a constant clock offset. **Limitation (D37):** the activity sampler is one wildcard counter query, which enumerates the process instances when it starts. The bounds cover those instances; the records neither establish coverage of a process created later nor show that such a process interfered | `g4_activity.json`, `comparison.csv`, `design_workload.csv`, `gates.json` → G4 |
| G5 timing-build overhead | **fail**: timing build 0.768 s vs plain build 0.858 s at k = 64, S1 (−10.4 %; the timing build is faster). Every released step time is flagged | `gates.json` |
| G6 dumps outside the intervals | **fail**: solve −14.2 %, design step +19.4 %. R's intervals are labelled instrumented; the native runs N (k = 64, 128, 160) give the released native loop times | `gates.json` |

## Q1: fixed-state comparison (`comparison.csv`)

Precision and boundary labels for every row are in `comparison.csv` (`operator`, `residual_precision`,
`krylov_precision`, `iterate_precision`, `native_stop_rule`, `timing_boundary` and `memory_definition`).
- Released: FP32 stencil input and output with FP64 element arithmetic; FP32 Krylov vectors and FP32 recursive
  residual; FP64 iterate; stop at ‖r‖/‖b‖ < 10⁻⁵ (FP32 recursive) or 1000 steps.
- Ours: FP64 operator; FP32 V-cycle; FP64 true-residual stop ≤ 10⁻⁵. `mgir_rep` has an outer FP64 residual.
- Steps for `mgir_rep` are given as outer/inner.
- Repeats and times:
  - Ours: each time is the median of 3 timed solves.
  - Released: 3 solves when the first took ≤ 120 s, otherwise that one solve (plan 4.2). This gives 3 at k = 64
    (S1, S5) and at k = 128 and 160 S1, and 1 at k = 128 and 160 S5 and at k = 256 and 320 S1.
  - IQRs and per-repeat in-solver residuals are in `comparison.csv` (`n_timed_solves`,
    `insolver_residual_each_repeat`).
  - In-solver residuals and steps are those of the first timed solve. The independent residual is also evaluated
    on the first solve's iterate.
- M1 is the job's dedicated peak. The released M1 is the WSL VM worker's growth.
- Setup times enter no prediction, and their G4 status is in `comparison.csv` (`g4_setup_*`,
  `g4_per_solve_setup_strict_activity`).
  - The released per-solve setup (b) is unresolved under the 5 % rule at k = 64 (S1, S5) and 128 (S1, S5): those
    sections last 0.04–0.70 s, far shorter than the 5-s counter interval.
  - Released setup (a) is unresolved at 64/S5 and 128/S5.
  - The low-clock rule is undecided for the setups listed in `gates.json` → G4 → `setup_sections` (D31).

| k | state | path | class | steps | in-solver res. | indep. FP64 res. | setup a / b s | solve s | Krylov step ms | M1 GB |
|---|---|---|---|---|---|---|---|---|---|---|
| 64 | S1 | traeff | 8 | 8 | 7.93e-6 | 2.33e-4 | 1.51 / 0.053 | 0.768 | 88.2 | 1.66 |
| 64 | S1 | mg64_orig | 9 | 10 | 3.13e-6 | 3.13e-6 | 0.309 / 0.058 | 0.168 | 10.6 | 0.53 |
| 64 | S1 | mg64_rep | 9 | 10 | 3.13e-6 | 3.13e-6 | 0.307 / 0.041 | 0.0819 | 3.93 | 0.53 |
| 64 | S1 | mgir_rep | 9 | 4/10 | 3.92e-6 | 3.92e-6 | 0.304 / 0.063 | 0.129 | 5.75 | 0.50 |
| 64 | S5 | traeff | 7 | 1000 | 0.561 | 0.561 | 0.944 / 0.053 | 90.7 | 87.3 | 1.66 |
| 64 | S5 | mg64_rep | 9 | 23 | 6.11e-6 | 6.11e-6 | 0.299 / 0.036 | 0.128 | 3.91 | 0.53 |
| 64 | S5 | mgir_rep | 9 | 5/26 | 2.37e-6 | 2.40e-6 | 0.311 / 0.070 | 0.172 | 3.83 | 0.50 |
| 128 | S1 | traeff | 8 | 14 | 9.67e-6 | 6.51e-4 | 5.72 / 0.380 | 10.8 | 739 | 2.83 |
| 128 | S1 | mg64_rep | 9 | 10 | 6.03e-6 | 6.03e-6 | 0.712 / 0.179 | 0.318 | 13.0 | 1.32 |
| 128 | S1 | mgir_rep | 9 | 4/10 | 8.69e-6 | 8.68e-6 | 0.684 / 0.213 | 0.319 | 8.13 | 1.04 |
| 128 | S5 | traeff | 7 | 1000 | 7.09 | 7.09 | 6.10 / 0.695 | 781 | 742 | 2.83 |
| 128 | S5 | mg64_rep | 9 | 33 | 7.35e-6 | 7.35e-6 | 0.708 / 0.177 | 0.616 | 13.0 | 1.32 |
| 128 | S5 | mgir_rep | 9 | 6/40 | 1.55e-6 | 1.65e-6 | 0.711 / 0.259 | 0.610 | 7.98 | 1.04 |
| 160 | S1 | traeff | 8 | 16 | 6.03e-6 | 8.33e-4 | 7.21 / 0.698 | 21.1 | 1174 | 3.55 |
| 160 | S1 | mg64_rep | 9 | 9 | 9.11e-6 | 9.11e-6 | 0.742 / 0.200 | 0.421 | 22.6 | 2.15 |
| 160 | S1 | mgir_rep | 9 | 4/10 | 4.10e-6 | 4.10e-6 | 0.756 / 0.333 | 0.504 | 12.7 | 1.58 |
| 160 | S5 | traeff | 7 | 1000 | 6.52 | 6.52 | 6.50 / 0.946 | 1247 | 1183 | 3.55 |
| 160 | S5 | mg64_rep | 9 | 32 | 6.13e-6 | 6.13e-6 | 0.763 / 0.273 | 1.02 | 22.7 | 2.15 |
| 160 | S5 | mgir_rep | 9 | 6/39 | 1.02e-6 | 1.20e-6 | 0.722 / 0.301 | 0.864 | 12.8 | 1.58 |
| 256 | S1 | traeff | 8 | 27 | 7.53e-6 | missing | 46.4 / 3.83 | 126 | 4249 | 9.57 |
| 256 | S1 | mg64_rep | 8 | 11 | 2.28e-6 | missing | 1.14 / 0.373 | 1.41 | 88.2 | 7.32 |
| 256 | S1 | mgir_rep | 8 | 4/11 | 9.31e-6 | missing | 0.909 / 0.501 | 1.21 | 48.1 | 5.01 |
| 320 | S1 | traeff | 8 | 31 | 8.82e-6 | missing | 45.1 / 8.81 | 239 | 6986 | 13.98 |
| 320 | S1 | mg64_rep | 8 | 10 | 3.34e-6 | missing | 1.25 / 0.645 | 2.50 | 173 | 13.60 |
| 320 | S1 | mgir_rep | 8 | 4/10 | 4.15e-6 | missing | 1.13 / 0.607 | 1.90 | 94.3 | 9.11 |

The `mg64_orig` rows at k ≥ 128 and the k = 64 S5 row are in `comparison.csv`. Their step counts equal
`mg64_rep`'s, and their residuals agree with `mg64_rep`'s to the digits shown except at 160/S5 (6.14e-6 against
6.13e-6). Their Krylov-step times are within 1 % of `mg64_rep`'s at k ≥ 128 (P11). At
k = 64, S1, `mg64_orig`'s step time is 10.6 ms against 3.93 ms. That window ran at a low SM clock (minimum median
900 MHz, D17); G4's low-clock rule covers only sections ≥ 1 s.

The k = 256 and 320 rows are descriptive completions. They are class 8 only because the independent residual is
missing: the checker K2 spilled at k = 256 (D22). G2 is not evaluated there either. Input sources (D32):
- The released fixed-state runs at S1 build their own system and read no input file, at both sizes.
- At k = 256 our drivers read the load, supports and `KE0` from the dumps of the invalid record run `R_k256`
  (class 6). Those inputs equal the plan's dump-free references entry by entry: the load over 101,649,411 entries, all
  100,230 fixed DOFs, and `KE0` bitwise (`fix_r2/check_k256_inputs.json`, D28).
- At k = 320 our drivers used the formula rebuild (`out/T_S1_k320_*.json`, `system.source`).

Our solved systems are therefore the prescribed ones at both sizes.

The in-solver values of `mg64_*` there are FP64 true residuals, and those of `mgir_rep` are outer FP64 residuals. These are not independent checks. The untimed history runs confirm them: their final FP64 true
residuals are 2.28e-6 (k = 256) and 3.34e-6 (k = 320) for `mg64_rep`, and 9.31e-6 and 4.15e-6 for `mgir_rep`
(`residual_histories/256_S1_*.csv`, `320_S1_*.csv`).

Rows that do not report a measurement (`comparison.csv`, `note` column):
- S5 at k = 256: class 1, because R did not complete four design steps.
- S5 at k = 320 and 384: class 1, because R was not run there.
- k = 384, S1: `traeff` class 2 (predicted 27.73 GB, driver free 24.10 GB); `mg64_orig` and `mg64_rep` class 2
  (predicted 25.26 GB, free 24.15 GB). These refusals are admission predictions, not measured limits.
- k = 384, S1, `mgir_rep`: class 4. The spill sampler stopped it at 308,281,344 B shared, 13,154,037,760 B dedicated.

### Common accuracy and convergence (`out/collect_common_accuracy.json`, `residual_histories/`)

| k / state | continuation class (queue) | attained 10⁻⁵ at a checked snapshot? | smallest checked residual (iteration) | non-finite: recursive from step / first snapshot |
|---|---|---|---|---|
| 64 / S1 | 5 (7) | no | 2.32e-4 (12) | 27 / 32 |
| 64 / S5 | 7 | no | 0.886 (768) | – |
| 128 / S1 | 5 (7) | no | 6.51e-4 (24) | 444 / 512 |
| 128 / S5 | 7 | no | 7.08 (1000) | – |
| 160 / S1 | 5 (7) | no | 8.33e-4 (128) | 473 / 512 |
| 160 / S5 | 7 | no | 6.50 (0, the start iterate) | – |

- Snapshots are checked only at the prespecified set C = {0, …, 16, 24, 32, 48, 64, 96, …, 1000} and at the
  native-stop iterate (plan 4.3). Accuracy between snapshots was not measured.
- The S1 continuations break down: their FP32 recursive residual becomes non-finite. Plan 4.8 takes the first class
  that applies, so they are class 5 (numerical breakdown), not class 7 as the queue recorded (D30). Their finite
  snapshots before the breakdown still count.
- At k = 256 the continuation H_S1 reached the 90-min cap (class 6, D21). Its snapshot routine copied the whole
  padded vector to the host in one transfer, 1,235,678,640 B per snapshot, against the plan's 256 MiB chunk limit
  (D27). Whether the prescribed protocol would have finished within the cap is not known. The same qualification
  applies to the record run `R_k256`, whose cap removed S5 at k = 256 (D33).
- Above k = 256 no continuation ran, because the H ladder had stopped.
- **Common accuracy was not attained by the released code at any checked snapshot** (k ≤ 160, S1 and S5), so no
  time to 10⁻⁵ exists for it.
- Our three paths attained 10⁻⁵ at every (k, state) through k = 160, independently checked. Their time to 10⁻⁵ is
  the solve time above.

### Native-stop solve-time ratio, `traeff` / `mg64_rep` (P5; at unequal accuracy at k ≤ 160, accuracy relationship unresolved at k = 256 and 320)

| k / state | ratio [IQR interval] | timed solves released / ours | released class, independent residual (first repeat) | `mg64_rep` independent residual |
|---|---|---|---|---|
| 64 / S1 | 9.39 [9.09, 9.67] | 3 / 3 | 8, 2.33e-4 | 3.13e-6 |
| 64 / S5 | 706 [578, 726] | 3 / 3 | 7 (cap), 0.561 (recursive 0.561, 0.912, 0.605) | 6.11e-6 |
| 128 / S1 | 33.9 [33.5, 35.6] | 3 / 3 | 8, 6.51e-4 | 6.03e-6 |
| 128 / S5 | 1268 [1266, 1268] | 1 / 3 | 7 (cap), 7.09 | 7.35e-6 |
| 160 / S1 | 50.1 [47.6, 50.2] | 3 / 3 | 8, 8.33e-4 | 9.11e-6 |
| 160 / S5 | 1225 [1190, 1225] | 1 / 3 | 7 (cap), 6.52 | 6.13e-6 |
| 256 / S1 (descriptive: G2 not evaluated; accuracy relationship unresolved) | 89.5 | 1 / 3 | 8, missing | missing |
| 320 / S1 (descriptive: G2 not evaluated; accuracy relationship unresolved) | 95.5 | 1 / 3 | 8, missing | missing |

- None of these is a speed-up at equal accuracy (plan 5.2). At S5 the released solve stops at its cap without
  converging.
- At k ≤ 160 the ratios are at unequal accuracy: the released iterate's independent residual exceeds 10⁻⁵ and ours
  does not. At k = 256 and 320 neither path has an independent residual and no released continuation completed, so
  the accuracy relationship is unresolved (D32).
- Where the released path had one timed solve, the interval reflects only our three solves. It holds no estimate
  of the released code's run-to-run variation.
- G4 (D31, D34): no whole solve time behind these ratios can be excluded.
  - Ours: covered at the counter's 5-s resolution, with a plan mean ≤ 0.066 %.
  - Released: the clock-free strict bound over each job window is ≤ 1.73 %. This needs no assumption about the WSL
    clock, whose offset during the jobs the records do not establish. The bound covers whole fixed-state solves only,
    not individual Krylov steps (see P4 below).
  - In the strict bound, five k = 64 rows could at most be flagged (all four paths at S1, and `mg64_rep` at S5).
  - P5 keeps its outcome on this coverage.
  - The bounds cover the process instances that the activity sampler enumerated at its start (D37).

### Krylov-step time (P4; descriptive, G5 failed)
- `traeff`/`mg64_rep` at S1: 22.4 (k = 64), 57.0 (128), 52.0 (160); and 48.2 (256), 40.4 (320) without G2.
- `traeff`/`mgir_rep` inner step: 15.3, 90.9, 92.5; and 88.3, 74.1 without G2.
- No IQRs overlap (`predictions.json` → P4a, P4b).
- The released step times are flagged (G5), so P4 is inconclusive.
- G4 at step duration (D34; `comparison.csv` → `g4_step_*`, `report_tables.md`). The solve-level bounds do not carry
  over to a single Krylov step: the foreign use that the counter intervals admit could all fall into one step. Divided
  by the median step, the same integral gives the following.
  - Released, 64/S1: about 14.3 % (job-window integral 1.26 %·s over the 88.2 ms median step).
  - The 5 % rule is unresolved at step duration for the P4 rows `traeff` 64/S1, `mg64_rep` and `mgir_rep` at 64/S1
    and 128/S1. At k ≥ 160 all P4 step-level bounds are ≤ 1.86 %, and `traeff` 128/S1 is 2.94 %.
  - The step-time ratios are therefore reported as measured, with the interference rule unresolved at k = 64 and
    128, not as cleared.
- **P11** (`mg64_rep`/`mg64_orig` per step, S1): 0.371 (k = 64), 1.003 (128), 1.002 (160), 1.004 (256), 1.003 (320).
  These are reported as measured. The interference rule is unresolved at step duration at k = 64 (bounds 42.1 % and
  15.2 %) and k = 128 (20.0 % and 12.4 %). At k = 160, 256 and 320 the step-level bounds are ≤ 0.80 %. P11 keeps
  its outcome under the plan's rule (G4 excludes only a section with a mean above 5 %), with this qualification.

### Memory (P6; `comparison.csv` M1–M4)
- Released M1 against ours, at k ≤ 160 for both S1 and S5 (P6 uses every (k, state) with data, D30). The values
  agree between the two states to the digits shown:
  - k = 64: 1.66 vs 0.53 (`mg64_*`) and 0.50 GB (`mgir_rep`);
  - k = 128: 2.83 vs 1.32 and 1.04 GB;
  - k = 160: 3.55 vs 2.15 and 1.58 GB.
  - The released M1 is higher in all 18 (k, state, path) comparisons (`predictions.json` → P6).
- Descriptive, without G2: k = 256: 9.57 vs 7.32 and 5.01 GB; k = 320: 13.98 vs 13.60 and 9.11 GB.
- Released host peak (VmHWM): 0.37 GB at k = 64, S1, rising to 15.5 GB at k = 320 (M4, kB in `comparison.csv`).
- Our CuPy pool peaks (M3 used) are 0.08–13.09 GB.
- M2 (device-wide) agrees with M1 to within 1 % except in four rows: released 128/S5 (3.86 against 2.83 GB),
  `mg64_orig` 128/S5 (1.13 against 1.32 GB), and `mg64_*` 160/S5 (2.18–2.19 against 2.15 GB). M2 includes other
  processes' fluctuation.

### Capacity lower bounds (`capacity.json`; P10)

| path | workload | run completed | native stop met | verified | next tested k (class) |
|---|---|---|---|---|---|
| traeff | fixed S1 | 320 (65,536,000 active; 79,588,740 allocated elements) | 320 | none | 384 (2, refusal) |
| mg64_orig, mg64_rep | fixed S1 | 320 | 320 | 160 | 384 (2, refusal) |
| mgir_rep | fixed S1 | 320 | 320 | 160 | 384 (4, spill) |
| traeff | fixed S5 | 160 (class 7: cap) | none | none | 256 (1) |
| our three paths | fixed S5 | 160 | 160 | 160 | 256 (1) |
| traeff | design loop R | 160 | – | – | 256 (6, wall cap under unchunked transfers, D33) |
| our three paths | design loop L | 160 | – | – | not run at 256 (no R) |

"Verified" above k = 160 is blocked by the missing independent check, not by a failed one. The k = 256 and 320
fixed-S1 entries are descriptive completions: G2 and the independent residual are missing there (D22, D28).
Refusals are predictions, not measured limits.

At k = 384 the timed `mgir_rep` run spilled. The queue then also launched that path's history run at the same size,
which plan 7's ladder rule should have prevented (D24). It spilled too and adds no capacity evidence, so the
completed bound stays k = 320. The paper-wide maximum (113,246,208 elements, T27) is not changed by T28.

## Q2: design workload (`update_checks.json`, `design_workload.csv`)

- **Step check at N = 1 (decisive): fails at k = 64, 128 and 160** (P8 contradicts).
  - Failed measures: dv, the filtered dc, x₂, xPhys₂ and the next action.
  - At k = 64: dv rel. L2 0.0109, filtered dc 0.154, x₂ max 0.158, xPhys₂ max 0.0853, next action 0.0121.
  - Raw dc agrees (2.8e-6 to 6.5e-6, within 10⁻⁵).
  - Cause (D14): in this build the released sensitivity filter returns dc unchanged and dv = 1, so the released
    update differs from the planned matched rule.
  - EXPLORATORY, decides nothing: under the as-executed rule (raw dc, dv = 1) the step agrees to 3.0e-8 in x₂ at
    k = 64 and 128, and to 1.25e-6 at k = 160; the next action agrees to ≤ 5.5e-6.
- **Drift:** every state 2–5 is unmatched for every path at k = 64, 128 and 160 (D₂ = 0.085, 0.069, 0.065; D₅ ≈ 0.37–0.41).
  - At k = 64, P9 is therefore supported.
  - No design iteration is a matched workload. The claim status is "distinct workloads" at every k.
- **Native loops, each its own workload, no ratio.** Medians per iteration (`report_tables.md`):
  - released native run N: solve 1.2 / 39.7 / 142 s and design step 0.0171 / 0.0888 / 0.118 s at k = 64 / 128 / 160;
  - our matched-rule loops L: solve 0.106–0.35 s and design step 0.025–0.225 s.
  - The released loops reach the 1000-step cap from design iteration 5 (k = 64) and 4 (k = 128, 160).
  - R's intervals are instrumented (G6 failed). The native loop times come from the N runs at k = 64, 128 and 160.
- **G4 of the loop times** (D31; per iteration in `design_workload.csv`, `g4_*` columns):
  - Solve times (D35). The native runs N and our loops L clear the 5 % threshold at whole-solve resolution; the
    instrumented record runs R do not everywhere:
    - N: clock-free strict bound ≤ 4.30 %, 7 of 13 ok and 6 at most flagged, none excludable. The low-clock rule is
      undecided for N's solves 2–4 at k = 64 (1.03–2.90 s).
    - L: plan mean ≤ 0.039 %, strict bound ≤ 2.94 %, none excludable.
    - R (instrumented, G6): clock-free, 6 ok, 18 at most flagged and 4 unresolved. The unresolved ones are the k = 64
      solves of iterations 1–4 (bounds 161.1, 121.2, 135.2 and 51.6 %; 0.76–2.37 s against the job's 1420-s window).
      For them the 5 % rule is undecided.
  - Design steps last 0.016–0.23 s, much shorter than the 5-s counter interval:
    - the 5 % rule is undecided ("unresolved") for all 13 N design steps, all 28 R design steps and 48 of the 84 L
      design steps (k = 64);
    - the plan mean is ≤ 0.039 % for L, and ≤ 0.035 % for N where it can be located (k = 128). At k = 64 and 160 the
      records refute a constant WSL clock offset, and only N's job-window means (0.035 % and 0.0029 %) are available.
    - R's design steps have no constant-offset reading. The record driver times its design step after the untimed
      compliance transfer and dumps, and in iterations 1–4 as a sum of pieces separated by dumps, so the evaluated
      window [solve return, solve return + design time] is not the timed interval (D36). Only their whole-job bounds
      are kept (job-window means 0.086 %, 0.033 % and 0.0030 % at k = 64, 128 and 160).
  - The design-step times are therefore reported with the 5 % rule undecided, not as cleared.
- **R at k = 256** is invalid: it reached the wall cap under the record driver's unchunked transfers (D33). The capped
  third solve (1000 steps, recursive residual 19.06) is a diagnostic of that interrupted run under the transfer method
  used, not a design-loop result.

## Predictions (`predictions.json`)

| id | outcome | basis |
|---|---|---|
| P1 | supports | released native-stop iterate (first timed solve) > 10⁻⁵ at 64, 128, 160 / S1; 256 and 320 listed as missing the independent check |
| P2 | supports | 10⁻⁵ not attained at any checked snapshot of the six completed continuations (k ≤ 160, S1 and S5); accuracy between snapshots and at k ≥ 256 unresolved; the S1 continuations are class 5 (breakdown) after their finite snapshots |
| P3 | supports | k = 64, S5: class 7 in all three repeats, 1000 steps; checked first repeat 0.561 (recursive 0.561, 0.912, 0.605) |
| P4a | inconclusive | G5 failed (flags every released step time); the ratios > 1 everywhere are descriptive; G4 unresolved at step duration at k = 64 and 128 (D34) |
| P4b | inconclusive | as P4a |
| P5 | supports | ratio > 1 at all six gated (k, state), at unequal accuracy; one released timed solve at 128/S5 and 160/S5; G4: no whole solve time excludable, released whole-solve bound ≤ 1.73 % clock-free (D31; whole solves only, D34); 256 and 320 descriptive, with the accuracy relationship unresolved (D32) |
| P6 | supports | released M1 higher at k = 64, 128, 160, S1 and S5, for all three paths (18 of 18; also at 256 and 320 S1, descriptive) |
| P7 | **contradicts** | class 9 at all 18 (k, state, path) through k = 160; class 8 at k = 256 and 320 because the independent residual is missing (no residual > 10⁻⁵ anywhere) |
| P8 | **contradicts** | step check fails at every k with an R run (D14) |
| P9 | supports | states 2–5 unmatched for all paths at k = 64 |
| P10 | **contradicts** | `traeff` and `mg64_*` as predicted (bound 320, refused at 384); `mgir_rep` spilled at 384 instead of completing |
| P11 | supports | `mg64_rep`/`mg64_orig` step ratio ≤ 1.15 at every k (1.002–1.004 at k ≥ 128; 0.37 at k = 64, ramping clock, D17); ratios as measured: the interference rule is unresolved at step duration at k = 64 and 128, and the step-level bounds are ≤ 0.80 % at k = 160–320 (D34) |

The contradictions of P7 and P10 rest on the spill rule. In the three spilled jobs, the shared usage crossed the
256 MiB limit only when the 77,594,624 B present right after the CUDA context was counted. Measured from the first
own sample, the growth was 220–231 MB (D23). That is reported for the authors' information. The guard's decision
stands.

## Findings carried from T12 (nvc 26.11 on this card, not the published A100 configuration)
- Build adaptations: a cc89 Makefile, the libgomp shim and the removal of five `nowait` clauses.
- The released solver reaches its 1000-step cap within the first five design iterations.
- Its first solve is not bitwise reproducible.
- In T28 the same cap appears at the warm-started state S5 at every k with S5.

## Corrections after the second check (D24, D26–D30)

| check point | correction | files |
|---|---|---|
| 1. G4 coverage | G4 re-evaluated on the counter intervals that overlap each section, with our setup (b) included. All sections are covered and "ok"; the strict bound excludes nothing. P5 and P11 keep their outcomes, with the coverage stated at the 5-s resolution. Released setup (a) at k = 256 and 320 is low-clock and is not repeated | `drivers/g4check.py`, `g4_activity.json`, D26 |
| 2. repeats | timed-solve counts and per-repeat residuals added; the checked iterate is named (first solve); single released solves leave the ratio interval without released variability | `comparison.csv`, `predictions.json` → P5, this report |
| 3. common accuracy | scoped to the checked snapshots of the six completed continuations; the S1 continuations reclassified 7 → 5 | `out/collect_common_accuracy.json`, P2, D30 |
| 4. transfers | the unchunked whole-vector transfers are recorded; H_S1_k256's wall cap is a result of the protocol as run | D27 |
| 5. k = 256 inputs | the dumps of the invalid R_k256 were compared with the dump-free references and are equal; k = 256 and 320 are described as descriptive completions | `fix_r2/check_k256_inputs.json`, D28 |
| 6. k = 384 history run | it should not have been launched; it adds no capacity evidence, and the bound stays k = 320 | `capacity.json`, D24 |
| 7. R′ wall predictor | the predictions as run and under the frozen rule are recorded; no admission changed | D29 |
| 8. assembly | P6 over S1 and S5 (18 of 18); refusal rows cite their `.refused.json` records | `predictions.json` → P6, `comparison.csv`, D30 |

The first G4 row above is superseded in part by the third and fourth checks, below.

## Corrections after the third check (D31–D33)

| check point | correction | files |
|---|---|---|
| 1. released per-solve setups and undecidable clock | The 16 released per-solve setups are now evaluated: 10 are unresolved under the 5 % rule, because each lasts 0.04–0.70 s against a 5-s counter. The low-clock rule is stated as undecided for our 6 setups (a) of ≥ 1 s with no clock series, and for the released setups that cannot be located in the clock series. Setup times enter no prediction | `drivers/g4check.py`, `g4_activity.json`, `comparison.csv`, D31 |
| 2. WSL clock alignment | No offset is assumed. The decisive released value is the clock-free strict bound over the job window. The plan's mean is given only under a constant offset in the interval the records allow, and is "not available" where the records refute one (F_S1_k160, N_k64, N_k160). Released solve times: ≤ 1.73 %, none excludable. The low clock of setup (a) at k = 256 and 320 is conditional | same, D31 |
| 3. design-loop timings | The N, R (k ≤ 160) and L jobs are evaluated per iteration, solve and design step. Solve times are not excludable; most design steps are unresolved at the 5-s resolution. G6 now names the N runs at k = 64, 128 and 160 | `design_workload.csv` (`g4_*`), `gates.json` → G4, G6, D31 |
| 4. k = 256/320 labels and inputs | The ratios are labelled "accuracy relationship unresolved". The inputs are stated per size: our k = 256 runs read the R_k256 dumps (checked equal to the references), our k = 320 runs used the formula rebuild, and the released runs build their own system | `predictions.json` → P5, `capacity.json`, D32 |
| 5. R_k256 | Its wall cap, and the missing S5 at k = 256, are qualified by the unchunked transfers. Iteration 3's residual 19.06 is a diagnostic of the interrupted invalid run, not a design-loop result | `capacity.json` → `traeff/design_loop_R.note`, D27, D33 |

Every prediction keeps its outcome. The changes in `predictions.json` are P5's G4 bound values (the released bounds
are now clock-free) and the two k = 256/320 labels. The values before these corrections are in `fix_r3/*_before_r3.*`.

Rows 2 and 3 above are superseded in part by the fourth check, below. The 1.73 % bound covers whole solves only, the
record-run solves are not all clear, and R's design steps have no conditional reading.

## Corrections after the fourth check (D34–D37)

| check point | correction | files |
|---|---|---|
| 1. 1.73 % bound and Krylov steps | The released 1.73 % bound covers whole fixed-state solves only. At step duration the same integral over the median step gives about 14.3 % at k = 64/S1 (1.26 %·s over 88.2 ms). The 5 % rule is unresolved at step duration for 15 of 32 timed rows (all of k = 64, and k = 128 except `traeff` S1). The P4 and P11 step-time ratios are reported as measured with the interference rule unresolved at k = 64 and 128, not as cleared | `drivers/g4check.py` (`step_level`), `comparison.csv` (`g4_step_*`), `gates.json` → G4 → `krylov_step_level`, `predictions.json` → P4a, P4b, P11 (`g4_step_level`), P5 (`g4_scope`), D34 |
| 2. loop solves | No longer "all loop solves clear exclusion". The native runs N and our loops L clear the threshold at whole-solve resolution. The instrumented record-run solves of iterations 1–4 at k = 64 are unresolved (161.1, 121.2, 135.2 and 51.6 %) | `gates.json` → G4 → `design_loop_solves`, D35 |
| 3. R design steps | The constant-offset readings for the 28 record-run design steps are dropped: their windows do not match the driver's design timer. Their whole-job bounds and the classification of all 28 as unresolved stay. The largest plan mean that can be located is now 0.65 % (was 0.91 %, an R design-step reading) | `drivers/g4check.py`, `g4_activity.json`, `design_workload.csv` (`g4_design_mean_foreign_pct` empty for R), D36 |
| 4. sampler coverage | Limitation: the single wildcard counter query bounds activity from the process instances enumerated at its start. The records neither establish coverage of processes created later nor show that such a process interfered | `g4_activity.json` → `limitation`, `gates.json` → G4 → `limitation`, D37 |

No GPU job was run and no measured value changed. Every prediction and every gate keeps its outcome. The frozen plan
is unchanged. The CPU-only before/after comparison `fix_r4/check_r4_diff.json` passes: no earlier cell of
`comparison.csv` changed. In `design_workload.csv` only R's design-step plan mean and basis changed. In
`g4_activity.json`, `gates.json` and `predictions.json` only the items above changed. `capacity.json`,
`update_checks.json` and `out/collect_common_accuracy.json` are byte-identical. The outputs and drivers as they were
before are kept as `fix_r4/*_before_r4.*`.

## Files
- `comparison.csv`, `update_checks.json`, `design_workload.csv`, `capacity.json`, `gates.json`, `predictions.json`,
  `residual_histories/*.csv` (30 files), `report_tables.md`, `verification.json`, `g4_activity.json`, `DEVIATIONS.md`.
- Second-check corrections: `drivers/g4check.py` and the CPU-only checks in `fix_r2/`: `check_k256_inputs.json`,
  `sampler_lag.json` and `wsl_clock_offset.json`. The outputs as they were before are kept as
  `fix_r2/*_before_r2.*`.
- Third-check corrections: `drivers/g4check.py` (revision 3) and the edits to `collect.py`, `analysis.py` and
  `summary.py` (`fix_r3/patch_summary_r3.py`). The outputs and drivers as they were before are kept as
  `fix_r3/*_before_r3.*`.
- Fourth-check corrections: `drivers/g4check.py` (revision 4), `collect.py`, `analysis.py` and `summary.py`; the
  check `fix_r4/check_r4_diff.py` → `fix_r4/check_r4_diff.json`. The outputs and drivers as they were before are kept
  as `fix_r4/*_before_r4.*`.
- Records: `out/*.json`, `runs/*/monitor.json`, `scratch/*/meta.txt`, `out/queue_state.json`, `logs/`.
