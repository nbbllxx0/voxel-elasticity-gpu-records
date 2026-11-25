"""Pixel comparison of the embedded design renderings (CPU only; data, draws nothing).

The design panels are embedded in the PDFs as raster images in panel order.  Compares
  (1) the fallback re-render (original fields, t25_fig_designs.py submitted) with the submitted F9_designs.pdf:
      does the copied processing reproduce the submitted surfaces?
  (2) the revised figure (difference-form fields) with the fallback re-render: how far the repaired surfaces differ
      visibly from the original ones under identical processing.
Writes out/figure/image_compare.json.
"""
import json
from pathlib import Path

import fitz
import numpy as np

T25 = Path(__file__).resolve().parent
PROJ = T25.parents[3]
FIG = T25 / "out" / "figure"


def images(pdf):
    doc = fitz.open(pdf)
    out = []
    for xref, smask, *_ in doc[0].get_images(full=True):
        pix = fitz.Pixmap(doc, xref)
        a = np.frombuffer(pix.samples, np.uint8).reshape(pix.height, pix.width, pix.n).astype(np.int16)
        if smask:
            m = fitz.Pixmap(doc, smask)
            alpha = np.frombuffer(m.samples, np.uint8).reshape(m.height, m.width, 1).astype(np.int16)
            a = np.concatenate([a[..., :3], alpha], axis=2)
        out.append(a)
    return out


def compare(a_pdf, b_pdf):
    A, B = images(a_pdf), images(b_pdf)
    res = {"n_images": [len(A), len(B)], "panels": []}
    for i, (a, b) in enumerate(zip(A, B)):
        if a.shape != b.shape:
            res["panels"].append({"panel": i + 1, "shape": [list(a.shape), list(b.shape)], "comparable": False})
            continue
        d = np.abs(a - b).max(axis=2)
        res["panels"].append({"panel": i + 1, "shape": list(a.shape), "identical": bool(d.max() == 0),
                              "max_abs_8bit": int(d.max()), "frac_pixels_diff_gt_0": float((d > 0).mean()),
                              "frac_pixels_diff_gt_16": float((d > 16).mean()),
                              "n_pixels_diff_gt_16": int((d > 16).sum())})
    return res


def main():
    out = {"fallback_vs_submitted": compare(FIG / "F4_designs_submitted.pdf",
                                            PROJ / "manuscript" / "fead1.3" / "figures" / "F9_designs.pdf"),
           "revised_vs_fallback": compare(FIG / "F4_designs_revised.pdf", FIG / "F4_designs_submitted.pdf"),
           "note": "8-bit RGBA per embedded image; panel numbers follow the embedding order, which is the drawing "
                   "order 1-7 (k = 160 row, k = 320 row, panel c)"}
    (FIG / "image_compare.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    for k in ("fallback_vs_submitted", "revised_vs_fallback"):
        print(k, out[k]["n_images"])
        for p in out[k]["panels"]:
            print("  ", p)


if __name__ == "__main__":
    main()
