"""T29: build comparison.json, the comparison tables and the paired-timing orientation check.

CPU only; reads records, never writes outside tasks/T29.  No GPU work, no language-model calls.

Sources (read in place, never modified):
  results/...            the authors' raw records, relative to the project folder <project>
  tasks/T14|T27|T28/...  earlier revision tasks, relative to the run's work folder
  input/manuscript/...   the submitted manuscript, relative to the run folder (only to compare stated values)

Every cell of every row is a dict:
  {"v": value, "src": "<file>#/<json pointer>"}            read from a JSON record
  {"v": value, "src": "<file>:<line>#<column>"}             read from a CSV row (line 1 = header)
  {"v": value, "formula": "...", "from": [src, ...]}        derived here from cited cells
  {"v": null, "missing": "<reason>"}                       not measured / not available
  {"v": value, "basis": "<code or plan location>"}          a label fixed by code or by a frozen plan
"""
import csv
import json
import math
import re
import statistics
from pathlib import Path

PROJ = Path(__file__).resolve().parents[4]  # T32 staging: project root
RUN = PROJ / "revision_round1"
WORK = RUN / "work"
OUT = WORK / "tasks" / "T29"


def resolve(rel):
    if rel.startswith("results/"):
        return PROJ / rel
    if rel.startswith("tasks/"):
        return WORK / rel
    if rel.startswith("input/"):
        return RUN / rel
    raise ValueError(rel)


_J, _C = {}, {}


def load(rel):
    if rel not in _J:
        _J[rel] = json.loads(resolve(rel).read_text(encoding="utf-8"))
    return _J[rel]


def J(rel, *path):
    o = load(rel)
    for p in path:
        o = o[p]
    return {"v": o, "src": rel + "#/" + "/".join(str(p).replace("~", "~0").replace("/", "~1") for p in path)}


def Jopt(rel, *path, missing="not recorded"):
    try:
        c = J(rel, *path)
    except (KeyError, IndexError, TypeError):
        return {"v": None, "missing": missing}
    if c["v"] is None:
        return {"v": None, "missing": missing, "src": c["src"]}
    return c


def csv_rows(rel):
    if rel not in _C:
        with open(resolve(rel), encoding="utf-8", newline="") as fh:
            rd = csv.reader(fh)
            header = next(rd)
            rows = []
            for rec in rd:
                rows.append((rd.line_num, dict(zip(header, rec))))
        _C[rel] = rows
    return _C[rel]


def num(s):
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return s
    s = s.strip()
    if s == "":
        return None
    try:
        f = float(s)
    except ValueError:
        return s
    return int(f) if re.fullmatch(r"-?\d+", s) else f


def C(rel, line, row, col, missing="empty in the source table"):
    v = num(row.get(col))
    src = f"{rel}:{line}#{col}"
    if v is None:
        return {"v": None, "missing": missing, "src": src}
    return {"v": v, "src": src}


def find_csv(rel, **match):
    out = [(ln, r) for ln, r in csv_rows(rel) if all(r.get(k) == str(v) for k, v in match.items())]
    if len(out) != 1:
        raise LookupError(f"{rel} {match}: {len(out)} rows")
    return out[0]


def D(v, formula, *cells, op=None, **params):
    """Derived cell.  With `op`, verify_sources.py recomputes v from the operand cells (copied in full) or, for
    op = "hist", from the record named in params; without `op` the cell cannot be rechecked and the verifier
    reports it."""
    c = {"v": v, "formula": formula, "from": [x.get("src") or x.get("formula") or x.get("basis") for x in cells]}
    if op:
        c["op"] = op
        if op not in ("hist", "len"):
            c["operands"] = [dict(x) for x in cells]
        if params:
            c["params"] = params
    return c


def H(rel, agg, field, formula, **kw):
    """Aggregate over history[*] of an optimization record (recomputed by the verifier from the record)."""
    h = load(rel)["history"]
    vals = [_hget(x, field) for x in h]
    v = _hagg(vals, agg, **kw)
    c = {"v": v, "formula": formula, "from": [rel + "#/history"], "op": "hist",
         "params": dict(file=rel, agg=agg, field=field, **kw)}
    return c


def _hget(x, field):
    o = x
    for p in field.split("."):
        if "|" in p:                       # first present alternative, e.g. "inner_iters|iters"
            o = next((o[q] for q in p.split("|") if isinstance(o, dict) and q in o), None)
        else:
            o = o.get(p) if isinstance(o, dict) else None
        if o is None:
            return None
    return o


def _hagg(vals, agg, threshold=None):
    fin = [x for x in vals if isinstance(x, (int, float)) and x == x]
    if agg == "len":
        return len(vals)
    if agg == "sum":
        return sum(fin)
    if agg == "mean":
        return sum(fin) / len(vals)
    if agg == "max":
        return max(fin)
    if agg == "median":
        return statistics.median(fin)
    if agg == "count":
        return len(fin)
    if agg == "count_gt":
        return sum(x > threshold for x in fin)
    raise ValueError(agg)


def M(reason):
    return {"v": None, "missing": reason}


def B(v, basis):
    return {"v": v, "basis": basis}


def val(c):
    return None if c is None else c.get("v")


def ratio(a, b, formula):
    if isinstance(val(a), (int, float)) and isinstance(val(b), (int, float)) and val(b):
        return D(val(a) / val(b), formula, a, b, op="div")
    return M("an operand is missing")


def gm_factor(r_end, r_start, n, comparable, note):
    """(r_end/r_start)^(1/n); only for comparable positive FP64 true residuals and n > 0."""
    if not comparable:
        return M("not computed: " + note)
    e, s, k = val(r_end), val(r_start), val(n)
    if not all(isinstance(x, (int, float)) for x in (e, s, k)):
        return M("not computed: a residual or the step count is missing")
    if not (e > 0 and s > 0 and k > 0 and math.isfinite(e) and math.isfinite(s)):
        return M("not computed: residual not positive and finite, or n = 0")
    c = D((e / s) ** (1.0 / k), "(r_end / r_start)^(1/n)", r_end, r_start, n, op="factor")
    c["n_kind"] = note
    return c


def add1(c, formula):
    return D(val(c) + 1, formula, c, op="add1")


ZERO_START = B(1.0, "zero starting iterate: ||b - K 0|| / ||b|| = 1 exactly")

DEVICE = "NVIDIA GeForce RTX 4090 (24 GB), this workstation, which also drives the display"

rows, pairs, largest, notes_global = [], [], [], []


def row(**kw):
    kw.setdefault("device", DEVICE)
    rows.append(kw)
    return kw


# ----------------------------------------------------------------------------------------------------------------
# A. Assembled sparse (cuSPARSE) against matrix-free applications: E2 and E4
# ----------------------------------------------------------------------------------------------------------------
def block_sparse():
    e2 = sorted((PROJ / "results" / "E2").glob("op_k*.json"), key=lambda p: (int(p.stem.split("_k")[1].split("_")[0]), p.stem))
    status_by = {}
    for p in e2:
        rel = "results/E2/" + p.name
        d = load(rel)
        k, dt = d["k"], d["dtype"]
        names = [r["method"] for r in d["rows"]]
        i_st = names.index("stencil")
        st = J(rel, "rows", i_st, "us_median")
        mf = [r for r in d["rows"] if r["method"] not in ("cusparse_csr", "cusparse_bsr", "empty_launch")]
        i_fast = names.index(min(mf, key=lambda r: r["us_median"])["method"])
        fast = J(rel, "rows", i_fast, "us_median")
        for fmt in ("cusparse_csr", "cusparse_bsr"):
            info = d["sparse_info"].get(fmt)
            if info is None:
                continue
            status = info["status"]
            r = dict(
                id=f"sparse_E2_{fmt}_{dt}_k{k}", block="A_sparse", provenance="historical record (submitted paper)",
                workload="one operator application on a fixed modulus field (operator survey)",
                system=f"authors' cantilever grid {2*k}x{k}x{k}, unit element matrix, random input vector",
                elements=J(rel, "n_elem"), dofs=J(rel, "ndof"),
                code="cuSPARSE " + ("CSR" if fmt.endswith("csr") else "BSR (3x3 blocks)") + " SpMV on the assembled matrix",
                operator_precision=dt.upper() + " matrix values and vectors",
                krylov_precision="not applicable (single application)", residual_precision="not applicable",
                iterate_precision="not applicable", native_stop="not applicable",
                status=J(rel, "sparse_info", fmt, "status"),
                admission=B("built only when 3 x the estimated matrix storage fits the guard's effective free memory",
                            "experiments/E2_operators.py:96-99 (guard.require_budget(3 * nb))"),
                coefficients=B("one modulus field E (log-uniform on [1e-9, 1]) and one input vector for every operator of the record: "
                               "the assembled matrix is built from E and the matrix-free operators apply E, so each comparison uses identical coefficients",
                               "experiments/E2_operators.py:83-84, 92, 103, 111-113"),
                times={}, memory={}, notes=[])
            if status == "ok":
                i = names.index(fmt)
                t = J(rel, "rows", i, "us_median")
                r["times"]["application"] = dict(t, unit="us", denominator="per application",
                                                 statistic="median of 11 randomized timing blocks (IQR in the record)",
                                                 boundary="GPU-event block of repeated applications divided by the count")
                r["times"]["matrix_free_stencil_same_file"] = dict(st, unit="us", denominator="per application",
                                                                   note="original 27-point stencil, same precision, same process")
                r["times"]["ratio_to_stencil"] = ratio(t, st, f"{fmt} median / stencil median (same file)")
                r["times"]["ratio_to_fastest_matrix_free"] = ratio(t, fast, f"{fmt} median / fastest matrix-free median (same file)")
                r["times"]["one_off_build"] = dict(J(rel, "sparse_info", fmt, "build_s"), unit="s",
                                                   denominator="once per sparsity pattern")
                r["setup"] = dict(build=J(rel, "sparse_info", fmt, "build_s"), unit="s",
                                  boundary="construction of the assembled matrix (pattern and values) between device synchronizations")
                r["memory"]["matrix_storage"] = dict(J(rel, "sparse_info", fmt, "storage_bytes"), unit="B",
                                                     definition="bytes of the assembled matrix arrays, computed by the driver")
            else:
                r["setup"] = M("not built")
                r["memory"]["estimated_storage"] = dict(J(rel, "sparse_info", fmt, "estimate_bytes"), unit="B",
                                                        definition="driver's storage estimate; the case was not built")
                r["notes"].append("not built under this study's admission rule (3 x the estimated storage had to fit the free memory); "
                                  "a prediction, not a measured limit: the update-cost study (E4) built and timed larger cases under its 1.15 x rule")
            rows.append(dict(r, device=DEVICE))
            status_by.setdefault((fmt, dt), []).append((d["n_elem"], status, r["id"]))
    for (fmt, dt), lst in sorted(status_by.items()):
        lst.sort()
        ok = [x for x in lst if x[1] == "ok"]
        nxt = [x for x in lst if x[1] != "ok" and (not ok or x[0] > ok[-1][0])]
        largest.append(dict(configuration=f"{fmt} SpMV, {dt.upper()}, operator-survey build rule",
                            workload="one application on a fixed field (operator survey)",
                            admission_rule=B("3 x the estimated matrix storage must fit the effective free memory",
                                             "experiments/E2_operators.py:96-99"),
                            largest_pass_elements=ok[-1][0] if ok else None, largest_pass_row=ok[-1][2] if ok else None,
                            next_size_elements=nxt[0][0] if nxt else None,
                            next_size_status=("not built under this rule (a prediction); the update-cost study's 1.15 x rule built larger cases"
                                              if nxt else "none tested"),
                            next_size_row=nxt[0][2] if nxt else None,
                            provenance="historical record (submitted paper)"))
    # matrix-free application: largest grid, both precisions
    for dt in ("fp32", "fp64"):
        rel = f"results/E2/op_k512_{dt}.json"
        largest.append(dict(configuration=f"matrix-free 27-point stencil and seven other mappings, {dt.upper()}",
                            workload="one application on a fixed field (operator survey)",
                            largest_pass_elements=load(rel)["n_elem"], largest_pass_row=None,
                            largest_pass_src=rel + "#/n_elem", spill=J(rel, "spill", "spilled"),
                            next_size_elements=None, next_size_status="largest grid of the survey; no larger grid tested",
                            provenance="historical record (submitted paper)"))
    # E4: refresh and SpMV against the hierarchy update
    for p in sorted((PROJ / "results" / "E4").glob("update_k*.json"), key=lambda p: int(p.stem.split("_k")[1])):
        rel = "results/E4/" + p.name
        d = load(rel)
        rr = d["rows"]
        st = J(rel, "rows", "apply_stencil_fp32_s")
        r = dict(id=f"sparse_E4_k{d['k']}", block="A_sparse", provenance="historical record (submitted paper)",
                 workload="one coefficient update (new moduli of one design iteration) and one application",
                 system=f"authors' cantilever grid {2*d['k']}x{d['k']}x{d['k']}",
                 elements=J(rel, "n_elem"), dofs=M("not recorded in this record"),
                 code="cuSPARSE CSR / BSR with the fused in-place value refresh; Galerkin multigrid update; matrix-free stencil",
                 operator_precision="FP32 values and vectors", krylov_precision="not applicable",
                 residual_precision="not applicable", iterate_precision="not applicable", native_stop="not applicable",
                 status=B("ok" if d["valid"] else "invalid", rel + "#/valid"),
                 admission=B("each assembled format built only when 1.15 x its estimated matrix storage fits the guard's effective free memory "
                             "(the fused build allocates only the matrix arrays plus O(n_node) helpers)",
                             "experiments/E4_update_cost.py:63-68"),
                 coefficients=B("two modulus fields drawn from the same distribution (log-uniform on [1e-9, 1]): the matrix-free stencil is timed "
                                "on the first field E; each assembled matrix is built from E, refreshed to the second field E2, and its SpMV is "
                                "timed after the refresh, i.e. on E2; the multigrid update also uses E2",
                                "experiments/E4_update_cost.py:56-57, 61, 70-73, 84-88, 93"),
                 times={}, memory={}, notes=[])
        r["setup"] = dict(csr_build=Jopt(rel, "rows", "csr_build_s", missing="CSR not built"),
                          bsr_build=Jopt(rel, "rows", "bsr_build_s", missing="BSR not built"), unit="s",
                          boundary="one-off pattern and value build of each assembled format between device synchronizations; "
                                   "the matrix-free operator has no assembly (the moduli array is the operator)")
        r["times"]["stencil_application"] = dict(st, unit="s", denominator="per application",
                                                 statistic="median of 21 host-synchronized calls")
        for key, lab in (("csr_refresh_s", "CSR value refresh"), ("csr_apply_fp32_s", "CSR SpMV"),
                         ("bsr_refresh_s", "BSR value refresh"), ("bsr_apply_fp32_s", "BSR SpMV"),
                         ("mg_update_s", "multigrid hierarchy update")):
            if key in rr:
                c = J(rel, "rows", key)
                r["times"][key] = dict(c, unit="s", denominator="per call",
                                       statistic="median of 7 (refresh), 21 (SpMV) or 5 (update) host-synchronized calls")
                r["times"][key + "_in_applications"] = ratio(c, st, f"{key} / stencil application")
        for fmt in ("csr", "bsr"):
            if f"{fmt}_status" in rr:
                r["notes"].append(f"{fmt.upper()}: " + rr[f"{fmt}_status"] + " (not admitted under this study's 1.15 x storage rule: a prediction, not a measured limit)")
                r[f"{fmt}_status"] = J(rel, "rows", f"{fmt}_status")
            elif f"{fmt}_storage_bytes" in rr:
                r["memory"][f"{fmt}_storage"] = dict(J(rel, "rows", f"{fmt}_storage_bytes"), unit="B",
                                                     definition="bytes of the assembled matrix arrays")
        rows.append(dict(r, device=DEVICE))
    for fmt in ("csr", "bsr"):
        lst = []
        for p in (PROJ / "results" / "E4").glob("update_k*.json"):
            d = load("results/E4/" + p.name)
            lst.append((d["n_elem"], f"{fmt}_refresh_s" in d["rows"], f"sparse_E4_k{d['k']}"))
        lst.sort()
        ok = [x for x in lst if x[1]]
        nxt = [x for x in lst if not x[1] and x[0] > ok[-1][0]]
        lrel = f"results/E4/update_k{ok[-1][2].split('_k')[1]}.json"
        largest.append(dict(configuration=f"{fmt.upper()} SpMV and value refresh, FP32, update-cost build rule",
                            workload="one coefficient update and one application (update-cost study)",
                            admission_rule=B("1.15 x the estimated matrix storage must fit the effective free memory",
                                             "experiments/E4_update_cost.py:63-68"),
                            largest_pass_elements=ok[-1][0], largest_pass_row=ok[-1][2],
                            largest_pass_spmv=dict(J(lrel, "rows", f"{fmt}_apply_fp32_s"), unit="s", statistic="median of 21 host-synchronized calls"),
                            largest_pass_refresh=dict(J(lrel, "rows", f"{fmt}_refresh_s"), unit="s", statistic="median of 7 host-synchronized calls"),
                            next_size_elements=nxt[0][0] if nxt else None,
                            next_size_status="not built under this rule (a prediction, not a measured limit)",
                            next_size_row=nxt[0][2] if nxt else None, provenance="historical record (submitted paper)"))


# ----------------------------------------------------------------------------------------------------------------
# B. Hou et al.: the seven historical E10 rows (same process, as submitted)
# ----------------------------------------------------------------------------------------------------------------
HOU_SYSTEM = ("Hou et al.'s solid cantilever 2k x k x k, their element matrix (E = 1, nu = 0.3, "
              "lambda = E nu / ((1 + nu)(1 - nu))), their supports (12 fixed DOFs) and z-load patch, zero start")


def block_hou_historical():
    for k in (16, 32, 64, 80, 128, 160, 256):
        rel = f"results/E10/hou_k{k}.json"
        d = load(rel)
        solved = "their_solve_s" in d
        common = dict(block="B_hou_historical", provenance="historical record (submitted paper; both codes in one process)",
                      workload="one operator application" + ("; one state solve from zero" if solved else " only (operator-only row)"),
                      system=HOU_SYSTEM.replace("2k x k x k", f"{2*k}x{k}x{k}"),
                      elements=J(rel, "n_elem"), dofs=J(rel, "ndof"), start="zero")
        th = dict(common, id=f"hou_E10_k{k}_theirs",
                  code="Hou et al. CuPy-for-TO (released, unmodified)",
                  operator="SpMV.honorAb: 24 generated element-row kernels over the surviving elements",
                  operator_precision="FP32 storage; FP64 literals inside each row kernel, FP32 output and accumulation",
                  krylov_precision="FP32 (unpreconditioned CG)", residual_precision="FP32 recursive",
                  iterate_precision="FP32",
                  native_stop=B("recursive ||r_k|| < 1e-3 ||r_0|| (their tolerance) or 10,000 iterations",
                                "external/CuPy-for-TO/cupy_for_TO/CG.py:20,31 and FE.py:26 (itermax 10000); experiments/E10_external_hou.py:114 (tol 1e-3)"),
                  times={}, memory={}, notes=[])
        th["times"]["application"] = dict(J(rel, "their_apply_s"), unit="s", denominator="per application",
                                          statistic="median of 11 single-call GPU-event intervals after 3 warm-up calls",
                                          boundary="one call of their operator, including its per-call allocations, as released")
        th["setup"] = dict(J(rel, "their_setup_s"), unit="s",
                           boundary="killer + survivor index construction (after kernel generation and import)")
        ou = dict(common, id=f"hou_E10_k{k}_ours",
                  code="authors' solver (submitted version)",
                  operator="application: original 27-point stencil, FP32, with Hou's element matrix; "
                           "solve: FP64 node_hoist operator",
                  operator_precision="FP32 stencil (application); FP64 operator in the solve",
                  krylov_precision="FP64 PCG", residual_precision="FP64 true residual",
                  iterate_precision="FP64", preconditioner="FP32 Galerkin V-cycle, fine level original stencil",
                  native_stop=B("FP64 true ||b - Ku|| / ||b|| <= 1e-5, maxit 5000", "experiments/E10_external_hou.py:144 (pcg64 ..., 1e-5, 5000)"),
                  times={}, memory={}, notes=[])
        ou["times"]["application"] = dict(J(rel, "our_stencil_apply_s"), unit="s", denominator="per application",
                                          statistic="median of 11 single-call GPU-event intervals after 3 warm-up calls",
                                          boundary="one stencil application into a preallocated output")
        rat = ratio(J(rel, "their_apply_s"), J(rel, "our_stencil_apply_s"),
                    "their application median / our original-stencil application median (>1: theirs slower)")
        pairs.append(dict(id=f"hou_E10_k{k}_application_ratio", rows=[th["id"], ou["id"]], value=rat,
                          orientation="Hou / ours", operator_ours="original 27-point stencil (not the repaired form)"))
        th["operator_agreement"] = J(rel, "operator_rel_diff")
        mem_missing = M("not measured: this record samples memory only for the spill check (process dedicated and shared usage at start and end)")
        th["memory"]["peak"] = mem_missing
        ou["memory"]["peak"] = mem_missing
        th["spill"] = J(rel, "spill", "spilled")
        ou["spill"] = J(rel, "spill", "spilled")
        if solved:
            th["status"] = B("native stop met (recursive); FP64 true residual above 1e-5", "derived from their_true_residual")
            th["released_index_i"] = dict(J(rel, "their_cg_iterations"),
                                          meaning="the zero-based loop index i that the released CG returns after the iterate update of its last iteration "
                                                  "(CG.py:23, 29, 38); E10 saved it unchanged (E10_external_hou.py:114, 116)")
            th["steps"] = add1(th["released_index_i"], "released zero-based index i + 1 = completed CG iterations")
            th["achieved_true_residual"] = dict(J(rel, "their_true_residual"), kind="FP64 true residual of their FP32 iterate, our FP64 operator, same process")
            th["times"]["solve"] = dict(J(rel, "their_solve_s"), unit="s", denominator="per solve (one solve)",
                                        boundary="their FE.FE call: load and support construction, survivor indexing, residual formation and CG, between device synchronizations")
            th["times"]["per_step_mean"] = dict(ratio(J(rel, "their_solve_s"), th["steps"],
                                                      "solve / completed iterations (mean, includes solve-start overhead; not a synchronized per-step time)"),
                                                unit="s", denominator="per CG iteration (run mean)")
            th["residual_factor_per_step"] = gm_factor(th["achieved_true_residual"], ZERO_START, th["steps"], True,
                                                       "n = completed unpreconditioned FP32 CG iterations (released index + 1)")
            ou["status"] = B("verified in-process (FP64 true residual <= 1e-5)", "our_true_residual <= 1e-5")
            ou["steps"] = J(rel, "our_pcg_iterations")
            ou["achieved_true_residual"] = dict(J(rel, "our_true_residual"), kind="FP64 true residual computed in the solver (not an independent check)")
            ou["times"]["solve"] = dict(J(rel, "our_solve_s"), unit="s", denominator="per solve (one solve)",
                                        boundary="pcg64 call only; load, mask, FP64 operator and hierarchy built before the timer")
            ou["times"]["per_step_mean"] = dict(ratio(J(rel, "our_solve_s"), J(rel, "our_pcg_iterations"),
                                                      "solve / iterations (mean; not a synchronized per-step time); pcg64 counts iterations from 1"),
                                                unit="s", denominator="per PCG iteration (run mean)")
            ou["residual_factor_per_step"] = gm_factor(ou["achieved_true_residual"], ZERO_START, ou["steps"], True,
                                                       "n = FP64 PCG iterations (one V-cycle each)")
            ou["setup"] = M("not recorded: the saved records hold no our_setup_s, although the current driver writes it (E10_external_hou.py:142)")
            ou["compliance_rel_diff_to_theirs"] = J(rel, "compliance_rel_diff")
            pairs.append(dict(id=f"hou_E10_k{k}_solve_time_ratio", rows=[th["id"], ou["id"]],
                              value=ratio(J(rel, "their_solve_s"), J(rel, "our_solve_s"), "their solve / our solve (>1: theirs slower)"),
                              orientation="Hou / ours", label="at unequal accuracy (their FP64 true residual >> 1e-5); different timer boundaries"))
        else:
            th["status"] = B("operator only: no solve in this record", "their_solve_s absent")
            ou["status"] = B("operator only: no solve in this record", "our_solve_s absent")
            ou["setup"] = M("not recorded (application only)")
            for r_ in (th, ou):
                r_["steps"] = M("no solve")
                r_["achieved_true_residual"] = M("no solve")
                r_["residual_factor_per_step"] = M("not computed: no solve")
        rows.append(dict(th, device=DEVICE))
        rows.append(dict(ou, device=DEVICE))
    largest.append(dict(configuration="Hou et al. released operator (historical, one process)", workload="one application",
                        largest_pass_elements=load("results/E10/hou_k256.json")["n_elem"], largest_pass_row="hou_E10_k256_theirs",
                        next_size_elements=None,
                        next_size_status="no valid larger record (an earlier attempt at 65.5M elements is in the authors' superseded folder, which is never reported; T27's plan excluded it)",
                        provenance="historical record (submitted paper)"))


# ----------------------------------------------------------------------------------------------------------------
# C. T27: matched Hou system in separate processes
# ----------------------------------------------------------------------------------------------------------------
T27M = "tasks/T27/hou_matched.csv"
T27X = "tasks/T27/hou_exploratory.csv"

T27_PATHS = {
    "hou_cg32": dict(code="Hou et al. CuPy-for-TO (released FE.FE / CG.CG, separate process)",
                     preconditioner="none"),
    "mg64_orig": dict(code="authors' FP64 PCG", preconditioner="FP32 Galerkin V-cycle, fine level original stencil"),
    "mg64_rep": dict(code="authors' FP64 PCG", preconditioner="FP32 Galerkin V-cycle, fine level difference-form stencil (repaired)"),
    "mgir_orig": dict(code="authors' iterative refinement", preconditioner="FP32 V-cycle, fine level original stencil"),
    "mgir_rep": dict(code="authors' iterative refinement", preconditioner="FP32 V-cycle, fine level difference-form stencil (repaired)"),
}


def block_t27():
    for ln, r in csv_rows(T27M):
        k, path, wl = int(r["k"]), r["path"], r["workload"]
        cc = lambda col, **kw: C(T27M, ln, r, col, **kw)
        if wl.startswith("reference"):
            continue
        base = dict(block="C_hou_matched", device=DEVICE,
                    provenance="T27 (" + r["endpoint_status"] + ")",
                    system=HOU_SYSTEM.replace("2k x k x k", f"{2*k}x{k}x{k}"),
                    elements=cc("n_elem"), dofs=cc("ndof"),
                    operator=cc("op_variant"), operator_precision=cc("operator_precision"),
                    residual_precision=cc("residual_precision", missing="not applicable (application only)"),
                    iterate_precision=cc("iterate_precision", missing="not applicable (application only)"),
                    native_stop=cc("native_stop", missing="not applicable (application only)"), times={}, memory={}, notes=[])
        setup_boundary = ("Hou: (a) autowrite + import + killer + survivor, (b) killer + survivor; exploratory re-measurement with the plan's "
                          "boundaries (setup_source_file)" if path == "hou_cg32" else
                          "ours: (a) first build incl. compilation (load, mask, operators, GMG, first update); (b) second identical build")
        if wl.startswith("application") and path != "hou_cg32":
            setup_boundary = B("ours, application process: (a) system construction (load, supports, fixed-DOF mask), mask copy to the device and "
                               "one operator construction including its kernel compilation; (b) the same again; no multigrid hierarchy and no "
                               "update, so this is not a hierarchy setup cost and is not comparable with the solve rows' setup",
                               "tasks/T27/drivers/hrun.py:157-163; code/src/voxfem/operators.py:595-608 (Operator.__init__ compiles the kernel)")
        if wl.startswith("application"):
            rr = dict(base, id=f"hou_T27_k{k}_{path}_application", workload="one operator application (field R)",
                      code={"hou_cg32": "Hou et al. honorAb (released)", "stencil32_orig": "authors' original 27-point stencil, FP32",
                            "stencil32_rep": "authors' difference-form stencil, FP32 (repaired)",
                            "hoist64_ref": "authors' FP64 node_hoist operator"}[path],
                      role={"hou_cg32": "the Krylov operator of Hou's CG",
                            "stencil32_orig": "fine-level operator of the original FP32 V-cycle (FP64 PCG) and the inner Krylov operator of original IR",
                            "stencil32_rep": "fine-level operator of the repaired FP32 V-cycle (FP64 PCG) and the inner Krylov operator of repaired IR",
                            "hoist64_ref": "the FP64 Krylov operator of both FP64 PCG paths"}[path],
                      krylov_precision="not applicable", start="not applicable",
                      status=cc("outcome"))
            rr["times"]["application"] = dict(cc("apply_median_s"), unit="s", denominator="per application",
                                              statistic="median of 11 single-call GPU-event intervals after 3 warm-up calls (E10 protocol); IQR in the source row",
                                              boundary="one call; Hou's includes its per-call allocations as released",
                                              timing_flag=cc("timing_flag"))
            rr["times"]["application_iqr"] = [cc("apply_iqr_lo_s"), cc("apply_iqr_hi_s")]
            rr["action_error_R"] = cc("d_R")
            rr["action_error_S"] = cc("d_S")
            rr["timing_flag"] = cc("timing_flag")
            rr["memory"]["process_dedicated_peak"] = dict(cc("process_dedicated_peak_bytes"), unit="B",
                                                          definition="max WDDM dedicated usage of the process over its life (1 s sampler)")
            rr["setup"] = dict(a=cc("setup_a_s", missing="not recorded"), b=cc("setup_b_s", missing="not recorded"),
                               status=cc("setup_status", missing="not recorded"),
                               source_record=cc("setup_source_file", missing="not recorded"), unit="s", boundary=setup_boundary)
            rows.append(rr)
            continue
        # state solves
        p = T27_PATHS[path]
        cls = r["outcome_class"]
        expl = r["exploratory_class"]
        rr = dict(base, id=f"hou_T27_k{k}_{path}_solve", workload="one state solve from zero", start="zero",
                  code=p["code"], preconditioner=p["preconditioner"],
                  krylov_precision=B({"hou_cg32": "FP32 unpreconditioned CG", "mg64_orig": "FP64 PCG", "mg64_rep": "FP64 PCG",
                                      "mgir_orig": "inner FP32 PCG", "mgir_rep": "inner FP32 PCG"}[path],
                                     "tasks/T27/drivers/hsys.py:61-64 (pcg64 for mg64, ir_lean for mgir); released CG on FP32 arrays "
                                     "(tasks/T27/drivers/hou_instr.py, U = cp.zeros(NP3, 'f') in hrun.py:250)"),
                  status=dict(cc("outcome"), class_=num(cls) if cls else None, exploratory_class=num(expl) if expl else None),
                  steps=cc("native_iterations", missing="no completed solve"), inner_steps=cc("inner_iterations", missing="not applicable or no completed solve"))
        ind = cc("independent_rel_true_native", missing="no independent check (breakdown, or not applicable)")
        if k == 160 and ind["v"] is not None:
            ind["qualification"] = "exploratory: replacement checker outside the plan's repeat conditions (T27 D9)"
        rr["achieved_true_residual"] = dict(ind, kind="independent FP64 checker process, FP64 node mapping")
        rr["insolver_residual"] = dict(cc("insolver_rel_true_native", missing="not formed by this solver"),
                                       kind="FP64 true residual (mg64), outer FP64 residual (IR); Hou's solver forms none")
        if path == "hou_cg32":
            rr["recursive_residual_at_native_stop"] = cc("recursive_rel_residual_native")
            rr["recursive_residual_at_10000"] = cc("recursive_rel_residual_10000")
            rr["smallest_checked_true_residual"] = cc("smallest_true_residual")
            rr["smallest_checked_true_residual_iteration"] = cc("smallest_true_residual_iteration")
            rr["attained_1e-5"] = cc("attained_1e-5")
        n = rr["inner_steps"] if path.startswith("mgir") else rr["steps"]
        if ind["v"] is None:
            rr["residual_factor_per_step"] = M("not computed: no completed solve and no independent residual (numerical breakdown)")
        else:
            rr["residual_factor_per_step"] = gm_factor(rr["achieved_true_residual"], ZERO_START, n, True,
                                                       "n = inner FP32 PCG iterations" if path.startswith("mgir") else
                                                       ("n = unpreconditioned FP32 CG iterations" if path == "hou_cg32" else "n = FP64 PCG iterations"))
        if ind["v"] is not None and k == 160:
            rr["residual_factor_per_step"]["qualification"] = "rests on the exploratory k = 160 checker value"
        rr["compliance_rel_err"] = cc("compliance_rel_err", missing="no independent check")
        rr["energy_rel_err"] = cc("energy_rel_err", missing="no independent check")
        rr["compliance_at_reference_resolution"] = cc("compliance_at_reference_resolution", missing="no independent check")
        planned = 1 if (path == "hou_cg32" and k == 256) else 3
        rec = cc("source_file")["v"]
        observed = len(load(rec)["timed"])
        n_obs = D(observed, "number of entries in the record's list of timed solves", op="len", file=rec, path=["timed"])
        n_obs["from"] = [rec + "#/timed"]
        solved = cc("solve_median_s")["v"] is not None
        assert observed == (planned if solved else 0), (rec, observed, planned, solved)
        rr["times"]["solve"] = dict(cc("solve_median_s", missing="no completed solve"), unit="s", denominator="per solve",
                                    statistic=("no timed solve completed (numerical breakdown); median not available" if not observed else
                                               "one timed solve" if observed == 1 else f"median of {observed} cold solves"),
                                    n_timed_solves_planned=B(planned, "tasks/T27/ANALYSIS_PLAN.md:109-111"),
                                    n_timed_solves=n_obs,
                                    sample_rule=B("T27 planned the number of timed solves by code and grid size: ours 3 at every k; Hou's CG 3 at k = 80 and 160, "
                                                  "1 at k = 256 (planned count; the observed count is n_timed_solves)", "tasks/T27/ANALYSIS_PLAN.md:109-111"),
                                    boundary="solver call between device synchronizations, setup excluded",
                                    timing_flag=cc("timing_flag"))
        STEP_BOUNDARY = {
            "hou_cg32": B("one CUDA event at the start of each CG iteration (on_iter hook of the instrumented copy); a step is the interval "
                          "from one iteration start to the next, the last one ending at the solve's end event",
                          "tasks/T27/drivers/hou_instr.py:39-41; tasks/T27/drivers/hrun.py:248-257"),
            "mg64": B("one CUDA event at the entry of each preconditioner call (EvM); a step is the interval from one entry to the next, "
                      "i.e. one full PCG iteration (operator, dot products, updates, V-cycle)",
                      "tasks/T27/drivers/hsys.py:70-81; tasks/T27/drivers/hrun.py:325-327"),
            "mgir": B("one CUDA event at the entry of each inner preconditioner call, tagged with the outer step; a step is the interval from "
                      "one entry to the next within the same outer step (intervals that span an outer FP64 residual are dropped)",
                      "tasks/T27/drivers/hsys.py:70-98 (EvR increments the tag); tasks/T27/drivers/hrun.py:325-327"),
        }
        rr["times"]["krylov_step"] = dict(cc("krylov_step_median_ms", missing="no completed solve"), unit="ms",
                                          denominator="per Krylov step (inner step for IR)",
                                          statistic="median over the steps of the timed solve; IQR in the source row",
                                          boundary=STEP_BOUNDARY["hou_cg32" if path == "hou_cg32" else path[:4]],
                                          timing_flag=cc("timing_flag"))
        rr["applications"] = dict(
            krylov_operator_row=f"hou_T27_k{k}_" + {"hou_cg32": "hou_cg32", "mg64_orig": "hoist64_ref", "mg64_rep": "hoist64_ref",
                                                     "mgir_orig": "stencil32_orig", "mgir_rep": "stencil32_rep"}[path] + "_application",
            vcycle_fine_level_row=(None if path == "hou_cg32" else
                                   f"hou_T27_k{k}_stencil32_{'orig' if path.endswith('orig') else 'rep'}_application"),
            note="FP64 PCG: FP64 node operator in the Krylov iteration, FP32 stencil on the V-cycle's fine level; "
                 "IR: the FP32 stencil is both the inner Krylov operator and the V-cycle's fine level")
        if path.startswith("mgir"):
            rr["times"]["outer_residual_per_outer_step"] = dict(cc("outer_residual_ms_mean_per_outer", missing="no completed solve"), unit="ms",
                                                                denominator="mean per outer step")
        if path == "hou_cg32":
            rr["times"]["solve_start_overhead"] = dict(cc("start_overhead_ms"), unit="ms",
                                                       boundary="solve call to first CG iteration: load and support construction, survivor indexing, residual formation, gc.collect")
        rr["setup"] = dict(a=cc("setup_a_s", missing="not recorded"), b=cc("setup_b_s", missing="not recorded"),
                           status=cc("setup_status", missing="not recorded"),
                           source_record=cc("setup_source_file", missing="not recorded"), unit="s", boundary=setup_boundary)
        rr["memory"]["H3_process_dedicated_peak"] = dict(cc("process_dedicated_peak_bytes"), unit="B",
                                                         definition="process-life WDDM dedicated peak of the timed solve process; covers a second build, so NOT a single-solve peak (T27 D14)")
        # exploratory single-build memory
        rr["memory"]["comparison_status"] = dict(
            J("tasks/T27/predictions.json", "predictions", "P6", "outcome"),
            note="the prespecified memory comparison uses the timed solve processes, whose peaks retain two builds; it is inconclusive. "
                 "Any ordering of the single-build peaks below is exploratory and not a confirmatory memory result.")
        try:
            lnx, rx = find_csv(T27X, k=str(k), path=path, workload="EXPLORATORY single build + single solve (memory)")
            watched = "coverage held from the watcher's first sampler baseline" in (rx.get("note") or "")
            for col, nm, de in (("pool_used_peak_bytes", "pool_used_peak", "CuPy pool used bytes, hook on throughout"),
                                ("pool_reserved_peak_bytes", "pool_reserved_peak", "CuPy pool reserved bytes"),
                                ("process_dedicated_peak_bytes", "process_dedicated_peak", "max WDDM dedicated usage of the process over its samples (1 s sampler)"),
                                ("device_peak_bytes", "device_peak", "max nvidia-smi memory.used over the samples taken while the process ran (device-wide, includes other processes)"),
                                ("device_baseline_bytes", "device_baseline", "nvidia-smi memory.used before the process allocates")):
                c = C(T27X, lnx, rx, col, missing=rx.get("outcome") or "missing")
                rr["memory"]["single_build_" + nm] = dict(c, unit="B", definition=de + "; separate run with one build and one solve (exploratory, T27 D17)")
                if watched and nm in ("process_dedicated_peak", "device_peak"):
                    rr["memory"]["single_build_" + nm]["coverage"] = dict(
                        C(T27X, lnx, rx, "note"),
                        reading="sampling coverage from the watcher's first sampler baseline onward, not over the whole process; "
                                "that baseline already held shared memory (value in the cited note)")
        except LookupError:
            pass
        rr["timing_flag"] = cc("timing_flag")
        rr["spill"] = cc("spilled")
        rows.append(rr)
    # T27 ratios recomputed from the medians (orientation check)
    for k in (80, 160, 256):
        for a, b, lab in (("mg64_rep", "mg64_orig", "repaired / original FP64 PCG solve time"),
                          ("mgir_rep", "mgir_orig", "repaired / original IR solve time")):
            ra = next(x for x in rows if x["id"] == f"hou_T27_k{k}_{a}_solve")
            rb = next(x for x in rows if x["id"] == f"hou_T27_k{k}_{b}_solve")
            pairs.append(dict(id=f"hou_T27_k{k}_{a}_over_{b}", rows=[ra["id"], rb["id"]],
                              value=ratio(ra["times"]["solve"], rb["times"]["solve"], lab), orientation=lab,
                              qualification="k = 160 exploratory (action check from the replacement checker)" if k == 160 else None))
        ra = next(x for x in rows if x["id"] == f"hou_T27_k{k}_hou_cg32_application")
        for o in ("stencil32_orig", "stencil32_rep"):
            rb = next(x for x in rows if x["id"] == f"hou_T27_k{k}_{o}_application")
            pairs.append(dict(id=f"hou_T27_k{k}_application_hou_over_{o}", rows=[ra["id"], rb["id"]],
                              value=ratio(ra["times"]["application"], rb["times"]["application"], f"Hou application / {o} application"),
                              orientation="Hou / ours (>1: Hou slower)",
                              qualification="k = 160 exploratory (G2 action gate on the replacement checker)" if k == 160 else None))
        rb = next(x for x in rows if x["id"] == f"hou_T27_k{k}_stencil32_rep_application")
        rc = next(x for x in rows if x["id"] == f"hou_T27_k{k}_stencil32_orig_application")
        pairs.append(dict(id=f"hou_T27_k{k}_application_rep_over_orig", rows=[rb["id"], rc["id"]],
                          value=ratio(rb["times"]["application"], rc["times"]["application"], "repaired / original stencil application"),
                          orientation="repaired / original (>1: repaired slower)",
                          qualification="k = 160 exploratory" if k == 160 else None))
        ra = next(x for x in rows if x["id"] == f"hou_T27_k{k}_hou_cg32_solve")
        rb = next(x for x in rows if x["id"] == f"hou_T27_k{k}_mg64_rep_solve")
        if k == 160:
            lab_acc = ("accuracy relationship from exploratory evidence only: both independent residuals at this grid come from the "
                       "replacement checker outside the plan's repeat conditions (T27 D9), and the prespecified every-grid test of Hou's "
                       "native-stop residual (T27 P1) is unresolved; no equal-accuracy ratio exists (Hou attains 1e-5 at no checkpoint)")
        else:
            lab_acc = "at unequal accuracy (confirmatory independent residuals); no equal-accuracy ratio exists (Hou attains 1e-5 at no checkpoint)"
        pairs.append(dict(id=f"hou_T27_k{k}_solve_hou_over_mg64_rep", rows=[ra["id"], rb["id"]],
                          value=ratio(ra["times"]["solve"], rb["times"]["solve"], "Hou native solve / mg64_rep solve"),
                          orientation="Hou / ours", label=lab_acc,
                          accuracy_evidence=dict(hou=ra["achieved_true_residual"], ours=rb["achieved_true_residual"],
                                                 prespecified_test=J("tasks/T27/predictions.json", "predictions", "P1", "outcome")),
                          qualification=("k = 160 exploratory (independent residuals and action check from the replacement checker)"
                                         if k == 160 else None)))
    # capacity of the Hou-system workloads (lower bounds; T27 REPORT section 4)
    for cfg, path, lb, nxt in (("Hou et al. CuPy CG (native stop)", "hou_cg32", 256, None),
                               ("authors' FP64 PCG, original stencil V-cycle", "mg64_orig", 256, None),
                               ("authors' FP64 PCG, repaired V-cycle", "mg64_rep", 256, None), ("authors' IR, repaired", "mgir_rep", 256, None),
                               ("authors' IR, original stencil", "mgir_orig", 80, 160)):
        rl = next(x for x in rows if x["id"] == f"hou_T27_k{lb}_{path}_solve")
        rn = next(x for x in rows if x["id"] == f"hou_T27_k{nxt}_{path}_solve") if nxt else None
        largest.append(dict(configuration=cfg + " on Hou's system (T27)", workload="state solve from zero",
                            largest_pass_elements=rl["elements"], largest_pass_row=rl["id"],
                            largest_pass_status=dict(rl["status"], achieved_true_residual=rl["achieved_true_residual"]),
                            next_size_elements=rn["elements"] if rn else None, next_size_row=rn["id"] if rn else None,
                            next_size_status=(dict(rn["status"], note="also at 33.6M: numerical breakdown (FP32 corrections rejected down to the inner-tolerance floor)")
                                              if rn else "no larger size in the plan"),
                            provenance="T27 confirmatory"))


# ----------------------------------------------------------------------------------------------------------------
# D. T28: Traeff et al.'s released OpenMP-offload code, fixed states S1 and S5
# ----------------------------------------------------------------------------------------------------------------
T28C = "tasks/T28/comparison.csv"
T28H = "tasks/T28/residual_histories"


def hist_start(k, state, path):
    rel = f"{T28H}/{k}_{state}_{path}.csv"
    if not resolve(rel).exists():
        return M("no residual history for this (k, state, path)")
    for ln, r in csv_rows(rel):
        it = r.get("iteration") if "iteration" in r else r.get("outer_step")
        if str(it) == "0":
            col = "independent_fp64_residual" if "independent_fp64_residual" in r else "fp64_true_residual"
            return C(rel, ln, r, col)
    return M("no iteration-0 entry in the history")


def g4_step_text(act, bound):
    if act == "unresolved":
        return f"interference rule unresolved at step duration (bound {bound:.1f} %)"
    if act in ("ok", "flagged"):
        return f"5 % rule met at step duration (bound {bound:.2f} %)"
    return "not evaluated"


T28_LIMIT = J("tasks/T28/g4_activity.json", "limitation")


def block_t28():
    for ln, r in csv_rows(T28C):
        cc = lambda col, **kw: C(T28C, ln, r, col, **kw)
        k, st, path = int(r["k"]), r["state"], r["path"]
        cls = num(r["class"])
        desc = k in (256, 320) and cls == 8
        prov = "T28" + (" (descriptive completion: system-identity gate and independent residual missing)" if desc else "")
        rr = dict(id=f"traeff_T28_k{k}_{st}_{path}", block="D_traeff_fixed_state", device=DEVICE, provenance=prov,
                  workload=f"one state solve at fixed state {st} ({'released iteration-1 state, x = 0.2' if st == 'S1' else 'density of the released fifth solve'})",
                  system=f"Traeff et al.'s cantilever {2*k}x{k}x{k} (their loads, supports, modulus law E = Emin + x^3 (E0 - Emin), Emin = 1e-6), free-DOF system",
                  elements=cc("active_elements"), allocated_elements=cc("allocated_elements"), dofs=cc("free_dofs"),
                  start=cc("start"), code="Traeff et al. TopOpt-in-OpenMP-GPU (released; nvc 26.11 build, cc89)" if path == "traeff" else "authors' solver",
                  operator=cc("operator"), preconditioner=cc("preconditioner"), operator_precision=cc("operator"),
                  krylov_precision=cc("krylov_precision"), residual_precision=cc("residual_precision"),
                  iterate_precision=cc("iterate_precision"), native_stop=cc("native_stop_rule"),
                  status=dict(cc("class_label"), class_=cls), steps=cc("steps", missing="no solve"),
                  inner_steps=cc("inner_iterations", missing="not applicable or no solve"), times={}, memory={}, notes=[])
        if r["note"]:
            rr["notes"].append(r["note"])
        ind = cc("independent_residual", missing="no independent check (k >= 256: the checker spilled; or no solve)")
        rr["achieved_true_residual"] = dict(ind, kind="independent FP64 checker (K2) on the iterate of the first timed solve")
        ins = cc("insolver_residual", missing="no solve")
        rr["insolver_residual"] = dict(ins, kind=r["residual_precision"])
        start = hist_start(k, st, path) if st == "S5" else (ZERO_START if r["start"] == "zero" else M("start residual not recorded"))
        rr["start_true_residual"] = start
        n = rr["inner_steps"] if path == "mgir_rep" else rr["steps"]
        nk = "n = inner FP32 PCG iterations" if path == "mgir_rep" else ("n = released FP32 PCG steps" if path == "traeff" else "n = FP64 PCG iterations")
        if ind["v"] is not None:
            rr["residual_factor_per_step"] = gm_factor(ind, start, n, True, nk)
        elif path != "traeff" and ins["v"] is not None:
            f = gm_factor(ins, start, n, True, nk + "; r_end = in-solver FP64 residual (no independent check)")
            if f.get("v") is not None:
                f["qualification"] = "in-solver FP64 residual, not independently checked"
            rr["residual_factor_per_step"] = f
        else:
            rr["residual_factor_per_step"] = M("not computed: no FP64 true residual at the native stop (released in-solver residual is FP32 recursive)")
        for col, nm in (("smallest_residual", "smallest_checked_true_residual"), ("smallest_residual_iteration", "smallest_checked_true_residual_iteration"),
                        ("attained_1e-5", "attained_1e-5")):
            rr[nm] = cc(col, missing="not available")
        boundary = cc("timing_boundary", missing="not run")
        rr["setup"] = dict(a=cc("setup_a_s", missing="no run"), b=cc("setup_b_s", missing="no run"), unit="s", boundary=boundary,
                           g4=cc("g4_setup_activity", missing="not evaluated"))
        g4_solve = dict(activity=cc("g4_activity", missing="not evaluated"), strict_activity=cc("g4_strict_activity", missing="not evaluated"),
                        strict_bound_max_pct=cc("g4_strict_bound_max_pct", missing="not evaluated"),
                        scope="whole fixed-state solves only; the bound does not carry over to a Krylov step (T28 D34)")
        rr["times"]["solve"] = dict(cc("solve_median_s", missing="no run"), unit="s", denominator="per solve",
                                    statistic=f"median of {r['n_timed_solves'] or '0'} timed solves", boundary=boundary, g4=g4_solve,
                                    n_timed_solves=cc("n_timed_solves", missing="no run"),
                                    sample_rule=B("T28 fixed the number of timed solves by duration: released code 3 solves in one process when "
                                                  "the first took <= 120 s, otherwise that one solve; ours 3", "tasks/T28/ANALYSIS_PLAN.md:149-152"))
        sact, sb = r["g4_step_strict_activity"], num(r["g4_step_strict_bound_pct"])
        rr["times"]["krylov_step"] = dict(cc("krylov_step_median_ms", missing="no run"), unit="ms",
                                          denominator="per Krylov step (inner step for IR)",
                                          statistic="median over the steps of the timed solve", boundary=boundary,
                                          g4_step=dict(activity=cc("g4_step_strict_activity", missing="not evaluated"),
                                                       bound_pct=cc("g4_step_strict_bound_pct", missing="not evaluated"),
                                                       basis=cc("g4_step_basis", missing="not evaluated")),
                                          g4_step_reading=(g4_step_text(sact, sb) if sact else "not evaluated"),
                                          qualification=("released step times from the timing build; its overhead gate G5 failed (timing build 10.4 % faster than the plain build), so they are flagged" if path == "traeff" else None))
        if path == "mgir_rep":
            rr["times"]["outer_residual_per_outer_step"] = dict(cc("outer_residual_mean_ms", missing="no run"), unit="ms", denominator="mean per outer step")
        rr["times"]["g4_whole_solve"] = cc("g4_activity", missing="not evaluated")
        rr["g4_limitation"] = T28_LIMIT
        rr["memory"]["M1"] = dict(cc("M1_job_dedicated_peak_bytes", missing="no run"), unit="B", definition=r["memory_definition"] or "M1: job dedicated peak")
        rr["memory"]["M2_device_growth"] = dict(cc("M2_device_growth_bytes", missing="no run"), unit="B", definition="nvidia-smi device-wide growth over baseline (includes other processes)")
        rr["memory"]["M3_pool_used"] = dict(cc("M3_pool_used_peak_bytes", missing="not applicable (released code) or no run"), unit="B", definition="CuPy pool used peak")
        rr["memory"]["M4_host_VmHWM_kB"] = dict(cc("M4_host_VmHWM_kB", missing="ours: not applicable; or no run"), unit="kB", definition="host peak of the released driver (VmHWM)")
        rr["admission"] = dict(predicted=cc("admission_predicted_bytes", missing="not recorded"), driver_free=cc("admission_driver_free_bytes", missing="not recorded"))
        rr["spill_growth"] = cc("spill_growth_bytes", missing="not recorded")
        rr["source_record"] = cc("source_file")
        rows.append(rr)

    def acc_label(ra, rb):
        a, b = val(ra["achieved_true_residual"]), val(rb["achieved_true_residual"])
        if a is None or b is None:
            return "accuracy relationship unresolved (no independent residual for at least one path)"
        if (a <= 1e-5) != (b <= 1e-5):
            return f"at unequal accuracy (independent FP64 residuals {a:.2e} and {b:.2e})"
        return f"both {'at or below' if a <= 1e-5 else 'above'} 1e-5 (independent FP64 residuals {a:.2e} and {b:.2e})"

    def step_label(*rs):
        parts, unres = [], False
        for x in rs:
            g = x["times"]["krylov_step"]["g4_step"]
            act, bd = val(g["activity"]), val(g["bound_pct"])
            unres |= act == "unresolved"
            parts.append(re.split(r"_S[15]_", x["id"])[-1] + ": "
                         + (f"{act}, bound {bd:.2f} %" if bd is not None else "not evaluated"))
        return ("as measured; interference rule unresolved at step duration (" if unres else "as measured; 5 % rule met at step duration (") + "; ".join(parts) + ")"

    for k in (64, 128, 160, 256, 320):
        for st in ("S1", "S5"):
            try:
                ra = next(x for x in rows if x["id"] == f"traeff_T28_k{k}_{st}_traeff")
                rb = next(x for x in rows if x["id"] == f"traeff_T28_k{k}_{st}_mg64_rep")
                rc = next(x for x in rows if x["id"] == f"traeff_T28_k{k}_{st}_mg64_orig")
            except StopIteration:
                continue
            if ra["times"]["solve"]["v"] is None:
                continue
            pairs.append(dict(id=f"traeff_T28_k{k}_{st}_solve_traeff_over_mg64_rep", rows=[ra["id"], rb["id"]],
                              value=ratio(ra["times"]["solve"], rb["times"]["solve"], "released / mg64_rep solve median"),
                              orientation="released / ours (>1: released slower)",
                              label=acc_label(ra, rb) + ("; descriptive (system-identity gate missing)" if k >= 256 else "")
                                    + "; whole-solve interference bounds: none excludable"))
            pairs.append(dict(id=f"traeff_T28_k{k}_{st}_step_traeff_over_mg64_rep", rows=[ra["id"], rb["id"]],
                              value=ratio(ra["times"]["krylov_step"], rb["times"]["krylov_step"], "released / mg64_rep Krylov-step median"),
                              orientation="released / ours", label="descriptive (G5 failed); " + step_label(ra, rb)))
            if st == "S1" and rc["times"]["krylov_step"]["v"] is not None:
                pairs.append(dict(id=f"traeff_T28_k{k}_S1_step_mg64_rep_over_mg64_orig", rows=[rb["id"], rc["id"]],
                                  value=ratio(rb["times"]["krylov_step"], rc["times"]["krylov_step"], "repaired / original FP64-PCG Krylov-step median"),
                                  orientation="repaired / original (>1: repaired slower)",
                                  label=("original-stencil window ran at a low SM clock (T28 D17); " if k == 64 else "") + step_label(rb, rc)))
    # T28 design loops: each its own workload, no ratio (the released update could not be matched)
    dw = "tasks/T28/design_workload.csv"
    DESIGN_TIMER = {
        "N": B("from the return of the state solve to the end of the density transfer (target update to(xPhys)); N makes no dumps",
               "tasks/T28/ANALYSIS_PLAN.md:153-156; tasks/T28/DEVIATIONS.md:429-432"),
        "R": B("instrumented: the record driver's design timer starts after the untimed FP64 compliance transfer and the level-2 dumps, "
               "and in iterations 1-4 sums pieces separated by the dc dumps; it is not the interval from solve return to the end of the update",
               "tasks/T28/DEVIATIONS.md:429-432 (released/t28_driver.c:338-379)"),
        "L": B("the same operations as the released design step (compliance and sensitivity, volume, filter, OC update, change, density filter), "
               "between device synchronizations", "tasks/T28/ANALYSIS_PLAN.md:153-157"),
    }
    groups = {}
    for ln, r in csv_rows(dw):
        groups.setdefault((int(r["k"]), r["code"], r["workload"]), []).append((ln, r))
    for (k, code, wl), lst in sorted(groups.items()):
        wk = "N" if "native" in wl else "R" if "record" in wl else "L"
        sol = [C(dw, ln, r, "solve_s") for ln, r in lst]
        des = [C(dw, ln, r, "design_step_s") for ln, r in lst]
        solv = [c for c in sol if c["v"] is not None]
        desv = [c for c in des if c["v"] is not None]

        def g4count(col):
            out = {}
            for ln, r in lst:
                out[r[col] or "not evaluated"] = out.get(r[col] or "not evaluated", 0) + 1
            return dict(counts=out, cells=[C(dw, ln, r, col, missing="not evaluated") for ln, r in lst])
        unres = [dict(iteration=C(dw, ln, r, "iteration"), bound_pct=C(dw, ln, r, "g4_solve_strict_bound_pct"))
                 for ln, r in lst if r["g4_solve_strict_activity"] == "unresolved"]
        rr = dict(id=f"traeff_T28_design_k{k}_{code}_{wk}",
                  block="D2_traeff_design_workload", device=DEVICE, provenance="T28 (distinct workloads; no ratio)",
                  workload=wl, system=f"Traeff et al.'s cantilever {2*k}x{k}x{k}, design loop from the released initial state",
                  elements=D(2 * k ** 3, "2 k^3 for the grid 2k x k x k", C(dw, lst[0][0], lst[0][1], "k"), op="two_k_cubed"),
                  code=code, operator_precision="as in the fixed-state rows of the same path",
                  krylov_precision="as in the fixed-state rows", residual_precision="as in the fixed-state rows",
                  iterate_precision="FP64", native_stop="as in the fixed-state rows",
                  status=B("design loop ran; update rules differ (the released build's sensitivity filter has no effect), so no design iteration is a matched workload",
                           "tasks/T28/predictions.json#/P8; tasks/T28/update_checks.json"),
                  setup=dict(per_solve=[C(dw, ln, r, "per_solve_setup_s", missing="not recorded") for ln, r in lst], unit="s",
                             boundary="per-solve setup inside the design iteration, as the fixed-state rows of the same path define it"),
                  design_iterations=D(len(lst), "number of design-iteration rows", *sol, op="count"),
                  steps_per_solve=[C(dw, ln, r, "steps") for ln, r in lst],
                  insolver_residual_per_solve=dict(
                      cells=[C(dw, ln, r, "insolver_residual", missing="not recorded") for ln, r in lst],
                      kind=(B("the released code's own recursive relative residual ||r||/||b|| at its stop (its native-stop quantity), "
                              "printed by the driver per design iteration; not an FP64 true residual",
                              "tasks/T28/drivers/collect.py:623, 633 (relres of the run's meta.txt)") if code == "traeff" else
                            B("the solver's in-process FP64 residual at its stop (FP64 PCG: true residual with the FP64 node operator; "
                              "IR: outer FP64 residual), with the operator of the fixed-state rows of the same path",
                              "tasks/T28/drivers/ours.py:540 (insolver_rel_res = st['rel_true']); tasks/T28/drivers/collect.py:649"))),
                  achieved_true_residual=M("no independent check of the design-loop states is recorded (T28 checked the fixed states S1 and S5)"),
                  times=dict(solve_median=dict(D(statistics.median(c["v"] for c in solv), "median of solve_s over the iterations", *solv, op="median"),
                                               unit="s", denominator="per design-iteration state solve",
                                               g4=dict(g4count("g4_solve_strict_activity"), unresolved=unres,
                                                       reading=("unresolved for iterations " + ", ".join(str(val(u["iteration"])) for u in unres)
                                                                + " (bounds " + ", ".join(f"{val(u['bound_pct']):.1f}" for u in unres) + " %); the others clear the 5 % threshold at whole-solve resolution"
                                                                if unres else "every solve clears the 5 % threshold at whole-solve resolution"))),
                             design_step_median=(dict(D(statistics.median(c["v"] for c in desv), "median of design_step_s over the iterations", *desv, op="median"),
                                                      unit="s", denominator="per design step", boundary=DESIGN_TIMER[wk],
                                                      g4=dict(g4count("g4_design_strict_activity"),
                                                              note=("whole-job bounds only; no constant-offset reading (T28 D36)" if wk == "R" else
                                                                    "design steps shorter than the 5-s counter interval are unresolved, not interference"))
                                                      ) if desv else M("no design-step time"))),
                  g4_limitation=T28_LIMIT,
                  memory=dict(peak=M("see the fixed-state rows (M1) of the same size")), notes=[])
        if wk == "R":
            rr["notes"].append("instrumented record run (dumps outside the timed intervals; G6 failed): not native loop times")
        rows.append(rr)
    rows.append(dict(id="traeff_T28_step_check", block="D2_traeff_design_workload", device=DEVICE, provenance="T28",
                     workload="one complete released design step from the same inputs, against the planned matched rule",
                     system="Traeff et al.'s cantilever at k = 64, 128, 160", status=J("tasks/T28/predictions.json", "P8", "outcome"),
                     setup=M("not applicable (operation-level check, untimed)"),
                     times={}, memory={}, notes=["the released build's sensitivity filter returns dc unchanged and dv = 1 (T28 D14)"]))
    cap = "tasks/T28/capacity.json"
    for key, lab in (("traeff/fixed_S1", "Traeff et al. released code"), ("mg64_rep/fixed_S1", "authors' FP64 PCG (repaired)"),
                     ("mg64_orig/fixed_S1", "authors' FP64 PCG (original V-cycle)"), ("mgir_rep/fixed_S1", "authors' IR (repaired)")):
        PLAIN = {"guard refusal": "not admitted: predicted peak + 1.5 GiB exceeds the driver-reported free memory (a prediction, not a measured limit)",
                 "spill": "stopped by the spill sampler: shared GPU memory grew by more than 256 MiB",
                 "native stop met, independent residual > 1e-5 or missing": "completed with the native stop met; independent FP64 residual missing (the checker spilled at 33.6M)"}
        for tier in ("run_completed", "verified"):
            t = load(cap)[key][tier]
            if t["largest_k"] is None:
                st = "never verified: native stop met at every completed size, independent FP64 residual above 1e-5 (8.19M and below) or missing (33.6M and 65.5M)"
                nxt_el = None
            else:
                st = PLAIN.get(t["next_class_label"], t["next_class_label"])
                nxt_el = (D(2 * t["next_tested_k"] ** 3, "2 k^3 active elements of the next tested grid 2k x k x k",
                            J(cap, key, tier, "next_tested_k"), op="two_k_cubed") if t["next_tested_k"] else None)
            largest.append(dict(configuration=lab + " on Traeff's fixed state S1 (T28)",
                                workload="state solve from zero, " + ("run completed with native stop" if tier == "run_completed" else "verified (independent FP64 residual <= 1e-5)"),
                                largest_pass_elements=J(cap, key, tier, "active_elements"), allocated_elements=J(cap, key, tier, "allocated_elements"),
                                next_size_elements=nxt_el, next_size_status=st, next_class=J(cap, key, tier, "next_class_label"),
                                state=B("S1: the released iteration-1 state (x = 0.2), solve from zero", "tasks/T28/capacity.json#/" + key.replace("/", "~1")),
                                admission_rule=B("predicted peak + 1.5 GiB must fit the free memory the CUDA driver reports at the job's start",
                                                 "tasks/T28/ANALYSIS_PLAN.md:265"),
                                provenance="T28" + (" (65.5M: descriptive completion; system-identity gate and independent residual missing)" if tier == "run_completed" else "")))
    # S5 (warm start from the released fourth solution): it exists only where the released record run R completed its four
    # design iterations, i.e. up to k = 160; R reached its wall cap at k = 256 and was not run above it
    r_key = "traeff/design_loop_R"
    no_s5 = dict(class_by_k_256=J(cap, r_key, "by_k", "256"), note=J(cap, r_key, "note"))
    for key, lab in (("traeff/fixed_S5", "Traeff et al. released code"), ("mg64_rep/fixed_S5", "authors' FP64 PCG (repaired)"),
                     ("mg64_orig/fixed_S5", "authors' FP64 PCG (original V-cycle)"), ("mgir_rep/fixed_S5", "authors' IR (repaired)")):
        for tier in ("run_completed", "verified"):
            t = load(cap)[key][tier]
            if t["largest_k"] is None:
                st = ("never verified: the released solver reached its 1000-step iteration cap at every completed size (k = 64, 128, 160), "
                      "so its native stop was never met and the independent FP64 residual stayed above 1e-5")
                nxt_el = None
            else:
                st = ("no S5 state at the next tested grid (class 'not run'): S5 is the released fourth solution, and the released record run "
                      "that supplies it reached its wall cap at k = 256 and was not run above it")
                nxt_el = D(2 * t["next_tested_k"] ** 3, "2 k^3 active elements of the next tested grid 2k x k x k",
                           J(cap, key, tier, "next_tested_k"), op="two_k_cubed")
            e = dict(configuration=lab + " on Traeff's fixed state S5 (T28)",
                     workload="state solve from the released fourth solution, " + ("run completed" if tier == "run_completed" else "verified (independent FP64 residual <= 1e-5)"),
                     largest_pass_elements=J(cap, key, tier, "active_elements"), allocated_elements=J(cap, key, tier, "allocated_elements"),
                     next_size_elements=nxt_el, next_size_status=st, next_class=J(cap, key, tier, "next_class_label"),
                     state=B("S5: density of the released fifth solve, warm start from the released fourth solution", "tasks/T28/capacity.json#/" + key.replace("/", "~1")),
                     classes_by_k={kk: J(cap, key, "classes_by_k", kk) for kk in ("64", "128", "160", "256")},
                     no_s5_above=no_s5, provenance="T28")
            if key.startswith("traeff/") and tier == "run_completed":
                e["native_stop_met_largest_elements"] = J(cap, key, "native_stop_met", "active_elements")
                e["native_stop_met_next_class"] = J(cap, key, "native_stop_met", "next_class_label")
                e["next_size_status"] = ("completed at every size up to k = 160 by reaching the 1000-step iteration cap (native stop not met); "
                                         "no S5 state at k = 256 (the released record run reached its wall cap there)")
            largest.append(e)
    # design loops (each its own workload, no ratio): R completed through k = 160; at k = 256 it reached the wall cap
    ln256, r256 = find_csv(T28C, k="256", state="S5", path="traeff")
    loop_len = B("20 design iterations at k = 64, 4 at k = 128 and 160 (states 1-5)", "tasks/T28/ANALYSIS_PLAN.md:432-433")
    largest.append(dict(configuration="Traeff et al. released code, design loop (record run) (T28)",
                        workload="released design loop from the released initial state", design_iterations_rule=loop_len,
                        largest_completed_k=J(cap, r_key, "largest_completed_k"),
                        largest_pass_elements=D(2 * load(cap)[r_key]["largest_completed_k"] ** 3, "2 k^3 active elements of the grid 2k x k x k",
                                                J(cap, r_key, "largest_completed_k"), op="two_k_cubed"),
                        completed_by_k={kk: J(cap, r_key, "by_k", kk) for kk in ("64", "128", "160")},
                        next_size_elements=D(2 * 256 ** 3, "2 k^3 active elements of the grid 2k x k x k", C(T28C, ln256, r256, "k"),
                                             op="two_k_cubed"),
                        next_class=J(cap, r_key, "by_k", "256"),
                        next_size_status="interrupted: reached the 90-min wall cap (class 6) with the record driver's unchunked whole-vector transfers "
                                         "counting toward the process wall; its iterations are diagnostics of an interrupted invalid run, not design-loop results",
                        note=J(cap, r_key, "note"), provenance="T28"))
    for key, lab in (("mg64_rep/design_loop_L", "authors' FP64 PCG (repaired)"), ("mg64_orig/design_loop_L", "authors' FP64 PCG (original V-cycle)"),
                     ("mgir_rep/design_loop_L", "authors' IR (repaired)")):
        largest.append(dict(configuration=lab + ", matched-rule design loop (T28)",
                            workload="matched-rule design loop on the released system",
                            design_iterations_rule=B("the released iteration count of R: 20 design iterations at k = 64, 4 at k = 128 and 160",
                                                     "tasks/T28/ANALYSIS_PLAN.md:432-433, 454-455"),
                            largest_completed_k=J(cap, key, "largest_completed_k"),
                            largest_pass_elements=D(2 * load(cap)[key]["largest_completed_k"] ** 3, "2 k^3 active elements of the grid 2k x k x k",
                                                    J(cap, key, "largest_completed_k"), op="two_k_cubed"),
                            completed_by_k={kk: J(cap, key, "by_k", kk) for kk in ("64", "128", "160")},
                            next_size_elements=None,
                            next_class=B("not run", "tasks/T28/capacity.json#/" + key.replace("/", "~1") + "/by_k (no k = 256 entry); tasks/T28/REPORT.md:227"),
                            next_size_status="not run at k = 256: no completed released record run to start from", provenance="T28"))


# ----------------------------------------------------------------------------------------------------------------
# E. Precision controls: E8 (original stencil inside the FP32 iteration) and E29
# ----------------------------------------------------------------------------------------------------------------
E8_SOLVERS = {
    "jac32": ("FP32 Jacobi-PCG", "FP32", "FP32 recursive (true FP64 residual evaluated at checks, never used to stop)", "FP32"),
    "mg32": ("FP32 PCG + FP32 V-cycle", "FP32 original stencil", "FP32 recursive", "FP32"),
    "mg32_x64": ("FP32 PCG + FP32 V-cycle, solution accumulated in FP64", "FP32 original stencil", "FP32 recursive", "FP64"),
    "mg_ir": ("iterative refinement (inner FP32 PCG + V-cycle, outer FP64 residual)", "FP32 original stencil (inner), FP64 residual", "FP64 outer residual", "FP64"),
}


def block_precision():
    for p in sorted((PROJ / "results" / "E8").glob("floor_k*.json"), key=lambda p: (int(p.stem.split("_k")[1].split("_")[0]), p.stem)):
        rel = "results/E8/" + p.name
        d = load(rel)
        field = "uniform density 0.3" if d["field"] == "uniform" else "optimized design (saved field)"
        for s, (code, op, res, it) in E8_SOLVERS.items():
            rr = dict(id=f"prec_E8_k{d['k']}_{d['field']}_{s}", block="E_precision_controls", device=DEVICE,
                      provenance="historical record (submitted paper)", workload="one state solve from zero, diagnostic control",
                      system=f"authors' cantilever {2*d['k']}x{d['k']}x{d['k']}, {field}",
                      elements=J(rel, "n_elem"), dofs=M("not recorded"), start="zero", code=code,
                      operator=op, operator_precision=op, krylov_precision="FP32" if s != "mg_ir" else "inner FP32",
                      residual_precision=res, iterate_precision=it,
                      native_stop="recursive FP32 residual <= 1e-5 (no FP64 test)" if s != "mg_ir" else "outer FP64 residual <= 1e-5",
                      times={}, memory={}, notes=[])
            if s == "mg_ir":
                rr["status"] = B("certified (outer FP64 residual <= 1e-5)" if d["solvers"][s]["converged"] else "failed", rel + "#/solvers/mg_ir/converged")
                rr["steps"] = J(rel, "solvers", s, "outer")
                rr["inner_steps"] = J(rel, "solvers", s, "inner_iters")
                rr["achieved_true_residual"] = dict(J(rel, "solvers", s, "rel_true"), kind="outer FP64 residual at the stop (in-solver)")
                rr["start_true_residual"] = J(rel, "solvers", s, "rel_initial")
                rr["residual_factor_per_step"] = gm_factor(rr["achieved_true_residual"], rr["start_true_residual"], rr["inner_steps"], True,
                                                           "n = inner FP32 PCG iterations")
                rr["times"]["solve"] = dict(J(rel, "solvers", s, "time_s"), unit="s", denominator="per solve (one solve; accuracy study, no timing claim)")
            else:
                fp = d["solvers"][s]["first_monitored_pass"]
                rr["status"] = B("monitored pass reached; FP64 true residual above 1e-5" if fp and fp["true"] > 1e-5 else "monitored pass reached", rel + f"#/solvers/{s}/first_monitored_pass")
                rr["steps"] = J(rel, "solvers", s, "first_monitored_pass", "it")
                rr["achieved_true_residual"] = dict(J(rel, "solvers", s, "first_monitored_pass", "true"), kind="FP64 true residual at the first monitored pass")
                rr["insolver_residual"] = dict(J(rel, "solvers", s, "first_monitored_pass", "monitored"), kind="FP32 recursive")
                rr["floor_true_residual"] = J(rel, "solvers", s, "floor_true")
                rr["residual_factor_per_step"] = gm_factor(rr["achieved_true_residual"], ZERO_START, rr["steps"], True,
                                                           "n = FP32 PCG iterations to the first monitored pass")
            cons = d["consequence"][s]
            for kk in ("compliance_rel_err", "energy_norm_rel_err", "sens_rel_err_2", "sens_rel_err_max"):
                rr[kk] = J(rel, "consequence", s, kk)
            rr["reference_true_residual"] = J(rel, "reference", "rel_true_independent")
            rr["setup"] = M("not recorded in this accuracy study")
            rr["memory"]["peak"] = M("not measured in this accuracy study")
            rows.append(rr)
    for op in ("elem_mean", "elem_ref"):
        rel = f"results/E29/floor_k320_uniform_{op}_mg32_x64.json"
        d = load(rel)
        rr = dict(id=f"prec_E29_k320_uniform_{op}_mg32_x64", block="E_precision_controls", device=DEVICE,
                  provenance="historical record (submitted paper)", workload="one state solve from zero, diagnostic control",
                  system="authors' cantilever 640x320x320, uniform density 0.3", elements=J(rel, "n_elem"), dofs=M("not recorded"),
                  start="zero", code="FP32 PCG + FP32 V-cycle, solution accumulated in FP64",
                  operator={"elem_mean": "FP32 element kernel, element-mean reference (repaired)", "elem_ref": "FP32 element kernel, corner reference"}[op],
                  operator_precision="FP32", krylov_precision="FP32", residual_precision="FP32 recursive", iterate_precision="FP64",
                  native_stop="recursive FP32 residual <= 1e-5 (no FP64 test)", times={}, memory={}, notes=[])
        rr["status"] = B("monitored pass reached; FP64 true residual above 1e-5", rel + "#/solvers/mg32_x64/first_monitored_pass")
        rr["steps"] = J(rel, "solvers", "mg32_x64", "first_monitored_pass", "it")
        rr["achieved_true_residual"] = dict(J(rel, "solvers", "mg32_x64", "first_monitored_pass", "true"), kind="FP64 true residual at the first monitored pass")
        rr["residual_factor_per_step"] = gm_factor(rr["achieved_true_residual"], ZERO_START, rr["steps"], True, "n = FP32 PCG iterations to the first monitored pass")
        for kk in ("compliance_rel_err", "energy_norm_rel_err", "sens_rel_err_2", "sens_rel_err_max"):
            rr[kk] = J(rel, "consequence", "mg32_x64", kk)
        rr["setup"] = M("not recorded in this accuracy study")
        rr["memory"]["peak"] = M("not measured in this accuracy study")
        rows.append(rr)
    rel = "results/E29/beam_controls.json"
    d = load(rel)
    OPN = {"stencil": "original 27-point stencil", "stencil_diff": "difference-form stencil (repaired)",
           "elem_atomic": "atomic element kernel", "elem_ref": "element kernel, corner reference",
           "elem_mean": "element kernel, element-mean reference (repaired)", "stencil_selfcorr": "self-block correction",
           "fp64_arith_node": "factored node kernel in FP64 arithmetic on FP32 vectors"}
    VC = {"own_vcycle": ("own", "the operator's own FP32 V-cycle (fine level = the same operator)"),
          "common_vcycle": ("common", "the common FP32 V-cycle (fine level = original stencil), the same preconditioner for every operator")}
    for i, rw in enumerate(d["rows"]):
        k = rw["k"]
        for name, c in rw["controls"].items():
            op, vc = name.split("|")
            rr = dict(id=f"beam_E29_k{k}_{op}_{VC[vc][0]}", block="E_precision_controls", device=DEVICE, provenance="historical record (submitted paper)",
                      workload="one state solve from zero, single-precision control",
                      system=f"slender clamped beam 8x1x1, {k} elements through the depth (unit modulus, nu = 0.3, unit end load)",
                      elements=J(rel, "rows", i, "n_elem"), dofs=M("not recorded"), start="zero",
                      code="FP32 conjugate gradients with " + VC[vc][1] + ", solution accumulated in FP64",
                      operator=OPN[op], operator_precision="FP32 (" + OPN[op] + ")", krylov_precision="FP32",
                      preconditioner=B(VC[vc][1], "experiments/E29_review.py:152 (common: GMG fine_variant='stencil'), 198-207"),
                      residual_precision="FP32 recursive", iterate_precision="FP64",
                      native_stop=B("recursive FP32 residual <= 1e-5 (no FP64 test)", "experiments/E29_review.py:8-10"),
                      setup=M("not recorded in this accuracy study"), times={}, memory={}, notes=[])
            if op == "stencil" and vc == "common_vcycle":
                rr["notes"].append("for the original stencil the common V-cycle is its own V-cycle; the two entries are the same configuration run twice")
            if c.get("iters") is None:
                rr["status"] = B("breakdown before the monitored residual reached 1e-5", rel + f"#/rows/{i}/controls/{name}/iters (null)")
                rr["steps"] = M("breakdown")
                rr["achieved_true_residual"] = M("breakdown")
                rr["compliance_rel_err_vs_fp64"] = M("breakdown")
                rr["residual_factor_per_step"] = M("not computed: breakdown")
            else:
                rr["status"] = B("monitored pass reached; FP64 true residual above 1e-5", rel + f"#/rows/{i}/controls/{name}")
                rr["steps"] = J(rel, "rows", i, "controls", name, "iters")
                rr["achieved_true_residual"] = dict(J(rel, "rows", i, "controls", name, "true_res_fp64_op"), kind="FP64 true residual at the stop, FP64 operator")
                rr["compliance_rel_err_vs_fp64"] = J(rel, "rows", i, "controls", name, "rel_err_vs_fp64")
                rr["residual_factor_per_step"] = gm_factor(rr["achieved_true_residual"], ZERO_START, rr["steps"], True, "n = FP32 CG iterations")
                for kk in ("floor_true", "true_res_stencil_c32", "true_res_stencil_diff_c32"):
                    rr[kk] = Jopt(rel, "rows", i, "controls", name, kk, missing="not recorded")
            rr["reference_true_residual"] = J(rel, "rows", i, "ref_rel_true")
            rr["memory"]["peak"] = M("not measured in this accuracy study")
            rows.append(rr)
        # the rounded-coefficient diagnostic
        for name, cf in rw["coef"].items():
            rr = dict(id=f"beam_E29_k{k}_{name}_fp64solve", block="E_precision_controls", device=DEVICE, provenance="historical record (submitted paper)",
                      workload="rounded-coefficient diagnostic: FP32-rounded stencil blocks applied in FP64, FP64 CG to 1e-8",
                      system=f"slender clamped beam 8x1x1, {k} elements through the depth", elements=J(rel, "rows", i, "n_elem"),
                      dofs=M("not recorded"), start="zero", code="FP64 conjugate gradients on the rounded operator",
                      operator=("original stencil" if name == "stencil_c32" else "difference-form stencil") + ", coefficients rounded as in FP32, applied in FP64",
                      operator_precision="FP32-rounded coefficients, FP64 arithmetic", krylov_precision="FP64",
                      residual_precision="FP64 (rounded operator)", iterate_precision="FP64", native_stop="FP64 residual of the rounded operator <= 1e-8",
                      status=J(rel, "rows", i, "coef", name, "status"), times={}, memory={}, notes=[])
            rr["min_energy_ratio"] = J(rel, "rows", i, "coef", name, "min_energy_ratio")
            rr["compliance_rel_err_vs_fp64"] = Jopt(rel, "rows", i, "coef", name, "rel_err_vs_fp64", missing="no solution (negative-energy direction)")
            rr["steps"] = J(rel, "rows", i, "coef", name, "iters")
            rr["insolver_residual"] = dict(
                J(rel, "rows", i, "coef", name, "rel"),
                kind=B("in-solver relative residual of FP64 CG on the rounded operator (operator: FP32-rounded stencil blocks applied in "
                       "FP64): recursive update, replaced by the recomputed residual of the rounded operator every 50 iterations; at a "
                       "negative-energy direction, the value before that step",
                       "experiments/E29_review.py:122-142 (pcg_energy)"))
            rr["achieved_true_residual"] = M("no independent check: the record holds no FP64-operator residual of the rounded-coefficient "
                                             "solution, and no separate process recomputed one")
            rr["residual_factor_per_step"] = M("not computed: the residual is that of the rounded operator, not comparable with FP64 true residuals")
            rr["setup"] = M("not recorded in this accuracy study")
            rr["memory"]["peak"] = M("not measured")
            rows.append(rr)


# ----------------------------------------------------------------------------------------------------------------
# F/G. Complete optimizations, recursive control, capacity; H. paired timings
# ----------------------------------------------------------------------------------------------------------------
SOLVER_LABEL = {
    "mg64": ("FP64 PCG + FP32 V-cycle", "FP64 node_hoist", "FP64 PCG", "FP64 true residual (in-solver)", "FP64", "FP64 true residual <= 1e-5 at every state solve"),
    "mg_ir": ("iterative refinement (inner FP32 PCG + V-cycle)", "FP32 (inner), FP64-arithmetic outer residual", "inner FP32 PCG", "FP64 outer residual (in-solver)", "FP64", "outer FP64 residual <= 1e-5 at every state solve"),
    "mg32_rec": ("recursive-stop control: FP32 PCG + FP32 V-cycle, FP64 iterate", "FP32", "FP32 PCG", "FP32 recursive (FP64 true residual recorded, never used to stop)", "FP64", "recursive FP32 residual <= 1e-5 (no FP64 test)"),
}
OP32_LABEL = {"stencil": "original 27-point stencil", "stencil_diff": "difference-form stencil (repaired)",
              "elem_atomic": "atomic element kernel", "node": "factored node kernel", "spoke": "27-neighbour kernel"}


def opt_row(rel, block, prov, extra_note=None):
    d = load(rel)
    cfg = d.get("config") or {}
    nm = Path(rel).stem
    solver = cfg.get("solver") or ("mg64" if "_mg64_" in nm else "mg_ir" if "_mg_ir_" in nm else "mg32_rec" if "mg32_rec" in nm else None)
    op32 = cfg.get("op32") or ("stencil_diff" if nm.endswith("_diff") else "elem_atomic" if "elem_atomic" in nm else "stencil")
    lab = SOLVER_LABEL[solver]
    ok = d.get("status") == "ok" and d.get("valid") is not False
    h = d.get("history", [])
    rr = dict(id="opt_" + rel.split("/")[1] + "_" + nm, block=block, device=DEVICE, provenance=prov,
              workload="complete optimization (filter, projection, continuation; " + str(d.get("problem")) + ")",
              system=f"authors' {d.get('problem')} {2*d['k']}x{d['k']}x{d['k']}", elements=J(rel, "n_elem"), dofs=J(rel, "ndof"),
              start="previous design iteration's state (warm start)", code=lab[0],
              operator=f"FP64 node_hoist outer operator; FP32 fine level {OP32_LABEL.get(op32, op32)}" if solver == "mg64" else f"FP32 {OP32_LABEL.get(op32, op32)}",
              operator_precision=lab[1] + f"; fine-level FP32 operator {OP32_LABEL.get(op32, op32)}",
              krylov_precision=lab[2], residual_precision=lab[3], iterate_precision=lab[4],
              native_stop=B(lab[5], "code/src/voxfem/simp.py:67 (Config.tol = 1e-5), 251-285 (solver dispatch)"),
              times={}, memory={}, notes=[])
    if extra_note:
        rr["notes"].append(extra_note)
    if ok:
        rr["status"] = dict(J(rel, "termination"), converged=d.get("converged"))
        rr["design_iterations"] = J(rel, "iterations")
        rr["compliance"] = J(rel, "compliance")
    else:
        rr["status"] = dict(J(rel, "status"), note="no design returned")
        rr["design_iterations_completed"] = H(rel, "len", "it", "number of history entries")
    rr["setup"] = dict(construction=dict(Jopt(rel, "setup_s", missing="not recorded"), unit="s",
                                         boundary="construction of the optimization object before the loop (problem, operators, multigrid hierarchy, "
                                                  "workspace) on the host clock; experiments/run_simp.py:63-67"),
                       hierarchy_updates_total=dict(Jopt(rel, "totals", "setup_s", missing="not recorded (no design returned)"), unit="s",
                                                    boundary="sum over the state solves of the multigrid update before each solve (voxfem/simp.py:255-259); "
                                                             "inside the per-design-iteration times"))
    if h:
        rr["times"]["optimization_compute"] = dict(H(rel, "sum", "t_iter_s", "sum of history[*].t_iter_s"), unit="s", denominator="per optimization",
                                                   boundary="sum of per-design-iteration times (filter and projection, multigrid update, state solve, sensitivities, update); excludes process start, compilation, guard checks and the final solve")
        rr["times"]["per_design_iteration"] = dict(H(rel, "mean", "t_iter_s", "sum of history[*].t_iter_s / number of design iterations"), unit="s",
                                                   denominator="per design iteration (state solve + design step)")
        if "totals" in d:
            rr["times"]["solve_total"] = dict(J(rel, "totals", "solve_s"), unit="s", denominator="per optimization (state solves only)")
        rr["krylov_steps_total"] = H(rel, "sum", "solve.inner_iters|iters", "sum of history[*].solve.iters (inner_iters for IR)")
        if "totals" in d and val(rr["krylov_steps_total"]):
            rr["times"]["krylov_step_mean"] = dict(ratio(J(rel, "totals", "solve_s"), rr["krylov_steps_total"],
                                                         "totals.solve_s / Krylov steps (a run mean, not a synchronized per-step time; includes outer residuals of IR)"),
                                                   unit="s", denominator="per Krylov step (run mean)")
        # residuals of the accepted (or recursive-stop) states
        rt = [(i, x["solve"].get("rel_true"), x["solve"].get("rel_initial"), x["solve"].get("inner_iters", x["solve"].get("iters")))
              for i, x in enumerate(h) if isinstance(x.get("solve"), dict)]
        good = [t for t in rt if isinstance(t[1], (int, float)) and t[1] == t[1]]
        rr["state_true_residual_max"] = H(rel, "max", "solve.rel_true", "max over history[*].solve.rel_true")
        rr["states_above_1e-5"] = H(rel, "count_gt", "solve.rel_true", "count of history[*].solve.rel_true > 1e-5", threshold=1e-5)
        rr["states_n"] = H(rel, "count", "solve.rel_true", "number of design-loop state solves with a recorded true residual")
        rr["state_true_residual_median"] = H(rel, "median", "solve.rel_true", "median over history[*].solve.rel_true")
        use = [t for t in good if isinstance(t[2], (int, float)) and t[2] > 0 and t[1] > 0 and isinstance(t[3], (int, float)) and t[3] > 0]
        if use:
            lg = sum(math.log(t[1] / t[2]) for t in use)
            n = sum(t[3] for t in use)
            rr["residual_factor_per_step"] = {"v": math.exp(lg / n), "formula": "exp( sum log(rel_true/rel_initial) / sum n ) over design-loop solves with n > 0 "
                                              "(n = iters, inner_iters for IR; rel_initial = true residual of the warm start)",
                                              "from": [rel + "#/history"], "op": "hist", "params": dict(file=rel, agg="run_factor", field="solve")}
            rr["residual_factor_per_step"]["n_solves_used"] = len(use)
            rr["residual_factor_per_step"]["n_kind"] = "Krylov steps (inner steps for IR)"
            if solver == "mg32_rec":
                rr["residual_factor_per_step"]["qualification"] = "r_end is the FP64 true residual of the recursive-stop state, recorded but not used to stop"
        else:
            rr["residual_factor_per_step"] = M("not computed: no solve with n > 0 and positive residuals")
    if "final_solve" in d:
        rr["final_solve_true_residual"] = Jopt(rel, "final_solve", "rel_true")
    if "certified_final" in d:
        rr["certified_final_true_residual"] = Jopt(rel, "certified_final", "solve", "rel_true")
    mem = d.get("memory")
    if mem:
        for kk, de in (("peak_pool_used_bytes", "CuPy pool used peak sampled at explicit points (iteration ends), not a continuous peak"),
                       ("peak_pool_reserved_bytes", "CuPy pool reserved peak sampled at explicit points"),
                       ("peak_device_used_bytes", "device-wide used memory (cudaMemGetInfo total - free, includes other processes), sampled at explicit points"),
                       ("baseline_device_used_bytes", "device-wide used memory at start")):
            if kk in mem:
                rr["memory"][kk.replace("_bytes", "")] = dict(J(rel, "memory", kk), unit="B", definition=de)
    rr["spill"] = Jopt(rel, "spill", "spilled")
    rr["spill_max_growth"] = Jopt(rel, "spill", "max_shared_growth_bytes")
    rr["valid"] = Jopt(rel, "valid")
    rows.append(rr)
    return rr


def block_optimizations():
    for p in sorted((PROJ / "results" / "E7").glob("simp_*.json")):
        opt_row("results/E7/" + p.name, "G_optimizations", "historical record (submitted paper; original stencil unless named)")
    for p in sorted((PROJ / "results" / "E32").glob("simp_*.json")):
        opt_row("results/E32/" + p.name, "G_optimizations" if "_r" not in p.stem[-3:] else "H_paired_timings",
                "historical record (submitted paper; repaired difference form or paired swap)")
    for p in sorted((PROJ / "results" / "E12").glob("simp_*.json")):
        blk = "F_recursive_control" if "mg32_rec" in p.stem else "G_optimizations"
        opt_row("results/E12/" + p.name, blk, "historical record (submitted paper)")
    rb = opt_row("results/E12b/simp_cantilever_k384_mg64_stencil_poollimit.json", "G_optimizations",
                 "historical record (submitted paper)", "CuPy pool capped at 21.5 GiB")
    lim = int(re.search(r"limit set to: ([\d,]+) bytes", rb["status"]["v"]).group(1).replace(",", ""))
    rb["pool_limit_bytes"] = D(lim, "the 'limit set to' byte count in the recorded status", rb["status"], op="status_limit_bytes")
    rb["pool_limit_GiB"] = D(lim / 2 ** 30, "pool limit / 2^30", rb["pool_limit_bytes"], op="div_const", divisor=2 ** 30)
    # E7 memory probes
    for p in sorted((PROJ / "results" / "E7").glob("memory_k*.json")):
        rel = "results/E7/" + p.name
        d = load(rel)
        rr = dict(id="mem_E7_" + p.stem, block="G_optimizations", device=DEVICE, provenance="historical record (submitted paper)",
                  workload="memory probe: two design iterations of the cantilever optimization (original stencil)",
                  system=f"authors' cantilever {2*d['k']}x{d['k']}x{d['k']}", elements=J(rel, "n_elem"), dofs=M("not recorded"),
                  start="zero", code=SOLVER_LABEL[d["solver"]][0], operator_precision=SOLVER_LABEL[d["solver"]][1],
                  krylov_precision=SOLVER_LABEL[d["solver"]][2], residual_precision=SOLVER_LABEL[d["solver"]][3],
                  iterate_precision="FP64", native_stop=SOLVER_LABEL[d["solver"]][5], status=J(rel, "status"),
                  times={}, memory={}, notes=[])
        rr["setup"] = dict(construction=dict(Jopt(rel, "construct_s", missing="not run"), unit="s",
                                             boundary="construction of the optimization object (experiments/E7_memory_probe.py:50-52)"))
        rr["memory"]["prediction_bytes_per_element"] = dict(Jopt(rel, "prediction", "bytes_per_element", missing="no prediction in this probe"), unit="B/element", definition="driver's prediction used for admission")
        rr["memory"]["prediction_need"] = dict(Jopt(rel, "prediction", "need_bytes", missing="no prediction in this probe"), unit="B", definition="predicted need")
        if d["status"] == "ok":
            rr["memory"]["accounted_total"] = dict(J(rel, "breakdown", "total_accounted"), unit="B", definition="sum of the accounted arrays by component")
            rr["memory"]["accounted_per_element"] = dict(J(rel, "breakdown", "per_element", "total_accounted"), unit="B/element", definition="accounted total / elements")
            for kk, de in (("peak_pool_used_bytes", "CuPy pool used peak sampled at explicit points"), ("peak_pool_reserved_bytes", "CuPy pool reserved peak sampled at explicit points"),
                           ("peak_device_used_bytes", "device-wide used memory (cudaMemGetInfo), includes other processes"),
                           ("baseline_device_used_bytes", "device-wide used memory at start")):
                rr["memory"][kk.replace("_bytes", "")] = dict(J(rel, "peak", kk), unit="B", definition=de)
            rr["spill"] = J(rel, "spill", "spilled")
        else:
            rr["notes"].append("not run: predicted need above the effective free memory of the shared display card (a prediction, not a measured limit)")
        rows.append(rr)
    # largest sizes of complete optimizations (historical, T27 confirmatory, T27 exploratory kept apart)
    cap = "tasks/T27/capacity.json"
    EFF_FREE = B("the guard's effective free-memory estimate guard.effective_free_bytes(): the smaller of the driver-reported free memory "
                 "(cudaMemGetInfo) and the total memory minus every other process's dedicated usage minus this process's pool",
                 "tasks/T27/src/voxfem/guard.py:116-126; tasks/T27/ANALYSIS_PLAN.md:186")
    T27_CAP_PROBLEM = B("the authors' cantilever, repaired FP32 operator", "tasks/T27/ANALYSIS_PLAN.md:80-81, 314")
    ent = {e["name"]: i for i, e in enumerate(load(cap)["entries"])}
    xen = {e["name"]: i for i, e in enumerate(load(cap)["exploratory"]["entries"])}
    nxp = {(e["configuration"], e["k"]): i for i, e in enumerate(load(cap)["exploratory_next_size_predictions"]["entries"])}

    def T(name, field, expl=False):
        return J(cap, "exploratory", "entries", xen[name], field) if expl else J(cap, "entries", ent[name], field)

    def opt_status(rel):
        d = load(rel)
        return dict(J(rel, "termination") if d.get("status") == "ok" else J(rel, "status"), elements=d["n_elem"])

    largest.append(dict(
        configuration="IR, repaired difference form (FP32 corrections and V-cycle, FP64 iterate and residual)",
        workload="complete optimization of the authors' cantilever, torsion and bridge",
        largest_pass_elements=113246208,
        largest_pass_status="historical completions of all three problems: every state accepted in-process at <= 1e-5; no independent check of the final state; spill sampled every 10 design iterations (T27 labels them historical completions, not its class 9)",
        evidence=[opt_status(f"results/E32/simp_{p}_k384_mg_ir_stencil_diff.json") for p in ("cantilever", "torsion", "bridge")],
        t27_confirmatory=dict(at_elements=113246208, status=T("C1_mg_ir_k384", "class_label"), basis=T("C1_mg_ir_k384", "class_basis"),
                              problem=T27_CAP_PROBLEM, admission_rule=J(cap, "definitions", "admission"), effective_free_rule=EFF_FREE,
                              predicted_workspace=J(cap, "entries", ent["C1_mg_ir_k384"], "admission", "W_bytes"),
                              effective_free=J(cap, "entries", ent["C1_mg_ir_k384"], "admission", "E_free_bytes"),
                              meaning="not admitted under T27's frozen rule (predicted workspace + 1.5 GiB > the guard's effective free memory); a prediction, not a measured limit"),
        t27_exploratory=dict(at_elements=113246208, status=T("X_C1_mg_ir_k384", "class_label", True),
                             independent_final_residual=T("X_C1_mg_ir_k384", "independent_final_rel_true", True),
                             meaning="completed outside T27's admission rule with a raised pool cap; exploratory, never a lower bound"),
        next_size_elements=J(cap, "exploratory_next_size_predictions", "entries", nxp[("mg_ir", 416)], "n_elem"),
        next_size_status="not run; predicted workspace + margin exceeds the card's total memory",
        next_size_prediction=J(cap, "exploratory_next_size_predictions", "entries", nxp[("mg_ir", 416)], "W_plus_margin_bytes"),
        device_total=J(cap, "exploratory_next_size_predictions", "entries", nxp[("mg_ir", 416)], "device_total_bytes"),
        provenance="historical record + T27"))
    largest.append(dict(
        configuration="IR, original stencil",
        workload="complete optimization of the authors' cantilever, torsion and bridge",
        largest_pass_elements=113246208, largest_pass_status="cantilever and torsion completed (historical)",
        evidence=[opt_status("results/E7/simp_cantilever_k384_mg_ir_stencil.json"), opt_status("results/E12/simp_torsion_k384_mg_ir_stencil.json"),
                  opt_status("results/E7/simp_bridge_k320_mg_ir_stencil.json"), opt_status("results/E12/simp_bridge_k384_mg_ir_stencil.json")],
        next_size_elements=None,
        next_size_status="bridge: no design returned at 65.5M and at 113.2M (the FP32 correction is rejected after design iteration 15); no larger size run",
        provenance="historical record (submitted paper)"))
    largest.append(dict(
        configuration="FP64 PCG + FP32 V-cycle",
        workload="complete optimization of the authors' cantilever, torsion and bridge",
        largest_pass_elements=65536000,
        largest_pass_status="completed all three problems with the original stencil and with the repaired form (historical)",
        evidence=[opt_status(f"results/E7/simp_{p}_k320_mg64_stencil.json") for p in ("cantilever", "torsion", "bridge")] +
                 [opt_status("results/E32/simp_cantilever_k320_mg64_stencil_diff_r1.json"), opt_status("results/E32/simp_torsion_k320_mg64_stencil_diff.json"),
                  opt_status("results/E32/simp_bridge_k320_mg64_stencil_diff.json")],
        t27_confirmatory=dict(at_elements=65536000, status=T("C3_mg64_k320", "class_label"), failure=T("C3_mg64_k320", "failure"),
                              problem=T27_CAP_PROBLEM, operator=T("C3_mg64_k320", "op32"),
                              pool_cap=J(cap, "entries", ent["C3_mg64_k320"], "admission", "pool_cap_bytes"),
                              meaning="repaired cantilever under T27's lower pool cap (E_free - 1.5 GiB): out of memory in design iteration 3; a result under that cap"),
        t27_exploratory=dict(at_elements=65536000, status=T("X_C3_mg64_k320", "class_label", True),
                             independent_final_residual=T("X_C3_mg64_k320", "independent_final_rel_true", True),
                             meaning="completed with the raised pool cap; exploratory"),
        next_size_elements=J("results/E12/simp_cantilever_k384_mg64_stencil.json", "n_elem"),
        next_size_status="original stencil at 113.2M: stopped by the spill check (pool spilled into shared memory; invalid) without a cap, and out of memory in design iteration 1 with a 21.5 GiB pool cap; the memory probe predicted that it exceeds capacity",
        next_size_evidence=[J("results/E12/simp_cantilever_k384_mg64_stencil.json", "status"),
                            J("results/E12b/simp_cantilever_k384_mg64_stencil_poollimit.json", "status"),
                            J("results/E7/memory_k384_mg64.json", "status")],
        intermediate_size=dict(elements=J(cap, "exploratory_next_size_predictions", "entries", nxp[("mg64", 352)], "n_elem"), status="not run (T27 ladder stopped after the allocation failure at 65.5M)",
                               prediction=J(cap, "exploratory_next_size_predictions", "entries", nxp[("mg64", 352)], "W_plus_margin_bytes")),
        provenance="historical record + T27"))
    largest.append(dict(
        configuration="recursive-stop control (FP32 PCG + V-cycle, FP64 iterate, no FP64 test), original stencil",
        workload="complete optimization",
        largest_pass_elements=65536000,
        largest_pass_label=B("largest historical completion (submitted paper's records); not the largest completion of any kind: an exploratory "
                             "completion at the next size exists outside the prespecified admission rule",
                             "results/E12/simp_*_k320_mg32_rec_stencil.json; tasks/T27/capacity.json#/entries (C6a, class_label) and "
                             "#/exploratory/entries (X_C6a, EXPLORATORY)"),
        largest_pass_status="cantilever and torsion ran to completion but accepted states above 1e-5; bridge: Krylov breakdown (negative curvature) after 15 design iterations at 65.5M",
        evidence=[opt_status(f"results/E12/simp_{p}_k320_mg32_rec_stencil.json") for p in ("cantilever", "torsion", "bridge")],
        t27_confirmatory=dict(at_elements=113246208, status=T("C6a_mg32_rec_orig_k384", "class_label"),
                              admission_rule=J(cap, "definitions", "admission"), effective_free_rule=EFF_FREE,
                              predicted_workspace=J(cap, "entries", ent["C6a_mg32_rec_orig_k384"], "admission", "W_bytes"),
                              effective_free=J(cap, "entries", ent["C6a_mg32_rec_orig_k384"], "admission", "E_free_bytes"),
                              meaning="not admitted under T27's frozen rule (prediction): predicted workspace + 1.5 GiB above the guard's effective "
                                      "free-memory estimate, not above the driver-reported free memory"),
        t27_exploratory=dict(at_elements=113246208, status=T("X_C6a_mg32_rec_orig_k384", "class_label", True),
                             states_above_1e_5=T("X_C6a_mg32_rec_orig_k384", "n_states_above_1e-5", True),
                             design_iterations=T("X_C6a_mg32_rec_orig_k384", "iterations", True),
                             label=T("X_C6a_mg32_rec_orig_k384", "EXPLORATORY", True),
                             meaning="exploratory completion (cantilever) outside T27's admission rule; never a lower bound"),
        next_size_elements=T("X_C6a_mg32_rec_orig_k384", "n_elem_active", True),
        next_size_status="T27: not admitted (confirmatory); exploratory run completed outside the admission rule",
        provenance="historical record + T27"))
    largest.append(dict(
        configuration="paper-wide maximum (complete optimization)", workload="complete optimization",
        largest_pass_elements=J(cap, "paper_wide_maximum", "elements_active"), largest_pass_status="historical completions; not raised by T27 or T28",
        updated=J(cap, "paper_wide_maximum", "updated"), carried_by=J(cap, "paper_wide_maximum", "carried_by"),
        next_size_elements=None, next_size_status="no larger complete optimization run", provenance="T27"))


def block_paired():
    rel = "results/E32/op_k320_fp32.json"
    d = load(rel)
    idx = {r["method"]: i for i, r in enumerate(d["rows"])}
    OPN = {"stencil": "original 27-point stencil", "stencil_diff": "difference-form stencil (repaired)", "spoke": "27-neighbour kernel",
           "elem_atomic": "atomic element kernel", "elem_ref": "element kernel, corner reference", "elem_mean": "element kernel, element-mean reference (repaired)",
           "stencil_selfcorr": "self-block correction", "mixed_fp64": "factored node kernel, FP64 arithmetic on FP32 vectors"}
    for m, i in idx.items():
        if m == "empty_launch":
            continue
        rr = dict(id=f"app_E32_k320_{m}", block="H_paired_timings", device=DEVICE, provenance="historical record (submitted paper)",
                  workload="one FP32 operator application on a fixed field (repair-cost survey)",
                  system="authors' cantilever grid 640x320x320", elements=J(rel, "n_elem"), dofs=J(rel, "ndof"),
                  code="authors' kernel", operator=OPN[m], operator_precision="FP32 vectors" + (", FP64 arithmetic" if m == "mixed_fp64" else ""),
                  krylov_precision="not applicable", residual_precision="not applicable", iterate_precision="not applicable",
                  native_stop="not applicable", status=J(rel, "status"), times={}, memory={}, notes=[])
        rr["times"]["application"] = dict(J(rel, "rows", i, "us_median"), unit="us", denominator="per application",
                                          statistic="median of 11 randomized timing blocks (about 40 ms each)",
                                          iqr=[J(rel, "rows", i, "us_q1"), J(rel, "rows", i, "us_q3")])
        rr["rel_err_vs_fp64"] = J(rel, "rows", i, "rel_err_vs_fp64_elem")
        rr["setup"] = M("not recorded: application survey on a prebuilt operator")
        rr["memory"]["peak"] = M("not measured")
        rows.append(rr)
    st = J(rel, "rows", idx["stencil"], "us_median")
    for m, lab in (("stencil_diff", "difference form / original stencil"), ("elem_mean", "element mean / atomic element"),
                   ("elem_ref", "element corner / atomic element"), ("stencil_selfcorr", "self-block correction / original stencil"),
                   ("mixed_fp64", "FP64-arithmetic node / original stencil"), ("elem_atomic", "atomic element / difference form")):
        a = J(rel, "rows", idx[m], "us_median")
        b = st if m in ("stencil_diff", "stencil_selfcorr", "mixed_fp64") else (
            J(rel, "rows", idx["elem_atomic"], "us_median") if m in ("elem_mean", "elem_ref") else J(rel, "rows", idx["stencil_diff"], "us_median"))
        pairs.append(dict(id=f"app_E32_k320_{m}_ratio", rows=[f"app_E32_k320_{m}"], value=ratio(a, b, lab), orientation=lab + " (>1: numerator slower)"))


def orientation_check():
    """Paired swap of the fine-level FP32 operator, 65.5M cantilever, FP64 PCG: order, pairing and sign."""
    runs = {}
    for op in ("stencil_diff", "stencil", "elem_atomic"):
        for r in (1, 2, 3):
            rel = f"results/E32/simp_cantilever_k320_mg64_{op}_r{r}.json"
            d = load(rel)
            runs[(op, r)] = dict(rel=rel, started=d["started"], t=sum(x["t_iter_s"] for x in d["history"]),
                                 it=d["iterations"], c=d["compliance"])
    order = sorted(runs.items(), key=lambda kv: kv[1]["started"])
    blocks = [[kv[0] for kv in order[i:i + 3]] for i in (0, 3, 6)]
    balanced = all(sorted(op for op, _ in b) == sorted(["stencil_diff", "stencil", "elem_atomic"]) for b in blocks)
    reps_match = all(len({r for _, r in b}) == 1 for b in blocks)
    positions = {op: sorted([b.index((op, b[0][1])) for b in blocks]) for op in ("stencil_diff", "stencil", "elem_atomic")}
    latin = all(v == [0, 1, 2] for v in positions.values())
    out = dict(design="three repetitions; in each, the three fine-level operators run once; pairs are formed within a repetition",
               run_order=[dict(op=op, repetition=r, started_src=runs[(op, r)]["rel"] + "#/started") for op, r in (kv[0] for kv in order)],
               blocks_contain_each_operator_once=balanced, block_equals_repetition_index=reps_match,
               each_operator_once_in_each_position=latin, positions=positions)
    res = {}
    for op in ("stencil", "elem_atomic"):
        diffs = []
        for r in (1, 2, 3):
            a, b = runs[(op, r)]["t"], runs[("stencil_diff", r)]["t"]
            diffs.append((a - b) / b)
        mean_t = statistics.mean(runs[(op, r)]["t"] for r in (1, 2, 3))
        mean_d = statistics.mean(runs[("stencil_diff", r)]["t"] for r in (1, 2, 3))
        res[op] = dict(orientation="(t_operator - t_difference_form) / t_difference_form, paired within repetition; > 0: the operator is slower",
                       paired_changes=diffs, paired_change_mean=statistics.mean(diffs), paired_range=[min(diffs), max(diffs)],
                       ratio_of_means_minus_1=mean_t / mean_d - 1, mean_s=mean_t, reference_mean_s=mean_d,
                       times_s=[runs[(op, r)]["t"] for r in (1, 2, 3)], reference_times_s=[runs[("stencil_diff", r)]["t"] for r in (1, 2, 3)],
                       sources=[runs[(op, r)]["rel"] + "#/history/*/t_iter_s" for r in (1, 2, 3)] +
                               [runs[("stencil_diff", r)]["rel"] + "#/history/*/t_iter_s" for r in (1, 2, 3)],
                       iterations_equal=len({runs[(o, r)]["it"] for o in (op, "stencil_diff") for r in (1, 2, 3)}) == 1)
        tc = [H(runs[(op, r)]["rel"], "sum", "t_iter_s", "sum of history[*].t_iter_s") for r in (1, 2, 3)]
        tr = [H(runs[("stencil_diff", r)]["rel"], "sum", "t_iter_s", "sum of history[*].t_iter_s") for r in (1, 2, 3)]
        ch = [D((a["v"] - b["v"]) / b["v"], "(t_operator - t_difference) / t_difference, same repetition", a, b, op="rel_change")
              for a, b in zip(tc, tr)]
        res[op]["cells"] = dict(
            times=tc, reference_times=tr,
            mean=D(statistics.mean(c["v"] for c in tc), "mean of the three repetitions", *tc, op="mean"),
            reference_mean=D(statistics.mean(c["v"] for c in tr), "mean of the three repetitions", *tr, op="mean"),
            paired_changes=ch,
            paired_change_mean=D(statistics.mean(c["v"] for c in ch), "mean of the paired changes", *ch, op="mean"),
            paired_change_min=D(min(c["v"] for c in ch), "smallest paired change", *ch, op="min"),
            paired_change_max=D(max(c["v"] for c in ch), "largest paired change", *ch, op="max"))
    out["changes"] = res
    # compare with the submitted table
    tex = (RUN / "input/manuscript/tables/tab_swaps_paired.tex").read_text(encoding="utf-8")
    stated = {}
    for lab, op in (("difference form", "stencil_diff"), ("27-pt stencil", "stencil"), ("element, atomic", "elem_atomic")):
        line = next(l for l in tex.splitlines() if l.strip().startswith(lab))
        nums = [float(x) for x in re.findall(r"[-+]?\d+\.\d+", line.replace("--", " "))]
        stated[op] = dict(line=line.strip(), numbers=nums)
    out["submitted_table"] = dict(src="input/manuscript/tables/tab_swaps_paired.tex", rows=stated)
    chk = []
    for op in ("stencil_diff", "stencil", "elem_atomic"):
        n = stated[op]["numbers"]
        ts = [runs[(op, r)]["t"] for r in (1, 2, 3)]
        chk.append(dict(op=op, repetition_times_match=all(abs(round(t, 1) - x) < 1e-9 for t, x in zip(ts, n[:3])),
                        mean_matches=abs(round(statistics.mean(ts), 1) - n[3]) < 1e-9))
    for op in ("stencil", "elem_atomic"):
        n = stated[op]["numbers"]
        r_ = res[op]
        chk.append(dict(op=op, stated_mean_change_pct=n[4], computed_paired_mean_pct=round(100 * r_["paired_change_mean"], 1),
                        computed_ratio_of_means_pct=round(100 * r_["ratio_of_means_minus_1"], 1),
                        stated_range_pct=n[5:7], computed_range_pct=[round(100 * x, 1) for x in r_["paired_range"]],
                        sign_and_range_match=[round(100 * x, 1) for x in r_["paired_range"]] == n[5:7],
                        mean_matches_paired_mean=round(100 * r_["paired_change_mean"], 1) == n[4],
                        mean_matches_ratio_of_means=round(100 * r_["ratio_of_means_minus_1"], 1) == n[4]))
    out["checks"] = chk
    # application-time orientation (E32 survey)
    rel = "results/E32/op_k320_fp32.json"
    d = load(rel)
    med = {r["method"]: r["us_median"] for r in d["rows"]}
    out["application"] = dict(
        difference_over_original=med["stencil_diff"] / med["stencil"],
        stated_main_text="2.73 ms, 7.6 % more than the original stencil (2.54 ms)",
        computed_pct=round(100 * (med["stencil_diff"] / med["stencil"] - 1), 1),
        atomic_over_difference=med["elem_atomic"] / med["stencil_diff"],
        element_mean_over_atomic=med["elem_mean"] / med["elem_atomic"],
        src=rel + "#/rows/*/us_median")
    return out


# ----------------------------------------------------------------------------------------------------------------
# I. Literature (T14): published figures, each with its own device and workload
# ----------------------------------------------------------------------------------------------------------------
def block_literature():
    rel = "tasks/T14/literature_block.json"
    d = load(rel)
    lit = []
    for i, r in enumerate(d["rows"]):
        lit.append(dict(id=f"lit_{i:02d}_{r['work']}", provenance="published figure (other device and workload; T14-verified quotes)",
                        work=r["work"], code=J(rel, "rows", i, "code"), device=J(rel, "rows", i, "device"),
                        workload=J(rel, "rows", i, "workload"), quantity=J(rel, "rows", i, "quantity"),
                        value=J(rel, "rows", i, "value"), unit=J(rel, "rows", i, "unit"), kind=J(rel, "rows", i, "kind"), quote_ids=r.get("quote_ids"),
                        note=r.get("note") or r.get("capacity_statement"),
                        dropped=("DROPPED" in (r.get("kind") or ""))))
    for i, r in enumerate(d["released_code"]):
        lit.append(dict(id=f"lit_code_{i}", provenance="released code (T14-verified code quotes)", code=r["code"], quantity=r["quantity"],
                        value=J(rel, "released_code", i, "value"), note=r.get("note"), quote_ids=r.get("quote_ids")))
    for i, r in enumerate(d["device_specs"]):
        lit.append(dict(id=f"lit_device_{i}", provenance="vendor specification (T14-verified)", device=r["device"], quantity=r["quantity"],
                        value=J(rel, "device_specs", i, "value"), unit=r["unit"], quote_ids=r.get("quote_ids")))
    return lit


# ----------------------------------------------------------------------------------------------------------------
def main():
    block_sparse()
    block_hou_historical()
    block_t27()
    block_t28()
    block_precision()
    block_optimizations()
    block_paired()
    orient = orientation_check()
    lit = block_literature()
    # every largest-size element count becomes a cited cell
    byid = {r["id"]: r for r in rows}
    for x in largest:
        for key, rk in (("largest_pass_elements", "largest_pass_row"), ("next_size_elements", "next_size_row")):
            n = x.get(key)
            if isinstance(n, dict) or n is None:
                continue
            if x.get(rk) in byid:
                x[key] = byid[x[rk]]["elements"]
            elif key == "largest_pass_elements" and x.get("largest_pass_src"):
                x[key] = {"v": n, "src": x["largest_pass_src"]}
            elif key == "largest_pass_elements" and x.get("evidence"):
                f = x["evidence"][0]["src"].split("#")[0]
                x[key] = J(f, "n_elem")
            else:
                raise ValueError(f"uncited element count in largest-size entry {x['configuration']}: {key} = {n}")
    # recursive-control summary by problem (E12 + T27 exploratory)
    rec = []
    for r in rows:
        if r["block"] == "F_recursive_control":
            rec.append(dict(row=r["id"], problem=r["system"], elements=r["elements"], status=r["status"],
                            states_n=r.get("states_n"), states_above_1e_5=r.get("states_above_1e-5"),
                            state_true_residual_max=r.get("state_true_residual_max"),
                            state_true_residual_median=r.get("state_true_residual_median"),
                            final_solve_true_residual=r.get("final_solve_true_residual"),
                            residual_factor_per_step=r.get("residual_factor_per_step")))
    t27c = "tasks/T27/capacity.json"
    for i, e in enumerate(load(t27c)["exploratory"]["entries"]):
        if e["configuration"] == "mg32_rec":
            rec.append(dict(row=e["name"], problem="authors' cantilever 768x384x384 (T27 exploratory, outside its admission rule)",
                            elements=J(t27c, "exploratory", "entries", i, "n_elem_active"), op32=e["op32"],
                            status=J(t27c, "exploratory", "entries", i, "class_label"),
                            states_above_1e_5=J(t27c, "exploratory", "entries", i, "n_states_above_1e-5"),
                            state_true_residual_max=J(t27c, "exploratory", "entries", i, "max_state_rel_true"),
                            final_solve_true_residual=J(t27c, "exploratory", "entries", i, "insolver_final_rel_true")))
    # row convention: every row states its setup (a cited value, or the reason it is missing or not applicable)
    no_setup = [r["id"] for r in rows if "setup" not in r]
    if no_setup:
        raise ValueError(f"rows without a setup field: {no_setup[:10]} ({len(no_setup)})")
    # missing-cell inventory
    miss = []

    def walk(o, path):
        if isinstance(o, dict):
            if "missing" in o and o.get("v") is None:
                miss.append(dict(at=path, reason=o["missing"]))
                return
            for k, v in o.items():
                walk(v, path + "/" + str(k))
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, path + f"/{i}")
    for r in rows:
        walk(r, r["id"])
    doc = dict(
        title="T29 comparison: same-card comparisons, precision controls, capacities and attributed literature",
        roots={"results/": "the authors' project folder <project>", "tasks/": "the run's work folder",
               "input/": "the run folder (submitted manuscript, read only)"},
        cell_convention=__doc__.split("Every cell")[1].strip() if "Every cell" in __doc__ else "",
        blocks={
            "A_sparse": "cuSPARSE CSR/BSR applications and refreshes against matrix-free applications (E2, E4)",
            "B_hou_historical": "the seven submitted Hou rows (E10), both codes in one process; application ratios against the ORIGINAL stencil",
            "C_hou_matched": "T27: Hou's released code and our original/repaired paths in separate guarded processes on Hou's system",
            "D_traeff_fixed_state": "T28: Traeff et al.'s released OpenMP-offload code and our paths on its cantilever at fixed states S1 and S5",
            "E_precision_controls": "E8 single-precision controls (original stencil), E29 controls (65.5M element kernels; slender beam: all 13 controls at each of the five grids, own and common V-cycle, and the rounded-coefficient diagnostic)",
            "F_recursive_control": "E12 recursive-stop control (FP32 PCG, FP64 iterate) in complete optimizations, per problem",
            "G_optimizations": "E7/E32/E12/E12b complete optimizations and memory probes (design-iteration denominators, memory definitions)",
            "H_paired_timings": "E32 application survey at 65.5M and the paired fine-level operator swaps",
        },
        rows=rows, pairs=pairs, largest_sizes=largest, recursive_control_by_problem=rec,
        orientation_check=orient, literature=lit, missing_cells=miss,
        t28_status=dict(status="complete; measurements final, four reporting corrections D34-D37 applied", src="tasks/T28/REPORT.md; tasks/T28/DEVIATIONS.md",
                        g4_scope=dict(whole_solves="no whole fixed-state solve time is excludable under the 5 % rule; these bounds cover whole solves only (D34)",
                                      krylov_steps="at step duration the 5 % rule is unresolved for 15 of 32 timed rows (every row at k = 64, and k = 128 except the released S1 row)",
                                      design_loop_solves="native runs N and our loops L clear the threshold at whole-solve resolution; the instrumented record-run solves of iterations 1-4 at k = 64 are unresolved (D35)",
                                      design_steps="R design steps: whole-job bounds only, no constant-offset reading (D36)",
                                      src="tasks/T28/REPORT.md:47; tasks/T28/gates.json#/G4"),
                        g4_limitation=J("tasks/T28/g4_activity.json", "limitation")),
        t27_status=dict(status="final (last attempt, D23)", src="tasks/T27/REPORT.md"),
        t14_status=dict(status="final; 131/131 quotes verified", src="tasks/T14/quote_check.json"),
    )
    (OUT / "comparison.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False, allow_nan=True), encoding="utf-8")
    print(f"rows {len(rows)}, pairs {len(pairs)}, largest {len(largest)}, literature {len(lit)}, missing cells {len(miss)}")
    return doc


if __name__ == "__main__":
    main()
