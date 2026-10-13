"""Colour-blind-safe palette for every jobcrawler / carecodeconnect figure (owner, 2026-10-06).

Okabe & Ito (2008) hues, validated with the dataviz skill's validate_palette.js on
plotnine theme_grey's #ebebeb panel:
  * BLUE vs VERMILLION (every two-series plot): all checks pass, ΔE ≥ 21.9 under
    protan/deutan/tritan simulation.
  * BLUE, VERMILLION, GREEN (Venn) and PURPLE, BLUE, VERMILLION (+ grey "neither" for
    the all-skills scatter): all pairs pass.
  * Eight job-title families cannot all be mutually distinct for colour-blind readers
    (no 8-hue palette passes the all-pairs check), so family plots ALSO vary the marker
    shape (FAMILY_SYMBOL) — colour never carries identity alone.
The previous palette (#2a78d6 / #eb6834 / #1baf7a / #008300 / #e34948 …) failed:
green↔orange ΔE 3.2 (protan) and red↔orange 7.1 even with normal vision.
"""
BLUE = "#0072B2"          # series 1 — Data Scientist
VERMILLION = "#D55E00"    # series 2 — AI Engineer
GREEN = "#009E73"         # series 3 — ML Engineer
ORANGE = "#E69F00"
PURPLE = "#CC79A7"        # reddish purple
SKY = "#56B4E9"
BROWN = "#8C564B"
DARK = "#333333"
BLUE_LIGHT = "#9fc5e8"    # BLUE's lighter step (nice-to-have segment of a stacked bar)
GREY = "#8a8a86"          # "neither" / connector lines
INK, INK_MUTED, PANEL = "#0b0b0b", "#52514e", "#ebebeb"

WINE = "#882255"          # Paul Tol muted — the 9th slot (Analytics Engineer, added 2026-10-07)
TEAL = "#44AA99"          # Paul Tol muted — the 10th slot (AI Automation, added 2026-10-13)
# NOTE: this list orders and colours the families; it must never DECIDE which exist.
# Every consumer derives its families from the data and looks colours up here, because
# a hardcoded list silently dropped AI Automation from the interactive map and from the
# per-title charts on the day it was added.
FAMILIES = ["Data Scientist", "AI Engineer", "ML Engineer", "Data Analyst", "Data Engineer",
            "Research Scientist", "Forward Deployed", "Quantitative Researcher", "Analytics Engineer",
            "AI Automation"]
FAMILY_COLOUR = dict(zip(FAMILIES, [BLUE, VERMILLION, GREEN, ORANGE, PURPLE, SKY, BROWN, DARK, WINE, TEAL]))
# plotly symbol names; matplotlib/plotnine equivalents in FAMILY_SHAPE. Nine hues cannot
# all be mutually distinct under CVD simulation, which is exactly why every family plot
# also varies the marker shape — colour never carries identity on its own here.
FAMILY_SYMBOL = dict(zip(FAMILIES, ["circle", "diamond", "square", "triangle-up", "cross", "x",
                                    "triangle-down", "star", "pentagon", "hexagon"]))
FAMILY_SHAPE = dict(zip(FAMILIES, ["o", "D", "s", "^", "P", "X", "v", "*", "p", "h"]))

# Seniority is ORDINAL, so it gets a sequential single-hue ramp rather than
# categorical hues (dataviz rule: sequential = one hue, light->dark). Steps are
# evenly spaced in OKLab lightness (0.95 -> 0.31) on the BLUE hue, which is what
# buys the separation: validate_palette.js reports every adjacent pair >= 15.3 ΔE
# under protan/deutan/tritan and >= 15.7 with normal vision. The light steps sit
# below 3:1 against the panel, so any chart using them must label its segments.
SENIORITY_RAMP = ["#DFF1FF", "#92C0E8", "#4A8FC7", "#005F9E", "#00335A"]
SENIORITY_ORDER = ["entry", "mid", "senior", "staff or principal", "leadership"]
