#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2", "numpy>=1.26"]
# ///
"""Generates `_titles-deepdive.qmd`: one section per job-title family, in the
approximate order the title entered data/AI hiring.

Everything quantitative here is computed from the published CSV, so the deep
dive cannot drift from the data the page ships. Two things are NOT from the CSV
and are marked as such:

  * the distinctive literal phrases, which come from the open-vocabulary (Haiku)
    pass over the pool — published in `data/skill-mentions.csv`;
  * the short evidence quotes in QUOTES below, selected by hand from the
    evidence sentences that pass stores with each mention (`sql/title-quotes.sql`).
    Fragments only, no employer named — the published CSV deliberately carries no
    ad text and that is not changing (owner, 2026-10-08).

The era given for each title is background, not a measurement: the sample covers
Apr–Oct 2026 only and can say nothing about when a title appeared.
"""
from pathlib import Path
import json
import re

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
df = pd.read_csv(HERE / "data" / "ai-data-job-skills.csv")
N = len(df)
REQ = [c for c in df.columns if c.startswith("req_")]
# The open-vocabulary phrases now come from the published skill-mentions.csv, not
# from a separate JSON: one source of truth, and the JSON had gone stale within a
# week of being written. "Over-represented" = the title's share of ads using the
# phrase, against the share across all ads.
_MP = pd.read_csv(HERE / "data" / "skill-mentions.csv", keep_default_na=False)
_FCOL = {f: "n_jobs_" + re.sub(r"[^a-z0-9]+", "_", f.lower()).strip("_")
         for f in df["family"].unique()}


def phrases_for(fam, n_fam, limit=5):
    col = _FCOL.get(fam)
    if col not in _MP.columns:
        return []
    m = _MP[_MP[col] > 0].copy()
    m["share"] = 100 * m[col] / n_fam
    m["base"] = 100 * m["n_jobs"] / N
    # Rank by over-representation, not raw count: the commonest phrases in a title
    # are the commonest everywhere ("statistics", "machine learning") and say
    # nothing about what makes the title different.
    # Both conditions matter. Rank by over-representation alone and you get
    # phrases in 1% of the title's ads; rank by raw count and you get the ones
    # common everywhere. So: present in at least 5% of this title's ads AND at
    # least 1.5x its share across all ads.
    m = m[(m[col] >= 3) & (m["base"] > 0) & (m["share"] >= 5)]
    m["lift"] = m["share"] / m["base"]
    m = m[m["lift"] >= 1.5]
    out = []
    for r in m.nlargest(limit * 5, "lift").itertuples():
        if r.phrase in STOP:
            continue
        out.append({"phrase": r.phrase, "n": int(getattr(r, col)), "share": round(r.share)})
        if len(out) == limit:
            break
    return out


def phrase_count(fam, phrase):
    col = _FCOL.get(fam)
    row = _MP[_MP.phrase == phrase]
    return int(row[col].iloc[0]) if len(row) and col in _MP.columns else None

# "Building or training a model" vs "calling someone else's over an API" — the
# distinction the page needs to make explicit (owner, 2026-10-08).
TRAIN = ["classical_ml", "deep_learning", "fine_tuning", "computer_vision", "recsys_ranking"]
CALL = ["llm_apps", "agents", "rag", "llm_observability"]

# Phrases the extraction returns that carry no information about a role.
STOP = {"engineering", "multitasking", "communication", "teamwork", "collaboration",
        "problem solving", "english", "german"}

# Chronology is approximate and from the history of the titles, not from this
# sample. Each entry: (family, era, what the title is and where it came from).
ORDER = [
    ("Quantitative Researcher", "finance, 1980s–1990s",
     "The oldest title here, and the one that got there first. Investment banks and hedge funds were "
     "hiring mathematicians and physicists to price derivatives and find trading signals two decades "
     "before anyone said “data scientist”. Everything the later titles claim as novel — statistics on "
     "large datasets, models in production, money riding on the output — was already the job."),
    ("Data Analyst", "business intelligence, 1990s–2000s",
     "Grew out of business intelligence and reporting. The job was to turn a company’s own operational "
     "data into numbers a manager could act on, and the tooling was the warehouse and the dashboard "
     "rather than the notebook."),
    ("Research Scientist", "industrial labs, long-standing; current AI form from ~2012",
     "The title is far older than data science — industrial research labs have used it for most of a "
     "century — but the version that shows up in this sample is the deep-learning lab role that "
     "followed the 2012 ImageNet result: publish, train large models, push the state of the art."),
    ("Data Scientist", "coined 2008, mainstream from ~2012",
     "Coined in 2008 by D.J. Patil and Jeff Hammerbacher, then leading data at LinkedIn and Facebook, "
     "and made famous by the 2012 *[Harvard Business Review](https://hbr.org/2012/10/data-scientist-the-sexiest-job-of-the-21st-century)* piece. The pitch was a "
     "hybrid: enough statistics to be rigorous, enough code to be self-sufficient, enough business "
     "sense to be listened to."),
    ("Data Engineer", "~2011–2014",
     "Split off from the data scientist once companies discovered that most of the work was moving and "
     "shaping data rather than modelling it. Hadoop, then Spark, then the cloud warehouse made the "
     "pipeline a full-time job."),
    ("ML Engineer", "~2015–2016",
     "Split off from the other side of the data scientist: the half concerned with getting a trained "
     "model to run reliably for real users. The title tracks the arrival of model serving, feature "
     "stores and the tooling that became MLOps."),
    ("Analytics Engineer", "~2018–2019",
     "The newest of the analytics titles, and essentially a dbt-era invention: apply software "
     "engineering practice — version control, tests, modular transformations — to the modelling layer "
     "between the warehouse and the dashboard."),
    ("Forward Deployed", "Palantir-era term, mainstream from ~2023",
     "A solutions-engineering lineage with a newer name. The engineer is embedded with the customer, "
     "building and adapting the product in front of them. The term escaped Palantir and spread as AI "
     "vendors discovered their product needed fitting to each buyer."),
    ("AI Engineer", "~2023",
     "The newest title in the sample and already the largest. It arrived with the production LLM "
     "stack — applications, retrieval, agents, evaluation — and it is the one title here defined by "
     "what it builds *with* rather than what it knows."),
    ("AI Automation", "~2024",
     "The newest family here, and the one the crawler began tracking last. The titles are AI, "
     "agentic, intelligent or workflow automation — Engineer, Specialist, Lead or Consultant — and "
     "they describe wiring an LLM into a business process rather than building a model. The QA, "
     "industrial and robotic-process senses of the word are excluded; they are a different job."),
]

# Short evidence fragments, chosen by hand from the stored evidence sentences.
# No employer named; each illustrates a pattern the numbers already establish.
# Short evidence fragments, chosen by hand from the stored evidence sentences
# (sql/title-quotes.sql). No employer named. Each is keyed to the literal phrase
# it illustrates, so the page can state how many other ads in the same title say
# the same thing — a quote without that frequency is just an anecdote (owner,
# 2026-10-08).
QUOTES = {
    "Quantitative Researcher": [("quantitative modeling", "5+ years of experience with quantitative modeling and pricing"),
                                ("market microstructure", "Strong understanding of market mechanics and microstructure invariants")],
    "Data Analyst": [("power bi", "data visualisation tools such as Power BI"),
                     ("a/b testing", "A/B testing that directly influence product improvements")],
    "Research Scientist": [("reinforcement learning", "Strong empirical research skills in Reinforcement Learning"),
                           ("deep learning", "state-of-the-art Deep Learning and Reinforcement Learning models")],
    "Data Scientist": [("causal inference", "experimental design, causal inference and quasi-experimental methods"),
                       ("predictive modeling", "Expertise in machine learning and predictive modelling")],
    "Data Engineer": [("etl/elt", "Own the design of scalable ETL/ELT pipelines")],
    "ML Engineer": [("model training", "training and iterating on deep learning models"),
                    ("model deployment", "transition of machine learning models into production")],
    "Analytics Engineer": [("dbt", "modeled in dbt and orchestrated by Airflow")],
    "Forward Deployed": [("solutions engineering", "8+ years experience in Solution Engineering role")],
    "AI Engineer": [("rag", "using large language models, RAG, vector search"),
                    ("agents", "AI application patterns (RAG, agents, tool use)"),
                    ("fine-tuning", "Exposure to fine-tuning or continuous learning techniques")],
}

NICE = {"nlp": "NLP", "rag": "RAG", "sql": "SQL", "r": "R", "bi_dashboards": "BI dashboards",
        "llm_apps": "LLM applications", "llm_observability": "LLM observability",
        "apis_services": "APIs and services", "cicd_testing": "CI/CD and testing",
        "mlops_tooling": "MLOps tooling", "dbt_modelling": "dbt modelling",
        "python": "Python", "quant_research": "quantitative research",
        "stakeholder_comms": "stakeholder communication", "systems_lang": "systems languages",
        "scala_java": "Scala or Java", "typescript": "TypeScript", "spark_distributed": "Spark",
        "pipelines_etl": "data pipelines", "classical_ml": "classical ML",
        "mentoring_leadership": "mentoring and leadership", "customer_facing": "customer-facing work",
        "product_analytics": "product analytics", "computer_vision": "computer vision",
        "recsys_ranking": "recommenders and ranking", "causal_inference": "causal inference",
        "time_series": "time series", "model_serving": "model serving",
        "model_evaluation": "model evaluation", "fine_tuning": "fine-tuning",
        "deep_learning": "deep learning", "software_engineering": "software engineering",
        "data_governance": "data governance", "responsible_ai": "responsible AI"}


def pretty(skill: str) -> str:
    return NICE.get(skill, skill.replace("_", " "))


def pct(x) -> str:
    return f"{100 * x:.0f}"


cent = {f: g[REQ].mean() for f, g in df.groupby("family")}
train_all = df[[f"req_{s}" for s in TRAIN]].sum(axis=1) > 0
call_all = df[[f"req_{s}" for s in CALL]].sum(axis=1) > 0

lines = ["<!-- GENERATED by build_titles.py — do not edit; edit the script. -->", ""]
add = lines.append

add("Nine titles, in the approximate order each entered data and AI hiring. The dates are "
    "background — this sample runs {{< var jobskills.months >}} and can say nothing about when a "
    "title appeared — but everything after them is measured from the ads.")
add("")
add(f"Across the whole sample, **{pct(train_all.mean())}%** of ads require building or training a "
    f"model of some kind and **{pct(call_all.mean())}%** require calling a model someone else trained. "
    f"That split is the thread running through these sections, and it moves with the chronology: the "
    f"older the title, the likelier it is to build.")
add("")
add('![](images/build-vs-call.png){fig-alt="Grouped bar chart of the nine job titles showing the share '
    'of each title\'s ads that require building or training a model versus calling one over an API"}')
add("")

# A horizontal chain of the nine titles in the same order (owner, 2026-10-08).
# Generated here rather than hand-written in the page because Quarto does not
# expand `{{< var >}}` inside a mermaid block — the same reason the distance
# diagram is generated.
SHORT = {"AI Automation": ("AI<br/>Automation", "~2024"),
         "Quantitative Researcher": ("Quantitative<br/>Researcher", "1980s–90s"),
         "Data Analyst": ("Data<br/>Analyst", "1990s–2000s"),
         "Research Scientist": ("Research<br/>Scientist", "~2012 in this form"),
         "Data Scientist": ("Data<br/>Scientist", "2008"),
         "Data Engineer": ("Data<br/>Engineer", "~2011–14"),
         "ML Engineer": ("ML<br/>Engineer", "~2015–16"),
         "Analytics Engineer": ("Analytics<br/>Engineer", "~2018–19"),
         "Forward Deployed": ("Forward<br/>Deployed", "~2023"),
         "AI Engineer": ("AI<br/>Engineer", "~2023")}
add("```{mermaid}")
add("%%| fig-width: 6.5")
add("%%| fig-align: center")
add('%%| fig-cap: "The nine titles in the approximate order each entered data and AI hiring, with the share of this sample each holds. The dates are background, not measured."')
add('%%{init: {"theme": "neutral", "fontSize": 17, "flowchart": {"curve": "basis", "nodeSpacing": 26, "rankSpacing": 34}}}%%')
add("flowchart TB")
# Two per rank rather than nine in a line: nine across shrinks the text to
# nothing at page width. This used to be done with invisible subgraphs, each
# with `direction LR`, joined by edges between the subgraphs — which Mermaid 11
# cannot lay out, and the whole diagram failed with "Syntax error in text".
# Plain nodes and edges only now: a --> b down the pairs, and an invisible link
# (`~~~`) across each pair to hold the two side by side.
idx = {fam: j for j, (fam, _, _) in enumerate(ORDER)}
PAIRS = [ORDER[k:k + 2] for k in range(0, len(ORDER), 2)]
for fam, _, _ in ORDER:
    label, when = SHORT[fam]
    share = pct(len(df[df.family == fam]) / N)
    add(f'  n{idx[fam]}["{label}<br/>{when}<br/>{share}% of job ads"]')
for pair in PAIRS:
    if len(pair) == 2:
        add(f"  n{idx[pair[0][0]]} ~~~ n{idx[pair[1][0]]}")
for a, b in zip(ORDER, ORDER[1:]):
    add(f"  n{idx[a[0]]} --> n{idx[b[0]]}")
add("```")
add("")

for i, (fam, era, blurb) in enumerate(ORDER, start=1):
    g = df[df.family == fam]
    rest = df[df.family != fam]
    n = len(g)
    top = g[REQ].mean().sort_values(ascending=False)
    lift = ((g[REQ].mean() + 0.01) / (rest[REQ].mean() + 0.01)).sort_values(ascending=False)
    d = sorted(((o, float(np.linalg.norm(cent[fam] - cent[o]))) for o in cent if o != fam),
               key=lambda kv: kv[1])
    SHIPC = ["model_serving", "mlops_tooling", "containers", "cicd_testing", "cloud",
             "orchestration"]
    MODELC = ["classical_ml", "deep_learning", "nlp", "computer_vision", "llm_apps", "agents",
              "rag", "fine_tuning"]
    sh = g[[f"req_{s}" for s in SHIPC if f"req_{s}" in g.columns]].sum(axis=1) > 0
    md = g[[f"req_{s}" for s in MODELC if f"req_{s}" in g.columns]].sum(axis=1) > 0
    tr = g[[f"req_{s}" for s in TRAIN]].sum(axis=1) > 0
    ca = g[[f"req_{s}" for s in CALL]].sum(axis=1) > 0

    add(f"### {i}. {fam} — {era} {{#sec-title-{fam.lower().replace(' ', '-')}}}")
    add("")
    add(f"*{n:,} ads, {pct(n / N)}% of the sample*")
    add("")
    add(blurb)
    add("")
    slug = fam.lower().replace(" ", "-")
    add(f"![](images/title-{slug}.png){{fig-alt=\"Bar chart of the skills {fam} ads require most "
        f"often and the skills most over-represented in them, each against the share across all ads\"}}")
    if fam == "Data Scientist":
        add("")
        add("![](images/model-and-ship.png){fig-alt=\"Stacked bars per job title showing the share of "
            "ads requiring both a model and its deployment, a model only, deployment only, or neither\"}")
    add("")
    add(f"**Take-home.** {pct((sh & md).mean())}% of these ads want both a model and its deployment "
        f"and {pct((~sh & md).mean())}% a model without it; the most distinctive requirement is "
        f"{pretty(lift.index[0][4:])}, and the nearest title is {d[0][0]}.")
    add("")
    add(f"**Nearest neighbour.** {d[0][0]} ({d[0][1]:.2f} apart on the skills map), then {d[1][0]} "
        f"({d[1][1]:.2f}). Furthest: {d[-1][0]} ({d[-1][1]:.2f}).")
    add("")
    add(f"**Build or call.** {pct(tr.mean())}% build or train a model, {pct(ca.mean())}% call one over "
        f"an API, and {pct((ca & ~tr).mean())}% want the API work with no model-building at all.")
    add("")

    ph = phrases_for(fam, n)
    if ph:
        words = ", ".join(f"“{p['phrase']}” ({p['share']}%)" for p in ph)
        add(f"**In the ads' own words.** The phrases most over-represented in this title, read out of "
            f"the ads by a second model that was never shown our skill list, with the share of the "
            f"title's ads using each: {words}.")
        add("")
    for phrase, quote in QUOTES.get(fam, []):
        c = phrase_count(fam, phrase)   # job count within this title
        if c is None:
            raise SystemExit(f"no phrase count for {fam} / {phrase!r} — check skill-mentions.csv")
        add(f"> {quote}")
        add(">")
        add(f"> <small>— one of **{c}** {fam} job ads ({round(100 * c / n)}% of the title) that ask for "
            f"“{phrase}”</small>")
        add("")

out = HERE / "_titles-deepdive.qmd"
out.write_text("\n".join(lines) + "\n")
print(f"wrote {out.name} — {len(ORDER)} titles, {N:,} ads")
for fam, _, _ in ORDER:
    g = df[df.family == fam]
    tr = g[[f"req_{s}" for s in TRAIN]].sum(axis=1) > 0
    ca = g[[f"req_{s}" for s in CALL]].sum(axis=1) > 0
    print(f"   {fam:24s} n={len(g):>4}  build {pct(tr.mean()):>3}%  call {pct(ca.mean()):>3}%")
