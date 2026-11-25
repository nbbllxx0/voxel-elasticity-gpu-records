# T31 deviations from ANALYSIS_PLAN.md

ANALYSIS_PLAN.md is unchanged (sha256 0a154a83...c5a697). Each entry gives the departure and its reason.

D1. Launcher wrapper `t31_launch.py`, a new file outside the plan's list of three. T30's `t30_launch.py` is copied
unchanged, but its `main()` hard-codes T30's job script and phases. The wrapper repeats `main()` for `t31_job.py`. It
imports every watch rule unchanged from `t30_launch.py`: the lock, exclusivity, the WDDM sampler, `Watch`, the final
checked sample and `kill`. The self-test (`t30_launch_selftest.py`, unchanged) tests those rules, and it passed before
the first GPU job (`out/launch_selftest.json`). The wrapper differs from T30's `main()` in three places:
- the job command line;
- the plan's admission prediction;
- a 4 h time cap per job instead of 2 h, so that an n = 384 optimization of up to 300 design iterations is not cut
  short (T30 measured about 10 s per design iteration at n = 384).

When a job has more than 400 samples, the full sample list goes to `samples.json` next to `monitor.json`.

D2. `t31_prep.py`, a new CPU-only file. It writes `code_hashes.json` and the host checks of section 4. It holds no
analysis.

D3. Admission prediction for the C0 and AUDIT jobs. The plan says "the same model with the FP64 PCG workspace in place
of the IR workspace (+3 × 8 B and +2 × 4 B per DOF)". The wrapper adds the 32 B per allocated DOF inside the 5 %
headroom and does not subtract the IR workspace. This prediction is larger, so it is the more cautious choice.

D4. Sign of the job's `net_F`/`net_M` fields (informational reaction check only). The job stores the applied load
resultant and the sum of (K u) at the clamped DOFs. Its `net` field subtracts the two, but (K u) at the supports is
minus the force the supports exert, so equilibrium is applied + (K u)_supports = 0, not applied − (K u)_supports.
`t31_analyse.py` recomputes the balance as applied + stored from the raw fields (`reactions_informational`) and does
not use `net`. The job code was left unchanged after the first job. The field enters no gate and no endpoint.

D5. Descriptive additions, outside the plan's endpoints and labelled so in `out/summary.json`
(`end_state_descriptive`). For each OPT run they record:
- the stopping quantities over the last 10 iterations: the J spread, max |Δρ_phys| and the number of elements moving
  by more than 0.01;
- the first iteration after 75 at which the J-spread test alone holds.

They show why the authors' stopping rule did not fire. They change no verdict.

D6. Fix round 1 (analysis and report only; CPU only, no GPU job, no measured value changed). `t31_analyse.py` now:
- counts the final production re-solve in the solve and setup totals and the summed outer and inner iterations,
  because the plan's optimization boundary includes it; the driver's design-iteration totals are kept under
  `totals_design_iterations_only`;
- gives the plan's audit and C0 time (four solves plus the multigrid setup) beside the job's wider timed interval;
- checks E1 (e) against the launcher's first sample. Coverage is complete only from the third sample in all eight
  jobs, so (e) is recorded as not established. This is a reading of the frozen criterion, not a change to it, and no
  verdict changes;
- records the largest early (iterations 1–75) J difference in C5;
- marks what the scalar histories can and cannot show about the end state.
The previous files are in `out/fix_r1/`.

D7. Fix round 2 (analysis and report only; CPU only, no GPU job, no measured value changed). Two job fields are
labelled differently from what they hold; `t31_job.py` was left as it ran and `t31_analyse.py` now relabels them:
- the audit `endpoints` field `audit_time_s_solves_plus_setup` (`t31_job.py:420`) holds the job's wider
  `solve_and_setup_s` interval. The summary gives the plan's endpoint (four solves plus the multigrid setup) under that
  name and the wider interval as `broader_interval_s`;
- `iterations_2_to_end_s` (`t31_job.py:357`) is timed from entry to iteration 1's `on_iter` callback, so it includes
  that callback's initial-state hashes and first history write. The summary exports it as
  `measured_from_iteration1_callback_entry_s`, with bounds [measured − `on_iter_io_s`, measured] for the plan's
  quantity and the corresponding bounds on the C4 ratio. The boundary is the same in all three OPT runs.
The previous files are in `out/fix_r2/`.
