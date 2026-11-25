# T24 deviations from ANALYSIS_PLAN.md

ANALYSIS_PLAN.md is unchanged (its sha256 is still 0f4b22e5…2d17). Each entry says whether it was written before or
after the confirmatory jobs.

## D1 (2026-11-24, before any confirmatory job): check C3 cannot hold, because the driver is not bit-reproducible run to run

Plan §5 C3: "the k = 16 smoke run with and without the hook agrees bit for bit in every per-iteration c, `rel_true`
and Krylov count". The plan adds that if C3 fails before the confirmatory jobs, the hook is fixed first.

What happened (development runs, `out/runs/dev16_*`). The hook-on run `dev16_1e-5` and the hook-off run
`dev16_1e-5_nohook` agree bit for bit through iteration 15. At iteration 16, the first continuation step, they start
from the same initial residual and take the same number of Krylov iterations (41), but their accepted residuals and
compliances differ (c = 4.230262022265744 against 4.230262022281601). To find out whether the hook caused this, three
more development repeats were run with the same code: two hook-off runs (`dev16_1e-5_nohook_r2`, `_r3`) and one hook-on
run (`dev16_1e-5_r2`). The first iteration at which c, `rel_true` or the Krylov count differs, for each pair:

| pair | first differing iteration |
|---|---|
| hook-off vs hook-off (3 pairs) | 18, 19, 18 |
| hook-on vs hook-on | 16 |
| hook-on vs hook-off (6 pairs) | 16, 16, 16, 17, 17, 17 |

So two hook-off runs of the unchanged driver also differ from each other. The authors' driver (byte-identical copy,
`src/voxfem`) is not bit-reproducible run to run at k = 16, whether or not the hook runs. A bit-for-bit C3 can
therefore not be met by any implementation of the hook, and no hook fix is possible. The hook is unchanged: it reads
driver state, writes only its own buffers, and C2 (hook residual = driver `rel_true`, bit for bit) held in every
development run. All five repeats stop at iteration 82 (`max_change`). Their tight FP64 compliances lie within
1.0e-8 relative of each other (the largest gap is `dev16_1e-5_nohook_r3`, +9.985e-9 against `dev16_1e-5`).

Consequences, all already in the plan:
- C3 is reported as failed, with this explanation. C3 qualifies the result and does not gate it.
- A′ is not expected to be bit-identical to A. The run-to-run attribution rule of §5 (A–B attributed only where it
  exceeds 10 × A–A′) therefore governs every contradiction verdict and the H3 attribution.
- The hook-on runs diverge from each other no later than the hook-off runs do (16 against 18–19). That is not evidence
  that the hook perturbs the computation. With one hook-on pair the difference cannot be resolved, and it is reported
  as observed.

No confirmatory data existed when this entry was written.

## Reading of two plan items (not deviations; fixed before the confirmatory jobs)

- Admission (plan §3): "predicted peak 3.5 GB". The launcher uses 3.5 GiB (3,758,096,384 B), the larger of the two
  readings, plus the 1.5 GiB margin.
- H3 attribution (plan §5): the sentence "H3 is inconclusive under the attribution rule when L2(A,B) ≤ 10 L2(A,A′) and
  A′ is not bit-identical to A" is applied to every H3 class, with the class reported beside it. L2(A,A′) uses the same
  iterations S−4…S, or those of min(N_A, N_A′) if A′ is shorter (`t24_analyse.py`, docstring).
