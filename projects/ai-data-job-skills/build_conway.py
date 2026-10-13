#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib>=3.8", "matplotlib-venn>=1.1", "pandas>=2.2"]
# ///
"""Three Venns for "what is data science?", in the order the page tells it:

  1. conway-2010.png     Drew Conway's 2010 diagram, redrawn (not reproduced) with
                         his labels and equal circles — the claim.
  2. conway-measured.png the same three circles, sized by how many of today's job
                         ads land in each region — the claim tested.
  3. ds-venn-2026.png    our own three circles, chosen because they are what the
                         ads actually cluster into — the replacement.

Plot text stays minimal: titles, labels and a provenance caption. The mapping from
tracked skills onto circles, and every caveat, lives in the page."""
from pathlib import Path
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib_venn import venn3, venn3_circles
from matplotlib_venn.layout.venn3 import DefaultLayoutAlgorithm

from palette import BLUE, VERMILLION, GREEN, WINE, INK, INK_MUTED, PANEL

HERE = Path(__file__).resolve().parent
SOURCE = "www.carecodeconnect.io"
IMG = HERE / "images"
df = pd.read_csv(HERE / "data" / "ai-data-job-skills.csv")
N = len(df)
CAPTION = (f"n = {N:,} de-duplicated job ads with a data / AI title, hiring in Germany, EU-wide, "
           f"worldwide-remote or the UK, Apr–Oct 2026.")

CONWAY = {
    "Hacking skills": ["python", "sql", "r", "scala_java", "typescript", "systems_lang",
                       "software_engineering", "apis_services", "cicd_testing", "containers",
                       "cloud", "mlops_tooling", "model_serving", "pipelines_etl",
                       "orchestration", "spark_distributed", "streaming", "warehouse",
                       "dbt_modelling"],
    "Maths & statistics": ["statistics", "experimentation", "causal_inference", "forecasting",
                           "time_series", "quant_research", "classical_ml", "deep_learning",
                           "nlp", "computer_vision", "recsys_ranking"],
    "Substantive expertise": ["stakeholder_comms", "customer_facing", "product_analytics",
                              "research", "bi_dashboards", "data_governance"],
}
# Our 2026 circles: the three things the ads actually cluster into. Stakeholder
# communication is deliberately NOT a circle — at 72% of all ads it is the ground
# everything stands on, so the page says so rather than the chart.
OURS = {
    # Named for its two biggest members — software engineering (68% of ads) and
    # model serving (50%) — because "software engineering" alone hid the fact
    # that half of all ads want the thing shipped and run, not just written.
    # Building and deploying are not separable: 60% of ads require both, and
    # only 6% want deployment without building (owner, 2026-10-08).
    "Software engineering\n& deployment": ["software_engineering", "apis_services", "cicd_testing", "containers",
                             "cloud", "mlops_tooling", "model_serving", "pipelines_etl",
                             "orchestration", "spark_distributed", "streaming", "warehouse",
                             "dbt_modelling", "typescript", "systems_lang", "scala_java"],
    "Statistics & Inference": ["statistics", "experimentation", "causal_inference", "forecasting", "time_series",
                  "quant_research", "classical_ml", "product_analytics", "bi_dashboards"],
    "LLM & agent engineering": ["llm_apps", "agents", "rag", "model_evaluation", "fine_tuning",
                                "llm_observability", "responsible_ai", "nlp", "deep_learning"],
}
ORDER = ("100", "010", "110", "001", "101", "011", "111")


def masks(spec):
    out = {}
    for k, ids in spec.items():
        cols = [f"req_{i}" for i in ids if f"req_{i}" in df.columns]
        out[k] = df[cols].sum(axis=1) > 0
    return list(out.values())


def regions(a, b, c):
    return {"100": (a & ~b & ~c).sum(), "010": (~a & b & ~c).sum(), "001": (~a & ~b & c).sum(),
            "110": (a & b & ~c).sum(), "101": (a & ~b & c).sum(), "011": (~a & b & c).sum(),
            "111": (a & b & c).sum()}


def nudge(t, dx, dy):
    x, y = t.get_position()
    t.set_position((x + dx, y + dy))


def leader(ax, t, xy_text, color=INK, size=9.0, weight="normal"):
    """Move a region/circle label outside the figure's circles and draw a thin
    leader line back to where it belongs. For slivers too narrow to hold their
    own text (owner, 2026-10-08) — cramming the words in makes them look like a
    label for the neighbouring region."""
    target = t.get_position()
    label = t.get_text()
    t.set_text("")
    ha = "left" if xy_text[0] > target[0] else "right"
    ax.annotate(label, xy=target, xytext=xy_text, textcoords="data",
                ha=ha, va="center", fontsize=size, color=color,
                fontweight=weight, linespacing=1.2,
                arrowprops=dict(arrowstyle="-", color=INK_MUTED, linewidth=0.8,
                                shrinkA=4, shrinkB=1))


def name_circles(v, names, cols, size=12, rot=(34, -34, 0), nudges=None):
    """Write each circle's name into its own exclusive lobe, which is where
    Conway put his. The two upper names are rotated along their lobe, as his
    are, so a long name fits inside the circle instead of spilling out of it
    (owner, 2026-10-08); the bottom name stays horizontal, as his does."""
    for rid, name, col, r in zip(("100", "010", "001"), names, cols, rot):
        t = v.get_label_by_id(rid)
        if t is None:
            continue
        t.set_text(name); t.set_fontsize(size); t.set_fontweight("bold")
        t.set_color(col); t.set_linespacing(1.15); t.set_rotation(r)
        t.set_rotation_mode("anchor")
        t.set_ha("center"); t.set_va("center")


def frame(ax, credit=SOURCE, lo=-0.72, hi=0.72, half=1.05):
    ax.set_xlim(-half, half); ax.set_ylim(lo, hi)
    for sp in ax.spines.values():
        sp.set_visible(False)
    ax.set_xticks([]); ax.set_yticks([])
    if credit:
        # Our site name goes ONLY on our own diagrams. A redrawing of someone
        # else's figure carries THEIR attribution instead (owner, 2026-10-08).
        ax.text(half - 0.05, lo + 0.02, credit, ha="right", va="bottom", fontsize=7.5, color=INK_MUTED)


def save(fig, name):
    out = IMG / name
    fig.savefig(out, facecolor="white")
    plt.close(fig)
    print("wrote", name)


# ── 1. Conway as drawn ───────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9.0, 7.2), dpi=200)
fig.patch.set_facecolor("white"); ax.set_facecolor(PANEL)
equal = DefaultLayoutAlgorithm(fixed_subset_sizes=(1,) * 7)
v = venn3(subsets=(1,) * 7, set_labels=("", "", ""), ax=ax, set_colors=(BLUE, VERMILLION, GREEN),
          alpha=0.45, layout_algorithm=equal)
venn3_circles(subsets=(1,) * 7, ax=ax, linewidth=1.1, color="#ffffff", layout_algorithm=equal)
for rid, text in [("110", "machine\nlearning"), ("011", "traditional\nresearch"),
                  ("101", "danger\nzone!"), ("111", "data\nscience")]:
    t = v.get_label_by_id(rid)
    if t is not None:
        t.set_text(text); t.set_fontsize(10.5); t.set_color(INK)
        if rid == "111":
            t.set_fontweight("bold")
name_circles(v, ["Hacking Skills", "Maths & Statistics\nKnowledge", "Substantive\nExpertise"],
             [BLUE, VERMILLION, GREEN], size=12)
frame(ax, credit="after Drew Conway (2010) · drewconway.com", lo=-0.78)
fig.suptitle("What is data science? The 2010 answer", x=0.02, ha="left", fontsize=15,
             fontweight="bold", color=INK, y=0.985)
ax.set_title("Drew Conway's data-science Venn diagram. Redrawn, not reproduced; regions are not to scale.",
             loc="left", fontsize=9.5, color=INK_MUTED, pad=10)
fig.text(0.02, 0.012, "After Drew Conway, “The Data Science Venn Diagram”, 2010 — drewconway.com/zia/2013/3/26/the-data-science-venn-diagram",
         fontsize=8, color=INK_MUTED, va="bottom")
fig.subplots_adjust(left=0.03, right=0.97, top=0.9, bottom=0.09)
save(fig, "conway-2010.png")

# ── 2. the same circles, measured ────────────────────────────────────────────
H, M, S = masks(CONWAY)
r = regions(H, M, S)
fig, ax = plt.subplots(figsize=(9.0, 7.2), dpi=200)
fig.patch.set_facecolor("white"); ax.set_facecolor(PANEL)
sub = tuple(int(r[k]) for k in ORDER)
v = venn3(subsets=sub, set_labels=("", "", ""), ax=ax, set_colors=(BLUE, VERMILLION, GREEN), alpha=0.45)
venn3_circles(subsets=sub, ax=ax, linewidth=1.1, color="#ffffff")
# Region names only, no percentages: with the regions already drawn to scale the
# figures made it hard to read, and the shares are in the prose (owner,
# 2026-10-08). Same treatment as the 2026 diagram — names inside the circles,
# the two upper ones tilted.
NAME = {"110": "machine\nlearning", "011": "traditional\nresearch", "101": "\u201cdanger\nzone\u201d",
        "111": "data\nscience"}
for rid in ("110", "011", "101", "111"):
    t = v.get_label_by_id(rid)
    if t is None:
        continue
    t.set_text(NAME[rid])
    t.set_fontsize(10.5 if rid == "111" else 8.5)
    t.set_color(INK); t.set_linespacing(1.2)
    t.set_fontweight("bold" if rid == "111" else "normal")
    # these two sit in thin slivers; keep them off the centre they border
    nudge(t, *{"110": (0.015, 0.015)}.get(rid, (0.0, 0.0)))
# Proportional geometry, so the lobes are not Conway's neat thirds: the maths
# circle is almost entirely contained and its exclusive sliver is 0.5% of ads,
# so its name is set small and steeply tilted to sit along that crescent.
name_circles(v, ["Hacking Skills", "Maths & Statistics", "Substantive Expertise"],
             [BLUE, VERMILLION, GREEN], size=9.0, rot=(32, 0, 0),
             nudges={"001": (0.0, 0.03)})
# Two slivers are too narrow to hold their text — the maths circle's own lobe
# (0.5% of ads) and "traditional research" (3%) — so those labels sit outside
# on a leader line instead of being crammed in (owner, 2026-10-08).
leader(ax, v.get_label_by_id("010"), (0.70, 0.34), color=VERMILLION, size=9.0, weight="bold")
leader(ax, v.get_label_by_id("011"), (0.70, -0.50), size=8.5)
frame(ax, credit=f"circles after Conway (2010) · analysis {SOURCE}", lo=-0.78)
fig.suptitle("The same three circles, measured", x=0.02, ha="left", fontsize=15,
             fontweight="bold", color=INK, y=0.985)
ax.set_title("Each job ad placed in the circles it requires at least one skill from. Region areas are to scale; the shares are in the text.",
             loc="left", fontsize=9.5, color=INK_MUTED, pad=10)
fig.text(0.02, 0.012, CAPTION, fontsize=8, color=INK_MUTED, va="bottom")
fig.subplots_adjust(left=0.03, right=0.97, top=0.9, bottom=0.09)
pass  # the measured Venn is superseded by the UpSet below
for k, c in r.items():
    print(f"   conway {k} {NAME.get(k,''):22s} {100*c/N:5.1f}%")

# Geometry of our 2026 Venn's text, in one place. Conway rotates every label that
# does not fit horizontally — the two upper circle names, "Danger Zone!" and
# "Traditional Research" — and we do the same for the same reason (owner,
# 2026-10-08): a tilted label follows the long axis of its lens and stops
# crossing the circle edge.
NAME2 = {"111": "Data\nScience", "110": "Analytics &\nForecasting", "101": "AI\nEngineering",
         "011": "Applied\nResearch"}
CIRCLE_NAMES = ["Software\nEngineering &\nDeployment", "Statistics\n& Inference",
                "LLM & Agent\nEngineering"]
CIRCLE_ROT = (42, -42, 0)          # steeper tilt than before, as asked
CIRCLE_NUDGE = {"100": (-0.02, -0.035), "010": (-0.005, -0.035), "001": (0.0, 0.11)}
# Region names stay horizontal — only the circle names are tilted (owner,
# 2026-10-08). The two side crescents are narrow, so their labels are set a
# little smaller and pushed away from the centre lens instead.
REGION_ROT = {"101": 0, "011": 0, "110": 0, "111": 0}
REGION_NUDGE = {"101": (-0.035, -0.02), "011": (0.035, -0.02)}


def label_regions(v, big=13.0, small=11.0, side=9.5):
    """The four meaningful regions. The two side lenses are rotated along their
    axis; the top lens and the centre are wide enough to stay horizontal."""
    for rid in ("110", "101", "011", "111"):
        t = v.get_label_by_id(rid)
        if t is None:
            continue
        t.set_text(NAME2[rid])
        t.set_fontsize(big if rid == "111" else side if rid in ("101", "011") else small)
        t.set_color(INK)
        t.set_fontweight("bold" if rid == "111" else "normal")
        t.set_linespacing(1.2)
        t.set_rotation(REGION_ROT[rid])
        t.set_rotation_mode("anchor")
        t.set_ha("center"); t.set_va("center")
        nudge(t, *REGION_NUDGE.get(rid, (0.0, 0.0)))



# ── 3. ours ──────────────────────────────────────────────────────────────────
# Drawn in Conway's idiom on purpose: EQUAL circles, big bold names on the
# circles themselves, and only the four meaningful regions labelled. His works
# because it can be read in two seconds; proportional geometry and seven labels
# made ours slower to read than the thing it updates (owner, 2026-10-08).
# The proportional version of the same data is the "measured" figure above.
A, B, C = masks(OURS)
r2 = regions(A, B, C)
fig, ax = plt.subplots(figsize=(9.6, 8.0), dpi=200)
fig.patch.set_facecolor("white"); ax.set_facecolor("white")
v = venn3(subsets=(1,) * 7, set_labels=("", "", ""), ax=ax, set_colors=(BLUE, GREEN, WINE),
          alpha=0.42, layout_algorithm=equal)
venn3_circles(subsets=(1,) * 7, ax=ax, linewidth=1.4, color="#ffffff", layout_algorithm=equal)
label_regions(v)
name_circles(v, CIRCLE_NAMES, [BLUE, GREEN, WINE], size=11.0, rot=CIRCLE_ROT, nudges=CIRCLE_NUDGE)
frame(ax, lo=-0.84, hi=0.72)
fig.suptitle("What is data science now? The 2026 answer", x=0.02, ha="left", fontsize=16,
             fontweight="bold", color=INK, y=0.985)
ax.set_title(f"The regions {N:,} European and UK data / AI job ads fall into. Circles drawn equal, as Conway drew his.",
             loc="left", fontsize=10, color=INK_MUTED, pad=10)
fig.text(0.02, 0.012, CAPTION, fontsize=8, color=INK_MUTED, va="bottom")
fig.subplots_adjust(left=0.03, right=0.97, top=0.90, bottom=0.07)
save(fig, "ds-venn-2026.png")
for k, c in r2.items():
    print(f"   2026   {k} {NAME2.get(k,'(unlabelled)').replace(chr(10),' '):24s} {100*c/N:5.1f}%")

# ── 4. the hero: Conway's ORIGINAL above our 2026 version ────────────────────
# The top panel is Conway's own image, reproduced with attribution rather than
# redrawn — he made the point, so it should be his artwork making it (owner,
# 2026-10-08). Stacked rather than side by side, because two Venns in one row
# render too small to read (owner, 2026-10-08). No site credit on his half.
import matplotlib.image as mpimg

fig, (axT, axB) = plt.subplots(2, 1, figsize=(8.6, 14.4), dpi=200,
                               gridspec_kw={"height_ratios": [1, 1]})
fig.patch.set_facecolor("white")

orig = mpimg.imread(HERE / "images" / "external" / "conway-data-science-vd.png")
axT.imshow(orig)
axT.set_xticks([]); axT.set_yticks([])
for sp in axT.spines.values():
    sp.set_visible(False)
axT.set_xlabel("© Drew Conway, 2010 · drewconway.com", fontsize=8.5, color=INK_MUTED, labelpad=6)

axB.set_facecolor("white")
vB = venn3(subsets=(1,) * 7, set_labels=("", "", ""), ax=axB, set_colors=(BLUE, GREEN, WINE),
           alpha=0.42, layout_algorithm=equal)
venn3_circles(subsets=(1,) * 7, ax=axB, linewidth=1.4, color="#ffffff", layout_algorithm=equal)
label_regions(vB, big=12.5, small=10.5, side=9.0)
name_circles(vB, CIRCLE_NAMES, [BLUE, GREEN, WINE], size=10.5, rot=CIRCLE_ROT, nudges=CIRCLE_NUDGE)
frame(axB, lo=-0.78, hi=0.60, half=0.70)

fig.suptitle("What is data science? Sixteen years apart", x=0.03, ha="left", fontsize=17,
             fontweight="bold", color=INK, y=0.992)
fig.text(0.03, 0.012, "Above: Drew Conway, \u201cThe Data Science Venn Diagram\u201d, 2010, reproduced with attribution.\n"
         "Below: this page's circles, drawn in the same idiom \u2014 equal circles, named regions \u2014 from\n"
         f"{N:,} European and UK data / AI job ads, Apr\u2013Oct 2026. Region shares are given on the page.",
         fontsize=8.5, color=INK_MUTED, va="bottom", linespacing=1.45)
fig.subplots_adjust(left=0.03, right=0.97, top=0.925, bottom=0.065, hspace=0.12)
for ax_, label in ((axT, "2010 — Drew Conway's answer"),
                   (axB, "2026 — from the European job market")):
    fig.text(0.03, ax_.get_position().y1 + 0.006, label, ha="left", va="bottom",
             fontsize=14, fontweight="bold", color=INK)
save(fig, "ds-venn-2010-vs-2026.png")


# conway-measured.png is no longer published: RQ1 makes the point in two
# sentences and the chart repeated them (owner, 2026-10-13).
