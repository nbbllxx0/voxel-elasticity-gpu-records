"""T31 analysis (CPU only).  Reads only the job outputs of ANALYSIS_PLAN.md section 4 and writes out/summary.json:
E1 (a)-(e) per R design, H1/H2 and the application status, S1-S4, C1-C5 for O_n192 against R_n192, the C0 work.
Every value carries the file it comes from."""
import json
import statistics
import sys
from pathlib import Path

import numpy as np

T31 = Path(__file__).resolve().parent
OUT = T31 / "out"
RUNS = OUT / "runs"
T30_WS = T31.parent / "T30" / "out" / "workspace.json"
VOL_TOL = 1e-4
PROD_TOL = 1e-5
TIGHT = 1e-8


def rel(p):
    return str(Path(p).relative_to(T31.parent.parent)).replace("\\", "/")


def load(p):
    p = Path(p)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def run_files(name):
    d = RUNS / name
    return {"dir": d, "monitor": load(d / "monitor.json"), "meta": load(d / "gpu_meta.json"),
            "history": (load(d / "history.json") or {}).get("history")}


def samples_of(mon, d):
    if mon.get("samples_file"):
        return load(d / mon["samples_file"])
    return mon.get("samples") or []


def coverage_start(samples, launched):
    """First launcher sample that holds the job's process with both counters (dedicated and shared) present."""
    for i, x in enumerate(samples):
        c = x.get("child")
        if c and c.get("ded") is not None and c.get("sh") is not None:
            return {"first_complete_sample_index": i, "first_complete_sample_number": i + 1,
                    "first_complete_sample_s_after_launch": x["t"] - launched,
                    "first_complete_sample_event": x.get("event"),
                    "dedicated_bytes_at_first_complete_sample": c["ded"],
                    "shared_bytes_at_first_complete_sample": c["sh"],
                    "earlier_samples": [{"number": k + 1, "child": samples[k].get("child")} for k in range(i)]}
    return {"first_complete_sample_index": None}


def monitor_ok(mon, meta, d):
    """(e) of the plan: no spill and no allocation failure, with the launcher's coverage complete from its first
    sample.  The launcher's first sample has no job process and its second lacks the dedicated counter, so coverage
    is complete only from the first sample holding both counters (the "go" sample, after the job's CUDA context and
    one-element probe allocation).  (e) as worded is therefore checked against that start."""
    if mon is None:
        return False, "no monitor record"
    w = mon.get("watch", {})
    alloc_fail = bool(meta and meta.get("allocation_failure"))
    cov = coverage_start(samples_of(mon, d), mon["launched_at_unix"])
    from_first = cov["first_complete_sample_index"] == 0
    no_spill = bool(mon.get("valid") and not mon.get("spilled") and w.get("covered_from_go") and
                    w.get("final_sample_checked") and not alloc_fail)
    ok = bool(no_spill and from_first)
    return ok, {"status": mon.get("status"), "valid": mon.get("valid"), "spilled": mon.get("spilled"),
                "no_spill_no_allocation_failure_over_covered_interval": no_spill,
                "coverage_from_launcher_first_sample": from_first, "coverage_start": cov,
                "covered_from_go": w.get("covered_from_go"), "final_sample_checked": w.get("final_sample_checked"),
                "shared_max_growth_bytes": w.get("shared_max_growth_bytes"),
                "child_dedicated_peak_bytes": w.get("child_dedicated_peak_bytes"),
                "max_sample_interval_s": w.get("max_sample_interval_s"), "allocation_failure": alloc_fail,
                "admission": mon.get("admission")}


def opt_record(name):
    f = run_files(name)
    m, h, mon = f["meta"], f["history"], f["monitor"]
    src = {"meta": rel(f["dir"] / "gpu_meta.json"), "history": rel(f["dir"] / "history.json"),
           "monitor": rel(f["dir"] / "monitor.json")}
    if m is None:
        return {"run": name, "present": False, "monitor_status": (mon or {}).get("status"), "sources": src}
    mok, mrec = monitor_ok(mon, m, f["dir"])
    out = {"run": name, "present": True, "completed": m.get("completed"), "outcome": m.get("outcome"),
           "error": m.get("error"), "monitor_ok": mok, "monitor": mrec, "sources": src,
           "counts": (m.get("driver") or {}).get("counts"), "host_checks_passed": m.get("host_checks", {}).get("passed"),
           "matching_state_hashes": m.get("matching_state_hashes"), "solve_failure": m.get("solve_failure"),
           "admission_in_process": m.get("admission_in_process")}
    if h:
        solves = [s for r in h for s in r["solves"]]
        if m.get("result"):
            solves += m["result"]["final_solves"]
        t_iter = [r["t_iter_s"] for r in h]
        fin_s = (m.get("result") or {}).get("final_solves") or []
        out["history_summary"] = {
            "iterations_recorded": len(h),
            "max_production_rel_true": max(s["rel_true"] for s in solves),
            "n_production_solves": len(solves),
            "all_production_solves_le_1e-5": bool(all(s["rel_true"] <= PROD_TOL for s in solves)),
            "median_iteration_s": statistics.median(t_iter),
            "median_solve_s_per_case": [statistics.median(r["solves"][k]["wall_s"] for r in h) for k in range(4)],
            "median_solve_scope": "the 300 design-iteration solves of each case (final re-solve not included)",
            # the plan's optimization boundary includes the final production re-solve: the summed work includes it
            "summed_outer_per_case": [sum(r["solves"][k]["outer"] for r in h) + (fin_s[k]["outer"] if fin_s else 0)
                                      for k in range(4)],
            "summed_inner_per_case": [sum(r["solves"][k]["inner_iters"] for r in h) +
                                      (fin_s[k]["inner_iters"] if fin_s else 0) for k in range(4)],
            "summed_outer_per_case_design_iterations_only": [sum(r["solves"][k]["outer"] for r in h) for k in range(4)],
            "summed_inner_per_case_design_iterations_only": [sum(r["solves"][k]["inner_iters"] for r in h)
                                                             for k in range(4)],
            "summed_scope": "design iterations plus the final production re-solve (the plan's optimization boundary)",
            "rejected_steps_total": sum(s.get("rejected_steps", 0) for s in solves),
            "warm_start_resets_total": sum(bool(s.get("warm_start_reset")) for s in solves)}
        last = h[-10:]
        Jw = [r["J"] for r in last]
        out["end_state_descriptive"] = {
            "note": "descriptive, outside the plan's endpoints: the stopping quantities over the last 10 iterations",
            "J_spread_rel_last10": (max(Jw) - min(Jw)) / abs(float(np.mean(Jw))),
            "max_drho_phys_last10": [r["drho_phys"] for r in last],
            "n_elem_drho_gt_0.01_last10": [r["n_elem_drho_gt_tol"] for r in last],
            "bounded_oscillation_bound": max(1, int(1.0e-6 * out["counts"]["active"])) if out["counts"] else None,
            "first_iteration_spread_le_1e-4": next((r["it"] for i, r in enumerate(h) if i >= 9 and r["it"] > 75 and
                                                    (max(x["J"] for x in h[i - 9:i + 1]) -
                                                     min(x["J"] for x in h[i - 9:i + 1])) /
                                                    abs(np.mean([x["J"] for x in h[i - 9:i + 1]])) <= 1e-4), None),
            "min_drho_phys_after_75": min(r["drho_phys"] for r in h if r["it"] > 75) if len(h) > 75 else None,
            "min_moving_after_75": min(r["n_elem_drho_gt_tol"] for r in h if r["it"] > 75) if len(h) > 75 else None,
            "J_last12": [r["J"] for r in h[-12:]],
            "J_successive_differences_alternate_in_sign_last12": bool(all(
                (h[i]["J"] - h[i - 1]["J"]) * (h[i + 1]["J"] - h[i]["J"]) < 0 for i in range(len(h) - 11, len(h) - 1))),
            "evidence_scope": "the history holds only scalars per iteration (J, c_k, volume, MND, max |drho_phys|, "
                              "the count of elements moving by more than 0.01); only the final field was saved, so "
                              "which elements moved, and whether the density field repeats, is not recorded"}
    if m.get("outcome") == "returned_design":
        r, fin = m["result"], m["final"]
        out["result"] = {"termination": r["termination"], "converged": r["converged"], "iterations": r["iterations"],
                         "J_prod": r["J"], "c_prod": r["c"], "volume_phys": r["volume_phys"],
                         "volume_abs_err": fin["volume_abs_err"], "mnd": fin["mnd"],
                         "solid_fraction_active_rho_gt_0.5": fin["solid_fraction_active"],
                         "E32_sha256": fin["E32_sha256"], "penalty": fin["penalty"], "mg_levels": r["mg_levels"]}
        t = m["timing"]
        fs_ = r["final_solves"]
        tot = dict(r["totals"])
        tot["solve_s"] += sum(s["wall_s"] for s in fs_)
        tot["setup_s"] += fs_[0]["setup_s"]
        out["cost"] = {"optimization_s": t["optimization_s"], "iterations_2_to_end_s": it2_record(t),
                       "on_iter_io_s": t["on_iter_io_s"], "driver_wall_s": r["wall_s"],
                       "totals": tot,
                       "totals_scope": "design iterations plus the final production re-solve (four solves and its "
                                       "multigrid setup), the plan's optimization boundary; the final re-solve has no "
                                       "sensitivity or OC step, and its prepare() (filter and moduli) lies inside "
                                       "optimization_s but is not timed separately",
                       "totals_design_iterations_only": r["totals"],
                       "final_resolve": {"solve_wall_s_per_case": [s["wall_s"] for s in fs_],
                                         "setup_s": fs_[0]["setup_s"], "outer_per_case": [s["outer"] for s in fs_],
                                         "inner_per_case": [s["inner_iters"] for s in fs_]},
                       "pool_peak_reserved_bytes": m["memory_boundary"]["pool_peak_reserved_bytes"],
                       "pool_peak_used_bytes": m["memory_boundary"]["pool_peak_used_bytes"],
                       "process_dedicated_peak_bytes_sampled": mrec["child_dedicated_peak_bytes"] if mrec != "no monitor record" else None,
                       "driver_peak_device_used_bytes": r["memory"]["peak_device_used_bytes"]}
        if out["counts"]:
            pp = out["cost"]["pool_peak_reserved_bytes"]
            out["cost"]["pool_bytes_per_allocated_element"] = pp / out["counts"]["allocated"]
            out["cost"]["pool_bytes_per_active_element"] = pp / out["counts"]["active"]
    return out


def audit_record(name):
    f = run_files(name)
    m, mon = f["meta"], f["monitor"]
    src = {"meta": rel(f["dir"] / "gpu_meta.json"), "monitor": rel(f["dir"] / "monitor.json")}
    if m is None:
        return {"run": name, "present": False, "monitor_status": (mon or {}).get("status"), "sources": src}
    mok, mrec = monitor_ok(mon, m, f["dir"])
    out = {"run": name, "present": True, "completed": m.get("completed"), "error": m.get("error"),
           "monitor_ok": mok, "monitor": mrec, "sources": src}
    if not m.get("completed"):
        return out
    t = m["tight"]
    out.update({"audit_valid": m["audit_valid"], "moduli_hash_match": t.get("moduli_hash_match"),
                "fixed_set_match": t["fixed_set"]["device_fixed_equals_supports_or_exterior_only"],
                "equilibrium_rel_residual_node_hoist": [c["equilibrium_rel_residual_node_hoist"] for c in t["cases"]],
                "all_equilibrium_passed": m["audit_all_equilibrium_passed"],
                "endpoints": audit_endpoints(m["endpoints"], t), "mg_setup_s": t["mg_setup_s"],
                "solver_per_case": [c["solver"] for c in t["cases"]],
                "iterations_per_case": [c["stats"].get("iters") for c in t["cases"]],
                "solve_wall_s_per_case": [c["stats"]["wall_s"] for c in t["cases"]],
                "pool_peak_reserved_bytes": t["memory"]["pool_peak_reserved_bytes"],
                "cpu_check": m.get("cpu_check")})
    out.update(tight_time(t))
    out["reactions_informational"] = reactions(t["cases"])
    return out


def it2_record(t):
    """The job's 'iterations_2_to_end_s' starts at entry to iteration 1's on_iter callback (t31_job.py:330), before
    the initial-state hashes and the first history write, not at the callback's end as its note says.  The recorded
    value is therefore iterations 2 to the end plus iteration 1's callback.  That callback is one of the callbacks
    summed in on_iter_io_s, so the plan's quantity lies in [recorded - on_iter_io_s, recorded]."""
    v = t["iterations_2_to_end_s"]
    return {"measured_from_iteration1_callback_entry_s": v,
            "plan_quantity_bounds_s": [v - t["on_iter_io_s"], v],
            "note": "measured from entry to iteration 1's on_iter callback (before the initial-state hashes and the "
                    "first history write) to run() return; the plan's 'iterations 2 to the end' starts after that "
                    "callback, whose duration is not recorded on its own but is at most on_iter_io_s (all 300 "
                    "callbacks); the same boundary was used in every OPT run"}


def audit_endpoints(ep, t):
    """The job's endpoints field 'audit_time_s_solves_plus_setup' (t31_job.py:420) holds the wider solve_and_setup_s
    interval.  Export the plan's endpoint (four solves plus the multigrid setup) under that name and the wider interval
    under its own label."""
    ep = dict(ep)
    wider = ep.pop("audit_time_s_solves_plus_setup")
    ep["audit_time_s_solves_plus_setup"] = tight_time(t)["audit_time_four_solves_plus_setup_s"]
    ep["broader_interval_s"] = wider
    ep["audit_time_note"] = ("audit_time_s_solves_plus_setup is the four solve times plus the multigrid setup (plan "
                             "section 4 AUDIT step 7); the job's gpu_meta.json field of the same name holds the wider "
                             "interval, exported here as broader_interval_s")
    return ep


def tight_time(t):
    """Plan section 4 AUDIT step 7: total audit time = the four solves plus the multigrid setup.  The job's
    solve_and_setup_s interval also holds the equilibrium checks, the reaction sums and the host transfers."""
    if not t.get("cases"):
        return {}
    plan = sum(c["stats"]["wall_s"] for c in t["cases"]) + t["mg_setup_s"]
    return {"audit_time_four_solves_plus_setup_s": plan,
            "broader_interval_s": t.get("solve_and_setup_s"),
            "broader_interval_note": "from before the multigrid setup to after the fourth case; also holds the "
                                     "node_hoist equilibrium checks, the reaction sums and the host transfers"}


def reactions(cases):
    """Applied load plus support reaction (the reaction is (K u) at the clamped DOFs with the sign of the force the
    supports exert, i.e. reaction = -(K u)_supports; the job stored (K u)_supports, so the balance is applied +
    stored).  Relative to |F_applied| (+ |M_applied| / 1 in for the couple)."""
    out = []
    for c in cases:
        r = c["reactions"]
        Fa, Ma = np.array(r["applied_F"]), np.array(r["applied_M"])
        Fs, Ms = np.array(r["reaction_F"]), np.array(r["reaction_M"])
        scale = max(np.linalg.norm(Fa), np.linalg.norm(Ma))
        out.append({"load": c["load"], "net_F": (Fa + Fs).tolist(), "net_M": (Ma + Ms).tolist(),
                    "rel_net_F": float(np.linalg.norm(Fa + Fs) / scale),
                    "rel_net_M": float(np.linalg.norm(Ma + Ms) / scale)})
    return out


def c0_record(n):
    f = run_files(f"c0_n{n}")
    m, mon = f["meta"], f["monitor"]
    c0 = load(OUT / f"c0_n{n}.json")
    if m is None:
        return {"present": False, "monitor_status": (mon or {}).get("status")}
    mok, mrec = monitor_ok(mon, m, f["dir"])
    t = m.get("tight", {})
    return {"present": True, "passed": bool(c0 and c0.get("passed")), "c0": c0["c0"] if c0 else None,
            "rel_residual_node_hoist": c0["rel_residual_node_hoist"] if c0 else None,
            "solver": c0["solver"] if c0 else None, "monitor_ok": mok, "monitor": mrec,
            "iterations": [c["stats"].get("iters") for c in t.get("cases", [])],
            "solve_wall_s": [c["stats"]["wall_s"] for c in t.get("cases", [])],
            **tight_time(t), "pool_peak_reserved_bytes": t.get("memory", {}).get(
                "pool_peak_reserved_bytes"), "fixed_set_match": t.get("fixed_set", {}).get(
                "device_fixed_equals_supports_or_exterior_only"), "cpu_check": m.get("cpu_check"),
            "reactions_informational": reactions(t["cases"]) if t.get("cases") else None,
            "sources": {"c0": rel(OUT / f"c0_n{n}.json"), "meta": rel(f["dir"] / "gpu_meta.json"),
                        "monitor": rel(f["dir"] / "monitor.json")}}


def e1(opt, aud):
    """E1 (a)-(e) for one R design."""
    if not opt.get("present") or opt.get("outcome") != "returned_design":
        return {"evaluated": False, "reason": opt.get("outcome") or opt.get("monitor_status") or "no run"}
    res = opt["result"]
    a = res["termination"] in ("max_change", "bounded_oscillation")
    b = res["volume_abs_err"] <= VOL_TOL
    c = opt["history_summary"]["all_production_solves_le_1e-5"]
    d = bool(aud.get("present") and aud.get("completed") and aud.get("audit_valid") and aud.get("all_equilibrium_passed"))
    e = bool(opt["monitor_ok"] and aud.get("monitor_ok"))
    mons = [opt.get("monitor") or {}, aud.get("monitor") or {}]
    e_spill = all(x.get("no_spill_no_allocation_failure_over_covered_interval") for x in mons)
    e_first = all(x.get("coverage_from_launcher_first_sample") for x in mons)
    return {"evaluated": True, "a_stopping_rule": a, "a_termination": res["termination"], "b_volume": b,
            "b_volume_abs_err": res["volume_abs_err"], "c_production_residuals": c,
            "c_max_production_rel_true": opt["history_summary"]["max_production_rel_true"],
            "d_audit": d, "e_no_spill_covered": e,
            "e_no_spill_no_allocation_failure_over_covered_interval": e_spill,
            "e_coverage_from_launcher_first_sample": e_first,
            "e_note": "not established as worded: in the OPT and AUDIT jobs coverage is complete from the launcher's "
                      "third sample (the first with the job process and both counters), after the job's CUDA "
                      "context and one-element probe allocation; no spill or allocation failure from there on"
                      if (e_spill and not e_first) else None,
            "passed": bool(a and b and c and d and e)}


def hypothesis(opt, aud, ev):
    """Section 6 rule for one size."""
    if not opt.get("present"):
        return "not run"
    if opt.get("outcome") == "solve_failure":
        return "contradicted (production solve failure)"
    if ev.get("evaluated") and aud.get("present") and aud.get("completed") and aud.get("audit_valid") \
            and not aud.get("all_equilibrium_passed"):
        return "contradicted (audit equilibrium check failed)"
    if ev.get("passed"):
        return "supported"
    reasons = []
    if ev.get("evaluated"):
        if not ev["a_stopping_rule"]:
            reasons.append("reached the 300-iteration guard" if ev["a_termination"] == "guard" else ev["a_termination"])
        if not ev["b_volume"]:
            reasons.append("volume")
        if not ev["c_production_residuals"]:
            reasons.append("production residual above 1e-5")
        if not ev["d_audit"]:
            reasons.append("audit invalid or missing")
        if not ev["e_no_spill_no_allocation_failure_over_covered_interval"]:
            reasons.append("spill/allocation failure")
        elif not ev["e_coverage_from_launcher_first_sample"]:
            reasons.append("coverage from the launcher's first sample not established (no spill from the third)")
    else:
        reasons.append(ev.get("reason", "no design"))
    return "inconclusive (" + "; ".join(reasons) + ")"


def c1_category(opt, aud, ev):
    if not opt.get("present"):
        return "not run"
    if opt.get("monitor", {}).get("spilled") or opt.get("monitor", {}).get("allocation_failure"):
        return "refused"
    if opt.get("outcome") == "solve_failure":
        sf = opt["solve_failure"]
        return f"solve-failure at iteration {sf['design_iteration']}, load case {sf['load_case']}"
    if opt.get("outcome") != "returned_design":
        return "no outcome (" + str(opt.get("error")) + ")"
    if ev["passed"]:
        return "completed-verified"
    if opt["result"]["termination"] == "guard":
        return "not-converged"
    return "completed-unverified"


def ratio_row(o, r):
    q = o / r if r else None
    return {"O": o, "R": r, "ratio_O_over_R": q,
            "reading": None if q is None else ("no difference measurable at single-run resolution"
                                               if 0.95 <= q <= 1.05 else "reported as measured")}


def it2_ratio(o, r):
    """C4 ratio for iterations 2 to the end: the ratio of the measured values (same boundary in both runs) and the
    range the ratio of the plan's quantity can take within the two bounds."""
    row = ratio_row(o["measured_from_iteration1_callback_entry_s"], r["measured_from_iteration1_callback_entry_s"])
    (olo, ohi), (rlo, rhi) = o["plan_quantity_bounds_s"], r["plan_quantity_bounds_s"]
    lo, hi = olo / rhi, ohi / rlo
    row["measured_boundary"] = "from entry to iteration 1's on_iter callback to run() return, in both runs"
    row["plan_quantity_ratio_bounds"] = [lo, hi]
    row["plan_quantity_reading"] = ("no difference measurable at single-run resolution" if 0.95 <= lo and hi <= 1.05
                                    else "reported as measured")
    return row


def comparison(R, O, aR, aO, fR, fO):
    out = {}
    hR, hO = R.get("matching_state_hashes") or {}, O.get("matching_state_hashes") or {}
    keys = ("initial_design_variable", "iteration1_rho_phys", "iteration1_E32")
    same = {k: (hR.get(k) is not None and hR.get(k) == hO.get(k)) for k in keys}
    out["C2_matching_state"] = {"per_hash": same, "all_identical": all(same.values()),
                                "R": {k: hR.get(k) for k in keys}, "O": {k: hO.get(k) for k in keys}}
    hr = (load(RUNS / R["run"] / "history.json") or {}).get("history") or []
    ho = (load(RUNS / O["run"] / "history.json") or {}).get("history") or []
    first = None
    for a, b in zip(hr, ho):
        if abs(b["J"] - a["J"]) / abs(a["J"]) > 1e-6:
            first = a["it"]
            break
    common = min(len(hr), len(ho))
    out["C5_path_divergence"] = {
        "first_iteration_J_rel_diff_gt_1e-6": first, "iterations_compared": common,
        "J_rel_diff_at": {str(i): abs(ho[i - 1]["J"] - hr[i - 1]["J"]) / abs(hr[i - 1]["J"])
                          for i in (1, 2, 5, 10, 15, 16, 20, 40, 41, 65, 66, 76, 100, 150, 200, 250, 300) if i <= common},
        "max_J_rel_diff_over_common_iterations": max(abs(b["J"] - a["J"]) / abs(a["J"]) for a, b in zip(hr, ho))
        if common else None}
    early = [(a["it"], abs(b["J"] - a["J"]) / abs(a["J"])) for a, b in zip(hr, ho) if a["it"] <= 75]
    if early:
        it_mx, mx = max(early, key=lambda x: x[1])
        out["C5_path_divergence"]["max_J_rel_diff_iterations_1_75"] = {"value": mx, "at_iteration": it_mx}
    if O.get("outcome") == "solve_failure":
        out["C5_path_divergence"]["failure"] = O["solve_failure"]
    both = R.get("outcome") == "returned_design" and O.get("outcome") == "returned_design"
    if not (both and out["C2_matching_state"]["all_identical"]):
        out["C3_C4"] = "not interpreted (" + ("no design from both runs" if not both else "initial states differ") + ")"
        return out
    JR, JO = aR["endpoints"]["J_tight"], aO["endpoints"]["J_tight"]
    cR, cO = aR["endpoints"]["c_tight"], aO["endpoints"]["c_tight"]
    rpR, rpO = fR["rho_phys"].astype(np.float64), fO["rho_phys"].astype(np.float64)
    des = fR["cls"].ravel() == 1
    d = np.abs(rpO[des] - rpR[des])
    out["C3_design_outcome"] = {
        "J_tight_R": JR, "J_tight_O": JO, "J_tight_rel_diff": abs(JO - JR) / JR,
        "c_tight_rel_diff_per_case": [abs(o - r) / r for o, r in zip(cO, cR)],
        "iterations": {"R": R["result"]["iterations"], "O": O["result"]["iterations"]},
        "terminations": {"R": R["result"]["termination"], "O": O["result"]["termination"]},
        "mean_abs_drho_phys_designable": float(d.mean()),
        "fraction_designable_abs_drho_phys_gt_0.5": float((d > 0.5).mean()),
        "equal_design_rule": "applies only when both runs are completed-verified; it does not apply here"
        if not (R.get("_verified") and O.get("_verified")) else
        ("equal design outcome" if abs(JO - JR) / JR <= 1e-4 else "different design outcome")}
    cR_, cO_ = R["cost"], O["cost"]
    hsR, hsO = R["history_summary"], O["history_summary"]
    out["C4_cost_ratios"] = {
        "optimization_s": ratio_row(cO_["optimization_s"], cR_["optimization_s"]),
        "iterations_2_to_end_s": it2_ratio(cO_["iterations_2_to_end_s"], cR_["iterations_2_to_end_s"]),
        "median_iteration_s": ratio_row(hsO["median_iteration_s"], hsR["median_iteration_s"]),
        "median_solve_s_per_case": [ratio_row(o, r) for o, r in zip(hsO["median_solve_s_per_case"],
                                                                     hsR["median_solve_s_per_case"])],
        "pool_peak_reserved_bytes": ratio_row(cO_["pool_peak_reserved_bytes"], cR_["pool_peak_reserved_bytes"]),
        "summed_outer_per_case": {"R": hsR["summed_outer_per_case"], "O": hsO["summed_outer_per_case"]},
        "summed_inner_per_case": {"R": hsR["summed_inner_per_case"], "O": hsO["summed_inner_per_case"]},
        "band": "[0.95, 1.05]: no difference measurable at single-run resolution",
        "interference": "shared display card; no activity-exclusion rule applied (plan section 6)"}
    return out


def main():
    ws = load(T30_WS)["model"]
    s = {"plan": "tasks/T31/ANALYSIS_PLAN.md (frozen, unchanged)", "selftest": load(OUT / "launch_selftest.json")["passed"],
         "code_hashes_copies_identical": load(T31 / "code_hashes.json")["all_copies_identical"],
         "host_checks": {n: {"passed": load(OUT / f"host_checks_{n}.json")["passed"],
                             "counts": load(OUT / f"host_checks_{n}.json")["counts"],
                             "source": rel(OUT / f"host_checks_{n}.json")} for n in (96, 192, 384)},
         "c0": {n: c0_record(n) for n in (192, 384)}, "runs": {}, "E1": {}, "S1": {}, "S2": {}}
    for nm in ("R_n192", "O_n192", "R_n384"):
        s["runs"][nm] = opt_record(nm)
    for nm in ("A_R_n192", "A_O_n192", "A_R_n384"):
        s["runs"][nm] = audit_record(nm)
    hyp = {}
    for n, key in ((192, "H1"), (384, "H2")):
        o, a = s["runs"][f"R_n{n}"], s["runs"][f"A_R_n{n}"]
        ev = e1(o, a)
        s["E1"][f"R_n{n}"] = ev
        hyp[key] = hypothesis(o, a, ev)
        o["_verified"] = bool(ev.get("passed"))
        if a.get("present") and a.get("completed"):
            mx = max(a["endpoints"]["c_rel_diff_prod_vs_tight"])
            s["S1"][f"R_n{n}"] = {"max_rel_diff_prod_vs_tight": mx, "prediction": "<= 1e-4",
                                  "holds": bool(mx <= 1e-4),
                                  "scope_note": "the plan's S1 rule is stated for R designs that pass E1; this design "
                                                "does not pass E1, so the value is reported against the prediction "
                                                "only" if not ev.get("passed") else "design passes E1"}
        if o.get("outcome") == "returned_design":
            N = o["counts"]["allocated"]
            model = ws["a_bytes_per_allocated_element"] * N + ws["b_bytes"]
            pp = o["cost"]["pool_peak_reserved_bytes"]
            s["S2"][f"R_n{n}"] = {"pool_peak_reserved_bytes": pp, "model_bytes": model, "ratio": pp / model,
                                  "holds": bool(abs(pp / model - 1) <= 0.05),
                                  "model": "254.5 B x N_alloc + 216 MB (T30 out/workspace.json)",
                                  "pool_peak_used_bytes": o["cost"]["pool_peak_used_bytes"],
                                  "ratio_used": o["cost"]["pool_peak_used_bytes"] / model}
    oO, aO = s["runs"]["O_n192"], s["runs"]["A_O_n192"]
    evO = e1(oO, aO)
    oO["_verified"] = bool(evO.get("passed"))
    s["O_n192_E1_items"] = evO
    s["C1_O_n192_category"] = c1_category(oO, aO, evO)
    s["C1_R_n192_category_same_rule"] = c1_category(s["runs"]["R_n192"], s["runs"]["A_R_n192"], s["E1"]["R_n192"])
    if oO.get("present") and aO.get("present") and aO.get("completed"):
        mx = max(aO["endpoints"]["c_rel_diff_prod_vs_tight"])
        s["S1"]["O_n192"] = {"max_rel_diff_prod_vs_tight": mx, "holds": bool(mx <= 1e-4)}
    fR = np.load(RUNS / "R_n192" / "fields.npz") if (RUNS / "R_n192" / "fields.npz").exists() else None
    fO = np.load(RUNS / "O_n192" / "fields.npz") if (RUNS / "O_n192" / "fields.npz").exists() else None
    s["comparison_O_vs_R_n192"] = comparison(s["runs"]["R_n192"], oO, s["runs"]["A_R_n192"], aO, fR, fO)
    s["hypotheses"] = hyp
    passing = [k for k, v in s["E1"].items() if v.get("passed")]
    contradicted = hyp["H1"].startswith("contradicted")
    s["application_status_R1_4"] = ("resolved (supported)" if passing else
                                    ("unresolved" if contradicted else "inconclusive"))
    s["designs_passing_E1"] = passing
    for nm in ("R_n192", "O_n192", "R_n384"):
        s["runs"][nm].pop("_verified", None)
    (OUT / "summary.json").write_text(json.dumps(s, indent=1, default=float), encoding="utf-8")
    print(json.dumps({"hypotheses": hyp, "application": s["application_status_R1_4"], "C1": s["C1_O_n192_category"],
                      "E1": s["E1"], "S1": s["S1"], "S2": s["S2"]}, indent=1, default=float))
    return 0


if __name__ == "__main__":
    sys.exit(main())
