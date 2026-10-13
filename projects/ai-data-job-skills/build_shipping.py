#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib>=3.8", "pandas>=2.2"]
# ///
"""Does an ad want a model built, the model run in production, or both?

The page's claim about the Data Scientist title is a conjunction — shipping is
added to modelling rather than replacing it — and a conjunction needs the four
cells, not two shares. One stacked bar per title: both, model only, production
only, neither. Every number is read off the published CSV here and read off
the published CSV, so the page's variables and this chart cannot disagree."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from palette import BLUE, GREY, INK, INK_MUTED, ORANGE, SKY

HERE = Path(__file__).resolve().parent
df = pd.read_csv(HERE / "data" / "ai-data-job-skills.csv")
SHIP = ["model_serving", "mlops_tooling", "containers", "cicd_testing", "cloud", "orchestration"]
AIML = ["classical_ml", "deep_learning", "nlp", "computer_vision", "llm_apps", "agents",
        "rag", "fine_tuning"]
ship = df[[f"req_{s}" for s in SHIP if f"req_{s}" in df.columns]].sum(axis=1) > 0
aiml = df[[f"req_{s}" for s in AIML if f"req_{s}" in df.columns]].sum(axis=1) > 0

rows = []
for fam, g in df.groupby("family"):
    i = g.index
    rows.append({"family": fam, "n": len(g),
                 "both": 100 * (ship[i] & aiml[i]).mean(),
                 "model_only": 100 * (~ship[i] & aiml[i]).mean(),
                 "ship_only": 100 * (ship[i] & ~aiml[i]).mean(),
                 "neither": 100 * (~ship[i] & ~aiml[i]).mean()})
t = pd.DataFrame(rows).sort_values("both", ascending=True).reset_index(drop=True)

fig, ax = plt.subplots(figsize=(9.6, 5.0))
left = [0.0] * len(t)
# Okabe-Ito, validated with the dataviz validator: the previous blue/light-blue
# pair was ΔE 9.2 apart for NORMAL vision, a hard fail, let alone for CVD. This
# order passes adjacent-pair CVD separation and the normal-vision floor in light
# and dark; grey is the neutral "neither" rather than a categorical hue, and the
# in-segment numbers are the secondary encoding the contrast WARN requires.
SEG = [("both", BLUE, "Model and deployment"), ("model_only", ORANGE, "Model only"),
       ("ship_only", SKY, "Deployment only"), ("neither", GREY, "Neither")]
for col, colour, label in SEG:
    ax.barh(t.family, t[col], left=left, color=colour, label=label, height=0.68)
    for y, (v, l) in enumerate(zip(t[col], left)):
        if v >= 7:
            ax.text(l + v / 2, y, f"{v:.0f}%", ha="center", va="center", fontsize=9,
                    color="white" if col == "both" else INK)
    left = [a + b for a, b in zip(left, t[col])]
ax.set_xlim(0, 100); ax.set_xlabel("% of the title's job ads", color=INK_MUTED, fontsize=10)
ax.tick_params(colors=INK_MUTED, labelsize=10)
for s in ("top", "right", "left"):
    ax.spines[s].set_visible(False)
ax.spines["bottom"].set_color("#d8d8d4")
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.14), ncol=4, frameon=False,
          fontsize=9.5, labelcolor=INK_MUTED)
fig.suptitle("Is the job ad asking for a model, for running it, or both?", fontsize=14,
             fontweight="bold", color=INK, x=0.015, ha="left", y=0.99)
fig.text(0.015, 0.925, "Model = classical ML, deep learning, NLP, computer vision, LLM apps, agents, RAG or fine-tuning.\n"
                       "Deployment = serving, MLOps, containers, CI/CD, cloud or orchestration.",
         fontsize=9, color=INK_MUTED, ha="left", va="top")
fig.text(0.015, 0.045,
         f"n = {len(df):,} de-duplicated job ads with a data / AI title, hiring in Germany, EU-wide,\n"
         "worldwide-remote or the UK, Apr-Oct 2026 — collected by a personal job-board crawler and\n"
         "scored by a model judge against a fixed vocabulary.   www.carecodeconnect.io",
         fontsize=8.5, color=INK_MUTED, ha="left", va="bottom")
fig.subplots_adjust(top=0.80, bottom=0.30, left=0.21, right=0.98)
fig.savefig(HERE / "images" / "model-and-ship.png", dpi=200, facecolor="white")

print("wrote images/model-and-ship.png")
print(t.round(0).to_string(index=False))
