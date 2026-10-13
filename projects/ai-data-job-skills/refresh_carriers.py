#!/usr/bin/env -S uv run --quiet
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Regenerate the three data carriers from the Pi, so no figure is transcribed.

The published CSV holds only Jev's binary required flag, so three sets of
figures on the page cannot come from it: which judge scored the pool, the
open-vocabulary extraction totals, and the machine-learning cross-check. They
are carried in data/*.json, which build_stats.py turns into page variables.

Those JSONs used to be edited by hand after running the .sql files beside them,
which is the same hardcoding the page's guard exists to prevent — the guard
scans index.qmd and cannot see a number typed into a carrier. This script runs
the queries and writes the files, so the figures are generated end to end.

    ./refresh_carriers.py            # needs Tailscale up and SSH to the Pi
    ./refresh_carriers.py --dry-run  # print what it would write

NOT yet regenerated, and still carried from the 2026-10-08 analysis: ml-crosscheck's
jev_required, jev_required_or_nice, jev_any_level, haiku_named, haiku_required,
kappa, implied_total_pct and the all_* figures. They need the Jev-vs-Haiku agreement
computation rather than a query, so they are the one place a figure is still
transcribed. Anything this script writes is generated.

Requires jobcrawler's scripts/connect-to-pi.sh; it is the only step that needs
the Pi, and it is why this is a separate script rather than part of the build.
"""
from __future__ import annotations

import argparse, datetime as dt, json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PI = Path.home() / "projects" / "jobcrawler" / "scripts" / "connect-to-pi.sh"
PSQL = "docker exec -i jobcrawler-postgres psql -U jobcrawler -d jobcrawler -tAF'|' -c"


def q(sql: str) -> list[list[str]]:
    if not PI.exists():
        sys.exit(f"{PI} not found — this script needs the jobcrawler checkout and Pi access")
    out = subprocess.run([str(PI), f'{PSQL} "{sql}"'], capture_output=True, text=True)
    if out.returncode != 0:
        sys.exit(f"query failed:\n{out.stderr[:400]}")
    return [l.split("|") for l in out.stdout.strip().splitlines() if l.strip()]


ML_SILENT = """WITH ds AS (SELECT job_id FROM job_insights WHERE role_family='data_scientist'),
noml AS (SELECT ds.job_id FROM ds WHERE NOT EXISTS (SELECT 1 FROM job_skill_mentions m
  WHERE m.job_id=ds.job_id AND (m.skill ILIKE '%%machine learning%%' OR lower(m.skill)='ml'
   OR m.skill ILIKE '%%deep learning%%' OR m.skill ILIKE '%%neural%%')))
SELECT (SELECT count(*) FROM ds), (SELECT count(*) FROM noml),
 (SELECT count(DISTINCT m.job_id) FROM job_skill_mentions m JOIN noml ON noml.job_id=m.job_id
  WHERE m.skill ILIKE ANY (ARRAY['%%scikit%%','%%sklearn%%','%%pytorch%%','%%tensorflow%%','%%xgboost%%',
   '%%lightgbm%%','%%keras%%','%%random forest%%','%%gradient boost%%','%%clustering%%','%%classification%%',
   '%%regression%%','%%predictive model%%','%%supervised%%','%%feature engineering%%','%%model training%%',
   '%%model development%%','%%mlflow%%','%%hugging face%%','%%transformer%%']))"""

ML_PHRASES = ML_SILENT.replace(
    "SELECT (SELECT count(*) FROM ds), (SELECT count(*) FROM noml),\n (SELECT count(DISTINCT m.job_id)",
    "SELECT lower(m.skill), count(DISTINCT m.job_id) AS n FROM job_skill_mentions m JOIN noml ON noml.job_id=m.job_id\n WHERE TRUE AND (SELECT 1")
# simpler to write the phrase query out than to patch the one above
ML_PHRASES = """WITH ds AS (SELECT job_id FROM job_insights WHERE role_family='data_scientist'),
noml AS (SELECT ds.job_id FROM ds WHERE NOT EXISTS (SELECT 1 FROM job_skill_mentions m
  WHERE m.job_id=ds.job_id AND (m.skill ILIKE '%%machine learning%%' OR lower(m.skill)='ml'
   OR m.skill ILIKE '%%deep learning%%' OR m.skill ILIKE '%%neural%%')))
SELECT lower(m.skill), count(DISTINCT m.job_id) n FROM job_skill_mentions m JOIN noml ON noml.job_id=m.job_id
WHERE m.skill ILIKE ANY (ARRAY['%%scikit%%','%%sklearn%%','%%pytorch%%','%%tensorflow%%','%%xgboost%%',
 '%%lightgbm%%','%%keras%%','%%random forest%%','%%gradient boost%%','%%clustering%%','%%classification%%',
 '%%regression%%','%%predictive model%%','%%supervised%%','%%feature engineering%%','%%model training%%',
 '%%model development%%','%%mlflow%%','%%hugging face%%','%%transformer%%'])
GROUP BY 1 ORDER BY n DESC LIMIT 10"""

OTHER_ASKS = """WITH ds AS (SELECT job_id FROM job_insights WHERE role_family='data_scientist'),
noml AS (SELECT ds.job_id FROM ds WHERE NOT EXISTS (SELECT 1 FROM job_skill_mentions m
  WHERE m.job_id=ds.job_id AND (m.skill ILIKE '%%machine learning%%' OR lower(m.skill)='ml'
   OR m.skill ILIKE '%%deep learning%%' OR m.skill ILIKE '%%neural%%')))
SELECT lower(m.skill), count(DISTINCT m.job_id) n FROM job_skill_mentions m JOIN noml ON noml.job_id=m.job_id
GROUP BY 1 ORDER BY n DESC LIMIT 7"""

PRETTY = {"predictive modeling": "predictive modelling", "mlflow": "MLflow", "pytorch": "PyTorch",
          "tensorflow": "TensorFlow", "scikit-learn": "scikit-learn", "sql": "SQL", "python": "Python",
          "a/b testing": "A/B testing", "r": "R", "data visualization": "data visualisation"}
pretty = lambda p: PRETTY.get(p, p)

ap = argparse.ArgumentParser(); ap.add_argument("--dry-run", action="store_true")
a = ap.parse_args()
today = dt.date.today().isoformat()

judge_rows = q("SELECT model, questions_version, count(*), max(judged_at)::date FROM job_insights "
               "GROUP BY 1,2 ORDER BY 3 DESC")
if len(judge_rows) > 1:
    print(f"  WARNING: {len(judge_rows)} judges in the pool — the page assumes one", file=sys.stderr)
jm, jv, jn, jt = judge_rows[0]

men = q("SELECT count(*), count(DISTINCT lower(skill)), count(DISTINCT job_id), "
        "round(100.0*count(*) FILTER (WHERE skill_norm IS NOT NULL)/count(*)) FROM job_skill_mentions")[0]
ten = q("SELECT count(*) FROM (SELECT lower(skill) FROM job_skill_mentions GROUP BY 1 "
        "HAVING count(DISTINCT job_id) >= 10) t")[0][0]
ds_n, silent, naming = (int(x) for x in q(ML_SILENT)[0])
phrases = q(ML_PHRASES)
asks = q(OTHER_ASKS)

files = {}
old_judge = json.loads((HERE / "data" / "judge.json").read_text())
files["judge.json"] = old_judge | {"_generated": today, "model": jm, "version": jm.rsplit(".", 1)[0],
                                   "questions_version": jv, "ads_judged": int(jn), "judged_through": jt}
old_men = json.loads((HERE / "data" / "mentions-summary.json").read_text())
files["mentions-summary.json"] = old_men | {
    "_generated": today, "total": int(men[0]), "phrases": int(men[1]),
    "phrases_in_10_ads_or_more": int(ten), "jobs_covered": int(men[2]), "pct_mapped": int(men[3])}
old_ml = json.loads((HERE / "data" / "ml-crosscheck.json").read_text())
files["ml-crosscheck.json"] = old_ml | {
    "_generated": today, "ds_ads": ds_n, "silent_ads": silent, "silent_naming_tool": naming,
    "silent_naming_tool_pct": round(100 * naming / silent),
    "silent_nothing": silent - naming, "silent_nothing_pct": round(100 * (silent - naming) / ds_n),
    "silent_examples": ", ".join(f"{pretty(p)} ({n} ads)" if i == 0 else f"{pretty(p)} ({n})"
                                 for i, (p, n) in enumerate(phrases)),
    "silent_other_asks": ", ".join(pretty(p) for p, _ in asks)}

for name, data in files.items():
    if a.dry_run:
        print(f"--- {name}"); print(json.dumps({k: v for k, v in data.items() if not k.startswith("_")}, indent=2))
    else:
        (HERE / "data" / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
        print(f"wrote data/{name}")
