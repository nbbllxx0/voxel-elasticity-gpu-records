# Reviewer-checkable inputs: records, arrays and data-only readers

This collection supports *Preserving rigid translations in single-precision matrix-free voxel finite element operators for large-scale topology optimization* (Yang and Wang). It is release v2.0 of the public records repository.

Every file keeps the path it has in the authors' project folder. `results/` holds the authors' measurement records
and arrays. `revision_round1/work/tasks/Txx/` holds the records of the studies made for the revision.
`revision_round1/input/manuscript/tables/` holds two tables of the submitted manuscript that the checks compare
against. `MANIFEST.json` lists the size and SHA-256 of every file.

## What it contains

- **Acceptance-tolerance study (Supplementary Table S24) and sensitivity localization.**
  - `results/E30/`: the twelve k = 80 tolerance runs, each with its record and its stored float16 final field.
  - `results/E30/dump_bridge_k160_mg64/`: the seven k = 160 bridge sensitivity dumps (float32 fields and
    sensitivities).
  - The audit records.
- **Design figure (Figure 4).**
  - Revised panels: the six difference-form fields of `results/E32/`, plus the newly computed k = 320 cantilever
    with its native float32 field and its float16 cast (`.../T25/out/runs/k320_cantilever_repaired/`).
  - Submitted panels: the seven original-stencil fields of `results/E6b/` and `results/E7/`.
  - The panel mapping, the labels, the compliance table, the rendered PDFs of both versions and the submitted
    rendered figure.
- **Bridge compliance across grids.** The re-solve records and the split table (`.../T26/out/`).
- **Comparison tables.** Every record that the comparison cites (`results/E2`, `E4`, `E7`, `E8`, `E10`, `E12`,
  `E12b`, `E29`, `E32` and the records of `.../T27` and `.../T28`), together with `comparison.json`, the table
  sources and the rendered tables (`.../T29/`).
- **Tight-reference field pair of the 8.2-million-element bridge.** The records of the two runs and of the repeat
  run (`.../T24/`). The per-iteration displacement fields (4.2 GB, files of 200 MB) are not included.
- **Saved designs of the external-code comparison.** The three k = 32 validation designs and the four exploratory
  k = 320 and k = 384 designs (float16), each with the record that names it (`.../T27/designs/`, `.../T27/out/`).
  The k = 320 and k = 384 designs are exploratory: their runs used a memory-pool cap above the prespecified one,
  and the prespecified admission rule would have refused the three k = 384 runs.
- **Records of the other revision studies.** The coefficient and symmetry analyses, the beam series, the spectra,
  the external-code comparisons and the bracket: summaries, tables, checks and the frozen analysis plans.

## Data-only readers (standard library, NumPy; PyMuPDF for the image comparison)

Run each one with `python -I` from any folder. The first two take the tree's root as an argument; the others find
the tree from their own location.

| purpose | command |
|---|---|
| Table S24 and localization | `python -I revision_round1/work/tasks/T23/t23_reader.py --data results/E30 --out <dir> --printed-table revision_round1/input/manuscript/tables/tab_tolerance_runs.tex` |
| Figure 4 labels | `python -I revision_round1/work/tasks/T25/t25_labels.py revision_round1/work/tasks/T25/out/panel_mapping.json . <out.json> revised` (or `submitted`) |
| Figure 4 image comparison | `python -I revision_round1/work/tasks/T25/t25_image_compare.py` |
| comparison tables | `build_comparison.py`, then `make_tables.py`, then `verify_sources.py [--selftest]` in `revision_round1/work/tasks/T29/` |
| bracket summary | `python -I revision_round1/work/tasks/T31/t31_analyse.py` |

Only one change was made to the staged copies of `build_comparison.py` and `verify_sources.py`: the absolute
project path became the tree's root.

## Not included

- **The implementation, the experiment drivers and every script that imports them.** The data statement promises
  the implementation at acceptance.
- **The scripts that draw the problem sketches and the design renderer.** These are diagram sources, and only the
  rendered figures are included.
- **Third-party code.** The released codes of Hou et al. and Träff et al. are available from their own repositories.
- **Arrays that were never kept.**
  - The native float32 final fields of the historical optimizations. Their archives are float16 casts.
  - Any field from the k = 320 cantilever timing runs.
  - The sensitivity vectors of the first k = 160 bridge audit run.
- **Large working arrays of the revision studies.** These are solution vectors, probe blocks and solver dumps. Each
  study's staged records summarize them.

## Redactions

The scheme is that of the public records repository; no measured value was altered.
- The machine name became `<redacted>`.
- The user's home directory became `<user-home>`, its temporary folder `<temp>`, and the project directory
  `<project>`.
- In records written for the revision, the source lines that tracebacks print became `<source line redacted>`.
- Other programs became `other-process-N`, with the public repository's numbering.

Records that are already public are included byte for byte as they were published.

The extended beam measurements and validation records are in `revision_round1/work/tasks/T33/`. The records of the bridge trajectory at the $10^{-8}$ state tolerance and its endpoint checks are in `revision_round1/work/tasks/T34/out/`; its displacement fields (1.4 GB) are not included. Records and retained fields for the bracket with final-phase damping are in `revision_round1/work/tasks/X0_2/out/`. The finer-grid continuation that meets the stopping rule at 7.23 million active voxels is in `revision_round1/work/tasks/X1_1/`: its analysis plan, fixed before the run, the deviations from it, the records, and the retained fields; the rendered Figure 6 is `revision_round1/work/tasks/X1_1F/fig_bracket_study.pdf`.
