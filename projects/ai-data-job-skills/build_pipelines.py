#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib>=3.8"]
# ///
"""The two pipeline models of data science, redrawn in this page's style so the
three canonical answers can sit side by side.

Redrawn, NOT reproduced: neither original is published under a licence that
clearly permits redistribution, so the page shows its own rendering of the idea
and links to the source. Each figure carries ITS AUTHOR's attribution, never
this site's — only our own analysis gets that (owner, 2026-10-08)."""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

from palette import BLUE, GREEN, WINE, INK, INK_MUTED, PANEL

HERE = Path(__file__).resolve().parent
IMG = HERE / "images"


def box(ax, x, y, w, h, text, face):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.012,rounding_size=0.03",
                                linewidth=1.1, edgecolor="white", facecolor=face, alpha=0.75))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=10.5, color=INK)


def arrow(ax, x1, y1, x2, y2, rad=0.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=12,
                                 linewidth=1.2, color=INK_MUTED,
                                 connectionstyle=f"arc3,rad={rad}"))


def finish(ax, fig, title, sub, credit):
    ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.set_aspect("auto")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_facecolor(PANEL)
    fig.suptitle(title, x=0.03, ha="left", fontsize=14, fontweight="bold", color=INK, y=0.97)
    ax.set_title(sub, loc="left", fontsize=9.5, color=INK_MUTED, pad=8)
    ax.text(0.995, 0.02, credit, ha="right", va="bottom", fontsize=7.5, color=INK_MUTED)


# ── OSEMN ────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7.6, 5.4), dpi=200)
fig.patch.set_facecolor("white")
steps = ["Obtain", "Scrub", "Explore", "Model", "iNterpret"]
h, w, x = 0.11, 0.56, 0.22
for i, st in enumerate(steps):
    y = 0.80 - i * 0.155
    box(ax, x, y, w, h, st, BLUE)
    if i:
        arrow(ax, x + w / 2, y + h + 0.045, x + w / 2, y + h + 0.004)
finish(ax, fig, "What do you do? (1)", "Mason & Wiggins, 2010 — later the OSEMN model",
       "after Mason & Wiggins (2010) · dataists.com")
fig.subplots_adjust(left=0.04, right=0.96, top=0.84, bottom=0.05)
fig.savefig(IMG / "osemn.png", facecolor="white"); plt.close(fig)
print("wrote osemn.png")

# ── R4DS ─────────────────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(7.6, 5.4), dpi=200)
fig.patch.set_facecolor("white")
box(ax, 0.06, 0.78, 0.34, 0.11, "Import", BLUE)
arrow(ax, 0.23, 0.775, 0.23, 0.735)
box(ax, 0.06, 0.62, 0.34, 0.11, "Tidy", BLUE)
# the understand loop
ax.add_patch(FancyBboxPatch((0.05, 0.19), 0.90, 0.37, boxstyle="round,pad=0.012,rounding_size=0.03",
                            linewidth=1.1, edgecolor=GREEN, facecolor=GREEN, alpha=0.14))
ax.text(0.50, 0.525, "Understand — repeat", ha="center", va="center", fontsize=10,
        fontweight="bold", color=GREEN)
for i, (lbl, xx) in enumerate([("Transform", 0.08), ("Visualise", 0.38), ("Model", 0.68)]):
    box(ax, xx, 0.29, 0.24, 0.11, lbl, GREEN)
    if i:
        arrow(ax, xx - 0.06, 0.345, xx - 0.004, 0.345)
arrow(ax, 0.92, 0.345, 0.92, 0.245, rad=0)
arrow(ax, 0.92, 0.245, 0.20, 0.245)
arrow(ax, 0.20, 0.245, 0.20, 0.285)
arrow(ax, 0.23, 0.615, 0.23, 0.565)
arrow(ax, 0.50, 0.185, 0.50, 0.145)
box(ax, 0.33, 0.03, 0.34, 0.11, "Communicate", WINE)
finish(ax, fig, "What do you do? (2)", "Wickham, Çetinkaya-Rundel & Grolemund — R for Data Science",
       "after Wickham et al. · r4ds.hadley.nz")
fig.subplots_adjust(left=0.04, right=0.96, top=0.84, bottom=0.05)
fig.savefig(IMG / "r4ds-workflow.png", facecolor="white"); plt.close(fig)
print("wrote r4ds-workflow.png")
