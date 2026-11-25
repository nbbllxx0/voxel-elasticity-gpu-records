### R. References (FP64 PCG on K0, target 5e-10)

| layout | k | elements | its | ρ K0-ind | ρ K0 | tightened solve | B_C | B_E | U_ref^C | U_ref^E | U_ref^C / U_ref^E set by | G-ref |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| uniform | 8 | 4,096 | 14 | 4.006e-10 | 4.006e-10 | capped_or_failed (true residual 4.239e+32 > 1.0e-11 after 20000 iterations) | 6.564e-13 | 2.404e-09 | 6.564e-13 | 2.404e-09 | residual bound (conditional on lambda_lb) / residual bound (conditional on lambda_lb) | pass |
| uniform | 16 | 32,768 | 15 | 3.260e-10 | 3.260e-10 | capped_or_failed (non-positive curvature nan at iteration 13588) | 1.116e-12 | 2.679e-09 | 1.116e-12 | 2.679e-09 | residual bound (conditional on lambda_lb) / residual bound (conditional on lambda_lb) | pass |
| uniform | 32 | 262,144 | 16 | 2.265e-10 | 2.265e-10 | capped_or_failed (true residual 1.129e+18 > 1.0e-11 after 20000 iterations) | 5.538e-13 | 2.585e-09 | 5.538e-13 | 2.585e-09 | residual bound (conditional on lambda_lb) / residual bound (conditional on lambda_lb) | pass |
| uniform | 64 | 2,097,152 | broke down | 3.707e+39 | 3.707e+39 | capped_or_failed (non-positive curvature nan at iteration 1) | – | – | – | – | – / – | FAIL |
| uniform | 128 | 16,777,216 | broke down | 5.110e+39 | 5.110e+39 | capped_or_failed (non-positive curvature nan at iteration 1) | – | – | – | – | – / – | FAIL |
| interface | 8 | 4,096 | 15 | 2.019e-10 | 2.019e-10 | converged | 9.003e-14 | 2.485e-09 | 9.121e-14 | 2.485e-09 | tightening estimate (larger than the residual bound) / residual bound (conditional on lambda_lb) | pass |
| interface | 16 | 32,768 | 16 | 1.355e-10 | 1.355e-10 | capped_or_failed (non-positive curvature nan at iteration 3180) | 9.897e-14 | 2.283e-09 | 9.897e-14 | 2.283e-09 | residual bound (conditional on lambda_lb) / residual bound (conditional on lambda_lb) | pass |
| interface | 32 | 262,144 | 16 | 2.138e-10 | 2.138e-10 | capped_or_failed (non-positive curvature nan at iteration 14225) | 5.063e-13 | 5.003e-09 | 5.063e-13 | 5.003e-09 | residual bound (conditional on lambda_lb) / residual bound (conditional on lambda_lb) | pass |
| interface | 64 | 2,097,152 | 16 | 3.338e-10 | 3.338e-10 | capped_or_failed (true residual 4.652e+25 > 1.0e-11 after 20000 iterations) | 3.655e-13 | 1.094e-08 | 3.655e-13 | 1.094e-08 | residual bound (conditional on lambda_lb) / residual bound (conditional on lambda_lb) | pass |
| interface | 128 | 16,777,216 | 17 | 2.701e-10 | 2.701e-10 | capped_or_failed (true residual 5.267e+11 > 1.0e-11 after 20000 iterations) | – | – | – | – | – / – | FAIL |

### C. Coefficient calculations (rounded coefficients, FP64 GMRES-DC), interface, D3 sensitivity

| form | k | iterate | D_coef | U | resolved | e | U^E | ratio to k/2 | own residual | gates |
|---|---|---|---|---|---|---|---|---|---|---|
| stencil | 8 | target | 1.609e-03 | 2.475e-11 | True | 1.711e-03 | 2.510e-09 | – | 3.268e-10 | gates passed |
| stencil | 16 | target | 6.477e-03 | 5.192e-13 | True | 6.875e-03 | 2.283e-09 | 4.025 | 1.436e-11 | gates passed |
| stencil | 32 | target | 2.645e-02 | 5.355e-13 | True | 2.807e-02 | 5.003e-09 | 4.085 | 4.198e-11 | gates passed |
| stencil | 64 | target | 1.161e-01 | 1.260e-12 | True | 1.233e-01 | 1.095e-08 | 4.388 | 1.315e-10 | gates passed |
| stencil | 128 | target | 7.668e-01 | – | False | 8.196e-01 | – | – | 6.547e-10 | G-ref failed; coefficient solve failed: this target iterate is the smallest-residual iterate, reported, enters no test |
| corner | 8 | target | 4.139e-05 | 3.251e-11 | True | 4.543e-05 | 2.518e-09 | – | 4.219e-10 | gates passed |
| corner | 16 | target | 8.093e-05 | 2.830e-13 | True | 8.924e-05 | 2.283e-09 | 1.955 | 5.331e-12 | gates passed |
| corner | 32 | target | 1.597e-04 | 7.967e-13 | True | 1.766e-04 | 5.003e-09 | 1.973 | 1.501e-11 | gates passed |
| corner | 64 | target | 3.172e-04 | 4.584e-13 | True | 3.510e-04 | 1.094e-08 | 1.986 | 4.236e-11 | gates passed |
| corner | 128 | target | 6.321e-04 | – | False | 7.001e-04 | – | – | 1.208e-10 | G-ref failed |
| mean | 8 | target | 2.498e-06 | 5.096e-12 | True | 2.527e-06 | 2.491e-09 | – | 2.172e-10 | gates passed |
| mean | 16 | target | 2.518e-06 | 1.895e-13 | True | 2.547e-06 | 2.283e-09 | 1.008 | 5.333e-12 | gates passed |
| mean | 32 | target | 2.524e-06 | 6.508e-13 | True | 2.552e-06 | 5.003e-09 | 1.002 | 1.512e-11 | gates passed |
| mean | 64 | target | 2.525e-06 | 5.386e-13 | True | 2.554e-06 | 1.094e-08 | 1.001 | 4.242e-11 | gates passed |
| mean | 128 | target | 2.525e-06 | – | False | 2.554e-06 | – | – | 1.199e-10 | G-ref failed |
| diff | 8 | target | 3.884e-07 | 6.227e-12 | True | 3.980e-07 | 2.492e-09 | – | 2.163e-10 | gates passed |
| diff | 16 | target | 3.879e-07 | 3.023e-13 | True | 3.985e-07 | 2.283e-09 | 0.999 | 5.261e-12 | gates passed |
| diff | 32 | target | 3.868e-07 | 1.027e-12 | True | 3.979e-07 | 5.003e-09 | 0.997 | 1.511e-11 | gates passed |
| diff | 64 | target | 3.859e-07 | 5.503e-13 | True | 3.974e-07 | 1.094e-08 | 0.998 | 4.240e-11 | gates passed |
| diff | 128 | target | 3.852e-07 | – | False | 3.967e-07 | – | – | 1.198e-10 | G-ref failed |

### C. Coefficient calculations (rounded coefficients, FP64 GMRES-DC), uniform, D3 sensitivity

| form | k | iterate | D_coef | U | resolved | e | U^E | ratio to k/2 | own residual | gates |
|---|---|---|---|---|---|---|---|---|---|---|
| stencil | 8 | target | 8.368e-03 | 1.718e-12 | True | 8.495e-03 | 2.405e-09 | – | 1.677e-11 | gates passed |
| stencil | 16 | target | 3.462e-02 | 4.897e-12 | True | 3.515e-02 | 2.683e-09 | 4.138 | 4.909e-11 | gates passed |
| stencil | 32 | target | 1.555e-01 | 7.158e-12 | True | 1.579e-01 | 2.592e-09 | 4.491 | 1.641e-10 | gates passed |
| stencil | 64 | target | – | – | False | – | – | – | 8.701e-10 | G-ref failed; coefficient solve failed: this target iterate is the smallest-residual iterate, reported, enters no test |
| stencil | 128 | target | – | – | False | – | – | – | 9.121e-10 | G-ref failed; coefficient solve failed: this target iterate is the smallest-residual iterate, reported, enters no test |
| corner | 8 | target | 1.430e-04 | 7.851e-13 | True | 1.468e-04 | 2.404e-09 | – | 5.822e-12 | gates passed |
| corner | 16 | target | 2.820e-04 | 1.909e-12 | True | 2.900e-04 | 2.680e-09 | 1.972 | 1.665e-11 | gates passed |
| corner | 32 | target | 5.590e-04 | 2.403e-12 | True | 5.754e-04 | 2.587e-09 | 1.982 | 4.994e-11 | gates passed |
| corner | 64 | target | – | – | False | – | – | – | 1.373e-10 | G-ref failed |
| corner | 128 | target | – | – | False | – | – | – | 3.823e-10 | G-ref failed |
| mean | 8 | target | 6.198e-06 | 9.233e-13 | True | 6.247e-06 | 2.404e-09 | – | 5.991e-12 | gates passed |
| mean | 16 | target | 6.243e-06 | 2.379e-12 | True | 6.292e-06 | 2.680e-09 | 1.007 | 1.735e-11 | gates passed |
| mean | 32 | target | 6.255e-06 | 1.887e-12 | True | 6.304e-06 | 2.587e-09 | 1.002 | 4.822e-11 | gates passed |
| mean | 64 | target | – | – | False | – | – | – | 1.335e-10 | G-ref failed |
| mean | 128 | target | – | – | False | – | – | – | 3.944e-10 | G-ref failed |
| diff | 8 | target | 1.119e-06 | 9.548e-13 | True | 1.128e-06 | 2.404e-09 | – | 6.121e-12 | gates passed |
| diff | 16 | target | 1.127e-06 | 1.212e-12 | True | 1.137e-06 | 2.680e-09 | 1.007 | 1.655e-11 | gates passed |
| diff | 32 | target | 1.130e-06 | 6.503e-13 | True | 1.139e-06 | 2.586e-09 | 1.002 | 4.682e-11 | gates passed |
| diff | 64 | target | – | – | False | – | – | – | 1.476e-10 | G-ref failed |
| diff | 128 | target | – | – | False | – | – | – | 3.764e-10 | G-ref failed |

### C. Coefficient calculations (rounded coefficients, FP64 GMRES-DC), interface, frozen plan

| form | k | iterate | D_coef | U | resolved | e | U^E | ratio to k/2 | own residual | gates |
|---|---|---|---|---|---|---|---|---|---|---|
| stencil | 8 | target | 1.609e-03 | 2.475e-11 | True | 1.711e-03 | 2.510e-09 | – | 3.268e-10 | gates passed |
| stencil | 16 | tight iterate, outer step 9 | 6.477e-03 | – | False | 6.875e-03 | – | – | 1.423e-11 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| stencil | 32 | tight iterate, outer step 8 | 2.645e-02 | – | False | 2.807e-02 | – | – | 4.185e-11 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| stencil | 64 | tight iterate, outer step 9 | 1.161e-01 | – | False | 1.233e-01 | – | – | 1.314e-10 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| stencil | 128 | target | 7.668e-01 | – | False | 8.196e-01 | – | – | 6.547e-10 | G-ref failed; coefficient solve failed: this target iterate is the smallest-residual iterate, reported, enters no test |
| corner | 8 | target | 4.139e-05 | 3.251e-11 | True | 4.543e-05 | 2.518e-09 | – | 4.219e-10 | gates passed |
| corner | 16 | tight iterate, outer step 4 | 8.093e-05 | – | False | 8.924e-05 | – | – | 5.261e-12 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| corner | 32 | tight iterate, outer step 4 | 1.597e-04 | – | False | 1.766e-04 | – | – | 1.499e-11 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| corner | 64 | tight iterate, outer step 5 | 3.172e-04 | – | False | 3.510e-04 | – | – | 4.233e-11 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| corner | 128 | tight iterate, outer step 4 | 6.321e-04 | – | False | 7.001e-04 | – | – | 1.198e-10 | G-ref failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| mean | 8 | target | 2.498e-06 | 5.096e-12 | True | 2.527e-06 | 2.491e-09 | – | 2.172e-10 | gates passed |
| mean | 16 | tight iterate, outer step 4 | 2.518e-06 | – | False | 2.547e-06 | – | – | 5.280e-12 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| mean | 32 | tight iterate, outer step 8 | 2.524e-06 | – | False | 2.552e-06 | – | – | 1.493e-11 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| mean | 64 | tight iterate, outer step 8 | 2.525e-06 | – | False | 2.554e-06 | – | – | 4.232e-11 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| mean | 128 | tight iterate, outer step 8 | 2.525e-06 | – | False | 2.554e-06 | – | – | 1.197e-10 | G-ref failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| diff | 8 | target | 3.884e-07 | 6.227e-12 | True | 3.980e-07 | 2.492e-09 | – | 2.163e-10 | gates passed |
| diff | 16 | target | 3.879e-07 | – | False | 3.985e-07 | – | – | 5.261e-12 | G-coef failed; coefficient solve failed: this target iterate is the smallest-residual iterate, reported, enters no test |
| diff | 32 | tight iterate, outer step 21 | 3.868e-07 | – | False | 3.979e-07 | – | – | 1.494e-11 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| diff | 64 | tight iterate, outer step 4 | 3.859e-07 | – | False | 3.974e-07 | – | – | 4.232e-11 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| diff | 128 | tight iterate, outer step 9 | 3.852e-07 | – | False | 3.967e-07 | – | – | 1.197e-10 | G-ref failed; coefficient solve failed: smallest-residual iterate reported, enters no test |

### C. Coefficient calculations (rounded coefficients, FP64 GMRES-DC), uniform, frozen plan

| form | k | iterate | D_coef | U | resolved | e | U^E | ratio to k/2 | own residual | gates |
|---|---|---|---|---|---|---|---|---|---|---|
| stencil | 8 | tight iterate, outer step 5 | 8.368e-03 | – | False | 8.495e-03 | – | – | 1.600e-11 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| stencil | 16 | tight iterate, outer step 10 | 3.462e-02 | – | False | 3.515e-02 | – | – | 4.858e-11 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| stencil | 32 | tight iterate, outer step 5 | 1.555e-01 | – | False | 1.579e-01 | – | – | 1.623e-10 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| stencil | 64 | target | – | – | False | – | – | – | 8.701e-10 | G-ref failed; coefficient solve failed: this target iterate is the smallest-residual iterate, reported, enters no test |
| stencil | 128 | target | – | – | False | – | – | – | 9.121e-10 | G-ref failed; coefficient solve failed: this target iterate is the smallest-residual iterate, reported, enters no test |
| corner | 8 | tight iterate, outer step 4 | 1.430e-04 | – | False | 1.468e-04 | – | – | 5.687e-12 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| corner | 16 | tight iterate, outer step 4 | 2.820e-04 | – | False | 2.900e-04 | – | – | 1.635e-11 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| corner | 32 | tight iterate, outer step 10 | 5.590e-04 | – | False | 5.754e-04 | – | – | 4.651e-11 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| corner | 64 | tight iterate, outer step 7 | – | – | False | – | – | – | 1.322e-10 | G-ref failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| corner | 128 | tight iterate, outer step 6 | – | – | False | – | – | – | 3.758e-10 | G-ref failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| mean | 8 | tight iterate, outer step 4 | 6.198e-06 | – | False | 6.247e-06 | – | – | 5.765e-12 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| mean | 16 | tight iterate, outer step 8 | 6.243e-06 | – | False | 6.292e-06 | – | – | 1.639e-11 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| mean | 32 | tight iterate, outer step 4 | 6.255e-06 | – | False | 6.304e-06 | – | – | 4.630e-11 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| mean | 64 | tight iterate, outer step 4 | – | – | False | – | – | – | 1.323e-10 | G-ref failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| mean | 128 | tight iterate, outer step 14 | – | – | False | – | – | – | 3.737e-10 | G-ref failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| diff | 8 | tight iterate, outer step 4 | 1.119e-06 | – | False | 1.128e-06 | – | – | 5.583e-12 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| diff | 16 | tight iterate, outer step 5 | 1.127e-06 | – | False | 1.137e-06 | – | – | 1.621e-11 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| diff | 32 | tight iterate, outer step 14 | 1.130e-06 | – | False | 1.139e-06 | – | – | 4.636e-11 | G-coef failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| diff | 64 | tight iterate, outer step 7 | – | – | False | – | – | – | 1.320e-10 | G-ref failed; coefficient solve failed: smallest-residual iterate reported, enters no test |
| diff | 128 | tight iterate, outer step 9 | – | – | False | – | – | – | 3.738e-10 | G-ref failed; coefficient solve failed: smallest-residual iterate reported, enters no test |

### F. FP32 controls (common V-cycle, first recursive 1e-5 pass), interface: medians of three repeats

| form | k | its | D_tot (median) | range | U_ref^C | resolved | e (median) | ratio D to k/2 | ratio e to k/2 | K0 residual (rep. 1) | repeats |
|---|---|---|---|---|---|---|---|---|---|---|---|
| stencil | 8 | 9 | 1.519e-03 | [1.519e-03, 1.519e-03] | 9.121e-14 | True | 1.625e-03 | – | – | 2.124e-03 | repeats bitwise identical |
| stencil | 16 | 10 | 6.711e-03 | [6.711e-03, 6.711e-03] | 9.897e-14 | True | 7.105e-03 | 4.419 | 4.374 | 6.070e-03 | repeats bitwise identical |
| stencil | 32 | 10 | 2.629e-02 | [2.629e-02, 2.629e-02] | 5.063e-13 | True | 2.792e-02 | 3.917 | 3.929 | 1.754e-02 | repeats bitwise identical |
| stencil | 64 | 10 | 1.164e-01 | [1.164e-01, 1.164e-01] | 3.655e-13 | True | 1.235e-01 | 4.427 | 4.425 | 5.430e-02 | repeats bitwise identical |
| stencil | 128 | 11 | 7.685e-01 | [7.685e-01, 7.685e-01] | – | False | 8.213e-01 | – | – | 2.393e-01 | repeats bitwise identical |
| corner | 8 | 9 | 4.259e-05 | [4.257e-05, 4.259e-05] | 9.121e-14 | True | 4.711e-05 | – | – | 9.645e-04 | repeats not bitwise identical |
| corner | 16 | 10 | 8.182e-05 | [8.181e-05, 8.183e-05] | 9.897e-14 | True | 9.138e-05 | 1.921 | 1.940 | 2.848e-03 | repeats not bitwise identical |
| corner | 32 | 10 | 1.595e-04 | [1.595e-04, 1.596e-04] | 5.063e-13 | True | 1.787e-04 | 1.950 | 1.955 | 7.979e-03 | repeats not bitwise identical |
| corner | 64 | 10 | 3.190e-04 | [3.190e-04, 3.190e-04] | 3.655e-13 | True | 3.575e-04 | 1.999 | 2.001 | 2.268e-02 | repeats not bitwise identical |
| corner | 128 | 10 | 6.356e-04 | [6.356e-04, 6.356e-04] | – | False | 7.129e-04 | – | – | 6.412e-02 | repeats not bitwise identical |
| mean | 8 | 9 | 2.836e-06 | [2.835e-06, 2.840e-06] | 9.121e-14 | True | 7.663e-06 | – | – | 9.770e-04 | repeats not bitwise identical |
| mean | 16 | 10 | 2.892e-06 | [2.884e-06, 2.897e-06] | 9.897e-14 | True | 1.452e-05 | 1.020 | 1.895 | 2.819e-03 | repeats not bitwise identical |
| mean | 32 | 10 | 1.266e-06 | [1.262e-06, 1.275e-06] | 5.063e-13 | True | 2.843e-05 | 0.438 | 1.957 | 8.008e-03 | repeats not bitwise identical |
| mean | 64 | 10 | 1.825e-06 | [1.815e-06, 1.828e-06] | 3.655e-13 | True | 5.688e-05 | 1.442 | 2.001 | 2.266e-02 | repeats not bitwise identical |
| mean | 128 | 10 | 3.077e-07 | [3.074e-07, 3.088e-07] | – | False | 1.137e-04 | – | – | 6.417e-02 | repeats not bitwise identical |
| diff | 8 | 9 | 9.001e-07 | [9.001e-07, 9.001e-07] | 9.121e-14 | True | 7.301e-06 | – | – | 1.043e-03 | repeats bitwise identical |
| diff | 16 | 10 | 9.783e-07 | [9.783e-07, 9.783e-07] | 9.897e-14 | True | 1.438e-05 | 1.087 | 1.970 | 2.854e-03 | repeats bitwise identical |
| diff | 32 | 10 | 1.241e-07 | [1.241e-07, 1.241e-07] | 5.063e-13 | True | 2.852e-05 | 0.127 | 1.983 | 8.039e-03 | repeats bitwise identical |
| diff | 64 | 10 | 1.999e-07 | [1.999e-07, 1.999e-07] | 3.655e-13 | True | 5.683e-05 | 1.611 | 1.993 | 2.268e-02 | repeats bitwise identical |
| diff | 128 | 10 | 1.085e-07 | [1.085e-07, 1.085e-07] | – | False | 1.136e-04 | – | – | 6.417e-02 | repeats bitwise identical |

### F. FP32 controls (common V-cycle, first recursive 1e-5 pass), uniform: medians of three repeats

| form | k | its | D_tot (median) | range | U_ref^C | resolved | e (median) | ratio D to k/2 | ratio e to k/2 | K0 residual (rep. 1) | repeats |
|---|---|---|---|---|---|---|---|---|---|---|---|
| stencil | 8 | 9 | 9.277e-03 | [9.277e-03, 9.277e-03] | 6.564e-13 | True | 9.401e-03 | – | – | 7.320e-03 | repeats bitwise identical |
| stencil | 16 | 9 | 3.385e-02 | [3.385e-02, 3.385e-02] | 1.116e-12 | True | 3.438e-02 | 3.649 | 3.657 | 2.084e-02 | repeats bitwise identical |
| stencil | 32 | 10 | 1.537e-01 | [1.537e-01, 1.537e-01] | 5.538e-13 | True | 1.560e-01 | 4.540 | 4.538 | 6.682e-02 | repeats bitwise identical |
| stencil | 64 | 11 | – | [–, –] | – | False | – | – | – | 3.484e-01 | repeats bitwise identical |
| stencil | 128 |  | – | [–, –] | – | False | – | – | – | – | repeats bitwise identical |
| corner | 8 | 9 | 1.427e-04 | [1.426e-04, 1.427e-04] | 6.564e-13 | True | 1.472e-04 | – | – | 3.114e-03 | repeats not bitwise identical |
| corner | 16 | 9 | 2.817e-04 | [2.817e-04, 2.818e-04] | 1.116e-12 | True | 2.914e-04 | 1.975 | 1.980 | 8.909e-03 | repeats not bitwise identical |
| corner | 32 | 10 | 5.530e-04 | [5.530e-04, 5.530e-04] | 5.538e-13 | True | 5.731e-04 | 1.963 | 1.967 | 2.504e-02 | repeats not bitwise identical |
| corner | 64 | 10 | – | [–, –] | – | False | – | – | – | 7.046e-02 | repeats not bitwise identical |
| corner | 128 | 10 | – | [–, –] | – | False | – | – | – | 2.002e-01 | repeats not bitwise identical |
| mean | 8 | 9 | 8.051e-06 | [8.040e-06, 8.068e-06] | 6.564e-13 | True | 1.764e-05 | – | – | 3.200e-03 | repeats not bitwise identical |
| mean | 16 | 9 | 4.714e-06 | [4.699e-06, 4.721e-06] | 1.116e-12 | True | 3.156e-05 | 0.586 | 1.790 | 8.714e-03 | repeats not bitwise identical |
| mean | 32 | 10 | 1.275e-06 | [1.266e-06, 1.277e-06] | 5.538e-13 | True | 6.270e-05 | 0.271 | 1.987 | 2.513e-02 | repeats not bitwise identical |
| mean | 64 | 10 | – | [–, –] | – | False | – | – | – | 7.054e-02 | repeats not bitwise identical |
| mean | 128 | 10 | – | [–, –] | – | False | – | – | – | 1.987e-01 | repeats not bitwise identical |
| diff | 8 | 9 | 3.354e-06 | [3.354e-06, 3.354e-06] | 6.564e-13 | True | 1.581e-05 | – | – | 3.111e-03 | repeats bitwise identical |
| diff | 16 | 9 | 4.584e-07 | [4.584e-07, 4.584e-07] | 1.116e-12 | True | 3.091e-05 | 0.137 | 1.955 | 8.745e-03 | repeats bitwise identical |
| diff | 32 | 10 | 1.451e-06 | [1.451e-06, 1.451e-06] | 5.538e-13 | True | 6.254e-05 | 3.165 | 2.024 | 2.502e-02 | repeats bitwise identical |
| diff | 64 | 10 | – | [–, –] | – | False | – | – | – | 7.052e-02 | repeats bitwise identical |
| diff | 128 | 10 | – | [–, –] | – | False | – | – | – | 1.993e-01 | repeats bitwise identical |

### O. Observed orders log2 g(k/2 → k) of the compliance error D and the energy error e (plan 5.5; g = |X(k)| / |X(k/2)|, so a positive order is growth)

| pass | layout | kind | form | 8→16 D / e | 16→32 D / e | 32→64 D / e |
|---|---|---|---|---|---|---|
| frozen plan | interface | fp32_control | stencil | 2.144 / 2.129 | 1.970 / 1.974 | 2.146 / 2.146 |
| frozen plan | interface | fp32_control | corner | 0.942 / 0.956 | 0.963 / 0.967 | 0.999 / 1.001 |
| frozen plan | interface | fp32_control | mean | 0.028 / 0.922 | -1.192 / 0.969 | 0.528 / 1.001 |
| frozen plan | interface | fp32_control | diff | 0.120 / 0.978 | -2.979 / 0.988 | 0.688 / 0.995 |
| frozen plan | uniform | fp32_control | stencil | 1.867 / 1.871 | 2.183 / 2.182 | – |
| frozen plan | uniform | fp32_control | corner | 0.982 / 0.985 | 0.973 / 0.976 | – |
| frozen plan | uniform | fp32_control | mean | -0.772 / 0.840 | -1.886 / 0.990 | – |
| frozen plan | uniform | fp32_control | diff | -2.871 / 0.967 | 1.662 / 1.017 | – |
| D3 sensitivity | interface | coefficient | stencil | 2.009 / 2.007 | 2.030 / 2.030 | 2.133 / 2.135 |
| D3 sensitivity | interface | coefficient | corner | 0.967 / 0.974 | 0.981 / 0.984 | 0.990 / 0.992 |
| D3 sensitivity | interface | coefficient | mean | 0.011 / 0.011 | 0.003 / 0.003 | 0.001 / 0.001 |
| D3 sensitivity | interface | coefficient | diff | -0.002 / 0.002 | -0.004 / -0.002 | -0.003 / -0.002 |
| D3 sensitivity | interface | fp32_control | stencil | 2.144 / 2.129 | 1.970 / 1.974 | 2.146 / 2.146 |
| D3 sensitivity | interface | fp32_control | corner | 0.942 / 0.956 | 0.963 / 0.967 | 0.999 / 1.001 |
| D3 sensitivity | interface | fp32_control | mean | 0.028 / 0.922 | -1.192 / 0.969 | 0.528 / 1.001 |
| D3 sensitivity | interface | fp32_control | diff | 0.120 / 0.978 | -2.979 / 0.988 | 0.688 / 0.995 |
| D3 sensitivity | uniform | coefficient | stencil | 2.049 / 2.049 | 2.167 / 2.167 | – |
| D3 sensitivity | uniform | coefficient | corner | 0.979 / 0.982 | 0.987 / 0.989 | – |
| D3 sensitivity | uniform | coefficient | mean | 0.010 / 0.010 | 0.003 / 0.003 | – |
| D3 sensitivity | uniform | coefficient | diff | 0.011 / 0.011 | 0.003 / 0.003 | – |
| D3 sensitivity | uniform | fp32_control | stencil | 1.867 / 1.871 | 2.183 / 2.182 | – |
| D3 sensitivity | uniform | fp32_control | corner | 0.982 / 0.985 | 0.973 / 0.976 | – |
| D3 sensitivity | uniform | fp32_control | mean | -0.772 / 0.840 | -1.886 / 0.990 | – |
| D3 sensitivity | uniform | fp32_control | diff | -2.871 / 0.967 | 1.662 / 1.017 | – |

### S. Split of the interface controls (D3 pass: D_rest = (C_ctrl − C_F)/C_ref where D_coef is resolved)

| form | k | repeat | D_tot | D_rest | S (1e-5 → 1e-7) | S label | ‖u_ctrl − u_F‖_K0/√(fᵀu_ref) |
|---|---|---|---|---|---|---|---|
| stencil | 8 | 1 | 1.519e-03 | -9.044e-05 | 3.852e-12 | not attributable | 9.848e-05 |
| corner | 8 | 1 | 4.257e-05 | 1.183e-06 | 1.955e-12 | not attributable | 7.309e-06 |
| mean | 8 | 1 | 2.840e-06 | 3.422e-07 | 5.925e-13 | not attributable | 7.108e-06 |
| diff | 8 | 1 | 9.001e-07 | 5.117e-07 | -4.052e-13 | not attributable | 7.263e-06 |
| stencil | 16 | 1 | 6.711e-03 | 2.346e-04 | 7.306e-12 | not attributable | 2.421e-04 |
| corner | 16 | 1 | 8.182e-05 | 8.884e-07 | -4.565e-12 | not attributable | 1.430e-05 |
| mean | 16 | 1 | 2.897e-06 | 3.786e-07 | -4.079e-14 | not attributable | 1.423e-05 |
| diff | 16 | 1 | 9.783e-07 | 5.905e-07 | -2.330e-13 | not attributable | 1.436e-05 |
| stencil | 32 | 1 | 2.629e-02 | -1.664e-04 | 7.251e-12 | not attributable | 1.994e-04 |
| corner | 32 | 1 | 1.595e-04 | -1.687e-07 | 5.244e-12 | not attributable | 2.838e-05 |
| mean | 32 | 1 | 1.262e-06 | -1.262e-06 | 1.525e-13 | not attributable | 2.843e-05 |
| diff | 32 | 1 | 1.241e-07 | -2.626e-07 | 2.136e-13 | not attributable | 2.852e-05 |
| stencil | 64 | 1 | 1.164e-01 | 3.066e-04 | -1.681e-11 | not attributable | 3.802e-04 |
| corner | 64 | 1 | 3.190e-04 | 1.799e-06 | 5.958e-12 | not attributable | 5.692e-05 |
| mean | 64 | 1 | 1.815e-06 | -7.098e-07 | 3.867e-13 | not attributable | 5.686e-05 |
| diff | 64 | 1 | 1.999e-07 | -1.860e-07 | 2.530e-13 | not attributable | 5.683e-05 |
| stencil | 128 | 1 | 7.685e-01 | – | 4.447e-11 | stopping error | – |
| corner | 128 | 1 | 6.356e-04 | – | 7.618e-12 | stopping error | 1.137e-04 |
| mean | 128 | 1 | 3.077e-07 | – | 1.209e-12 | stopping error | 1.137e-04 |
| diff | 128 | 1 | 1.085e-07 | – | 1.395e-12 | stopping error | 1.136e-04 |

### P. PCG diagnostic (E29's pcg_energy on the rounded operator, common V-cycle)

| layout | form | k | status | its | min pᵀA p / pᵀK0 p | symmetry s_F |
|---|---|---|---|---|---|---|
| interface | stencil | 8 | ok | 15 | 0.9984 | 2.8e-10 |
| interface | corner | 8 | ok | 15 | 1.0000 | 1.8e-08 |
| interface | mean | 8 | ok | 15 | 1.0000 | 2.0e-16 |
| interface | diff | 8 | ok | 15 | 1.0000 | 2.7e-10 |
| interface | stencil | 16 | ok | 16 | 0.9936 | 1.2e-09 |
| interface | corner | 16 | ok | 16 | 0.9999 | 8.2e-08 |
| interface | mean | 16 | ok | 16 | 1.0000 | 2.2e-15 |
| interface | diff | 16 | ok | 16 | 1.0000 | 2.7e-09 |
| interface | stencil | 32 | ok | 16 | 0.9744 | 9.3e-11 |
| interface | corner | 32 | ok | 16 | 0.9998 | 1.2e-09 |
| interface | mean | 32 | ok | 16 | 1.0000 | 1.3e-16 |
| interface | diff | 32 | ok | 16 | 1.0000 | 7.5e-11 |
| interface | stencil | 64 | ok | 16 | 0.8977 | 1.2e-10 |
| interface | corner | 64 | ok | 16 | 0.9997 | 5.4e-09 |
| interface | mean | 64 | ok | 16 | 1.0000 | 3.3e-16 |
| interface | diff | 64 | ok | 16 | 1.0000 | 1.4e-10 |
| interface | stencil | 128 | ok | 17 | 0.5909 | 5.7e-11 |
| interface | corner | 128 | ok | 16 | 0.9994 | 1.8e-08 |
| interface | mean | 128 | ok | 16 | 1.0000 | 9.7e-16 |
| interface | diff | 128 | ok | 16 | 1.0000 | 4.6e-11 |
| uniform | stencil | 8 | ok | 14 | 0.9917 | 2.8e-15 |
| uniform | corner | 8 | ok | 14 | 0.9999 | 1.0e-07 |
| uniform | mean | 8 | ok | 14 | 1.0000 | 6.0e-15 |
| uniform | diff | 8 | ok | 14 | 1.0000 | 2.8e-15 |
| uniform | stencil | 16 | ok | 15 | 0.9666 | 2.4e-14 |
| uniform | corner | 16 | ok | 15 | 0.9997 | 2.7e-07 |
| uniform | mean | 16 | ok | 15 | 1.0000 | 2.4e-14 |
| uniform | diff | 16 | ok | 15 | 1.0000 | 3.9e-14 |
| uniform | stencil | 32 | ok | 16 | 0.8665 | 6.1e-16 |
| uniform | corner | 32 | ok | 16 | 0.9994 | 8.1e-09 |
| uniform | mean | 32 | ok | 16 | 1.0000 | 1.5e-16 |
| uniform | diff | 32 | ok | 16 | 1.0000 | 1.2e-15 |
| uniform | stencil | 64 | ok | 17 | 0.4655 | 5.5e-16 |
| uniform | corner | 64 | ok | 16 | 0.9989 | 1.6e-08 |
| uniform | mean | 64 | ok | 16 | 1.0000 | 9.6e-16 |
| uniform | diff | 64 | ok | 16 | 1.0000 | 2.0e-16 |
| uniform | stencil | 128 | negative energy direction | 1 | -1.1385 | 1.4e-15 |
| uniform | corner | 128 | ok | 16 | 0.9978 | 3.6e-08 |
| uniform | mean | 128 | ok | 16 | 1.0000 | 1.4e-15 |
| uniform | diff | 128 | ok | 16 | 1.0000 | 1.2e-15 |

### V. Verdicts (k = 8–64; extension k = 128 separately)

| hypothesis | frozen plan | D3 sensitivity |
|---|---|---|
| primary verdict, interface (mean / diff) | inconclusive (inconclusive / inconclusive) | support (support / support) |
| H1 interface | inconclusive | support |
| H2 interface (mean / diff) | inconclusive / inconclusive | support / support |
| H2E interface (mean / diff) | inconclusive / inconclusive | support / support |
| companion verdict, uniform (mean / diff) | inconclusive (inconclusive / inconclusive) | inconclusive (inconclusive / inconclusive) |
| H1 uniform | inconclusive | inconclusive |
| H2 uniform (mean / diff) | inconclusive / inconclusive | inconclusive / inconclusive |
| H2E uniform (mean / diff) | inconclusive / inconclusive | inconclusive / inconclusive |
| H3 | inconclusive | inconclusive |
| H4 | inconclusive | inconclusive |
| H5 | support | support |
| extension H3_64_128 | inconclusive | inconclusive |
| extension H4_at_128 | inconclusive | inconclusive |
| extension H5_at_128 | inconclusive | inconclusive |
| extension H1 at 128, uniform | inconclusive | inconclusive |
| extension H1 at 128, interface | inconclusive | inconclusive |

### E. E29 reuse (uniform layout, §5.6)

| k | stencil control reproduced | diff control reproduced | corner: E29 C in T21 range | mean: E29 C in T21 range | diff bias E29 | diff bias T21 (reported iterate) | T21 iterate | abs. difference (reported iterate) | abs. difference (target iterate) |
|---|---|---|---|---|---|---|---|---|---|
| 8 | True | True | True | True | 1.119e-06 | 1.119e-06 | smallest residual (tight iterate, outer step 4) | 2.123e-15 | 3.129e-15 |
| 16 | True | True | False | True | 1.127e-06 | 1.127e-06 | smallest residual (tight iterate, outer step 5) | 6.656e-16 | 7.987e-15 |
| 32 | True | True | False | True | 1.130e-06 | 1.130e-06 | smallest residual (tight iterate, outer step 14) | 4.235e-22 | 8.856e-16 |
| 64 | True | True | True | True | – | – |  | – | – |

### L. Dependence of the resolved values on lambda_lb (summary.json → lambda_sensitivity; descriptive)

| pass | quantity | resolved values with a residual bound | smallest factor | at | factors < 10 | factors < 100 |
|---|---|---|---|---|---|---|
| frozen_plan | D | 116 | 1.67e+08 | interface k = 64, diff, fp32_control rep. 1 | 0 | 0 |
| frozen_plan | e | 116 | 257 | interface k = 8, diff, coefficient | 0 | 0 |
| sensitivity_D3 | D | 140 | 1.67e+08 | interface k = 64, diff, fp32_control rep. 1 | 0 | 0 |
| sensitivity_D3 | e | 140 | 13.2 | interface k = 64, diff, coefficient | 0 | 2 |

### M. D3 estimator against the observed change from the target to the later saved iterate (summary.json → D3_model_check; descriptive)

| layout | k | form | r_pre / r_target | U^C (D3) | observed ΔC | observed / U^C | U^E (D3) | observed ΔE | observed / U^E | D resolved with max(D3, observed) | e resolved with max(D3, observed) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| uniform | 8 | corner | 184 | 1.287e-13 | 9.164e-15 | 0.0712 | 1.543e-13 | 4.431e-14 | 0.287 | True | True |
| uniform | 8 | diff | 205 | 2.984e-13 | 1.006e-15 | 0.00337 | 3.062e-13 | 4.130e-14 | 0.135 | True | True |
| uniform | 8 | mean | 168 | 2.669e-13 | 1.788e-15 | 0.0067 | 3.472e-13 | 4.233e-14 | 0.122 | True | True |
| uniform | 8 | stencil | 63 | 1.062e-12 | 3.976e-13 | 0.375 | 1.109e-12 | 5.813e-13 | 0.524 | True | True |
| interface | 16 | corner | 137 | 1.840e-13 | 6.993e-16 | 0.0038 | 2.013e-13 | 3.841e-14 | 0.191 | True | True |
| interface | 16 | diff | 155 | 2.033e-13 | 1.166e-16 | 0.000573 | 2.097e-13 | 3.741e-14 | 0.178 | True | True |
| interface | 16 | mean | 124 | 9.051e-14 | 2.331e-16 | 0.00258 | 1.271e-13 | 3.764e-14 | 0.296 | True | True |
| interface | 16 | stencil | 43 | 4.203e-13 | 6.877e-13 | 1.64 | 4.398e-13 | 7.069e-13 | 1.61 | True | True |
| uniform | 16 | corner | 127 | 7.933e-13 | 1.331e-15 | 0.00168 | 8.918e-13 | 8.371e-14 | 0.0939 | True | True |
| uniform | 16 | diff | 115 | 9.593e-14 | 7.321e-15 | 0.0763 | 3.833e-13 | 8.299e-14 | 0.217 | True | True |
| uniform | 16 | mean | 157 | 1.263e-12 | 3.772e-15 | 0.00299 | 1.292e-12 | 8.423e-14 | 0.0652 | True | True |
| uniform | 16 | stencil | 57 | 3.781e-12 | 1.478e-12 | 0.391 | 3.822e-12 | 1.527e-12 | 0.399 | True | True |
| interface | 32 | corner | 120 | 2.904e-13 | 2.326e-16 | 0.000801 | 3.426e-13 | 7.301e-14 | 0.213 | True | True |
| interface | 32 | diff | 119 | 5.209e-13 | 3.489e-16 | 0.00067 | 5.435e-13 | 7.510e-14 | 0.138 | True | True |
| interface | 32 | mean | 115 | 1.444e-13 | 0.000e+00 | 0 | 2.050e-13 | 7.660e-14 | 0.374 | True | True |
| interface | 32 | stencil | 46 | 2.912e-14 | 2.211e-13 | 7.59 | 5.433e-13 | 3.480e-13 | 0.64 | True | True |
| uniform | 32 | corner | 135 | 1.849e-12 | 4.428e-15 | 0.00239 | 1.924e-12 | 1.712e-13 | 0.089 | True | True |
| uniform | 32 | diff | 116 | 9.653e-14 | 8.856e-16 | 0.00917 | 2.446e-13 | 1.622e-13 | 0.663 | True | True |
| uniform | 32 | mean | 125 | 1.333e-12 | 2.657e-15 | 0.00199 | 1.390e-12 | 1.683e-13 | 0.121 | True | True |
| uniform | 32 | stencil | 46 | 6.604e-12 | 3.390e-12 | 0.513 | 6.759e-12 | 3.485e-12 | 0.516 | True | True |
| interface | 64 | corner | 123 | 9.286e-14 | 9.298e-16 | 0.01 | 1.867e-13 | 1.489e-13 | 0.798 | True | True |
| interface | 64 | diff | 136 | 1.848e-13 | 0.000e+00 | 0 | 2.910e-13 | 1.701e-13 | 0.585 | True | True |
| interface | 64 | mean | 128 | 1.731e-13 | 2.324e-16 | 0.00134 | 2.241e-13 | 1.523e-13 | 0.68 | True | True |
| interface | 64 | stencil | 46 | 8.949e-13 | 6.269e-13 | 0.701 | 1.147e-12 | 8.121e-13 | 0.708 | True | True |
