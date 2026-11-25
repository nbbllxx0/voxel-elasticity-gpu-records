# T22 deviations and implementation records

ANALYSIS_PLAN.md is frozen and unchanged. Every entry below was written on 2026-11-24 before any confirmatory output
(k = 32, 64) was opened, except where an entry says otherwise. None changes a frozen parameter of sections 5, 6 or 9.

**D1. Orthonormalisation of the LOBPCG basis (plan 6.1), implementation choice.** The plan orthonormalises
Z = [X, W, P] by SVQB applied twice, with W and P directions dropped below a scaled Gram eigenvalue of 1e-12. The code
keeps the Ritz block X (orthonormal from the previous Rayleigh–Ritz step) fixed, removes the X components from [W, P]
twice (block classical Gram–Schmidt, applied identically to the carried S-images), and then applies SVQB twice to
[W, P] with the 1e-12 drop on the unit-diagonal scaled Gram matrix. This makes the implicit previous-direction block
P = W C_W + P C_P of standard LOBPCG well defined after in-place updates; the span of Z, the Rayleigh–Ritz problem and
the drop rule are those of the plan. Drop counts are recorded per solve (`drops_total`, `iterations_with_drops`).

**D2. Admission prediction per phase (plan 8.2).** Each job's pool peak is recorded separately for its setup phase
(V-cycle build, operators, setup checks) and its own part. At k = 8 and 16 the setup phase (the V-cycle's dense
coarsest factor) is the larger one, so a fit of the job-wide maximum would have fitted the near-constant setup peak
(about 10 bytes per DOF). The fit of plan 8.2 (a fixed part plus a per-DOF coefficient through two points) is therefore
applied to each phase separately and the larger prediction is used, plus T20's measured CUDA context. This is the
plan's "measured pool peaks of the same phases".

**D3. Development code fixes and reruns (plan 10).** Two job crashes during development were code errors outside
validation items 1–4 and were fixed before any confirmatory job: the first k = 4 J_skew run stopped on a Python
scoping error in the probe function (`out/runs/k4_skew_1`, rerun as `k4_skew_2`); the first k = 16 J_act run stopped on
an uninitialised record field (`out/runs/k16_act_1`, rerun as `k16_act_2`). Validation items 1–5 then passed on the
first evaluation (`out/dev_check.json`). No parameter changed.

**D4. Bootstrap of the authors' experiment copies.** `src/E8_precision_floor.py`, `src/E28_verification.py` and
`src/E29_review.py` are byte-identical copies of the authors' files (their hashes match the code manifest of
results/E29). They import `_boot`, which would put the authors' own code folder on the module path and create a
results folder. `t22_common.py` provides an in-memory `_boot` stub naming only the authors' folder, so the copies run
unchanged against the T22 copy of voxfem and write nothing.

**D5. Development V-cycle at k = 4.** At k = 4 the common V-cycle is built with two levels (as T21 did), because the
default coarsening is meant for larger grids. k = 4 is development only.

**D6. Settings the plan names by reference.** The search directions p^st and p^K use E29 part R2's `pcg_energy` with
its tolerance 1e-8 and default cap of 20,000 iterations; p^32 uses E8's `pcg32` with `mg32_x64`, a 400-iteration cap
and a true-residual check every iteration, as E29 runs it. The FP32-arithmetic control of plan 3.2 is the authors'
`MixedOperator` (labelled `fp64_arith_node`). The FP32 actions are applied with the production fixed-node mask
(`GMG.fixed0`), under which a fixed DOF returns its input; every input vector is zero there, so every output is zero
on the fixed DOFs.

**D7. p^st directions verified under the stencil matrix.** H5's contradiction clause (plan 9.6) needs every
available p^st direction verified positive. J_act therefore applies the witness rule of plan 6.3 to every p^st
direction under the `stencil` form, in addition to the negative candidates. The code was added after the development
J_act runs and before the first confirmatory J_act run, so the development records at k = 4, 8 and 16 lack this field
(see D8).

**D8. Development rerun of J_act at k = 4 (after the confirmatory jobs).** To exercise the p^st verification of D7 on development data, J_act at k = 4 was run again (`out/runs/k4_act_2`) after every confirmatory job had finished and before any confirmatory output was opened; the earlier record is kept as `out/data/k4/act_before_D7.json`. All five k = 4 p^st directions were verified positive under the stencil matrix. The k = 8 and 16 development records keep the earlier J_act code.

**D9. k = 128 J_skew refused for memory; not rerun (recorded after the extension jobs).** The k = 128 coefficient-skew job (`out/runs/k128_skew_1`) was stopped by the spill watch: its shared GPU usage grew 383,778,816 B above its first watched value (limit 268,435,456 B). About 115 MB of the growth came from the common setup, the same growth every completed k = 128 job showed. The step above the limit coincided with the start of the probe colouring, which copies three host node-index arrays of 136,456,200 B each to the device in single transfers. Under rule (c) of the authors' GPU memory rule, the job is recorded as refused for memory and was not rerun at this size. The k = 128 values of s_F, s_F^T, ||A||_F, ||A||_inf and ||A||_1 are therefore missing for all six forms. The k = 128 classes do not use s_F. The k = 128 extension of H1 for mean and diff cannot meet its s_F <= 1e-12 support clause and is inconclusive for that reason alone. `decision_request.json` asks the authors whether a single rerun with the index arrays formed on the device may be run; nothing was run.

**D10. T21 reference vectors at k = 64 and 128 (recorded after the confirmatory outputs were opened; no rule changed).** The plan's integrity check (correct length, finite, zero on the fixed DOFs, K0 residual within 1 % of T21's record) was passed by T21's saved `ref_target.npy` at k = 64 and 128, but its recorded and recomputed K0 residuals are 3.71e39 and 5.11e39: these files are the diverged reference iterates that T21's D7 describes, not solutions. At these k, u_ref, e_coef = u_coef - u_ref and (k = 64) e_ctrl = u_ctrl - u_ref are therefore, after scaling to unit maximum, essentially the same diverged vector. They stay in the action tables as the plan requires, labelled as such, and enter no hypothesis (H4 uses the smooth and low-mode sets only). At k = 128 the FP32 stencil control file does not exist, so e_ctrl is absent there. At k = 32 all three T21 vectors are solutions in the sense T21 recorded (K0 residuals 2.26e-10, 1.99e-2, 6.68e-2).

**D11. Departure from the transfer rule of plan 8.1 (recorded in fix round 1, after the checker's review).** Plan 8.1 asks for every host-to-device copy in pieces of E8's `CHUNK`. The job code that ran did not meet that rule in three places. (a) `t22_gpu.colours`, in J_skew only, copied three int64 node-index arrays to the device in single transfers (136,456,200 B each at k = 128). Their start coincided with the shared-memory step that stopped the k = 128 J_skew job (D9), so this departure cost the k = 128 skew endpoint. (b) The setup of every job uploaded the FP32 moduli in one piece (`cp.asarray(E)`, 67,108,864 B at k = 128). (c) T20's operator class, used as copied, uploads the free-DOF mask in one piece for each form (51,171,075 B at k = 128). The authors' multigrid and load classes were used as copied, and their transfers were not audited against the rule. Every completed job's monitor record passes (shared growth at most 115,343,360 B at k = 128), so those results stand. The refusal of D9 stands, and nothing was rerun. Code corrected for any later job: (a) the indices are formed on the device (`t22_gpu.node_ijk`), and (b) the moduli go through the chunked `upload`. (c) is left as T20 verified it and remains a departure for any later run. CPU test: `out/fix_r1/code_tests.json` (`colours_on_device`, `no_oneshot_uploads`).

**D12. Guard details of the job child (recorded in fix round 1).** Plan 8.2 allows no allocation until a sample holds the job PID with both counters ('go'), and it records `guard.require_budget`'s answer, computed in the job process. In the job version that ran, the child (i) created its CUDA context with a one-element CuPy allocation after 'armed' but before the first complete sample, (ii) set its pool cap only after 'go', and (iii) wrote the in-process budget answer only in `gpu_meta.json` at normal completion. That answer is therefore missing for the refused k = 128 J_skew job and for the two crashed development runs (`checks.json` → `runs` → `admission_in_process_note`). The launcher's admission from nvidia-smi exists for every job. Coverage of every job is stated from the first complete sample onward, and every retained job has a passing monitor record from there on. Code corrected for any later job: the context comes from the driver's free-memory query (no allocation), the pool cap is set before 'ctx', and `admission_in_process.json` is written as soon as the answer is computed. CPU test with a recording stand-in for CuPy: `out/fix_r1/code_tests.json` → `child_start_order`. The restored first version fails it.

**D13. Fix round 1, reporting and export corrections (no measured value changed).** (1) Exact symmetry is stated for k = 32 and 64 only, and the k = 128 symmetry endpoint is open for all six forms. (2) The k = 128 FP64 first PCG direction (E29's −1.1385383514247778 exactly) and the FP32-rounded unit-maximum witness vector (−1.1385382176691647) are kept apart. (3) The element-mean low-mode skew bound is 5.32e-9 at k = 128. (4) The T21 rows at k = 64 and 128 are labelled as the diverged iterate and differences from it (D10), and the report names the negative-energy count and the largest δ that come from them. (5) Repeat medians and ranges are exported to `action_repeats.csv`. The outputs before this round are in `out/before_fix_r1/`.
