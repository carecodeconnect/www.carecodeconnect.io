"""UpSet plots, which this page uses instead of Venn diagrams.

A three-set Venn has seven regions, and the only way to say which region is
which is position — so each region ends up labelled with a bare percentage and
the reader has to decode the geometry to learn what it counts. Area is not
proportional either, unless the circles are redrawn, and then they stop being
readable. An UpSet plot says the same thing in words: one row per combination,
a matrix showing which sets are in it, the share and the count, and room for a
label such as the job title most common there.

draw(): one figure, built from boolean masks over the same index, so the plot
and the page's variables are computed from the same data.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
from palette import INK, INK_MUTED

GRID = "#dcdcd8"


def draw(sets: dict[str, "pandas.Series"], *, title: str, subtitle: str = "", caption: str = "",
         annot: dict[tuple[str, ...], str] | None = None, annot_header: str = "",
         value_label: str = "% of job ads", min_pct: float = 0.5, outfile=None,
         colour: str = "#0072B2", figsize=(10.4, 6.0)):
    names = list(sets)
    n = len(next(iter(sets.values())))
    combos = []
    for bits in range(1, 2 ** len(names)):
        members = tuple(nm for i, nm in enumerate(names) if bits >> i & 1)
        m = None
        for i, nm in enumerate(names):
            s = sets[nm] if bits >> i & 1 else ~sets[nm]
            m = s if m is None else (m & s)
        if 100 * m.mean() >= min_pct:
            combos.append((members, m.sum(), 100 * m.mean()))
    combos.sort(key=lambda c: c[1], reverse=True)

    rows = len(combos)
    fig, (axm, axb) = plt.subplots(1, 2, figsize=figsize, sharey=True,
                                   gridspec_kw={"width_ratios": [1, 2.5], "wspace": 0.04})
    ys = list(range(rows))[::-1]

    # membership matrix
    for xi, nm in enumerate(names):
        for y, (members, _, _) in zip(ys, combos):
            on = nm in members
            axm.scatter(xi, y, s=118, color=colour if on else "#e2e2de",
                        edgecolor="none", zorder=3)
        axm.text(xi, rows + 0.25, nm, rotation=28, ha="right", va="bottom",
                 fontsize=9, color=INK_MUTED, rotation_mode="anchor")
    for y, (members, _, _) in zip(ys, combos):
        on = [i for i, nm in enumerate(names) if nm in members]
        if len(on) > 1:
            axm.plot([min(on), max(on)], [y, y], color=colour, lw=2.2, zorder=2)
    axm.set_xlim(-0.6, len(names) - 0.4); axm.set_ylim(-0.7, rows + 1.5)
    axm.set_axis_off()

    # bars, each labelled in words
    for y, (members, cnt, pc) in zip(ys, combos):
        axb.barh(y, pc, color=colour, height=0.6)
        # The matrix on the left already says WHICH sets a row is, so repeating the
        # names here only overflows the axis. Where there is an annotation it earns
        # the space instead; where there is not, the names are the only text there
        # is, and a bare percentage is not a label.
        extra = (annot or {}).get(members, "")
        if not extra:
            extra = " + ".join(members) if len(members) > 1 else f"{members[0]} only"
        axb.text(pc + 1.0, y, f"{pc:.0f}%   {cnt:,} job ads · {extra}",
                 va="center", fontsize=9.5, color=INK)
    # Fit the axis to the longest row label rather than a guessed multiplier, or
    # the top row — always the longest bar and often the longest text — runs off.
    longest = max(len(f"{pc:.0f}%   {cnt:,} job ads · "
                      + ((annot or {}).get(m) or (" + ".join(m) if len(m) > 1 else f"{m[0]} only")))
                  for m, cnt, pc in combos)
    biggest = max(c[2] for c in combos)
    axb.set_xlim(0, biggest + longest * biggest * 0.021 + 4)
    axb.set_ylim(-0.7, rows + 1.5)
    axb.set_xlabel(value_label, color=INK_MUTED, fontsize=9.5)
    axb.tick_params(axis="x", colors=INK_MUTED, labelsize=9)
    axb.tick_params(axis="y", left=False, labelleft=False)
    for sp in ("top", "right", "left"):
        axb.spines[sp].set_visible(False)
    axb.spines["bottom"].set_color(GRID)

    fig.suptitle(title, fontsize=14.5, fontweight="bold", color=INK, x=0.015, ha="left", y=0.985)
    head = subtitle + (f"  {annot_header}" if annot_header else "")
    if head:
        fig.text(0.015, 0.905, head, fontsize=9.5, color=INK_MUTED, ha="left", va="top")
    if caption:
        # wrapped and left-aligned: a one-line source note runs off the figure
        import textwrap as _tw
        fig.text(0.012, 0.012, "\n".join(_tw.wrap(caption, 118)),
                 fontsize=8.5, color=INK_MUTED, ha="left", va="bottom")
    fig.subplots_adjust(top=0.74, bottom=0.22, left=0.10, right=0.985)
    if outfile:
        fig.savefig(outfile, dpi=200, facecolor="white")
    return fig
