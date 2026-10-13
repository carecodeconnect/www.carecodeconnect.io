#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2", "numpy>=1.26", "plotnine>=0.13"]
# ///
"""Seniority: the whole sample, and each title family against it.

  images/seniority.png   one stacked bar per title family plus an "All job ads"
                         bar, so the cross-role picture and the per-role one are
                         read off the same axis.

Seniority is ORDINAL, so it gets a sequential single-hue ramp (palette.py's
SENIORITY_RAMP) rather than categorical hues. Its light steps fall below 3:1
against the panel, which obliges visible labels — every segment wide enough to
hold one carries its percentage, and the five levels are also ordered
left-to-right, so colour never carries the identity on its own.

Figures are written to _variables.yml by build_stats.py, not here; this file
draws, and prints the numbers it drew so they can be eyeballed (owner, 2026-10-13).
"""
from pathlib import Path

import pandas as pd
from plotnine import (aes, coord_flip, element_blank, element_text, geom_col, geom_text,
                      ggplot, labs, scale_color_manual, scale_fill_manual, scale_x_discrete,
                      scale_y_continuous, theme, theme_grey)

from palette import INK_MUTED, SENIORITY_RAMP, SENIORITY_ORDER

HERE = Path(__file__).resolve().parent
IMG = HERE / "images"
ALL = "All job ads"
# The judge's own labels; "staff_principal" is the only one that needs prettying.
PRETTY = {"entry": "entry", "mid": "mid", "senior": "senior",
          "staff_principal": "staff or principal", "leadership": "leadership"}

df = pd.read_csv(HERE / "data" / "ai-data-job-skills.csv")
if "seniority" not in df.columns:
    raise SystemExit("ai-data-job-skills.csv has no seniority column — re-run "
                     "jobcrawler's scripts/eda-export.sh first.")
df = df[df["seniority"].notna()].copy()
df["level"] = df["seniority"].map(PRETTY)
if df["level"].isna().any():
    raise SystemExit(f"unmapped seniority levels: {sorted(df.loc[df['level'].isna(), 'seniority'].unique())}")

# Families ordered by their senior-and-above share, so the chart itself makes the
# ranking visible; the all-ads bar is pinned to the top as the reference.
SENIOR_PLUS = ["senior", "staff or principal", "leadership"]
rows = []
for fam, g in list(df.groupby("family")) + [(ALL, df)]:
    share = g["level"].value_counts(normalize=True)
    for lv in SENIORITY_ORDER:
        rows.append({"family": fam, "level": lv, "pct": 100 * share.get(lv, 0.0),
                     "n": int((g["level"] == lv).sum()), "total": len(g)})
s = pd.DataFrame(rows)

rank = (s[s["level"].isin(SENIOR_PLUS)].groupby("family")["pct"].sum().sort_values())
order = [f for f in rank.index if f != ALL] + [ALL]
s["family"] = pd.Categorical(s["family"], categories=order, ordered=True)
# plotnine stacks the LAST category at the START of the bar, so the categories go
# in reversed order to put entry (lightest) on the left and leadership (darkest)
# on the right. scale_fill_manual's `limits` keeps the legend in reading order.
s["level"] = pd.Categorical(s["level"], categories=list(reversed(SENIORITY_ORDER)), ordered=True)
# A segment narrower than this cannot hold its own label legibly; leaving it bare
# is why the caption says so. The "%" lives in the label, not in a format_string,
# which would otherwise stamp a lone "%" onto every unlabelled segment.
s["label"] = [f"{v:.0f}%" if v >= 6 else "" for v in s["pct"]]
# Ink on the three light steps, white on the two dark ones. The ramp is designed
# to span the lightness range, which is exactly what makes a single label colour
# unreadable at one end of it.
DARK_STEPS = {"staff or principal", "leadership"}
s["ink"] = ["light" if lv in DARK_STEPS else "dark" for lv in s["level"]]
# The label's position is computed, not left to position="stack". Adding a colour
# aesthetic to geom_text re-groups it, and a re-grouped text stack silently puts
# every label on the wrong segment — so the midpoint is derived from the same
# ordering the bars use.
# Key the cumulative sum to the DISPLAY order (entry first, leftmost), not to the
# categorical order, which is reversed for the fill stack and would run the labels
# the other way down the bar.
s["_ord"] = [SENIORITY_ORDER.index(lv) for lv in s["level"]]
s = s.sort_values(["family", "_ord"])
s["pos"] = s.groupby("family", observed=True)["pct"].cumsum() - s["pct"] / 2

# The headline states the sample-wide senior-and-above share, so it is computed,
# never typed: an earlier draft said "two in three" and would have gone stale the
# first time the pool moved.
# No figure in a plot title (owner, 2026-10-13) — the percentages are in the
# segments. The title carries the take-home, and which take-home it is still
# follows from the data rather than from what was true the day it was written.
SP_SHARE = s[(s["family"] == ALL) & (s["level"].isin(SENIOR_PLUS))]["pct"].sum()
HEADLINE = ("Most of these job ads ask for senior or above, in every title"
            if SP_SHARE >= 50 else
            "These job ads are mostly pitched below senior, in every title")

lab = (s.assign(fam=s["family"].astype(str))
        .drop_duplicates("fam")[["fam", "total"]].set_index("fam")["total"])
g = (ggplot(s, aes("family", "pct", fill="level"))
     + geom_col(width=0.72)
     + geom_text(aes(y="pos", label="label", color="ink"), ha="center",
                 va="center", size=7.5, show_legend=False)
     + scale_color_manual(values={"dark": "#0b0b0b", "light": "#FFFFFF"})
     + coord_flip()
     + scale_fill_manual(values=dict(zip(SENIORITY_ORDER, SENIORITY_RAMP)),
                         limits=SENIORITY_ORDER)
     # No explicit limits: the stack sums to 100 only up to floating point, and a
     # hard (0, 100) silently drops the segment that lands a hair above it.
     + scale_y_continuous(expand=(0.045, 0))
     + scale_x_discrete(labels=[f"{f}  (n = {lab[f]:,})" for f in order])
     + labs(title=HEADLINE,
            subtitle="Share of each title family's job ads at each seniority level, read from the ad by the "
                     "same judge that scores the skills.\nLevels run entry (lightest) to leadership (darkest).",
            caption=f"n = {len(df):,} de-duplicated job ads with a data / AI title, hiring in Germany, EU-wide, "
                    "worldwide-remote or the UK.\nSegments below 6% are left unlabelled. "
                    "Seniority is the judge's reading of the ad, not a stated field.",
            x="", y="% of the title family's job ads")
     + theme_grey(base_size=10)
     + theme(figure_size=(9.2, 5.4), plot_title=element_text(weight="bold", size=12),
             plot_subtitle=element_text(color=INK_MUTED, size=8.5),
             plot_caption=element_text(color=INK_MUTED, size=7.5, ha="left"),
             panel_grid_major_y=element_blank(), legend_title=element_blank(),
             legend_position="top", axis_text_y=element_text(size=8.5)))
out = IMG / "seniority.png"
g.save(out, dpi=200, verbose=False)
print(f"  wrote {out.relative_to(HERE)}")
for f in reversed(order):
    r = s[s["family"] == f].set_index("level")["pct"]
    print(f"    {f:28s} " + "  ".join(f"{lv[:4]} {r[lv]:4.1f}%" for lv in SENIORITY_ORDER))
