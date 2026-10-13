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

# A membership grid, not a Venn: rows are the skills, columns the three titles,
# a filled dot means the skill is core to that title. A Venn would make the reader
# decode which region is which, and its areas would mean nothing anyway.
TITLES = ["Data Scientist", "AI Engineer", "ML Engineer"]
COL = {"Data Scientist": BLUE, "AI Engineer": VERMILLION, "ML Engineer": GREEN}
union = sorted(ds | ai | ml,
               key=lambda x: (-sum(x in sets[t] for t in TITLES), -rate.loc[:, f"req_{x}"].max()))
fig, ax = plt.subplots(figsize=(7.8, 0.34 * len(union) + 2.2))
for yi, sk in enumerate(union):
    y = len(union) - yi - 1
    shared = sum(sk in sets[t] for t in TITLES)
    ax.text(-0.25, y, LABEL.get(sk, sk.replace("_", " ")), ha="right", va="center",
            fontsize=10, color=INK if shared == 3 else INK_MUTED,
            fontweight="bold" if shared == 3 else "normal")
    for xi, t in enumerate(TITLES):
        on = sk in sets[t]
        ax.scatter(xi, y, s=150, color=COL[t] if on else "#e4e4e0", edgecolor="none", zorder=3)
    on_idx = [i for i, t in enumerate(TITLES) if sk in sets[t]]
    if len(on_idx) > 1:
        ax.plot([min(on_idx), max(on_idx)], [y, y], color="#b9b9b4", lw=1.6, zorder=2)
for xi, t in enumerate(TITLES):
    ax.text(xi, len(union) - 0.35, t, rotation=24, ha="left", va="bottom", rotation_mode="anchor",
            fontsize=9.5, color=COL[t], fontweight="bold")
ax.set_xlim(-2.2, len(TITLES) + 0.55); ax.set_ylim(-0.8, len(union) + 0.9)
ax.set_axis_off()
fig.suptitle("Which skills are core to which title", fontsize=14, fontweight="bold",
             color=INK, x=0.02, ha="left", y=0.985)
fig.text(0.02, 0.945, f"A skill is core to a title when at least {CORE_PCT}% of that title's job ads "
                      "require it. Bold rows are core to all three.",
         fontsize=9.5, color=INK_MUTED, ha="left", va="top")
fig.text(0.02, 0.015, f"n = {len(df):,} de-duplicated job ads with a data / AI title, hiring in Germany, "
                      "EU-wide, worldwide-remote or the UK,\nApr-Oct 2026 — collected by a personal "
                      "job-board crawler and scored by a model judge.   www.carecodeconnect.io",
         fontsize=8.5, color=INK_MUTED, ha="left", va="bottom")
fig.subplots_adjust(top=0.86, bottom=0.10, left=0.46, right=0.86)
fig.savefig(HERE / "images" / "core-skills-venn.png", dpi=200, facecolor="white")
print(f"  wrote images/core-skills-venn.png (membership grid, {len(union)} skills)")
