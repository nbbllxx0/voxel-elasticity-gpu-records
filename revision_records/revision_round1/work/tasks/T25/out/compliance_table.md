| Panel | Problem | k | Elements | Solver | Submitted c (original stencil) | Submitted 2kc | Revised c (difference form) | Revised 2kc | Relative change |
|---|---|---|---|---|---|---|---|---|---|
| 1 | cantilever | 160 | 8,192,000 | mg64 | 0.2945005459 | 94.2402 | 0.2945005456 | 94.2402 | -1.03e-09 |
| 2 | bridge | 160 | 8,192,000 | mg64 | 0.08798177036 | 28.1542 | 0.08798177029 | 28.1542 | -8.00e-10 |
| 3 | torsion | 160 | 8,192,000 | mg64 | 0.1161447239 | 37.1663 | 0.1161446754 | 37.1663 | -4.18e-07 |
| 4 | cantilever | 320 | 65,536,000 | mg64 | 0.1480662466 | 94.7624 | 0.1480662466 | 94.7624 | -3.37e-11 |
| 5 | bridge | 320 | 65,536,000 | mg64 | 0.04744067069 | 30.3620 | 0.04744073912 | 30.3621 | +1.44e-06 |
| 6 | torsion | 320 | 65,536,000 | mg64 | 0.05833546982 | 37.3347 | 0.05833546982 | 37.3347 | -8.76e-11 |
| 7 | cantilever | 384 | 113,246,208 | mg_ir | 0.1236620794 | 94.9725 | 0.1236620379 | 94.9724 | -3.36e-07 |

Sources: submitted = results/E6b/simp_cantilever_k160_mg64_stencil.json; results/E6b/simp_bridge_k160_mg64_stencil.json; results/E6b/simp_torsion_k160_mg64_stencil.json; results/E7/simp_cantilever_k320_mg64_stencil.json; results/E7/simp_bridge_k320_mg64_stencil.json; results/E7/simp_torsion_k320_mg64_stencil.json; results/E7/simp_cantilever_k384_mg_ir_stencil.json
Revised = results/E32/simp_cantilever_k160_mg64_stencil_diff.json; results/E32/simp_bridge_k160_mg64_stencil_diff.json; results/E32/simp_torsion_k160_mg64_stencil_diff.json; revision_round1/work/tasks/T25/out/runs/k320_cantilever_repaired/simp_cantilever_k320_mg64_stencil_diff.json; results/E32/simp_bridge_k320_mg64_stencil_diff.json; results/E32/simp_torsion_k320_mg64_stencil_diff.json; results/E32/simp_cantilever_k384_mg_ir_stencil_diff.json
