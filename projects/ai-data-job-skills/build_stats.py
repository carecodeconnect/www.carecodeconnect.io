#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2", "numpy>=1.26", "scipy>=1.11"]
# ///
"""Every number the page quotes, computed from the published CSV and written to
`_variables.yml` for Quarto to interpolate.

Why: the prose used to carry hand-typed percentages. Each re-judge or vocabulary
change silently made a dozen of them wrong, and the only guard was remembering
to re-check every sentence. Now the page holds `{{< var jobskills.x >}}` and the
figures regenerate with the data. If a number appears in the text, it is defined
HERE — never typed into index.qmd.

Owns the whole `jobskills:` block, so it is the single writer of _variables.yml.
Run it after scripts/skill-clusters.py has refreshed the CSV."""
from __future__ import annotations

import datetime as dt
import itertools
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
WWW = HERE.parent.parent
df = pd.read_csv(HERE / "data" / "ai-data-job-skills.csv")
VOCAB = json.load(open(HERE / "data" / "skills.json"))
LABEL = {v["id"]: v["label"] for v in VOCAB}
REQ = [c for c in df.columns if c.startswith("req_")]
rate = df.groupby("family")[REQ].mean().mul(100)
counts = df["family"].value_counts()

AREA: dict[str, list[str]] = {}
for v in VOCAB:
    AREA.setdefault(v["area"], []).append(v["id"])


def key(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# Labels are title-cased for chart axes ("Model serving"), which reads wrong
# mid-sentence. Lowercase the first word unless it is a name or an acronym —
# "Python", "SQL", "R", "dbt modelling" must keep their case.
PROPER = {"python", "sql", "r", "rag", "nlp", "bi", "mlops", "llm", "ci", "rust",
          "scala", "java", "typescript", "spark", "dbt", "recsys", "genai", "ml", "ai"}


def sentence(label: str) -> str:
    head = label.split()[0]
    if head.isupper() or head.lower() in PROPER or not head[0].isupper():
        return label
    return label[0].lower() + label[1:]


out: dict[str, object] = {
    "n_ads": f"{len(df):,}",
    "n_skills": len(REQ),
    "n_areas": len(AREA),
    "n_titles": len(counts),
    "vocab_date": pd.Timestamp.today().strftime("%Y-%m-%d"),
    "months": f"{df['month'].min()} to {df['month'].max()}",
}

# ── per-title counts and shares ──────────────────────────────────────────────
for fam, n in counts.items():
    out[f"n_{key(fam)}"] = f"{n:,}"
    out[f"pct_{key(fam)}"] = f"{100 * n / len(df):.0f}"

# ── pairwise distances between requirement profiles ──────────────────────────
fams = list(rate.index)
dist = {
    tuple(sorted((a, b))): float(np.linalg.norm((rate.loc[a].values - rate.loc[b].values) / 100))
    for a, b in itertools.combinations(fams, 2)
}
for (a, b), v in dist.items():
    out[f"d_{key(a)}__{key(b)}"] = f"{v:.2f}"
# nearest neighbour of each title, by name and distance
for f in fams:
    near = sorted(((v, (a if b == f else b)) for (a, b), v in dist.items() if f in (a, b)))[0]
    out[f"near_{key(f)}"] = near[1]
    out[f"near_d_{key(f)}"] = f"{near[0]:.2f}"
closest = min(dist.items(), key=lambda kv: kv[1])
out["closest_pair_a"], out["closest_pair_b"] = closest[0]
out["closest_pair_d"] = f"{closest[1]:.2f}"

# ── per-skill shares, overall and per title ──────────────────────────────────
overall = df[REQ].mean().mul(100).sort_values(ascending=False)
for i, (c, v) in enumerate(overall.items(), 1):
    if i <= 8:
        out[f"top{i}_skill"] = sentence(LABEL.get(c[4:], c[4:]))
        out[f"top{i}_pct"] = f"{v:.0f}"
for c, v in overall.items():
    out[f"all_{c[4:]}"] = f"{v:.0f}"
tail = list(overall.items())[-5:]
out["tail_skills"] = ", ".join(f"{sentence(LABEL.get(c[4:], c[4:]))} {v:.0f}%" for c, v in tail)
for fam in fams:
    for c in REQ:
        out[f"{key(fam)}_{c[4:]}"] = f"{rate.loc[fam, c]:.0f}"

# ── skill AREAS, Data Scientist vs AI Engineer ───────────────────────────────
for area, ids in AREA.items():
    cols = [f"req_{i}" for i in ids if f"req_{i}" in df.columns]
    if not cols:
        continue
    for fam in ("Data Scientist", "AI Engineer"):
        d = df[df["family"] == fam]
        out[f"area_{key(area)}_{key(fam)}"] = f"{100 * (d[cols].sum(axis=1) > 0).mean():.0f}"

# ── odds and ends the prose leans on ─────────────────────────────────────────
out["ai_no_python"] = f"{100 * (df.loc[df.family == 'AI Engineer', 'req_python'] == 0).mean():.0f}"
CORE = 30
core = {f: {c[4:] for c in REQ if rate.loc[f, c] >= CORE} for f in fams}
out["core_pct"] = CORE
shared = core["Data Scientist"] & core["AI Engineer"] & core["ML Engineer"]
out["core_shared"] = ", ".join(sorted(sentence(LABEL.get(s, s)) for s in shared))
out["n_core_shared"] = len(shared)
out["n_core_ds_ai"] = len(core["Data Scientist"] & core["AI Engineer"])

# ── does an inference background transfer to AI-engineering work? ────────────
# Asked directly (owner, 2026-10-08): does a Data Scientist's statistics help
# with evals, and with LLMOps? Measured WITHIN the engineering families, because
# across the whole pool the family mix hides it — a textbook Simpson's paradox.
eng = df[df.family.isin(["AI Engineer", "ML Engineer"])]
out["n_eng_ads"] = f"{len(eng):,}"
for a, b, name in [("model_evaluation", "experimentation", "evals_ab"),
                   ("model_evaluation", "statistics", "evals_stats"),
                   ("llm_observability", "statistics", "obs_stats"),
                   ("model_evaluation", "llm_observability", "evals_obs")]:
    A, B = f"req_{a}", f"req_{b}"
    base = eng[B].mean()
    given = eng[eng[A] == 1][B].mean()
    out[f"lift_{name}"] = f"{given / base:.1f}" if base else "n/a"
    out[f"pct_{name}_given"] = f"{given * 100:.0f}"
    out[f"pct_{name}_base"] = f"{base * 100:.0f}"
# the reverse direction, which is the one a job-seeker cares about
base_ev = eng["req_model_evaluation"].mean()
out["pct_evals_base_eng"] = f"{base_ev * 100:.0f}"
for src, name in [("experimentation", "from_ab"), ("statistics", "from_stats"), ("product_analytics", "from_prodanalytics")]:
    c = f"req_{src}"
    out[f"pct_evals_{name}"] = f"{eng[eng[c] == 1]['req_model_evaluation'].mean() * 100:.0f}"

# ── Conway's 2010 Venn, measured (see build_conway.py for the mapping) ───────
CONWAY = {
    "hacking": ["python", "sql", "r", "scala_java", "typescript", "systems_lang",
                "software_engineering", "apis_services", "cicd_testing", "containers", "cloud",
                "mlops_tooling", "model_serving", "pipelines_etl", "orchestration",
                "spark_distributed", "streaming", "warehouse", "dbt_modelling"],
    "maths": ["statistics", "experimentation", "causal_inference", "forecasting", "time_series",
              "quant_research", "classical_ml", "deep_learning", "nlp", "computer_vision",
              "recsys_ranking"],
    "domain": ["stakeholder_comms", "customer_facing", "product_analytics", "research",
               "bi_dashboards", "data_governance"],
}
mem = {}
for k, ids in CONWAY.items():
    cols = [f"req_{i}" for i in ids if f"req_{i}" in df.columns]
    mem[k] = df[cols].sum(axis=1) > 0
H, M, S = mem["hacking"], mem["maths"], mem["domain"]
for label, mask in [("all_three", H & M & S), ("danger_zone", H & ~M & S),
                    ("ml_only", H & M & ~S), ("trad_research", ~H & M & S)]:
    out[f"conway_{label}"] = f"{100 * mask.mean():.0f}"
# the part Conway has no circle for: the GenAI stack
GENAI = ["llm_apps", "agents", "rag", "model_evaluation", "fine_tuning", "llm_observability",
         "responsible_ai"]
gcols = [f"req_{g}" for g in GENAI if f"req_{g}" in df.columns]
gen = df[gcols].sum(axis=1) > 0
out["conway_outside_pct"] = f"{100 * gen.mean():.0f}"
out["conway_outside_n"] = f"{len(gcols)}"
for fam in ["AI Engineer", "Data Scientist", "Data Analyst", "Data Engineer"]:
    out[f"genai_{key(fam)}"] = f"{100 * gen[df.family == fam].mean():.0f}"

# ── our own 2026 Venn (circles defined in build_conway.py — keep in step) ────
# The diagram no longer prints percentages, so every region share quoted on the
# page comes from here (owner, 2026-10-08).
OURS = {
    "swe": ["software_engineering", "apis_services", "cicd_testing", "containers", "cloud",
            "mlops_tooling", "model_serving", "pipelines_etl", "orchestration",
            "spark_distributed", "streaming", "warehouse", "dbt_modelling", "typescript",
            "systems_lang", "scala_java"],
    "inference": ["statistics", "experimentation", "causal_inference", "forecasting",
                  "time_series", "quant_research", "classical_ml", "product_analytics",
                  "bi_dashboards"],
    "llm": ["llm_apps", "agents", "rag", "model_evaluation", "fine_tuning",
            "llm_observability", "responsible_ai", "nlp", "deep_learning"],
}
om = {}
for k, ids in OURS.items():
    cols = [f"req_{i}" for i in ids if f"req_{i}" in df.columns]
    om[k] = df[cols].sum(axis=1) > 0
A, B, C = om["swe"], om["inference"], om["llm"]
for label, mask in [("swe", A), ("inference", B), ("llm", C),
                    ("datascience", A & B & C), ("aieng", A & ~B & C),
                    ("analytics", A & B & ~C), ("research", ~A & B & C)]:
    out[f"v26_{label}"] = f"{100 * mask.mean():.0f}"
# The centre region is a PRACTICE, not the job title of the same name — a
# reader seeing "data science" in the middle will otherwise take it to mean
# Data Scientist ads require all three circles, and most of them do not.
# These three say who is actually in there.
out["v26_centre_data_scientist_titled"] = f"{100 * (df.family[A & B & C] == 'Data Scientist').mean():.0f}"
out["v26_centre_ai_engineer_titled"] = f"{100 * (df.family[A & B & C] == 'AI Engineer').mean():.0f}"
out["v26_data_scientist_in_centre"] = f"{100 * (A & B & C)[df.family == 'Data Scientist'].mean():.0f}"
out["v26_data_scientist_in_llm"] = f"{100 * C[df.family == 'Data Scientist'].mean():.0f}"

# AI Engineering is the heir to Conway's danger zone: shipping without inference.
out["v26_aieng_titled"] = f"{100 * (df.family[A & ~B & C] == 'AI Engineer').mean():.0f}"

# ── where did Conway's "machine learning" lens go? (owner, 2026-10-08) ───────
# Checked rather than assumed: the first draft claimed ML had "spread across all
# three circles", which the data contradicts — it is named in 1 ad in 5.
cml, dlrn = df.req_classical_ml == 1, df.req_deep_learning == 1
ml_any = cml | dlrn
LLMSTACK = ["llm_apps", "agents", "rag", "fine_tuning", "llm_observability"]
llm_stack = df[[f"req_{i}" for i in LLMSTACK if f"req_{i}" in df.columns]].sum(axis=1) > 0
for lab, m in [("classical", cml), ("deep", dlrn), ("any", ml_any),
               ("llmstack", llm_stack), ("llm_no_ml", llm_stack & ~ml_any),
               ("ml_no_llm", ml_any & ~llm_stack)]:
    out[f"ml_{lab}_pct"] = f"{100 * m.mean():.0f}"
out["ml_any_n"] = f"{int(ml_any.sum()):,}"
# ML ads are MORE engineering-bound than the rest, not less
out["ml_serving_pct"] = f"{100 * df.req_model_serving[ml_any].mean():.0f}"
out["ml_serving_rest_pct"] = f"{100 * df.req_model_serving[~ml_any].mean():.0f}"
out["ml_in_centre_pct"] = f"{100 * ((Hh_ := H & M & S)[ml_any]).mean():.0f}"
out["ml_in_conway_ml_pct"] = f"{100 * ((H & M & ~S)[ml_any]).mean():.0f}"
for fam in ["Data Scientist", "AI Engineer", "ML Engineer", "Research Scientist"]:
    g = df[df.family == fam]
    out[f"mlfam_{key(fam)}_classical"] = f"{100 * g.req_classical_ml.mean():.0f}"
    out[f"mlfam_{key(fam)}_deep"] = f"{100 * g.req_deep_learning.mean():.0f}"
    out[f"mlfam_{key(fam)}_llm"] = f"{100 * llm_stack[df.family == fam].mean():.0f}"

# ── building/training a model vs calling one over an API (owner, 2026-10-08) ─
# The vocabulary calls both "AI work"; the ads do not treat them as one job.
TRAIN_S = ["classical_ml", "deep_learning", "fine_tuning", "computer_vision", "recsys_ranking"]
CALL_S = ["llm_apps", "agents", "rag", "llm_observability"]
_tr = df[[f"req_{i}" for i in TRAIN_S if f"req_{i}" in df.columns]].sum(axis=1) > 0
_ca = df[[f"req_{i}" for i in CALL_S if f"req_{i}" in df.columns]].sum(axis=1) > 0
out["bc_train"] = f"{100 * _tr.mean():.0f}"
out["bc_call"] = f"{100 * _ca.mean():.0f}"
out["bc_both"] = f"{100 * (_tr & _ca).mean():.0f}"
out["bc_call_only"] = f"{100 * (_ca & ~_tr).mean():.0f}"
out["bc_train_only"] = f"{100 * (_tr & ~_ca).mean():.0f}"
out["bc_finetune"] = f"{100 * df.req_fine_tuning.mean():.0f}"
for _f in df.family.unique():
    _g = df.family == _f
    out[f"bc_{key(_f)}_train"] = f"{100 * _tr[_g].mean():.0f}"
    out[f"bc_{key(_f)}_call"] = f"{100 * _ca[_g].mean():.0f}"

# ── would "machine learning" earn a circle of its own? (owner, 2026-10-08) ──
# Tested rather than asserted, because readers ask why Conway's ML lens is gone.
MLSET = ["classical_ml", "deep_learning", "computer_vision", "recsys_ranking"]
mlc = df[[f"req_{i}" for i in MLSET if f"req_{i}" in df.columns]].sum(axis=1) > 0
out["mlc_pct"] = f"{100 * mlc.mean():.0f}"
out["mlc_n"] = f"{int(mlc.sum()):,}"
out["mlc_inside_any_pct"] = f"{100 * (mlc & (A | B | C))[mlc].mean():.1f}"
out["mlc_alone_n"] = f"{int((mlc & ~A & ~B & ~C).sum())}"
out["mlc_in_centre_pct"] = f"{100 * (mlc & A & B & C)[mlc].mean():.0f}"
for nm, X in [("swe", A), ("inf", B), ("llm", C)]:
    out[f"mlc_covers_{nm}"] = f"{100 * mlc[X].mean():.0f}"
# Conway's label, tested against his own region
out["conway_ml_label_fit"] = f"{100 * mlc[H & M & ~S].mean():.0f}"
out["conway_centre_ml_fit"] = f"{100 * mlc[H & M & S].mean():.0f}"

# ── data governance: the Analytics/Data Engineer branch vs everywhere else ───
# The executive summary contrasts that pair with the rest of the sample, so the
# "elsewhere" baseline needs a variable too — the per-family figures it sits
# beside already come from the family x skill loop above.
BRANCH = ["Analytics Engineer", "Data Engineer"]
out["data_governance_elsewhere"] = (
    f"{100 * df.loc[~df.family.isin(BRANCH), 'req_data_governance'].mean():.0f}"
)

# ── figures the published CSV cannot carry ───────────────────────────────────
# The CSV exports Jev's binary req_* flag and nothing else, so the Method
# section's two cross-checks — the open-vocabulary extraction totals, and the
# machine-learning agreement between Jev and Haiku — are exported from the Pi
# into these JSON files instead. They are read here rather than typed into the
# page, which keeps the rule: if a number appears in the text, it is defined in
# this script. Regenerate them with sql/mentions-summary.sql and
# sql/ml-crosscheck.sql.
def carry(name: str, prefix: str) -> None:
    f = HERE / "data" / f"{name}.json"
    if not f.exists():
        print(f"  WARNING: {f.name} missing — the page's {prefix}* vars will not resolve")
        return
    for k, v in json.load(open(f)).items():
        if k.startswith("_"):
            continue
        name = f"{prefix}{k}"
        assert name not in out, f"{f.name} key {k!r} would overwrite computed variable {name}"
        out[name] = f"{v:,}" if isinstance(v, int) and v >= 1_000 else v


carry("circles-2026", "c26_")
carry("mentions-summary", "mentions_")
carry("judge", "judge_")

# ── is "shipping" a separate skill set from "building"? (owner, 2026-10-08) ──
DEP = ["model_serving", "mlops_tooling", "containers", "cloud", "orchestration", "cicd_testing"]
BUILD = ["software_engineering", "apis_services", "typescript", "systems_lang", "scala_java"]
dcols = [f"req_{i}" for i in DEP if f"req_{i}" in df.columns]
bcols = [f"req_{i}" for i in BUILD if f"req_{i}" in df.columns]
dep, bld = df[dcols].sum(axis=1) > 0, df[bcols].sum(axis=1) > 0
out["pct_build_and_deploy"] = f"{100 * (dep & bld).mean():.0f}"
out["pct_build_only"] = f"{100 * (bld & ~dep).mean():.0f}"
out["pct_deploy_only"] = f"{100 * (dep & ~bld).mean():.0f}"
out["all_model_serving_pct"] = f"{100 * df['req_model_serving'].mean():.0f}"

# ── the title-distance diagram ───────────────────────────────────────────────
# Quarto does NOT expand `{{< var >}}` inside a ```{mermaid}``` block, so the
# numbers there cannot come from _variables.yml like the rest of the page. The
# whole block is generated here instead and spliced in with `{{< include >}}`,
# which keeps the rule intact: no figure in the page is typed by hand.
def nd(a: str, b: str) -> str:
    return out[f"d_{key(a)}__{key(b)}"]


def node(code: str, fam: str) -> str:
    return f'    {code}["{fam}<br/>n = {out["n_" + key(fam)]}"]'


MERMAID = f"""```{{mermaid}}
%%| fig-width: 7
%%| fig-height: 9
%%| fig-align: center
%%{{init: {{"theme": "neutral", "fontSize": 15, "flowchart": {{"curve": "basis", "nodeSpacing": 38, "rankSpacing": 55}}}}}}%%
flowchart TB
{node("QR", "Quantitative Researcher")}
{node("DS", "Data Scientist")}
{node("DA", "Data Analyst")}
{node("AE", "Analytics Engineer")}
{node("DE", "Data Engineer")}
{node("ML", "ML Engineer")}
{node("RS", "Research Scientist")}
{node("AI", "AI Engineer")}
{node("FD", "Forward Deployed")}
    QR ---|"{nd("Data Scientist", "Quantitative Researcher")}<br/>statistics, forecasting"| DS
    DA ---|"{nd("Data Analyst", "Data Scientist")}<br/>SQL, BI ↔ Python, classical ML"| DS
    AE ---|"{nd("Analytics Engineer", "Data Analyst")}<br/>dbt, pipelines ↔ BI, product analytics"| DA
    DE ---|"{nd("Analytics Engineer", "Data Engineer")}<br/>cloud, Spark ↔ SQL, dbt"| AE
    DS ---|"{nd("Data Scientist", "ML Engineer")}<br/>+ MLOps, serving, containers"| ML
    RS -. "{nd("ML Engineer", "Research Scientist")}<br/>research, experimentation ↔<br/>MLOps, serving, CI/CD" .- ML
    ML ---|"{nd("AI Engineer", "ML Engineer")}<br/>+ LLM apps, agents, NLP"| AI
    DS -. "{nd("AI Engineer", "Data Scientist")} direct" .- AI
    AI -. "{nd("AI Engineer", "Forward Deployed")}<br/>LLM apps, NLP ↔<br/>customer-facing, stakeholders" .- FD
    classDef inf fill:#dbe8f8,stroke:#0072B2,color:#0b0b0b;
    classDef eng fill:#fde3d8,stroke:#D55E00,color:#0b0b0b;
    classDef data fill:#e4dde9,stroke:#882255,color:#0b0b0b;
    classDef hinge fill:#0072B2,stroke:#0072B2,color:#ffffff;
    class QR,DA,DS inf;
    class AI,FD,RS eng;
    class AE,DE data;
    class ML hinge;
```
"""
mp = HERE / "_titles-diagram.qmd"
mp.write_text("<!-- GENERATED by build_stats.py — do not edit; Quarto cannot expand vars inside a mermaid block. -->\n" + MERMAID)
print(f"wrote {mp.name}")

# ── shipping vs modelling (owner, 2026-10-13) ───────────────────────────────
# Conway's "hacking skills" meant manipulating data with code. Today's ads ask
# for running the result in production. These measure how far that reaches,
# WITHOUT claiming when it arrived: the sample is one year and has no baseline.
SHIP = ["model_serving", "mlops_tooling", "containers", "cicd_testing", "cloud", "orchestration"]
AIML = ["classical_ml", "deep_learning", "nlp", "computer_vision", "llm_apps", "agents",
        "rag", "fine_tuning"]
_ship = df[[f"req_{i}" for i in SHIP if f"req_{i}" in df.columns]].sum(axis=1) > 0
_aiml = df[[f"req_{i}" for i in AIML if f"req_{i}" in df.columns]].sum(axis=1) > 0
# Shipping is an ADDITION to modelling, not a replacement — so the measure that
# matters is the conjunction, and the conditional: of the ads that ask for a
# model, how many also ask for it to run in production.
out["pct_model_and_ship"] = f"{100 * (_ship & _aiml).mean():.0f}"
out["pct_model_not_ship"] = f"{100 * (~_ship & _aiml).mean():.0f}"
for _f in ["Data Scientist", "AI Engineer", "ML Engineer"]:
    _m = df.family == _f
    out[f"both_{key(_f)}"] = f"{100 * (_ship & _aiml)[_m].mean():.0f}"
    out[f"ship_given_model_{key(_f)}"] = f"{100 * _ship[_m & _aiml].mean():.0f}"
    out[f"model_only_{key(_f)}"] = f"{100 * (~_ship & _aiml)[_m].mean():.0f}"
out["pct_ship_all"] = f"{100 * _ship.mean():.0f}"
out["pct_aiml_all"] = f"{100 * _aiml.mean():.0f}"
for _f in ["Data Scientist", "AI Engineer", "ML Engineer", "Data Engineer", "Data Analyst"]:
    _m = df.family == _f
    out[f"ship_{key(_f)}"] = f"{100 * _ship[_m].mean():.0f}"
    out[f"aiml_{key(_f)}"] = f"{100 * _aiml[_m].mean():.0f}"

# ── evals: the one engineering skill an inference background buys ───────────
# Asked 2026-10-13. Within the engineering titles, does requiring experimentation
# or statistics predict requiring evals — and does it predict LLMOps too? The
# odds ratios are what separate "travels together" from "is the same thing".
from scipy.stats import fisher_exact  # noqa: E402

_eng = df[df.family.isin(["AI Engineer", "ML Engineer"])]


def _odds(outcome: str, given: str) -> tuple[float, float]:
    c = _eng[f"req_{given}"] == 1
    o = _eng[f"req_{outcome}"] == 1
    return fisher_exact([[(o & c).sum(), (~o & c).sum()], [(o & ~c).sum(), (~o & ~c).sum()]])


for _out, _giv, _name in [("model_evaluation", "experimentation", "evals_ab"),
                          ("model_evaluation", "statistics", "evals_stats"),
                          ("llm_observability", "experimentation", "obs_ab"),
                          ("llm_observability", "statistics", "obs_stats")]:
    _or, _p = _odds(_out, _giv)
    out[f"or_{_name}"] = f"{_or:.1f}"
    out[f"p_{_name}"] = "<0.001" if _p < 0.001 else f"{_p:.2f}"
out["pct_obs_base_eng"] = f"{100 * _eng.req_llm_observability.mean():.0f}"
out["pct_obs_from_stats"] = f"{100 * _eng.req_llm_observability[_eng.req_statistics == 1].mean():.0f}"

# ── figures that used to arrive in a JSON, now computed from the published data ──
# scripts/eda-export.sh writes both files straight from the jobcrawler DB, so the
# page has ONE source of truth. Carrying these in a hand-maintained JSON meant the
# guard could not see them: it scans index.qmd and cannot check a number typed into
# a carrier. Anything derivable from the CSVs is derived here.
MENT = HERE / "data" / "skill-mentions.csv"
if MENT.exists():
    mp = pd.read_csv(MENT, keep_default_na=False)
    out["mentions_total"] = f"{int(mp.n_mentions.sum()):,}"
    out["mentions_phrases"] = f"{len(mp):,}"
    out["mentions_phrases_in_10_ads_or_more"] = f"{int((mp.n_jobs >= 10).sum()):,}"
    out["mentions_pct_mapped"] = f"{100 * mp.loc[mp.mapped_to != '', 'n_mentions'].sum() / mp.n_mentions.sum():.0f}"

# The machine-learning cross-check, from the per-ad flags the second pass wrote.
# Population note: selected on the judge's role_family, not the title regex, which
# is why its n differs from n_data_scientist — the page says so.
if "names_ml" in df.columns and str(df["names_ml"].iloc[0]) != "":
    ds = df[df.role_family == "data_scientist"]
    silent = ds[ds.names_ml == 0]
    out["mlx_ds_ads"] = f"{len(ds):,}"
    out["mlx_silent_ads"] = f"{len(silent):,}"
    out["mlx_silent_naming_tool"] = f"{int(silent.names_ml_tool.sum()):,}"
    out["mlx_silent_naming_tool_pct"] = f"{100 * silent.names_ml_tool.mean():.0f}"
    out["mlx_silent_nothing"] = f"{int((silent.names_ml_tool == 0).sum()):,}"
    out["mlx_silent_nothing_pct"] = f"{100 * (silent.names_ml_tool == 0).sum() / len(ds):.0f}"
    out["mlx_haiku_named"] = f"{100 * ds.names_ml.mean():.0f}"
    out["mlx_implied_total_pct"] = f"{100 * ((ds.names_ml == 1) | (ds.names_ml_tool == 1)).mean():.0f}"
    out["mlx_jev_required"] = f"{100 * ds[[c for c in ('req_classical_ml', 'req_deep_learning') if c in ds]].max(axis=1).mean():.0f}"
    # agreement between the two passes on machine learning, over the same ads
    jev = ds[[c for c in ("req_classical_ml", "req_deep_learning") if c in ds]].max(axis=1)
    hai = ds.names_ml_required
    po = (jev == hai).mean()
    pe = jev.mean() * hai.mean() + (1 - jev.mean()) * (1 - hai.mean())
    out["mlx_kappa"] = f"{(po - pe) / (1 - pe):.2f}"
    out["mlcheck_kappa"] = out["mlx_kappa"]
    out["mlcheck_all_jev_mentioned"] = f"{100 * df[[c for c in ('req_classical_ml', 'req_deep_learning') if c in df]].max(axis=1).mean():.0f}"
    out["mlcheck_all_haiku_named"] = f"{100 * df.names_ml.mean():.0f}"
    out["mlx_haiku_required"] = f"{100 * ds.names_ml_required.mean():.0f}"
    out["mlcheck_all_jev_required"] = out["mlcheck_all_jev_mentioned"]
    # counted WITHIN the silent ads, not pool-wide: a pool-wide count answers a
    # different question and would read as if it were this one.
    _col = "n_jobs_ds_silent" if "n_jobs_ds_silent" in mp.columns else "n_jobs"
    ex = mp[mp.phrase.str.contains("scikit|sklearn|pytorch|tensorflow|xgboost|lightgbm|keras|random forest|"
                                   "gradient boost|clustering|classification|regression|predictive model|"
                                   "supervised|feature engineering|model training|model development|mlflow",
                                   case=False)].nlargest(10, _col)
    PRETTY = {"predictive modeling": "predictive modelling", "mlflow": "MLflow", "pytorch": "PyTorch",
              "tensorflow": "TensorFlow"}
    out["mlx_silent_examples"] = ", ".join(f"{PRETTY.get(r.phrase, r.phrase)} ({getattr(r, _col)} ads)" if i == 0
                                           else f"{PRETTY.get(r.phrase, r.phrase)} ({getattr(r, _col)})"
                                           for i, r in enumerate(ex.itertuples()))
    top_other = mp.nlargest(7, _col).phrase.tolist()
    out["mlx_silent_other_asks"] = ", ".join({"sql": "SQL", "python": "Python", "r": "R",
                                              "a/b testing": "A/B testing"}.get(x, x) for x in top_other)

block = "jobskills:\n" + "".join(f"  {k}: \"{v}\"\n" for k, v in out.items())
vp = WWW / "_variables.yml"
keep = [l for l in vp.read_text().splitlines() if not l.startswith("jobskills:") and not l.startswith("  ")] if vp.exists() else []
vp.write_text("\n".join([l for l in keep if l.strip()] + [block.rstrip()]) + "\n")
print(f"wrote {vp.relative_to(WWW)} — {len(out)} variables, {len(df):,} ads, {len(REQ)} skills, {len(counts)} titles")
print("  closest pair:", out["closest_pair_a"], "/", out["closest_pair_b"], out["closest_pair_d"])

# ── the page's "updated" date ────────────────────────────────────────────────
# Quarto cannot expand `{{< var >}}` in YAML front matter, so the one date on
# the page could not come from _variables.yml like every other figure, and went
# stale four days running. This script already owns everything generated here,
# so it owns this too: `date` stays the publication date, `date-modified` is
# rewritten on every run, which is every time the figures are regenerated.
ip = HERE / "index.qmd"
src = ip.read_text()
today = dt.date.today().isoformat()
if re.search(r"(?m)^date-modified:", src):
    src = re.sub(r"(?m)^date-modified:.*$", f"date-modified: {today}", src, count=1)
else:
    src = re.sub(r"(?m)^(date:.*)$", rf"\1\ndate-modified: {today}", src, count=1)
ip.write_text(src)
print(f"  index.qmd date-modified: {today}")

# ── the guard: no figure may be typed into the page ──────────────────────────
# The rule in this file's docstring used to be enforced by remembering it, and
# it was quietly broken four times. Scan the page for numerals that are not
# inside a `{{< var >}}`, outside the places a number is not a measurement:
# YAML front matter, the iframe's CSS, years, and licence names.
SKIP = re.compile(r"^(date:|date-modified:|<iframe|\s*(title|subtitle):)")
BARE = re.compile(r"\d[\d,.]*\s*%|\b\d{2,}(?:,\d{3})*\b|κ ≈ [\d.]+|\b\d+\.\d+\b")
strays = []
for n, line in enumerate((HERE / "index.qmd").read_text().splitlines(), 1):
    if SKIP.match(line):
        continue
    bare = re.sub(r"\{\{<\s*var[^>]*>\}\}", "§", line)
    bare = re.sub(r"https?://\S+", "", bare)          # URLs and DOIs
    bare = re.sub(r"\b(19|20)\d\d\b", "", bare)      # years: context, not data
    bare = re.sub(r"CC BY[A-Z-]*\s*[\d.]+", "", bare)  # licence versions
    if BARE.search(bare):
        strays.append(f"    index.qmd:{n}  {line.strip()[:88]}")
if strays:
    print(f"  WARNING: {len(strays)} hand-typed figure(s) in the page — define them here instead:")
    print("\n".join(strays))
else:
    print("  guard: no hand-typed figures in index.qmd")

