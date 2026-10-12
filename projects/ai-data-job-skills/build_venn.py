#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib>=3.8", "matplotlib-venn>=1.1", "pandas>=2.2"]
# ///
"""Venn diagram of the CORE skills of Data Scientist, AI Engineer and ML Engineer ads.

A title's core skill = required in at least CORE_PCT % of that title's ads. Sets are
drawn with equal circles (unweighted): the regions list skills, their areas mean
nothing. Same data as every other figure: data/ai-data-job-skills.csv."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib_venn import venn3, venn3_circles
from matplotlib_venn.layout.venn3 import DefaultLayoutAlgorithm

HERE = Path(__file__).resolve().parent
CORE_PCT = 30
import json
LABEL = {v["id"]: v["label"].replace(" / evals", "") for v in json.load(open(HERE / "data" / "skills.json"))}
from palette import BLUE, VERMILLION, GREEN, INK, INK_MUTED, PANEL   # Okabe-Ito, see palette.py

df = pd.read_csv(HERE / "data" / "ai-data-job-skills.csv")
req = [c for c in df.columns if c.startswith("req_")]
rate = df.groupby("family")[req].mean().mul(100)
n = df["family"].value_counts()
sets = {f: {c[4:] for c in req if rate.loc[f, c] >= CORE_PCT} for f in ("Data Scientist", "AI Engineer", "ML Engineer")}
ds, ai, ml = sets["Data Scientist"], sets["AI Engineer"], sets["ML Engineer"]

def lab(members, rid=""):
    """Region label. An empty two-way region says "(none of their own)", not
    "(none)": everything those two share is also required by the third title, so
    it sits in the centre. The plot says only that much — the explanation belongs
    in the page text, never on the chart (owner, 2026-10-08)."""
    if members:
        return "\n".join(LABEL.get(x, x.replace("_", " "))
                         for x in sorted(members, key=lambda x: -rate.loc[:, f"req_{x}"].max()))
    centre = ds & ai & ml
    if rid in {"110", "101", "011"} and centre:
        return "(none of their own)"
    return "(none)"

fig, ax = plt.subplots(figsize=(9, 7.2), dpi=200)
fig.patch.set_facecolor("white"); ax.set_facecolor(PANEL)
# Equal regions regardless of how many skills fall in each (matplotlib-venn >= 1.1 API).
equal = DefaultLayoutAlgorithm(fixed_subset_sizes=(1, 1, 1, 1, 1, 1, 1))
v = venn3([ds, ai, ml], set_labels=("", "", ""), ax=ax, set_colors=(BLUE, VERMILLION, GREEN), alpha=0.45,
          layout_algorithm=equal)
venn3_circles([ds, ai, ml], ax=ax, linewidth=1.2, color="#ffffff", layout_algorithm=equal)
regions = {"100": ds - ai - ml, "010": ai - ds - ml, "001": ml - ds - ai, "110": (ds & ai) - ml,
           "101": (ds & ml) - ai, "011": (ai & ml) - ds, "111": ds & ai & ml}
for rid, members in regions.items():
    t = v.get_label_by_id(rid)
    if t is not None:
        t.set_text(lab(members, rid)); t.set_fontsize(9.5); t.set_color("#0b0b0b"); t.set_linespacing(1.25)
        if rid == "111": t.set_fontweight("bold")
        if rid == "011": t.set_position((t.get_position()[0] + 0.03, t.get_position()[1] - 0.05))
        if rid == "101": t.set_position((t.get_position()[0] - 0.02, t.get_position()[1] - 0.04))
# set names + n, as text in the title colour, outside the circles
for (x, y, name, col, ha) in [(-0.55, 0.55, "Data Scientist", BLUE, "right"), (0.55, 0.55, "AI Engineer", VERMILLION, "left"),
                              (0.0, -0.72, "ML Engineer", GREEN, "center")]:
    ax.text(x, y, f"{name}\n{len(sets[name])} core skills · n = {n[name]:,}", ha=ha, va="center", fontsize=11,
            fontweight="bold", color=col)
ax.set_xlim(-1.05, 1.05); ax.set_ylim(-0.92, 0.78)
for s in ax.spines.values(): s.set_visible(False)
ax.set_xticks([]); ax.set_yticks([])
fig.suptitle("Which core skills the three titles share", x=0.02, ha="left", fontsize=15, fontweight="bold", color=INK, y=0.985)
ax.set_title(f"A title's core skill = required in at least {CORE_PCT}% of its ads. Equal circles: regions list skills, their sizes mean nothing.",
             loc="left", fontsize=9.5, color=INK_MUTED, pad=10)
fig.text(0.02, 0.012, f"n = {len(df):,} de-duplicated job ads with a data / AI title, hiring in Germany, EU-wide, worldwide-remote or the UK, "
         "Apr–Oct 2026.\nSkill requirements read from each ad's full description by a model judge (Jev); 'required' means the ad asks for it.",
         fontsize=8, color=INK_MUTED, va="bottom")
ax.text(1.0, -0.86, "www.carecodeconnect.io", ha="right", va="bottom", fontsize=7.5, color=INK_MUTED)
fig.subplots_adjust(left=0.03, right=0.97, top=0.9, bottom=0.1)
out = HERE / "images" / "core-skills-venn.png"
fig.savefig(out, facecolor="white"); print("wrote", out.relative_to(HERE.parent.parent))
for k, m in regions.items(): print(k, sorted(m))
