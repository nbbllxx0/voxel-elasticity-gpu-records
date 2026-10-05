# Measurement records: matrix-free voxel elasticity on one graphics processor

Measurement records and logs for the manuscript *Matrix-free voxel elasticity on one graphics processor: speed, memory and accuracy* by Shaoliang Yang and Jun Wang (Santa Clara University), submitted for publication.

The study compares eight matrix-free finite-element operator implementations on one 24 GB NVIDIA RTX 4090. It follows their effects into mixed-precision state solves and complete 3D topology optimizations of up to 113 million elements.

**This repository contains records only.** The implementation (operators, multigrid, solvers, optimizer and experiment drivers) will be released in this repository upon acceptance of the manuscript.

## What is here

`records/` holds one JSON record per measurement. Every number in the manuscript's tables and figures comes from these records. Each record contains:
- the measured values;
- a validity flag;
- the recorded GPU, driver and library versions;
- a `code_hash` identifying the exact source version that produced it. The released code will reproduce these hashes.

| Folder | Study |
|---|---|
| `E0_platform.json` | measured device ceilings (DRAM, FP32/FP64 throughput, atomics) |
| `E2/` | operator survey: eight matrix-free mappings and cuSPARSE CSR/BSR, FP32 and FP64, 6.6×10⁴ to 2.68×10⁸ elements |
| `E3_mechanism.json` | static instruction counts and the FP64 issue-rate model fit |
| `E4/` | cost of refreshing assembled matrices and of the multigrid hierarchy update |
| `E5/` | cold state solves on fixed designs (preconditioner and fine-level mapping) |
| `E6/`, `E6b/`, `E7/` | complete optimizations at 1.02, 8.2 and 65.5 million elements; memory probes and mapping swaps in `E7/` |
| `E6rep/` | timing repetitions of the headline optimizations |
| `E8/`, `E8b/`, `E13/` | single-precision accuracy: residual floors and compliance errors for several operators and controls |
| `E9/` | raw-density lower-bound ablation |
| `E10/` | same-GPU comparison with the released code of Hou et al. |
| `E11/` | hardware counters (Nsight Compute) |
| `E12/`, `E12b/` | 113-million-element runs and recursive-FP32-stop controls |
| `E14/` | recursive-stop controls with an FP64-arithmetic operator and with the difference-form stencil |
| `E15/` | FP64 operators with FP32- versus FP64-stored moduli; difference-form stencil cost |
| `E16/` | iterative refinement with the difference-form stencil on the bridge problem |
| `E17/` | FP64 outer-operator swap inside a complete optimization |
| `T1_*`, `T2_*`, `T3_*` | verification of operators, multigrid and the precision-control operators |
| `logs/` | run logs, the job queue log and the GPU-activity log used to screen timings for interference |
| `_superseded/` | earlier records that the manuscript still cites (an independent timing repetition and a capacity test) |
| `*.npz` | optimized density fields (NumPy arrays) |

Some records are not timing evidence, and their elapsed times should not be read as performance results:
- records with `"valid": false`;
- failed or unsuccessful runs, which are kept on purpose (for example, runs that stop because a solve fails);
- accuracy-only runs made on a busier desktop (`E13`, `E14`, `E16`).

## Redactions

Only identifiers were changed; no measured value was altered.
- **Machine name:** the `host` field in every record is replaced by `<redacted>`.
- **File-system paths:** the user's home directory became `<user-home>` and the project directory `<project>`.
- **Traceback source lines:** in the run logs, the source-code lines that Python prints in tracebacks are replaced by `<source line redacted>`.
- **Program names:** in `logs/gpu_engine_activity.csv`, other programs on the shared display GPU are anonymized as `other-process-N`. `python` (the measured process), `System` and `dwm` (the Windows compositor) are kept.

`MANIFEST.json` lists the SHA-256 and size of every file as released.

## Licence and citation

The records are released under the Creative Commons Attribution 4.0 International licence (`LICENSE`). Please cite the manuscript; citation details will be added on publication.
