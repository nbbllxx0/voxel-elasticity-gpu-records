# T28 deviations and implementation notes

The frozen plan is `ANALYSIS_PLAN.md`; it was not edited. Each item below gives what was done, why, and which endpoint
it affects. Items marked "no endpoint affected" are implementation details that the plan leaves open. Items marked
EXPLORATORY add information outside the plan and decide nothing.

## Guards and launchers

**D1. WSL record folder.** `tasks/T12/t12mon.py` revision 4.3 is used in place and unchanged. Its `main()` writes
records under `tasks/T12/runs/<tag>`, so `drivers/t28mon.py` repeats `main()`'s three statements (record header,
`GpuLock`, `t12mon.run`) with the folder `tasks/T28/runs/<tag>`. It passes the matching WSL path to t12mon's own
`write_launcher`/`start_job` through their `wsl_dir` parameter. The lock, exclusivity check, samplers, armed live
stop, admission probe, launch, `close_watch`, `killtree.sh`, `validate` and `record_coverage` are t12mon's.
No endpoint affected.

**D2. Host-memory admission and G4 samplers in the WSL wrapper.** Plan 4.7's host admission (VmHWM fit × 1.25 + 4 GiB
≤ MemAvailable inside WSL; MemAvailable ≥ 8 GiB with no prior) is checked by `t28mon.py` before t12mon starts. At
k = 128 only one measured size exists, so the VmHWM prediction scales the k = 64 value by the padded-node ratio. The
G4 activity sampler (foreign 3D-engine use excluding the WSL VM worker) and the SM-clock sampler run in the wrapper,
outside the guard. No endpoint affected.

**D3. Pre-exit hold.** The released driver holds 4 s with every allocation alive before it exits (`-H 4`). This is
outside every timed interval. `t12mon.validate` needs at least three WDDM samples inside a job, and a k = 16 test
job without the hold had two. This is a fourth difference of the driver from the T12 harness, beside the three that
G1 lists. It changes no arithmetic and no interval. No endpoint affected.

**D4. Epoch pairing.** The released driver writes one `gettimeofday`/`omp_get_wtime` pair (`epoch_pair`) so its
intervals can be placed on the Windows G4 samplers. `omp_get_wtime` is epoch-based on this toolchain: the pair agrees
to 1 µs. No endpoint affected.
Correction after the third check (D31): the pair ties `omp_get_wtime` to the WSL wall clock only. It does not tie the
WSL clock to the Windows clock of the G4 samplers, whose offset during a job is not known.

## Order of steps

**D5. G3 is evaluated in the k = 64 checker (K2_k64).** G3 needs states S1 and S5 at k = 64. S5 at k = 64 exists
only after the k = 64 record run, which is confirmatory step 1, so G3 cannot precede it. Step V ran the same checker
at k = 16 and 32 as a preliminary. No k > 64 job starts before K2_k64 has written G3.

**D6. G1's continuation-iterate comparison at k = 32** uses a second verification run of the continuation build
(`V_Hg1_S1_k32`). The checker of the first verification run had already deleted that run's snapshots, as Section 6
requires. Verification only.

**D7. Verification checker rerun.** The first verification checker passes (`pretest_V_K2_k16_noprefix`,
`pretest_V_K2_k32_noprefix`) looked for the iterates without the `V_` prefix and found none. Their snapshot sets
were therefore not checked and not deleted. The corrected passes `V_K2_k16` and `V_K2_k32` replace them.
Verification only. The k = 16 build pre-test files (`pretest_*`) are kept and are not verification records.

## Definitions the plan leaves open

**D8. Krylov-step median and IQR** are taken over all steps of all timed solves of the run (three for our paths, up
to three for the released code), not over one solve.

**D9. Matched-rule loop (L).** The hierarchy is built once (setup a). Each state updates it with that state's moduli
(`mg.update(E)`), as a design loop would. The loop's per-solve setup is the moduli update plus `mg.update`. The solve
starts from the previous state's solution.

**D10. Drift thresholds where the released self-difference is unavailable.** R′ makes four solves and dumps xPhys at
states 1–5. So S_N exists for N ≤ 5, and S^c_N only for N ≤ 4. For N = 5, and for N > 5 at k = 64, the thresholds
fall back to their floors (10⁻³ and 10⁻⁴). At k ≥ 128 the record run makes no fifth solve. There c₅ of the released
code is the compliance of the released fixed-state S5 iterate (F-S5, checked by K2), which starts from the same U₄.
A state whose compliance is missing is not matched.

**D11. The released action at S5 on "the released U"** is K(xPhys₅)·(float)U₄. The record run makes no fifth solve
at k ≥ 128, so U₅ does not exist there, and U₄ is the S5 start of every path. It is taken at every k.

**D12. Admission predictions of auxiliary jobs.** The plan gives prediction formulas for the solver paths and the
released jobs. The checker (K1, K2), the step check and the matched-rule loop use workspace estimates
(`queue_t28.ours_predict`) until two measured sizes of the same job type exist; from then on they use a fit through
those two sizes. Each record holds its prediction and basis.

**D13. History wrapper for `mgir_rep`.** T27's `HistR` used the solver's FP64 operator, which T28's lean `mgir_rep`
path does not hold. The history process therefore builds an FP64 `node_hoist` operator with FP64 moduli, outside the
pool peak of any timed run. Untimed. No timed endpoint affected.

## Findings that change what a step can show

**D14. The released sensitivity filter has no effect in this build (found in verification at k = 16).** In the T28
record runs, the released `dc` read back after `applyDensityFilterGradient` is bitwise equal to the raw `dc`, and the
released `dv` is 1 on every element. The density filter (on the host) works. The released update therefore runs OC
on the unfiltered sensitivities with dv = 1. The frozen matched rule (plan 4.6) includes the sensitivity filter and
dv = H(1/Hs). The decisive step check compares against that rule, and its tolerances are kept. The step-check records
also report, EXPLORATORY, the same step under the as-executed rule (raw dc, dv = 1). This decides nothing, and it does
not replace the matched rule.

**D15. The released continuation can break down after convergence.** At k = 16 (verification), the FP32 recursive
residual of the continuation reached 3.8e-12 and then became NaN. Snapshots after that point have non-finite
residuals. Common accuracy is read from the first finite snapshot at or below 10⁻⁵. The smallest finite residual and
its iteration are reported.

## Running the queue

**D16. Queue restart between jobs.** The queue was started for k = 128–384 in one process. It was stopped during
R_k128 because one process could not finish within the 6-hour limit on background commands. Only the queue process
was ended; the guarded launcher of R_k128 ran to completion. The queue was restarted in per-k chunks after that
launcher had exited. The restarted queue read R_k128's own record, which is valid, and did not rerun it. A stop file
(`out/STOP`) lets the queue end between jobs. No endpoint affected.

**D17. Clock ramp during short timed sections.** At k = 64, our timed solves last 0.04–0.17 s. Some of them ran
while the SM clock was still ramping up from idle: the median SM clock of the window was 795–900 MHz. G4's low-clock
rule covers only sections of 1 s or more, so these measurements are valid under the plan and were not repeated.
`comparison.csv` gives, per row, the smallest median SM clock of its timed windows
(`timed_window_sm_clock_mhz_min`), so that the effect can be seen.

**D18. Queue ended by the session, stale lock released by the operator.** The k = 128–160 queue chunk ended at
21:42:35, when the earlier 6-hour per-call limit ended the first T28 session (operator note of 19:00, addendum
21:56). That was one second after it had
launched `HO_S1_k160_mg64_orig` (ours.py, pid 50292) and before the job wrote any record. The queue saved no entry for
the job. `gpu_job.lock` remained, owned by pid 50292. Before the queue was restarted, the operator checked three
things: pid 50292 no longer existed, nvidia-smi showed only the desktop's baseline (2582 MiB used, 0 % utilization),
and no T28 process was running inside WSL. Only then was the lock file removed. The guard itself never removes a lock.
The restarted queue runs `HO_S1_k160_mg64_orig` as a first run, because the killed attempt measured nothing and left
no record. Under the operator's 19:00 note this counts as a rerun after an operator stop, not as a refusal. No endpoint
affected.

**D19. Operator stop between jobs at k = 160; the guard self-tests were not rerun at the 21:44 restart.**
- The second session restarted the queue at 21:44:38 (`logs/queue_k160_resume.log`). It completed four jobs, all
  with complete records whose coverage and validity pass:
  - `HO_S1_k160_mg64_orig`, `HO_S1_k160_mg64_rep` and `HO_S1_k160_mgir_rep`;
  - `F_S5_k160` (class 7, 1000 steps, monitor record clean and covered).
- The operator created `out/STOP` at 21:53:07. The queue finished its current job (`F_S5_k160`, ended 22:06:58) and
  ended before `T_S5_k160_mg64_orig`, as the stop-file mechanism of D16 provides. This is an operator stop between
  jobs. No job was interrupted, and no record is incomplete.
- The operator's note of 19:00 asks for both guard self-tests to be rerun before the first new GPU job after a
  restart. That note was not in the second session's task brief, so the four jobs above ran without the rerun. The
  guard files they used are byte-identical to the files G0 tested: `t12guard.py`, `t12mon.py`, `killtree.sh` and
  `t12_gate.py` give the same SHA-256 digests as `g0/t12_manifest_after.txt`. The four records therefore stand, as
  the note directs for complete runs whose monitor records pass.
- The next session reruns both self-tests (`tasks/T12/test_t12guard_v4.py` and `tasks/T12/test_t12kill_v4_3.py`)
  before its first GPU job, then continues the k = 160 block at `T_S5_k160_mg64_orig`. Still to run at k = 160:
  T-S5 (three paths), H-S5, HO-S5 (three paths), the step check, the three L loops and K2. The blocks for k = 256,
  320 and 384 follow.
- No endpoint affected.

**D20. Third session: G0 rerun, then the k = 160 block resumed at `T_S5_k160_mg64_orig`.**
- The operator stop of D19 ended the second session as blocked; under the operator's second addendum (22:15) that
  was the stop the operator meant, not a fault, and its result was set aside. The stop file was gone, no
  `gpu_job.lock` was present, nvidia-smi showed the desktop baseline only (0 % utilization), and no T28 process ran
  in Windows or WSL.
- Before the first new GPU job both guard self-tests were rerun (`g0/resume_k160/G0.json`): `test_t12guard_v4.py`
  passed 51 of 51 cases (revision 4.3); `test_t12kill_v4_3.py` passed (A: 18 of 18 launches ended and confirmed;
  B: 4.3 confirmed with no surviving child, the 4.2 control reproduced its fault; C: survivors left the end
  unconfirmed). T12's own records were backed up and restored; T12's file manifest is identical before and after.
  Compared with the first G0's manifest, the only new files in T12 are six `__pycache__/*.pyc` bytecode files;
  every source and record file is identical.
- The queue was restarted as the per-k chunk `queue_t28.py run 160` (`logs/queue_k160_resume2.log`), keeping the
  stop-file mechanism. Every completed job kept its record and was not rerun.
- No endpoint affected.

**D21. Released wall predictions at k = 256 fell short of the measured times; both jobs ended at the 90-min cap.**
- `R_k256` was predicted at 324 s by the plan's rule (four F-S1 solves plus four design steps at k = 160, scaled by
  the padded-node ratio). Its third design iteration's solve reached the 1000-step cap with a recursive residual of
  19.06 and took 4,538 s (`scratch/R_k256/meta.txt`), so the job reached the cap at 5,400 s: class 6. The plan's
  rule assumes native-stop solves; the record runs at k = 64–160 had already shown the released solver at its cap
  from design iteration 4 (k = 128, 160) or 5 (k = 64).
- `H_S1_k256` was predicted at 4,278 s (per-solve setup + 1000 × the F-S1 median step + snapshot writing at 1 GB/s).
  It reached the cap: class 6. At k = 160 the continuation runs took 2,441–2,796 s against a prediction of 1,181 s,
  because the snapshots are written from WSL to the Windows drive at far less than 1 GB/s.
- Both caps were enforced inside WSL (`timeout --signal=KILL`); no released process survived and both monitor
  records are clean and covered. Under plan 7 the class 6 stops the released R and H-S1 run types from ascending,
  so k = 320 and 384 have no R, R′, N, K1 or H run, and S5 does not exist at k ≥ 256 (class 1).
- The predictions were applied as frozen. No endpoint definition changed.
- Correction after the third check (D33): R_k256's wall cap is qualified by the record driver's unchunked transfers,
  and its iteration 3 is a diagnostic of an interrupted invalid run, not a design-loop result.

**D22. The independent checker K2 was stopped for a spill at k = 256 (class 4); no independent residual at k ≥ 256.**
- `K2_k256` was admitted (predicted 4.00 GB, driver free 24.15 GB). It was stopped by the spill sampler when its
  shared usage reached 297,795,584 B at 2,798,202,880 B dedicated (`out/K2_k256.refused.json`). Under the authors'
  rule a spill is never rerun at the same size, and the queue's ladder stops K2 from ascending, so K2 did not run at
  k = 320 or 384.
- Consequences: G2 is not evaluated at k ≥ 256 (it needs a valid R as well, see D21). The fixed-state iterates at
  k = 256 and 320 have no independent FP64 residual. Under plan 4.8 their class is 8 ("independent residual …
  missing"), although the in-solver FP64 true residuals of `mg64_*` and the outer FP64 residuals of `mgir_rep` are
  all ≤ 10⁻⁵ (these are not independent checks).
- The K2 checker's shared usage grew with k in the valid runs: 98,566,144 B (k = 64), 121,634,816 B (128) and
  138,412,032 B (160) above the stop baseline (`out/K2_k{64,128,160}.json`).

**D23. Spill baseline of a new CuPy process.** `t12guard.cupy_guard` revision 4.3 (used unchanged, G0) takes a
process's shared baseline as 0 because the process is absent before it starts. The first sample with the process
already held 77,594,624 B shared, just after its CUDA context was created. The three spills of this session
(`K2_k256`, `T_S1_k384_mgir_rep`, `HO_S1_k384_mgir_rep`) crossed 268,435,456 B only with that amount counted. Measured from
the first own sample their growth was 220,200,960 B, 230,686,720 B and 230,686,720 B. The guard's decision stands.
The jobs were stopped and no number from them is kept. This is reported for the authors' information, not as a
change of rule.

**D24. `HO_S1_k384_mgir_rep` started after `T_S1_k384_mgir_rep` had spilled.** The queue treats the history run as
its own workload with its own ladder. It therefore launched the history run of `mgir_rep` at k = 384 after the timed
run of the same path and size had been stopped for a spill. The history run spilled as well (308,281,344 B shared at
13,948,866,560 B dedicated), and nothing from it is kept. The authors' rule forbids rerunning a spilled run at the same
size. The history run is a different measurement, not a repeat of the timed run, but it ran the same solver at the same
size, so it is listed here. No endpoint is affected, because neither job yields a number.
Correction after the second check: under plan 7, a path stops ascending for a workload at its first class 4 at that
workload. The history run belongs to the same fixed-S1 workload of `mgir_rep`, so it should not have been launched.
Its spill adds no capacity evidence, and the completed lower bound of `mgir_rep` at S1 stays k = 320
(`capacity.json`, `mgir_rep/fixed_S1.note`).

**D25. Final assembly.**
- `drivers/analysis.py` now applies three plan rules that it had not applied before:
  - P4a and P4b are inconclusive because G5 failed (plan 5.2: "G4 or G5 fails at every k"). G5 is the single
    k = 64 test whose failure flags every released step time. The ratios are kept as descriptive values.
  - Released-path entries enter P4, P5 and P6 only at a k where G2 passed (plan 5.2: "with data" means gates
    passed). The k = 256 and 320 values are given beside them as descriptive.
  - The G0 record of this session (`g0/resume_k160/G0.json`) is included.
- `drivers/collect.py` adds notes to the class-1 and class-4 rows of `comparison.csv`. The class-4 rows also get
  their admission inputs, read from the refusal records.
- No measured value changed.

## Corrections after the second check (assembly only; no GPU job, no measured value changed)

**D26. G4 was evaluated on the wrong samples; re-evaluated from the saved samples.**
- The plan (5.1) asks for the mean foreign 3D-engine use over each timed section, sampled every ≤ 10 s. The sampler
  reads the Windows counter every 5 s, and each value is the mean over the interval since the previous sample.
- The first evaluation (`t28lib.g4_eval`, `collect.g4_wsl`) averaged the samples received within 5 s of either end
  of a section. That window includes samples whose interval ends before the section starts. It also left out our
  setup (b), which is part of our reported solve time. For 64 of our 72 timed solves, no sample was received inside
  the solve. Report and gates therefore claimed more coverage than the evaluation had.
- `drivers/g4check.py` (output `g4_activity.json`) now takes the counter intervals that overlap each timed section:
  setup (a), setup (b), each solve, and each reported solve time of ours, which is setup (b) + solve.
  - Margins: 0.1 s for our processes. The counter's reception lag is ≤ 9 ms (`fix_r2/sampler_lag.json`).
  - 2 s for the released runs, whose section times come from the WSL clock. Offsets of about 1.3 s between the WSL
    and Windows clocks were seen (`fix_r2/wsl_clock_offset.json`).
  - Setup (b) of ours has no wall timestamps. It is evaluated over its envelope, from the end of the memory pass to
    the start of timed solve 0.
- Result:
  - All 144 timed sections are covered by counter intervals: 120 of ours and 24 of the released runs.
  - The plan's measure, the mean over the covering intervals, is ≤ 0.13 % everywhere. Every section is "ok".
- That measure is taken at the counter's 5-s resolution. A section shorter than 5 s is diluted in it. So the file
  also gives a strict bound, in which all foreign use of the covering intervals is placed inside the section.
  - That bound is ≤ 4.1 % for single sections and ≤ 2.04 % for reported solve times.
  - No section could exceed the 5 % exclusion level under any distribution of the foreign use.
  - Single sections with a bound in the 1–5 % flag band occur at k = 64 and 128 (32 sections). Reported solve
    times with a bound in that band occur only at k = 64 (9 of 72). In the strict reading these would at most be
    flagged, and flagged times stay in the analysis.
- The SM-clock rule was applied to the setup sections as well:
  - Released setup (a) at k = 256 and 320 ran at a median of 210 MHz, the idle clock, and is "low clock". The plan
    asks for one repeat. The runs are complete, and the operator's note of 19:00 forbids repeating them, so these
    setup values are reported flagged, not repeated.
  - Our setup (a) sections of ≥ 1 s at k ≥ 160 have no saved clock series. Their low-clock status is "not saved".
  - No prediction uses setup time.
- Endpoints: no row of `comparison.csv` changes its G4 activity class. P5 and P11 keep their outcomes, now with this
  coverage stated.
- Superseded in part by D31 (third check): the 2-s margin for the released runs assumed a clock alignment that the
  records do not establish. The released per-solve setups and the design-loop jobs had not been evaluated, and the
  low-clock finding for the released setup (a) at k = 256 and 320 holds only under a constant clock offset.

**D27. Whole-vector device↔host transfers in the released driver were not chunked to ≤ 256 MiB (plan 6).**
- The continuation build's snapshot routine (`released/lib_cont/stencil_solvers.c:14`) copies the whole padded FP64
  displacement vector to the host for every snapshot. That is 326,002,608 B at k = 160 and 1,235,678,640 B at
  k = 256, above the 256 MiB limit. The row-wise file writes follow.
- The fixed-state and record drivers (`released/t28_driver.c`) do the same for U, the FP32 dumps and the uploads of
  the start vector. At k ≥ 160 the FP64 vectors exceed the limit, and at k ≥ 256 the FP32 vectors do too. These
  transfers all lie outside every timed interval. Our CuPy processes do chunk theirs (`t28lib.to_host`).
- These are copies, so no residual, iterate or action changes. Every such job's monitor record is clean and covered.
- What the deviation leaves open is wall time. `H_S1_k256` reached the 90-min cap (D21) under the transfer protocol
  as run. Whether the prescribed chunked protocol would have finished within the cap is not known. Its class 6 is a
  result of the protocol as run.
- Extended after the third check (D33): the same applies to the record run `R_k256`.

**D28. At k = 256 our drivers read their inputs from the dumps of the invalid record run `R_k256`.**
- `ours.the_system()` uses a record run's dumps whenever `F.f32` exists, and the queue passed `scratch/R_k256`.
  `R_k256` ended at the wall cap (class 6) and is invalid. The plan (4.8) excludes all outputs of an invalid job.
- Without those dumps, the plan (3.2) prescribes three references: the formula rebuild of the load rounded to FP32,
  the formula rebuild of the supports, and the k = 64 `KE0`.
- The dumps were compared with those references (`fix_r2/check_k256_inputs.json`, CPU only). The load is
  entry-by-entry equal over 101,649,411 entries, with no halo entry. The fixed set is identical (100,230 DOFs). `KE0`
  is bitwise equal to the k = 64 dump.
- The systems solved at k = 256 are therefore the ones the plan prescribes, and the numerical values stand.
- The dump-level check is not G2. G2's action agreement needs a valid record run, so G2 stays not evaluated at
  k = 256 and 320. With the independent residual also missing (D22), the k = 256 and 320 rows are descriptive
  completions.

**D29. The wall-time predictor for R′ and for N at k ≥ 128 differed from the frozen rule.**
- The plan (7) predicts R′ from four F-S1 solves and four design-step intervals at the next smaller k, scaled by
  the padded-node ratio. The queue (`queue_t28.py`, R′ and N blocks) used the sum of the current R's first four
  solves and design steps, capped solves included.
- Predictions as run, against the frozen rule (`out/queue_state.json`, `wall_prediction_s`):
  - k = 64: 5.1 s against none, because there is no smaller k;
  - k = 128: 859 s against 24.3 s;
  - k = 160: 1,605 s against 67.7 s.
- Every value lies far below the 5,400-s cap, so no admission changed. R′ and N did not run at k ≥ 256, because R
  there was class 6.

**D30. Assembly corrections.**
- **Continuation classes.** The queue classed the three S1 continuations H_S1_k64, H_S1_k128 and H_S1_k160 as
  class 7, but their FP32 recursive residual became non-finite from step 27, 444 and 473. Plan 4.8 takes the first
  class that applies, so a non-finite residual (class 5) comes before the iteration cap (class 7).
  - `collect.py` now gives these continuations class 5 and keeps the queue's class beside it.
  - The finite snapshots before the breakdown still decide P2.
- **P6 states.** P6 now uses every (k, state) with data, S1 and S5 at k = 64, 128 and 160 (plan 5.2). Before, it
  used only S1. The released M1 is higher in all 18 comparisons.
- **Refusal records.** The class-2 rows at k = 384 for `mg64_orig` and `mg64_rep` now cite their records
  `out/T_S1_k384_*.refused.json`. Rows without a record of their own (class 1) cite their queue entry.
- **New columns in `comparison.csv`.** The number of timed solves and the in-solver residual of each repeat.
  Released, k = 64/S5: 0.561, 0.912 and 0.605, with 0.561 the first repeat, whose iterate the checker evaluated.
  Also the corrected G4 columns.
- The files as they were before these corrections are kept in `fix_r2/*_before_r2.*`.

## Corrections after the third check (assembly only; no GPU job, no measured value changed)

**D31. G4 revision 3: every presented timed section, and no assumed clock alignment for the released runs.**
- *Released per-solve setups.* The 16 released per-solve setup intervals (b), from entry of `solveStateMG_halo` to the
  start of its CG loop, are reported in `comparison.csv` but had not been evaluated. `drivers/g4check.py` now evaluates
  them, together with setup (a) and the solves.
- *Clock alignment.* The released sections are timed on the WSL clock and the G4 samplers on the Windows clock. The
  2-s margin of D26 assumed that the two clocks agree to within 2 s during each job. The records do not establish
  this:
  - assuming a constant offset during a job, the records bound it by t_prog0 ≥ t_launch and last timestamp + 4-s hold
    ≤ t_exit;
  - that interval is empty for `F_S1_k160` ([+0.410, −0.183] s), `N_k64` and `N_k160`, so the records refute a
    constant offset there;
  - elsewhere it is up to 16 s wide (`F_S1_k256`: [−16.55, −0.43] s);
  - the later reading of +1.3 s (`fix_r2/wsl_clock_offset.json`) cannot stand in for the offset during the jobs.
- *New rule, released runs.* Two tiers (`g4_activity.json`, each released section):
  - **clock-free (decisive):** every section lies inside its job's window [t_launch, t_exit] of
    `runs/<job>/monitor.json`, which is on the samplers' clock. The strict bound (the foreign use of all counter
    intervals overlapping the job window, divided by the section's duration) needs no alignment;
  - **conditional:** under a constant offset in the record-derived interval, the section's envelope on the Windows
    clock is evaluated as before. Where the interval is empty, this tier is not available.
  - In `comparison.csv` the released `g4_activity` is now what the clock-free bound proves (ok < 1 %, at most flagged
    1–5 %, unresolved > 5 %). The plan's mean is in `g4_max_mean_foreign_pct` as a conditional value.
  - "Unresolved" means that the 5 % rule is undecided. It does not mean that interference was seen: the plan's
    mean, wherever it can be located, is ≤ 0.13 % in the fixed-state runs and ≤ 0.91 % in all jobs.
- *Clock rule, released runs.* The SM-clock series is on the Windows clock too, so the median inside a released
  section cannot be read exactly. A median of n samples is low only if at least ⌈n/2⌉ are low; a section of duration d
  holds at least ⌊d/g⌋ samples (g the largest gap). Counting the low and high samples in a window that surely contains
  the section (clock-free: the job window; conditional: the envelope) proves "not low", proves "low" or leaves it
  undecided.
- *Design-loop jobs.* The native runs N (k = 64, 128, 160), the record runs R (k = 64, 128, 160; instrumented, G6) and
  our matched-rule loops L are now evaluated section by section, solve and design step of every iteration. The
  per-iteration values are in `design_workload.csv` (`g4_*` columns). `R_k256` is invalid and is not evaluated (D33).
- *Results:*
  - **Released fixed-state solves** (16 sections): the clock-free bound is ≤ 1.73 %. No solve time can be excluded
    under any clock alignment. Three are at most flagged, all at k = 64, S1, and the row 64/S1/`traeff` is now
    "flagged" (at most). No solve is low-clock.
  - **Released per-solve setups** (16): clock-free, 5 ok, 1 at most flagged and 10 unresolved (5.6–188 %; the
    unresolved sections are 0.04–0.70 s long). Conditional, the three at k = 64 S1 (6.25 %, 11.34 % and 18.79 %) are
    unresolved too.
  - **Released setup (a)** (8): clock-free, 6 ok and 2 unresolved (k = 64 S5, 9.4 %; k = 128 S5, 16.0 %).
    Conditional, all 8 are ok.
  - **Released clock:** setup (a) at k = 256 and 320 is low-clock (210 MHz) only under the conditional tier. Clock-free,
    the low-clock rule is undecided for 6 setup (a) sections (k = 64 S1, 128 S5, 160 S1, 160 S5, 256 S1, 320 S1) and for
    2 per-solve setups (k = 256, 320).
  - **Our setups:** the 6 setup (a) sections of 1.05–2.03 s (k = 160 `mg64_orig`; k = 256 `mg64_*`; k = 320, all
    three paths) have no saved clock series. The low-clock rule is undecidable for them.
  - **Released native runs N** (29 sections):
    - solves: clock-free 7 ok and 6 at most flagged (≤ 4.30 %), none unresolved; the low-clock rule is undecided for
      the solves of iterations 2–4 at k = 64 (1.03–2.90 s), and "not low" for the other 10;
    - design steps (0.016–0.12 s): all 13 unresolved;
    - plan mean: conditional only at k = 128 (≤ 0.035 %). At k = 64 and 160 the records refute a constant offset, and
      only the job-window means (0.035 % and 0.0029 %) are available.
  - **Released record runs R** (instrumented): solves 6 ok, 18 at most flagged and 4 unresolved; design steps all 28
    unresolved; conditional plan mean ≤ 0.91 %.
  - **Our loops L** (same clock): the plan's mean is ≤ 0.039 % in all 168 sections. In the strict bound, the solves
    give 24 ok and 60 at most flagged (≤ 2.94 %), and the design steps give 20 ok, 16 at most flagged and 48 unresolved
    (≤ 8.16 %; all at k = 64). No section is low-clock.
- *Endpoints.* P4, P5 and P11 use solve and Krylov-step times only, and every one of those sections is ok or at most
  flagged under the decisive measure. Every prediction keeps its outcome.
  - Setup times and design-loop times enter no prediction. Where they are unresolved, the report says that the 5 %
    rule is undecided at the counter's 5-s resolution.
  - The plan's repeat for a low-clock or excluded section was not made: the runs are complete, and the operator's note
    of 19:00 forbids repeating them.
- `gates.json` → G6 now names the native runs N at k = 64, 128 and 160 as the source of the released native loop
  times. The report had already used all three N runs.
- Superseded in part by D34–D37 (fourth check). The endpoint statement above holds for whole solves, not for Krylov
  steps (D34). The record-run solves include 4 unresolved ones (D35). The R design steps' conditional plan mean, and
  with it "≤ 0.91 % in all jobs", are dropped (D36).

**D32. k = 256 and 320: accuracy labels and input sources.**
- At k = 256 and 320 neither path has an independent residual (K2 spilled at k = 256, D22), and no released
  continuation completed there. The native-stop time ratios (89.5 and 95.5) were labelled "at unequal accuracy",
  which turned missing evidence into a result. They are now labelled "accuracy relationship unresolved: no independent
  residual for traeff or mg64_rep" (`predictions.json` → P5, `descriptive_G2_not_evaluated`).
- Input sources:
  - At k = 256 our drivers read the load, supports and `KE0` from the dumps of the invalid `R_k256`, which equal the
    plan's dump-free references (D28).
  - At k = 320 our drivers used the formula rebuild (`out/T_S1_k320_*.json`, `system.source`), because there was no
    record run at k = 320.
  - The released fixed-state runs at S1 build their own system at every k and read no input file (`-m fixed -s 1`).
  - The report had attributed both grids' inputs to `R_k256`; it now gives these sources.

**D33. `R_k256`: wall cap qualified, iteration 3 a diagnostic.**
- The record driver copies the whole displacement vector to the host inside the design loop
  (`released/t28_driver.c:339`, `target update from(U[:ndof])`, then the U dumps). At k = 256 that is above the
  256 MiB chunk limit of plan 6 (D27).
- These copies lie outside the timed intervals but count toward the process wall time. The driver recorded
  11.3 s, 22.6 s and 9.1 s of dump time in iterations 1–3 (`scratch/R_k256/meta.txt`, `dump_s_this_iter`).
- So `R_k256`'s wall cap (class 6) is a result of the transfer method as run, as for `H_S1_k256` (D27). The same holds
  for what followed from it under plan 7: no R, R′ or N at k ≥ 256, and no S5 state at k = 256. Whether the chunked
  protocol would have changed the outcome is not known.
- The released solve of iteration 3 (1000 steps, recursive residual 19.06) comes from this invalid, interrupted job.
  It is a diagnostic of that run under the transfer method used, not a design-loop result. `R_k256` stays out of
  `design_workload.csv` and out of G4.
- `capacity.json` → `traeff/design_loop_R.note` states this.
- The files as they were before these corrections are kept in `fix_r3/*_before_r3.*`.

## Corrections after the fourth check (assembly only; no GPU job, no measured value changed)

These follow the operator's note of 2026-11-24 03:25. The frozen plan is unchanged. Every prediction and every gate
keeps its outcome. `fix_r4/check_r4_diff.json` compares the outputs before and after, CPU only, and finds only the
changes listed here. The files as they were before are kept in `fix_r4/*_before_r4.*`.

**D34. The released 1.73 % bound covers whole fixed-state solves only, not Krylov steps.**
- The strict bound divides the foreign use of the covering counter intervals by the section's duration. For a whole
  solve that gives ≤ 1.73 % (released, clock-free) and ≤ 2.04 % (ours). It says nothing about a part of the solve: the
  same foreign use could all fall into one step.
- `g4check.step_level()` divides the same integral by the median Krylov step. For the released runs this is the
  clock-free job-window integral; for ours, the largest integral over the intervals covering one timed solve. The
  values are in `comparison.csv` (`g4_step_strict_bound_pct`, `g4_step_strict_activity`) and in `gates.json` → G4 →
  `krylov_step_level`.
  - Released 64/S1: 1.26 %·s over the 88.2 ms median step, about 14.3 %.
  - The 5 % rule is unresolved at step duration for 15 of the 32 timed rows: all eight at k = 64, and the k = 128 rows
    except `traeff` 128/S1 (2.94 %). At k ≥ 160 every step-level bound is ≤ 2.99 %.
- P4a, P4b and P11 carry these values (`g4_step_level`). Their step-time ratios are reported as measured, with the
  interference rule unresolved at k = 64 and 128, not as cleared.
  - P11: `mg64_rep` 42.1 % and `mg64_orig` 15.2 % at k = 64; 20.0 % and 12.4 % at k = 128; ≤ 0.80 % at k = 160–320.
  - No outcome changes: the plan's G4 excludes a section only for a mean above 5 %, and an unresolved bound is not
    such a mean. P4 stays inconclusive by G5. P11 stays "supports", qualified as above.
- P5 uses whole solve times; `predictions.json` → P5 → `g4_scope` states that its bounds are not step bounds.

**D35. The design-loop solves do not all clear exclusion.**
- The report said that the loop solves were not excludable and named only the N and L runs.
- At whole-solve resolution the native runs N (clock-free: 7 ok, 6 at most flagged) and our loops L (24 ok, 60 at most
  flagged) clear the 5 % threshold.
- The instrumented record runs R give 6 ok, 18 at most flagged and 4 unresolved. The unresolved ones are the k = 64
  solves of iterations 1–4: bounds 161.1, 121.2, 135.2 and 51.6 %, for solves of 0.76–2.37 s in a 1420-s job window.
  For them the 5 % rule is undecided.
- `gates.json` → G4 → `design_loop_solves` states this.

**D36. No constant-offset readings for the record runs' design steps.**
- D31 placed each design step of R at [solve return, solve return + design_s] on the WSL clock. The record driver
  times it differently (`released/t28_driver.c:338-379`). Its timer starts after the untimed FP64 compliance transfer
  and the level-2 dumps, and in iterations 1–4 it sums pieces separated by the dc dumps. The evaluated window is
  therefore not the timed interval. For N, which makes no dumps, the timer starts at the solve's return.
- `g4check.py` now gives R's 28 design steps no conditional tier (`conditional: null`, with `conditional_dropped` stating
  why). `design_workload.csv` leaves `g4_design_mean_foreign_pct` empty for R.
- The clock-free strict bound needs only the duration and the job window, so it stays: all 28 R design steps remain
  unresolved. The job-window means stay (0.086 %, 0.033 % and 0.0030 % at k = 64, 128 and 160).
- The R conditional summary now covers 31 sections (setup and solves), with a largest plan mean of 0.65 %. The
  "≤ 0.91 %" of D31 came from an R design-step reading (k = 64, iteration 11) and is withdrawn. Wherever the plan mean
  can be located, it is now ≤ 0.65 %.

**D37. Limitation: activity coverage of processes created after the sampler started.**
- The G4 activity sampler (`drivers/t28lib.py`, `_PS_ACT`) is one `Get-Counter -Continuous` call with the wildcard path
  `\GPU Engine(*engtype_3D)\Utilization Percentage`. It resolves the matching process instances once, when it starts.
- Every activity value and bound in T28 therefore covers the process instances enumerated at the sampler's start. The
  records do not establish coverage of a process created later in a job, nor do they show that such a process
  interfered.
- `g4_activity.json` → `limitation` and `gates.json` → G4 → `limitation` state this. The memory guards are not
  affected: `t12guard` issues a fresh counter query per sample.
