# T27 deviations from the frozen analysis plan

The plan file (`ANALYSIS_PLAN.md`) is unchanged. Each item below gives what was done differently or what the plan
left open, the reason, and which endpoints it affects. Endpoints affected by D1–D7 are not changed numerically;
D8 adds exploratory runs that are reported separately and never enter a confirmatory endpoint.

## D1. Protective pool cap on every non-capacity process (H1–H5, V)

Every Hou-system process sets the CuPy pool limit to E_free − 1.5 GiB at start, with E_free read in the process
by `guard.effective_free_bytes()`. This is the cap formula of plan 4.6. The plan prescribes it only for admitted
runs (the capacity runs and `hou_cg32` at k = 256).

Reason: with ~7 GiB of other processes' WDDM dedicated usage on this desktop, E_free was ~16.6 GiB. The historical
E10 note reports 15.5 GiB dedicated for Hou's application at k = 256. A process that outgrows the free memory
spills silently on WDDM, which would invalidate the run with no repeat allowed. The cap turns that into an
allocation error.

Effect: the cap changes no arithmetic. It can lower a pool *reserved* peak only if it binds. Whether it bound is
checked from the records (pool reserved peak against `protective_pool_cap.pool_cap_bytes`); see REPORT.md.

## D2. One untimed warm-up application before the timed solves (H3)

Before the timed solves, every H3 process applies its operator once (Hou: one `honorAb`; ours: one FP64
application plus one preconditioner or fused-residual call). The time is recorded as `first_application_s`.

Reason: the plan excludes setup and compilation from solve time. Hou's 24 element-row kernels are compiled at
their first call, which lies outside their setup (a) as the plan defines it. At k = 256 there is only one timed
Hou solve, so without the warm-up compilation would enter it.

## D3. Pool-peak pass of our H3 paths

The plan's untimed pass "with the hook enabled" is implemented as follows.
- The pass rebuilds the setup (load, mask, operators, `GMG`, first `mg.update`) and runs the history solve,
  with the hook enabled throughout.
- The history solve's FP64 residual buffer is allocated outside the CuPy pool (`cupy.cuda.Memory`), so the pool
  peak covers the workload only.

The process-dedicated and device-wide peaks are process-life values (plan 4.4). They therefore include this
buffer (8 bytes per DOF), which is conservative for our paths in P6. For Hou the hook pass is killer + survivor +
solve.

## D4. Pool readings at hook enable/disable

The plan's hook reads the pool at every allocation. Arrays allocated before the hook was enabled are counted by
one additional reading when the hook is switched on and one when it is switched off.

Reason: an application into a preallocated buffer performs no allocation, so the hook alone would report 0.

## D5. Setup of application rows (H2)

For the application rows, setup (a)/(b) is the build of that operator:
- ours: load and mask + `Operator(...)`;
- Hou: autowrite + import + killer + survivor; (b) is killer + survivor.

The solver setup of plan 4.2, with `GMG` and the first update, is in the H3 rows.

Hou's `autowrite` contains a fixed `time.sleep(2)`. It is part of their setup (a) as released and is included.

## D6. Activity window for short timed sections (G4)

The foreign 3D-engine sampler runs at 10 s. The mean for a timed section is taken over the samples within
[start − 10 s, end + 10 s]. A process too short to receive a sample takes one synchronous sample at its end.
If no timed window holds a sample, the process-wide mean is used (`t27lib.py`, `Run.finish`).

Limitation found by the implementation check: for sections much shorter than 10 s (the application timings last
about 0.07 s; the k = 160 stencil timings had one sample each), the gate reports activity near the section, not
during it. G4 therefore cannot establish whether foreign activity overlapped a short application timing. The flags
are kept as recorded; no timing was excluded or repeated on their basis.

## D7. Hou application timing and our application timing (H2)

Both are timed on field R, without the fixed mask, as in `E10_external_hou.py`. The fixed DOFs are zeroed only in
the saved actions used for d_R and d_S.

## D9. Pinned staging buffer for device<->host transfers; one repeat of the k = 160 checker

The first k = 160 checker process (`out/H5_check_k160__attempt1.json`) met the plan's spill criterion: shared
usage grew 413 MB, against a dedicated peak of 1.5 GB with ~16 GB free.

The growth came from the driver's staging memory for pageable copies of 256 MiB chunks, which WDDM reports as
shared usage. The project README records the same false trigger. A probe showed:
- 256 MiB chunks: +512 MB;
- 32 MiB chunks: creeping up to ~220 MB;
- one reused 16 MiB pinned buffer: a constant +16 MB, with bit-identical round trips.

The transfers now go through that one pinned buffer. The checker at k = 160 was run once more
(`out/H5_check_k160.json`, growth 27 MB, not spilled). Every number in it is identical to attempt 1. A k = 32
recheck also gave identical numbers (`logs/V_transfer_recheck/`).

The plan allows a repeat only for spill caused by foreign activity. This repeat is a deviation. The trigger was
transfer staging, not VRAM oversubscription, and the checker's values are deterministic FP64 values, identical in
both runs. Under plan Section 1, however, every endpoint that the deviation affects is exploratory. At k = 160
these are the checker-derived endpoints:
- d_R and d_S of the three FP32 actions (the G2 action gate and P7 at k = 160);
- the reference's independent residual, which names the reference;
- the independent true residuals at the native stop (P1 at k = 160; the independent confirmation behind class 9
  of our k = 160 solves);
- the compliance and energy errors.

They are listed as exploratory in `hou_matched.csv` (`endpoint_status`, `note`) and `predictions.json`
(`exploratory_values`), and no confirmatory decision uses them. Endpoints at k = 160 that do not come from the
checker stay confirmatory:
- the native timing records and the solve classes, including the class-5 breakdown of `mgir_orig`;
- G2's system identity, recorded by the H2 Hou process;
- the in-process FP64 checkpoints of the continuation (H4), which decide P2 at k = 160.

(An earlier version of this report treated the replacement checker's values as confirmatory. That was wrong and
is corrected here.)

## D10. Queue halted by the operator to apply D9

When the k = 160 spill flag appeared, the queue was stopped to fix the transfers before k = 256 (larger
transfers). The stop caught two processes in flight.

1. `H2_apply_k256_hou_cg32` was stopped mid-run and wrote no record. It ran again in full after the restart.
   This is not a repeat of a measurement.
2. The shell loop had already started the capacity block. Its first process, `C1_mg_ir_k384`, had evaluated
   admission: W = 17.18 GiB, E_free = 16.55 GiB, refused (`logs/C1_mg_ir_k384.log`). It was stopped while
   writing its record. The queue counted that evaluation as C1's first admission evaluation (session 1), and the
   record is reconstructed from the log as `out/C1_mg_ir_k384__eval0.json`.

   Correction after the second implementation check: C1's process started (07:57:26) while
   `H2_apply_k256_hou_cg32` (started 07:57:06) was still in flight, against the one-GPU-job rule. Its E_free
   reading therefore measured availability beside another GPU process. It is not an isolated reading and counts as
   no evidence (`capacity.json` → `admission_evaluations`, `isolated: false`). C1's class 2 rests on the
   session-2 and session-3 refusals (E_free 17,833,230,336 and 17,832,361,984 B, against W + 1.5 GiB =
   20,059,347,391 B). See D19.

The restarted queue is session 2.

## D8. Exploratory capacity runs outside the admission rule (used)

On this desktop, E_free was 16.55–17.20 GiB in every capacity evaluation. Other processes held ~7 GiB of WDDM
dedicated memory, the desktop compositor about 4.3 GB of it. That gave these confirmatory outcomes:
- the plan's anchors C1 (`mg_ir`, k = 384) and C2 (`mg32_rec`, k = 384) were refused at every allowed
  evaluation (W + 1.5 GiB = 18.68 GiB);
- C3 (`mg64`, k = 320) failed allocation under the cap E_free − 1.5 GiB;
- the plan's ladder rules then left no T27 capacity measurement.

To give the authors the isolated full-run peaks and the k = 384 recursive-control outcome that the task asks for,
the same driver was run with `--explore` (`x_queue.py capacity`) for C1, C2, C3 and C6a:
- the admission decision is recorded but not applied;
- the pool cap is cudaMemGetInfo free − 1.5 GiB;
- the records are `out/X_*.json`, with `exploratory.plan_admission_would_admit`.

These runs are listed only under `capacity.json` → `exploratory` and in REPORT.md 3.2. They do not change any
confirmatory class, lower bound, prediction outcome or the paper-wide maximum. The next-size W values computed
from them (`exploratory_next_size_predictions`) are predictions from exploratory anchors and are labelled so.

What these runs changed:
- They bypassed admission.
- They raised the pool cap above the plan's E_free − 1.5 GiB. For `mg64` at k = 320 this came after its
  confirmatory allocation failure under the plan's cap.
- Their bytes-per-element figures (pool used and pool reserved peak divided by the element count) are two
  allocator quantities from one grid per configuration. They describe those runs.

What they do not establish:
- a hardware requirement at 10⁹ elements;
- any replacement for the historical 146 GB extrapolation of the historical single-load configuration.

A next-size W + margin above the observed E_free (16.55–17.20 GiB) means "not admissible on this desktop under
the plan's rule". It does not mean "larger than the card". For `mg64` at k = 352 the predicted 21.65 GiB lies
between the two.

## D11. Exploratory k = 160 application-timing diagnostic

The confirmatory k = 160 application times of our operators were slower per element than at k = 256, and
flagged for 1–5 % foreign activity. A diagnostic repeated the four k = 160 application timings in fresh
processes (`out/X_H2_apply_k160_*.json`).

`hrun.py` H2 was given GPU state readings (`nvidia-smi` clocks and P-state) immediately before and after the
timing. These readings are outside the timed interval, and the change affects only the X runs. Every
confirmatory H2 run had finished before the edit.

The diagnostic reproduced the slow stencil times, and in those later processes the SM clock read 390–555 MHz
(P5). The clock was not read in the confirmatory k = 160 processes. Low clocks are therefore a plausible
explanation of the confirmatory k = 160 timings, not a measured condition of them. The diagnostic does not
replace the confirmatory values. (Correction after the second check: the k = 160 timings are no longer singled out as
descriptive. P4 and P5a use the same records under the same standard, and G4's limitation (D6) applies to every
application timing at every k. P4's 15.2 lies in the D12 gap.)

## D12. P4 decision rule gap

Plan 5.2 defines P4 support as ≥ 100 at all three k, contradiction as < 10 at any k, and inconclusive as a G2
failure. It leaves a value between 10 and 100 undefined. The k = 160 ratio of 15.2 falls in that gap, so P4 is
reported as "inconclusive (a k between the support and contradiction thresholds)", with all three values. The
cause of the low k = 160 value is not established (D6, D11), so P4 is unresolved.

## D13. G2 evaluated after the solves

The plan (Section 6, H2) evaluates G2 right after the four application processes. The queue evaluated the action
part (d_R) in the H5 checker, after the H3 solves and the H4 continuation. The system-identity part was recorded
inside the H2 Hou process, but it was read only at the end.

The values do not depend on the order: d_R uses only the saved H2 actions. But the gate did not stand before the
solves, as planned; it confirms system identity retrospectively. At k = 160, d_R is also exploratory (D9).

## D14. The H3 memory peaks retain workspaces of two builds

The implementation check found that the H3 process peaks do not measure a single solve.
- Our paths (`hrun.py`, `h3_ours`): the Krylov-step timing wrapper (`EvM`, and for mgir `EvR`) holds the first
  build's preconditioner, that is the CastPrecond buffers and the whole multigrid hierarchy, or the fused
  residual. Setting `o = None` before the untimed history pass therefore did not release them. The history pass
  then built a second hierarchy while the first was still alive, and it added the 8-bytes-per-DOF history
  buffer. The pool peaks of that pass include the live first build, because the hook reads the pool when it is
  enabled.
- Hou (`h3_hou`): the driver kept a survivor index (`r.t11`) through the timed solves and the hook pass, while their
  CG (`CG.py`, `t11 = survivor(struct)`) built its own. Their released `main.py` holds only `tunion`.

The recorded values are process-life peaks as defined in plan 4.4, but they belong to a workload with a second
build. Subtracting the history buffer does not recover a single-solve value. P6 is therefore inconclusive. It is
no longer reported as a contradiction. The single-build, single-solve peaks were re-measured as exploratory runs
(D17).

## D15. Whole-vector host copies in the Hou application process

To capture the system of their released `FE.FE` for G2, the H2 Hou process copied the whole load vector and the
whole initial iterate to the host (`cp.asnumpy`). At k = 256 each vector is 406.6 MB, more than the plan's
256 MiB transfer limit (plan Section 6). The process peak of `H2_apply_k256_hou_cg32` therefore includes staging
outside the protocol, and it is not quoted as Hou's application-alone peak. At k = 80 and 160 the copies were
within the limit. An in-protocol exploratory rerun at k = 256 (D17) captures only the 12 fixed indices and the 8
nonzero load entries and tests the zero iterate on the device. It then computes d_R immediately afterwards.

## D16. Hou setup timings include work outside the plan's boundaries

Hou's setup (a) in H2 and H3 was timed around `hou_load_modules`, which first deletes and copies the source tree
into `_work/hou_k{k}/`. Setup (b) was timed around a `gc.collect()` that precedes killer + survivor. Neither value
is a timing of only the operations of plan 4.2. Neither enters a ratio: P3a uses our `mg64_rep` setup (b), whose
boundary is the planned one. The confirmatory values stay in `hou_matched.csv` with a note. Boundary-correct
values come from the exploratory setup processes (D17).

## D17. Exploratory re-measurements after the implementation check (`drivers/xfix.py`, `drivers/x2_queue.py`)

These runs are labelled EXPLORATORY in their records (`out/X_SETUP_*`, `X_APPLY_*`, `X_G2_*`, `X_IRHIST_*`,
`X_MEM_*`). They are collected in `hou_exploratory.csv` and `residual_histories/X_*_mgir_orig.csv`. They change no
confirmatory class, prediction outcome or lower bound. `hrun.py` stays as it ran for the confirmatory records;
the corrected procedures are in `xfix.py`. Each run used one process at a time, with the same guards, samplers
and protective cap (D1).
- `MEM` (k = 80, 160, 256; `hou_cg32`, `mg64_orig`, `mg64_rep`, `mgir_rep`): one build and one solve from zero in
  a fresh process, with the hook on throughout.
  - There is no second build, no retained index and no history buffer.
  - Hou runs their released `FE.FE` unmodified, and the caller holds only `struct`, `U` and `tunion`, as in their
    `main.py`.
  - The process stays alive 4 s after the solve, so that the 1 s WDDM sampler sees the retained pool.
- `SETUP` (k = 80, 160, 256): Hou setup (a) = autowrite + import + killer + survivor, after the staging; setup
  (b) = killer + survivor, after the earlier indices were dropped and collected. The first version also timed the
  allocation and filling of the FP32 density grid (`cp.ones`) inside (a). It was rerun with the grid created
  before the timer (`x2_queue.py setup`, D19); the first records are kept as `out/X_SETUP_k*__v1_density_in_a.json`.
- `APPLY` and `G2` (k = 256): the Hou application process with in-protocol transfers (D15), then d_R against the
  confirmatory FP64 reference action.
- `IRHIST` (k = 160, 256): the `mgir_orig` history solve up to its breakdown. The failing confirmatory processes
  had exited before their history pass (`hrun.py`, `h3_ours`), so their trajectories were missing. The run
  records:
  - the FP64 true residual (node_hoist) at every outer residual evaluation, including rejected corrections and
    their undo evaluations;
  - the in-solver residual;
  - the inner FP32 iterations, counted as operator calls between evaluations.

Before these runs, the drivers were smoke-tested at k = 16 (records in `logs/X_smoke/`, never reported). The
smoke script's clean-up pattern also matched the four `out/X_H2_apply_k160_*.json` diagnostic records (D11) and
moved them into `logs/X_smoke/`. They were moved back at once, unmodified.

## D18. Scope of the true-residual histories

- Hou continuation (H4): the FP64 true residual was evaluated only at the plan's checkpoints: every 50 iterations
  at k = 80 and 160, every 250 at k = 256, plus the iterate where the native test first holds. These are 201,
  201 and 41 checkpoints. No checkpoint reached 10⁻⁵, which is the planned P2 endpoint. The iterates between
  checkpoints were not tested. The report says "at no checkpoint", not "never".
- `mgir_orig` at k = 160 and 256: the confirmatory class-5 exceptions are recorded, but not the trajectories that
  led to them (see D17, `IRHIST`).

## D19. Corrections after the second implementation check

- **C1 session-1 evaluation (procedure).** This evaluation ran beside the in-flight k = 256 Hou application
  process (D10), so it was not one GPU job at a time. It is kept in the log but carries no evidential weight.
  - Because the queue counted it, C1 received no session-4 evaluation, which the plan would otherwise have
    allowed (two re-evaluations after a valid first one).
  - In session 4, C2 and C6a, which have the same W (same workspace class, plan 4.6), read E_free =
    18,466,537,472 B (17.20 GiB). That is below the 20,059,347,391 B (18.68 GiB) that admission needs. A
    session-4 C1 evaluation would therefore very probably also have been refused, but it was not made. The queue
    has ended, and the plan allows no evaluation after that.
- **SETUP rerun (exploratory).** See D17. The new records are flagged by G4 (1.6–3.1 % mean foreign activity) and
  not spilled. The rerun changes no confirmatory value. P3a uses our setup (b).
- **Classes at k = 160.** `hou_matched.csv` no longer assigns class 9 to `mg64_orig`, `mg64_rep` and `mgir_rep` at
  k = 160. Class 9 needs an independent confirmation, and the only one is exploratory (D9). Those rows carry a blank
  `outcome_class` and `exploratory_class` = 9.
- **P7 rule.** Plan 5.2 requires support "at every k". With k = 160 exploratory, P7 is inconclusive (unresolved),
  not supported. P1 ("every k with a completed solve") and P3a ("every k with both solves"; a failed gate makes a
  k inconclusive) keep their two-grid decisions under their own wording.
- **Spilled historical records.** In `capacity.json` the two class-4 historical entries (E12, E23) keep their
  classification, but no measurement is exported from them.
- **Text patches.** The report and this file were edited by `logs/fix2_report_patch.py` and
  `logs/fix2_dev_patch.py` (text only, no data).

## D20. Corrections after the third check (operator note of 2026-11-23 on T27)

The measurements stand and none was repeated. The analysis and the report were corrected as follows.
- **Gate handling of P4 and P5a.** At k = 160 the G2 action gate (d_R) rests on the exploratory replacement checker
  (D9). P5a now applies the system-identity gate as P3a does, so its k = 160 ratio is exploratory. Its criterion
  covers every k, so P5a is inconclusive (unresolved). P4 likewise treats its k = 160 ratio as exploratory and is
  inconclusive (unresolved).
- **P1 denominator.** Plan 5.2 counts every k with a completed Hou solve, and k = 160 has one. With no confirmatory
  independent residual at k = 160, P1 is inconclusive (unresolved). The exploratory k = 160 value is listed beside
  it. (This reverses the reading of P1 in D19.)
- **Historical capacity records.** A historical optimization gets class 9 (or class 8 for the recursive control)
  only if it meets T27's class rule (plan 4.8). None does: there is no independent check of the final state, and
  spill was sampled every 10 design iterations, not continuously (plan 4.4); E32 `mg64` k = 320 also saved no
  design. These records are labelled historical completions (`capacity.json` → `historical[*].T27_class_rule`).
  They still carry the paper-wide maximum (`paper_wide_maximum.carried_by`).
- **Wording.** The report no longer explains the exploratory Hou setup differences as run-to-run variation. G4
  activity during those setups is unknown, because each process has one process-wide sample. Hou's solve-start
  overhead is named for what it contains. P5b is stated by its ratios and the ±15 % band.
- **One new exploratory run: original-stencil IR single-build peak at k = 80.** It ran in one short guarded process
  (`drivers/xmem_p6.py`, `out/X_MEM_k80_mgir_orig.json`), with the same procedure as the other `X_MEM` runs and
  under the authors' GPU-memory rule of 2026-11-23:
  - admission: the predicted peak (the measured `mgir_rep` peak at k = 80) plus 1.5 GiB was checked against
    cudaMemGetInfo free, and `guard.require_budget`'s answer and the other processes' usage were recorded;
  - the pool cap was set to cudaMemGetInfo free − 1.5 GiB;
  - a stop-on-spill watcher was active. It was tested on CPU first (`logs/test_xmem_p6_watcher.py`, `.out`).
    That watcher had a gap and the run was repeated (D21).

  No other GPU job ran during it. At k = 160 and 256 no such peak exists, because the path breaks down (class 5);
  these are marked missing. The run is exploratory and changes no decision (P6 stays inconclusive).
- **Exploratory capacity admissions.** For each exploratory capacity record, `capacity.json` → `exploratory` now
  lists the plan's admission answer (recorded, not applied), the cudaMemGetInfo free reading and the pool cap used.
  The confirmatory classes and bounds stay as the frozen rule left them.
- **Text patch.** The outputs were regenerated by `drivers/collect.py` and `drivers/predictions.py`. The previous
  outputs are kept in `logs/fix3_prev/`.

## D21. Corrections after the fourth check

The confirmatory measurements stand, and none was repeated. One exploratory run was repeated because its live guard
had a gap.
- **Live spill stop of `drivers/xmem_p6.py`.** The WDDM sampler (`t27lib.WddmSampler`) writes a process's
  dedicated and shared counters for the same timestamp as separate lines. The earlier watcher marked a timestamp
  checked when the dedicated line arrived, so a shared value arriving later at that timestamp went unchecked. A
  CPU-only test by the checker passed 300 MiB of growth this way. Changes:
  - The sampler now publishes a timestamp only when a line of a later timestamp arrives (or the stream ends).
    Get-Counter writes all counters of one timestamp before the next, so a published sample is complete. The
    sampler also records which of this process's counters each sample held. `series` and `report()` are unchanged,
    so the other drivers' post-hoc memory values are unaffected.
  - The watcher reads published samples only. A sample counts as checked only when it holds this process's
    dedicated and shared counters. A sample without them, or an empty shared baseline at arming, stops the job at
    once with coverage lost (exit 5). Shared growth above 256 MiB stops it refused for memory (exit 4). Either way
    the record is written first and is not a result.
  - After the job, and before the watcher disarms, it checks every remaining published sample and requires one
    taken after the job ended (15 s limit, otherwise coverage lost).

  CPU-only test: `logs/test_xmem_p6_watcher_v2.py`, output `logs/test_xmem_p6_watcher_v2.out`. The seven cases are
  the checker's case, a missing shared counter, an unrelated process only, an empty baseline, no spill, a spill in
  the post-job sample and no post-job sample. They give exit 4, 5, 5, 5, 0, 4 and 5, as expected.

  The k = 80 `mgir_orig` memory run was then repeated once. It took 28 s, and no other GPU job was active. The
  watcher checked 15 samples, the last taken after the job ended, with 12.6 MB of shared growth. Coverage held from
  its first sampler baseline onward, not over the whole process (D23).
  The pool used, pool reserved and process-dedicated peaks equal the first run's to the byte. The first record is
  kept as `out/X_MEM_k80_mgir_orig__v1_watcher_gap.json` and is not used. `collect.py` and `predictions.py` treat a
  run under the 2026-11-23 rule as missing unless its watcher reports coverage.
- **Pool peaks without a measurement.** A record whose pool hook was never enabled holds zero calls and zero
  readings, and these are now exported as missing, not 0 (`collect.pool_peaks`). The records concerned are:
  - the reference solves (H1);
  - the two original-stencil IR breakdowns at k = 160 and 256, which exit before the instrumented pass;
  - the Hou setup re-measurements (X_SETUP);
  - the refused confirmatory capacity records.
- **Reference resolution.** `hou_matched.csv` gains `compliance_at_reference_resolution`,
  `energy_at_reference_resolution` and `reference_resolution_limit`, copied from the checker (plan: an error below
  10 × the reference residual is "at the resolution of the reference"). The report's solve table marks the five
  flagged compliance errors.
- **Exploratory designs.** The report now counts four saved exploratory designs: three at k = 384 and one at
  k = 320.
- **Outputs** were regenerated by `drivers/collect.py` and `drivers/predictions.py`. The previous outputs and
  drivers are kept in `logs/fix4_prev/`.

## D22. Corrections after the fifth check

The confirmatory measurements stand, and none was repeated. The exploratory k = 80 `mgir_orig` memory run was
repeated once more because its live guard had two faults.
- **Baseline.** `guard.SpillWatch` (`src/voxfem/guard.py`) fills an absent process or counter with 0. The
  launcher passed that start sample to the watcher, which refused only a missing value (None), so an empty counter
  response armed the watcher with a zero baseline. `guard.py` is unchanged, because the other drivers' records
  depend on it. Instead:
  - `StopOnSpill` takes its baseline from its own first published WDDM sample, which must hold this process's
    dedicated and shared counters;
  - otherwise arming fails closed (coverage lost, exit 5) before the job starts;
  - the launcher's arming step, `xmem_p6.arm_watch`, records `guard.SpillWatch`'s start sample for information
    only.
- **Continuity.** The live loop did not test the spacing or age of samples. It now requires:
  - at most 3 s between consecutive checked samples, the baseline included;
  - a readable timestamp that increases from sample to sample;
  - while armed, including the post-job check, a last checked sample at most 5 s old.

  Any violation stops the job at once with coverage lost (exit 5). The limits rest on a CPU-only probe with no
  CUDA context (`logs/sampler_spacing_probe.py`, `.out`): 37 samples spaced 1.004–1.156 s (minimum and maximum
  of the 36 intervals; the median printed by the probe is dropped, D23). A spill
  lasting less than one sampling interval is below the sampler's resolution. Every checked sample's timestamp,
  shared usage and dedicated usage is now kept in `spill_watcher.checked_samples_ts_shared_dedicated`, together
  with the largest gap.
- **CPU-only test.** `logs/test_xmem_p6_watcher_v3.py`, output `logs/test_xmem_p6_watcher_v3.out`. The eleven
  cases and their exit codes:
  - the checker's case, an empty counter response through the production `guard.SpillWatch` and `arm_watch`: 5;
  - no published sample: 5;
  - a baseline without a shared counter: 5;
  - the checker's replay, a 29 s gap followed by a valid post-job sample: 5;
  - no new sample for more than 5 s: 5;
  - the D21 case: 4;
  - a missing shared counter: 5;
  - an unrelated process only: 5;
  - no spill: 0, covered;
  - a spill in the post-job sample: 4;
  - no post-job sample: 5.

  The v2 test exercises the earlier constructor and is kept as a record only.
- **Repeated run.** It took 29 s, and no other GPU job was active. The admission and pool cap are as before:
  predicted peak 576,897,024 B + 1.5 GiB against 24,152,899,584 B driver free, `guard.require_budget` also
  admitting, and a cap of 22,542,286,848 B. Other processes held 6,296,915,968 B.
  - Watcher: baseline 77,594,624 B; 14 samples checked after it, the last taken after the job ended; largest gap
    1.069 s; shared growth 12,582,912 B. Coverage held from this baseline onward, not over the whole process: the
    baseline sample already held 77,594,624 B shared (D23).
  - Peaks: pool used 163,632,640 B, pool reserved 178,890,752 B and process-dedicated 576,897,024 B, equal to both
    earlier runs. The device-wide peak minus baseline is 576,716,800 B, as in the D21 run; the first run measured
    622,854,144 B (D23). The iterations (18) and the in-solver residual are unchanged.
  - The D21 record is kept as `out/X_MEM_k80_mgir_orig__v2_no_gap_check.json` and is not used.
- **Outputs.** `collect.py` and `predictions.py` were rerun. Only the `mgir_orig` k = 80 row of
  `hou_exploratory.csv` changed, in its device-wide columns, solve time and note, together with one note in
  `predictions.json`. The previous outputs and drivers are kept in `logs/fix5_prev/`.

## D23. Reporting corrections after the sixth check (operator note of 2026-11-23 15:25)

No measurement was repeated or added, and the plan is unchanged. No class, prediction outcome, gate, capacity entry
or confirmatory value changed. Five reporting points were corrected.
1. **The three k = 80 `mgir_orig` memory runs.** Earlier text said they gave the same peaks, the device-wide one
   included. They agree in pool used (163,632,640 B), pool reserved (178,890,752 B) and process-dedicated
   (576,897,024 B) peaks. Their device-wide peaks above baseline, as measured, are 622,854,144 B in the first run
   (`out/X_MEM_k80_mgir_orig__v1_watcher_gap.json`) and 576,716,800 B in the later two
   (`out/X_MEM_k80_mgir_orig__v2_no_gap_check.json`, `out/X_MEM_k80_mgir_orig.json`). The device-wide quantity
   includes other processes' activity. `collect.py` now computes this comparison from the three records and writes
   it into the row's note in `hou_exploratory.csv`.
2. **Coverage of that run.** The watcher's coverage runs from its first sampler baseline onward, not over the whole
   process. That baseline sample already held 77,594,624 B of this process's shared usage. Whatever arose before it
   was not watched; the shared growth of 12,582,912 B is measured from it.
3. **Hou setup columns of `hou_matched.csv`.** The six `hou_cg32` rows (application and state solve, three k) had
   setup timers whose boundaries differ from the frozen endpoint (D16). Their setup columns are now marked
   exploratory:
   - `setup_status` = exploratory, and `endpoint_status` ends in "setup columns exploratory";
   - `setup_a_s` and `setup_b_s` hold the separately labelled exploratory measurement with the plan's boundaries
     (`out/X_SETUP_k{80,160,256}.json`, named in `setup_source_file`; the same values as in `hou_exploratory.csv`);
   - the values recorded in these processes are kept in `setup_a_recorded_offboundary_s` and
     `setup_b_recorded_offboundary_s`.

   Our rows carry `setup_status` = confirmatory. No prediction used a Hou setup time (P3a uses our setup (b)).
4. **P5b.** The k = 160 `mg64` ratio, 0.953, is now listed under `exploratory_values`. Its action check comes from
   the exploratory replacement checker (D9), outside the system-identity gate, which P5b now applies as P3a and P5a
   do. P5b stays a contradiction, decided by the k = 80 IR ratio, 0.103. The confirmatory `mg64` ratios, 0.991
   (k = 80) and 1.005 (k = 256), lie inside the ±15 % band.
5. **Sampler spacing.** `logs/sampler_spacing_probe.py` printed `sorted(d)[len(d)//2]` as the median of 36 intervals.
   That is the upper of the two middle intervals, not their mean. The intervals were not saved, so the median is
   dropped. The minimum and maximum, 1.004 and 1.156 s, are kept; the watcher's limits, 3 s and 5 s, lie above the maximum. The
   probe script and its output are left as run.

`collect.py` and `predictions.py` were rerun (`logs/collect_fix6.out`, `logs/predictions_fix6.out`; their console
output equals that of the fifth fix). `capacity.json` and the gates are unchanged. The previous outputs and drivers
are kept in `logs/fix6_prev/`.
