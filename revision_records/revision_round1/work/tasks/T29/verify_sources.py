"""T29 check of comparison.json and of every rendered table cell.  CPU only.  Writes verify_sources.json.

1. Record cells: every {"v", "src"} cell is re-read from its record (JSON pointer or CSV line/column) and must hold
   the same value; a cell marked missing must be empty in its source.
2. Derived cells: every {"v", "formula", "op"} cell is recomputed here, independently of build_comparison.py, from
   its operand cells (each verified in turn) or, for op = "hist", from the optimization record it names.  A derived
   cell without an op, or a value cell with no provenance at all, is a problem.
3. Table cells (table_sources.json): every cell is either a label or a value cell.
   - A label must contain no number (footnote markers and LaTeX structure aside).
   - A value cell lists the comparison.json cells it shows ("shows": pointer, scale, offset, or as="text") and any
     claims it makes ("asserts").  Each pointer is resolved and verified as in 1-2.  The numbers in the rendered
     text are parsed and must equal the cited values (value x scale, after offset) within half a unit of the last
     displayed digit; a number shown from a text cell must occur in that text.  Every rendered number must be
     accounted for, and every cited value must be found.  Each assert is evaluated on the verified values.
4. The rendered files themselves: every generated tables/*.tex is parsed row by row and cell by cell, and so is the
   Markdown mirror comparison_tables.md.  Markdown rows are split as a GitHub-flavoured renderer splits them (at
   every unescaped pipe; '\|' is a literal bar), and every row must have its header's cell count.  Each rendered
   cell must equal its traced text, and the number and assert checks of 3 are run again on the rendered text, so a
   number changed in a .tex or .md file alone is caught.  A bound qualifier the source carries ("over", "up to")
   must appear in the rendered cell.  Headers show no number.
5. Table text and the suggested caption notes contain no run labels, file names or lab detail.

--selftest plants faults (altered record value, wrong pointer, wrong CSV column, altered ratio, altered derived
operand, run label in a table, altered rendered number, table value with its source removed, a false status assert,
an altered number in the final TeX only, an altered number in the Markdown mirror only, unescaped norm bars in the
Markdown mirror, a bound qualifier dropped from the TeX) and requires that each is caught.
"""
import copy
import csv
import json
import math
import re
import statistics
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
PROJ = Path(__file__).resolve().parents[4]  # T32 staging: project root
RUN = PROJ / "revision_round1"
WORK = RUN / "work"


def resolve(rel):
    return (PROJ if rel.startswith("results/") else WORK if rel.startswith("tasks/") else RUN) / rel


_cache = {}


def lookup(src):
    """Return the source value for 'file#/a/b' (JSON) or 'file:line#col' (CSV)."""
    if re.match(r".+\.csv:\d+#", src):
        f, rest = src.split(":", 1)
        line, col = rest.split("#", 1)
        if f not in _cache:
            with open(resolve(f), encoding="utf-8", newline="") as fh:
                rd = csv.reader(fh)
                hdr = next(rd)
                _cache[f] = {rd.line_num: dict(zip(hdr, rec)) for rec in rd}
        row = _cache[f][int(line)]
        if col not in row:
            raise KeyError(f"column {col}")
        s = row[col].strip()
        if s == "":
            return None
        try:
            f_ = float(s)
            return int(f_) if re.fullmatch(r"-?\d+", s) else f_
        except ValueError:
            return s
    f, ptr = src.split("#", 1)
    if f not in _cache:
        _cache[f] = json.loads(resolve(f).read_text(encoding="utf-8"))
    o = _cache[f]
    for p in [x.replace("~1", "/").replace("~0", "~") for x in ptr.strip("/").split("/") if x != ""]:
        if "*" in p:
            raise KeyError("wildcard")
        o = o[int(p)] if isinstance(o, list) else o[p]
    return o


def same(a, b, rel=1e-12):
    if isinstance(a, bool) or isinstance(b, bool):
        return a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        if isinstance(a, float) and math.isnan(a):
            return isinstance(b, float) and math.isnan(b)
        return a == b or abs(a - b) <= rel * max(abs(a), abs(b))
    return a == b


class Bad(Exception):
    pass


# ---------------------------------------------------------------------------------------------------- history ops
def _hget(x, field):
    o = x
    for p in field.split("."):
        if "|" in p:
            o = next((o[q] for q in p.split("|") if isinstance(o, dict) and q in o), None)
        else:
            o = o.get(p) if isinstance(o, dict) else None
        if o is None:
            return None
    return o


def hist_value(params):
    h = json.loads(resolve(params["file"]).read_text(encoding="utf-8"))["history"]
    agg, field = params["agg"], params["field"]
    if agg == "run_factor":
        lg, n = 0.0, 0
        for x in h:
            s = x.get("solve")
            if not isinstance(s, dict):
                continue
            rt, ri = s.get("rel_true"), s.get("rel_initial")
            it = s["inner_iters"] if "inner_iters" in s else s.get("iters")
            if all(isinstance(z, (int, float)) for z in (rt, ri, it)) and rt == rt and rt > 0 and ri > 0 and it > 0:
                lg += math.log(rt / ri)
                n += it
        return math.exp(lg / n)
    vals = [_hget(x, field) for x in h]
    fin = [x for x in vals if isinstance(x, (int, float)) and not isinstance(x, bool) and x == x]
    return {"len": lambda: len(vals), "sum": lambda: sum(fin), "mean": lambda: sum(fin) / len(vals),
            "max": lambda: max(fin), "median": lambda: statistics.median(fin), "count": lambda: len(fin),
            "count_gt": lambda: sum(x > params["threshold"] for x in fin)}[agg]()


# ---------------------------------------------------------------------------------------------------- cell check
STATS = {"record": 0, "record_missing": 0, "derived": 0, "basis": 0, "missing": 0}


def check_cell(c, at, bad, count=True):
    """Verify one cell; return its value.  Raises nothing; appends problems to bad."""
    if not isinstance(c, dict) or "v" not in c:
        bad.append(dict(at=at, problem="not a cell"))
        return None
    v = c["v"]
    if isinstance(c.get("src"), str) and "#" in c["src"] and "*" not in c["src"]:
        try:
            sv = lookup(c["src"])
        except Exception as e:  # noqa: BLE001
            bad.append(dict(at=at, src=c["src"], problem=f"unresolvable: {e}"))
            return v
        if v is None:
            if sv not in (None, ""):
                bad.append(dict(at=at, src=c["src"], problem=f"marked missing but source holds {sv!r}"))
            elif count:
                STATS["record_missing"] += 1
        elif not same(v, sv):
            bad.append(dict(at=at, src=c["src"], problem=f"value {v!r} != source {sv!r}"))
        elif count:
            STATS["record"] += 1
        return v
    if "op" in c:
        op = c["op"]
        try:
            if op == "hist":
                w = hist_value(c["params"])
            elif op == "len":                       # length of a list in a record, e.g. the timed solves
                o = json.loads(resolve(c["params"]["file"]).read_text(encoding="utf-8"))
                for p in c["params"]["path"]:
                    o = o[p]
                w = len(o)
            else:
                xs = [check_cell(o, f"{at}/operands/{i}", bad, count=False) for i, o in enumerate(c["operands"])]
                pr = c.get("params") or {}
                w = {"div": lambda: xs[0] / xs[1], "add1": lambda: xs[0] + 1,
                     "factor": lambda: (xs[0] / xs[1]) ** (1.0 / xs[2]), "two_k_cubed": lambda: 2 * xs[0] ** 3,
                     "count": lambda: len(xs), "median": lambda: statistics.median(xs), "mean": lambda: statistics.mean(xs),
                     "min": lambda: min(xs), "max": lambda: max(xs), "rel_change": lambda: (xs[0] - xs[1]) / xs[1],
                     "div_const": lambda: xs[0] / pr["divisor"],
                     "status_limit_bytes": lambda: int(re.search(r"limit set to: ([\d,]+) bytes", xs[0]).group(1).replace(",", "")),
                     }[op]()
        except Exception as e:  # noqa: BLE001
            bad.append(dict(at=at, problem=f"derived cell ({op}) does not recompute: {e!r}"))
            return v
        if not same(v, w, 1e-9):
            bad.append(dict(at=at, problem=f"derived {op}: stored {v!r} != recomputed {w!r}"))
        elif count:
            STATS["derived"] += 1
        return v
    if "formula" in c:
        bad.append(dict(at=at, problem="derived cell without an op (cannot be rechecked)"))
        return v
    if "basis" in c:
        if count:
            STATS["basis"] += 1
        return v
    if "missing" in c:
        if v is not None:
            bad.append(dict(at=at, problem="marked missing but holds a value"))
        if count:
            STATS["missing"] += 1
        return None
    bad.append(dict(at=at, problem=f"value {v!r} without provenance"))
    return v


def walk_cells(o, path, out):
    if isinstance(o, dict):
        if "v" in o and any(k in o for k in ("src", "formula", "basis", "missing", "op")):
            out.append((path, o))
            if "operands" not in o:
                for k, x in o.items():
                    if isinstance(x, (dict, list)):
                        walk_cells(x, f"{path}/{k}", out)
            return
        if "v" in o:
            out.append((path, o))
            return
        for k, x in o.items():
            walk_cells(x, f"{path}/{k}", out)
    elif isinstance(o, list):
        for i, x in enumerate(o):
            walk_cells(x, f"{path}/{i}", out)


def ptr_get(doc, ptr):
    o = doc
    for p in [x.replace("~1", "/").replace("~0", "~") for x in ptr.strip("/").split("/") if x != ""]:
        o = o[int(p)] if isinstance(o, list) else o[p]
    return o


# ---------------------------------------------------------------------------------------------------- numbers
_NUM = re.compile(r"(?P<sci>[-+]?\d+(?:\.\d+)?)\s*\\times\s*10\^\{(?P<sexp>[-+]?\d+)\}"
                  r"|(?<![A-Za-z\d.])(?P<enot>[-+]?\d+(?:\.\d+)?)[eE](?P<eexp>[-+]?\d+)(?![\dA-Za-z])"
                  r"|(?<![\w.])10\^\{(?P<pexp>[-+]?\d+)\}"
                  r"|(?<![A-Za-z\d.])(?P<plain>[-+]?\d+(?:\.\d+)?)(?P<suf>[kM](?![A-Za-z]))?(?![\dA-Za-z])")


def display_numbers(tex):
    """Numbers as rendered: (value, half unit of the last displayed digit)."""
    t = re.sub(r"\\textsuperscript\{[^}]*\}", "", tex)
    t = re.sub(r"\\multicolumn\{\d+\}\{[^}]*\}", "", t)
    t = re.sub(r"\\cite\{[^}]*\}", "", t)
    t = re.sub(r"\\(?:cmidrule|emph|textbf)\b", "", t)
    t = t.replace("{,}", "")
    t = re.sub(r"_\{[^}]*\}|_[A-Za-z0-9]", "", t)
    out = []
    for m in _NUM.finditer(t):
        if m.group("sci") is not None:
            s, e = m.group("sci"), int(m.group("sexp"))
            d = len(s.split(".")[1]) if "." in s else 0
            out.append((float(s) * 10 ** e, 0.5 * 10 ** (e - d)))
        elif m.group("enot") is not None:
            s, e = m.group("enot"), int(m.group("eexp"))
            d = len(s.split(".")[1]) if "." in s else 0
            out.append((float(s) * 10 ** e, 0.5 * 10 ** (e - d)))
        elif m.group("pexp") is not None:
            e = int(m.group("pexp"))
            out.append((10.0 ** e, 0.0))
        else:
            s = m.group("plain")
            mult = {"k": 1e3, "M": 1e6, None: 1.0}[m.group("suf")]
            d = len(s.split(".")[1]) if "." in s else 0
            out.append((float(s) * mult, 0.5 * 10 ** (-d) * mult))
    return out


def source_numbers(s):
    """Numbers appearing anywhere in a source string (liberal: FP32 gives 32, 10,000 gives 10000)."""
    s = str(s)
    s = re.sub(r"(?<=\d),(?=\d{3})", "", s)
    out = []
    for m in re.finditer(r"10\^\{?([-+]?\d+)\}?", s):
        out.append(10.0 ** int(m.group(1)))
    for m in re.finditer(r"\d+(?:\.\d+)?(?:[eE][-+]?\d+)?", s):
        out.append(float(m.group(0)))
    return out


def matches(tok, hu, x):
    return abs(tok - x) <= hu * (1 + 1e-6) + 1e-12 * abs(x)


def check_table_cell(doc, tname, i, j, c, bad):
    at = f"tables/{tname}[{i}][{j}]"
    text = c["text"]
    toks = display_numbers(text)
    if c.get("kind") == "label":
        if toks:
            bad.append(dict(at=at, text=text, problem=f"label shows numbers {[t for t, _ in toks]} without a source"))
        return "label"
    shows = c.get("shows") or []
    if not shows:
        bad.append(dict(at=at, text=text, problem="value cell without a source"))
        return "unsourced"
    expect, pool = [], []
    for s in shows:
        try:
            cell = ptr_get(doc, s["ptr"])
        except Exception as e:  # noqa: BLE001
            bad.append(dict(at=at, problem=f"pointer {s['ptr']} unresolvable: {e}"))
            continue
        v = check_cell(cell, at + " -> " + s["ptr"], bad, count=False)
        if s.get("as") == "text":
            pool += source_numbers(v)
        elif v is not None:
            expect.append((v + s.get("offset", 0.0)) * s.get("scale", 1.0))
    k = 0
    for tok, hu in toks:
        if k < len(expect) and matches(tok, hu, expect[k]):
            k += 1
        elif any(same(tok, p, 1e-9) or matches(tok, hu, p) for p in pool):
            continue
        else:
            bad.append(dict(at=at, text=text, problem=f"rendered number {tok:g} not found in the cited cells"))
    if k < len(expect):
        bad.append(dict(at=at, text=text, problem=f"cited value(s) {expect[k:]} not rendered"))
    for a in c.get("asserts") or []:
        try:
            x = check_cell(ptr_get(doc, a["ptr"]), at + " assert -> " + a["ptr"], bad, count=False)
            y = check_cell(ptr_get(doc, a["ptr2"]), at + " assert -> " + a["ptr2"], bad, count=False) if "ptr2" in a else a.get("value")
            ok = {"==": lambda: x == y, "<=": lambda: x is not None and x <= y, ">": lambda: x is not None and y is not None and x > y,
                  "in": lambda: x in y, "is_none": lambda: x is None, "startswith": lambda: isinstance(x, str) and x.startswith(y),
                  "contains": lambda: isinstance(x, str) and y in x}[a["op"]]()
        except Exception as e:  # noqa: BLE001
            ok = False
            a = dict(a, error=repr(e))
        if not ok:
            bad.append(dict(at=at, text=text, problem=f"assert failed: {a}"))
    return "value"


def parse_tex_table(text):
    """(header lines, body rows) of a generated tabular: each body row is ("section", text) or ("row", [cell texts])."""
    lines = [x for x in text.splitlines() if x.strip()]
    i_top, i_mid = lines.index("\\toprule"), lines.index("\\midrule")
    i_bot = lines.index("\\bottomrule")
    header = lines[i_top + 1:i_mid]
    body = []
    for ln in lines[i_mid + 1:i_bot]:
        if ln == "\\midrule":
            continue
        if not ln.endswith(" \\\\"):
            body.append(("bad", ln))
            continue
        s = ln[:-3]
        m = re.fullmatch(r"\\multicolumn\{\d+\}\{l\}\{\\emph\{(.*)\}\}", s)
        body.append(("section", m.group(1)) if m else ("row", s.split(" & ")))
    return header, body


def md_cells(ln):
    """Cells of one Markdown table row as a GitHub-flavoured renderer splits them: the outer pipes are dropped, the row is
    split at every pipe not escaped by a backslash, each cell is trimmed, and an escaped pipe '\\|' becomes '|'."""
    s = ln.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip().replace("\\|", "|") for c in re.split(r"(?<!\\)\|", s)]


def parse_md_tables(md):
    """{table name: body rows} of comparison_tables.md, split as a renderer does (md_cells).  The header fixes the cell
    count; the delimiter row must have the same count, and a body row with any other count is reported as "bad" (a
    renderer would drop or shift its cells).  Body rows: ("section", text) for a bold first cell with every other cell
    empty, else ("row", cells) with all header-count cells (multi-column rows end in empty padding cells)."""
    out, ncol, name, rows = {}, {}, None, None
    for ln in md.splitlines():
        if ln.startswith("## "):
            name = ln[3:].strip()
            rows = out.setdefault(name, [])
            continue
        if name is None or not ln.startswith("|"):
            continue
        cells = md_cells(ln)
        if name not in ncol:                       # the header row
            ncol[name] = len(cells)
            continue
        if all(re.fullmatch(r":?-{3,}:?", c) for c in cells):
            if len(cells) != ncol[name]:
                rows.append(("bad", f"delimiter row with {len(cells)} cells against {ncol[name]} header cells"))
            continue
        if len(cells) != ncol[name]:
            rows.append(("bad", f"{len(cells)} cells against {ncol[name]} header cells: {ln}"))
            continue
        m = re.fullmatch(r"\*\*(.*)\*\*", cells[0])
        if m and all(c == "" for c in cells[1:]):
            rows.append(("section", m.group(1)))
        else:
            rows.append(("row", cells))
    return out


def md_numbers_text(s):
    """Markdown cells use 1,234 separators; drop them so the number parser sees one number."""
    s = re.sub(r"(?<=\d)x(?![A-Za-z])", " x", s)          # "4.94x" (times) in the mirror
    return re.sub(r"(?<=\d),(?=\d{3}(?!\d))", "", s)


def check_rendered(doc, trace, tables_text, md_text, bad):
    """The final TeX and the Markdown mirror, parsed cell by cell: each cell must equal its traced text, and its
    rendered numbers and asserts are checked against the cited cells from the rendered text itself."""
    n = 0
    md_tabs = parse_md_tables(md_text) if md_text is not None else {}
    for tname, rws in trace.items():
        if tname not in tables_text:
            bad.append(dict(at=f"tables/{tname}.tex", problem="traced table has no TeX file"))
            continue
        try:
            header, body = parse_tex_table(tables_text[tname])
        except ValueError as e:
            bad.append(dict(at=f"tables/{tname}.tex", problem=f"unparsable tabular: {e}"))
            continue
        for h in header:
            h_ = re.sub(r"\\cmidrule\([a-z]*\)\{\d+-\d+\}", "", h)      # column spans
            h_ = re.sub(r"\$10\^\{-?\d+\}\$", "", h_)                  # thresholds such as 10^{-5}
            if display_numbers(h_):
                bad.append(dict(at=f"tables/{tname}.tex header", text=h, problem="header shows a number"))
        for form, rendered in (("tex", body), ("md", md_tabs.get(tname))):
            if rendered is None:
                bad.append(dict(at=f"comparison_tables.md#{tname}", problem="table missing from the Markdown mirror"))
                continue
            if len(rendered) != len(rws):
                bad.append(dict(at=f"{form}:{tname}", problem=f"{len(rendered)} rendered rows against {len(rws)} traced rows"))
            for i, (rw, (kind, item)) in enumerate(zip(rws, rendered)):
                cells = [item] if kind == "section" else item
                if form == "md" and kind == "row" and len(cells) > len(rw):
                    if any(c != "" for c in cells[len(rw):]):
                        bad.append(dict(at=f"md:{tname}[{i}]", text=str(item), problem="Markdown row has text in cells the traced row does not have"))
                        continue
                    cells = cells[:len(rw)]          # empty padding after a multi-column cell
                if kind == "bad" or (kind == "section") != bool(rw[0].get("section")) or len(cells) != len(rw):
                    bad.append(dict(at=f"{form}:{tname}[{i}]", text=str(item), problem="rendered row does not match the traced row's layout"))
                    continue
                for j, (c, txt_) in enumerate(zip(rw, cells)):
                    want = c["text"] if form == "tex" else c.get("md", "")
                    if txt_ != want:
                        bad.append(dict(at=f"{form}:{tname}[{i}][{j}]", text=txt_, problem=f"rendered text differs from the traced text {want!r}"))
                    shown = txt_ if form == "tex" else md_numbers_text(txt_)
                    check_table_cell(doc, f"{form}:{tname}", i, j, dict(c, text=shown), bad)
                    for w in c.get("must_render") or []:
                        if w not in txt_:
                            bad.append(dict(at=f"{form}:{tname}[{i}][{j}]", text=txt_, problem=f"required qualifier {w!r} not rendered"))
                    n += 1
    return n


BANNED = [r"\bT(12|14|27|28|29)\b", r"\bD\d{1,2}\b", r"\.json", r"\.csv", r"results/", r"tasks/", r"\bmg64_|\bmgir_|\bhou_cg32\b|\btraeff\b",
          r"\bclass \d\b", r"exploratory", r"\bseed\b", r"sha256|hash", r"20\d\d-\d\d-\d\d", r"\bbudget"]


def check(doc, trace, tables_text, md_text):
    for k in STATS:
        STATS[k] = 0
    bad = []
    cells = []
    walk_cells(doc, "", cells)
    for path, c in cells:
        check_cell(c, path, bad)
    kinds = {"label": 0, "value": 0, "unsourced": 0}
    n_tab = 0
    for tname, rws in trace.items():
        for i, rw in enumerate(rws):
            for j, c in enumerate(rw):
                kinds[check_table_cell(doc, tname, i, j, c, bad)] += 1
                n_tab += 1
    n_rendered = check_rendered(doc, trace, tables_text, md_text, bad)
    for name, text in list(tables_text.items()) + [("comparison_tables.md (table rows)", md_rows_only(md_text))]:
        for pat in BANNED:
            for m in re.finditer(pat, text):
                bad.append(dict(at=f"tables/{name}", problem=f"banned text {m.group(0)!r}"))
    return dict(cells_checked=len(cells), **{f"cells_{k}": v for k, v in STATS.items()},
                table_cells=n_tab, table_value_cells=kinds["value"], table_label_cells=kinds["label"],
                table_unsourced_cells=kinds["unsourced"], rendered_cells_checked=n_rendered, problems=bad)


def md_rows_only(md_text):
    """The table rows and suggested caption notes of the Markdown mirror (its headings and intro name the files)."""
    return "\n".join(ln for ln in (md_text or "").splitlines() if ln.startswith("|") or ln.startswith("Notes: "))


def first_value_cell(trace, tname):
    for i, rw in enumerate(trace[tname]):
        for j, c in enumerate(rw):
            if c.get("kind") != "label" and c.get("shows") and c["shows"][0].get("as") != "text" and display_numbers(c["text"]):
                return i, j
    raise LookupError(tname)


def main():
    doc = json.loads((OUT / "comparison.json").read_text(encoding="utf-8"))
    trace = json.loads((OUT / "table_sources.json").read_text(encoding="utf-8"))
    tables = {p.stem: p.read_text(encoding="utf-8") for p in (OUT / "tables").glob("*.tex")}
    md = (OUT / "comparison_tables.md").read_text(encoding="utf-8")
    res = check(doc, trace, tables, md)
    base = len(res["problems"])
    if "--selftest" in sys.argv:
        planted = []
        rid = {r["id"]: i for i, r in enumerate(doc["rows"])}
        d1 = copy.deepcopy(doc)
        d1["rows"][rid["hou_E10_k64_theirs"]]["times"]["application"]["v"] *= 1.01
        planted.append(("altered record value", d1, trace, tables))
        d2 = copy.deepcopy(doc)
        d2["rows"][rid["hou_E10_k64_theirs"]]["times"]["application"]["src"] = "results/E10/hou_k64.json#/their_apply_sx"
        planted.append(("wrong pointer", d2, trace, tables))
        d3 = copy.deepcopy(doc)
        c = d3["rows"][rid["hou_T27_k256_mg64_rep_solve"]]["times"]["solve"]
        c["src"] = c["src"].replace("solve_median_s", "solve_iqr_hi_s")
        planted.append(("wrong CSV column", d3, trace, tables))
        d3b = copy.deepcopy(doc)
        d3b["rows"][rid["hou_T27_k160_mgir_orig_solve"]]["times"]["solve"]["n_timed_solves"]["v"] = 3   # the planned count
        planted.append(("planned solve count reported as observed", d3b, trace, tables))
        d4 = copy.deepcopy(doc)
        next(x for x in d4["pairs"] if x["id"] == "hou_E10_k64_application_ratio")["value"]["v"] = 250.0
        planted.append(("altered ratio", d4, trace, tables))
        d5 = copy.deepcopy(doc)
        d5["rows"][rid["hou_E10_k64_theirs"]]["steps"]["operands"][0]["v"] = 1262   # the off-by-one fault
        planted.append(("altered derived operand", d5, trace, tables))
        t6 = dict(tables)
        t6["tab_comparison_external"] = t6["tab_comparison_external"] + "\n% mg64_rep from tasks/T27/hou_matched.csv\n"
        planted.append(("run label in a table", doc, trace, t6))
        tr7 = copy.deepcopy(trace)
        c7 = next(c for rw in tr7["tab_comparison_external"] for c in rw
                  if c.get("kind") == "value" and re.fullmatch(r"\d+\.\d+", c["text"]))
        c7["text"] = c7["text"][:-1] + str((int(c7["text"][-1]) + 5) % 10)      # last displayed digit off by 5 units
        planted.append(("altered rendered number", doc, tr7, tables))
        tr8 = copy.deepcopy(trace)
        i, j = first_value_cell(tr8, "tab_comparison_capacity")
        tr8["tab_comparison_capacity"][i][j]["shows"] = []
        planted.append(("table value with its source removed", doc, tr8, tables))
        tr9 = copy.deepcopy(trace)
        hit = next((c for rw in tr9["tab_comparison_capacity"] for c in rw if c.get("asserts")), None)
        if hit is not None:
            a = hit["asserts"][0]
            a["op"], a["value"] = "==", "a status no record holds"
            a.pop("ptr2", None)
        planted.append(("false status assert", doc, tr9, tables))
        planted = [p + (md,) for p in planted]
        # faults in the rendered files only, the source map left intact
        pi = next(n for n, x in enumerate(doc["pairs"]) if x["id"] == "hou_E10_k64_application_ratio")
        c10 = next(c for rw in trace["tab_supp_hou_historical"] for c in rw
                   if any(s.get("ptr") == f"/pairs/{pi}/value" for s in c.get("shows") or []))
        t10 = dict(tables)
        old = " & " + c10["text"] + " & "
        assert old in t10["tab_supp_hou_historical"]
        t10["tab_supp_hou_historical"] = t10["tab_supp_hou_historical"].replace(old, " & 250 & ", 1)   # 648-fold shown as 250
        planted.append(("altered number in the final TeX only", doc, trace, t10, md))
        old_md = "| " + c10["md"] + " |"
        assert old_md in md
        planted.append(("altered number in the Markdown mirror only", doc, trace, tables, md.replace(old_md, "| 250 |", 1)))
        assert "\\|r_0\\|" in md
        planted.append(("unescaped norm bars in the Markdown mirror (extra cells)", doc, trace, tables, md.replace("\\|", "|")))
        c12 = next(c for rw in trace["tab_supp_literature"] for c in rw if c.get("must_render"))
        t12 = dict(tables)
        t12["tab_supp_literature"] = t12["tab_supp_literature"].replace(c12["text"], c12["text"].replace(c12["must_render"][0] + " ", "", 1), 1)
        planted.append(("bound qualifier dropped from the final TeX", doc, trace, t12, md))
        st = []
        for lab, dd, tt, tx, mm in planted:
            rr = check(dd, tt, tx, mm)
            st.append(dict(fault=lab, caught=len(rr["problems"]) > base))
        res = check(doc, trace, tables, md)       # restore the counts of the real check
        res["selftest"] = st
    (OUT / "verify_sources.json").write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    print({k: (len(v) if k == "problems" else v) for k, v in res.items()})
    for b in res["problems"][:40]:
        print("  ", b)
    return 0 if not res["problems"] and all(x["caught"] for x in res.get("selftest", [{"caught": True}])) else 1


if __name__ == "__main__":
    sys.exit(main())
