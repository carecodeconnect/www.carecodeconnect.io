#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["plotnine>=0.14", "pandas>=2.2", "adjustText>=1.0"]
# ///
"""Static figures for the AI / Data Job Skills page, all from the published CSV so a
reader can reproduce every number: roles.png (title proportions), skills-by-demand.png
(every tracked skill by required share) and ds-vs-ai-engineer.png (skill areas, DS vs AI Engineer).
plotnine theme_grey throughout."""
from pathlib import Path

import pandas as pd
import numpy as np
from plotnine import (aes, annotate, coord_flip, element_blank, element_line, element_text, geom_abline, geom_col, geom_hline,
                      geom_point, geom_segment, geom_text, geom_vline, ggplot, labs, scale_color_manual,
                      scale_x_continuous, scale_y_continuous, theme, theme_grey)

HERE = Path(__file__).resolve().parent
IMG = HERE / "images"
df = pd.read_csv(HERE / "data" / "ai-data-job-skills.csv")
N = len(df)
REQ = [c for c in df.columns if c.startswith("req_")]
# The vocabulary (ids, labels, skill areas) comes from data/skills.json, exported by
# jobcrawler's scripts/skill-clusters.py from the crawler's own config, so a vocabulary
# edit upstream flows through here without code changes.
import json
VOCAB = json.load(open(HERE / "data" / "skills.json"))
LABEL = {v["id"]: v["label"] for v in VOCAB}
AREA: dict[str, list[str]] = {}
for v in VOCAB:
    AREA.setdefault(v["area"], []).append(v["id"])
N_SKILLS = len([c for c in REQ if c[4:] in LABEL])
from palette import BLUE, VERMILLION as ORANGE, PURPLE, GREY, INK, INK_MUTED  # Okabe-Ito, see palette.py
CAPTION = (f"n = {N:,} de-duplicated job ads with a data / AI title, hiring in Germany, EU-wide, worldwide-remote or the UK, "
           "Apr–Oct 2026.\nSkill requirements read from each ad's full description by a model judge (Jev); "
           "'required' means the ad asks for it.")
# Source credit, bottom-right of every figure, so a screenshot taken out of
# context still says where it came from (owner, 2026-10-08).
SOURCE = "www.carecodeconnect.io"


def src_at(corner: str):
    """Put the source credit in the named corner of the panel."""
    return theme(plot_tag_position=corner)
BASE = (theme_grey(base_size=11)
        + theme(plot_title=element_text(weight="bold"), plot_subtitle=element_text(color=INK_MUTED, size=9),
                plot_caption=element_text(color=INK_MUTED, size=8, ha="left"), panel_grid_major_y=element_blank(),
                plot_tag=element_text(color=INK_MUTED, size=7.5),
                # "panel" puts the credit INSIDE the plotting area, so it travels
                # with a screenshot that crops the caption. Corner is per-figure
                # (`src_at`) because the empty corner differs from plot to plot.
                plot_tag_location="panel", plot_tag_position="bottomright",
                legend_title=element_blank()))


def roles() -> None:
    c = df["family"].value_counts().rename_axis("family").reset_index(name="n").sort_values("n")
    c["pct"] = 100 * c["n"] / N
    c["lab"] = [f"{p:.0f}%  ({n:,})" for p, n in zip(c["pct"], c["n"])]
    c["family"] = pd.Categorical(c["family"], categories=list(c["family"]))
    p = (ggplot(c, aes("family", "pct")) + geom_col(width=0.65, fill=BLUE)
         + geom_text(aes(label="lab"), ha="left", nudge_y=0.6, size=8.5, color=INK)
         + coord_flip() + scale_y_continuous(labels=lambda v: [f"{x:.0f}%" for x in v], expand=(0, 0, 0.25, 0))
         + labs(title="Which titles are in the sample", subtitle=f"Share of the {N:,} job ads by job-title family (from the ad's own title)",
                caption=CAPTION, tag=SOURCE, x="", y="% of job ads") + BASE + theme(figure_size=(9, 4)) + src_at("bottomright"))
    p.save(IMG / "roles.png", dpi=200, verbose=False)


def demand() -> None:
    g = df[REQ].mean().mul(100).rename("pct").reset_index().rename(columns={"index": "skill"})
    g["label"] = g["skill"].str[4:].map(LABEL)
    g = g.sort_values("pct")
    g["label"] = pd.Categorical(g["label"], categories=list(g["label"]))
    g["lab"] = [f"{x:.0f}%" for x in g["pct"]]
    p = (ggplot(g, aes("label", "pct")) + geom_col(width=0.7, fill=BLUE)
         + geom_text(aes(label="lab"), ha="left", nudge_y=0.8, size=7.5, color=INK)
         + coord_flip() + scale_y_continuous(labels=lambda v: [f"{x:.0f}%" for x in v], expand=(0, 0, 0.1, 0))
         + labs(title=f"The {N_SKILLS} skills, ranked by how many ads require them", subtitle="Share of all job ads that list the skill as a requirement",
                caption=CAPTION, tag=SOURCE, x="", y="% of job ads") + BASE + theme(figure_size=(9, 10.5)) + src_at("bottomright"))
    p.save(IMG / "skills-by-demand.png", dpi=200, verbose=False)


def ds_vs_ai() -> None:
    a, b = "Data Scientist", "AI Engineer"
    rows = []
    for area, ids in AREA.items():
        cols = [f"req_{i}" for i in ids if f"req_{i}" in df.columns]
        for fam in (a, b):
            d = df[df["family"] == fam]
            rows.append({"area": area, "family": fam, "rate": 100 * (d[cols].sum(axis=1) > 0).mean()})
    r = pd.DataFrame(rows)
    w = r.pivot(index="area", columns="family", values="rate")
    w["gap"] = w[b] - w[a]
    w = w.sort_values(a).reset_index()
    order = list(w["area"])
    r["area"] = pd.Categorical(r["area"], categories=order); r["family"] = pd.Categorical(r["family"], categories=[a, b])
    w["area"] = pd.Categorical(w["area"], categories=order)
    w["xlab"] = w[[a, b]].max(axis=1) + 3
    w["gaplab"] = ["even" if abs(g) < 0.5 else f"{'AI' if g > 0 else 'DS'} +{abs(g):.0f} pp" for g in w["gap"]]
    w["leader"] = pd.Categorical([b if g > 0 else a for g in w["gap"]], categories=[a, b])
    n = df["family"].value_counts()
    p = (ggplot()
         + geom_segment(w, aes(x=a, xend=b, y="area", yend="area"), color=GREY, size=0.9)
         + geom_point(r, aes("rate", "area", color="family"), size=3.2)
         + geom_text(w, aes(x="xlab", y="area", label="gaplab", color="leader"), ha="left", size=7.5, show_legend=False)
         + scale_color_manual(values=[BLUE, ORANGE], labels=[f"{a} (n={n[a]:,})", f"{b} (n={n[b]:,})"])
         # Room on the right for the gap label: "Software engineering" sits at 96%,
         # so the annotation runs past 100 and was being clipped.
         + scale_x_continuous(labels=lambda v: [f"{x:.0f}%" for x in v], limits=(0, 118),
                              breaks=range(0, 101, 20), expand=(0, 0))
         + labs(title="What a “Data Scientist” job asks for vs an “AI Engineer” job",
                subtitle=f"{len(AREA)} skill areas, each covering several of the {N_SKILLS} skills tracked. Label = the title that asks for the area more often.",
                caption=CAPTION, tag=SOURCE, x="% of jobs that require at least one skill in the area", y="")
         + BASE + theme(figure_size=(9, 5.4), legend_position="top") + src_at("bottomright"))
    p.save(IMG / "ds-vs-ai-engineer.png", dpi=200, verbose=False)
    print(w[["area", a, b, "gap"]].round(0).to_string(index=False))


def skill_scatter(core_pct: float = 30.0) -> None:
    """Every skill as a dot: x = share of Data Scientist ads requiring it, y = the same for
    AI Engineer ads. The dashed lines are the Venn's core threshold, so the four quadrants
    ARE the Venn regions — this is the continuous picture the Venn simplifies."""
    a, b = "Data Scientist", "AI Engineer"
    g = pd.DataFrame({"skill": [c[4:] for c in REQ],
                      "ds": [100 * df.loc[df["family"] == a, c].mean() for c in REQ],
                      "ai": [100 * df.loc[df["family"] == b, c].mean() for c in REQ]})
    g["label"] = g["skill"].map(LABEL)
    g["region"] = pd.Categorical(np.select(
        [(g.ds >= core_pct) & (g.ai >= core_pct), (g.ds >= core_pct), (g.ai >= core_pct)],
        ["Core for both", "Core for Data Scientist only", "Core for AI Engineer only"], "Core for neither"),
        categories=["Core for both", "Core for Data Scientist only", "Core for AI Engineer only", "Core for neither"])
    # Every dot gets text (owner, 2026-10-06: the unlabelled bottom-left knot was the
    # complaint). Skills required by >= 8% of either title are labelled in place, repelled
    # by adjustText; the knot of rarely-required skills is numbered on the plot and the
    # numbers are keyed in the empty top-left quadrant, where nothing is ever plotted.
    n = df["family"].value_counts()
    knot_mask = (g["ds"] < 8) & (g["ai"] < 8)
    knot = g[knot_mask].sort_values(["ds", "ai"], ascending=False).copy()
    knot["num"] = [str(i) for i in range(1, len(knot) + 1)]
    # Right-hand dots (DS >= 65%) get a plain right-aligned label so nothing runs off the
    # panel edge; everything else in between is repelled by adjustText.
    right = g[~knot_mask & (g["ds"] >= 65)].copy()
    right["ly"] = right["ai"] + np.where(right["skill"] == "python", 2.6, np.where(right["skill"] == "stakeholder_comms", -2.6, 0.0))
    labelled = g[~knot_mask & (g["ds"] < 65)]
    key = "Rarely required by either title (<8%):\n" + "\n".join(f"{k}  {l}" for k, l in zip(knot["num"], knot["label"]))
    p = (ggplot(g, aes("ds", "ai"))
         + geom_hline(yintercept=core_pct, linetype="dashed", color=GREY, size=0.5)
         + geom_vline(xintercept=core_pct, linetype="dashed", color=GREY, size=0.5)
         + geom_abline(slope=1, intercept=0, color="#c8c8c8", size=0.4)
         + geom_point(aes(color="region"), size=2.6)
         + geom_text(labelled, aes(label="label"), size=6.2, color=INK,
                     adjust_text={"expand": (1.3, 1.6), "arrowprops": {"arrowstyle": "-", "color": "#9a9a96", "lw": 0.4},
                                  "force_text": (0.4, 0.7), "force_static": (0.3, 0.5), "max_move": (30, 30), "min_arrow_len": 4,
                                  "ensure_inside_axes": True})
         + geom_text(right, aes(y="ly", label="label"), size=6.2, color=INK, ha="right", nudge_x=-1.6)
         + geom_text(knot, aes(label="num"), size=5.6, color=INK,
                     adjust_text={"expand": (1.2, 1.4), "arrowprops": {"arrowstyle": "-", "color": "#9a9a96", "lw": 0.35},
                                  "force_text": (0.3, 0.5), "max_move": (25, 25), "min_arrow_len": 3})
         + annotate("text", x=1, y=101, label=key, ha="left", va="top", size=6.2, color=INK, lineheight=1.25)
         + scale_color_manual(values=[PURPLE, BLUE, ORANGE, GREY])
         + scale_x_continuous(labels=lambda v: [f"{x:.0f}%" for x in v], limits=(-15, 104), breaks=range(0, 101, 20), expand=(0, 0))
         + scale_y_continuous(labels=lambda v: [f"{x:.0f}%" for x in v], limits=(-11, 103), breaks=range(0, 101, 20), expand=(0, 0))
         + labs(title="Every skill, by how often each title requires it",
                subtitle=f"One dot per skill. Dashed lines = the {core_pct:.0f}% core threshold used in the Venn diagram; "
                         "the grey diagonal = required equally often by both titles.",
                caption=CAPTION, tag=SOURCE, x=f"% of Data Scientist ads requiring it (n = {n[a]:,})",
                y=f"% of AI Engineer ads requiring it (n = {n[b]:,})")
         + BASE + theme(figure_size=(10, 8.8), legend_position="top", panel_grid_major_y=element_line(color="white")) + src_at("topright"))
    p.save(IMG / "skills-ds-vs-ai-scatter.png", dpi=200, verbose=False)


roles(); demand(); ds_vs_ai(); skill_scatter()
print("roles:", df["family"].value_counts().to_dict())
print("python absent among AI Engineer ads: %.0f%%" % (100 * (df.loc[df.family == "AI Engineer", "req_python"] == 0).mean()))
print("wrote", sorted(p.name for p in IMG.glob("*.png")))
