"""T23 reader: recompute the E30 k=80 tolerance rows and the k=160 bridge sensitivity-error localization from the saved
records alone (endpoint JSONs, FP16 final fields, FP32 sensitivity dumps).  Needs only numpy and the standard library;
no GPU, no project code.

usage: python t23_reader.py --data <folder with the E30 records> --out <output folder> [--printed-table tab_tolerance_runs.tex]

Writes
  tolerance.csv               twelve k=80 rows (3 problems x 4 tolerances), each compared with the 1e-5 run of its problem
  localization.csv            seven k=160 bridge snapshots: 2-norm error, squared-error shares by density class and by rank
  localization_populations.csv  per-snapshot medians over two explicit populations (top 100 by |error|; intermediate density)
  historical_proxies.json     the submitted script's integer-index distance proxies, reproduced and described (not for the paper)
  checks.json                 the values the plan inventory and the submitted table state, against the recomputed ones

The mask, denominator, precision and solve stage of every column are given in statistics.md beside this script.
"""
import argparse
import csv
import json
import math
import re
from pathlib import Path

import numpy as np

PROBLEMS = ("cantilever", "bridge", "torsion")
TOLS = ("1e-03", "1e-04", "1e-05", "1e-06")
BASE = "1e-05"


def load_json(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def fp16_field(p):
    r = np.load(p)["rho"]
    assert r.dtype == np.float16, (p, r.dtype)
    return r


def rounding_preimage(s16):
    """Closed interval [lo, hi] of the values in [0, 1] that round to each stored FP16 value (round to nearest; the
    half-way points are included, so the interval is a superset of the FP32 values behind it).  The physical density
    is a projection into [0, 1]; an FP32 value one ulp above 1 would add 1.2e-7, ignored."""
    s = s16.astype(np.float64)
    up = np.nextafter(s16, np.float16(np.inf)).astype(np.float64) - s
    down = s - np.nextafter(s16, np.float16(-np.inf)).astype(np.float64)
    lo = np.where(s16 > 0, s - 0.5 * down, 0.0)
    hi = np.where(s16 < 1, s + 0.5 * up, 1.0)
    return lo, hi


def prestorage_mean_range(r16, rb16, same_run=False):
    """Sharp range of mean|x - y| over all FP32 fields x, y in [0, 1] that round to the stored r16, rb16.  The entries
    are independent, so the extremes of the mean are the means of the per-entry extremes of |x - y|.  When both
    fields are the same run (the 1e-5 baseline against itself), one FP32 field x = y lies behind both: the range is 0."""
    if same_run:
        return 0.0, 0.0
    lo, hi = rounding_preimage(r16)
    lob, hib = rounding_preimage(rb16)
    a, b = lo - hib, hi - lob                         # x - y ranges over [a, b]
    dmax = np.maximum(np.abs(a), np.abs(b))
    dmin = np.where((a <= 0) & (b >= 0), 0.0, np.minimum(np.abs(a), np.abs(b)))
    return float(dmin.mean()), float(dmax.mean())


def prestorage_extremes_attained(r16, rb16, same_run=False):
    """Sharpness check: build FP32 fields that round to the stored ones and attain the two extremes up to the FP32
    step at each interval end.  Returns the largest gap between an attained mean and the range end it targets.
    For the same run a single FP32 field is built and used on both sides, so the attained mean is 0."""
    lo, hi = rounding_preimage(r16)
    lob, hib = rounding_preimage(rb16)
    a, b = lo - hib, hi - lob
    big = np.abs(a) >= np.abs(b)
    xmax, ymax = np.where(big, lo, hi), np.where(big, hib, lob)
    overlap = (a <= 0) & (b >= 0)
    common = np.maximum(lo, lob)
    xmin = np.where(overlap, common, np.where(a > 0, lo, hi))
    ymin = np.where(overlap, common, np.where(a > 0, hib, lob))

    def fp32_in(v, s16):                              # nearest FP32 value that rounds to the stored FP16 value
        v32 = v.astype(np.float32)
        for _ in range(4):
            bad = v32.astype(np.float16) != s16
            if not bad.any():
                break
            v32 = np.where(bad, np.nextafter(v32, s16.astype(np.float32)), v32)
        assert (v32.astype(np.float16) == s16).all()
        return v32.astype(np.float64)

    if same_run:
        assert (r16 == rb16).all()
        x = fp32_in(lo, r16)                          # any FP32 field behind the stored one, used on both sides
        return float(np.abs(x - x).mean())
    pmin, pmax = prestorage_mean_range(r16, rb16)
    gmax = abs(float(np.abs(fp32_in(xmax, r16) - fp32_in(ymax, rb16)).mean()) - pmax)
    gmin = abs(float(np.abs(fp32_in(xmin, r16) - fp32_in(ymin, rb16)).mean()) - pmin)
    return max(gmax, gmin)


# ----------------------------------------------------------------------------------------------- k = 80 tolerance rows
def tolerance_rows(data):
    rows = []
    for prob in PROBLEMS:
        b = load_json(data / f"tol_{prob}_k80_mg64_stencil_diff_tol{BASE}.json")
        rb16 = fp16_field(data / b["density_file"])
        for t in TOLS:
            d = load_json(data / f"tol_{prob}_k80_mg64_stencil_diff_tol{t}.json")
            r16 = fp16_field(data / d["density_file"])
            assert r16.shape == rb16.shape == (d["n_elem"],)
            r64, rb64 = r16.astype(np.float64), rb16.astype(np.float64)
            diff = np.abs(r64 - rb64)                                     # exact: FP16 values subtracted in FP64
            # the submitted table generator: FP16 -> FP32, subtraction and mean in FP32
            l1_fp32 = float(np.abs(r16.astype(np.float32) - rb16.astype(np.float32)).mean())
            changed = r16 != rb16
            # FP16 bit patterns of non-negative values are ordered like the values: step count between stored values
            steps = np.abs(r16.view(np.uint16).astype(np.int32) - rb16.view(np.uint16).astype(np.int32))
            assert (r16 >= 0).all() and (rb16 >= 0).all()
            cls, clsb = r64 > 0.5, rb64 > 0.5
            half_bits = int(np.float16(0.5).view(np.uint16))
            near = lambda x: np.abs(x.view(np.uint16).astype(np.int32) - half_bits) <= 1
            tot = d["totals"]
            same_run = t == BASE                                          # the baseline row: one run on both sides
            assert same_run == (d["density_file"] == b["density_file"])
            pmin, pmax = prestorage_mean_range(r16, rb16, same_run)
            row = {
                "problem": prob, "tol": float(t), "n_elem": d["n_elem"],
                "design_iterations": d["iterations"], "termination": d["termination"],
                "krylov_iterations_loop": d["solver_iters_total"],
                "solve_s_loop": tot["solve_s"], "setup_s_loop": tot["setup_s"],
                "solve_plus_setup_s_loop": tot["solve_s"] + tot["setup_s"],
                "compliance_final_accepted": d["compliance_run"],
                "compliance_tight_fp64": d["compliance_ref"], "tight_rel_true_residual": d["ref_rel_true"],
                "compliance_tight_fp64_base": b["compliance_ref"],
                "rel_compliance_diff_pct": 100.0 * (d["compliance_ref"] - b["compliance_ref"]) / b["compliance_ref"],
                "krylov_ratio_to_base": d["solver_iters_total"] / b["solver_iters_total"],
                "time_ratio_to_base": (tot["solve_s"] + tot["setup_s"]) / (b["totals"]["solve_s"] + b["totals"]["setup_s"]),
                "mean_abs_drho_fp16_stored": float(diff.mean()),
                "mean_abs_drho_fp32_generator": l1_fp32,
                "max_abs_drho_fp16_stored": float(diff.max()),
                "changed_entries": int(changed.sum()),
                "changed_entries_one_fp16_step": int((steps == 1).sum()),
                "max_fp16_steps": int(steps.max()),
                "strict_gt05_crossings": int((cls != clsb).sum()),
                "crossings_up": int((cls & ~clsb).sum()), "crossings_down": int((~cls & clsb).sum()),
                "entries_eq_05_run": int((r16 == np.float16(0.5)).sum()),
                "entries_eq_05_base": int((rb16 == np.float16(0.5)).sum()),
                "entries_within_1step_of_05_run": int(near(r16).sum()),
                "entries_within_1step_of_05_base": int(near(rb16).sum()),
                # rounding is monotone: with no stored entry equal to 0.5, each stored entry is on the same side of 0.5
                # as the FP32 value it came from, so the crossing count is that of the FP32 fields before the cast
                "crossings_equal_prestorage": bool((r16 != np.float16(0.5)).all() and (rb16 != np.float16(0.5)).all()),
                # sharp range of the pre-storage mean |x - y| given only the stored s, t and x, y in [0, 1]
                "prestorage_mean_min": pmin, "prestorage_mean_max": pmax,
                "prestorage_mean_max_departure": max(float(diff.mean()) - pmin, pmax - float(diff.mean())),
                "prestorage_extremes_attained_gap": prestorage_extremes_attained(r16, rb16, same_run),
                "density_file": d["density_file"],
            }
            rows.append(row)
    return rows


def printed_rows(tex):
    """Parse the submitted tab_tolerance_runs.tex into {(problem, tol): cells}."""
    out = {}
    for line in Path(tex).read_text(encoding="utf-8").splitlines():
        m = re.match(r"(cantilever|bridge|torsion) & \$1\\times10\^\{(-\d)\}\$ & (.*)\\\\", line.strip())
        if not m:
            continue
        cells = [c.strip() for c in m.group(3).split("&")]
        out[(m.group(1), f"1e-0{m.group(2)[-1]}")] = cells
    return out


def sci_tex(v, d=1):
    """The submitted generator's formatter (make_tables_e29.py:13-23)."""
    if v == 0:
        return "0"
    e = int(math.floor(math.log10(abs(v))))
    m = v / 10 ** e
    if round(abs(m), d) >= 10:
        m, e = m / 10, e + 1
    return f"${m:.{d}f}\\times10^{{{e}}}$"


def compare_printed(rows, tex):
    pr = printed_rows(tex)
    res = []
    for r in rows:
        key = (r["problem"], f"{r['tol']:.0e}")
        cells = pr[key]
        base = key[1] == BASE
        mine = [str(r["design_iterations"]), str(r["krylov_iterations_loop"]), f"{r['solve_plus_setup_s_loop']:.1f}",
                "--" if base else f"{r['rel_compliance_diff_pct']:+.4f}\\%",
                "--" if base else sci_tex(r["mean_abs_drho_fp32_generator"]),
                "--" if base else str(r["strict_gt05_crossings"])]
        res.append({"row": f"{key[0]} {key[1]}", "printed": cells, "recomputed": mine, "match": cells == mine})
    return res


# ------------------------------------------------------------------------------------- k = 160 bridge localization
GROUPS = {  # density classes of the submitted script (E30_dump_analysis.py:21), on the dumped physical density
    "void": lambda rho: rho < 0.01,
    "intermediate": lambda rho: (rho >= 0.01) & (rho <= 0.99),
    "solid": lambda rho: rho > 0.99,
}


def localization(data):
    dump = data / "dump_bridge_k160_mg64"
    audit = {a["it"]: a for a in load_json(data / "audit_bridge_k160_mg64_stencil_diff_dump.json")["audits"]}
    audit_nd = {a["it"]: a for a in load_json(data / "audit_bridge_k160_mg64_stencil_diff.json")["audits"]}
    hist = load_json(data / "dump_bridge_k160_mg64_analysis.json")
    snaps, pops, proxies = [], [], {}
    files = sorted(dump.glob("dump_it*.npz"), key=lambda p: int(p.stem[7:]))
    for f in files:
        it = int(f.stem[7:])
        z = np.load(f)
        nx, ny, nz = (int(v) for v in z["shape"])
        for k in ("dc", "dc_ref", "rho_phys"):
            assert z[k].dtype == np.float32 and z[k].shape == (nx * ny * nz,)
        dc, dr, rho = (z[k].astype(np.float64) for k in ("dc", "dc_ref", "rho_phys"))
        e = dc - dr
        e2 = e ** 2
        tot = float(e2.sum())
        masks = {g: fn(rho) for g, fn in GROUPS.items()}
        assert sum(int(m.sum()) for m in masks.values()) == rho.size
        order = np.argsort(-np.abs(e), kind="stable")
        ae = np.abs(e)[order]
        rec = {"iteration": it, "n_elem": rho.size,
               "rel_err_2": math.sqrt(tot / float((dr ** 2).sum())),
               "rel_err_2_audit_record": audit[it]["sens_rel_err_2"],
               "rel_err_2_first_audit_run": audit_nd[it]["sens_rel_err_2"],
               "n_void": int(masks["void"].sum()), "n_intermediate": int(masks["intermediate"].sum()),
               "n_solid": int(masks["solid"].sum()),
               "n_grey_strict_audit": int(((rho > 0.01) & (rho < 0.99)).sum()),
               "n_grey_strict_audit_record": audit[it]["n_gray"]}
        for g, m in masks.items():
            rec[f"share_{g}"] = float(e2[m].sum()) / tot
        for n in (10, 100, 1000):
            rec[f"share_top{n}"] = float(e2[order[:n]].sum()) / tot
            rec[f"tie_gap_top{n}"] = float(ae[n - 1] - ae[n])           # > 0: the top-n set is unambiguous
        rec["solid_share_exceeds_intermediate"] = rec["share_solid"] > rec["share_intermediate"]
        rec["update_max_abs_diff_audit_record"] = audit[it]["update_max_abs_diff"]
        rec["update_n_diff_gt_1e-3_audit_record"] = audit[it]["update_n_diff_gt_1e-3"]
        rec["accepted_rel_true_residual"] = audit[it]["accepted_rel_true"]
        rec["reference_rel_true_residual"] = audit[it]["ref_rel_true"]
        snaps.append(rec)

        relerr = np.abs(e) / np.maximum(np.abs(dr), 1e-300)
        top100 = order[:100]
        inter = np.flatnonzero(masks["intermediate"])
        for name, ix in (("top100_abs_error", top100), ("intermediate_0.01_0.99", inter)):
            pops.append({"iteration": it, "population": name, "n": int(ix.size),
                         "median_rel_err": float(np.median(relerr[ix])) if ix.size else float("nan"),
                         "median_rho_phys": float(np.median(rho[ix])) if ix.size else float("nan"),
                         "share_sq_error": float(e2[ix].sum()) / tot,
                         "overlap_with_other_population": int(np.intersect1d(top100, inter).size)})

        # the submitted script's distance proxies (E30_dump_analysis.py:27-31): integer element indices, not element
        # centres; support "points" (0,0) and (nx-1,0), load "point" (nx/2, ny-1), normalised by ny; z ignored
        def proxy(ix):
            ex, ey, _ = np.unravel_index(ix, (nx, ny, nz))
            ds = np.minimum(np.hypot(ex, ey), np.hypot(nx - 1 - ex, ey)) / ny
            dl = np.hypot(ex - nx / 2, ny - 1 - ey) / ny
            return float(np.median(ds)), float(np.median(dl))
        ps, pl = proxy(top100)
        qs, ql = proxy(inter) if inter.size else (float("nan"), float("nan"))
        h = hist[f"dump_it{it}"]
        proxies[f"it{it}"] = {"top100": {"support_proxy_median": ps, "load_proxy_median": pl,
                                         "historical_record": [h["top100_dist_support_median"], h["top100_dist_load_median"]]},
                              "intermediate": {"support_proxy_median": qs, "load_proxy_median": ql}}
        assert abs(rec["share_top10"] - h["top_10"]) < 1e-12 and abs(rec["rel_err_2"] - h["rel_err_2"]) < 1e-12
        assert abs(ps - h["top100_dist_support_median"]) < 1e-12 and abs(pl - h["top100_dist_load_median"]) < 1e-12
        assert abs(float(np.median(relerr[top100])) - h["top100_rel_err_median"]) < 1e-12
    return snaps, pops, proxies


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        for r in rows:
            w.writerow({k: (repr(v) if isinstance(v, float) else v) for k, v in r.items()})


def close(a, b, rel):
    return abs(a - b) <= rel * abs(b)


def checks(rows, snaps, pops, printed):
    R = {(r["problem"], f"{r['tol']:.0e}"): r for r in rows}
    S = {s["iteration"]: s for s in snaps}
    P = {(p["iteration"], p["population"]): p for p in pops}
    b3 = R[("bridge", "1e-03")]
    others = [S[i]["rel_err_2"] for i in S if i != 67]
    c = [
        ("k80 bridge 1e-3 vs 1e-5 tight compliance difference +0.003624%", f"{b3['rel_compliance_diff_pct']:+.6f}", f"{b3['rel_compliance_diff_pct']:+.6f}" == "+0.003624"),
        ("k80 bridge 1e-3 tight compliance 0.16309835568", f"{b3['compliance_tight_fp64']:.11f}", f"{b3['compliance_tight_fp64']:.11f}" == "0.16309835568"),
        ("k80 bridge 1e-5 tight compliance 0.16309244473", f"{b3['compliance_tight_fp64_base']:.11f}", f"{b3['compliance_tight_fp64_base']:.11f}" == "0.16309244473"),
        ("k80 bridge tight residuals 7.62e-11 / 8.82e-11", f"{b3['tight_rel_true_residual']:.2e} / {R[('bridge', '1e-05')]['tight_rel_true_residual']:.2e}",
         f"{b3['tight_rel_true_residual']:.2e}" == "7.62e-11" and f"{R[('bridge', '1e-05')]['tight_rel_true_residual']:.2e}" == "8.82e-11"),
        ("k80 bridge 1e-3 mean |drho| 8.98547e-5 (8.985e-5)", f"{b3['mean_abs_drho_fp16_stored']:.5e}", f"{b3['mean_abs_drho_fp16_stored']:.5e}" == "8.98547e-05"),
        ("k80 bridge 1e-3 strict >0.5 crossings 92", b3["strict_gt05_crossings"], b3["strict_gt05_crossings"] == 92),
        ("k80 bridge Krylov 593 vs 1510, design its 77 vs 82", f"{b3['krylov_iterations_loop']} vs {R[('bridge', '1e-05')]['krylov_iterations_loop']}, {b3['design_iterations']} vs {R[('bridge', '1e-05')]['design_iterations']}",
         (b3["krylov_iterations_loop"], R[("bridge", "1e-05")]["krylov_iterations_loop"], b3["design_iterations"], R[("bridge", "1e-05")]["design_iterations"]) == (593, 1510, 77, 82)),
        ("k80 bridge solve+setup 5.4 vs 10.4 s", f"{b3['solve_plus_setup_s_loop']:.1f} vs {R[('bridge', '1e-05')]['solve_plus_setup_s_loop']:.1f}",
         (f"{b3['solve_plus_setup_s_loop']:.1f}", f"{R[('bridge', '1e-05')]['solve_plus_setup_s_loop']:.1f}") == ("5.4", "10.4")),
    ]
    for prob, n, m in (("cantilever", 3914, "6.11e-09"), ("bridge", 2724, "3.40e-09"), ("torsion", 4449, "1.25e-09")):
        r = R[(prob, "1e-06")]
        c.append((f"k80 {prob} 1e-6 vs 1e-5: {n} changed entries, mean {m}, 0 crossings",
                  f"{r['changed_entries']}, {r['mean_abs_drho_fp16_stored']:.2e}, {r['strict_gt05_crossings']}",
                  r["changed_entries"] == n and f"{r['mean_abs_drho_fp16_stored']:.2e}" == m and r["strict_gt05_crossings"] == 0))
    c += [
        ("k80 bridge 1e-3 vs 1e-5: pre-storage mean |drho| lies in [8.98285e-5, 1.38696e-4] (rounded outward), "
         "departure at most 4.885e-5 and below the stored mean",
         f"[{b3['prestorage_mean_min']:.6e}, {b3['prestorage_mean_max']:.6e}], {b3['prestorage_mean_max_departure']:.5e}",
         8.98285e-5 <= b3["prestorage_mean_min"] < 8.98295e-5 and f"{b3['prestorage_mean_max']:.5e}" == "1.38696e-04"
         and b3["prestorage_mean_max_departure"] <= 4.885e-5
         and b3["prestorage_mean_max_departure"] < b3["mean_abs_drho_fp16_stored"]),
        ("k80 all 12 pre-storage ranges are attained by FP32 fields that round to the stored ones (gap <= 1.2e-7)",
         max(r["prestorage_extremes_attained_gap"] for r in rows), all(r["prestorage_extremes_attained_gap"] <= 1.2e-7 for r in rows)),
        ("k80 the three 1e-5 baseline rows (run against itself): stored mean, pre-storage range and departure all exactly 0",
         [(r["problem"], r["mean_abs_drho_fp16_stored"], r["prestorage_mean_min"], r["prestorage_mean_max"], r["prestorage_mean_max_departure"])
          for r in rows if f"{r['tol']:.0e}" == BASE],
         sum(1 for r in rows if f"{r['tol']:.0e}" == BASE) == 3
         and all(r["mean_abs_drho_fp16_stored"] == r["prestorage_mean_min"] == r["prestorage_mean_max"]
                 == r["prestorage_mean_max_departure"] == r["prestorage_extremes_attained_gap"] == 0.0
                 for r in rows if f"{r['tol']:.0e}" == BASE)),
    ]
    s67 = S[67]
    c += [
        ("k80 all 12 crossing counts equal those of the FP32 fields before the FP16 cast (no stored entry equals 0.5)",
         sum(r["crossings_equal_prestorage"] for r in rows), all(r["crossings_equal_prestorage"] for r in rows)),
        ("k160 it67 2-norm error 0.169616", f"{s67['rel_err_2']:.6f}", f"{s67['rel_err_2']:.6f}" == "0.169616"),
        ("k160 it67 top-ten share 95.24%", f"{100 * s67['share_top10']:.2f}", f"{100 * s67['share_top10']:.2f}" == "95.24"),
        ("k160 it67 intermediate (75 elements) share 88.07%", f"{s67['n_intermediate']}, {100 * s67['share_intermediate']:.2f}",
         s67["n_intermediate"] == 75 and f"{100 * s67['share_intermediate']:.2f}" == "88.07"),
        ("k160 it67 median rel. error top 100 by |error| 17.96%", f"{100 * P[(67, 'top100_abs_error')]['median_rel_err']:.2f}",
         f"{100 * P[(67, 'top100_abs_error')]['median_rel_err']:.2f}" == "17.96"),
        ("k160 it67 median rel. error 75 intermediate 0.32%", f"{100 * P[(67, 'intermediate_0.01_0.99')]['median_rel_err']:.2f}",
         f"{100 * P[(67, 'intermediate_0.01_0.99')]['median_rel_err']:.2f}" == "0.32"),
        ("k160 other six snapshots 8.60e-6 to 3.95e-3", f"{min(others):.2e} to {max(others):.2e}",
         f"{min(others):.2e}" == "8.60e-06" and f"{max(others):.2e}" == "3.95e-03" and len(others) == 6),
        ("k160 it66 solid share exceeds intermediate share", f"{100 * S[66]['share_solid']:.1f} vs {100 * S[66]['share_intermediate']:.1f}",
         S[66]["solid_share_exceeds_intermediate"]),
        ("k160 it67 OC update identical (audit record)", S[67]["update_max_abs_diff_audit_record"], S[67]["update_max_abs_diff_audit_record"] == 0.0),
        ("k160 recomputed 2-norm errors equal the dump-run audit records (rel. 1e-6)",
         {i: S[i]["rel_err_2"] / S[i]["rel_err_2_audit_record"] - 1 for i in S}, all(close(S[i]["rel_err_2"], S[i]["rel_err_2_audit_record"], 1e-6) for i in S)),
    ]
    if printed is not None:
        c.append(("submitted Table S24: all 12 rows reproduced cell by cell", [p["row"] for p in printed if not p["match"]], all(p["match"] for p in printed)))
    return [{"check": a, "recomputed": v, "pass": bool(ok)} for a, v, ok in c]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--printed-table", type=Path)
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    rows = tolerance_rows(a.data)
    write_csv(a.out / "tolerance.csv", rows)
    snaps, pops, proxies = localization(a.data)
    write_csv(a.out / "localization.csv", snaps)
    write_csv(a.out / "localization_populations.csv", pops)
    printed = compare_printed(rows, a.printed_table) if a.printed_table else None
    (a.out / "historical_proxies.json").write_text(json.dumps({
        "not_for_the_revision": "Distances are omitted from the revised paper. These are the submitted script's proxies, "
                                "reproduced only to identify them.",
        "definition": {
            "script": "E30_dump_analysis.py lines 27-31 (copied to inputs/authors_code)",
            "element_position": "integer element indices (ex, ey) of the 320x160x160 grid, not element centres (ex+0.5, ey+0.5)",
            "support_proxy": "min(hypot(ex, ey), hypot(nx-1-ex, ey)) / ny: index distance to the element-index points (0,0) and "
                             "(nx-1,0), standing in for the support lines x=0,y=0 and x=2,y=0 (node indices 0 and nx), z ignored",
            "load_proxy": "hypot(ex - nx/2, ny-1-ey) / ny: index distance to (nx/2, ny-1), standing in for the top-centre load "
                          "strip at x=1,y=1 (node indices nx/2 and ny, strip width 0.1 ignored), z ignored",
            "unit": "divided by ny=160, i.e. a fraction of the domain depth only up to the half-element index offset; "
                    "the submitted text called them 'depth units'",
            "population_in_record": "the 100 largest |error| elements (order[:100]), not the 75 intermediate-density elements",
        },
        "values": proxies}, indent=1), encoding="utf-8")
    ck = checks(rows, snaps, pops, printed)
    (a.out / "checks.json").write_text(json.dumps({"checks": ck, "printed_table": printed,
                                                   "all_pass": all(x["pass"] for x in ck)}, indent=1, default=str), encoding="utf-8")
    for x in ck:
        print(("PASS " if x["pass"] else "FAIL ") + x["check"] + " -> " + str(x["recomputed"]))
    return 0 if all(x["pass"] for x in ck) else 1


if __name__ == "__main__":
    raise SystemExit(main())
