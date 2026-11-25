# T25: Figure 4 with repaired designs (A.1, A.3, R2.5)

Outcome against the acceptance statement: **supports**. Each of the seven surfaces now has an identified operator,
field storage precision, solver and numerical record. Each label is computed from that panel's own record. The one
discrepancy with the historical timing records is explained below and changes no label digit. The fallback (the
original seven panels, relabelled) is also rendered. The authors can therefore choose either version.

## 1. What the submitted Figure 4 showed

The submitted `F9_designs.pdf` (manuscript/fead1.3/figures) is byte-identical to the project's figures/F9_designs.pdf.
The panel record that fig_designs.py wrote with it (figures/F9_designs_panels.json) names the seven fields. All seven
are **original-stencil** runs (`op32 = stencil`), and each submitted label equals its record's compliance exactly
(out/checks.json: `seven_submitted_panels_original_stencil`, `seven_submitted_labels_match_records`). Re-rendering
those seven fields with the copied processing reproduces every embedded panel image of the submitted PDF pixel for
pixel (out/figure/image_compare.json, `fallback_vs_submitted`: all 7 identical).

## 2. Panel mapping (out/panel_mapping.json, out/compliance_table.md)

Panel order as submitted: (b) row 1 is k = 160 (8,192,000 elements) and row 2 is k = 320 (65,536,000 elements), with
the columns cantilever, bridge and torsion. (c) is the k = 384 cantilever (113,246,208 elements).

| Panel | Problem, k | Solver | Revised field (difference form) | Storage | Revised record | 2kc submitted → revised |
|---|---|---|---|---|---|---|
| b1 | cantilever 160 | FP64 PCG + FP32 V-cycle | results/E32/simp_cantilever_k160_mg64_stencil_diff.npz | float16 archive of FP32 field | same name .json | 94.2402 → 94.2402 |
| b2 | bridge 160 | FP64 PCG + FP32 V-cycle | results/E32/simp_bridge_k160_mg64_stencil_diff.npz | float16 archive | same name .json | 28.1542 → 28.1542 |
| b3 | torsion 160 | FP64 PCG + FP32 V-cycle | results/E32/simp_torsion_k160_mg64_stencil_diff.npz | float16 archive | same name .json | 37.1663 → 37.1663 |
| b4 | cantilever 320 | FP64 PCG + FP32 V-cycle | **T25 run**: out/runs/k320_cantilever_repaired/simp_cantilever_k320_mg64_stencil_diff_native_fp32.npz | **native FP32** | same folder, .json | 94.7624 → 94.7624 |
| b5 | bridge 320 | FP64 PCG + FP32 V-cycle | results/E32/simp_bridge_k320_mg64_stencil_diff.npz | float16 archive | same name .json | 30.3620 → 30.3621 |
| b6 | torsion 320 | FP64 PCG + FP32 V-cycle | results/E32/simp_torsion_k320_mg64_stencil_diff.npz | float16 archive | same name .json | 37.3347 → 37.3347 |
| c | cantilever 384 | iterative refinement (FP32 V-cycle correction, FP64 residual) | results/E32/simp_cantilever_k384_mg_ir_stencil_diff.npz | float16 archive | same name .json | 94.9725 → 94.9724 |

The submitted records are results/E6b/simp_*_k160_mg64_stencil.json, results/E7/simp_*_k320_mg64_stencil.json and
results/E7/simp_cantilever_k384_mg_ir_stencil.json. Every repaired panel uses the same solver as its submitted panel.
All 14 records are accepted: status ok, valid, converged, not stopped by the iteration guard, final FP64 true residual
≤ 1e-5, no spill (`all_fourteen_records_accepted`).

**Labels.** Each label is n_elem and the physical compliance 2kc, from t25_labels.py run on the panel's own record
(out/panel_labels_revised.json; fallback out/panel_labels_submitted.json). The labels are 94.24, 28.15, 37.17, 94.76,
30.36, 37.33 and 94.97 in both versions, because the repaired and original compliances differ by between 3.4e-11 and
1.4e-6 relative (out/compliance_table.csv, `rel_change_2kc`). Between grids, the bridge's 2kc changes by +7.84 %
from k = 160 to k = 320 in both sets (submitted 0.078420, revised 0.078422; out/cross_grid_2kc.json). The cantilever
changes by +0.55 % and the torsion by +0.45 %. Explaining the bridge change is T26's task.

**Field to record identity.**
- **Provenance tie.** The process that wrote each record also wrote its field, and every record names its field
  (`every_record_names_its_field`). For the new run, the record stores the SHA-256 of the native FP32 array, which
  matches the saved field (`native_field_sha256_matches_its_record`).
- **Consistency check.** Volume fraction and grayness recomputed from each stored field agree with the record. The
  float16 archives agree to within 1.6e-9 in volume and 6.7e-9 in grayness. The native field agrees exactly, with a
  difference of 0 in both (out/field_checks.json).
- **What this check cannot do.** Volume and grayness do not tell an original field from its repaired counterpart.
  The original field measured against the repaired record agrees in volume to within 1.4e-9
  (`submitted_field_vs_revised_record_*` in panel_mapping.json). Identity therefore rests on the provenance tie, not
  on matching numbers. Matching rounded compliances do not establish that two fields are the same.

## 3. The new repaired k = 320 cantilever (out/verification_k320.json)

**Setup.** The run used a task-local driver (t25_job.py) that calls voxfem.simp.SIMP exactly as run_simp.py does,
with the configuration of the E32 records simp_cantilever_k320_mg64_stencil_diff_r{1,2,3}.json (`config_equal` true
for all three). The copied solver and run_simp.py match the per-file provenance of those records file for file
(out/code_copy_hashes.json). The driver copied the native FP32 final physical field to the host in chunks and saved
it before any cast. It then wrote the historical float16 cast beside it. That cast equals run_simp.py's convention
(`archive_equals_cast_of_native`), with a largest cast error of 2.25e-4.

**Checks.**
- dtype float32 on the device and on the host; shape 640 × 320 × 320 = the record's grid.
- Accepted: converged by bounded oscillation at 76 design iterations. The final FP64 true residual was 5.12e-6
  (limit 1e-5). The in-process spill watch and the launcher watch both report no spill.
- Its own compliance is c = 0.14806624661500312, so 2kc = 94.7624. The three E32 records each give 0.1480662466150064.
  The relative difference is −2.21e-14.

**Discrepancy with the timing counterparts.**
- *Numbers.* The run's history equals the E32 records bit for bit through design iteration 28. At iteration 29 the
  state solve starts from the same initial residual, but its result differs in the 8th digit of the true residual.
  From there on the compliances differ by at most 5.42e-11 relative per iteration, and the largest change in
  `drho_phys` is 2.81e-4. The Krylov iteration count is equal at all 76 iterations, and the iteration count and
  termination of the optimization are equal. The three E32 runs are bitwise identical with each other.
  - The environment differs only in the Windows build (10.0.26200 then, 10.0.26300 now). CuPy 13.4.1, the CUDA 12.8
    runtime and the driver API are the same.
  - Nothing order-dependent was found on this path. The solver code has no random start vector, and its atomic
    kernels belong to the element-atomic operator only.
  - The task specifies one run, so the cause was not isolated. The two candidates are the changed system software
    and a rare run-to-run variation; this record cannot tell them apart.
  - In the displayed quantity 2kc the difference is 2.10e-12 in absolute terms. The label's display increment of
    0.01 is about 4.75e9 times larger, 9.7 orders of magnitude, and the new value lies 0.0026 from the nearest
    rounding boundary. Both the new run and the three E32 records round to 94.76
    (verification_k320.json, `label_separation_vs_e32`). The field is tied to its own record. The discrepancy is
    therefore bounded in size, and it does not make the field's identification unresolved.
- *Timing.* The run's summed per-iteration time is 178.5 s, against 147.8, 148.3 and 151.1 s in E32. The mean of the
  E32 values, 149.07 s, is the manuscript's 149.1 s. The excess lies in the first iteration, which took 39.1 s
  against 2.90–2.99 s. From iteration 3 on the run took 136.4 s, against 142.7–145.8 s in E32 (mean 143.9 s).
  - A plausible cause is kernel compilation into the task-local kernel cache. Every one of the 72 compiled-kernel
    files now in that cache was written during this job, between 3.6 s and 53.2 s after the watch's baseline sample
    (verification_k320.json, `kernel_cache`).
  - The records hold no compilation timer, so the share of the first iteration spent compiling was not measured.
    The explanation is plausible, not established.
  - Either way, this run's timings are not performance data. Repaired-run performance claims stay with the E32
    timing records and the scale figure.

**GPU rule record.**
- Admission: predicted peak 16,656,205,312 B (E32's measured peak pool of 16,301,635,072 B plus the CUDA context).
  With the 1.5 GiB margin it fits the 22,651,338,752 B that nvidia-smi reported free. Other processes held
  6,486,069,248 B of dedicated memory, which was recorded and not counted.
- guard.require_budget, computed in the job: ok.
- Pool cap: 22,542,286,848 B.
- Measured: peak pool 16,301,635,072 B, the same as E32. The job's peak dedicated usage was 16,718,934,016 B.
- Coverage (monitor.json records it as `covered_from_go`): the watch covers the job from its first sample that
  contains the job's process onward. Before that sample, the job had created its CUDA context and made one
  one-element probe allocation (t25_job.py, `cp.empty(1)`). Every allocation of the optimization came later.
  - That baseline sample already held 354,570,240 B dedicated and 77,594,624 B shared memory.
  - From the baseline through the final sample, which was checked, shared usage grew by at most 79,691,776 B
    (limit 268,435,456 B = 256 MiB). Its largest absolute value was 157,286,400 B (verification_k320.json,
    `monitor_coverage`).
  - The interval before the baseline sample is not covered.
- The launcher self-test passed before the job (out/launch_selftest.json).

## 4. The regenerated figure

- **out/figure/F4_designs_revised.pdf (recommended).** The seven difference-form designs. The processing is unchanged
  from the submitted figure: the authors' fig_designs.py layout and render3d.py, copied unchanged into fig_src/. That
  means a block average to at most 384 cells along x, a Gaussian of 0.9 elements, the level 0.45, and the bridge and
  torsion cut on the mid-plane, all in the submitted panel order. Size 188.5 × 122.6 mm, the same as the submitted
  PDF, with no creator or date metadata. The heading of panel b names the operator ("Difference form, FP64 PCG + FP32
  V-cycle …"). Panel c reads "(iterative refinement) · 2kc = 94.97".
- **out/figure/F4_designs_submitted.pdf (the fallback).** The original seven fields, relabelled with 2kc. Its panel b
  heading reads "Original FP32 stencil, …".
- **How far the revised panels differ from the originals.**
  - In the fields: elements that change between solid and void at ρ = 0.5 number 0 (cantilever 160), 2 (bridge 160),
    4 (torsion 160), 0 (cantilever 320), 21 (bridge 320), 0 (torsion 320) and 83 (cantilever 384), of 8.2M to 113M
    (panel_mapping.json, `revised_vs_submitted_field`).
  - In the images: four of the seven embedded panel images are pixel-identical. Panel b1 differs by 1/255 in one
    pixel. Panels b5 and c differ by more than 16/255 in 2 and 6 pixels (image_compare.json, `revised_vs_fallback`).
  - The two figures therefore look the same. The correction is in the attribution, not in the visible shapes.

## 5. Release (A.3)

Not for release, under the authors' standing rule on diagram sources: t25_fig_designs.py, fig_src/fig_designs.py and
fig_src/render3d.py. The first two draw the problem sketches with supports and loads; render3d.py provides their
projection. Releasing the renderer separately remains an author decision.

May be released: the rendered PDF, the data-to-label script t25_labels.py (standard library only, draws nothing), the
data-only scripts t25_map.py and t25_image_compare.py, the tables and JSON in out/, and the native FP32 field of the
new run. T36 enforces the exclusion.

## 6. Notes for the writer (house rules)

- **Caption.** The submitted caption says compliances "are the normalized values … not comparable across grids". With
  2kc labels it should define 2kc as the physical compliance (C_phys = 2kc for reference edge 2 and physical edge 1/k)
  and name the operator: difference form in every panel, FP64 PCG with the FP32 V-cycle in (b), and iterative
  refinement in (c). The processing sentence stays as it was.
- **Corrections section (A.1).** The submitted surfaces came from original-stencil runs. The revised figure shows six
  historical difference-form designs and one newly computed one (the k = 320 cantilever), each labelled from its own
  record. The two sets look identical at the printed resolution.
- **Main text.** No file names, tool names or run labels. Supplement table of k, c and 2kc: out/compliance_table.md.

## Files

- Scripts: t25_hashes.py, t25_common.py, t25_launch.py and t25_launch_selftest.py (T30's guard, unchanged rules),
  t25_job.py, t25_map.py, t25_labels.py, t25_image_compare.py, t25_fig_designs.py (not for release).
- Outputs:
  - out/checks.json: 19 checks. 18 hold; `new_run_compliance_bitwise_equal_E32` is false, as explained in §3.
  - out/panel_mapping.json, out/field_checks.json, out/verification_k320.json, out/compliance_table.{csv,md},
    out/cross_grid_2kc.json, out/panel_labels_{revised,submitted}.json.
  - out/figure/*.
  - out/runs/k320_cantilever_repaired/ (record, native FP32 field, float16 cast, monitor).

## Corrections after the first check

Three reporting points were corrected; no value changed.
1. Coverage is stated from the watch's baseline sample onward, not from the first allocation.
2. The E32 discrepancy is 9.7 orders of magnitude below the label's display increment, not 13.
3. Kernel compilation is given as a plausible, unmeasured cause of the first-iteration excess.

t25_map.py now writes the coverage, the label separation and the cache-file times into verification_k320.json; it
previously inserted the cache explanation as literal text. It was rerun on the CPU. Every other output file is
byte-identical to its previous version, and every earlier field of verification_k320.json is unchanged. No GPU
job was run.

Compute used: one GPU job of 224 s (watch wall time) and about 10 min of CPU rendering, within T25's 3 h budget.
