"""Panel labels of the design figure from the numerical records (data only; draws nothing).

Each panel's label is computed from the record of the run whose final field the panel shows: the number of
elements n_elem and the physical compliance 2 k c, where c is the record's compliance (normalized code units, the
final state solve on the run's own final FP32 physical field) and k the number of elements per unit length (grid
2k x k x k on the domain 2 x 1 x 1).  With reference element edge 2 and physical edge 1/k, K_phys = K_code / (2k)
for the same loads, so C_phys = 2 k c.

Input: a panel mapping (JSON) listing per panel the record path, relative to a root folder.  Output: a JSON list of
labels, one per panel, with the numbers they show.

usage: python t25_labels.py <panel_mapping.json> <root> <out.json> [submitted|revised]
"""
import json
import sys
from pathlib import Path

SOLVER_NOTE = {"mg64": "FP64 PCG + FP32 V-cycle", "mg_ir": "iterative refinement"}


def physical_compliance(rec):
    return 2 * rec["k"] * rec["compliance"]


def label(rec, largest=False):
    n = rec["n_elem"] / 1e6
    C = physical_compliance(rec)
    if largest:
        return (f"{rec['problem']}, {n:.1f}M elements\n"
                f"({SOLVER_NOTE[rec['config']['solver']]}) · 2kc = {C:.4g}")
    return f"{n:.1f}M elements · 2kc = {C:.4g}"


def labels(mapping, root, side):
    out = []
    panels = mapping["panels"]
    for p in panels:
        path = Path(root) / p[side]["record"]
        rec = json.loads(path.read_text(encoding="utf-8"))
        out.append({"panel": p["panel"], "position": p["position"], "record": p[side]["record"],
                    "problem": rec["problem"], "k": rec["k"], "n_elem": rec["n_elem"],
                    "solver": rec["config"]["solver"], "op32": rec["config"]["op32"],
                    "compliance_c": rec["compliance"], "physical_compliance_2kc": physical_compliance(rec),
                    "label": label(rec, largest=p["position"] == "c")})
    return out


def main():
    mapping = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    side = sys.argv[4] if len(sys.argv) > 4 else "revised"
    res = labels(mapping, sys.argv[2], side)
    Path(sys.argv[3]).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    for r in res:
        print(r["panel"], r["label"].replace("\n", " "))


if __name__ == "__main__":
    main()
