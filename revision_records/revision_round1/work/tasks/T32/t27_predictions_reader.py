"""Data-only reader of T27's prediction outcomes (plan Section 5.2) and gate summary (CPU only, standard library).

Recomputes revision_round1/work/tasks/T27/predictions.json from T27's staged records: hou_matched.csv,
capacity.json and the records in out/ (G1 and G3 validation, the two k = 80 hook-overhead applications, the H3
Hou solves, the H4 continuations, the H5 independent checkers at k = 80, 160 and 256, and the exploratory
single-build memory runs X_MEM_*).  The decision rules are those of tasks/T27/drivers/predictions.py, copied here
line for line; only its bootstrap import (t27boot, which belongs to the unreleased implementation tree) is replaced
by paths relative to this file and a JSON writer with the same format (indent 1, the platform's line ending, as
the original was written).  No GPU and no implementation import.

usage: python -I t27_predictions_reader.py --out <dir> [--t27 <T27 folder>]
       python -I t27_predictions_reader.py --list-inputs [--t27 <T27 folder>]
The T27 folder defaults to ../T27 beside this file's folder (the tree layout).  Writes <dir>/predictions.json and
<dir>/inputs_read.json (every record the rules asked for, and whether it exists).
"""
import argparse
import csv
import json
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("--t27", default=str(Path(__file__).resolve().parents[1] / "T27"))
ap.add_argument("--out")
ap.add_argument("--list-inputs", action="store_true")
A = ap.parse_args()
T = Path(A.t27)
RESULTS = T / "out"
ASKED = []

KS = (80, 160, 256)
# Endpoints read from the independent checker at k = 160 rest on its replacement run (the first run met the spill
# criterion; the repeat lay outside the plan's repeat conditions, DEVIATIONS.md D9).  Under plan Section 1 they are
# exploratory: listed, never used in a confirmatory decision.
CHECKER_EXPLORATORY = {160}
TIMING_NOTE = ("All application timings (every k, every operator) are used as recorded under G4: none exceeded 5 %, "
               "the k = 160 stencil timings carry the 1-5 % flag. G4 cannot establish foreign activity during any "
               "application timing, which lasts far less than its 10 s sampling interval (D6); this caveat applies "
               "equally to P4 and P5a and to every k. The k = 160 stencil timings are also slower per element than at "
               "k = 256, cause not established (D11).")


def write_json(path, obj):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1), encoding="utf-8")


def f(x):
    return None if x in (None, "", "None") else float(x)


def rows():
    ASKED.append("hou_matched.csv")
    with open(T / "hou_matched.csv", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def get(R, k, path, wl):
    for r in R:
        if int(r["k"]) == k and r["path"] == path and r["workload"].startswith(wl):
            return r
    return None


def rec(name):
    p = RESULTS / f"{name}.json"
    ASKED.append(f"out/{name}.json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def timing_ok(r):
    return r is not None and r.get("timing_flag") != "excluded" and r.get("spilled") != "True"


def main():
    R = rows()
    ASKED.append("capacity.json")
    cap = json.loads((T / "capacity.json").read_text(encoding="utf-8"))
    out = {"gates": {}, "predictions": {}}
    g1 = rec("V_G1_static"); cg = rec("V_G1_cg16"); g3 = rec("V_G3_k16")
    out["gates"]["G1"] = {"pass": bool(g1 and g1["pass_static"] and cg and cg["pass"]),
                          "sources": ["tasks/T27/out/V_G1_static.json", "tasks/T27/out/V_G1_cg16.json"]}
    out["gates"]["G3"] = {"pass": bool(g3 and g3["pass"]), "relative_difference": g3 and g3["relative_difference"],
                          "source": "tasks/T27/out/V_G3_k16.json"}
    g2 = {}
    for k in KS:
        h5 = rec(f"H5_check_k{k}")
        if h5 is None:
            g2[k] = None; continue
        s = h5.get("G2_system") or {}
        g2[k] = {"pass": bool(h5.get("G2_dR_pass") and s.get("fixed_sets_identical") and s.get("load_identical")
                              and s.get("their_initial_iterate_zero")),
                 "d_R": {kk: v for kk, v in h5["G2_actions"].items() if kk.startswith("d_R")},
                 "d_R_status": "exploratory (replacement checker, D9)" if k in CHECKER_EXPLORATORY else "confirmatory",
                 "evaluated": "after H3-H4 (in the H5 checker), not immediately after H2 as planned (D13)",
                 "source": f"tasks/T27/out/H5_check_k{k}.json"}
    out["gates"]["G2"] = g2
    g2c = {k: (v if k not in CHECKER_EXPLORATORY else None) for k, v in g2.items()}     # confirmatory gate evidence
    hook = rec("H2_apply_k80_hou_cg32"), rec("H2_apply_k80_stencil32_rep")
    out["gates"]["G4_hook_overhead"] = {p: (d or {}).get("hook_overhead_rel") for p, d in
                                        zip(("hou_cg32", "stencil32_rep"), hook)}
    P = out["predictions"]
    # P1
    va = {k: f((get(R, k, "hou_cg32", "state") or {}).get("independent_rel_true_native")) for k in KS}
    v = {k: (None if k in CHECKER_EXPLORATORY else x) for k, x in va.items()}
    have = {k: x for k, x in v.items() if x is not None}
    h4 = {k: next((c.get("rel_true") for c in (rec(f"H4_cont_k{k}") or {}).get("checkpoints", [])
                   if c.get("native_test_first_holds")), None) for k in KS}
    # plan 5.2: the denominator is every k with a completed Hou solve (operator note of 2026-11-23, item 2): k = 160
    # has a completed solve but no confirmatory independent residual, so P1 is unresolved there
    solved = [k for k in KS if ((rec(f"H3_solve_k{k}_hou_cg32") or {}).get("outcome_class") == 8)]
    missing = [k for k in solved if v[k] is None]
    P["P1"] = {"values": v, "outcome": "inconclusive (no Hou solve)" if not solved else
               "contradiction" if any(x <= 1e-5 for x in have.values()) else
               ("inconclusive (unresolved: > 1e-5 at k = %s; no confirmatory independent residual at k = %s, which "
                "has a completed Hou solve)" % (", ".join(str(k) for k in have), ", ".join(str(k) for k in missing))
                if missing else "support"),
               "k_with_completed_hou_solve": solved,
               "k_without_confirmatory_data": missing,
               "exploratory_values": {k: va[k] for k in CHECKER_EXPLORATORY},
               "in_process_continuation_value_at_native_stop": h4,
               "note": "the criterion covers every k with a completed Hou solve, k = 160 included. The k = 160 checker "
                       "value is exploratory (D9) and agrees (> 1e-5); the H4 in-process FP64 residual of the "
                       "continuation iterate at the native-stop iteration is a separate measurement, listed beside it"}
    # P2
    v = {k: (get(R, k, "hou_cg32", "state") or {}).get("attained_1e-5") for k in KS}
    sm = {k: f((get(R, k, "hou_cg32", "state") or {}).get("smallest_true_residual")) for k in KS}
    have = {k: x for k, x in v.items() if x not in (None, "")}
    P["P2"] = {"attained": v, "smallest_true_residual": sm,
               "smallest_at_iteration": {k: (get(R, k, "hou_cg32", "state") or {}).get("smallest_true_residual_iteration") for k in KS},
               "outcome": "inconclusive" if not have else
               "support" if all(x == "False" for x in have.values()) else "contradiction",
               "k_without_data": [k for k in KS if v[k] in (None, "")],
               "n_checkpoints": {k: (get(R, k, "hou_cg32", "state") or {}).get("n_checkpoints") for k in KS},
               "recursive_residual_at_native_stop": {k: f((get(R, k, "hou_cg32", "state") or {}).get(
                   "recursive_rel_residual_native")) for k in KS},
               "recursive_residual_at_10000": {k: f((get(R, k, "hou_cg32", "state") or {}).get(
                   "recursive_rel_residual_10000")) for k in KS},
               "recursive_note": "their recursive FP32 residual ||r_m|| / ||r_0|| from the H4 continuation (the quantity "
                                 "of their stopping test), beside the FP64 true residual of the same iterates",
               "note": "true residuals tested at the plan's checkpoints only (every 50 iterations at k = 80, 160; every "
                       "250 at k = 256; plus the native-stop iterate); iterates between checkpoints were not tested. "
                       "k = 80, 160 in-process (H4); k = 256 snapshots read by the H5 checker"}
    # P3a
    v = {}
    for k in KS:
        h = get(R, k, "hou_cg32", "state"); m = get(R, k, "mg64_rep", "state")
        if h and m and f(h["solve_median_s"]) and f(m["solve_median_s"]) and timing_ok(h) and timing_ok(m) and (g2c.get(k) or {}).get("pass"):
            v[k] = {"ratio": f(h["solve_median_s"]) / (f(m["setup_b_s"]) + f(m["solve_median_s"])),
                    "hou_solve_s": f(h["solve_median_s"]), "mg64_rep_setup_b_s": f(m["setup_b_s"]),
                    "mg64_rep_solve_s": f(m["solve_median_s"]),
                    "hou_independent_rel_true": f(h["independent_rel_true_native"]),
                    "mg64_rep_independent_rel_true": f(m["independent_rel_true_native"])}
    vx = {}
    for k in CHECKER_EXPLORATORY:
        h = get(R, k, "hou_cg32", "state"); m = get(R, k, "mg64_rep", "state")
        if h and m and f(h["solve_median_s"]) and f(m["solve_median_s"]):
            vx[k] = {"ratio": f(h["solve_median_s"]) / (f(m["setup_b_s"]) + f(m["solve_median_s"])),
                     "hou_independent_rel_true": f(h["independent_rel_true_native"]),
                     "mg64_rep_independent_rel_true": f(m["independent_rel_true_native"])}
    P["P3a"] = {"values": v, "outcome": "inconclusive" if not v else
                "support" if all(x["ratio"] > 1 for x in v.values()) else "contradiction",
                "note": "elapsed-time ratio at unequal accuracy unless both attained 1e-5; the denominator uses our "
                        "setup (b), whose timing boundary is the planned one (Hou's setup timings are not used)",
                "k_without_confirmatory_data": [k for k in KS if k not in v],
                "exploratory_values": vx,
                "exploratory_note": "k = 160: G2 d_R and the accuracies come from the replacement checker (D9)"}
    # P3b
    v = {}
    for k in KS:
        h = get(R, k, "hou_cg32", "state"); m = get(R, k, "mg64_rep", "state")
        if h and h.get("attained_1e-5") == "True" and f(h.get("time_to_1e-5_s")) and m:
            v[k] = f(h["time_to_1e-5_s"]) / (f(m["setup_b_s"]) + f(m["solve_median_s"]))
    P["P3b"] = {"values": v, "outcome": "inconclusive (no common-accuracy time for Hou)" if not v else
                "support" if all(x > 1 for x in v.values()) else "contradiction"}
    # P4 (operator note of 2026-11-23, item 1): a k whose G2 action gate rests on the exploratory replacement checker
    # gives an exploratory value only; the confirmatory decision uses the k with a confirmatory G2 pass
    v, vx = {}, {}
    for k in KS:
        h = get(R, k, "hou_cg32", "application"); s = get(R, k, "stencil32_rep", "application")
        if h and s and f(h["apply_median_s"]) and f(s["apply_median_s"]) and timing_ok(h) and timing_ok(s):
            e = {"ratio": f(h["apply_median_s"]) / f(s["apply_median_s"]),
                 "ratio_iqr_bounds": [f(h["apply_iqr_lo_s"]) / f(s["apply_iqr_hi_s"]),
                                      f(h["apply_iqr_hi_s"]) / f(s["apply_iqr_lo_s"])]}
            if (g2c.get(k) or {}).get("pass"):
                v[k] = e
            elif k in CHECKER_EXPLORATORY:
                vx[k] = e
    g2fail = any(g2c.get(k) is not None and not g2c[k]["pass"] for k in KS)
    miss = [k for k in KS if k not in v]
    P["P4"] = {"values": v, "exploratory_values": vx, "k_without_confirmatory_data": miss,
               "outcome": "inconclusive (G2 failure)" if g2fail else
               "inconclusive" if not v else
               "contradiction" if any(x["ratio"] < 10 for x in v.values()) else
               "support" if not miss and all(x["ratio"] >= 100 for x in v.values()) else
               ("inconclusive (unresolved: >= 100 at k = %s; the G2 action gate at k = %s is exploratory, so its "
                "ratio is exploratory)" % (", ".join(str(k) for k in v), ", ".join(str(k) for k in miss))
                if miss and all(x["ratio"] >= 100 for x in v.values()) else
                "inconclusive (a k between the support and contradiction thresholds)"),
               "note": "the support criterion needs all three k. At k = 160 the G2 action gate (d_R) comes from the "
                       "exploratory replacement checker (D9), so the k = 160 ratio is exploratory; it also lies "
                       "between the support and contradiction thresholds (D12). " + TIMING_NOTE}
    # P5a: the same system-identity gate as P3a (operator note of 2026-11-23, item 1); support needs every k
    v, vx, outc = {}, {}, []
    for k in KS:
        o = get(R, k, "stencil32_orig", "application"); s = get(R, k, "stencil32_rep", "application")
        if o and s and f(o["apply_median_s"]) and timing_ok(o) and timing_ok(s):
            rr = f(s["apply_median_s"]) / f(o["apply_median_s"])
            lo = f(s["apply_iqr_lo_s"]) / f(o["apply_iqr_hi_s"]); hi = f(s["apply_iqr_hi_s"]) / f(o["apply_iqr_lo_s"])
            e = {"ratio": rr, "ratio_iqr_bounds": [lo, hi]}
            if (g2c.get(k) or {}).get("pass"):
                v[k] = e
                outc.append("support" if rr <= 1.15 else "inconclusive" if lo <= 1.15 else "contradiction")
            elif k in CHECKER_EXPLORATORY:
                vx[k] = e
    miss = [k for k in KS if k not in v]
    P["P5a"] = {"values": v, "exploratory_values": vx, "k_without_confirmatory_data": miss,
                "outcome": "inconclusive" if not outc else "contradiction" if "contradiction" in outc
                else "inconclusive" if "inconclusive" in outc else
                ("inconclusive (unresolved: <= 1.15 at k = %s; no confirmatory G2 action gate at k = %s, where the "
                 "first checker run spilled and its replacement is exploratory)" % (
                     ", ".join(str(k) for k in v), ", ".join(str(k) for k in miss)) if miss else "support"),
                "note": "plan 5.2 requires <= 1.15 at every k. The system-identity gate is applied as in P3a; at k = 160 "
                        "it rests on the exploratory replacement checker (D9), so the k = 160 ratio is exploratory "
                        "(listed). Same timing records and standard as P4. " + TIMING_NOTE}
    # P5b: the same system-identity gate as P3a and P5a (D23): a k whose G2 action check rests on the exploratory
    # replacement checker gives an exploratory ratio only
    v, vx, outc = {}, {}, []
    for k in KS:
        for sv in ("mg64", "mgir"):
            o = get(R, k, f"{sv}_orig", "state"); s = get(R, k, f"{sv}_rep", "state")
            if o and s and f(o["solve_median_s"]) and f(s["solve_median_s"]) and timing_ok(o) and timing_ok(s) and f(o.get("solve_iqr_lo_s")):
                rr = f(s["solve_median_s"]) / f(o["solve_median_s"])
                overlap = not (f(s["solve_iqr_lo_s"]) > f(o["solve_iqr_hi_s"]) or f(s["solve_iqr_hi_s"]) < f(o["solve_iqr_lo_s"]))
                e = {"ratio": rr, "iqrs_overlap": overlap,
                     "iterations_rep": s["native_iterations"], "iterations_orig": o["native_iterations"]}
                if (g2c.get(k) or {}).get("pass"):
                    v[f"{k}_{sv}"] = e
                    outc.append("support" if 0.85 <= rr <= 1.15 else "inconclusive" if overlap else "contradiction")
                elif k in CHECKER_EXPLORATORY:
                    vx[f"{k}_{sv}"] = e
    P["P5b"] = {"values": v, "exploratory_values": vx,
                "outcome": "inconclusive" if not outc else "contradiction" if "contradiction" in outc
                else "inconclusive" if "inconclusive" in outc else "support",
                "band": [0.85, 1.15],
                "note": "ratio = repaired / original solve time (medians). The contradiction is decided by the k = 80 "
                        "mgir ratio, which lies far below the band with disjoint IQRs (the original-stencil IR needed "
                        "more outer steps). The confirmatory mg64 ratios (k = 80, 256) lie inside the +/-15 % band. The "
                        "k = 160 mg64 ratio is exploratory: its action check comes from the exploratory replacement "
                        "checker (D9), outside the system-identity gate, which is applied as in P3a and P5a. No mgir "
                        "ratio exists at k = 160 and 256, where the original-stencil IR breaks down (P8). The band "
                        "tests equal cost within +/-15 %; it is not a statement that the repair costs nothing."}
    # P6
    v = {}
    for k in KS:
        h = get(R, k, "hou_cg32", "state")
        if not h or not f(h.get("process_dedicated_peak_bytes")) or h.get("spilled") == "True":
            continue
        e = {"hou_cg32": f(h["process_dedicated_peak_bytes"])}
        for p in ("mg64_rep", "mgir_rep"):
            m = get(R, k, p, "state")
            if m and f(m.get("process_dedicated_peak_bytes")):
                e[p] = f(m["process_dedicated_peak_bytes"])
        v[k] = e
    res = [all(e[p] < e["hou_cg32"] for p in e if p != "hou_cg32") for e in v.values()]
    P["P6"] = {"recorded_process_peaks_bytes": v,
               "recorded_ranking": "ours lower at every k" if v and all(res) else "ours higher at some k" if v else None,
               "outcome": "inconclusive (no Hou solve)" if not v else
               "inconclusive (the recorded process peaks retain workspaces of two builds, D14)",
               "note": "The recorded values are process-life peaks as defined, but they do not measure one solve: in our "
                       "H3 processes the timing wrapper kept the first build's preconditioner and multigrid hierarchy "
                       "alive while the history pass built a second one (plus the history buffer, 8 bytes per DOF); in "
                       "Hou's H3 process the driver kept a survivor index while their CG built its own. Subtracting the "
                       "history buffer does not recover a single-solve value. Single-build, single-solve peaks were "
                       "re-measured as EXPLORATORY runs (out/X_MEM_*.json, hou_exploratory.csv).",
               "exploratory_single_build": {
                   k: {p: ({"pool_used_peak_bytes": d["pool"]["pool_used_peak_bytes"],
                            "pool_reserved_peak_bytes": d["pool"]["pool_reserved_peak_bytes"],
                            "process_dedicated_peak_bytes": d["process_dedicated"]["dedicated_peak_bytes"],
                            "source": f"tasks/T27/out/X_MEM_k{k}_{p}.json"}
                           if (d := rec(f"X_MEM_k{k}_{p}")) and (not d.get("admission_rule_2026_11_23") or
                                                                (d.get("spill_watcher") or {}).get("covered") is True)
                           else "missing: the live stop-on-spill watcher did not cover the run (D21, D22)" if d else
                           ("missing: no single-build peak (mgir_orig breaks down at this k, class 5)"
                            if p == "mgir_orig" else "missing"))
                       for p in ("hou_cg32", "mg64_orig", "mg64_rep", "mgir_orig", "mgir_rep")} for k in KS},
               "exploratory_note": "EXPLORATORY, never a P6 decision. mgir_orig at k = 80 was added after the operator "
                                   "note of 2026-11-23 (item 7) in one guarded run (D20); that run was repeated with the revised live "
                                   "stop-on-spill watcher, which checks complete samples only and a final sample "
                                   "after the job (D21); it was repeated again after the watcher was made to take its "
                                   "baseline from its own measured sample and to require at most 3 s between checked "
                                   "samples (D22). The three runs agree in pool used, pool reserved and process-dedicated "
                                   "peaks; their device-wide peaks above baseline are given in hou_exploratory.csv "
                                   "(D23). The watcher's coverage runs from its first sampler baseline onward, not "
                                   "over the whole process."}
    # P7
    v, vx = {}, {}
    for k in KS:
        h5 = rec(f"H5_check_k{k}")
        if h5 and "d_S_stencil32_rep" in h5["G2_actions"] and k in CHECKER_EXPLORATORY:
            vx[k] = {"d_S_rep": h5["G2_actions"]["d_S_stencil32_rep"], "d_S_orig": h5["G2_actions"]["d_S_stencil32_orig"],
                     "d_S_hou": h5["G2_actions"].get("d_S_hou_cg32")}
        elif h5 and "d_S_stencil32_rep" in h5["G2_actions"]:
            v[k] = {"d_S_rep": h5["G2_actions"]["d_S_stencil32_rep"], "d_S_orig": h5["G2_actions"]["d_S_stencil32_orig"],
                    "d_S_hou": h5["G2_actions"].get("d_S_hou_cg32")}
    # plan 5.2: support requires d_S(rep) < d_S(orig) at every k (no "with data" qualifier); a contradiction at any
    # confirmatory k decides on its own, a support needs all three k confirmatory
    missing = [k for k in KS if k not in v]
    P["P7"] = {"values": v, "outcome": "inconclusive (G2 failure)" if g2fail else "inconclusive" if not v else
               "contradiction" if any(x["d_S_rep"] >= x["d_S_orig"] for x in v.values()) else
               ("inconclusive (unresolved: d_S(rep) < d_S(orig) at k = %s; no confirmatory d_S at k = %s)"
                % (", ".join(str(k) for k in v), ", ".join(str(k) for k in missing)) if missing else "support"),
               "k_without_confirmatory_data": missing, "exploratory_values": vx,
               "note": "the support criterion requires every k; the k = 160 d_S comes from the replacement checker "
                       "(exploratory, D9). The exploratory k = 160 values agree with the two confirmatory k."}
    # P8
    v = {}
    for k in KS:
        for p in ("mg64_orig", "mg64_rep", "mgir_orig", "mgir_rep"):
            r = get(R, k, p, "state")
            v[f"{k}_{p}"] = None if r is None else r["outcome_class"]
    cl = [x for x in v.values() if x not in (None, "", "1")]
    P["P8"] = {"classes": v, "outcome": "inconclusive" if not cl else
               "contradiction" if "5" in cl else "support" if all(x == "9" for x in v.values()) else "not supported",
               "note": "the class-5 outcomes (mgir_orig, k = 160 and 256) come from the solve processes, not from the "
                       "checker, and decide the contradiction. At k = 160, mg64_orig, mg64_rep and mgir_rep have no "
                       "confirmatory class (blank): their in-process acceptance stands, but the independent "
                       "confirmation that class 9 requires comes only from the exploratory replacement checker (D9)"}
    # capacity predictions
    E = {e["name"]: e for e in cap["entries"]}

    def cl_of(n):
        return (E.get(n) or {}).get("class")
    c = cl_of("C2_mg32_rec_k384")
    P["C-A"] = {"class": c, "outcome": "support" if c == 8 and E["C2_mg32_rec_k384"].get("design_file") else
                "contradiction" if c in (2, 3, 4, 5, 7) else "inconclusive"}
    c = cl_of("C4_mg64_k352")
    P["C-B"] = {"class": c, "outcome": "support" if c == 9 else "contradiction" if c in (3, 4, 5, 7) else
                "inconclusive (by prediction only)" if c == 2 else "inconclusive"}
    c = cl_of("C5_mg_ir_k416")
    P["C-C"] = {"class": c, "outcome": "support" if c == 9 else "contradiction" if c in (3, 4, 5, 7) else
                "inconclusive (by prediction only)" if c == 2 else "inconclusive (not run)"}
    return out


def inputs():
    """The records the rules ask for, in order of first use, with their existence."""
    seen = []
    for n in ASKED:
        if n not in seen:
            seen.append(n)
    return [{"path": n, "exists": (T / n).is_file()} for n in seen]


if __name__ == "__main__":
    res = main()
    if A.list_inputs:
        print(json.dumps(inputs(), indent=1))
    else:
        if not A.out:
            ap.error("--out <dir> is required")
        write_json(Path(A.out) / "predictions.json", res)
        (Path(A.out) / "inputs_read.json").write_text(json.dumps(inputs(), indent=1), encoding="utf-8")
        for kk, vv in res["predictions"].items():
            print(kk, vv["outcome"])
