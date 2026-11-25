# T19: reference-change identity and the weighted eight-cell patch

Numbers are cited to the files of this folder. `coefficients.json` holds the coefficient checks, `summary.json` the
patch checks, `affine.csv` every force (raw, same-input FP64, excess) by node, `local_contributions.csv` every element
contribution, and `node_class_summary.csv` the maxima by node class. The scripts are `t19_common.py` (definitions),
`t19_gpu.py` and `t19_launch.py` (the one GPU job), `t19_analyse.py` and `t19_summarise.py` (CPU). `t19_fix_r8_checks.py`
(CPU) reads `affine.csv` and writes `out/fix_r8/checks.json`: the P2 rotation forces by axis, the axial interface
difference-form action and the inversion-pair check of Section 4. The authors' code is used unchanged (copied into
`src/voxfem`).

## 1. Setting

The free operator is $y=\sum_e E_e\,G_e^{\mathsf T}K_0G_eu$, with the unit element matrix $K_0$ of
`voxfem.core.ke_unit(0.3)` (24×24 trilinear hexahedron on the reference cube $[-1,1]^3$, local node $i$ at sign vector
$s_i\in\{\pm1\}^3$). Notation:

* $T\in\mathbb R^{24\times3}$ repeats a nodal vector at the eight nodes, so $u_e=Tt$ is a translation of the element.
* $Q=\mathrm{fl}_{32}(K_0)$ is the FP32 element matrix that the element kernels hold, and $\Delta=Q-K_0$ is its rounding.
* $P=TT^{\mathsf T}/8$ replaces each component by its element mean.
* An *element reference form* evaluates $f_e=E_eQ\,(u_e-Tr_e)$ with a reference displacement $r_e\in\mathbb R^3$:
  * original element kernel: $r_e=0$;
  * corner reference (`elem_ref`): $r_e=u_{e,0}$, the first local node;
  * mean reference (`elem_mean`): $r_e=\bar u_e=\tfrac18T^{\mathsf T}u_e$, summed pairwise.
* *Stencil forms*: $W_r(n)$ is the 3×3 block coupling node $n$ to $n+r$, formed in FP32 by the kernel from the incident
  moduli. The original stencil evaluates $\sum_rW_ru_{n+r}$, self block included. The difference form evaluates
  $\sum_{r\ne0}W_r(u_{n+r}-u_n)$. The self-block correction evaluates $W_0^{\rm sc}u_n+\sum_{r\ne0}W_ru_{n+r}$ with
  $W_0^{\rm sc}=-\sum_{r\ne0}W_r$ accumulated in FP32.

Three arithmetic levels are kept apart throughout:

* exact rational arithmetic;
* the fixed rounded coefficients ($Q$, or the kernel's $W_r$) applied in FP64 ("coef64");
* the production FP32 kernels' raw output ("fp32").

Every excess is the force minus the same-input FP64 force $\sum_eE_eK_0u_e$, where $K_0$ is `ke_unit` and the input is
the FP32-represented field promoted to FP64. Every row of `affine.csv` also gives the excess over the exact force on the
same input (`exact_excess_*`). For the coefficient forms this is the rounded coefficients evaluated in exact rational
arithmetic. For the FP64 `ke_unit` force and the production FP32 outputs it is the recorded output minus the exact force,
with the difference taken exactly. For the exact-force rows (`K0_exact`) it is 0 by definition.

The *physical force* is the exact matrix applied to the input that is actually applied. Rounding an affine field to FP32
can change it into a field that is no longer exactly affine; the exact force on the represented input is then nonzero
even for a rotation. This physical force is kept apart from the operator error, which is always the excess over the
same input.

## 2. Facts about the rounded element matrix (`coefficients.json`)

* $K_0$ in FP64 differs from the exact integral (sympy, $\nu=3/10$) by at most $1.1\times10^{-16}$. It is not bitwise
  symmetric: 81 pairs differ, by at most $2.8\times10^{-17}$. Under 47 of the 48 cube symmetries it is invariant only to
  within $1.7\times10^{-16}$.
* $Q$ equals the correctly rounded FP32 value of the exact matrix in all 576 entries. It is bitwise symmetric, and it is
  bitwise invariant under all 48 signed permutations of the axes, the three reflections and the inversion included. The
  exact $K_0$ has the same invariance.
* $QT=cT$ holds exactly, with $c=-9/2^{30}=-8.381903171539307\times10^{-9}$. $K_0T=0$ holds exactly. For comparison,
  $\max|\Delta_{ij}|=5.35\times10^{-9}$.
* Hence $QP=cP$ and $PQ=(QP)^{\mathsf T}=cP$, so $PQ-QP=0$ exactly. The mean-reference element operator $A_m=Q(I-P)$ is
  exactly symmetric, since $A_m-A_m^{\mathsf T}=PQ-QP$. The corner-reference element operator $A_c=Q(I-TR_c)$ is not:
  $\max|A_c-A_c^{\mathsf T}|=|c|=8.38\times10^{-9}$, so its skew-symmetric part $(A_c-A_c^{\mathsf T})/2$ has largest
  entry $|c|/2=4.19\times10^{-9}$ (both exact).

## 3. The reference-change identity

For two references of the same element,
$$
f_e^{(1)}-f_e^{(2)}=E_eQT\,(r_e^{(2)}-r_e^{(1)})=c\,E_e\,T\,(r_e^{(2)}-r_e^{(1)}) .
$$
The first equality holds for any $Q$. The second uses $QT=cT$. The exact matrix gives the same element force for every
reference, because $K_0T=0$. The reference enters a rounded form only through $c$. Assembled at node $n$, the excess
$\varepsilon^{R}_n=\sum_{e\ni n}[E_e\Delta(u_e-Tr_e)]_n$ obeys
$$
\varepsilon^{(1)}_n-\varepsilon^{(2)}_n=c\sum_{e\ni n}E_e\,(r_e^{(2)}-r_e^{(1)}) .
$$
The original element kernel is the case $r=0$.

**Check.** In exact rational arithmetic the identity holds for every node, field, layout and input: 0 mismatches in
79,056 component checks, for corner minus mean and for original minus mean (`summary.json` → `identity`). Evaluated in
FP64 with the rounded coefficients, it agrees to $8.8\times10^{-15}$ absolute, or $4.4\times10^{-16}$ of the node's term
scale $\sum|E_eK_{0,ij}u_j|$.

### 3.1 Translations

For $u_e=Tt$, the corner and mean references return $t$ exactly. The corner value is a copy. The pairwise mean
$\big((t+t)+(t+t)\big)+\dots$ forms $2t$, $4t$ and $8t$ exactly, and the factor $0.125$ is exact, provided nothing
overflows. Then $u_e-Tr_e=0$ exactly, every product is zero, and the raw output is zero for any $Q$, any moduli and any
arithmetic. The difference form subtracts equal values, $u_{n+r}-u_n=0$. Neither argument uses symmetry, uniformity or
the size of the rounding. The original forms keep a coefficient-level translation force, plus application rounding in
FP32. For the original element form it is $c\sum_{e\ni n}E_e\,t$. For the original stencil it is its row-sum action
$R_nt$ with $R_n=\sum_rW_r(n)$, and for the self-block correction $R^{\rm sc}_nt$. These equal $c\sum E\,t$ only where
the kernel's rounded row sum happens to be $c\sum E\,I$: at the uniform centre for $E=1$, not for $E=0.7$ (Section 5).

**Raw-output check.** The production FP32 kernels `elem_ref`, `elem_mean` and `stencil_diff` were run on 16
translations: three directions times five amplitudes from $3.7\times10^{-4}$ to $1.2345\times10^{7}$, plus one generic
vector. They covered all four layouts, all 27 nodes and every repeat. All 62,208 raw output entries are exactly zero,
with no negative zeros. At coefficient level the same three forms are also exactly zero
(`summary.json` → `translation_guarantee`). The original forms are not: at unit amplitude, uniform layout, the maximum
raw force is $3.95\times10^{-7}$ for the FP32 original stencil and $1.28\times10^{-7}$ for the FP32 original element
kernel. At coefficient level it is $6.71\times10^{-8}=8|c|$ for both. The FP32 self-block correction gives 0 at
amplitude 1 but $1.79\times10^{-7}$ at amplitude 0.37 (`summary.json` → `translation_by_amplitude`). The FP64
`ke_unit` operator itself returns up to $9.7\times10^{-9}$ for the $1.2345\times10^{7}$ translation.

### 3.2 Affine fields $u=a+Bx$

With node positions in cell-edge units, $r^c_e=a+Bx_{e,0}$ and $r^m_e=a+B\bar x_e$, where $\bar x_e-x_{e,0}=d=(\tfrac12,\tfrac12,\tfrac12)$
for every element. Therefore
$$
\varepsilon^{c}_n-\varepsilon^{m}_n=c\Big(\sum_{e\ni n}E_e\Big)Bd ,\qquad
\varepsilon^{o}_n-\varepsilon^{m}_n=c\sum_{e\ni n}E_e\,(a+B\bar x_e).
$$

* **Corner.** The corner term has the same sign at every node and in every element for a given $B$; it is coherent and
  does not cancel at assembly. On exactly affine inputs this closed form holds to $2.7\times10^{-16}$ relative over
  3,240 node-field pairs, the rounding of the exact excesses to FP64 for the comparison (`summary.json` → `corner_closed_form_exactly_affine_inputs`).
* **Original element form.** In a uniform region the original term is $8Ec\,u(x_n)$: it is proportional to the node's
  absolute displacement. At the uniform interior node, on exactly affine inputs, the original element excess equals
  $8Ec\,u(x_n)$ with zero deviation for $E=1$ and $E=0.7$ (exact excesses rounded to FP64, compared with
  $8Ec\,u$ in FP64)
  (`summary.json` → `uniform_centre_original_forms`). The original *stencil* is a different form with its own terms
  (Section 5).

## 4. Mean reference: cancellation at assembly, not in the element

$$
\varepsilon^m_n=\sum_{e\ni n}E_e\big[\Delta\,(I-P)u_e\big]_n=\sum_{e\ni n}E_e\Big[\textstyle\sum_j\Delta_{ij}\,B\,(x_j-\bar x_e)\Big] ,
$$
with $i$ the local index of $n$ in $e$ and $x_j-\bar x_e=\tfrac12s_j$. The excess depends on $B$ and on the incident
moduli, not on $a$ or on the node position.

**Element level.** The single-element contributions are not zero. In the uniform patch with $u=(x,0,0)$, each incident
cell contributes up to $1.08\times10^{-8}$ to the centre node (`summary.json` → `element_vs_assembled_interior_node`).

**Uniform region: the reflection argument.** Let $G=\{\mathrm{diag}(\pm1,\pm1,\pm1)\}$. Each $R\in G$ maps local node $i$
to the node with sign vector $Rs_i$. Because $Q$, and hence $\Delta$, is invariant under these reflections, the
contribution of the cell in which $n$ has local index $\pi_R(0)$ is $R\,g_0(RBR)$, where $g_0$ is the contribution of
cell 0. The assembled sum $F(B)=\sum_{R\in G}R\,g_0(RBR)$ is a linear map from 3×3 matrices to vectors with
$F(R'BR')=R'F(B)$. A component $F_m$ can depend on $B_{kl}$ only if $R_mR_kR_l=1$ for every sign choice, and no index
triple satisfies that. Hence $F\equiv0$: with equal moduli the eight contributions cancel exactly, for every $B$,
including the infinitesimal rotations. The argument needs only the reflection invariance of $Q$, which holds bitwise.
The same argument gives zero physical force for $K_0$.

Equal moduli in all eight cells are sufficient, not necessary. The inversion $R=-I$ maps each cell to the cell opposite
across the node, and its contribution is $(-I)\,g_e\big((-I)B(-I)\big)=-g_e(B)$: the two cells of an inversion-related
pair give opposite forces at the centre. Equal weights within each of the four pairs therefore suffice, whatever the
weights of the other pairs. In exact rational arithmetic, with pair weights $1$, $1/8$, $7/10$ and $3/1000$, the
assembled mean-reference force of $Q$ at the centre is exactly 0 in every component for all nine gradients
(`out/fix_r8/checks.json` → `inversion_pair_weights_mean_reference_centre`). At the planar interface below, every
inversion pair joins a cell of modulus 1 to a cell of modulus 1/8, so no pair cancels.

**Patch check, exact arithmetic.** For all nine gradients, three strains and three rotations, at the uniform interior
node, on exactly affine inputs, the mean excess is exactly 0. This holds for $E=1$ and for $E=0.7$
(`summary.json` → `survival_affine`, entries `Q_mean`). This is a statement about the rounded coefficients in rational
arithmetic. Applying them in FP64 arithmetic leaves a rounding residue of up to $9.7\times10^{-17}$ ($E=1$) and
$1.1\times10^{-16}$ ($E=0.7$) at that node (`uniform_centre_exact_vs_fp64_application`; Section 8, item 1).

**Planar interface ($E=1$ for $x<x_n$, $E=1/8$ for $x>x_n$).** The moduli split into a uniform part and a part with the
sign of $R_{xx}$. The second part survives where $R_mR_kR_l=R_x$. In the $x$ force that is $B_{xx}$, $B_{yy}$ and
$B_{zz}$. In the $y$ force it is $B_{xy}$ and $B_{yx}$, and in the $z$ force $B_{xz}$ and $B_{zx}$. Both the physical
force and the mean excess follow this pattern exactly: every other component is exactly 0
(`summary.json` → `selection_rule_centre`). The interface excess is therefore not a rounding accident; it is the
part of $\Delta$ that the unequal weights do not cancel. The values for $u=(x,0,0)$, P0 are:

| centre node, $x$ force | uniform | 8:1 interface |
|---|---|---|
| physical (exact) | 0 | 2.355769230769231 |
| original element, coefficient excess | $-6.705522537\times10^{-8}$ $(=8c)$ | $+4.41\times10^{-9}$ |
| corner reference, coefficient excess | $-3.3527612686\times10^{-8}$ $(=4c)$ | $+8.60\times10^{-9}$ |
| mean reference, coefficient excess | 0 (exact) | $+2.745610590\times10^{-8}$ |
| difference form, coefficient excess | 0 (exact) | $+4.21\times10^{-8}$ |
| original stencil, coefficient excess | $-6.71\times10^{-8}$ | $-1.75\times10^{-8}$ |

Source: `summary.json` → `axial_example`. These reproduce the planners' uniform corner value ($-3.35276\times10^{-8}$),
the zero uniform mean excess, the interface force 2.35577 and the interface mean excess ($+2.74561\times10^{-8}$). At
the interface the mean reference loses its advantage.

The physical $y$ and $z$ forces of this field are exactly 0 at the centre in both layouts. The transverse excesses are
not zero for every form (`axial_example` → `centre_yz_excess_exact_by_form`):

* uniform, $E=1$: exactly 0 for the original element, corner, mean, difference and original-stencil forms; the
  self-block correction gives a $y$ excess of $-4.47\times10^{-8}$;
* 8:1 interface: exactly 0 for the original element, corner, mean and difference forms; the original stencil gives a
  $z$ excess of $-1.862645\times10^{-9}$, and the self-block correction $y$ and $z$ excesses of
  $-1.303852\times10^{-8}$ and $+1.862645\times10^{-9}$.

The difference-form part of these transverse components is exactly 0, so they come from the row-sum term $R_nu_n$ with
$u_n=(1,0,0)$: they are the off-diagonal entries $R_n[y,x]$ and $R_n[z,x]$ of the kernel's rounded row sums (and
$R^{\rm sc}_n$ for the self-block correction), which the layout's $y$ and $z$ reflection symmetry would set to zero
(`coefficients.json` → `stencil_blocks.<layout>.centre_row_sum_stencil_kernel`, `centre_row_sum_selfcorr_kernel`).
At the uniform centre with $E=1$ the stencil's row sum is $8cI$ and has no such entries; the self-block correction's
has $R^{\rm sc}_n[x,y]=R^{\rm sc}_n[y,x]=-4.47\times10^{-8}$.

Over the 15 unit-gradient, strain and rotation fields (P0 and P1), the largest interior-interface coefficient excess per
form is as follows, for the two tested 8:1 interfaces: moduli $1\,|\,1/8$ and $0.7\,|\,0.0875$
(`summary.json` → `interface_centre_coef_max_by_form`, layouts `interface` and `interface_s07`):

| form | $1\,\vert\,1/8$: max excess | attained for | $0.7\,\vert\,0.0875$: max excess | attained for |
|---|---|---|---|---|
| original element | $3.77\times10^{-8}$ | $g_{xy}$ | $2.64\times10^{-8}$ | $g_{xy}$ |
| corner reference | $3.76\times10^{-8}$ | $g_{yy}$ | $2.63\times10^{-8}$ | $g_{yy}$ |
| mean reference | $3.76\times10^{-8}$ | $g_{yy}$ | $2.63\times10^{-8}$ | $g_{yy}$ |
| difference form | $4.21\times10^{-8}$ | $g_{xx}$ | $6.02\times10^{-8}$ | $g_{xx}$ |
| original stencil | $8.61\times10^{-8}$ | $g_{yy}$ | $1.10\times10^{-7}$ | $g_{xz}$ |
| self-block correction | $1.68\times10^{-7}$ | $g_{yx}$ | $7.06\times10^{-7}$ | $g_{xz}$ |

The physical forces of the maximising fields at $1\,|\,1/8$ are $(0,0.673,0)$ for $g_{xy}$ and $g_{yx}$,
$(1.010,0,0)$ for $g_{yy}$ and $(2.356,0,0)$ for $g_{xx}$; at $0.7\,|\,0.0875$ they are 0.7 times these. The maxima are
taken across fields, and the maximising field depends on the form: $g_{yy}$ attains it for three forms at $1\,|\,1/8$,
and $g_{xz}$ for two at $0.7\,|\,0.0875$. The element and reference forms scale with the modulus (0.7 times), while the
difference form, the original stencil and the self-block correction grow, because their rounded weights come from the
kernel's FP32 formation for each modulus value. The physical force 2.356 belongs to the axial field $g_{xx}$ alone; its
excesses per form are in the first table of this section.

## 5. Difference form: opposite weights

For $u=a+Bx$, the difference form gives $\sum_{r\ne0}W_rBr$, which is the first moment
$M_{pqk}=\sum_{r\ne0}W_r[p,q]\,r_k$ of its blocks contracted with $B$. The exact operator has zero row sums, so its
action on the same field is the same expression with the exact blocks. The coefficient excess is therefore
$(M^{\rm rounded}-M^{\rm exact})$ contracted with $B$, and it vanishes for every $B$ if and only if the rounded and exact
first moments agree.

* **Homogeneous interior node.** The exact blocks satisfy $W_{-r}=W_r$, by the inversion $-I\in G$, so
  $M^{\rm exact}=0$. The criterion becomes a zero first moment of the rounded blocks, $M^{\rm rounded}_{pqk}=0$ for all
  $p,q,k$, and the excess is $\sum_{r\in H}(\delta_r-\delta_{-r})Br$ over a half set $H$, where
  $\delta_r=W_r^{\rm rounded}-W_r^{\rm exact}$. Equal rounded opposite blocks, $W_{-r}=W_r$, are sufficient for this,
  not necessary: unequal pairs can still cancel in the sum over $r$. At the uniform centre the two conditions give the
  same answer in the production kernel: $M=0$ exactly at $E=1$, and at $E=0.7$ $\max|M|=1.60\times10^{-9}$ with 11 of
  27 entries nonzero (exact sum of the rounded blocks; `summary.json` → `uniform_centre_difference_first_moment`).
* **Interface or boundary node.** The exact first moment is not zero there; it carries the physical force of the
  affine field. Zero affine excess needs the rounded and exact first moments to agree, not a zero rounded moment. In the
  axial interface row ($u=(x,0,0)$, P0, moduli $1\,|\,1/8$, interior interface node) they differ: the rounded action is
  $2.3557692729$ against the physical $2.355769230769231$, a coefficient excess of $4.21244\times10^{-8}$
  (`summary.json` → `axial_example.interface.diff_excess_x_exact`; `out/fix_r8/checks.json` →
  `interface_centre_g_xx_P0_difference_form`).

* **E = 1.** In the production kernel all 13 opposite pairs at the uniform interior node are bitwise equal, and the
  difference-form excess is exactly 0 for all 15 affine fields.
* **E = 0.7.** Only 10 of the 13 pairs are bitwise equal, with mismatch up to $1.60\times10^{-9}$, so the
  coefficient-level excess at the uniform interior node is $1.60\times10^{-9}$, not zero (`coefficients.json` →
  `stencil_blocks.uniform_s07.opposite_weights_by_node_class`; `survival_affine`).

**Why the pairs differ at E = 0.7.** The 11 mismatched entries are exactly zero in exact arithmetic. The kernel forms
them as sums of literal-weighted groups of opposite sign, and their FP32 residues ($3.6\times10^{-10}$ to
$1.07\times10^{-9}$ in magnitude) differ between $r$ and $-r$ (`coefficients.json` →
`stencil_blocks.uniform_s07.centre_opposite_entries_differing`). The same residues break the axis-reflection symmetry of
the rounded blocks at the uniform centre, by up to $4.3\times10^{-9}$ (`centre_reflection_symmetry`). The kernel's coefficients equal the `stencil_c32` kernel's bit for bit
in every layout. An FP32 emulation of the coefficient formation without fused multiply-add reproduces them only for
$E=1$: it differs in 30, 529 and 426 entries for the other three layouts. The compiler contracts the formation into
fused multiply-adds, so the rounded weights depend on the modulus value and on code generation, not on the literals
alone.

**At the interface** the exact blocks already differ ($\max|W_r-W_{-r}|=0.748$ at the interior interface node), and the
rounding part of the mismatch reaches $9.4\times10^{-9}$ ($E=1|1/8$) or $3.0\times10^{-8}$ ($0.7|0.0875$). The rounded
blocks also lose the $y$ and $z$ reflection symmetry of the layout: by up to $7.45\times10^{-9}$ ($E=1|1/8$) and
$2.1\times10^{-8}$ ($0.7|0.0875$), where the exact blocks keep it exactly (`centre_reflection_symmetry`). The difference-form
interface excess therefore appears in components that the selection rule of Section 4 sets to zero. For example, at the
centre, P0: $g_{xy}$ gives a $z$ force of $1.86\times10^{-9}$, and $g_{yz}$ gives an $x$ force of $-3.73\times10^{-9}$
(`selection_rule_centre`). The opposite-weight mismatch is not confined to nodes whose incident cells differ and to the
patch boundary: at $E=0.7$ the homogeneous interior node also has three unequal opposite pairs and a first-moment entry
of $1.60474\times10^{-9}$ (above, and `summary.json` → `uniform_centre_difference_first_moment`).

The stencil's global symmetry $W_{-r}(n+r)=W_r(n)^{\mathsf T}$ holds bitwise for $E=1$. It fails by
$3.7\times10^{-9}$ (interface), $1.6\times10^{-9}$ ($E=0.7$) and $5.3\times10^{-9}$ (interface, $E=0.7$). The
row sums $\sum_rW_r(n)$ of the original stencil, its translation defect, are $6.7\times10^{-8}$ at the uniform interior
node ($E=1$). For the self-block correction they are $5.4\times10^{-7}$; they are exactly zero for the exact blocks.

**The original stencil's own terms.** At every node,
$$
\sum_rW_ru_{n+r}=R_n\,u_n+\sum_{r\ne0}W_r\,(u_{n+r}-u_n),\qquad R_n=\sum_rW_r(n),
$$
so the original-stencil excess is the row-sum term $R_nu_n$ plus the difference-form excess. For an affine field the
second part is the opposite-weight term $\sum_{r\in H}(\delta_r-\delta_{-r})Br$ (in a uniform region). The self-block
correction has the same form with its own row sum $R^{\rm sc}_n$. Both identities hold exactly in rational arithmetic:
0 mismatches in 79,056 component checks (`summary.json` → `stencil_decomposition`).

The original stencil is not the element form. Its translation defect $R_n$ comes from the kernel's FP32 coefficient
formation, not from $c$ (`coefficients.json` → `stencil_blocks.<layout>.centre_row_sum_stencil_kernel`):

* At $E=1$ the uniform-centre row sum is $R_n=8cI=-6.705522537\times10^{-8}\,I$ exactly, the same as the element
  kernel's, and the opposite weights are equal. The original stencil therefore gives $8c\,u(x_n)$, like the element form.
* At $E=0.7$ it is not $8Ec\,I$ ($8Ec=-4.693866\times10^{-8}$). Its diagonal is
  $(-1.825392\times10^{-7},\ 5.587935\times10^{-8},\ 5.587935\times10^{-8})$, and its off-diagonal entries reach
  $4.7\times10^{-9}$. For $u=(x,0,0)$ the original-stencil excess at the centre is
  $(-1.825392\times10^{-7},\ -1.99\times10^{-9},\ -3.8\times10^{-10})$. That is the row-sum term
  $(-1.825392\times10^{-7},\ -1.99\times10^{-9},\ +1.07\times10^{-9})$ plus the opposite-weight term
  $(0,\ 0,\ -1.45\times10^{-9})$, against $-4.69387\times10^{-8}$ in $x$ alone for the element form
  (`summary.json` → `uniform_centre_original_forms`).

## 6. What survives weighted assembly

**Coefficient level, exactly affine inputs** (`survival_affine`, $u_{64}$, P0 and P1):

| node class | original element | original stencil | self-block correction | corner | mean | difference |
|---|---|---|---|---|---|---|
| translation, any node | $c\sum E\,t$ | $R_n t$ (row sum) | $R^{\rm sc}_n t$ (row sum) | exact 0 | exact 0 | exact 0 |
| uniform interior, $E=1$ | $8Ec\,u(x_n)$ | $8c\,u(x_n)$ ($R_n=8cI$, equal opposite weights) | $\le5.4\times10^{-7}$ | $8Ec\,Bd$ (coherent) | exact 0 | exact 0 |
| uniform interior, $E=0.7$ | $8Ec\,u(x_n)$ | $R_nu_n$ + opposite-weight term; $\le1.83\times10^{-7}$ | $\le4.2\times10^{-7}$ | $8Ec\,Bd$ (coherent) | exact 0 | $\le1.6\times10^{-9}$ |
| interior on an 8:1 interface ($E=1\,\vert\,1/8$) | $\le3.77\times10^{-8}$ | $\le8.61\times10^{-8}$ | $\le1.68\times10^{-7}$ | $\le3.76\times10^{-8}$ | $\le3.76\times10^{-8}$ | $\le4.21\times10^{-8}$ |
| patch boundary nodes, uniform $E=1$ | $\le5.0\times10^{-8}$ | $\le5.0\times10^{-8}$ | $\le7.3\times10^{-7}$ | $\le4.8\times10^{-8}$ | $\le4.3\times10^{-8}$ | $\le4.8\times10^{-8}$ |

The bounds are coefficient-level maxima over the 15 unit-gradient, strain and rotation fields with $\beta=1$ or $0.37$
per cell; the maximising field depends on the form (Section 4). The interface row is for moduli $1\,|\,1/8$; at
$0.7\,|\,0.0875$ the bounds are $2.64$, $2.63$ and $2.63\times10^{-8}$ for the original element, corner and mean forms,
but $6.02\times10^{-8}$ (difference), $1.10\times10^{-7}$ (original stencil) and $7.06\times10^{-7}$ (self-block
correction). The physical interface force 2.356 belongs to $u=(x,0,0)$ alone.

**Production FP32, input $u_{32}$** (`node_class_summary.csv`; `survival_affine`, fp32 entries). Application rounding
adds an excess for every form, of the size of FP32 rounding of the products. No form is free of it at any node class.
Single field-node cases still come out exactly equal to the exact force: 32 of 540 field-form cases at the uniform
interior node, 19 of them from the difference kernel (`summary.json` → `fp32_uniform_centre_exact_cancellation`).

* **Uniform interior node, P0** (inputs $0,1,2$), maxima over the affine fields:

  | FP32 form | excess |
  |---|---|
  | original stencil | $3.1\times10^{-7}$ |
  | self-block correction | $9.5\times10^{-7}$ |
  | original element kernel | $1.5\times10^{-7}$ |
  | corner reference | $1.2\times10^{-7}$ |
  | mean reference | $1.2\times10^{-7}$ |
  | difference form | $8.2\times10^{-8}$ |

  Relative to the term scale these are $0.8$–$9\times10^{-8}$: with no translation part in the input, the reference forms
  gain little in a single action.
* **Uniform interior node, P2** (offset placement: the field carries a translation part $Bo$ about 45 times its
  variation per cell):

  | FP32 form | excess |
  |---|---|
  | original stencil | $1.67\times10^{-7}$ |
  | self-block correction | $5.2\times10^{-7}$ |
  | original element kernel | $7.0\times10^{-8}$ |
  | corner reference | $1.63\times10^{-9}$ |
  | mean reference | $1.40\times10^{-9}$ |
  | difference form | $1.58\times10^{-9}$ |

  The reference forms remove the translation part. The original forms are about 40 to 370 times larger, consistent with
  cancellation from $|u|$ rather than from $|u_{n+r}-u_n|$.
* **Interior interface node, P2.** The values are $7.1\times10^{-8}$ (original stencil), $8.5\times10^{-8}$ (original
  element kernel), $1.2\times10^{-9}$ (corner), $2.2\times10^{-9}$ (mean) and $3.7\times10^{-9}$ (difference). For
  scale, the physical $x$ force for $g_{xx}$ there is $2.72\times10^{-2}$.
* **Corner minus mean.** In FP32 this difference does not follow the identity within one action. At the centre node it
  deviates from $c\sum E\,Bd$ by a median of 1.9 times and a maximum of 24 times the predicted term (180 node-field
  cases, `identity_fp32_centre_rel_dev`). The identity is a statement about the rounded coefficients. In a single FP32
  action the application rounding is of the same order as the coherent corner term.
* **Determinism.** Five repeats of each atomic element kernel and two of each stencil kernel gave bitwise-identical
  outputs in all 244 cases. The FP32 scatter of the element kernels differs from the FP64 sum of the same kernel's
  single-cell outputs by at most $1.1\times10^{-7}$ of the term scale (`fp32_scatter_vs_local_sum`).
* **Input representation.** With the offset placement, rounding the input to FP32 changes the field itself. The exact
  force on $u_{32}$ is $1.6\times10^{-7}$ at the uniform centre for $g_{xx}$ (`centre_table`), above the reference forms'
  operator excess. This is why every excess is taken over the same represented input.

**Rotations (R2.4).** Source: `summary.json` → `rotations`, which breaks every rotation result down by layout, placement,
input, form and node class.

*Physical force.* The physical force is the exact matrix applied to the input actually used.

* It is exactly zero at every node where that input is an exact rigid rotation: the FP64 and FP32 inputs of P0 and P1
  (324 node-field cases each), and the FP32 input of `rot_x` in P2.
* FP32 representation does not destroy every rigid rotation in the offset placement P2. The P2 $x$-axis rotation stays
  rigid: its FP32 values are exactly affine (zero second differences along every line of the patch) with a skew
  gradient, and the exact matrix gives zero physical force in all 108 node-layout cases. The $y$- and $z$-axis rotations
  are no longer exact rotations after rounding and give all 216 nonzero cases of the 324, up to $2.29\times10^{-8}$
  (`out/fix_r8/checks.json` → `p2_u32_rotation_physical_force_by_axis`, `p2_rot_x_u32`). An example is the $y$ force
  of `rot_z` at the uniform centre: $2.2924863\times10^{-8}$.
* The FP64 input of P2 also carries a physical force, of at most $2.1\times10^{-17}$, from its own FP64 representation.

This force belongs to the input and is not an operator error. Every operator figure below is the excess over the exact
force on the same input.

*Coefficient level* (FP64 inputs of P0 and P1, which are exact rotations):

* Maxima across the patch are nonzero for every form. No tested form preserves every rotation at every node.
* The mean reference is exactly zero at the uniform interior node for all three rotations at both moduli.
* The difference form is exactly zero at the uniform interior node for all three rotations at $E=1$; at $E=0.7$ it
  reaches $1.34\times10^{-9}$.
* The original element and corner forms reach $3.35\times10^{-8}$ and $1.68\times10^{-8}$ at the uniform interior node
  (P0, $E=1$).
* Individual fields and nodes do cancel exactly outside the uniform interior node:
  * At the 8:1 interface centre, the mean reference is exactly zero for `rot_x` (whose gradient components the
    selection rule of Section 4 removes), and reaches $8.96\times10^{-9}$ for the other rotations.
  * On homogeneous boundary faces (all layouts, placements and inputs), the rounded mean reference is exactly zero in 72
    of 288 node-field cases and the rounded difference form in 36 of 288. An example is `rot_x` at face node 4 of the
    uniform patch, P0.
  * The difference form reaches $2.79\times10^{-9}$ at the interface centre.

*Production FP32* (excess over the exact force on the FP32 input):

* Every form is nonzero somewhere in every node class.
* Single cases still come out exactly zero. The FP32 difference kernel returns the zero vector for `rot_x` at the
  uniform centre with $E=1$, P0. The FP32 element kernels and stencils give exact zeros at a few boundary corners, edges
  and faces (`exact_zero_excess_counts_by_form_and_class`).
* Magnitudes at P0 ($\beta=1$, uniform centre, $E=1$): difference form $7.45\times10^{-9}$, mean reference
  $2.12\times10^{-8}$, corner reference $3.73\times10^{-8}$, original stencil $7.45\times10^{-8}$, original element
  kernel $8.0\times10^{-8}$, self-block correction $4.77\times10^{-7}$.
* At P2 ($\beta=0.37/32$, translation part included), at the uniform centre, the reference and difference forms stay at
  $0.7$–$5.3\times10^{-10}$ above the physical force of $2.29\times10^{-8}$. The original element kernel reaches
  $4.66\times10^{-8}$, the original stencil $6.28\times10^{-8}$ and the self-block correction $1.42\times10^{-7}$.

The translation guarantee does not extend to rotations. A rotation cancels exactly, at coefficient level, only where the
coefficients are reflection symmetric and equally weighted within each inversion pair (mean reference, and difference
form whose rounded blocks have zero first moment, at a homogeneous interior node) or for particular fields, nodes and
roundings.

## 7. Consequences under refinement (argument, not tested here)

For a smooth field with gradient $G$, the per-cell differences are $\beta B\sim Gh$. The interior physical force of the
fixed unit matrix scales as $h^2|\nabla^2u|$.

* **Corner.** The coherent corner term $c\,(\sum E)\,Bd\sim|c|\,|G|\,h$ gives a relative defect of order $|c|/h$, with
  the same sign at every node of a uniform region.
* **Original forms.** The element term $8Ec\,u(x_n)$, and the stencil's row-sum term $R_nu_n$, give a relative defect of
  order $|c|/h^2$ (for the stencil, $|R_n|/h^2$).
* **Mean and difference.** These have no coefficient term in a uniform region; the difference form only where the
  first moment of its rounded blocks vanishes (for example where the rounded opposite weights are equal). Their rounded coefficients act on the quadratic part only, which gives a relative
  error of order $\delta$.
* **FP32 application rounding.** This is a separate per-node term, present for every form, of order
  $\varepsilon_{32}\sum_r|W_r|\,|v_r|$, where $v_r$ is the nodal quantity that the form multiplies.
  * The reference and difference forms multiply differences, $u_{n+r}-u_n$ or $u_e-Tr_e$, of size $|G|h$. Their
    rounding term is of order $\varepsilon_{32}|W|\,|G|h$.
  * The original element and stencil forms (and the self-block correction) multiply the absolute displacements. Their
    rounding term is of order $\varepsilon_{32}|W|\,|u|$, and it is present even for $G=0$. At unit translation the FP32
    original stencil gives $3.95\times10^{-7}$ against a coefficient-level defect of $6.71\times10^{-8}$, and the FP32
    original element kernel $1.28\times10^{-7}$ (Section 3.1). Relative to the term scale $\sum|E_eK_{0,ij}u_j|$ (10.94 at
    the uniform centre for a unit translation), the FP32 translation excess of the original forms is up to
    $1.1\times10^{-7}$ (stencil), $7.5\times10^{-8}$ (element kernel) and $2.1\times10^{-7}$ (self-block correction),
    with no trend over the amplitudes from $3.7\times10^{-4}$ to $1.2\times10^{7}$ (`node_class_summary.csv`, family
    `translation`, input `u32`). This is a relative error of the size of $\varepsilon_{32}=2^{-24}\approx6\times10^{-8}$
    on $|u|$.
  * Relative to the physical force of order $h^2|\nabla^2u|$, the original forms' rounding term therefore scales like the
    coefficient term $8Ec\,u$: as $|u|/h^2$, not as $|G|/h$.

Whether these per-node terms accumulate in a solved compliance (coherent versus sign-varying) is outside what one patch
can show. The refinement series of T21/T33 measures it.

## 8. Discrepancies and limits

1. The mean-reference cancellation in a uniform region is exact for the rounded coefficients evaluated in rational
   arithmetic on exactly affine inputs. Applying the same coefficients in FP64 arithmetic leaves a rounding residue: at
   the uniform interior node up to $9.7\times10^{-17}$ at $E=1$ (for example $-9.71445\times10^{-17}$ in the $z$ force
   of the $xz$ strain, P1, where the exact force is 0) and $1.1\times10^{-16}$ at $E=0.7$. Of the 30 field cases per
   modulus, 16 ($E=1$) and 12 ($E=0.7$) come out exactly zero in FP64 (`summary.json` →
   `uniform_centre_exact_vs_fp64_application`). In the production FP32 actions application rounding leaves up to
   $1.2\times10^{-7}$ at the uniform interior node for the FP32 mean reference; only 6 of its 90 field cases there are
   exactly zero. "Zero to calculation precision" therefore holds exactly for the coefficients and to FP64 rounding for
   their FP64 application, not for the FP32 action.
2. "Equal weights round to equal values" (submitted Sec. 3.2) holds for the production stencil at $E=1$, but not at
   $E=0.7$: 3 of 13 opposite pairs differ by up to $1.6\times10^{-9}$. The difference form's affine cancellation at the
   homogeneous interior node is exact when the first moment of the kernel's rounded blocks vanishes. Coinciding
   opposite weights suffice for that; at $E=0.7$ the moment does not vanish, and the excess is $1.6\times10^{-9}$. At
   interface and boundary nodes the rounded first moment has to equal the exact one instead (Section 5).
3. At the 8:1 interface no form cancels for every field. Over the 15 unit-gradient, strain and rotation fields, the
   largest coefficient excess at the interior interface node with moduli $1\,|\,1/8$ is $3.76$–$4.21\times10^{-8}$ for
   the mean, corner, original element and difference forms, $8.61\times10^{-8}$ for the original stencil and
   $1.68\times10^{-7}$ for the self-block correction. With moduli $0.7\,|\,0.0875$ it is $2.63$–$2.64\times10^{-8}$ for
   the mean, corner and original element forms, $6.02\times10^{-8}$ for the difference form, $1.10\times10^{-7}$ for the
   original stencil and $7.06\times10^{-7}$ for the self-block correction. The maximising field depends on the form and
   the moduli (Section 4). For the axial field alone ($1\,|\,1/8$), whose physical force is 2.356, the $x$ excesses are
   $+2.75\times10^{-8}$ (mean), $+8.60\times10^{-9}$ (corner), $+4.41\times10^{-9}$ (original element),
   $+4.21\times10^{-8}$ (difference) and $-1.75\times10^{-8}$ (original stencil). Its transverse excesses are exactly 0
   for the original element, corner, mean and difference forms, but not for the original stencil ($z$: $-1.86\times10^{-9}$) or the
   self-block correction ($y$: $-1.30\times10^{-8}$, $z$: $+1.86\times10^{-9}$). Single fields can still cancel exactly
   there: the mean reference gives exact zero for `rot_x`. The stencil kernel's rounded weights are not reflection
   symmetric there, so the difference, original-stencil and self-block-corrected excesses appear in components that the
   selection rule sets to zero.
4. In one FP32 action the corner-minus-mean difference does not follow the coefficient identity: the median deviation is
   1.9 times the predicted term.
5. The FP64 `ke_unit` matrix is not bitwise symmetric (81 pairs, $\le2.8\times10^{-17}$). The FP32 rounding $Q$ is.
6. The original stencil is not the original element form with other coefficients. At $E=0.7$ its row sum is not
   $8Ec\,I$, and its axial excess at the uniform centre ($-1.825\times10^{-7}$ in $x$, with transverse components) is
   about four times the element form's $-4.69\times10^{-8}$ (Section 5).
7. Rotations: the physical force on an FP32-represented rotation is not zero where rounding breaks the rotation (the
   $y$- and $z$-axis rotations of P2, up to $2.29\times10^{-8}$; the P2 $x$-axis rotation stays rigid). It is kept
   apart from the operator excess.
8. GPU monitor coverage starts at the first sample that holds the job process with both counters. Before that sample
   the job had created its CUDA context and one one-element array. The shared usage at that sample, 77,594,624 B, is the
   baseline; the growth after it was 2 MiB, and the final sample was checked. The pool cap and the in-process budget
   check came after that sample (`summary.json` → `monitor_coverage`).
9. Scope:
   * one 2×2×2-cell free patch, cubic voxels, $\nu=0.3$;
   * one interface orientation (normal $x$), two modulus scales, three placements;
   * one GPU and toolchain (RTX 4090, CUDA runtime 12.8 through CuPy 13.4.1; FP32 coefficient rounding depends on the
     compiler's fused multiply-add contraction);
   * no distorted elements and no solved problems.
