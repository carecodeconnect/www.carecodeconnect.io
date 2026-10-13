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

fig, ax = plt.subplots(figsize=(9.2, 6.4))
v = venn3([set(df.index[E]), set(df.index[D]), set(df.index[I])],
          set_labels=("", "", ""), ax=ax,
          set_colors=(BLUE, GREEN, VERMILLION), alpha=0.42)
venn3_circles([set(df.index[E]), set(df.index[D]), set(df.index[I])],
              ax=ax, lw=0.9, color="white")
for key in REGIONS:
    lab = v.get_label_by_id(key)
    if lab:
        lab.set_text(f"{pct(REGIONS[key])}%")
        lab.set_fontsize(11); lab.set_color(INK)
ax.text(-0.62, 0.50, f"Engineering, deployment & AI\n{out['pct_eng']}%", color=BLUE, fontsize=12,
        fontweight="bold", ha="center")
ax.text(0.62, 0.50, f"Data platform\n{out['pct_data']}%", color=GREEN, fontsize=12,
        fontweight="bold", ha="center")
ax.text(0.0, -0.68, f"Statistics & inference\n{out['pct_inference']}%", color=VERMILLION,
        fontsize=12, fontweight="bold", ha="center")
ax.set_axis_off()
fig.suptitle("What AI / data job ads ask for together, 2026", fontsize=15, fontweight="bold",
             color=INK, x=0.02, ha="left", y=0.99)
fig.text(0.02, 0.925,
         "Skills grouped by how often employers ask for them in the same ad, not by hand.\n"
         f"Communication is required by {out['pct_ground']}% of ads in every region, so it is the ground, not a circle.",
         fontsize=9.5, color=INK_MUTED, ha="left", va="top")
ax.text(1.0, -0.06, f"n = {N:,} ads · www.carecodeconnect.io", transform=ax.transAxes,
        fontsize=8.5, color=INK_MUTED, ha="right")
fig.subplots_adjust(top=0.84, bottom=0.06)
fig.savefig(HERE / "images" / "circles-2026.png", dpi=200, facecolor="white")
print("wrote images/circles-2026.png and data/circles-2026.json")
for k, val in out.items():
    if not k.startswith("_"):
        print(f"  {k:26}{val}")
