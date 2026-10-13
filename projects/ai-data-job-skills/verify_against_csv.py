# /// script
# requires-python = ">=3.11"
# dependencies = ["pandas>=2.2","scipy>=1.11","numpy>=1.26"]
# ///
"""Recompute the page's headline figures straight from the published CSV and
compare with _variables.yml. Independent of build_stats.py."""
import json, re, sys, pandas as pd
sys.path.insert(0, ".")
import circles as C
df = pd.read_csv("data/ai-data-job-skills.csv")
V = dict(re.findall(r'^  (\w+): "(.*)"$', open("../../_variables.yml").read(), re.M))
ok = bad = 0
def chk(key, got):
    global ok, bad
    want = V.get(key)
    got = str(got)
    if want == got: ok += 1
    else:
        bad += 1; print(f"  MISMATCH {key}: page={want!r} csv={got!r}")

chk("n_ads", f"{len(df):,}")
chk("n_skills", sum(c.startswith("req_") for c in df.columns))
for fam, var in [("AI Engineer","ai_engineer"),("Data Scientist","data_scientist"),
                 ("Data Engineer","data_engineer"),("Data Analyst","data_analyst"),
                 ("ML Engineer","ml_engineer"),("Analytics Engineer","analytics_engineer"),("AI Automation","ai_automation")]:
    g = df.family == fam
    chk(f"n_{var}", g.sum()); chk(f"pct_{var}", round(100*g.mean()))
    chk(f"{var}_statistics", round(100*df.req_statistics[g].mean()))
chk("all_stakeholder_comms", round(100*df.req_stakeholder_comms.mean()))
chk("all_python", round(100*df.req_python.mean()))
chk("ai_no_python", round(100*(df.req_python[df.family=="AI Engineer"]==0).mean()))
chk("analytics_engineer_data_governance", round(100*df.req_data_governance[df.family=="Analytics Engineer"].mean()))
chk("data_engineer_data_governance", round(100*df.req_data_governance[df.family=="Data Engineer"].mean()))
chk("ai_engineer_software_engineering", round(100*df.req_software_engineering[df.family=="AI Engineer"].mean()))
chk("data_scientist_software_engineering", round(100*df.req_software_engineering[df.family=="Data Scientist"].mean()))
# the new circles
m = C.masks(df); E, D, I, G = m["Engineering, deployment & AI"], m["Data platform"], m["Statistics & inference"], m["_ground"]
chk("c26_pct_eng", round(100*E.mean())); chk("c26_pct_data", round(100*D.mean()))
chk("c26_pct_inference", round(100*I.mean())); chk("c26_pct_ground", round(100*G.mean()))
centre = E & D & I
chk("c26_pct_centre", round(100*centre.mean()))
chk("c26_pct_eng_only", round(100*(E & ~D & ~I).mean()))
chk("c26_pct_eng_data", round(100*(E & D & ~I).mean()))
chk("c26_pct_eng_inference", round(100*(E & ~D & I).mean()))
chk("c26_pct_data_inference", round(100*(~E & D & I).mean()))
vc = df.family[centre].value_counts()
chk("c26_centre_title", vc.index[0]); chk("c26_centre_title_pct", round(100*vc.iloc[0]/centre.sum()))
chk("c26_centre_not_data_scientist", 100-round(100*vc.iloc[0]/centre.sum()))
for reg, key in [((E & ~D & ~I),"eng_only"), ((E & D & ~I),"eng_data"),
                 ((E & ~D & I),"eng_inference"), ((~E & D & I),"data_inference")]:
    v = df.family[reg].value_counts()
    chk(f"c26_{key}_title", v.index[0]); chk(f"c26_{key}_title_pct", round(100*v.iloc[0]/reg.sum()))
# ── seniority (added 2026-10-13) ────────────────────────────────────────────
# Recomputed here independently of build_stats.py, which is the whole point of
# this file: two separate readings of the same column must agree.
if "seniority" in df.columns:
    SEN = ["entry", "mid", "senior", "staff_principal", "leadership"]
    sen = df["seniority"].dropna()
    for lv in SEN:
        chk(f"sen_pct_{lv}", round(100 * (sen == lv).mean()))
        chk(f"sen_n_{lv}", f"{int((sen == lv).sum()):,}")
    chk("sen_n_judged", f"{len(sen):,}")
    sp = sen.isin(["senior", "staff_principal", "leadership"])
    chk("sen_pct_senior_plus", round(100 * sp.mean()))
    chk("sen_pct_entry_mid", round(100 * sen.isin(["entry", "mid"]).mean()))
    byfam = df.assign(sp=df["seniority"].isin(["senior", "staff_principal", "leadership"])) \
              .groupby("family")["sp"].mean().mul(100).sort_values()
    chk("sen_most_senior_family", byfam.index[-1])
    chk("sen_most_senior_pct", round(byfam.iloc[-1]))
    chk("sen_least_senior_family", byfam.index[0])
    chk("sen_least_senior_pct", round(byfam.iloc[0]))
    chk("sen_family_spread", round(byfam.iloc[-1] - byfam.iloc[0]))
    ent = df.assign(e=df["seniority"].eq("entry")).groupby("family")["e"].mean().mul(100).sort_values()
    chk("sen_most_entry_family", ent.index[-1])
    chk("sen_most_entry_pct", round(ent.iloc[-1]))
    # The confound check the page leans on in RQ3.
    for lv in ["mid", "senior", "staff_principal"]:
        d = df[df["seniority"] == lv]
        a = 100 * d.req_statistics[d.family == "Data Scientist"].mean()
        b = 100 * d.req_statistics[d.family == "AI Engineer"].mean()
        chk(f"sen_stats_gap_{lv}", round(a - b))
    # Which families are over-weighted to the final month (collected late).
    base = (df["month"] == df["month"].max()).mean()
    conc = df.assign(f=df["month"] == df["month"].max()).groupby("family")["f"].mean() / base
    chk("n_late_families", len(conc[conc >= 1.4]))
    chk("sample_final_month_pct", round(100 * base))

print(f"\n{ok} figures verified against the CSV, {bad} mismatched")
