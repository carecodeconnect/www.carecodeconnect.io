#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2", "numpy>=1.26", "plotnine>=0.13"]
# ///
"""Figures for the per-title deep dive.

  images/title-<slug>.png   one per title family: the skills it requires most,
                            and the skills most over-represented in it, each
                            against the whole-sample share so the gap is visible
                            rather than asserted.
  images/build-vs-call.png  one plot for all nine titles: building or training a
                            model versus calling one over an API.

Replaces the prose lists these sections used to carry (owner, 2026-10-08).
Colours come from palette.py (Okabe-Ito); two series only, so colour is safe,
and the marker shape differs as well."""
from pathlib import Path

import numpy as np
import pandas as pd
from plotnine import (aes, coord_flip, element_blank, element_text, facet_wrap,
                      geom_col, geom_point, geom_segment, ggplot, labs, scale_color_manual,
                      scale_fill_manual, scale_shape_manual, scale_x_discrete,
                      scale_y_continuous, theme, theme_grey)

from palette import BLUE, VERMILLION, GREY, INK_MUTED

HERE = Path(__file__).resolve().parent
IMG = HERE / "images"
SOURCE = "www.carecodeconnect.io"
df = pd.read_csv(HERE / "data" / "ai-data-job-skills.csv")
N = len(df)
REQ = [c for c in df.columns if c.startswith("req_")]

NICE = {"nlp": "NLP", "rag": "RAG", "sql": "SQL", "r": "R", "bi_dashboards": "BI dashboards",
        "llm_apps": "LLM applications", "llm_observability": "LLM observability",
        "apis_services": "APIs and services", "cicd_testing": "CI/CD and testing",
        "mlops_tooling": "MLOps tooling", "dbt_modelling": "dbt modelling", "python": "Python",
        "quant_research": "quantitative research", "stakeholder_comms": "stakeholder communication",
        "systems_lang": "systems languages", "scala_java": "Scala or Java", "typescript": "TypeScript",
        "spark_distributed": "Spark", "pipelines_etl": "data pipelines", "classical_ml": "classical ML",
        "mentoring_leadership": "mentoring and leadership", "customer_facing": "customer-facing work",
        "recsys_ranking": "recommenders and ranking", "fine_tuning": "fine-tuning",
        "responsible_ai": "responsible AI"}
# Canonical presentation order, then anything the data has that this list does
# not. A hardcoded list silently skipped the AI Automation family when it was
# added, leaving its section in the deep dive pointing at a figure that was
# never drawn — so the list can order families but must not decide which exist.
_CANON = ["Quantitative Researcher", "Data Analyst", "Research Scientist", "Data Scientist",
          "Data Engineer", "ML Engineer", "Analytics Engineer", "Forward Deployed", "AI Engineer"]
_present = list(df["family"].unique())
ORDER = [f for f in _CANON if f in _present] + [f for f in _present if f not in _CANON]
if [f for f in _present if f not in _CANON]:
    print("   note: families not in the canonical order, appended: "
          + ", ".join(f for f in _present if f not in _CANON))
TRAIN = ["classical_ml", "deep_learning", "fine_tuning", "computer_vision", "recsys_ranking"]
CALL = ["llm_apps", "agents", "rag", "llm_observability"]

BASE = (theme_grey(base_size=10)
        + theme(plot_title=element_text(weight="bold", size=12),
                plot_subtitle=element_text(color=INK_MUTED, size=8.5),
                plot_caption=element_text(color=INK_MUTED, size=7.5, ha="left"),
                panel_grid_major_y=element_blank(),
                strip_text=element_text(weight="bold", size=9),
                legend_title=element_blank(), legend_position="top"))


def pretty(s: str) -> str:
    return NICE.get(s, s.replace("_", " "))


def slug(f: str) -> str:
    return f.lower().replace(" ", "-")


def title_figure(fam: str) -> None:
    g = df[df.family == fam]
    rest = df[df.family != fam]
    share = g[REQ].mean()
    allshare = df[REQ].mean()
    lift = (share + 0.01) / (rest[REQ].mean() + 0.01)

    rows = []
    for panel, keys in (("Required most often", share.sort_values(ascending=False).head(10).index),
                        ("Most over-represented in this title",
                         lift.sort_values(ascending=False).head(10).index)):
        for k in keys:
            rows.append({"panel": panel, "skill": pretty(k[4:]), "here": 100 * share[k],
                         "all": 100 * allshare[k], "lift": lift[k]})
    d = pd.DataFrame(rows)
    # order bars within each panel; a plain category order would interleave them
    d["key"] = d.panel + "||" + d.skill
    d["rank"] = np.where(d.panel.eq("Required most often"), d.here, d.lift)
    order = d.sort_values(["panel", "rank"]).key.tolist()
    d["key"] = pd.Categorical(d.key, categories=order, ordered=True)
    d["panel"] = pd.Categorical(d.panel, categories=["Required most often",
                                                     "Most over-represented in this title"],
                                ordered=True)

    p = (ggplot(d, aes("key", "here"))
         + geom_col(fill=BLUE, width=0.68)
         + geom_point(aes("key", "all", color='"All ads in the sample"'), shape="D", size=2.1)
         # the bar order differs per panel, so the axis key carries the panel; strip it for display
         + coord_flip()
         # stacked, not side by side: two panels in one row render too small
         + facet_wrap("~panel", ncol=1, scales="free_y")
         + scale_color_manual(values=[VERMILLION])
         + scale_x_discrete(labels=lambda ks: [k.split("||")[1] for k in ks])
         + scale_y_continuous(limits=(0, 100), breaks=[0, 25, 50, 75, 100])
         + labs(title=f"{fam}: what the ads require",
                subtitle=f"Share of the {len(g):,} {fam} ads requiring each skill (bar), against the "
                         f"share across all {N:,} ads (diamond).\nTop: most required here. Bottom: "
                         f"most over-represented here compared with every other title.",
                caption=f"n = {len(g):,} {fam} ads of {N:,}. {SOURCE}", x="", y="% of ads")
         + BASE + theme(figure_size=(8.2, 8.6)))
    out = IMG / f"title-{slug(fam)}.png"
    p.save(out, dpi=200, verbose=False)
    print(f"  wrote {out.name}")


def build_vs_call() -> None:
    """A dumbbell, not grouped bars: the question is the *shift* from building a
    model to calling one as the titles get newer, and an arrow from one dot to
    the other shows that in a way paired bars do not (owner, 2026-10-08)."""
    rows = []
    for fam in ORDER:
        g = df[df.family == fam]
        tr = 100 * (g[[f"req_{s}" for s in TRAIN]].sum(axis=1) > 0).mean()
        ca = 100 * (g[[f"req_{s}" for s in CALL]].sum(axis=1) > 0).mean()
        rows.append({"family": fam, "build": tr, "call": ca, "n": len(g)})
    w = pd.DataFrame(rows)
    w["family"] = pd.Categorical(w.family, categories=list(reversed(ORDER)), ordered=True)
    w["dir"] = np.where(w.call >= w.build, "Calls more than it builds", "Builds more than it calls")
    long = w.melt(id_vars=["family"], value_vars=["build", "call"],
                  var_name="kind", value_name="pct")
    long["kind"] = long.kind.map({"build": "Builds or trains a model",
                                  "call": "Calls a model over an API"})
    long["kind"] = pd.Categorical(long.kind, categories=["Builds or trains a model",
                                                         "Calls a model over an API"], ordered=True)

    p = (ggplot()
         # plain connector: an arrow head renders at the wrong angle under
         # coord_flip, and the two dots already carry the direction
         + geom_segment(w, aes("family", "build", xend="family", yend="call"),
                        color=GREY, size=1.0)
         + geom_point(long, aes("family", "pct", fill="kind", shape="kind"),
                      size=3.4, color="white", stroke=0.5)
         + coord_flip()
         + scale_fill_manual(values=[BLUE, VERMILLION])
         + scale_shape_manual(values=["o", "D"])
         + scale_y_continuous(limits=(0, 100), breaks=[0, 25, 50, 75, 100])
         + labs(title="As the titles get newer, the job shifts from building models to calling them",
                subtitle="Each line joins the share of a title's ads requiring that a model be built "
                         "or trained to the share requiring that\none be called over an API. Titles in "
                         "the approximate order each entered data and AI hiring, oldest at the top.",
                caption=f"Building = classical ML, deep learning, fine-tuning, computer vision, "
                        f"recommenders. Calling = LLM applications, retrieval, agents, observability.\n"
                        f"n = {N:,} de-duplicated job ads, Apr\u2013Oct 2026. {SOURCE}",
                x="", y="% of that title's ads")
         + BASE + theme(figure_size=(9, 5.4)))
    out = IMG / "build-vs-call.png"
    p.save(out, dpi=200, verbose=False)
    print(f"  wrote {out.name}")


if __name__ == "__main__":
    build_vs_call()
    for fam in ORDER:
        title_figure(fam)
