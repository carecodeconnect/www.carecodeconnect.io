#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["plotly>=5.18", "pandas>=2.2"]
# ///
"""Interactive skills map for the AI / Data Job Skills project page.

Reads data/ai-data-job-skills.csv (one row per de-duplicated job ad: title, title
family, hiring region, month, t-SNE position, and a 0/1 required flag per skill)
and writes cluster.html, a self-contained Plotly page embedded by index.qmd.
Styled after plotnine's theme_grey so it matches the static charts.
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

HERE = Path(__file__).resolve().parent
df = pd.read_csv(HERE / "data" / "ai-data-job-skills.csv")
req_cols = [c for c in df.columns if c.startswith("req_")]
import json
VOCAB = json.load(open(HERE / "data" / "skills.json"))          # exported with the CSV by jobcrawler
LABEL = {f"req_{v['id']}": v["label"] for v in VOCAB}
AREA: dict[str, list[str]] = {}
for v in VOCAB:
    AREA.setdefault(v["area"], []).append(v["id"])
from palette import FAMILIES as _CANON, FAMILY_COLOUR as COLOUR, FAMILY_SYMBOL, INK, INK_MUTED, PANEL   # Okabe-Ito + shapes

def top_skills(row) -> str:
    on = [LABEL[c] for c in req_cols if row[c] == 1]
    return ", ".join(on[:6]) + (f" (+{len(on) - 6} more)" if len(on) > 6 else "") if on else "none named"

df["hover"] = [f"<b>{t}</b><br>{f} · {r} · {m}<br><i>requires:</i> {s}"
               for t, f, r, m, s in zip(df["title"], df["family"], df["region"], df["month"], df.apply(top_skills, axis=1))]

fig = go.Figure()
# Families present in the data, in the canonical order, plus any the palette does
# not know — so a new family is drawn even before it is added to palette.py.
_present = list(df["family"].unique())
FAMILIES = [f for f in _CANON if f in _present] + [f for f in _present if f not in _CANON]
for fam in FAMILIES:
    d = df[df["family"] == fam]
    fig.add_trace(go.Scattergl(
        x=d["x"], y=d["y"], mode="markers", name=f"{fam} ({len(d):,})",
        # Colour-blind readers cannot tell eight hues apart, so each title also has its own
        # marker shape — identity is never carried by colour alone.
        marker=dict(size=7, color=COLOUR[fam], symbol=FAMILY_SYMBOL[fam], opacity=0.75, line=dict(width=0.5, color=PANEL)),
        text=d["hover"], hovertemplate="%{text}<extra></extra>", customdata=d[req_cols].values))

# "Highlight a skill area" menu: dims every job that does not require a skill in the area.
buttons = [dict(label="All jobs", method="restyle",
                args=[{"marker.opacity": [0.75] * len(FAMILIES)}])]
for area, ids in AREA.items():
    cols = [f"req_{i}" for i in ids if f"req_{i}" in df.columns]
    ops = []
    for fam in FAMILIES:
        d = df[df["family"] == fam]
        hit = (d[cols].sum(axis=1) > 0).to_numpy()
        ops.append([0.85 if h else 0.08 for h in hit])
    share = 100 * (df[cols].sum(axis=1) > 0).mean()
    buttons.append(dict(label=f"{area} ({share:.0f}% of jobs)", method="restyle", args=[{"marker.opacity": ops}]))

fig.update_layout(
    title=dict(text="<b>Where each data & AI job sits on the skills map</b><br>"
                    "<span style='font-size:13px;color:#52514e'>One dot per job ad, placed by the skills it requires "
                    "(t-SNE: nearby dots have similar requirements). Each title has its own colour <i>and</i> marker shape.<br>Click a title in the legend to hide it; "
                    "pick a skill area above right to see where it concentrates.</span>",
               x=0, xanchor="left", font=dict(size=18, color=INK)),
    paper_bgcolor="white", plot_bgcolor=PANEL,
    font=dict(family="Helvetica, Arial, sans-serif", color="#4d4d4d", size=12),
    xaxis=dict(showgrid=True, gridcolor="white", zeroline=False, showticklabels=False, title=""),
    yaxis=dict(showgrid=True, gridcolor="white", zeroline=False, showticklabels=False, title="", scaleanchor="x"),
    # yanchor="top", not "bottom": with ten families the horizontal legend wraps
    # to two rows, and anchored at its bottom it grew UPWARD into the panel and
    # collided with the source credit at y=0.01 (owner, 2026-10-13). Anchored at
    # its top it grows downward into the margin, which is sized for it below.
    legend=dict(orientation="h", yanchor="top", y=-0.02, x=0, title=dict(text="")),
    updatemenus=[dict(type="dropdown", buttons=buttons, x=1.0, xanchor="right", y=1.12, yanchor="bottom",
                      bgcolor="white", bordercolor="#c8c8c8", font=dict(size=12))],
    # b=140 leaves room for the two legend rows plus the caption beneath them.
    margin=dict(l=20, r=20, t=130, b=140), height=760, hoverlabel=dict(bgcolor="white", font_size=12),
)
fig.add_annotation(text=f"n = {len(df):,} de-duplicated job ads with a data / AI title, hiring in Germany, EU-wide, "
                        "worldwide-remote or the UK, Apr–Oct 2026.", xref="paper", yref="paper", x=0, y=-0.21,
                   showarrow=False, font=dict(size=11, color=INK_MUTED), xanchor="left")
fig.add_annotation(text="www.carecodeconnect.io", xref="paper", yref="paper", x=0.995, y=0.01,
                   showarrow=False, font=dict(size=11, color=INK_MUTED), xanchor="right", yanchor="bottom")
out = HERE / "cluster.html"
fig.write_html(out, include_plotlyjs="cdn", full_html=True, config=dict(displaylogo=False, responsive=True))
print(f"wrote {out.relative_to(HERE.parent.parent)} ({out.stat().st_size // 1024} KB)")
