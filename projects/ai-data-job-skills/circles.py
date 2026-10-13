"""The 2026 circles, derived from the ads rather than chosen.

The previous version of this diagram grouped the tracked skills into three
circles by hand, which made the picture an illustration of an argument rather
than a result. This module instead asks the data which skills employers ask for
*together*: the distance between two skills is 1 - their correlation across all
ads, and average-linkage clustering cuts that into four groups.

The four it finds are not the three that were drawn by hand, and the
differences are the point:

  - software engineering and LLM/agent work fall in ONE group, not two. Ads that
    want an LLM application overwhelmingly also want someone who can ship it.
  - the data-platform skills (SQL, dbt, pipelines, warehouse, BI, governance,
    streaming, Spark, orchestration) form a group of their own. The hand-drawn
    version had buried them inside "software engineering & deployment".
  - deep learning and computer vision sit with statistics and classical ML, not
    with LLM work — so the circle previously labelled new contained skills that
    predate LLMs by a decade.
  - communication, mentoring and customer-facing form a fourth group required by
    most ads of every title. It is drawn as the ground the circles stand on, not
    as a circle, because a circle that contains nearly everything separates
    nothing.

Both the figure and the page's numbers import from here, so they cannot drift.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.cluster.hierarchy import fcluster, linkage
from scipy.spatial.distance import squareform

K = 4  # three circles + the universal group


def _cluster(df: pd.DataFrame) -> dict[int, list[str]]:
    req = [c for c in df.columns if c.startswith("req_")]
    x = df[req].astype(float)
    d = 1 - np.nan_to_num(np.corrcoef(x.T.values))
    np.fill_diagonal(d, 0)
    d = (d + d.T) / 2          # guard against float asymmetry
    lab = fcluster(linkage(squareform(d, checks=False), "average"), K, criterion="maxclust")
    return {g: [req[i] for i in range(len(req)) if lab[i] == g] for g in sorted(set(lab))}


def circles(df: pd.DataFrame) -> dict[str, list[str]]:
    """The three circles plus the universal group, keyed by the name the page uses.

    Groups are identified by their content, never by cluster number, which is
    arbitrary and changes as the pool grows."""
    grp = _cluster(df)
    has = lambda g, *ids: any(c[4:] in ids for c in grp[g])
    ground = min(grp, key=lambda g: len(grp[g]))                       # the 3-skill soft group
    data = next(g for g in grp if g != ground and has(g, "dbt_modelling", "warehouse"))
    inference = next(g for g in grp if g not in (ground, data) and has(g, "statistics", "causal_inference"))
    eng = next(g for g in grp if g not in (ground, data, inference))
    return {
        "Engineering, deployment & AI": grp[eng],
        "Data platform": grp[data],
        "Statistics & inference": grp[inference],
        "_ground": grp[ground],
    }


def masks(df: pd.DataFrame) -> dict[str, pd.Series]:
    """One boolean per group: does this ad require at least one of its skills."""
    return {k: df[v].sum(axis=1) > 0 for k, v in circles(df).items()}
