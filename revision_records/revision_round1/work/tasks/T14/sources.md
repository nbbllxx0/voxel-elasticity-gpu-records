# T14: Source verification (CMAME 2020 112847, NVIDIA cuDSS, R1.1 context block)

Serves A.3, R1.1, R1.2, R2.1 and R2.2. This task made no language-model calls. Its only GPU-toolkit use is NVRTC compilation to PTX (no kernel launch, no GPU memory).

## How this file is built

Each cited fact carries a quote id (K…, C…, T…, TC…, H…, W…, L…, A…). The id maps to an entry in `quotes.json`, which gives the verbatim quote, its location in the original source and the local copy it was checked against. `verify_quotes.py` collapses whitespace and otherwise requires an exact match. Its output is `quote_check.json`, which reports **131/131 quotes found verbatim**. It also checks two kinds of location: each Träff et al. quote whose location names a section (31 quotes) must lie in that section of the page text, as delimited by the paper's numbered headings; each code quote whose location gives line numbers (30 quotes) must occur within those lines. 0 location problems. Run on the previous `quotes.json`, the section check flags exactly T33, T34 and T37, which that version placed in Section 4.1 (corrected below). `python -I verify_quotes.py --selftest` plants one fault per case (wrong section, wrong code line, altered quote, missing support map, unknown id) and confirms each is caught.

`literature_block.json` has 24 entries. Its scope differs by kind:
- The 16 published-figure `rows` each carry a per-claim `support` map from every part of the row (code, device, size, workload, value) to the quote ids that back it. `verify_quotes.py` checks that these ids exist, verify, and equal the row's `quote_ids`.
- The four `device_specs` entries and the four `released_code` entries carry quote lists only, with no per-claim map. For them the script checks only that every listed id exists and verifies.
- 0 id problems over the 24 entries. Whether a quote covers the claim it backs was judged by reading each entry against its passages; the substring test cannot judge that. `code_checks.py` → `code_checks.json` holds the code checks (Träff iteration cap, Hou kernel precision) and the arithmetic on Träff's extrapolations. `fetch_sources.sh` lists the retrievals. Retrieval date: 23 Nov 2026, which goes in "accessed" fields only and never in the paper text.

Facts that could not be tied to a verbatim location are listed under "Dropped / unverified" (Section 5) and must not be cited.

---

## 1. CMAME 2020;362:112847 (DOI 10.1016/j.cma.2020.112847)

**Bibliographic record** (Crossref record `fetched/crossref_10.1016_j.cma.2020.112847.json`; Elsevier metadata `fetched/elsapi_S0045782520300281.xml`):
- Title: "A method using successive iteration of analysis and design for large-scale topology optimization considering eigenfrequencies" [K1]
- Authors: Zhan Kang, Jingjie He, Lin Shi, Zhaohui Miao [K2–K5]
- Computer Methods in Applied Mechanics and Engineering, vol. 362 [K7], article 112847, issue dated 15 April 2020 [K6]
- PII S0045782520300281. The Elsevier record says `openaccess 0`, so the paper is closed access.

**Problem class: eigenfrequency, not compliance.** The title says "considering eigenfrequencies" [K1]. The abstract says:
> "Repeatedly solving the generalized eigenvalue problems by far dominates the computational cost in large-scale topology optimization involving natural frequency constraints." (Abstract, sentence 1) [K8]

> "This study proposes a method for dynamic topology optimization problems considering natural frequencies using successively executed iterations for the structural analysis and design." (Abstract, sentence 2) [K9]

**What it shows about inexact intermediate analyses** (abstract only):
> "By using the Rayleigh quotients as approximations of the natural frequencies and achieving sequential approximation of the eigenpairs through inverse iteration-like procedures to improve the eigenvectors along with the topological evolution of the structure, the method avoids solving the time-consuming eigenvalue problem in each design iteration." (Abstract, sentence 3) [K10]

> "The convergence property of the method is analyzed under the assumption of sufficiently small design changes between two successive design iterations." (Abstract, sentence 5) [K11]

> "Numerical examples regarding frequency and frequency gap constraints show that this method is able to realize concurrent convergence of the eigenvalue analysis and design optimization, and is more efficient than the conventional double-loop approach." (Abstract, last sentence) [K12]

**Source of the abstract.** ScienceDirect returned HTTP 403 to automated access, and the Elsevier API returned metadata without an abstract. The abstract text comes from the Semantic Scholar record (`fetched/s2_10.1016_j.cma.2020.112847.json`), which reproduces the publisher abstract and begins with "Abstract". The full text was not read. Before submission, the authors should check the wording against the ScienceDirect abstract page.

**Limits for the R2.2 response:**
- The abstract does not contain the words "compliance", "adjoint" or "state equation". An absence check against the stored abstract confirmed this.
- The reviewer paraphrases the paper as showing that "state equations and adjoint sensitivity equations might not necessarily be solved exactly". That goes beyond what the abstract states.
- The verified statement is narrower. The method uses approximate eigenpairs: Rayleigh-quotient frequencies and inverse-iteration-like eigenvector updates carried along with the design. It avoids an exact eigen-solve at every design iteration. Its convergence is analysed for small design changes, and its examples converge the eigen-analysis and the design concurrently for frequency and frequency-gap constraints.
- Not verified, so do not state:
  - the objective function;
  - whether a static compliance or state solve is included;
  - solver type, tolerance, hardware or precision;
  - problem sizes or speedups.

Suggested bib entry (fields from Crossref):
```
@article{kang2020successive,
  author  = {Kang, Zhan and He, Jingjie and Shi, Lin and Miao, Zhaohui},
  title   = {A method using successive iteration of analysis and design for large-scale topology optimization considering eigenfrequencies},
  journal = {Comput. Methods Appl. Mech. Eng.},
  volume  = {362},
  pages   = {112847},
  year    = {2020},
  doi     = {10.1016/j.cma.2020.112847}
}
```

---

## 2. NVIDIA cuDSS documentation

Pages: https://docs.nvidia.com/cuda/cudss/latest/ (landing page, Getting Started, Data Types, Functions, Advanced Features, Tips and tricks, Release Notes). Local text copies are in `fetched/cudss/*.txt`. The newest release-notes entry at retrieval was **cuDSS v1.0.0** [C29]. The page title is "NVIDIA cuDSS: A high-performance CUDA Library for Direct Sparse Solvers" [C30].

**What it does.**
> "NVIDIA cuDSS is a library of GPU-accelerated linear solvers with sparse matrices." (landing page) [C1]

The library solves AX = B "with a sparse matrix \(A\), right-hand side \(B\) and unknown solution \(X\) (could be a matrix or a vector)." [C2]

> "cuDSS is following a commonly used multi-stage approach in sparse direct solvers. The process of solving a linear system is split into several phases: reordering and symbolic factorization, numerical factorization (and, optionally, refactorization) and solving (with optional iterative refinement)." (Getting Started, cuDSS Workflow) [C10]

- **Input is an assembled sparse matrix in CSR form:** `cudssMatrixCreateCsr()` [C11]; "Input sparse matrix (CSR):" (Functions, cudssExecute()).
- **Matrix types:** "Real/complex general/symmetric/positive-definite (incl. complex symmetric) sparse matrices" [C3]. For SPD: "Symmetric positive-definite matrix Cholesky factorization will be computed with optional local pivoting" [C27].
- **Factors reused across right-hand sides:** "Single and multiple right-hand sides" [C5]. Also: "During the factorization phase, numerical factorization is performed and during the solve phase, the factorization is used to find the solution to the linear system." [C12]
- **Memory:** "Memory and flops estimates for factorization after the analysis phase" [C8]. In the default mode, "L and U factors (which comprise the largest part of the total device memory consumed by cuDSS) must fit into the device memory". An optional hybrid host/device memory mode lifts that limit (Advanced Features) [C28].
- **Platform:** Windows is supported: "and Windows (x86_64)" [C9].

**Precisions.**
- > "Single, double, and double-double (experimental) precision datatypes for values and int and int64_t datatypes for indices" (landing page) [C4]
- Mixed precision through downcast factors, added in v1.0.0: "Added CUDSS_CONFIG_DOWNCAST_FACTORS to store double-precision factors in single precision" (Release Notes v1.0.0) [C26]. The setting "Controls whether cuDSS stores the double-precision factors in single (reduced) precision after factorization, releasing the full-precision factors. When disabled (the default) the factors are kept in full precision." [C22]
  > "Numerical factorization is performed in the matrix value precision. Iterative refinement is also computed in the matrix value precision." [C23]

  > "CUDSS_R_64F right-hand side and solution matrices run a mixed-precision solve with double-precision arithmetic, single-precision off-diagonal factor sources, and retained double-precision diagonal factor sources." [C24]

  > "CUDSS_R_32F right-hand side and solution matrices run the entire solve in single precision over the downcast factors." [C25]

**Iterative refinement option.**
- `CUDSS_CONFIG_IR_N_STEPS`: "Maximum number of steps during the iterative refinement." [C16] Its default is 0 [C17], so refinement is off unless set.
- `CUDSS_CONFIG_IR_TOL`: "In each iteration, the relative residual norm is computed as \(||r||_2 / ||b||_2\) where \(r = b - Ax\)." [C18] Also: "The refinement terminates early if the residual norm is less than the specified tolerance." [C19]
- On failure: "If the tolerance is not met after all iterations, CUDSS_STATUS_IR_FAILED is returned." [C20]
- Default tolerance: "Default value: 0.0 (tolerance checking disabled)" [C21].
- Refinement runs in the matrix value precision [C23]. It is a correction step on top of the direct factors, not a Krylov iteration.

**Refactorization and reuse when the values change.**
> "Re-using the analysis results is supported. Users can change matrix values and only need to run the (re-)factorization and solve phases." (Functions, cudssExecute()) [C13]

> "Re-using analysis (reordering and symbolic factorization) and numerical factorization by only calling the corresponding phases when the matrix structure or values change (in the latter case, one should call cudssExecute() with CUDSS_PHASE_REFACTORIZATION), respectively." (Tips and tricks) [C15]

> "Numerical re-factorization. Note: For now it is only used if the reordering algorithm is set to CUDSS_REORDERING_ALG_BTF_COLAMD or CUDSS_REORDERING_ALG_COLAMD. Otherwise, it is the same as FACTORIZATION phase." (Data Types, cudssPhase_t) [C14]

**What this supports for R2.1, as documentation facts only:**
- cuDSS factorizes an assembled CSR matrix. The symbolic analysis can be reused while the sparsity pattern is fixed [C13, C15].
- Every change of matrix values needs a new numerical factorization. With the default reordering, the refactorization phase "is the same as FACTORIZATION phase" [C14]. A SIMP design update changes the values at every design iteration, so cuDSS would refactorize once per design iteration. That last step is our inference from [C13–C15], not a statement in the documentation.
- One set of factors serves several right-hand sides [C5, C12].
- Refinement is optional, is off by default, and is computed in the matrix value precision [C16–C23].
- FP32 factor storage with an FP64 solve is available from v1.0.0 [C22–C26].
- Not established, so leave unestimated as the plan requires:
  - cuDSS speed;
  - factor size or fill for our matrices;
  - whether a 24 GB card holds the factors of any of our grids.

No cuDSS run was made.

Suggested bib entry:
```
@misc{nvidiacudss,
  author       = {{NVIDIA Corporation}},
  title        = {{NVIDIA cuDSS}: A high-performance {CUDA} Library for Direct Sparse Solvers},
  howpublished = {\url{https://docs.nvidia.com/cuda/cudss/}},
  note         = {Documentation, release 1.0.0; accessed 23 November 2026}
}
```

---

## 3. R1.1 context block: published figures

The context block is the supplement section "Published large-grid results provide context" (submitted `supplementary.tex:319–326`) together with main text `main.tex:139–142`. A machine-readable version for T29 is in `literature_block.json`. In that file every figure keeps its own code, device and workload.

### 3.1 Träff et al. 2023 (CMAME 410, 116043; DOI 10.1016/j.cma.2023.116043)

Source: the open-access publisher PDF held by the authors, `<project>/references/traff2023.pdf` (CC BY), read in place. Page text is in `src/traff_pages/pNN.txt`. PDF page 1 is a repository cover sheet, so **article page = PDF page − 1**; the locations below use article pages. The abstract matches the OpenAlex and Semantic Scholar records.

**Sizes and times:**
- **Cantilever, Futhark, 100 design iterations.** The mesh is 640 × 320 × 320, "approximately 65.5 million elements" [T3], with filter radius r = 2.5 elements and 100 design iterations [T4]. "Linear cantilever example with 65.5 million elements, volume fraction of V ∗ = 0.1, and filter radius of 2.5 elements." (Fig. 4 caption) [T36]. The Fig. 4 caption (p. 13) says: "Computed using the Futhark implementation on a Nvidia A100 GPU to run 100 design iterations, in 7380 s, approximately 2 h." [T2] Futhark used its OpenCL backend [T39].
  - The paper gives no replicate count for this run. The "single sample" sentence [T15] belongs to the performance study of Fig. 6 (p. 15), so it is not attached to the 7380 s.
- **OpenMP-GPU and OpenMP-CPU full-run times are published estimates, not measurements:** "the OpenMP implementations are estimated to take approximately 2 h (GPU) and 3.15 h (CPU) , by extrapolating the computation time of the first 20 design iterations presented in Fig. 6." (p. 14) [T5]
  - **Not the same workload as the Futhark 7380 s.** The 7380 s run uses filter radius 2.5 elements [T4]. The Fig. 6 series behind the OpenMP estimates uses "a filter radius of 1.5 elements, resulting in possibly different topologies obtained for every mesh size" (Fig. 6 caption, p. 15) [T10]. Cite the estimates as Träff et al.'s estimates and state the filter difference. Do not present them as runs of the Fig. 4 cantilever.
  - **The source states no extrapolation rule, and the obvious one does not reproduce the numbers.** Scaling the 20-iteration times by 100/20 = 5 gives 3.19 h (GPU, from 2300 s) and 5.28 h (CPU, from 3800 s), not 2 h and 3.15 h. Our arithmetic (`code_checks.json`, `traff_extrapolation`) finds that all four published estimates (2 h, 3.15 h, 55 min, 63 min) equal 2.98–3.13 times the matching 20-iteration time. That ratio is our observation, not a rule the source states, and must not be attributed to Träff et al.
- **First 20 design iterations, 65.5M elements, filter radius 1.5 elements [T10], 4 multigrid levels:**
  - Series: "Runtimes for 20 design iterations of a linear elastic minimum compliance cantilever example with a volume fraction of V ∗ = 0.1." [T38] "All shown times are computed using 4 multigrid levels, with the exception of the additional points shown with dashed line and square marks, which are computed using 5 levels." [T32] (both Fig. 6 caption, p. 15)
  - Size: "The slowest implementation is the OpenMP-CPU implementation, solving the problem with 65.5 million elements." [T37]
  - OpenMP-CPU: "20 design iterations in 3800 seconds (63 min)" [T11]
  - OpenMP-GPU: "2300 s (40 min) using the A100 GPU" [T12]
  - Futhark: "2096 s" [T13]
  - All three on p. 15. For this performance study the paper says "results for a single sample are presented" [T15].
- **With a fifth multigrid level:** "The two GPU accelerated implementations perform better for the largest problems if a fifth multigrid level is added." [T33] "These data points are shown as squares in Fig. 6" [T34], so they belong to the same 20-iteration, filter-1.5 series. "the computation times are reduces to 1105 s and 1264 s for Futhark and OpenMP-GPU respectively, reducing the estimated times for the entire optimisation problem to 55 and 63 min respectively." (p. 16) [T14]
- **MBB beam:** "This example contains 41 million elements and was computed in 4 h using the Futhark implementation and a Nvidia A100 GPU as accelerator." (p. 14) [T6]
- **Per operator application:** "the Futhark linear implementation takes 1.316ms for a single matrix–vector product, while the nonlinear case takes 1075.4ms, using 2 million elements on the A100 GPU." (p. 19) [T20, T21]
- **Abstract:** "65.5 million elements in approximately 2 h using a single GPU, while the reference implementation takes approximately 3 h and 10 min using 48 CPU cores." [T1] The Discussion says: "The GPU accelerated implementations both cut this time to 2 h when using a single Nvidia A100 GPU." (p. 21) [T28] For OpenMP-GPU this rests on the extrapolation in [T5].

**Hardware:**
- "The other machine used for testing has a Nvidia A100 GPU (80gb), and an Intel Xeon 6226R CPU, which has 16 cores and 700 Gb of RAM." (p. 15) [T9]
- CPU runs: "a machine with two Intel Xeon 8160 CPUs" (p. 14) [T8].
- Compiler: "the NVIDIA HPC SDK (version 22.5) was used for OpenMP-GPU" (p. 14) [T7].
- The paper does not state the A100 form factor. NVIDIA lists 1,935 GB/s for the 80GB PCIe card and 2,039 GB/s for the 80GB SXM card [A2, A3], so the bandwidth of the card used is not known.
- Träff et al. quote "19.5 TFLOPS for the A100" as double-precision peak [T29]. On NVIDIA's table that is the FP64 Tensor Core figure; the non-tensor FP64 rate is 9.7 TFLOPS [A1].

**Memory:**
- The text gives **no numeric memory values**. Fig. 10 shows GPU memory against mesh size only graphically ("GPU memory usage of the Futhark and OpenMP-GPU implementations as a function of mesh refinement.", p. 19) [T19]. Values read off the plot are not verbatim, so they are **dropped**.
- Verified statements:
  - "This memory usage is the reason that 65 million elements is the limit for the Futhark implementation when using the A100 GPU." (p. 18) [T16]
  - "The OpenMP-GPU implementation has much lower memory usage, enabling it to run on cards with less memory, and solve larger problems." (p. 18) [T17]
  - On the 8 GiB GTX 1080Ti ("the Futhark implementation tested on a 1080Ti card with 8GiB, shown in Fig. 6", p. 18) [T35], Futhark "runs out of memory when run with more than 8 million elements" (p. 18) [T18].
- **The 65 million is a rounded statement, not an exact maximum.** The demonstrated Futhark mesh on the A100 is 640 × 320 × 320 = 65,536,000 elements [T3, T2], which already exceeds 65×10⁶ taken literally. Report the demonstrated mesh (640 × 320 × 320, about 65.5 million elements) and, if the capacity is cited, keep the authors' approximation: "about 65 million elements, which Träff et al. state is the limit of their Futhark code on the A100". Do not state an exact maximum grid.

**Solver, precision, stopping** (paper and released OpenMP-GPU code; T12 copied the code unmodified from upstream revision b46ed453, see `../T12/gate.json`):
- Paper: "32-bit floating point numbers are used to store the auxiliary vectors, while the matrix operations and multigrid hierarchy are computed using 64-bit floating point numbers." (p. 5) [T22]
- Code types: `typedef double MTYPE; typedef double STYPE; typedef float CTYPE;` (definitions.h:25–27) [TC1]. The fine operator takes `CTYPE` (float) in and out (stencil_methods.c:7–8) [TC7] and accumulates in `MTYPE` (double) locals (stencil_methods.c:31) [TC8].
- Stopping:
  - `const float cgtol = 1e-5; const int cgmax = 200;` (top3d.c:82–83, hard-coded) [TC2]. **Only the tolerance reaches the solver.**
    - `cgmax` is a parameter of `top3dmgcg` (stencil_optimization.c:15–16) [TC13]. It is not used anywhere else in that file (`code_checks.json`, `traff.cgmax`).
    - The only solver call passes `cgtol` and no cap (stencil_optimization.c:155–156) [TC12].
    - The solver signature has no cap argument (stencil_solvers.c:259–262) [TC11].
  - **Executed iteration cap: 1000.** `const int maxIter = 1000;` (stencil_solvers.c:334) [TC9] is enforced by `for (int iter = 0; iter < maxIter; iter++) {` (stencil_solvers.c:338) [TC10]. The value 200 in top3d.c is declared but never takes effect.
  - FP32 recursive residual `r[i] -= alpha * q[i];` (stencil_solvers.c:377) [TC4]
  - FP64 iterate `u[i] += (STYPE)(alpha * p[i]);` (stencil_solvers.c:373) [TC3]
  - `const CTYPE relres = rnorm / bnorm;` (stencil_solvers.c:384) [TC5] and `if (relres < tol) break;` (stencil_solvers.c:393–394) [TC6]

  The stop is therefore a recursively updated FP32 residual relative to ‖b‖ below 1e-5, with at most 1000 CG iterations per state solve.
- **Coarse levels:**
  - "For the OpenMP implementations, the used coarse space matrices are not the Galerkin projections shown in algorithm 1 lines 1–3" (p. 5) [T23]. Instead the stiffness is assembled on the coarse grid with multiresolution densities.
  - The Galerkin construction belongs to the Futhark code: "For the coarse levels in the multigrid preconditioner, the Galerkin projection of the matrices is constructed and stored in memory." (p. 7) [T30]
  - OpenMP uses CHOLMOD on the coarsest level: "The OpenMP implementations, on the other hand, use a direct solution strategy for the coarsest level, using the Cholmod package to implement the factorisation and back substitution" (p. 6) [T24].
  - The reason given: "As the multigrid method generally performs better with a direct solution on the coarse space, it was chosen for the OpenMP implementations." [T31]
  - The cost: "The direct solver comes at the cost of transferring data between the CPU and GPU every time the preconditioner is applied." (p. 7) [T25]
  - This is the published example the R2.1 answer can cite for "a direct coarse solve complementing the iterative method".
- **Operator:** "In order to update all nodes in the finite element mesh independently, a nodal traversal approach is used." (p. 7, Eq. 11) [T26]. The passage gives the nodal traversal only, not a neighbour count.
  - **27 is a count from the released code, not from the paper.** The fine-grid operator `applyStateOperator_stencil` in `stencil_methods.c` loads its neighbour data with 27 `loadStencilInput` calls between lines 50 and 388, the first with offset `{0, 0, 0}` [TC14] and the last with `{-1, 1, 1}` [TC15]. Their 27 offset triples are distinct and are exactly {−1, 0, 1}³ (`stencil_offsets.py` → `stencil_offsets.json`; the file has no other such call).
  - "27-neighbour" is the manuscript's name for this organization; Träff et al. do not use it.

### 3.2 Hou et al. 2025 (FEAD 250, 104388; DOI 10.1016/j.finel.2025.104388)

- **Bibliographic record:** title [H1] and vol. 250 [H2] are confirmed by Crossref. Authors are Jiangnan Hou, Jiajie Li, Shengfeng Zhu, Xindi Hu and Zeyang Yu (Crossref author list in `fetched/crossref_10.1016_j.finel.2025.104388.json`). The paper is closed access (Elsevier metadata `openaccess 0`).
- **Largest example, 63 million elements: verified in the abstract.**
  - Source: the ScienceDirect article-preview page saved in the authors' earlier pre-submission audit (`manuscript/fead1.1/tmp/presubmission_audit_20261009_134801/exemplars/recent_hou2025_preview.txt`, abstract at lines 55–56). It is copied unmodified to `fetched/archived/recent_hou2025_preview.txt`.
  - The page identifies the paper as FEAD vol. 250, article 104388 [H11], with the same title [H12] and DOI [H13].
  - **CuPy:** the title names it ("Parallel computing on GPU with CuPy and vectorized SpMV for large-scale topology optimization") [H12], and the Numerical experiments snippet confirms it: "CuPy is chosen for its convenience since it shares the same syntax as NumPy when using a GPU." (line 80 of the saved preview) [H24].

  > "Numerical examples of topology optimization on GPU, such as heat transfer and structural design, in both 2D and 3D with up to 63 million elements illustrate the effectiveness and efficiency of the proposed approach." (Abstract) [H10]

  - The figure is the **maximum over all published examples**: heat transfer and structural design, in 2D and 3D.
  - The abstract does not say which physics or dimension the 63-million-element example has, nor which device it ran on. It therefore does not support a statement that ties 63×10⁶ elements to elasticity specifically.
- **Published account of hardware and precision** (Numerical experiments snippet, line 80 of the saved preview):

  > "The experimental equipment includes a laptop Lagion R7000 2020 with GPU Nvidia GeForce GTX 1650 (Video RAM (VRAM) 4.0 GB) and CPU AMD Ryzen 7 4800H (RAM 16.0 GB), and a workstation Precision T7920 with GPU Nvidia GeForce GTX 3090 GPU (VRAM 24.0 GB) and CPU Xeon(R) Gold 6230R (RAM 128.0 GB)." [H23]

  > "The sensitivities are processed in double precision, and all other data are processed in single precision." [H22]

  - Two test machines are named ("GTX 3090" is the source's wording). The accessible text does not say which one ran the 63-million-element example, so **the device for that example stays unspecified**.
  - The published account says that everything except the sensitivities is single precision. The released kernels (below) evaluate their arithmetic in FP64 when compiled. Both facts must be reported side by side.
- **Released code facts** (revision d8dca7a, the authors' read-only copy in `<project>/external/CuPy-for-TO`):
  - **24 generated element-row kernels:** `for mulj in range(24):` (SpMV.py:10) [H7], over 24 `cp.ElementwiseKernel`s with signature `'float32 x,raw int32 t,raw float32 y',` (ker.py) [H8]. **The signature establishes FP32 storage, not FP32 arithmetic.**
  - **Storage:** the kernel output is `'float32 z'` [H14]. The displacement [H18], load [H19] and accumulation vectors [H20] are FP32 CuPy arrays, so the CG vector operations are FP32.
  - **Literals:** inside each kernel the stiffness coefficients are unsuffixed decimal literals, e.g. `z = x +0.207570207570 *y[u]` (ker.py:9–11) [H14]. `kernel_writer.py` regenerates ker.py at run time [H17] and writes each coefficient as `str()` of an FP64 value truncated to 15 characters [H15, H16].
  - **Typing:** under C++ rules an unsuffixed literal is `double`. Each product, and the sum with `x`, is therefore evaluated in FP64 and rounded to FP32 only on assignment to `z`.
  - **Check** (`code_checks.json`, `hou`):
    - All 24 kernels have FP32 inputs and outputs, and none of their 576 coefficient literals has an `f` suffix.
    - Each kernel body was compiled verbatim with NVRTC to PTX (compute_89) inside a stand-in function with the same argument types. All 24 contain FP64 instructions and one FP64→FP32 conversion.
    - With `f`-suffixed literals as a control, none contains FP64 instructions.
    - The stand-in reproduces the argument types CuPy declares, not CuPy's generated wrapper itself.
    - **Scope of the check:** it shows how the released expressions compile in that stand-in wrapper. It cannot establish which arithmetic ran in the published benchmarks, which the paper describes as single precision apart from the sensitivities [H22].
  - **Net precision of one operator application in the released code:** each element-row kernel forms its 24 products and their sum in FP64 and rounds the result to FP32. The 24 kernel results are chained through FP32 storage (`sumsub = add_r[mulj](sumsub,tunion, Ab0j)`, SpMV.py:14) [H21]. For the released code, "FP32 operator arithmetic" is incorrect; the accurate description is "FP32 storage with FP64 evaluation inside each element-row kernel".
  - **How to word it:** "Hou et al. report single-precision processing of all data except the sensitivities [H22]; in their released code the element-row kernels store FP32 but evaluate their unsuffixed coefficient products in double precision." Do not claim either description for the published timings beyond what [H22] states.
  - **Unpreconditioned CG:** `r1 = r0 - alpha * Ap` then `if (cp.linalg.norm(r1) < tol):` (CG.py:30–31) [H4]. The loop has no preconditioner.
  - **Tolerance:** `tol=0.001;` (main.py:10) [H5], cap of 10000 iterations (FE.py:26) [H6].
  - **Note for T29: the tolerance is relative to the initial residual of each solve**, `tol = cp.linalg.norm(r0) * tol` (CG.py:20) [H3], not relative to ‖b‖.
  - **Plane-stress Lamé parameter:** `lambdaa =E*nu/((1+nu)*(1-nu))` (materialInfo.py:6) [H9].

### 3.3 Wang et al. 2025 (SMO 68, 174; DOI 10.1007/s00158-025-04127-3)

Source: the Springer abstract (`fetched/springer_wang2025.html`).
> "This paper presents an efficient MATLAB framework for large-scale density-based topology optimization and porous infill optimization in 3D." [W3]

> "this framework supports significantly larger models with up to 128 million hexahedral simulation elements on a standard PC equipped with 64 GB RAM." [W1]

> "A tailored element-based matrix-free computing stencil is demonstrated to circumvent the vast memory consumption in large-scale FEM." [W2]

> "All code is made publicly available at https://github.com/PSLer/TOP3D_XL" [W4]

The abstract gives no run time.

### 3.4 Liu et al. 2018 (ACM TOG 37(6); DOI 10.1145/3272127.3275012)

Source: the publisher-deposited abstract in the Crossref record. Title: "Narrow-band topology optimization on a sparsely populated grid" [L4]. The method simulates "elastic deformation in a dynamic narrow-band region around high-density sites" [L3].
> "Our technique accommodates computational domains with over one billion grid voxels on a single shared-memory multiprocessor platform" [L1]

> "We have also designed a mixed-precision multigrid-preconditioned iterative solver that keeps the memory footprint of the simulation to a compact size while maintaining double-precision accuracy." [L2]

---

## 4. Manuscript statements checked (submitted FEAD 1.3)

| Location | Statement | Verdict | Action for the writer |
|---|---|---|---|
| supplementary.tex:321 | Träff et al. run 100 iterations at 65.5×10⁶ elements on an A100 with 80 GB in about two hours with Futhark | **Supported** [T2, T3, T9, T36] | Keep. The measured figure is 7380 s; the paper gives no replicate count for it. If a capacity is added, give the demonstrated 640 × 320 × 320 mesh and keep Träff et al.'s rounded "65 million elements is the limit" [T16] as their approximate statement, not an exact maximum. |
| supplementary.tex:322 | OpenMP time extrapolated to about two hours from its first 20 iterations | **Supported as Träff et al.'s published estimate** [T5, T12]. The 20 iterations behind it use filter radius 1.5 elements [T10], not the 2.5 elements of the 100-iteration Futhark run [T4]. The source states no extrapolation rule, and 5× the 20-iteration time gives 3.19 h, not 2 h. | Keep, attributed as "estimated by Träff et al.", and say that the estimate comes from a series with a 1.5-element filter. Do not present it as a run of the same cantilever, and do not rederive it. |
| supplementary.tex:323 | Released OpenMP GPU solver: Krylov vectors FP32, displacement FP64, element arithmetic FP64, stops on a recursively updated FP32 residual below 10⁻⁵ | **Supported** [TC1–TC8, T22]. The executed cap is 1000 CG iterations [TC9, TC10]. The declared `cgmax = 200` never reaches the solver [TC2, TC11–TC13]. | Keep. If useful, add "relative to ‖b‖" [TC5]. If a cap is quoted anywhere (e.g. T12, T29), quote 1000, not 200. |
| main.tex:141 | Both closest codes stop on a recursively updated residual | **Supported for Träff's OpenMP-GPU code and Hou's code** [TC4–TC6, H4]. Not checked for Träff's Futhark code. | Attribute the recursive stop to the released OpenMP-GPU code, not to "Futhark and OpenMP". |
| main.tex:142 | "Our multigrid hierarchy follows the structured-voxel construction of Träff et al., with Galerkin coarse operators" | **Ambiguous.** Träff's OpenMP coarse matrices are stated *not* to be Galerkin projections [T23]; their Futhark code uses Galerkin [T30]. | Word it so that "Galerkin" describes our hierarchy (or Träff's Futhark code), not their OpenMP code. |
| main.tex:141, supplementary.tex:547 | 27-neighbour operator of the published OpenMP code | **Supported by the released code.** Its fine-grid operator loads 27 distinct neighbour offsets, exactly {−1, 0, 1}³, in the 27 `loadStencilInput` calls of `stencil_methods.c:50–388` [TC14, TC15; count in `stencil_offsets.json`]. The 27 is a count from the code; the paper describes only a nodal traversal [T26] and gives no count. The name "27-neighbour" is ours. | Keep as our label, as a description of the released code. Do not attribute the count or the name to Träff et al.'s paper. |
| supplementary.tex:325 | Wang et al. reach 1.28×10⁸ hexahedra on a PC with 64 GB using matrix-free MATLAB | **Supported** [W1–W4] (MATLAB framework, density-based TO and porous infill in 3D [W3]; code TOP3D_XL [W4]) | Keep. |
| supplementary.tex:325 | Liu et al. exceed 10⁹ background voxels "on one shared-memory CPU" | **Partly supported.** The source says "a single shared-memory multiprocessor platform" [L1]. | Replace "one shared-memory CPU" with "a single shared-memory multiprocessor platform". |
| main.tex:141; supplementary.tex:326 | Hou et al. reach / report up to 63×10⁶ elements | **Supported as the maximum over their examples** [H10] (abstract). The abstract does not give the physics, dimension or device of that example. | Keep the number, worded as "examples (heat transfer and structural, 2D and 3D) with up to 63×10⁶ elements". In main.tex:141, do not tie it to "voxel elasticity on one GPU". The paper names two test machines [H23] but the accessible text does not assign the largest example to either; leave its device unspecified. |
| supplementary.tex:496 | Hou code: 24 generated element-row kernels, unpreconditioned FP32 CG, recursive residual 10⁻³ | **Supported** [H3–H8, H18–H21]. The CG vectors are FP32. The element-row kernels evaluate in FP64 and store FP32 [H14–H16]. | Keep. Add "relative to the initial residual" [H3], which matters when true residuals are compared with ours. Describe the precision at two levels: Hou et al. state that all data except the sensitivities are single precision [H22]; the released kernels store FP32 but evaluate in FP64 when compiled (our check). Do not call the released operator's arithmetic FP32, and do not claim which arithmetic ran in their published benchmarks. |
| supplementary.tex:374 | A100 "9.7 TFLOP/s of scalar FP64 and 2.04 TB/s" (hypothetical port) | **Supported** for the 80GB SXM card [A1–A3] | Keep as an NVIDIA specification. Do not attribute 2.04 TB/s to Träff's card, whose form factor is unstated. |

---

## 5. Dropped / unverified

1. **Hou et al. "63×10⁶ elements": no longer dropped.**
   - The previous version dropped the figure because live retrieval failed:
     - ScienceDirect: HTTP 403;
     - Elsevier API: no abstract;
     - Crossref, OpenAlex and Semantic Scholar: no abstract;
     - ECNU Pure: captcha;
     - arXiv: HTTP 429.
   - That advice was wrong. The authors' earlier audit had saved the ScienceDirect preview, and its abstract gives the figure verbatim [H10] (Section 3.2).
   - What remains unverified is the physics, dimension and device of the largest example. The abstract does not state them, and the full text was not accessible.
2. **Träff et al. GPU memory values.** These appear only graphically in Fig. 10 and are dropped. Only the verbal statements [T16–T18] may be cited.
3. **Kang et al. full-text details** (objective, solver, problem sizes, any statement about state or adjoint equations): not accessed, so not cited. Only the abstract statements [K8–K12] are usable.
4. **cuDSS performance, factor memory and capacity for our matrices:** not in the documentation and not measured. Leave unestimated, as the plan for R2.1 requires.
5. **Träff et al. Futhark stopping rule:** not checked, because the Futhark code is not available here.

## Files

- `sources.md`: this file.
- `quotes.json`: every quote with its source file and location.
- `verify_quotes.py` → `quote_check.json`: the verbatim check (131/131), the section and code-line location checks, and the literature-block id cross-check with its scope by entry kind. `--selftest` runs the planted-fault cases.
- `stencil_offsets.py` → `stencil_offsets.json`: the 27 distinct `loadStencilInput` offset triples of the released fine-grid operator (`stencil_methods.c:50–388`). Run: `python -I stencil_offsets.py ../T12/src_TopOpt-in-OpenMP-GPU`.
- `edit_r4.py`: the latest corrections to `quotes.json` and `literature_block.json` (T33, T34 and T37 relocated to Section 4.2; code quotes TC14 and TC15 for the stencil count; CuPy mapped to H12 and H24 instead of H23).
- `code_checks.py` → `code_checks.json`: occurrences of the Träff CG cap, typing of the Hou kernel literals with the PTX check, and the arithmetic on Träff's extrapolations. Run: `python -I code_checks.py ../T12/src_TopOpt-in-OpenMP-GPU ../../../../external/CuPy-for-TO/cupy_for_TO`.
- `fetched/archived/recent_hou2025_preview.txt`: unmodified copy of the ScienceDirect preview of Hou et al. saved in the authors' earlier audit.
- `literature_block.json`: verified published figures for T29. `edit_lit_r3.py` applies the latest corrections to it and to `quotes.json` (demonstrated Träff mesh, Hou precision statement and machines, per-row support maps).
- `fetch_sources.sh`, `html2txt.py`: retrieval and HTML-to-text conversion.
- `fetched/`: Crossref, OpenAlex, Semantic Scholar and Elsevier records, the Springer abstract page, the NVIDIA A100 page and the cuDSS documentation (HTML plus text).
- `src/traff_pages/`: per-page text of the Träff et al. PDF. `src/traff_p20-20.png` is the rendered page with Fig. 10, showing that its memory values are graphical only.
