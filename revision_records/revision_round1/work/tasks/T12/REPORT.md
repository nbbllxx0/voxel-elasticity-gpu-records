# T12: feasibility gate for Träff et al.'s TopOpt-in-OpenMP-GPU on the RTX 4090

**Outcome: gate passed, results admissible for R1.1.** The gate is set from the four technical conditions of the acceptance statement, and all four are met (`gate.json` → `acceptance`). Since revision 4.3 the gate needs two separate conditions, and both hold:
- `numerical_result_admitted`: the fixed-state comparison, taken from the saved records together with their own guard evidence;
- `guard_current_passed`: the tests of the current guard revision, 4.3.

The four technical conditions:
- GPU execution is confirmed.
- The guards cover the WSL GPU process (`acceptance.guards_cover_process`, revision 4.3). This takes the saved records' six conditions (`guards.conditions`: admission before launch, a live stop of the job inside WSL whose checks span the whole job, an exit status that counts, and the passed tests of guard version 3) and also the passed tests of the current revision 4.3. Post-run detection alone does not count.
- Both codes describe the same free-DOF system.
- All 10 GPU actions of `harness_i5_v2` agree with an FP64 reference to 3.47e-8 or better, and all 20 of the two admitted repeat runs to 3.67e-8 or better (target 1e-5).

**Admissibility.** The operator note of 2026-11-23 on T12 settles it. The Ubuntu-24.04 distribution, build-essential, libsuitesparse-dev and nvhpc-26-11 recorded in `probe_provenance.log` (07:04–07:07) were installed by the run's operator with the authors' permission. That permission is the authors' update of 2026-11-23, which replaces decision (4).

**T28.** `gate.json` → `t28_cleared` is computed by `t12_gate.decide`. Like `gate_passed`, it needs both `numerical_result_admitted` and `guard_current_passed`. Both hold, so T28 is cleared. `guard_current_passed` means that `guards.guard_version_4_tests` passes at revision 4.3, and that covers:
- 51 no-GPU unit cases (`guard_selftest_v4.json`): the 38 earlier cases rerun on the 4.3 code (the gate's source check adapted), plus 13 for the four points of the operator note of 14:20, four of which are negative controls on the 4.2 code;
- the real-WSL kill test of revision 4.3, no GPU work (`kill_selftest_v4_3.json`);
- the real-counter runs of revisions 4.0–4.2, read with the 4.3 validator. No GPU work was done for 4.3.

T28 must first re-run the guard self-tests (`test_t12guard_v4.py`, `test_t12kill_v4_3.py`) before its first GPU job, and stop if one fails. Then:
- Run every WSL job through `t12mon.py` revision 4.3 and every CuPy process through `t12guard.cupy_guard` revision 4.3. Both take `gpu_job.lock`.
- End a CuPy process's watch with `t12guard.close_watch(stream, stop, t_end)` before `stream.stop()`, then compute its coverage with `stop.coverage(t_end)`.
- Accept a job only when its status is `completed` and its coverage is `covered`. For a WSL job, also require that `t12mon.validate` gives `clean=true` with `carrier_is_watched=true`.

**The fixed-state comparison is stated as admitted only when both conditions hold.** `gate.json` → `fixed_state_comparison_admitted` and `consequence_for_R1_1` follow `t12_gate.decide`, which needs both `numerical_result_admitted` and `guard_current_passed`. The installed toolchain's admissibility is a separate flag (`admissible_for_R1_1`, `acceptance.toolchain_admissible_for_R1_1`).

**What the gate supports.** A same-card, fixed-state comparison on the same free-DOF system. In the released code's native cantilever, every state solve from design iteration 5 on stops at the 1000-step cap. That is a result about the released code under this toolchain, not a gate failure. Matched design-workload performance is left to T28.

Every number below is in `gate.json`, which `t12_gate.py` builds from the run records. No acceptance flag is typed in. The earlier measurements are kept (`native_patched_v1`, `harness_i5_v2`, the dumps, the positive control).

**New this round (checker's review of guard revision 4.2; operator note of 2026-11-23 14:20): guard revision 4.3.** Only the four points of the last check were fixed, each with a test that needs no GPU work, and there was no new GPU work. The numerical results are unchanged: every block of `gate.json` except `gate_basis`, `t28`, `guards` and `acceptance` is identical to `gate_v8.json` (the 4.2 gate), and so are the numbers in `acceptance`. See "Guard revision 4.3" below. The 4.2 files are kept: `t12guard_v4_2.py`, `t12mon_v4_2.py`, `t12_gate_v4_2.py`, `killtree_v4_2.sh`, `probe_free_v4_2.sh` (unchanged), `test_t12guard_v4_2.py` → `guard_selftest_v4_2.json`, `gate_v8.json` and `REPORT_v8.md`. The edits are in `patch_guard_v4_3.py`, `patch_mon_v4_3.py` and `patch_gate_v4_3.py`; `killtree.sh` was rewritten.

**Previous round (checker's review of guard revision 4.1): guard revision 4.2.** Only the guard, its tests and the gate changed. The numerical results, the harness runs and the comparison stay as accepted and were not rerun; `acceptance`, `system_match`, `action_check`, `fp64_residual_check` and `released_run_to_run` are identical to `gate_v7.json`. The only new GPU work is three short guarded checks: `runs/v4_2_carrier_job`, `runs/v4_2_trigger_job` and `runs/v4_2_cupy_job`. See "Guard revision 4.2" below.

**Previous round (checker's review of guard version 4.0): guard revision 4.1**, kept below as "Guard revision 4.1". **Before that (operator note of 2026-11-23 13:00): guard version 4.0**, kept below as "Guard version 4".

**Previous round (third review), because the checker's six points needed new code and runs:**
- guard version 3 (`t12guard.py`, `t12mon.py`), with a no-GPU logic self-test (`test_t12guard.py` → `guard_selftest.json`, 11 cases);
- two live-stop tests: `livestop_v3_trigger` (test trigger) and `livestop_v3_sampler_lost` (the sampler ended mid-job);
- two synthetic exit-status runs with no GPU work: `status_v3_exit3` and `status_v3_oom_message`;
- a contention test (`contention_test.py` → `contention/`);
- a rerun of `t12_compare.py` under `cupy_guard` version 3.

The repeat harness runs were not rerun: their records show a baseline before launch, checks spanning each job, and exit 0 (see Guards).

All jobs ran one at a time. Superseded outputs are kept:
- `gate_v1`–`v4.json`, `REPORT_v1`–`v4.md`;
- `compare_v2.json`/`.log`, `compare_v3.json`/`.log`;
- `t12_compare_v2.py`, `t12_compare_v3.py`, `t12_gate_v4.py`, `t12guard_v2.py`, `t12mon_v2.py`;
- from the guard revision 4.1 round: `gate_v7.json`, `REPORT_v7.md`, `t12guard_v4_1.py`, `t12mon_v4_1.py`, `t12_gate_v4_1.py`, `killtree_v4_1.sh`, `probe_free_v4_1.sh`, `test_t12guard_v4_1.py` → `guard_selftest_v4_1.json` (30 cases). The 4.2 edits are in `patch_guard_v4_2.py`, `patch_mon_v4_2.py` and `patch_gate_v4_2.py`;
- from the guard version 4.0 round: `gate_v6.json`, `REPORT_v6.md`, `t12mon_v4_0.py`, `test_t12guard_v4_0.py` → `guard_selftest_v4_0.json` (23 cases). `t12guard.py` was revised in place; its 4.0 `on_sample` is reproduced in `negative_control_v4_0.py`;
- from the third-review round: `gate_v5.json`, `REPORT_v5.md`, `t12_gate_v5.py`, `t12guard_v3.py`, `t12mon_v3.py`, `test_t12guard_v3.py` → `guard_selftest_v3.json`. The comparison and the version 3 runs were made with these.

The gate edits of the third-review round are in `patch_gate_v5.py` and `patch_gate_v5b.py`.

## Guard revision 4.3 (checker's review of revision 4.2; operator note of 2026-11-23 14:20)
The checker's sixth review accepted the numerical results and found four points in the guard and the gate. Each is fixed below and tested on the case the checker built. Where the fault can be shown, a negative control on the 4.2 code (`t12mon_v4_2.py`, `t12guard_v4_2.py`, `killtree_v4_2.sh`) shows it.

The tests:
- `test_t12guard_v4.py` → `guard_selftest_v4.json`: 51 cases, all passed (`test_v4_3_run.log`). These are the 38 earlier cases rerun on the 4.3 code (one of them, the gate's source check, adapted to `decide`) and 13 new ones. The fakes now follow the 4.3 contracts: a sample is checked before it is published, and the fake `killtree.sh` prints `recorded:` and `alive:` lines.
- `test_t12kill_v4_3.py` → `kill_selftest_v4_3.json`: real WSL processes, `sleep` in place of any GPU command, passed (`kill_selftest_v4_3.log`).

No GPU work was done for 4.3.

1. **The WSL stop confirms an end only after every recorded PID, parent and children, is checked again and gone** (`killtree.sh`, `t12mon.end_wsl_tree`).
   - `killtree.sh` now records every PID of the tree that any call has seen, with its start time, in `<pidfile>.tree`. A PID counts as the recorded process only while its start time still matches, so a reused PID is never killed.
   - Every call checks all recorded PIDs again, so a child that survived an earlier call is found after its parent has ended. Each process is stopped (SIGSTOP) before its children are listed.
   - The last two output lines are `recorded:` and `alive:`.
   - `end_wsl_tree` confirms an end only when three things hold:
     - the job's `wsl.exe` has exited;
     - the last reply has code 0, 2, 3 or 4;
     - that reply checked every PID that any reply of this stop recorded, and found none alive.
   - A reply without those lines, or one that leaves a recorded PID unchecked or alive, never confirms. At the 20 s deadline the stop is recorded as unconfirmed, with the survivors and the unchecked PIDs named.
   - **Unit tests, the checker's in-memory case.** The first reply reports child 101 surviving (code 5); the second says the parent 100 is not running (code 4, the 4.2 format, which does not check the child).
     - 4.3: unconfirmed, with `unchecked=[100, 101]`.
     - A second reply that lists only the parent: unconfirmed, `unchecked=[101]`.
     - A second reply with the child still alive: unconfirmed, `survivors=[101]`.
     - A reply without `recorded:`/`alive:` lines: unconfirmed.
     - Only a second reply that checks 100 and 101 and finds both gone confirms.
     - Negative control, 4.2's `end_wsl_tree` on the checker's two replies: confirmed. This is the fault.
   - **Real WSL processes (B).** The job is a bash with two children started with `setsid`, so they are in their own session. The first `killtree.sh` call has its `kill` disabled through `BASH_ENV`, so it records three PIDs, all alive (code 5). Then the parent is killed from outside, and the next call finds the pidfile's PID not running.
     - 4.3: the second reply (code 4) checked all three recorded PIDs again, killed the two orphaned children and found none alive. The end was confirmed, and `pgrep` found no survivor 1 s later.
     - 4.2 control (`killtree_v4_2.sh`, 4.2's `end_wsl_tree`): the second reply was `pid … not running` (code 4) and the end was confirmed, but both children were still running 1 s later (`B_negative_control_4_2.survivors_1s_after_stop`). **The checker's fault is reproduced with real processes.**
   - **Real WSL processes (C).** A survivor is never killed (every call has `kill` disabled): codes 5, unconfirmed, all three recorded PIDs named as survivors.
   - **Real WSL processes (A).** The 4.2 startup schedule on the 4.3 code: job and probe each stopped 0–2 s after the start. All 18 launches ended and all 18 were confirmed.
   - Earlier runs of this test are kept in `killtest/`:
     - `kill_selftest_v4_3_without_setsid.*`: the children ran in their parent's session. WSL ended them together with the parent, so the 4.2 control did not show the fault; B was then changed to use `setsid`.
     - `kill_selftest_v4_3_run2.*`: B with a test deadline of 8 s. The injected no-kill first call and the outside kill took longer than that. 4.3 made one attempt and recorded the end as unconfirmed, with both children alive. That is the fail-closed outcome, not a false confirmation.
     - `kill_selftest_v4_3_run3.*`: 8 s, passed.
     - The kept file uses the production deadline of 20 s.
2. **Coverage needs the carrier in both PID lists** (`t12mon.pid_lists`, `validate`, `record_coverage`, `admitted_live`).
   - A monitor version 4 record must hold both the launcher's list (`watched_carrier_pids`) and the live stop's list (`live_stop.watched_pids`). Both must be non-empty and equal, and the carrier must be in both.
   - Otherwise `carrier_is_watched=false` and `clean=false`, `record_coverage` gives `covered=false`, and `admitted_live` does not count the job as covered. The reason is named. 4.2 took the launcher's list alone whenever it was present.
   - Earlier records (versions 2 and 3) have only the live stop's list, which is used as before (`pid_lists.agree=null`).
   - **Test on in-memory copies of the real `v4_2_carrier_job` record.**
     - The original is clean and covered, and the lists agree.
     - Seven changes each give clean=false, carrier_is_watched=false and covered=false under both `record_coverage` and `admitted_live`:
       - the live stop's list without the carrier (the checker's case);
       - the live stop's list empty;
       - the live stop's list missing;
       - the launcher's list without the carrier;
       - the launcher's list missing;
       - the live stop's list with an extra PID;
       - both lists equal but without the carrier.
     - Negative control, 4.2's `validate` on the checker's case: clean=true, carrier_is_watched=true.
   - The saved records read with the 4.3 validator: `v4_2_carrier_job` and `v4_1_carrier_job` keep clean=true and covered. The repeat harness runs `harness_i5_v3` and `harness_i5_v4` (version 2) keep clean=true and covered.
   - One value in `gate.json` changed. `v4_short_job` (memfree, no growing VM process, so no carrier in either list) is now `covered=false`. Its samples still span the job (`samples_span_job=true`). 4.2 had already credited it for sampling cadence and launch order only, and the gate's cadence check now reads `samples_span_job` and `pid_lists_agree`. Every other change to `guards` adds the fields `pid_lists`, `samples_span_job`, `pid_lists_agree` and `carrier_in_both_lists`.
3. **No sample is skipped at disarm** (`t12guard.WddmStream.run`, `close_watch`, `t12mon.run`).
   - The sampler now hands every sample to the stop rules before it appends it to `samples`, so a published sample has been checked.
   - `close_watch(stream, stop, t_end)` disarms only after a published sample whose Get-Counter call started at or after the job's end. That sample was checked by the armed stop, or it fired the stop.
   - `t12mon.run` closes the watch this way and records `closing`. If the closing sample fires the stop, the launcher waits for the kill record.
   - If no such sample arrives within 8 s, the stop is disarmed with no closing sample and the coverage stays open (`covered=false`).
   - **Test on the checker's schedule.** The real `WddmStream.run` parser is fed through a queue. The job ends, and its next sample, called after the end, carries 1 GiB of shared growth. The check of that sample is delayed by 0.6 s, which models a thread switch between publication and check.
     - 4.3: the stop fired on it (`shared_growth`), and `close_watch` records the closing sample as checked and as the one that fired.
     - Negative control, 4.2's sampler and 4.2's closing loop: the launcher disarmed on publication and the spill was skipped (`fired=null`, closing sample not checked). This is the fault.
   - **Launcher-level test** (`t12mon.run` with a fake stream whose only sample after the exit has a spill and a delayed check): status `refused_memory_spill`, `closing.closing_sample_fired_stop=true`.
   - CuPy callers end with `close_watch` from now on (`cupy_guard` docstring). `v4_2_cupy_job.py` and `t12_compare.py` used the 4.2 closing; their records are kept as they are.
4. **The gate keeps the numerical result and the current guard apart** (`t12_gate.decide`, `build`, `guard_current_tests`).
   - `numerical_result_admitted` covers GPU execution, the same free-DOF system and the action differences, all from the saved records, together with those records' own guard evidence (`guards.conditions`).
   - `guard_current_passed` is `guards.guard_version_4_tests.passed` at the current revision. It requires the unit-test record to be of revision 4.3 with all cases passed, and the 4.3 kill test to pass.
   - `guards_cover_process` (`acceptance` and `guards.covers_process`) needs the records' evidence and the current revision's tests. `technical_acceptance_met`, `gate_passed`, `fixed_state_comparison_admitted`, `consequence_for_R1_1` and `t28_cleared` all need both conditions. 4.2 computed `guards_cover_process` from tests up to version 3, and used 4.2 only for T28.
   - **Tests.**
     - `decide` on every combination of the inputs.
     - `t12_gate.build` with an injected failing 4.3 unit-test record, and separately with a failing kill-test record. In both cases: numerical_result_admitted=true; guard_current_passed, gate_passed, technical_acceptance_met, guards_cover_process, fixed_state_comparison_admitted and t28_cleared all false; the consequence begins "Not admitted".
     - With passing records, everything is true.
   - **Rebuilt `gate.json`:** numerical_result_admitted=true, guard_current_passed=true (revision 4.3), gate_passed=true, t28_cleared=true. All 16 parts of `guards.guard_version_4_tests` hold.

**Notes for T28** (outside the four points; T28 re-runs the guard self-tests before its first GPU job and stops if one fails):
- An unconfirmed stop (`linux_process_ended_confirmed=false`) still ends with the launcher releasing `gpu_job.lock`. The next launch's exclusivity check refuses only while a survivor holds more than 200 MiB on the WSL VM. T28 should treat an unconfirmed stop as the end of its GPU work until the survivor is accounted for.
- `killtree.sh` finds descendants by parent PID from the recorded PIDs. A process that has already left the tree before the first call (double-forked and reparented to init) is not found. Tracking by session or cgroup would cover that.
- In test C, killing the job's Windows `wsl.exe` at the deadline also ended the Linux processes of its session; only the `setsid` child outlived it. The 4.2 startup model assumed that killing `wsl.exe` never reaches Linux. 4.3 does not rely on either behaviour.
- The real-counter GPU runs credited in the gate are those of revisions 4.0–4.2. In particular, `v4_2_trigger_job`'s kill was confirmed under the 4.2 rule; its one `killtree.sh` reply (`killed: 437 438`, code 0) means that the call found every PID it had listed gone.

## Guard revision 4.2 (checker's review of revision 4.1; `gate.json` → `guards.guard_version_4_tests`)
The checker found four faults in revision 4.1. Each is fixed below. The no-GPU tests were `test_t12guard_v4.py` → `guard_selftest_v4.json` at revision 4.2: 38 cases, all passed (`test_v4_2_run.log`; kept as `test_t12guard_v4_2.py` → `guard_selftest_v4_2.json`). The kill test with real WSL processes and no GPU work is `test_t12kill_v4_2.py` → `kill_selftest_v4_2.json`.

1. **A WSL job could start after the stop fired** (`t12guard.LiveStop._fire`, `t12mon.run`).
   - In 4.1, `_fire` set `stop.fired` under the stop's own lock. The launcher checked it under `gate`, so a stop could be set between that check and `start_job`.
   - In 4.2, `LiveStop` takes the launcher's lock (`fire_lock=gate`, re-entrant). The stop decision, the launcher's check of the stop, and the start of the probe or the job now hold the same lock.
   - So a stop either comes before the check, which then refuses the launch, or after the start, and the action then finds the job registered and kills it.
   - Test with the checker's schedule: the stop is triggered from another thread after the check and before the job's process exists.
     - In 4.2 the trigger could not complete before the job was created. At creation `fired` was unset; the stop then fired and the job was killed (`stopped_coverage_lost`, end confirmed).
     - Negative control, the same schedule on 4.1's stop decision (`LiveStopNoSharedLock`): the trigger completed first, and the job was created with the stop already set. This is the checker's fault.
   - Race test (16 runs, stop fired from another thread at 0–75 ms): 14 runs were refused before launch and 2 were launched and then killed. No job was created with the stop set, and none was left running.
   - The 4.1 race test could not see this fault: its hook fired only after the mock job had started. The new hook fires before the job is created.
2. **The stop could miss the Linux process during startup** (`t12mon.end_wsl_tree`, `killtree.sh`, `probe_free.sh`, `launch.sh`).
   - Both launchers are now started with the `t12job` marker as an argument (`bash launch.sh t12job`, `bash probe_free.sh <tag> t12job`). The marker is in the PID's command line before the PID is recorded, and it stays there through the `exec`.
   - `killtree.sh` now tells five outcomes apart by exit code:
     - 2: no PID recorded yet;
     - 3: the PID runs but is not a T12 job;
     - 4: the PID is not running;
     - 5: part of the tree survived the kill;
     - 0: the tree was killed and none of it survives.
   - The probe and the job are now ended by one routine. It retries `killtree.sh` until the process's `wsl.exe` has exited; `wsl.exe` exits with its Linux command, which confirms the end.
   - `wsl.exe` is killed only after 20 s without that confirmation, recorded as `linux_process_ended_confirmed=false`. In 4.1, the probe was killed once and then only its `wsl.exe`, and the job's retries stopped on code 3.
   - Unit tests use a startup model: the PID is recorded only 0.8 s after the start, and killing the Windows `wsl.exe` does not end the Linux process. For both the probe and the job, a stop at 0.1 s gives `killtree.sh` codes 2, 2, 0, the end confirmed, and the probe's `wsl.exe` not killed.
   - **Real WSL processes** (`kill_selftest_v4_2.json`, `sleep` in place of the GPU command): the job and the probe were each stopped at 0, 0.05, 0.1, 0.2, 0.3, 0.5, 0.8, 1.2 and 2.0 s after the start. Under 4.2, all 18 launches ended and all 18 were confirmed ended, 1 s after the kill.
   - Control, 4.1's scripts and kill logic on the same schedule: all 18 launches also ended. `killtree.sh` returned 0 at the first attempt in all 36 launches. Its own `wsl.exe` call took longer than the launchers' startup window, so it always found a marked PID.
   - **The 4.1 fault is therefore shown only by the startup model, not reproduced with real processes on this machine.** Revision 4.2 confirms each end instead of assuming it.
   - **Real GPU stop** (`runs/v4_2_trigger_job`, the 4 GiB `spill_probe 4` with a 2 GiB dedicated-growth test trigger): the stop fired 1.7 s after launch and the job was killed inside WSL (`killed: 437 438`, one attempt). Its end was confirmed by its `wsl.exe` exiting 1.91 s after launch (exit 9). The VM was kept, and no `spill_probe` process remained.
3. **The validator could credit an unwatched VM process** (`t12mon.validate`, `admitted_live`).
   - `validate` now takes as carrier only a growing VM process whose PID the live stop watched, and records `vm_carrier_pid`, `watched_pids` and `carrier_is_watched`.
   - With no watched carrier, the record is not monitored and not clean, with the reason named. `admitted_live` counts the job as covered only when `carrier_is_watched` is true.
   - Records with no live stop (the post-run monitor of version 1) give `carrier_is_watched=null` ("not checkable") and keep their earlier flags, as the operator notes allow.
   - Test on an in-memory copy of the real `v4_1_carrier_job` record: the original gives carrier 3440, watched, clean=true and covered. With the carrier PID changed to an unwatched one (the checker's case) it gives clean=false, monitored=false and covered=false. With an unwatched VM process growing three times as much, the watched 3440 is still the carrier.
   - **Real run** (`runs/v4_2_carrier_job`, `spill_probe 4` under 4.2):
     - Predicted 4718592000 B; cudaMemGetInfo inside WSL 24104665088 B free; guard.require_budget ok; other processes 6152855552 B, not counted.
     - Sequence armed → admission probe → job; carrier 3440 watched.
     - Dedicated growth 4697804800 B (0.999 of the nvidia-smi device growth); shared growth 77594624 B; monitored and clean.
     - 16 checked samples, largest gap 1.46 s, covered, exit 0, `completed`.
4. **A CuPy sample without the process, after the context, did not stop the job** (`LiveStop.on_sample`, `cupy_guard`, `WddmStream`).
   - The sampler now records when each Get-Counter call started (`t_call_start`); the counter instances are listed after that moment.
   - `cupy_guard` calls `opened()` once the CUDA context exists, after `memGetInfo` returns. From then on, a sample whose call started after the context and lacks the process, or has a missing counter, stops the job at once and gives covered=false.
   - Only a sample whose call started before the context, and which therefore cannot contain the process, is left unchecked (`call_started_before_context`). The 10 s wait of 4.1 remains only as a backstop when no such sample arrives.
   - Tests:
     - the checker's case (an unrelated PID only, after the context) stops at once with 0 checked samples and covered=false;
     - a missing counter after the context stops;
     - a sample called before the context and arriving after it is left unchecked, and coverage runs from the first appearance;
     - in `cupy_guard`, a sample after the context without the process ends the process through the stop (exit 5) before admission, `require_budget`, the pool cap or any allocation.
   - **Real counters** (`runs/v4_2_cupy_job`, a 1 GiB array for about 6 s):
     - None of the 9 samples whose call started after the context was left unchecked, and all 9 contain the process with both counters. It first appeared 1.155 s after its context, before its first allocation.
     - Covered, largest gap 1.29 s, no stop.
     - Dedicated peak 1428320256 B against a prediction of 1610612736 B; shared growth 77594624 B over a zero baseline.
     - Its stderr (`runs_v4_2_cupy_job.log`) holds one Get-Counter message, "The data in one of the performance counter samples is not valid", from the project's own counter reader (`voxfem.guard.gpu_process_memory`) during the pre-launch checks. Both answers were complete (exclusivity: no python process or VM holding GPU memory; guard.require_budget ok, for information).

`guard_version_4_tests.parts` lists each check separately, and `t28_cleared` requires all of them: the unit-test groups, revision 4.2 of the test file, the 4.0 negative control, the refusal, the cadence run, the 4.2 carrier run, the 4.2 stop run, the real-WSL kill test and the 4.2 CuPy run.

## Guard revision 4.1 (checker's review of version 4.0; `gate.json` → `guards.guard_version_4_tests`)
The checker found five problems in version 4.0. Each is fixed or corrected below. The no-GPU tests are `test_t12guard_v4.py` → `guard_selftest_v4.json`: 30 cases, all passed. `negative_control_v4_0.py` → `negative_control_v4_0.json` runs the checker's two fault scenarios on the version 4.0 code paths, with no GPU work. Both faults reproduce there, and the 4.1 code does not show them.

1. **A CuPy sample without the process counted as checked** (`t12guard.LiveStop.on_sample`, `cupy_guard`).
   - Version 4.0 counted samples without the process as checked, with zero usage put in, until the process first appeared, for up to 10 s after it opened the device. The first allocation came before that appearance.
   - Negative control: an unrelated-PID sample after `opened()` gave 1 checked sample, no stop, and covered=true from arming.
   - In revision 4.1, a sample without the watched process is never a checked sample, before or after the device is opened. No zero is put in for it; it is counted under `samples_not_checked_process_not_yet_seen`.
   - `cupy_guard` now creates the CUDA context without allocating (`Device.use`, `memGetInfo`) and waits until the process appears with both counters. Only then does it run the admission, `guard.require_budget` and the pool cap and return for allocation. A process that does not appear within 10 s is refused before admission.
   - A CuPy process's coverage runs from its first appearance (`LiveStop.coverage`).
   - Tests: the checker's case now gives 0 checked samples, covered=false and no zero usage; coverage starts at the first appearance; absence after it stops the job; a process never seen is stopped and refused with nothing admitted or allocated; the event order is arm → context → seen → `memGetInfo` → `require_budget` → `set_limit`, with no allocation in the guard.
   - **Real counters** (`runs/v4_1_cupy_job`, a 1 GiB array for about 6 s):
     - The process appeared in the first sample after its context, 1.17 s later, with 352473088 B dedicated (the context only). That was before its first allocation, and no sample was left unchecked.
     - All 8 checked samples contain it with both counters. Covered, largest gap 1.30 s, no stop.
     - Dedicated peak 1428320256 B against a prediction of 1610612736 B.
     - Shared growth was 77594624 B over a zero baseline. The baseline is zero because the process is absent at arming, so its context's own shared usage counts against the 256 MiB limit.
2. **A WSL job could launch after the stop had fired** (`t12mon.py`).
   - The stop action and the launcher's start of the admission probe and of the job now hold one lock. The probe and the job start only when the stop has not fired.
   - A stop that fires before the probe or the launch refuses the launch.
   - A stop during the admission probe kills the probe's process tree inside WSL (`probe_free.sh` records its PID; `killtree.sh`). The launcher then refuses.
   - The launcher records its steps in program order (`sequence`), because clock ties can hide the order.
   - Negative control on `t12mon_v4_0.py`: a stop during the exclusivity recheck, after the last check of `stop.fired`, let the job launch, and the kill action found "no job to kill".
   - Tests:
     - a stop during the probe kills the probe and refuses;
     - a stop in the recheck refuses;
     - a stop after the last pre-launch step refuses;
     - a stop inside the launch section kills the started job;
     - a stop after launch kills the job;
     - in a 16-run race with the stop fired from another thread at 0–75 ms, 14 runs were refused before launch and 2 were launched and then killed, and no run left a job running after the stop.
3. **Overcounted samples** (`t12_gate.presence_retro`).
   - In-job samples now run from launch to exit: 76 in `harness_i5_v3` and 75 in `harness_i5_v4`, with 2 and 3 samples after the exit counted separately. The 78 reported before included those post-exit samples.
   - vmwp's dedicated and shared values are both positive in every in-job sample (76 of 76, 75 of 75).
4. **Key presence is not evidence.** The version 3 sampler and the comparison writer filled missing values with zero, so the gate no longer counts keys. It counts samples whose stored dedicated and shared values are both strictly positive, which proves each counter row was present. The comparison's 61 of 61 checked samples meet that test (minimum 354570240 B dedicated, 77594624 B shared). The repeat runs meet it as in point 3.
5. **The clearance overstated the WSL check.**
   - `v4_short_job` is now credited for sampling cadence and launch order only. Its record has no carrier (monitored=false, spilled=null, clean=false), because memfree has no growth to follow.
   - Carrier following under the revised launcher is shown by a new 4 GiB WSL job (`runs/v4_1_carrier_job`, `spill_probe 4`):
     - Predicted 4718592000 B, from `livestop_test_4g`'s measured growth for the same command. cudaMemGetInfo inside WSL gave 24104665088 B free; guard.require_budget ok; other processes 6181175296 B, not counted.
     - Sequence: armed → admission probe → job.
     - vmwp dedicated growth 4697804800 B, 0.999 of the nvidia-smi device growth; shared growth 77594624 B; monitored and clean.
     - 15 checked samples, largest gap 1.41 s, covered, exit 0, `completed`, no stop.
   - `guard_version_4_tests.parts` lists each real-counter check separately, with the unit tests, the 4.1 revision of the test file and the negative control. `t28_cleared` requires all of them.

## Guard version 4 (operator note of 2026-11-23 13:00)
Version 4.0 as reported in the previous round, with the corrections of revision 4.1 marked. Its tests were `test_t12guard_v4_0.py` → `guard_selftest_v4_0.json` (23 cases, all passed).

1. **Coverage fails closed** (`t12guard.LiveStop`, `WddmStream`).
   - An empty or missing baseline refuses the launch, and so does a baseline without the watched PID or with a missing counter.
   - The sampler now records which of the two counters each PID actually had in a sample.
   - A sample counts as checked only when every watched PID is in it with both counters.
   - A sample without the watched PID, with a missing counter, or with no rows at all stops the job at once (`stopped_coverage_lost`). `coverage()` then gives `covered=false` even when the timing is otherwise complete.
   - Tested: 4 baseline refusals and 4 in-job stops (only an unrelated PID, a missing shared counter, a missing dedicated counter, an empty sample), each with `covered=false`. Also a good series that is covered with no stop, and the sampler's parsing of a missing counter value.
   - The WSL launcher now watches only the vmwp PIDs that the baseline holds with both counters. Version 3 also watched vmmem, which has no GPU counters.
   - **CuPy process.** Before it opens the device it has no counter instance. Its absence is accepted until it first appears, which must happen within 10 s of opening; after that, any absence stops it. An empty sample stops it at any time. *(Corrected in 4.1: 4.0 counted those absent samples as checked; see revision 4.1, point 1.)*
2. **No GPU work outside the watch.**
   - `cupy_guard` now runs in this order: lock, exclusivity check, sampler, baseline, armed stop. Only then does it create the CUDA context and call cudaMemGetInfo and `guard.require_budget` (in the watched process), set the pool cap, and wait until the process appears in the counters.
   - `t12mon.py` arms the vmwp watch before its admission probe (memfree inside WSL). It computes `guard.require_budget`'s rule from that probe and the WDDM counters, with no CUDA context on Windows. If the stop fires during the probe, the launch is refused.
   - Tested with recorded event orders (4 cases), plus two short real-counter runs:
     - `runs/v4_refused_admission`: a 30000 MiB prediction, refused at admission; armed before the probe, vmwp 3440 in the baseline with both counters, nothing launched.
     - `runs/v4_short_job`: memfree followed by 8 s of sleep; completed and covered, 13 checked samples, largest gap 1.44 s, no stop. *(4.1: this shows cadence and launch order only. Its record has no carrier (monitored=false, clean=false); carrier following is shown by `v4_1_carrier_job`.)*
   - The only GPU work in these two runs is memfree's CUDA context inside WSL, made under the watch.
   - **Earlier records** keep their results with the coverage they have, which starts at arming (`guards.coverage_of_earlier_records`). In version 3 the launchers' own probe and context work came before arming.
     - All 61 checked samples of the comparison have strictly positive dedicated and shared values, so both counter rows were present. *(4.1: the earlier statement rested on key presence, which the zero-filling writer cannot establish.)*
     - In `harness_i5_v3` and `_v4`, vmwp's dedicated and shared values are both positive in all 76 and 75 in-job samples (launch to exit), with 2 and 3 more samples after the exit. *(4.1: the earlier count of 78 included those post-exit samples.)*
3. **Lock.** `gpu_job.lock` is created with O_CREAT|O_EXCL. Any existing lock, stale or not, refuses the launch with its owner and PID named and is never removed automatically.
   - Tested: a second taker is refused; a lock left by a dead PID is refused and kept; of 16 threads racing for the lock, exactly one gets it; the source of `acquire` has no remove call.
4. **Gate statement.** The comparison is stated as admitted only when technical acceptance holds. Tested: `consequence_for_r11(False, …)` gives "Not admitted", and both the flag and the text are tied to `tech_ok`.

## Toolchain
- **Compiler used:** `nvc 26.11-0 64-bit target on x86-64 Linux -tp alderlake` (NVIDIA HPC SDK 26.11, bundled CUDA 13.4), with `-mp=gpu -gpu=cc89`. The released code was tuned with HPC SDK 22.5 (its README: nvc 22.5, CUDA 11.1, SuiteSparse 5.1.2, A100). Sources: `probe_runtime.log`, `gate.json` → `toolchain`.
- **CHOLMOD:** Ubuntu SuiteSparse 7.6.1 (`libcholmod.so.5`).
- **Second OpenMP runtime** (`gate.json` → `openmp_runtime`):
  - **The conflict.** Ubuntu's CHOLMOD calls GNU libgomp (`probe_gomp.log`), while nvc links NVIDIA's libnvomp. With both loaded, the binary prints "Another OpenMP runtime library has been detected" and aborts with `libgomp: TODO` (`runs/native_v1/stderr.txt`).
  - **How it was settled.** No CHOLMOD rebuild and no further installation: `env_run.sh`, sourced by every T12 run, puts the SDK's compiler library directory first in `LD_LIBRARY_PATH`. There, `libgomp.so.1 → libgomp.so → libnvomp.so`, so CHOLMOD's GOMP calls go to NVIDIA's runtime.
  - **Check.** `ldd` under `env_run.sh` lists no GNU libgomp for the released binary or the harness; without it, `/lib/x86_64-linux-gnu/libgomp.so.1` is loaded (`probe_runtime.log`). The native run's stderr is empty (0 bytes).

## Finding 1: build adaptations (`gate.json` → `build_adaptations`)
1. **Makefile** (`build/Makefile.t12`):
   - `-gpu=cc80` → `cc89`.
   - The cluster SuiteSparse 5.1.2 and OpenBLAS paths → the Ubuntu system paths.
   - `-lopenblas` → `-lblas`. This is host BLAS, used only by CHOLMOD's coarse-level factorisation.
   - All other flags as released: `-Wall -g -mp=gpu -mp=noautopar -Msafeptr -march=native -O4 -mavx -mavx2 -DDTU_HPC`. `src_TopOpt-in-OpenMP-GPU/` itself is unmodified.
2. **Runtime:** the libgomp shim above.
3. **Source:** the five `nowait` clauses are removed (`patch_nowait.diff`, `src_patched/`). They sit on the two `target enter data` directives in `gpu_definitions.c`, and on the `z = u` copy, the `invD` update-from and the `u += αp` update in `stencil_solvers.c`.
   - **Why:** under WSL2 the device reports "Concurrent Managed Memory: No" (`probe_mem.log`). With the clauses, the binary faults with *Invalid Managed Memory Access* at the launch after the first deferred kernel (`probe_bt.log`).
   - **Effect:** each of the five is followed by a `taskwait` before its result is used (`stencil_solvers.c:323` for `z` and `invD`, `:389` for `u`, and the `taskwait` after the enter-data block in `gpu_definitions.c`). Running a target task undeferred is a schedule that OpenMP allows for a `nowait` region. The patched program therefore runs one of the executions that the released program permits, without the overlap.

## Results
- **GPU execution.** One design iteration made 1378 kernel launches, all on device 0, from 36 offloaded kernels (`runs/notify_i1`, offload MANDATORY). In the native run, 6864 of 6963 nvidia-smi samples showed utilisation ≥ 50%.
- **Guards** (`gate.json` → `guards`; `t12mon.validate` and `t12mon.admitted_live` applied to every record).
  - **Carrier.** WDDM charges a WSL job to the VM worker `vmwp`. A run is clean only if `vmwp` is the carrier, at least 3 WDDM samples fall inside the job, its dedicated growth is within a factor of 2 of the nvidia-smi growth, and its shared growth stays under 256 MiB. With no carrier, the spill state is unknown.
  - **Monitor version 1** recorded every run up to `harness_i5_v2`. It took WDDM snapshots about every 2.4 s and evaluated shared growth only after the job had exited.
    - It formed no admission and could not stop a job.
    - The 22 GiB positive control shows the consequence. It was over the limit from its first in-job sample (0.41 s, shared growth 406847488 B), ran on to its normal exit at 14.235 s, and was flagged only afterwards (`guards.positive_control_timeline`).
  - **Monitor version 2** (kept as `t12mon_v2.py`, `t12guard_v2.py`; superseded by version 3 below) runs in this order:
    1. **Admission before launch.** The predicted peak plus 1.5 GB must fit in the free memory that cudaMemGetInfo reports inside WSL (`memfree/memfree`). nvidia-smi inside WSL, guard.require_budget's answer and the other processes' dedicated usage are recorded beside it.
    2. **Sampling.** A WDDM sample about every 1.3 s, each one checked by the live stop; nvidia-smi is sampled on Windows and inside WSL.
    3. **Live stop.** At the first sample where `vmwp`'s shared usage is more than 256 MiB above its start, the job's process tree inside WSL is killed (`killtree.sh`, which refuses any PID that is not a T12 job). The VM is never touched.
  - **Live-stop test** (`runs/livestop_test_4g`, `guards.live_stop_test`). The authors' rule forbids any job to use shared memory, so the stop path was driven by a test trigger on dedicated growth (> 2 GiB) on a job holding 4 GiB in dedicated memory. Shared usage was not zero: `vmwp`'s shared counter grew by 77594624 B during the job, below the 256 MiB limit. The test passed:
    - the trigger sample came 1.21 s after launch;
    - the job's tree (2 PIDs) was killed 0.373 s later, and the job exited 1.58 s after launch instead of holding for 12 s;
    - the VM PIDs were the same before and after, and `vmwp`'s dedicated usage returned to its base.

    The shared-memory trigger is the same code path (`LiveStop.on_sample`), and the 22 GiB control shows that `vmwp`'s shared counter rises with a WSL spill.
  - **Defect found and fixed (second review).** The first live-stop test (`runs/livestop_test_4g_attempt1`) saw no carrier. `Get-Counter -Continuous` resolves the counter instances once, but a WSL job's GPU instance appears under `vmwp` only when the job opens the device. The sampler now issues a fresh Get-Counter for each sample. Version 1 made one call per sample and is not affected.
  - **Guard version 3** (`t12guard.py`, `t12mon.py`; `guards.monitor_versions.3`, `guards.guard_version_3_tests`). The checker found four defects in version 2; version 3 fixes them:
    - **No baseline.** Version 2 ignored the result of `wait_first`. If no sample came before launch, the first sample after allocation became the baseline and hid the initial growth. Version 3 refuses to launch without a baseline sample at most 5 s old (`LiveStop.arm` raises `NoBaseline`).
    - **Lost sampling.** If the sampler ended mid-job, version 2 waited for the job unguarded. Version 3 stops the job at once when the sampler ends, or when no sample arrives for 5 s.
    - **Coverage.** Version 3 keeps every checked sample time. The gate requires that checks span the whole job: a baseline before launch, no gap above 5 s and a check after the exit. A few early samples no longer count (`t12mon.record_coverage`).
    - **Status.** Version 3 takes the status from the exit code and the job's output (`t12guard.job_status`). A nonzero exit is `failed_nonzero_exit`, and an out-of-memory message is `refused_allocation_failure`, never `completed`. The repeat-run gate now also requires exit 0 and status `completed`.
    - **Exclusivity.** Both launchers now take one lock file (`gpu_job.lock`, created exclusively; a lock whose holder is dead is taken over). They share one exclusivity check, `t12guard.exclusive_check`, which refuses while another python process or the WSL VM holds more than 200 MiB. The WSL launcher repeats that check immediately before launch.
      - Launchers outside this folder (the authors' project drivers) do not take the lock. Against them, the check before launch is the only protection, and a start in the gap between that check and the launch is not excluded.
  - **Tests of version 3** (all passed):
    - **Logic self-test** without a GPU: 11 cases (`guard_selftest.json`).
    - **Test-trigger stop** (`livestop_v3_trigger`): trigger 1.99 s after launch; job killed 0.905 s later; job exit at 2.892 s instead of a 12 s hold; VM survived. `vmwp` shared growth was 77594624 B, below the limit.
    - **Sampling-lost stop** (`livestop_v3_sampler_lost`): the sampler was ended 3 s after launch while the job held 4 GiB. The stop fired at 3.02 s, the job was killed 0.406 s later and exited at 3.424 s. The record correctly says the checks no longer span the job.
    - **Exit status** (synthetic jobs with no GPU work): `exit 3` was recorded as `failed_nonzero_exit`. A printed "cudaMalloc failed" with exit 0 was recorded as `refused_allocation_failure`.
    - **Contention** (`contention/contention.json`): while `contention_holder` held 4 GiB through the WSL VM:
      - `t12_compare.py` was refused at the lock before opening a CUDA context;
      - a second `t12mon.py` job was refused at the lock;
      - the exclusivity check without the lock refused because the WSL VM held 4738183168 B;
      - the holder completed with exit 0, covered and clean.
    - **Mislaunched first attempt** (`livestop_v3_trigger_attempt1`): Git Bash rewrote the job path and the job exited 127 at once. Version 3 recorded `failed_nonzero_exit`, where version 2 would have recorded `completed`.
  - **Native run** (version 1): dedicated growth 1669505024 B against 1611 MiB on nvidia-smi; shared growth 81788928 B; clean.
  - **Harness runs:**
    - `harness_i5_v2` (version 1): 1737011200 B against 1673 MiB; shared growth 106549248 B; clean.
    - `harness_i5_v3` and `harness_i5_v4` (version 2): admitted; 1713545216 B each; shared growth 81788928 B; live stop not fired; clean. Checked against version 3's criteria from their records (`guards.admission_and_live_stop_per_run`): each had a baseline sample before launch, and 78 checked samples ran from launch to the closing check after the exit (76 and 75 of them inside the job), with largest gaps of 1.36 s and 1.35 s. Each exited 0 with status `completed`. They were therefore not rerun.
- **Intervals** (`dumps_v2/meta.txt`):
  - setup 1.253 s;
  - solves 0.770, 1.094, 0.982, 2.516 and 92.28 s, which is 92–99 ms per PCG step;
  - design steps 0.020–0.027 s.
- **Same free-DOF system** (`compare.json`, `gate.json` → `system_match`).
  - **System:** 1,628,445 free DOFs and 6630 fixed.
  - **Load:** one right-hand side, the released FP32 load widened to FP64. The FP64 rebuild equals it after rounding to FP32 and differs by 4.67e-8 before rounding.
  - **Element matrix:** the released one, matched to 2.9e-16 (`ke_check.json`). Our FP64 GPU operator with it agrees with the CPU reference to ≤ 6.1e-13.
  - **Starting vectors:** matched (zero at iteration 1, then the released U of the previous iteration).
- **Action difference** (released GPU action vs independent CPU FP64 loop, free DOFs; `action_check`). Each design state has two actions, on a random test vector and on the released solution. Both now enter the maximum: before, a shared dictionary key let the second overwrite the first.
  - `harness_i5_v2`, iterations 1–5: test vector 2.56e-8, 2.55e-8, 2.52e-8, 2.54e-8, 2.53e-8; released solution 3.30e-8, 3.34e-8, 3.33e-8, 3.47e-8, 2.99e-8; at modulus contrasts 1 to 1e6.
  - The two admitted repeat runs: 20 actions, all ≤ 3.67e-8, with fixed rows equal to the input.
- **FP64 true residuals** of the free system (fixed DOFs of u set to zero). The values below are identical in the rerun comparison. Only the wall times of our own solves changed (see the third review, point 6):

  | Iteration | Released steps | Released FP32 recursive stop | Released FP64 true | Ours: steps (matched start) | Ours FP64 true | Compliance difference |
  |---|---|---|---|---|---|---|
  | 1 | 8 | 7.93e-6 | 2.33e-4 | 10 | 3.13e-6 | −3.1e-10 |
  | 2 | 11 | 4.63e-6 | 5.42e-4 | 13 | 7.23e-6 | 1.5e-7 |
  | 3 | 10 | 6.58e-6 | 3.28e-4 | 13 | 5.75e-6 | −3.8e-8 |
  | 4 | 27 | 7.79e-6 | 3.91e-4 | 17 | 7.26e-6 | −1.2e-8 |
  | 5 | 1000 (cap) | 0.92 | 0.92 | 23 | 6.11e-6 | 6.7e-3 |

  The released code meets its FP32 recursive stop of 1e-5 at iterations 1–4, but that leaves FP64 true residuals of 2.3–5.4e-4. Its printed objective is an FP32 reduction: 86.55604 at iteration 1, against an FP64 work F·U of 86.57065.

## Finding 2: the released solver stalls from design iteration 5
In the native 20-iteration run (`native_iterations.csv`, `runs/native_patched_v1`):
- iterations 1–4 meet the released stop in 8–27 steps;
- iterations 5–20 stop at the 1000-step cap, with the recursive residual rising to 1.3e3;
- the final printed objective is 13293.365234, after 1441 s.

The stall also occurs with one host thread and at `-O2` (`runs/diag_threads1_i6`, `runs/diag_O2_i6`); its cause was not isolated. This is a result about the released code on this card and toolchain, not a gate failure. At the same iteration-5 state, our path converges from the released start in 23 steps to 6.1e-6.

## Finding 3: the released code is not run-to-run reproducible
Three harness runs used the same binary, the same inputs and the same instrumentation: dumps and two extra operator actions at states 1–5 (`harness_i5_v2`, `harness_i5_v3`, `harness_i5_v4`; `gate.json` → `released_run_to_run.identical_instrumentation`).
- At iteration 1 the densities are bitwise equal in all three pairs. The returned displacements are not bitwise equal: they differ by 3.7e-8 relative on the free DOFs, so the first state solve is not bitwise reproducible.
- The densities differ from iteration 2 on. At iteration 5 the maximum differences are 4.5e-5 to 5.3e-5.
- The FP32 recursive residual of the iteration-4 solve is 7.786e-6, 7.740e-6 and 7.713e-6.
- All three iteration-5 solves stop at the 1000-step cap, at 0.9215127, 1.548609 and 0.9416427.

The earlier pair, `harness_i5` against `harness_i5_v2`, is kept but labelled as differently instrumented: `harness_i5` dumped only at states 1 and 5. That pair alone could not isolate the cause, and the identical-instrumentation runs now do. Which operation of the first solve is nondeterministic was not located.

## The checker's reviews and their closure
### First review (seven points)
| Point | Closed by | Evidence |
|---|---|---|
| 1 Different right-hand sides | one load (released FP32, widened) for every residual, compliance and solve | `compare.json`, `system_match.rhs` |
| 2 Unmatched starts at iteration 5 | our solve N starts from released U of N−1; zero start kept, labelled separately | `fp64_residual_check` |
| 3 Residual included prescribed displacements | fixed DOFs set to zero; 0.921533 projected vs 0.921512 unprojected | `fp64_residual_check.iteration_5` |
| 4 Gate could pass unmonitored; hard-coded flags; smoke test outside monitor | `t12mon.validate` (unknown when no carrier), self-test, computed flags, smoke test removed, unmonitored probes listed | `validate_selftest.log`, `t12_gate.py`, `guards.unmonitored_gpu_work` |
| 5 Fallback not reconciled, installation not attributed | settled by the operator note of 2026-11-23: installed by the run's operator with the authors' permission | `toolchain_provenance`, `admissibility_basis` |
| 6 Objective 13290 vs 13293; printed objective vs work | 6-decimal summary line 13293.365234; FP32 printed objective distinguished from FP64 F·U | `native_run`, `fp64_residual_check.iteration_1` |
| 7 "Converge" unqualified; true residual at iterations 1, 5 only | "meets the released FP32 recursive stop"; FP64 true residual at iterations 1–5 | `fp64_residual_check` |

### Second review (five points)
| Point | Closed by | Evidence |
|---|---|---|
| 1 Guard passed on post-run detection; positive control ran on after crossing the limit; T28 clearance unconditional | monitor version 2 with live stop; live-stop test passed; `covers_process` needs the live stop, the admitted repeat runs and the guarded CuPy process; `t28_cleared` computed | `guards.conditions`, `guards.live_stop_test`, `guards.positive_control_timeline`, `t28_cleared` |
| 2 Headroom of the earlier runs was a retrospective estimate | relabelled as a retrospective estimate that cannot certify admission; the new runs were admitted against cudaMemGetInfo inside WSL, with a prediction from measured workspace and guard.require_budget recorded | `gpu_memory_rule_2026_11_23.earlier_runs_not_admitted`, `.admitted_runs` |
| 3 CuPy comparison: no pool cap, checkpoint-only spill checks, result written regardless | `t12guard.cupy_guard`: admission, `set_limit`, a live WDDM stop that ends the process, all samples kept, `compare.json` written only when clean; comparison rerun. "Reproduced exactly" holds for the numerical results only, not for the solve wall times (third review, point 6) | `compare.json` → `guard`, `gpu_memory_rule_2026_11_23.cupy_comparison_process` |
| 4 Action gate dropped one action per state | key per state and action; 10 actions of `harness_i5_v2` and 20 of the repeat runs | `action_check` |
| 5 Run-to-run runs differed in instrumentation | two repeat runs with the same instrumentation as `harness_i5_v2`; the old pair labelled | `released_run_to_run`, Finding 3 |

### Third review (six points)
| Point | Closed by | Evidence |
|---|---|---|
| 1 Launch without a valid baseline; job continued after sampling stopped; a few early samples counted as coverage | no launch without a baseline sample ≤ 5 s old; stop on sampler end or 5 s without a sample; every checked sample time kept, and the gate requires checks spanning each job; sampling-lost stop tested live | `guards.guard_version_3_tests`, `guards.admission_and_live_stop_per_run.*.coverage`, `runs/livestop_v3_sampler_lost` |
| 2 Allocation failure could be labelled completed; repeat-run gate omitted the exit code | status from exit code and out-of-memory messages (`job_status`); repeat-run gate requires exit 0 and `completed`; labels tested live | `guards.guard_version_3_tests.exit_status_labels`, `gpu_memory_rule_2026_11_23.allocation_failures` |
| 3 CuPy launcher blind to a running WSL job; no reservation between check and launch | shared `exclusive_check` (python processes and the WSL VM) in both launchers; `gpu_job.lock` taken before the check; check repeated before launch; contention test; residual gap for launchers outside this folder stated | `guards.guard_version_3_tests.contention`, `guards.launch_refusal` |
| 4 A refused comparison left a stale `compare.json` eligible | invocation id in `compare_invocation.json`, `compare.json` and `compare_refused.json`; the gate accepts `compare.json` only from the last invocation, and only if it completed. Shown live: after the contention test's refused start, the gate rejected the old `compare.json` and failed (`contention/gate_after_refused_compare.json`). A later run that crashed at its end without writing `compare.json` (`compare_crashed_invocation.log`, a shadowed variable name, fixed) also left its invocation unaccepted | `comparison_reproduction`, `guards.conditions.cupy_comparison_admitted_capped_live_stopped_clean` |
| 5 Overstated memory evidence | the dedicated-trigger tests record 77594624 B of `vmwp` shared growth, below the 256 MiB limit, not zero; CuPy sample counts are stated as samples before arming (baseline) and samples checked | `guards.live_stop_test.why_a_test_trigger`, `gpu_memory_rule_2026_11_23.cupy_comparison_process.live_stop` |
| 6 "Reproduced every earlier number exactly" too broad | leaf-by-leaf comparison: against `compare_v3.json`, 654 of 663 common leaves are equal, and the 9 that differ are all wall times of our solves (iteration 1, matched start: 0.3566 s then, 0.0814 s now). Against `compare_v2.json`: 354 of 363 equal, 9 wall times differ (0.0610 s then) | `comparison_reproduction.vs_compare_v3`, `.vs_compare_v2` |

### Fourth review (guard version 4.0, five points)
| Point | Closed by | Evidence |
|---|---|---|
| 1 CuPy samples without the process counted as checked, with zero put in | never checked; context without allocation, then wait for appearance before admission and allocation; coverage from first appearance; negative control; real CuPy run | `guards.guard_version_4_tests` (unit cases, `negative_control`, `real_counter_runs.v4_1_cupy_job`) |
| 2 WSL launch after a fired stop; probe not interruptible | probe and launch serialised with the stop action; probe killable inside WSL; deterministic and 16-run race tests; negative control | `guard_selftest_v4.json`, `negative_control_v4_0.json` |
| 3 78 in-job samples overcounted | 76 and 75 from launch to exit, post-exit counted apart | `guards.coverage_of_earlier_records` |
| 4 Key presence cannot prove counter presence | strictly positive values counted instead: 61/61, 76/76, 75/75 | `guards.coverage_of_earlier_records` |
| 5 Clearance accepted a run with no carrier | `v4_short_job` credited for cadence only; new 4 GiB WSL run monitored and clean; parts listed separately | `guards.guard_version_4_tests.parts`, `runs/v4_1_carrier_job/monitor.json` |

### Fifth review (guard revision 4.1, four points)
| Point | Closed by | Evidence |
|---|---|---|
| 1 Stop set between the launcher's check and `start_job` | stop decided under the launcher's lock; deterministic test of the checker's schedule with a negative control on 4.1's decision; race test with no job created with the stop set | `guard_selftest_v4_2.json` (`t12mon_stop_between_check_and_job_creation_*`, `negative_control_4_1_*`, `t12mon_launch_race_*`) |
| 2 Linux probe or job missed during startup | marker as a launcher argument before the PID is recorded; one kill routine retrying until `wsl.exe` exits; `killtree.sh` exit codes 2–5; startup-model tests; real-WSL kill test (the 4.1 control was not reproduced with real processes); real GPU stop with the end confirmed | `guard_selftest_v4_2.json`, `kill_selftest_v4_2.json`, `runs/v4_2_trigger_job/monitor.json` |
| 3 Validator credited an unwatched VM PID | carrier must be a watched PID (`carrier_is_watched`); covered only then; the checker's in-memory case gives clean=false; 4.2 carrier run | `guard_selftest_v4_2.json` (`validate_credits_only_a_watched_carrier`), `runs/v4_2_carrier_job/monitor.json` |
| 4 CuPy sample without the process after the context skipped | strict from the CUDA context, using each Get-Counter call's start; immediate stop; real CuPy run with all 9 post-context samples checked | `guard_selftest_v4_2.json`, `runs/v4_2_cupy_job/record.json` |

### Sixth review (guard revision 4.2, four points; operator note of 2026-11-23 14:20)
| Point | Closed by | Evidence |
|---|---|---|
| 1 Stop confirmed with a surviving child unchecked | `killtree.sh` keeps every recorded PID with its start time and checks all of them on every call; confirmation only when the last reply checked every recorded PID and found none alive; the checker's in-memory case unconfirmed, 4.2 control confirmed; real WSL: orphaned `setsid` children killed and confirmed under 4.3, left running with the end confirmed under 4.2 | `guard_selftest_v4.json` (`stop_*`, `negative_control_4_2_confirms_*`), `kill_selftest_v4_3.json` (A, B, C) |
| 2 Launcher's PID list took precedence over the live stop's | both lists required, equal, carrier in both; seven in-memory changes of the real 4 GiB record all fail validity and coverage; 4.2 control clean | `guard_selftest_v4.json` (`carrier_in_both_lists_*`, `pid_list_disagreement_*`, `negative_control_4_2_credits_*`) |
| 3 Disarm between publication and check | sampler checks before publishing; `close_watch` disarms only after a checked sample called after the job's end; delayed-check spill fires under 4.3, skipped under the 4.2 control; launcher-level spill in the closing sample gives `refused_memory_spill` | `guard_selftest_v4.json` (`final_sample_*`, `negative_control_4_2_disarms_*`, `t12mon_spill_in_the_closing_sample_*`) |
| 4 Gate used version 3 tests for `guards_cover_process` | `numerical_result_admitted` and `guard_current_passed` kept apart; `decide` needs both for every admitting flag and for T28; injected failing 4.3 tests give gate_passed=false, t28_cleared=false | `guard_selftest_v4.json` (`gate_decision_*`, `gate_with_a_failed_current_guard_test_*`), `gate.json` |

## GPU-memory rule of 2026-11-23 (`gate.json` → `gpu_memory_rule_2026_11_23`)
- **Admitted runs** (versions 2 and 3): every prediction was taken from measured workspace, and every run was admitted against cudaMemGetInfo inside WSL, which reported 24104665088 B free. guard.require_budget answered ok each time; it reported 19.0–19.3 GB of effective free memory because it counts the other processes' 6.1–6.3 GB, which the authors' rule does not count.
  - `livestop_v3_trigger`, `livestop_v3_sampler_lost`, `contention_holder` (version 3): predicted 4823449600 B, from the vmwp growth observed in `livestop_test_4g`, rounded up. Observed 4697804800 B each.
  - `harness_i5_v3` and `harness_i5_v4`: predicted 1929379840 B and 1976565760 B, observed 1713545216 B; shared growth 81788928 B.
  - `livestop_test_4g`: predicted 4399824896 B, observed 4697804800 B, so the prediction was 6.8% low. It had taken the 22 GiB control's dedicated growth as the per-request overhead, but part of that control went to shared memory. Admission still held with 17796247552 B to spare.
- **CuPy comparison** (`t12_compare.py` through `t12guard.cupy_guard` version 3, accepted invocation `4ddc6807…`): at its start no python process or WSL VM held GPU memory; predicted 1543503872 B, which is twice T27's measured growth for the mg64 path at k=80; cudaMemGetInfo free 24152899584 B; admitted.
  - Pool cap 22542286848 B.
  - 63 WDDM samples about every 1.29 s: 2 before arming (the last is the baseline) and 61 checked after arming. The checks span the work, with a largest gap of 1.32 s. Maximum shared growth over the baseline was 33554432 B, and the stop did not fire.
  - In the guard version 2 run (`compare_v3.json`): 66 samples, of which the first was the baseline and 65 were checked.
  - WDDM dedicated peak 539189248 B; pool peak 117574656 B used, 125215232 B reserved; no allocation failure.
- **Earlier runs** (version 1: `native_patched_v1`, `harness_i5`, `harness_i5_v2`, `notify_i1`, the diagnostics). These have a retrospective estimate only, not an admission. The device total recorded in `probe_ubuntu.log`, minus the Windows nvidia-smi usage before launch, gives 21133–22574 MiB. Observed growth of 1611–2187 MiB stands in for a prediction.
  - No launch-time free-memory query was made inside WSL, and no guard.require_budget answer was recorded. These runs cannot be certified as admitted.
  - Their shared growth stayed under 256 MiB, and they are kept under the operator note.
  - The action check they fed is reproduced by the admitted runs.
- **Positive control** (`spill_control_22g`): it used shared memory on purpose, under version 1. It would not be admitted under the rule. It is a guard test, none of its output is a result, and no further spill control is run.
- **Allocation failures:** none in any measured or test job (`allocation_failures`, computed from every run's exit code and output).
  - The nonzero exits are: `native_v1` (libgomp abort); the three jobs ended by a live stop (exit 9 after the kill); the mislaunched `livestop_v3_trigger_attempt1` (127); and the synthetic `status_v3_exit3` (3).
  - `status_v3_oom_message` prints a cudaMalloc failure on purpose, without any GPU work.

## For R1.1
- **Available now:** a same-card, fixed-state comparison with Träff et al.'s released code on the same free-DOF system, with matched actions (≤ 3.47e-8, and ≤ 3.67e-8 in two admitted repeat runs).
- **Native stop:** an FP32 recursive residual, which leaves FP64 true residuals of 2.3–5.4e-4 where it is met.
- **In the cantilever:** the released solver stalls at the cap from design iteration 5. Its first state solve is not bitwise reproducible from run to run, even with identical instrumentation. Both are findings about the released code under nvc 26.11 on the RTX 4090.
- **Adaptations needed to run it:** cc89 with Ubuntu libraries, the libgomp shim, and removal of the `nowait` clauses.
- **Left to T28:** matched design-workload performance, under `t12mon.py` revision 4.3 and `cupy_guard` revision 4.3 (closing with `close_watch`), after re-running the guard self-tests.

This task makes no timing comparison.
