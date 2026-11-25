"""Descriptive figures quoted in REPORT.md that are not single cells of endpoints.json / verdicts.json (CPU only).
Reads out/pair.csv, out/pair_AAprime.csv, out/endpoints.json and the three monitor records; writes
out/course_summary.json.  Exploratory/descriptive only: no verdict depends on it."""
import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent / "out"


def rows(name):
    with open(OUT / name, encoding="utf-8") as f:
        return [{k: (float(v) if v not in ("", "saved", "P_prev") else v) for k, v in r.items()} for r in csv.DictReader(f)]


def main():
    p, f = rows("pair.csv"), rows("pair_AAprime.csv")
    ep = json.loads((OUT / "endpoints.json").read_text(encoding="utf-8"))
    S = int(p[-1]["it"])
    D = {int(r["it"]): r["D"] for r in p}
    F = {int(r["it"]): r["D"] for r in f}
    ratio = {i: D[i] / F[i] for i in D if F.get(i)}
    x = max(p, key=lambda r: r["X"])
    m = max(p, key=lambda r: r["M"])
    dmin = min(p, key=lambda r: r["D"])
    dc = max(p, key=lambda r: abs(r["dc_rel_preupdate"]))
    first_M1 = next((int(r["it"]) for r in p if r["M"] >= 0.5), None)
    out = {
        "S": S,
        "D_min": {"it": int(dmin["it"]), "D": dmin["D"]},
        "D_window_68_S": {"min": min(D[i] for i in range(68, S + 1)), "max": max(D[i] for i in range(68, S + 1))},
        "D_window_71_S": {"min": min(D[i] for i in range(71, S + 1)), "max": max(D[i] for i in range(71, S + 1))},
        "D_phase_41_65_from_44": {"min": min(D[i] for i in range(44, 66)), "max": max(D[i] for i in range(44, 66))},
        "X_max": {"it": int(x["it"]), "X": int(x["X"])},
        "X_total_iterations_with_crossings": sum(1 for r in p if r["X"] > 0),
        "M_max": {"it": int(m["it"]), "M": m["M"]},
        "first_it_M_ge_0.5": first_M1,
        "dc_rel_preupdate_max_abs": {"it": int(dc["it"]), "value": dc["dc_rel_preupdate"]},
        "dc_rel_preupdate_its_73_S": {"min": min(r["dc_rel_preupdate"] for r in p if r["it"] >= 73),
                                      "max": max(r["dc_rel_preupdate"] for r in p if r["it"] >= 73)},
        "n_diff_it1": int(p[0]["n_diff"]),
        "floor": {"first_it_nonzero": ep["E6"]["first_it_F_nonzero"], "F_max": max(F.values()),
                  "F_max_it": max(F, key=F.get), "X_AAp_max": int(max(r["X"] for r in f)),
                  "krylov_counts_equal_all_its": all(r["krylov_ref"] == r["krylov_other"] for r in f),
                  "D_over_F_min_from_first_nonzero": min(ratio.values()) if ratio else None,
                  "D_over_F_min_it": min(ratio, key=ratio.get) if ratio else None,
                  "its_with_D_le_10F": [i for i in ratio if D[i] <= 10 * F[i]]},
        "krylov_B_minus_A_negative_its": [int(r["it"]) for r in p if r["krylov_other"] < r["krylov_ref"]],
    }
    mon = {}
    for run in ("A", "B", "Aprime"):
        m = json.loads((OUT / "runs" / run / "monitor.json").read_text(encoding="utf-8"))
        w = m["watch"]
        mon[run] = {"status": m["status"], "valid": m["valid"], "n_samples": w["n_samples"],
                    "shared_max_growth_bytes": w["shared_max_growth_bytes"],
                    "child_dedicated_peak_bytes": w["child_dedicated_peak_bytes"], "wall_s": w["wall_s"],
                    "admission_free_bytes": m["admission"]["nvidia_smi_free_bytes"],
                    "others_dedicated_bytes": m["admission"]["others_dedicated_bytes"]}
    out["monitors"] = mon
    (OUT / "course_summary.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
