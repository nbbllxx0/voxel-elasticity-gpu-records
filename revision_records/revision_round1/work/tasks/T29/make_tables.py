"""T29: LaTeX tabular bodies (manuscript style: booktabs, tabular only) and a Markdown mirror, from comparison.json.

Every table cell is traced (table_sources.json) as either
  a label: plain wording with no number; or
  a value cell: the comparison.json cells it shows ("shows": JSON pointer into comparison.json, with the scale and
  offset that turn the cited value into the displayed number, or as="text" for a cited text whose numbers it
  repeats) and the claims its status words make ("asserts": a condition on a cited cell).
verify_sources.py follows each pointer to the record, re-parses the rendered numbers and evaluates the asserts.
Table text follows the house rules: no file names, run labels, dates or other lab detail.
"""
import json
import math
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent
DOC = json.loads((OUT / "comparison.json").read_text(encoding="utf-8"))
ROWS = {r["id"]: r for r in DOC["rows"]}
PAIRS = {p["id"]: p for p in DOC["pairs"]}
TRACE = {}

# pointer of every dict in DOC (cells are the dicts that carry "v")
PATH = {}


def _index(o, p):
    if isinstance(o, dict):
        PATH[id(o)] = p
        for k, x in o.items():
            _index(x, f"{p}/{str(k).replace('~', '~0').replace('/', '~1')}")
    elif isinstance(o, list):
        for i, x in enumerate(o):
            _index(x, f"{p}/{i}")


_index(DOC, "")


def P(c):
    if id(c) not in PATH:
        raise KeyError("cell is not part of comparison.json")
    return PATH[id(c)]


def v(c):
    return None if c is None else (c.get("v") if isinstance(c, dict) else c)


# ------------------------------------------------------------------------------------------------- formatting
def sci(x):
    if x is None:
        return "--"
    if x == 0:
        return "0"
    if 1e-2 <= abs(x) < 1e3:
        return f"{x:#.3g}".rstrip(".")
    e = int(math.floor(math.log10(abs(x))))
    m = x / 10 ** e
    if round(m, 2) >= 10:
        m, e = m / 10, e + 1
    return f"${m:.2f}\\times10^{{{e}}}$"


def num_t(x):
    if x is None:
        return "--"
    if x >= 1000:
        return f"{x:,.0f}".replace(",", "{,}")
    if x >= 10:
        return f"{x:.1f}"
    if x >= 1:
        return f"{x:.2f}"
    return f"{x:#.3g}"


def fac(x):
    return "--" if x is None else (f"{x:.5f}" if x > 0.995 else f"{x:.3f}")


def gb(x):
    return "--" if x is None else f"{x / 1e9:.2f}"


def ints(x):
    return "--" if x is None else f"{int(x):,}".replace(",", "{,}")


def pct(x):
    return "--" if x is None else f"{100 * x:+.1f}\\%"


def sz(n):
    if n is None:
        return "--"
    if n < 1e5:
        return ints(n)
    return f"${n / 1e6:.1f}\\times10^{{6}}$" if n >= 1e7 else f"${n / 1e6:.2f}\\times10^{{6}}$"


def mill(n):
    return "--" if n is None else (f"{n / 1e6:.1f}M" if n >= 1e7 else f"{n / 1e6:.2f}M")


def tex_clean(s):
    s = re.sub(r"\\times10\^\{(-?\d+)\}", r"e\1", s)
    s = re.sub(r"10\^\{(-?\d+)\}", r"1e\1", s)
    s = re.sub(r"\\textsuperscript\{(\w)\}", r" (\1)", s)
    s = re.sub(r"\\multicolumn\{\d+\}\{\w\}\{(.*)\}$", r"\1", s)
    for a, b in (("$", ""), ("{,}", ","), ("\\%", "%"), ("\\,", " "), ("~", " "), ('\\"a', "ä"), ("\\|", "||"), ("\\times", "x"),
                 ("\\emph{", ""), ("\\cite{", "["), ("\\&", "&"), ("\\_", "_"), ("\\#", "#")):
        s = s.replace(a, b)
    return s


# ------------------------------------------------------------------------------------------------- cells
def num(c, scale=1.0, offset=0.0):
    return {"ptr": P(c), "scale": scale, "offset": offset}


def txt(c):
    return {"ptr": P(c), "as": "text"}


def A(c, op, value=None, c2=None):
    a = {"ptr": P(c), "op": op}
    if c2 is not None:
        a["ptr2"] = P(c2)
    elif op != "is_none":
        a["value"] = value
    return a


def L(text, md=None):
    return dict(text=text, md=md if md is not None else tex_clean(text), kind="label")


def X(text, shows, md=None, asserts=()):
    return dict(text=text, md=md if md is not None else tex_clean(text), kind="value", shows=list(shows), asserts=list(asserts))


def V(c, f, scale=1.0, offset=0.0, pre="", post="", asserts=()):
    return X(pre + f(v(c)) + post, [num(c, scale, offset)], asserts=asserts)


class Table:
    def __init__(self, name, colspec, header):
        self.name, self.colspec, self.header = name, colspec, header
        self.body = []

    def section(self, text, shows=(), asserts=()):
        self.body.append(("section", X(text, shows, asserts=asserts) if shows else L(text)))

    def add(self, *cells):
        assert len(cells) == self.ncol() or any("\\multicolumn" in c["text"] for c in cells), (self.name, [c["text"] for c in cells])
        self.body.append(("row", list(cells)))

    def ncol(self):
        return len(re.findall(r"p\{[^}]*\}|[lcr]", self.colspec))

    def tex(self):
        n = self.ncol()
        out = [f"\\begin{{tabular}}{{{self.colspec}}}", "\\toprule"] + self.header + ["\\midrule"]
        first = True
        for kind, item in self.body:
            if kind == "section":
                if not first:
                    out.append("\\midrule")
                out.append(f"\\multicolumn{{{n}}}{{l}}{{\\emph{{{item['text']}}}}} \\\\")
            else:
                out.append(" & ".join(c["text"] for c in item) + " \\\\")
            first = False
        return "\n".join(out + ["\\bottomrule", "\\end{tabular}", ""])

    def md(self, md_header):
        """GitHub-flavoured Markdown: a literal '|' inside a cell (norm bars) is escaped as '\\|', and a row whose TeX
        cell spans several columns is padded with empty cells, so every row has its header's cell count."""
        esc = lambda s: s.replace("|", "\\|")
        n = len(md_header)
        out = ["| " + " | ".join(esc(h) for h in md_header) + " |", "|" + "---|" * n]
        for kind, item in self.body:
            if kind == "section":
                out.append(f"| **{esc(item['md'])}** |" + " |" * (n - 1))
            else:
                cells = [esc(c["md"]) for c in item]
                assert len(cells) <= n, (self.name, cells)
                out.append("| " + " | ".join(cells) + " |" + " |" * (n - len(cells)))
        return "\n".join(out)

    def trace(self):
        rows = []
        for kind, item in self.body:
            cells = [item] if kind == "section" else item
            rows.append([dict(c, section=(kind == "section")) for c in cells])
        TRACE[self.name] = rows


def largest(prefix, wl=None):
    for x in DOC["largest_sizes"]:
        if x["configuration"].startswith(prefix) and (wl is None or wl in x["workload"]):
            return x
    raise KeyError(prefix)


def flagged(r_flag):
    """Superscript f for a timing whose activity check is flagged; the assert states the record's flag either way."""
    if v(r_flag) == "flagged":
        return "\\textsuperscript{f}", [A(r_flag, "==", "flagged")]
    return "", [A(r_flag, "in", ["ok", None])]


VERIFIED_IND = lambda r: [A(r["achieved_true_residual"], "<=", 1e-5)]


# ------------------------------------------------------------------------------------------------------------
# Table 1 (main): same-card fixed-state comparison with the two released codes
# ------------------------------------------------------------------------------------------------------------
def precision_cells(r, op, kr, it):
    return [X(op, [txt(r["operator_precision"])]), X(kr, [txt(r["krylov_precision"])]), X(it, [txt(r["iterate_precision"])])]


def t_external():
    t = Table("tab_comparison_external", "llcccrrrrrr", [
        "Code and solver & Native stop & Op. & Kryl. & Iter. & Steps & FP64 true residual & Factor per step & Solve (s) & Step (ms) & Memory (GB) \\\\"])
    r0 = ROWS["hou_T27_k256_hou_cg32_solve"]
    t.section(f"Hou et al.'s cantilever and element matrix, {sz(v(r0['elements']))} elements, start from zero", [num(r0["elements"])])
    H = [("hou_cg32", "released CuPy CG", "recursive, $10^{-3}$ of $\\|r_0\\|$", "32/64", "32", "32"),
         ("mg64_orig", "FP64 PCG, original V-cycle", "true, $10^{-5}$", "64", "64", "64"),
         ("mg64_rep", "FP64 PCG, repaired V-cycle", "true, $10^{-5}$", "64", "64", "64"),
         ("mgir_rep", "IR, repaired", "outer, $10^{-5}$", "32", "32", "64"),
         ("mgir_orig", "IR, original stencil", "outer, $10^{-5}$", "32", "32", "64")]
    for path, lab, stop, op, kr, it in H:
        r = ROWS[f"hou_T27_k256_{path}_solve"]
        head = [L(lab), X(stop, [txt(r["native_stop"])])] + precision_cells(r, op, kr, it)
        if v(r["steps"]) is None:
            r1, r2 = ROWS[f"hou_T27_k160_{path}_solve"], ROWS[f"hou_T27_k80_{path}_solve"]
            t.add(*head, X(f"\\multicolumn{{6}}{{l}}{{numerical breakdown (also at {sz(v(r1['elements']))}; verified at {sz(v(r2['elements']))})}}",
                           [num(r1["elements"]), num(r2["elements"])],
                           asserts=[A(r["status"], "==", "numerical breakdown"), A(r1["status"], "==", "numerical breakdown")] + VERIFIED_IND(r2)))
            continue
        steps = X(f"{v(r['steps'])}/{v(r['inner_steps'])}" if path.startswith("mgir") else ints(v(r["steps"])),
                  [num(r["steps"])] + ([num(r["inner_steps"])] if path.startswith("mgir") else []))
        t.add(*head, steps, V(r["achieved_true_residual"], sci), V(r["residual_factor_per_step"], fac),
              V(r["times"]["solve"], num_t), V(r["times"]["krylov_step"], num_t),
              V(r["memory"]["single_build_process_dedicated_peak"], gb, 1e-9, post="\\textsuperscript{a}",
                asserts=[A(r["memory"]["comparison_status"], "startswith", "inconclusive")]))
    for st, title in (("S1", "state of the first design iteration, start from zero"),
                      ("S5", "state of the fifth solve, start from the released fourth solution")):
        r0 = ROWS[f"traeff_T28_k160_{st}_traeff"]
        t.section(f"Tr\\\"aff et al.'s cantilever, {sz(v(r0['elements']))} elements, {title}", [num(r0["elements"])])
        PTH = [("traeff", "released OpenMP-offload PCG", "recursive, $10^{-5}$ of $\\|b\\|$", "32/64", "32", "64"),
               ("mg64_orig", "FP64 PCG, original V-cycle", "true, $10^{-5}$", "64", "64", "64"),
               ("mg64_rep", "FP64 PCG, repaired V-cycle", "true, $10^{-5}$", "64", "64", "64"),
               ("mgir_rep", "IR, repaired", "outer, $10^{-5}$", "32", "32", "64")]
        for path, lab, stop, op, kr, it in PTH:
            r = ROWS[f"traeff_T28_k160_{st}_{path}"]
            if path == "mgir_rep":
                steps = X(f"{v(r['steps'])}/{v(r['inner_steps'])}", [num(r["steps"]), num(r["inner_steps"])])
            elif path == "traeff" and v(r["steps"]) == 1000:
                steps = X(ints(v(r["steps"])) + "\\textsuperscript{c}", [num(r["steps"])], asserts=[A(r["status"], "==", "iteration cap")])
            else:
                steps = V(r["steps"], ints)
            t.add(L(lab), X(stop, [txt(r["native_stop"])]), *precision_cells(r, op, kr, it), steps,
                  V(r["achieved_true_residual"], sci), V(r["residual_factor_per_step"], fac), V(r["times"]["solve"], num_t),
                  V(r["times"]["krylov_step"], num_t, post="\\textsuperscript{b}" if path == "traeff" else ""), V(r["memory"]["M1"], gb, 1e-9))
    t.trace()
    md_head = ["Code and solver", "Native stop", "Op.", "Kryl.", "Iter.", "Steps", "FP64 true residual", "Factor per step", "Solve (s)", "Step (ms)", "Memory (GB)"]
    pu = {p: v(ROWS[f"hou_T27_k256_{p}_solve"]["memory"]["single_build_pool_used_peak"]) for p in ("hou_cg32", "mg64_rep", "mgir_rep")}
    h160, h256 = ROWS["hou_T27_k160_hou_cg32_solve"]["times"]["solve"], ROWS["hou_T27_k256_hou_cg32_solve"]["times"]["solve"]
    assert v(h160["n_timed_solves"]) == 3 and v(h256["n_timed_solves"]) == 1 and "grid size" in v(h160["sample_rule"])
    ours = {p: ROWS[f"hou_T27_k256_{p}_solve"]["times"]["solve"] for p in ("mg64_orig", "mg64_rep", "mgir_rep", "mgir_orig")}
    assert all(v(c["n_timed_solves_planned"]) == 3 for c in ours.values())
    assert [v(ours[p]["n_timed_solves"]) for p in ("mg64_orig", "mg64_rep", "mgir_rep", "mgir_orig")] == [3, 3, 3, 0] and v(ours["mgir_orig"]) is None
    tr = [ROWS[f"traeff_T28_k160_{s}_traeff"]["times"]["solve"] for s in ("S1", "S5")]
    assert [v(c["n_timed_solves"]) for c in tr] == [3, 1] and "by duration" in v(tr[0]["sample_rule"]) and "120 s" in v(tr[0]["sample_rule"])
    notes = ("Op./Kryl./Iter.: precision (bits) of the operator, the Krylov vectors and the iterate; 32/64 = FP32 storage with FP64 element arithmetic. "
             "Steps: Krylov steps (IR: outer/inner). FP64 true residual: ||b-Ku||/||b|| of the returned iterate from an independent FP64 checker. "
             "Factor per step: (r_end/r_0)^(1/n) of FP64 true residuals, n = Krylov steps (IR: inner steps). Solve: our paths, median of three timed solves (original-stencil IR: none timed, as its solves broke down). "
             "The number of timed solves of each released code followed its own prespecified rule: for Hou et al.'s code it was fixed by grid size "
             f"(three timed solves at {mill(v(ROWS['hou_T27_k160_hou_cg32_solve']['elements']))} elements, median {v(h160):.1f} s; one at "
             f"{mill(v(ROWS['hou_T27_k256_hou_cg32_solve']['elements']))}); for the released OpenMP-offload code it was set by duration (three solves "
             "when the first took at most 120 s, otherwise that one solve; at 8.19M, three at S1 and one at S5). Step: synchronized time per Krylov step "
             "(ours: interval between successive preconditioner calls, IR within an outer step; Hou: between iteration starts; released OpenMP code: "
             "between iteration ends). Memory: dedicated GPU memory of the job "
             f"(a: from a separate run with one build and one solve, outside the prespecified protocol; the prespecified memory comparison, from the timed processes, "
             f"which retain two builds, is inconclusive, so this column gives no confirmatory memory ordering; Hou's value is mostly reserved pool memory and depends on the pool cap of that run; "
             f"by live allocation (pool used) Hou's {gb(pu['hou_cg32'])} GB lies between FP64 PCG's {gb(pu['mg64_rep'])} GB and IR's {gb(pu['mgir_rep'])} GB; "
             "the released OpenMP code: growth of the WSL virtual-machine process). "
             "b: per-step times of the released code come from its timing build, which ran 10% faster than the plain build. c: iteration cap of the released code. "
             "Neither released code reaches 1e-5 at any checked iterate, so every time ratio in this table is at unequal accuracy.")
    return t, md_head, notes


# ------------------------------------------------------------------------------------------------------------
# Table 2 (main): largest sizes by workload, with pass or refusal status
# ------------------------------------------------------------------------------------------------------------
def t_capacity():
    t = Table("tab_comparison_capacity", "lllll", ["Workload & Configuration & Largest completed & Status there & Next size: outcome \\\\"])

    def size(x, key="largest_pass_elements"):
        return V(x[key], sz)

    def nxt(x, words, asserts=()):
        return X(f"{sz(v(x['next_size_elements']))}: {words}", [num(x["next_size_elements"])], asserts=asserts)

    t.section("One operator application")
    x = largest("matrix-free 27-point stencil and seven other mappings, FP32")
    x64 = largest("matrix-free 27-point stencil and seven other mappings, FP64")
    t.add(L("application"), L("matrix-free stencil, FP32 and FP64"), size(x),
          X("no spill", [txt(x["spill"])], asserts=[A(x["spill"], "==", False), A(x64["spill"], "==", False)]), L("largest grid tested"))
    for fmt, lab in (("csr", "CSR"), ("bsr", "BSR")):
        xs = largest(f"cusparse_{fmt} SpMV, FP32, operator-survey")
        xu = largest(f"{lab} SpMV and value refresh, FP32, update-cost")
        rs, rn = ROWS[xs["largest_pass_row"]], ROWS[xs["next_size_row"]]
        t.add(L("application"), L(f"assembled {lab}, FP32, survey build rule\\textsuperscript{{a}}"), size(xs),
              X("completed", [txt(rs["status"])], asserts=[A(rs["status"], "==", "ok")]),
              nxt(xs, "not built under this rule", [A(rn["status"], "startswith", "skipped")]))
        ru, rnu = ROWS[xu["largest_pass_row"]], ROWS[xu["next_size_row"]]
        t.add(L("application"), L(f"assembled {lab}, FP32, update-study build rule\\textsuperscript{{a}}"), size(xu),
              V(xu["largest_pass_spmv"], lambda z: f"{1e3 * z:.2f}", 1e3, pre="completed; SpMV ", post="~ms"),
              nxt(xu, "not built under this rule", [A(rnu[f"{fmt}_status"], "startswith", "skipped")]))
    x = largest("Hou et al. released operator")
    t.add(L("application"), L("Hou et al. operator"), size(x),
          X("completed", [txt(ROWS[x["largest_pass_row"]]["spill"])], asserts=[A(ROWS[x["largest_pass_row"]]["spill"], "==", False)]),
          L("no larger valid run"))
    t.section("State solve on a fixed state")
    x = largest("Hou et al. CuPy CG")
    r = ROWS[x["largest_pass_row"]]
    t.add(L("Hou's cantilever"), L("released CuPy CG"), size(x),
          V(r["achieved_true_residual"], lambda z: f"{z:.3f}", pre="native stop; FP64 residual ",
            asserts=[A(r["status"], "==", "native stop"), A(r["achieved_true_residual"], ">", 1e-5)]),
          L("no larger size tested"))
    xa = [largest(f"authors' FP64 PCG, {s} on Hou") for s in ("original stencil V-cycle", "repaired V-cycle")]
    xi = largest("authors' IR, repaired on Hou")
    t.add(L("Hou's cantilever"), L("FP64 PCG (both V-cycles) and IR, repaired"), size(xi),
          X("verified", [txt(ROWS[z["largest_pass_row"]]["status"]) for z in xa + [xi]],
            asserts=sum((VERIFIED_IND(ROWS[z["largest_pass_row"]]) for z in xa + [xi]), []) +
                    [A(ROWS[z["largest_pass_row"]]["elements"], "==", v(xi["largest_pass_elements"])) for z in xa]),
          L("no larger size tested"))
    x = largest("authors' IR, original stencil on Hou")
    rl, rn = ROWS[x["largest_pass_row"]], ROWS[x["next_size_row"]]
    t.add(L("Hou's cantilever"), L("IR, original stencil"), size(x), X("verified", [txt(rl["status"])], asserts=VERIFIED_IND(rl)),
          nxt(x, "numerical breakdown", [A(rn["status"], "==", "numerical breakdown")]))
    S1 = " on Traeff's fixed state S1"
    for cfg, lab, status_words in (("Traeff et al. released code", "released OpenMP-offload PCG", "native stop; not verified at any size\\textsuperscript{b}"),
                                   ("authors' FP64 PCG (repaired)", "FP64 PCG, repaired V-cycle", None),
                                   ("authors' FP64 PCG (original V-cycle)", "FP64 PCG, original V-cycle", None),
                                   ("authors' IR (repaired)", "IR, repaired", None)):
        xr, xv = largest(cfg + S1, "run completed"), largest(cfg + S1, "verified")
        words = {"guard refusal": "not admitted (prediction)\\textsuperscript{d}", "spill": "stopped on spill into shared memory"}[v(xr["next_class"])]
        st_assert = [A(xr["next_class"], "==", v(xr["next_class"]))] + ([A(xr["admission_rule"], "contains", "free memory the CUDA driver reports")]
                                                                      if v(xr["next_class"]) == "guard refusal" else [])
        s_as = [A(xr["state"], "startswith", "S1:"), A(xv["state"], "startswith", "S1:")]
        if status_words:
            status = X(status_words, [txt(xr["next_class"])], asserts=[A(xv["largest_pass_elements"], "is_none")] + s_as)
        else:
            status = V(xv["largest_pass_elements"], sz, pre="native stop; verified up to ", post="\\textsuperscript{b}", asserts=s_as)
        t.add(L("Tr\\\"aff's cantilever, state S1 (from zero)"), L(lab), size(xr), status, nxt(xr, words, st_assert))
    # S5: the warm-started state exists only where the released design loop completed four design iterations
    S5 = " on Traeff's fixed state S5"
    x5r, x5v = largest("Traeff et al. released code" + S5, "run completed"), largest("Traeff et al. released code" + S5, "verified")
    cb = x5r["classes_by_k"]
    t.add(L("Tr\\\"aff's cantilever, state S5 (warm start)"), L("released OpenMP-offload PCG"), size(x5r),
          X("iteration cap at every completed size; not verified", [txt(x5r["native_stop_met_next_class"])],
            asserts=[A(x5r["state"], "startswith", "S5:"), A(x5r["native_stop_met_largest_elements"], "is_none"),
                     A(x5r["native_stop_met_next_class"], "==", "iteration cap"), A(x5v["largest_pass_elements"], "is_none")] +
                    [A(cb[kk], "==", 7) for kk in ("64", "128", "160")]),
          nxt(x5r, "no state S5 at this size\\textsuperscript{e}", [A(x5r["next_class"], "==", "not run"), A(x5r["no_s5_above"]["class_by_k_256"], "==", 6)]))
    xo = [largest(cfg + S5, "verified") for cfg in ("authors' FP64 PCG (repaired)", "authors' FP64 PCG (original V-cycle)", "authors' IR (repaired)")]
    xor = [largest(cfg + S5, "run completed") for cfg in ("authors' FP64 PCG (repaired)", "authors' FP64 PCG (original V-cycle)", "authors' IR (repaired)")]
    t.add(L("Tr\\\"aff's cantilever, state S5 (warm start)"), L("FP64 PCG (both V-cycles) and IR, repaired"), size(xo[2]),
          X("verified", [txt(z["next_class"]) for z in xo],
            asserts=[A(z["state"], "startswith", "S5:") for z in xo] +
                    [A(z["largest_pass_elements"], "==", v(xo[2]["largest_pass_elements"])) for z in xo + xor]),
          nxt(xo[2], "no state S5 at this size\\textsuperscript{e}", [A(z["next_class"], "==", "not run") for z in xo + xor] +
              [A(z["next_size_elements"], "==", v(xo[2]["next_size_elements"])) for z in xo]))
    t.section("Design loop on Tr\\\"aff et al.'s cantilever (each code its own workload)")
    xR = largest("Traeff et al. released code, design loop")
    t.add(L("released design loop"), L("released OpenMP-offload code"), size(xR),
          X("completed", [txt(xR["completed_by_k"]["160"]), txt(xR["design_iterations_rule"])],
            asserts=[A(xR["completed_by_k"][kk], "==", "completed") for kk in ("64", "128", "160")]),
          nxt(xR, "interrupted at the run-time cap\\textsuperscript{e}", [A(xR["next_class"], "==", 6), A(xR["note"], "contains", "wall cap")]))
    xL = [largest(cfg + ", matched-rule design loop") for cfg in ("authors' FP64 PCG (repaired)", "authors' FP64 PCG (original V-cycle)", "authors' IR (repaired)")]
    t.add(L("matched-rule design loop"), L("FP64 PCG (both V-cycles) and IR, repaired"), size(xL[2]),
          X("completed", [txt(z["completed_by_k"]["160"]) for z in xL],
            asserts=[A(z["completed_by_k"][kk], "==", "completed") for z in xL for kk in ("64", "128", "160")] +
                    [A(z["largest_pass_elements"], "==", v(xL[2]["largest_pass_elements"])) for z in xL]),
          X("next size not run (no completed released loop to start from)", [txt(z["next_class"]) for z in xL],
            asserts=[A(z["next_class"], "==", "not run") for z in xL]))
    t.section("Complete optimization")
    x = largest("IR, repaired difference form")
    ok_term = ["bounded_oscillation", "max_change"]
    xc = x["t27_confirmatory"]
    t.add(L("authors' three problems"), L("IR, repaired"),
          X(f"{sz(v(x['largest_pass_elements']))} (historical completion)\\textsuperscript{{c}}", [num(x["largest_pass_elements"])]),
          X("all three completed; the prespecified repaired cantilever run at this size was not admitted (prediction)",
            [txt(e) for e in x["evidence"]] + [txt(xc["status"]), txt(xc["admission_rule"])],
            asserts=[A(e, "in", ok_term) for e in x["evidence"]] +
                    [A(xc["status"], "==", "guard prediction"), A(xc["admission_rule"], "contains", "E_free (guard.effective_free_bytes)"),
                     A(xc["problem"], "startswith", "the authors' cantilever, repaired"),
                     A(xc["predicted_workspace"], ">", c2=xc["effective_free"])]),
          X(f"{sz(v(x['next_size_elements']))}: not run, predicted above the card's memory", [num(x["next_size_elements"])],
            asserts=[A(x["next_size_prediction"], ">", c2=x["device_total"])]))
    x = largest("IR, original stencil")
    ev = x["evidence"]
    t.add(L("authors' three problems"), L("IR, original stencil"), size(x),
          X("cantilever, torsion completed", [txt(e) for e in ev[:2]], asserts=[A(e, "in", ok_term) for e in ev[:2]]),
          X(f"bridge: no design at {sz(v(ev[2]['elements']))} and {sz(v(ev[3]['elements']))}",
            [num(ROWS['opt_E7_simp_bridge_k320_mg_ir_stencil']['elements']), num(ROWS['opt_E12_simp_bridge_k384_mg_ir_stencil']['elements'])],
            asserts=[A(ev[2], "startswith", "failed"), A(ev[3], "startswith", "failed")]))
    x = largest("FP64 PCG + FP32 V-cycle")
    rb = ROWS["opt_E12b_simp_cantilever_k384_mg64_stencil_poollimit"]
    ne = x["next_size_evidence"]
    xc = x["t27_confirmatory"]
    t.add(L("authors' three problems"), L("FP64 PCG"),
          X(f"{sz(v(x['largest_pass_elements']))} (historical completion)\\textsuperscript{{c}}", [num(x["largest_pass_elements"])]),
          X("all three completed; the prespecified repaired cantilever run at this size ran out of memory under its pool cap",
            [txt(e) for e in x["evidence"]] + [txt(xc["status"]), txt(xc["failure"])],
            asserts=[A(e, "in", ok_term) for e in x["evidence"]] +
                    [A(xc["status"], "==", "allocation failure"), A(xc["failure"], "contains", "OutOfMemoryError"),
                     A(xc["problem"], "startswith", "the authors' cantilever, repaired"), A(xc["operator"], "==", "stencil_diff")]),
          X(f"{sz(v(x['next_size_elements']))}: spill without a cap; out of memory with a {v(rb['pool_limit_GiB']):.1f}~GiB cap",
            [num(x["next_size_elements"]), num(rb["pool_limit_GiB"])],
            asserts=[A(ne[0], "contains", "spill"), A(ne[1], "contains", "OutOfMemoryError")]))
    x = largest("recursive-stop control")
    ev = x["evidence"]
    xe = x["t27_exploratory"]
    rc = ROWS["opt_E12_simp_cantilever_k320_mg32_rec_stencil"]
    t.add(L("authors' three problems"), L("recursive-stop control"),
          X(f"{sz(v(x['largest_pass_elements']))} (historical completion)\\textsuperscript{{c}}", [num(x["largest_pass_elements"]), txt(x["largest_pass_label"])],
            asserts=[A(x["largest_pass_label"], "startswith", "largest historical completion")]),
          X("states above $10^{-5}$ accepted; bridge breakdown", [txt(rc["native_stop"]), txt(ev[2])],
            asserts=[A(rc["states_above_1e-5"], ">", 0), A(ROWS["opt_E12_simp_torsion_k320_mg32_rec_stencil"]["states_above_1e-5"], ">", 0),
                     A(ev[2], "contains", "curvature")]),
          X(f"{sz(v(x['next_size_elements']))}: prespecified run not admitted (prediction); a run outside that rule completed the cantilever, "
            f"{v(xe['states_above_1e_5'])} of {v(xe['design_iterations'])} states above $10^{{-5}}$",
            [num(x["next_size_elements"]), num(xe["states_above_1e_5"]), num(xe["design_iterations"]), txt(rc["native_stop"])],
            asserts=[A(x["t27_confirmatory"]["status"], "==", "guard prediction"), A(xe["status"], "startswith", "native stop"),
                     A(xe["label"], "startswith", "EXPLORATORY"),
                     A(x["t27_confirmatory"]["admission_rule"], "contains", "E_free (guard.effective_free_bytes)"),
                     A(x["t27_confirmatory"]["effective_free_rule"], "contains", "smaller of the driver-reported free memory")]))
    t.trace()
    notes = ("Sizes are active elements. Verified: an independent FP64 residual <= 1e-5 at the returned iterate. "
             "a: the two assembled-matrix studies used different admission rules for the build: the operator survey required three times the "
             "estimated matrix storage to fit the free memory, the update-cost study 1.15 times (its fused build allocates only the matrix arrays); "
             "both refusals are predictions, not measured limits. "
             "b: at 33.6M and 65.5M elements the independent check is missing for every path, because the checker did not fit, so the accuracy "
             "relationship there is unresolved; the released code's allocated grid at 65.5M active elements has 79.6M elements. "
             "State S1 is the released first design state, solved from zero; state S5 is the density of the released fifth solve, solved from the "
             "released fourth solution. The 65.5M completions hold for S1 only. "
             "c: historical completions (the submitted paper's records), not results of the prespecified protocol. At the same size the prespecified "
             "runs fared as stated: for repaired IR and the recursive-stop control at 113.2M, not admitted because the predicted workspace plus 1.5 GiB "
             "exceeded the guard's effective free-memory estimate (the smaller of the driver-reported free memory and the total memory less the other "
             "processes' dedicated use); a prediction, not a measured limit. For FP64 PCG at 65.5M, an allocation failure in design iteration 3 under "
             "the pool cap of that protocol. For the recursive-stop control, a run outside the admission rule (not a lower bound) completed the "
             "cantilever at 113.2M. The paper-wide maximum is unchanged. "
             "d: on the fixed states, the predicted peak plus 1.5 GiB exceeded the free memory the driver reported; a prediction, not a measured limit. "
             "e: a state S5 exists only where the released design loop completed its first four design iterations. At 33.6M that loop was interrupted at "
             "its run-time cap, which also counted its in-loop transfers of whole vectors to the host; it was not run above that size, so no S5 state "
             "exists at 33.6M or above, and the matched-rule loops had no released loop to start from.")
    return t, ["Workload", "Configuration", "Largest completed", "Status there", "Next size: outcome"], notes


# ------------------------------------------------------------------------------------------------------------
# Table 3 (main, R1.2): cost of the repair against its accuracy, each on its own problem
# ------------------------------------------------------------------------------------------------------------
def t_cost():
    t = Table("tab_comparison_cost", "llrr", ["Quantity & Configuration & Value & Relative to the reference \\\\"])
    ap = {m: ROWS[f"app_E32_k320_{m}"] for m in ("stencil", "stencil_diff", "elem_atomic", "elem_mean", "elem_ref", "stencil_selfcorr", "mixed_fp64")}
    t.section(f"One FP32 application, authors' cantilever grid, {sz(v(ap['stencil']['elements']))} elements", [num(ap["stencil"]["elements"])])
    us_ms = lambda z: f"{z / 1000:.3f}~ms"
    APP = lambda m: V(ap[m]["times"]["application"], us_ms, 1e-3)
    PR = lambda m, f, scale=1.0, offset=0.0: V(PAIRS[f"app_E32_k320_{m}_ratio"]["value"], f, scale, offset)
    t.add(L("application"), L("original stencil"), APP("stencil"), L("reference"))
    t.add(L("application"), L("difference-form stencil"), APP("stencil_diff"), PR("stencil_diff", lambda z: pct(z - 1), 100, -1))
    t.add(L("application"), L("self-block correction"), APP("stencil_selfcorr"), PR("stencil_selfcorr", lambda z: pct(z - 1), 100, -1))
    t.add(L("application"), L("atomic element kernel"), APP("elem_atomic"), PR("elem_atomic", lambda z: f"{z:.2f}$\\times$ the difference form"))
    t.add(L("application"), L("element kernel, element mean"), APP("elem_mean"), PR("elem_mean", lambda z: pct(z - 1) + " vs atomic", 100, -1))
    t.add(L("application"), L("node kernel, FP64 arithmetic"), APP("mixed_fp64"), PR("mixed_fp64", lambda z: f"{z:.1f}$\\times$ the original"))
    oc = DOC["orientation_check"]["changes"]
    rd = ROWS["opt_E32_simp_cantilever_k320_mg64_stencil_diff_r1"]
    t.section(f"Complete cantilever optimization, {sz(v(rd['elements']))} elements, FP64 PCG; fine-level FP32 operator of the V-cycle swapped "
              "(mean of three paired repetitions)", [num(rd["elements"])])
    sec = lambda z: f"{z:.1f}~s"
    t.add(L("optimization time"), L("difference-form stencil"), V(oc["stencil"]["cells"]["reference_mean"], sec), L("reference"))
    for op, lab in (("stencil", "original stencil"), ("elem_atomic", "atomic element kernel")):
        c = oc[op]["cells"]
        t.add(L("optimization time"), L(lab), V(c["mean"], sec),
              X(f"{pct(v(c['paired_change_mean']))} ({pct(v(c['paired_change_min']))} to {pct(v(c['paired_change_max']))})",
                [num(c["paired_change_mean"], 100), num(c["paired_change_min"], 100), num(c["paired_change_max"], 100)]))
    t.section("Accuracy and robustness on their own problems")
    b64o, b64d, b64m = (ROWS[f"beam_E29_k64_{o}_own"] for o in ("stencil", "stencil_diff", "elem_mean"))
    beam = lambda r: X(f"slender beam, {sz(v(r['elements']))} elements", [num(r["elements"])])
    t.add(beam(b64o), L("original stencil"), V(b64o["compliance_rel_err_vs_fp64"], lambda z: f"{100 * z:.2f}\\%", 100), L("compliance error vs FP64"))
    t.add(beam(b64d), L("difference-form stencil"), V(b64d["compliance_rel_err_vs_fp64"], sci), L("compliance error vs FP64"))
    t.add(beam(b64m), L("element mean"), V(b64m["compliance_rel_err_vs_fp64"], sci), L("compliance error vs FP64"))
    b128 = ROWS["beam_E29_k128_stencil_own"]
    t.add(beam(b128), L("original stencil"), X("breakdown", [txt(b128["status"])], asserts=[A(b128["status"], "startswith", "breakdown")]),
          X("before the recursive residual reached $10^{-5}$", [txt(b128["native_stop"])]))
    br_ir = ROWS["opt_E7_simp_bridge_k320_mg_ir_stencil"]
    br_rc = ROWS["opt_E12_simp_bridge_k320_mg32_rec_stencil"]
    br_d = ROWS["opt_E32_simp_bridge_k320_mg64_stencil_diff"]
    br_o = ROWS["opt_E7_simp_bridge_k320_mg64_stencil"]
    br_i3 = ROWS["opt_E32_simp_bridge_k384_mg_ir_stencil_diff"]
    bridge = lambda r: X(f"bridge, {sz(v(r['elements']))}", [num(r["elements"])])
    done = lambda r: V(r["design_iterations"], ints, pre="completed, ", post=" design iterations", asserts=[A(r["status"], "in", ["bounded_oscillation", "max_change"])])
    t.add(bridge(br_ir), L("IR, original stencil"), X("no design", [txt(br_ir["status"])], asserts=[A(br_ir["status"], "startswith", "failed")]),
          V(br_ir["design_iterations_completed"], ints, pre="correction rejected after ", post=" design iterations",
            asserts=[A(br_ir["status"], "contains", "correction rejected")]))
    t.add(bridge(br_rc), L("recursive-stop control, original"), X("breakdown", [txt(br_rc["status"])], asserts=[A(br_rc["status"], "contains", "curvature")]),
          V(br_rc["design_iterations_completed"], ints, pre="negative curvature after ", post=" design iterations",
            asserts=[A(br_rc["status"], "contains", "curvature -")]))
    t.add(bridge(br_o), L("FP64 PCG, original"), V(br_o["times"]["optimization_compute"], sec), done(br_o))
    t.add(bridge(br_d), L("FP64 PCG, repaired"), V(br_d["times"]["optimization_compute"], sec), done(br_d))
    t.add(bridge(br_i3), L("IR, repaired"), V(br_i3["times"]["optimization_compute"], sec), done(br_i3))
    o80, r80 = ROWS["hou_T27_k80_mgir_orig_solve"], ROWS["hou_T27_k80_mgir_rep_solve"]
    t.section(f"Hou et al.'s cantilever, {sz(v(o80['elements']))} elements, solve from zero", [num(o80["elements"])])
    t.add(L("IR solve"), L("original stencil"), V(o80["times"]["solve"], lambda z: f"{z:.3f}~s"),
          X(f"{v(o80['steps'])} outer / {v(o80['inner_steps'])} inner steps", [num(o80["steps"]), num(o80["inner_steps"])]))
    t.add(L("IR solve"), L("difference-form stencil"), V(r80["times"]["solve"], lambda z: f"{z:.4f}~s"),
          V(PAIRS["hou_T27_k80_mgir_rep_over_mgir_orig"]["value"], lambda z: f"{z:.3f}$\\times$ the original"))
    t.trace()
    notes = ("Each accuracy entry is on its own problem; no cost is averaged across solvers or precision paths. Application: median of 11 "
             "randomized timing blocks. Optimization-time changes are paired within a repetition (each operator once in each position of a balanced order): "
             "(t - t_difference)/t_difference; range over the three pairs. Beam controls: FP32 CG with the operator's own FP32 V-cycle, FP64 iterate, "
             "stopped at the recursive residual 1e-5; the supplement gives every grid and the common-V-cycle controls.")
    return t, ["Quantity", "Configuration", "Value", "Relative to the reference"], notes


# ------------------------------------------------------------------------------------------------------------
# Supplement tables
# ------------------------------------------------------------------------------------------------------------
def t_hou_hist():
    t = Table("tab_supp_hou_historical", "rrrrrrrrrr", [
        " & \\multicolumn{3}{c}{one application (ms)} & \\multicolumn{3}{c}{their FP32 CG to $10^{-3}$} & \\multicolumn{3}{c}{FP64 PCG + FP32 V-cycle} \\\\",
        "\\cmidrule(lr){2-4}\\cmidrule(lr){5-7}\\cmidrule(lr){8-10}",
        "Elements & theirs & ours\\textsuperscript{a} & ratio & iter.\\textsuperscript{b} & time (s) & true res. & iter. & solve (s) & true res. \\\\"])
    for k in (16, 32, 64, 80, 128, 160, 256):
        th, ou = ROWS[f"hou_E10_k{k}_theirs"], ROWS[f"hou_E10_k{k}_ours"]
        n = v(th["elements"])
        el = X(f"{n / 1e3:.1f}k" if n < 1e6 else f"{n / 1e6:.2f}M", [num(th["elements"])])
        ms = lambda z: f"{1e3 * z:.2f}" if z >= 1e-3 else f"{1e3 * z:.3f}"
        cells = [el, V(th["times"]["application"], ms, 1e3), V(ou["times"]["application"], lambda z: f"{1e3 * z:.3f}", 1e3),
                 V(PAIRS[f"hou_E10_k{k}_application_ratio"]["value"], lambda z: f"{z:.0f}")]
        if "solve" in th["times"]:
            cells += [V(th["steps"], ints), V(th["times"]["solve"], lambda z: f"{z:.1f}"), V(th["achieved_true_residual"], sci),
                      V(ou["steps"], ints), V(ou["times"]["solve"], lambda z: f"{z:.2f}"), V(ou["achieved_true_residual"], sci)]
        else:
            cells += [X("\\multicolumn{6}{c}{operator only}", [txt(th["status"])], asserts=[A(th["status"], "startswith", "operator only")])]
        t.add(*cells)
    t.trace()
    rat = [v(PAIRS[f"hou_E10_k{k}_application_ratio"]["value"]) for k in (16, 32, 64, 80, 128, 160, 256)]
    kmax = (16, 32, 64, 80, 128, 160, 256)[rat.index(max(rat))]
    notes = ("Both codes in one process, Hou et al.'s element matrix and boundary conditions in both. a: ours = the ORIGINAL 27-point stencil, "
             "FP32, with their element matrix; their call includes its per-call allocations as released. Ratios therefore range from "
             f"{min(rat):.0f} to {max(rat):.0f} ({max(rat):.0f} at {v(ROWS[f'hou_E10_k{kmax}_theirs']['elements']) / 1e6:.2f}M elements). "
             "b: completed CG iterations (the released solver returns the zero-based index of its last iteration, so one is added). "
             "Their true residual is the FP64 residual of their FP32 iterate. The 33.55M row is an operator application only.")
    return t, ["Elements", "theirs (ms)", "ours (ms)", "ratio", "iter.", "time (s)", "true res.", "iter.", "solve (s)", "true res."], notes


def t_hou_t27():
    t = Table("tab_supp_hou_matched", "rllrrrrrrrr", [
        "Elements & Code and solver & Status & Steps & FP64 true res. & Factor & Solve (s) & Step (ms) & Krylov operator (ms)\\textsuperscript{c} & "
        "V-cycle stencil (ms)\\textsuperscript{c} & Memory (GB)\\textsuperscript{a} \\\\"])
    NAMES = {"hou_cg32": "released CuPy CG", "mg64_orig": "FP64 PCG, original V-cycle", "mg64_rep": "FP64 PCG, repaired V-cycle",
             "mgir_orig": "IR, original stencil", "mgir_rep": "IR, repaired"}
    msf = lambda z: f"{1e3 * z:#.3g}".rstrip(".")
    for k in (80, 160, 256):
        r0 = ROWS[f"hou_T27_k{k}_hou_cg32_solve"]
        t.section(f"{sz(v(r0['elements']))} elements" + (" (independent check outside the prespecified protocol\\textsuperscript{b})" if k == 160 else ""),
                  [num(r0["elements"])])
        for p, lab in NAMES.items():
            r = ROWS[f"hou_T27_k{k}_{p}_solve"]
            stv = v(r["status"])
            if stv == "native stop":
                stc = X("native stop", [txt(r["status"])], asserts=[A(r["status"], "==", "native stop"), A(r["achieved_true_residual"], ">", 1e-5)])
            elif stv == "numerical breakdown":
                stc = X("breakdown", [txt(r["status"])], asserts=[A(r["status"], "==", "numerical breakdown")])
            elif stv.startswith("verified"):
                stc = X("verified", [txt(r["status"])], asserts=[A(r["status"], "startswith", "verified")] + VERIFIED_IND(r))
            else:
                stc = X("accepted in-process\\textsuperscript{b}", [txt(r["status"])],
                        asserts=[A(r["status"], "startswith", "in-process acceptance"), A(r["insolver_residual"], "<=", 1e-5)])
            if v(r["steps"]) is None:
                steps = L("--")
            elif p.startswith("mgir"):
                steps = X(f"{v(r['steps'])}/{v(r['inner_steps'])}", [num(r["steps"]), num(r["inner_steps"])])
            else:
                steps = V(r["steps"], ints)
            fs, fa = flagged(r["timing_flag"])
            ka = ROWS[r["applications"]["krylov_operator_row"]]
            kfs, kfa = flagged(ka["timing_flag"])
            if r["applications"]["vcycle_fine_level_row"]:
                va = ROWS[r["applications"]["vcycle_fine_level_row"]]
                vfs, vfa = flagged(va["timing_flag"])
                vcell = V(va["times"]["application"], msf, 1e3, post=vfs, asserts=vfa)
            else:
                vcell = L("--")
            solve = V(r["times"]["solve"], num_t, post=fs if v(r["times"]["solve"]) is not None else "", asserts=fa)
            step = V(r["times"]["krylov_step"], num_t, post=fs if v(r["times"]["krylov_step"]) is not None else "", asserts=fa)
            mc = r["memory"]["single_build_process_dedicated_peak"]
            m_as = [A(r["memory"]["comparison_status"], "startswith", "inconclusive")]
            if "coverage" in mc:
                m_post = "\\textsuperscript{w}"
                m_as.append(A(mc["coverage"], "contains", "coverage held from the watcher's first sampler baseline"))
            else:
                m_post = ""
            t.add(L(""), L(lab), stc, steps, V(r["achieved_true_residual"], sci), V(r["residual_factor_per_step"], fac), solve, step,
                  V(ka["times"]["application"], msf, 1e3, post=kfs, asserts=kfa), vcell,
                  V(mc, gb, 1e-9, post=m_post if v(mc) is not None else "", asserts=m_as))
    t.trace()
    notes = ("Separate processes; Hou et al.'s element matrix, supports, load, numbering and zero start in every path. "
             "a: dedicated GPU memory of a separate run with one build and one solve, outside the prespecified protocol; the prespecified memory comparison, "
             "from the timed processes, which retain two builds, is inconclusive, so the column gives no confirmatory ordering. "
             "w: sampled from the spill watcher's first baseline onward, not over the whole process. "
             "b: at 8.19M the independent residuals come from a supplementary check outside the prespecified protocol; the status rests on the in-process FP64 acceptance. "
             "c: one application of the operator in the Krylov iteration (Hou: their operator; FP64 PCG: the FP64 node operator; IR: the inner FP32 stencil) "
             "and of the FP32 stencil on the V-cycle's fine level (original or repaired; for IR the same stencil as the inner operator). "
             "f: the activity check flagged foreign GPU use of 1-5% near this timing (not excluded). "
             "Step: CUDA events at successive preconditioner calls (IR: within an outer step); Hou: between successive iteration starts. "
             "Hou's code reaches 1e-5 at none of its checked iterates up to 10,000 iterations.")
    return t, ["Elements", "Code and solver", "Status", "Steps", "FP64 true res.", "Factor", "Solve (s)", "Step (ms)", "Krylov operator (ms)",
               "V-cycle stencil (ms)", "Memory (GB)"], notes


def t_traeff():
    t = Table("tab_supp_traeff", "rllrrrrrrrr", [
        "Elements & State & Code and solver & Steps & In-solver res. & FP64 true res. & Factor & Setup a / b (s) & Solve (s) & Step (ms) & Memory (GB) \\\\"])
    NAMES = {"traeff": "released OpenMP-offload PCG", "mg64_orig": "FP64 PCG, original V-cycle", "mg64_rep": "FP64 PCG, repaired V-cycle", "mgir_rep": "IR, repaired"}
    WORD = {"not run": "not run (no state available)", "guard refusal": "not admitted (predicted peak above free memory)",
            "spill": "stopped: spill into shared memory"}
    for k in (64, 128, 160, 256, 320, 384):
        r0 = ROWS[f"traeff_T28_k{k}_S1_traeff"]
        t.section(f"{sz(v(r0['elements']))} elements" + (" (descriptive: independent check and system-identity gate missing)" if k in (256, 320) else ""),
                  [num(r0["elements"])])
        for st in ("S1", "S5"):
            for p, lab in NAMES.items():
                r = ROWS[f"traeff_T28_k{k}_{st}_{p}"]
                cls = v(r["status"])
                if cls in WORD:
                    if cls == "not run" and k > 160:
                        continue
                    t.add(L(""), L(st), L(lab), X(f"\\multicolumn{{8}}{{l}}{{{WORD[cls]}}}", [txt(r["status"])], asserts=[A(r["status"], "==", cls)]))
                    continue
                steps = (X(f"{v(r['steps'])}/{v(r['inner_steps'])}", [num(r["steps"]), num(r["inner_steps"])]) if p == "mgir_rep" else V(r["steps"], ints))
                sa, sb = r["setup"]["a"], r["setup"]["b"]
                g = r["times"]["krylov_step"]["g4_step"]
                if v(g["activity"]) == "unresolved":
                    step = V(r["times"]["krylov_step"], num_t, post="\\textsuperscript{u}", asserts=[A(g["activity"], "==", "unresolved")])
                else:
                    step = V(r["times"]["krylov_step"], num_t, asserts=[A(g["activity"], "in", ["ok", "flagged"])])
                t.add(L(""), L(st), L(lab), steps, V(r["insolver_residual"], sci), V(r["achieved_true_residual"], sci), V(r["residual_factor_per_step"], fac),
                      X(f"{num_t(v(sa))} / {num_t(v(sb))}", [num(sa), num(sb)]), V(r["times"]["solve"], num_t, asserts=[A(r["times"]["solve"]["g4"]["activity"], "in", ["ok", "flagged"])]),
                      step, V(r["memory"]["M1"], gb, 1e-9))
    t.trace()
    st64 = ROWS["traeff_T28_k64_S1_traeff"]["times"]["krylov_step"]
    notes = ("Released: FP32 stencil input and output with FP64 element arithmetic, FP32 Krylov vectors and recursive residual, FP64 iterate, stop at "
             "||r||/||b|| < 1e-5 (FP32, recursive) or 1000 steps. Ours: FP64 operator with FP32 V-cycle and FP64 true-residual stop, or IR with an "
             "outer FP64 residual. S1 starts from zero; S5 from the released solution of the fourth design iteration. At 33.6M and 65.5M the "
             "factor of our paths uses the in-solver FP64 residual (no independent check), and the accuracy relationship with the released code is unresolved. "
             "Released step times come from its timing build, which ran 10% faster than the plain build. "
             "Interference: no whole-solve time is excludable under the 5% rule; that bound covers whole solves only. "
             f"u: at the duration of one Krylov step the 5% rule is unresolved (released, 0.52M, S1: about {v(st64['g4_step']['bound_pct']):.1f}%); "
             "the other step times meet it at step duration. The activity bounds cover the GPU processes present when the activity sampler started; "
             "the records neither establish coverage of a process created later nor show that one interfered.")
    return t, ["Elements", "State", "Code and solver", "Steps", "In-solver res.", "FP64 true res.", "Factor", "Setup a / b (s)", "Solve (s)", "Step (ms)", "Memory (GB)"], notes


def t_recursive():
    t = Table("tab_supp_recursive_control", "llrrrrrl", [
        "Problem & Elements & Design iterations & States above $10^{-5}$ & Largest state residual & Median state residual & Factor per step & Outcome \\\\"])
    for p in ("cantilever", "torsion", "bridge"):
        for k in (160, 320):
            r = ROWS[f"opt_E12_simp_{p}_k{k}_mg32_rec_stencil"]
            ok = v(r["status"]) in ("bounded_oscillation", "max_change")
            it = r.get("design_iterations") or r.get("design_iterations_completed")
            out = (X("completed", [txt(r["status"])], asserts=[A(r["status"], "in", ["bounded_oscillation", "max_change"])]) if ok else
                   X("Krylov breakdown (negative curvature)", [txt(r["status"])], asserts=[A(r["status"], "contains", "curvature -")]))
            t.add(L(p), V(r["elements"], sz), V(it, ints),
                  X(f"{v(r['states_above_1e-5'])} of {v(r['states_n'])}", [num(r["states_above_1e-5"]), num(r["states_n"])]),
                  V(r["state_true_residual_max"], sci), V(r["state_true_residual_median"], sci), V(r["residual_factor_per_step"], fac), out)
    t.trace()
    notes = ("Recursive-stop control: FP32 PCG with the FP32 V-cycle (original stencil), FP64 iterate, stop on the recursive FP32 residual at 1e-5, "
             "no FP64 test. State residuals are FP64 true residuals of the design-loop states, recorded but not used to stop. Factor per step: "
             "exp(sum log(r_end/r_start) / sum n) over the design-loop solves, r_start = true residual of the warm start, n = Krylov steps.")
    return t, ["Problem", "Elements", "Design iterations", "States above 1e-5", "Largest state residual", "Median state residual", "Factor per step", "Outcome"], notes


def t_precision():
    t = Table("tab_supp_precision_controls", "lllrrrr", [
        "Field & Elements & Solver & Steps & FP64 true res. & Factor per step & Compliance error \\\\"])
    NAMES = {"jac32": "FP32 Jacobi-PCG", "mg32": "FP32 MG-PCG", "mg32_x64": "FP32 MG-PCG, FP64 iterate", "mg_ir": "IR (certified)"}
    for fld in ("design", "uniform"):
        for k in (40, 80, 160, 320):
            for s, lab in NAMES.items():
                rid = f"prec_E8_k{k}_{fld}_{s}"
                if rid not in ROWS:
                    continue
                r = ROWS[rid]
                steps = X(f"{v(r['steps'])}/{v(r['inner_steps'])}", [num(r["steps"]), num(r["inner_steps"])]) if s == "mg_ir" else V(r["steps"], ints)
                t.add(L(fld), V(r["elements"], mill), L(lab), steps, V(r["achieved_true_residual"], sci), V(r["residual_factor_per_step"], fac),
                      V(r["compliance_rel_err"], sci))
    for op, lab in (("elem_mean", "FP32 MG-PCG, FP64 iterate, element mean"), ("elem_ref", "FP32 MG-PCG, FP64 iterate, corner reference")):
        r = ROWS[f"prec_E29_k320_uniform_{op}_mg32_x64"]
        t.add(L("uniform"), V(r["elements"], mill), L(lab), V(r["steps"], ints), V(r["achieved_true_residual"], sci), V(r["residual_factor_per_step"], fac),
              V(r["compliance_rel_err"], sci))
    t.trace()
    notes = ("Cold solves from zero on the authors' cantilever. Rows other than IR are single-precision controls stopped at the first pass of "
             "their recursive FP32 residual at 1e-5, without an FP64 test, with the original stencil unless named; the true residual is that "
             "of the iterate at that pass. Compliance error against a reference solved to an independently checked residual of about 1e-10.")
    return t, ["Field", "Elements", "Solver", "Steps", "FP64 true res.", "Factor per step", "Compliance error"], notes


def t_beam():
    t = Table("tab_supp_beam_controls", "llrrrrrr", [
        " & & \\multicolumn{3}{c}{own V-cycle} & \\multicolumn{3}{c}{common V-cycle (original stencil)} \\\\",
        "\\cmidrule(lr){3-5}\\cmidrule(lr){6-8}",
        "Elements & FP32 operator & Steps & FP64 true res. & Compliance error & Steps & FP64 true res. & Compliance error \\\\"])
    OPS = {"stencil": "original stencil", "stencil_diff": "difference-form stencil", "elem_atomic": "atomic element kernel",
           "elem_ref": "element kernel, corner reference", "elem_mean": "element kernel, element mean", "stencil_selfcorr": "self-block correction",
           "fp64_arith_node": "node kernel, FP64 arithmetic"}

    def trio(r):
        if r is None:
            return [L("--"), L("--"), L("--")]
        if v(r["steps"]) is None:
            return [X("\\multicolumn{3}{c}{breakdown}", [txt(r["status"])], asserts=[A(r["status"], "startswith", "breakdown")])]
        return [V(r["steps"], ints), V(r["achieved_true_residual"], sci), V(r["compliance_rel_err_vs_fp64"], sci)]
    for k in (8, 16, 32, 64, 128):
        first = True
        for op, lab in OPS.items():
            own, com = ROWS.get(f"beam_E29_k{k}_{op}_own"), ROWS.get(f"beam_E29_k{k}_{op}_common")
            r_any = own or com
            el = V(r_any["elements"], sz) if first else L("")
            first = False
            t.add(el, L(lab), *trio(own), *trio(com))
    t.trace()
    notes = ("Slender clamped beam (8 x 1 x 1, unit modulus, Poisson ratio 0.3, unit end load), solves from zero: FP32 CG with an FP32 V-cycle, FP64 "
             "iterate, stopped at the first pass of the recursive FP32 residual at 1e-5 without an FP64 test. Own V-cycle: its fine level is the same "
             "operator; common V-cycle: the original-stencil V-cycle for every operator, so the preconditioner is held fixed while the operator changes "
             "(for the original stencil both are the same configuration). The FP64-arithmetic node kernel was run with the common V-cycle only. "
             "Compliance error against the FP64 reference solve of the same grid.")
    return t, ["Elements", "FP32 operator", "Steps (own)", "FP64 true res. (own)", "Compliance error (own)", "Steps (common)", "FP64 true res. (common)",
               "Compliance error (common)"], notes


def t_sparse():
    t = Table("tab_supp_sparse", "rllrrrr", ["Elements & Format & Precision & SpMV (ms) & Stencil (ms) & Ratio & Matrix (GB) \\\\"])
    e2 = next(r for r in DOC["rows"] if r["id"].startswith("sparse_E2_"))
    e4 = next(r for r in DOC["rows"] if r["id"].startswith("sparse_E4_"))
    t.section("Operator survey (built only when 3 times the estimated matrix storage fits)", [txt(e2["admission"])])
    refused_seen = set()
    for r in DOC["rows"]:
        if not r["id"].startswith("sparse_E2_"):
            continue
        key = r["id"].rsplit("_k", 1)[0]
        if key in refused_seen:
            continue
        fmt = "CSR" if "csr" in r["id"] else "BSR"
        dt = "FP32" if "fp32" in r["id"] else "FP64"
        if v(r["status"]) == "ok":
            t.add(V(r["elements"], mill), L(fmt), L(dt), V(r["times"]["application"], lambda z: f"{z / 1e3:.3f}", 1e-3),
                  V(r["times"]["matrix_free_stencil_same_file"], lambda z: f"{z / 1e3:.4f}", 1e-3), V(r["times"]["ratio_to_stencil"], lambda z: f"{z:.1f}"),
                  V(r["memory"]["matrix_storage"], gb, 1e-9))
        else:
            refused_seen.add(key)
            t.add(V(r["elements"], mill), L(fmt), L(dt),
                  X("\\multicolumn{4}{l}{not built under this rule (larger grids likewise)}", [txt(r["status"])], asserts=[A(r["status"], "startswith", "skipped")]))
    t.section("Update-cost study (built only when 1.15 times the estimated matrix storage fits)", [txt(e4["admission"])])
    e4_refused = set()
    for r in DOC["rows"]:
        if not r["id"].startswith("sparse_E4_"):
            continue
        st = r["times"]["stencil_application"]
        for fmt in ("csr", "bsr"):
            key = f"{fmt}_apply_fp32_s"
            if key in r["times"]:
                t.add(V(r["elements"], mill), L(fmt.upper()), L("FP32"), V(r["times"][key], lambda z: f"{1e3 * z:.3f}", 1e3),
                      V(st, lambda z: f"{1e3 * z:.4f}", 1e3), V(r["times"][key + "_in_applications"], lambda z: f"{z:.1f}"),
                      V(r["memory"][f"{fmt}_storage"], gb, 1e-9))
            elif f"{fmt}_status" in r and fmt not in e4_refused:
                e4_refused.add(fmt)
                t.add(V(r["elements"], mill), L(fmt.upper()), L("FP32"),
                      X("\\multicolumn{4}{l}{not built under this rule (larger grids likewise)}", [txt(r[f"{fmt}_status"])],
                        asserts=[A(r[f"{fmt}_status"], "startswith", "skipped")]))
    t.trace()
    assert "identical coefficients" in v(e2["coefficients"]) and "first field E" in v(e4["coefficients"]) and "on E2" in v(e4["coefficients"])
    notes = ("Operator survey: one application each, median of 11 randomized timing blocks; update-cost study: median of 21 host-synchronized calls. "
             "Stencil = original 27-point stencil of the same record and precision. Coefficients: in the operator survey every operator of a row "
             "applies the same modulus field, so each comparison uses identical coefficients. In the update-cost study the stencil was timed on a "
             "modulus field E and the sparse product on a second field E2 drawn from the same distribution (the matrix is built from E, refreshed "
             "to E2, then timed). The two studies used the same assembled-matrix classes; "
             "they differ in the admission rule for the build, so each refusal is a prediction under its own rule, not a measured limit.")
    return t, ["Elements", "Format", "Precision", "SpMV (ms)", "Stencil (ms)", "Ratio", "Matrix (GB)"], notes


def t_literature():
    t = Table("tab_supp_literature", "p{4.2cm}p{3.6cm}p{6.4cm}p{3.2cm}r", ["Work and code & Device & Workload & Quantity & Value \\\\"])
    cite = {"traff2023simple": "Tr\\\"aff et al.~\\cite{traff2023simple}", "wang2025matrixfree": "Wang et al.~\\cite{wang2025matrixfree}",
            "liu2018narrowband": "Liu et al.~\\cite{liu2018narrowband}", "hou2025cupy": "Hou et al.~\\cite{hou2025cupy}"}

    def esc(s):
        for a, b in (("\\", "\\textbackslash{}"), ("&", "\\&"), ("%", "\\%"), ("_", "\\_"), ("#", "\\#")):
            s = s.replace(a, b)
        return s

    def kind_word(k):
        """T14's own classification: the words before its first qualifier."""
        return re.split(r"[;(]", k or "stated by the source")[0].strip()

    for x in DOC["literature"]:
        if "work" not in x or x.get("dropped"):
            continue
        val = v(x["value"])
        unit_full = v(x["unit"]) or ""
        unit = unit_full.split(" (")[0]
        # a bound qualifier in T14's unit ("(over)", "(up to)") is part of the value and stays with it
        qual = re.search(r"\((over|up to|above|below|under|about|approximately)\)", unit_full)
        bound = (qual.group(1) + " ") if qual else ""
        vt = bound + (f"{val:,.0f}".replace(",", "{,}") if isinstance(val, (int, float)) and val >= 1000 else str(val)) + " " + unit
        val_asserts = [A(x["unit"], "contains", f"({qual.group(1)})")] if qual else []
        dev = v(x["device"]).split(". ")[0].replace("NVIDIA ", "")
        q = esc(v(x["quantity"]) + " (" + kind_word(v(x["kind"])) + ")")
        t.add(X(cite.get(x["work"], x["work"]) + ", " + esc(v(x["code"])), [txt(x["code"])], md=x["work"] + ", " + v(x["code"])),
              X(esc(dev), [txt(x["device"])], md=dev), X(esc(v(x["workload"])), [txt(x["workload"])], md=v(x["workload"])),
              X(q, [txt(x["quantity"]), txt(x["kind"])], md=tex_clean(q), asserts=[A(x["kind"], "startswith", kind_word(v(x["kind"])))]),
              dict(X(vt.strip(), [num(x["value"]), txt(x["unit"])], md=vt.strip().replace("{,}", ","), asserts=val_asserts),
                   **({"must_render": [bound.strip()]} if qual else {})))
    t.trace()
    notes = ("Published figures, each with its own device, code and workload; none was measured here and none is compared with our times. "
             "The word in brackets is the source's own status of the figure (measured, published estimate, demonstrated run, stated). "
             "Verbatim quotations and their locations are kept with the sources. Graphical-only memory values are omitted.")
    return t, ["Work and code", "Device", "Workload", "Quantity", "Value"], notes


def main():
    (OUT / "tables").mkdir(exist_ok=True)
    md = ["# T29 tables (generated by make_tables.py from comparison.json)", "",
          "LaTeX tabular bodies are in `tables/`; each cell's source is in `table_sources.json`. Suggested caption notes follow each table.", ""]
    for fn in (t_external, t_capacity, t_cost, t_hou_hist, t_hou_t27, t_traeff, t_recursive, t_precision, t_beam, t_sparse, t_literature):
        t, head, notes = fn()
        (OUT / "tables" / f"{t.name}.tex").write_text(t.tex(), encoding="utf-8")
        md += [f"## {t.name}", "", t.md(head), "", "Notes: " + notes, ""]
    (OUT / "comparison_tables.md").write_text("\n".join(md), encoding="utf-8")
    (OUT / "table_sources.json").write_text(json.dumps(TRACE, indent=1, ensure_ascii=False), encoding="utf-8")
    print("tables:", ", ".join(TRACE))


if __name__ == "__main__":
    main()
