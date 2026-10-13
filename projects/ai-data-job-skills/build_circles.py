#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib>=3.8", "matplotlib-venn>=1.1", "pandas>=2.2", "scipy>=1.11", "numpy>=1.26"]
# ///
"""The 2026 circles: what ads ask for together, and which title owns each region.

Circle membership is not chosen here — it comes from circles.py, which clusters
the tracked skills by how often employers ask for them in the same ad. This
script draws the result and writes every number it shows to
data/circles-2026.json, which build_stats.py turns into page variables, so the
figure and the prose cannot disagree."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib_venn import venn3, venn3_circles

import circles as C
from palette import BLUE, VERMILLION, GREEN, INK, INK_MUTED

HERE = Path(__file__).resolve().parent
df = pd.read_csv(HERE / "data" / "ai-data-job-skills.csv")
N = len(df)
m = C.masks(df)
E, D, I = m["Engineering, deployment & AI"], m["Data platform"], m["Statistics & inference"]
G = m["_ground"]

REGIONS = {                      # venn3 subset keys: 1=E, 2=D, 4=I
    "100": E & ~D & ~I, "010": ~E & D & ~I, "001": ~E & ~D & I,
    "110": E & D & ~I,  "101": E & ~D & I,  "011": ~E & D & I,
    "111": E & D & I,
}
pct = lambda s: round(100 * s.mean())
dominant = lambda s: df.family[s].value_counts().index[0] if s.sum() else "—"
dom_pct = lambda s: round(100 * df.family[s].value_counts().iloc[0] / s.sum()) if s.sum() else 0

out = {
    "_comment": ("The 2026 circles, drawn from the published CSV. Circle membership comes from "
                 "clustering the tracked skills by co-occurrence (circles.py), not from hand "
                 "grouping. Regenerate with build_circles.py; build_stats.py reads this file so "
                 "the page's numbers and the figure are the same numbers."),
    "_generated": __import__("datetime").date.today().isoformat(),
    "n_skills_eng": len(C.circles(df)["Engineering, deployment & AI"]),
    "n_skills_data": len(C.circles(df)["Data platform"]),
    "n_skills_inference": len(C.circles(df)["Statistics & inference"]),
    "n_skills_ground": len(C.circles(df)["_ground"]),
    "pct_eng": pct(E), "pct_data": pct(D), "pct_inference": pct(I), "pct_ground": pct(G),
    "pct_centre": pct(REGIONS["111"]),
    "centre_title": dominant(REGIONS["111"]), "centre_title_pct": dom_pct(REGIONS["111"]),
    "pct_eng_only": pct(REGIONS["100"]),
    "eng_only_title": dominant(REGIONS["100"]), "eng_only_title_pct": dom_pct(REGIONS["100"]),
    "pct_eng_data": pct(REGIONS["110"]),
    "eng_data_title": dominant(REGIONS["110"]), "eng_data_title_pct": dom_pct(REGIONS["110"]),
    "pct_eng_inference": pct(REGIONS["101"]),
    "eng_inference_title": dominant(REGIONS["101"]), "eng_inference_title_pct": dom_pct(REGIONS["101"]),
    "pct_data_inference": pct(REGIONS["011"]),
    "data_inference_title": dominant(REGIONS["011"]), "data_inference_title_pct": dom_pct(REGIONS["011"]),
    "pct_none": pct(~E & ~D & ~I),
}
# the share of DATA SCIENTIST ads that sit in the centre, and of the centre that is not them
ds = df.family == "Data Scientist"
out["data_scientist_in_centre"] = pct(REGIONS["111"][ds])
out["centre_not_data_scientist"] = 100 - out["centre_title_pct"]
# The page describes what is in each circle. Emit the members so prose cannot
# drift from the clustering: the six most-required labels, and the full list.
LAB = {v["id"]: v["label"] for v in json.load(open(HERE / "data" / "skills.json"))}
for _k, _name in [("eng", "Engineering, deployment & AI"), ("data", "Data platform"),
                  ("inference", "Statistics & inference"), ("ground", "_ground")]:
    _cols = C.circles(df)[_name]
    _top = df[_cols].mean().sort_values(ascending=False).index.tolist()
    out[f"members_{_k}"] = ", ".join(LAB.get(c[4:], c[4:]) for c in _top[:6])
    out[f"members_{_k}_all"] = ", ".join(sorted(LAB.get(c[4:], c[4:]) for c in _cols))

(HERE / "data" / "circles-2026.json").write_text(json.dumps(out, indent=2) + "\n")

# No figure is written here any more: RQ2 and RQ3 make their points in prose
# (owner, 2026-10-13). The numbers this script computes are still the source
# for those sections, via data/circles-2026.json.
