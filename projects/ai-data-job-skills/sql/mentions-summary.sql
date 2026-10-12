-- Totals for the open-vocabulary (Haiku) extraction layer, quoted in the
-- Method section of index.qmd. These cannot come from the published CSV —
-- it exports only Jev's binary req_* flag — so they are exported here into
-- data/mentions-summary.json, which build_stats.py turns into page variables.
--
-- Run against the jobcrawler Postgres on the Pi, then paste the figures into
-- data/mentions-summary.json (the "current" block only; the dated review
-- blocks are frozen evidence and must not be recomputed).
\pset pager off
\echo '== mentions, distinct phrases, jobs covered, % mapped onto the fixed vocabulary =='
SELECT count(*)                                                        AS mentions,
       count(DISTINCT lower(skill))                                    AS phrases,
       count(DISTINCT job_id)                                          AS jobs,
       round(100.0 * count(*) FILTER (WHERE skill_norm IS NOT NULL)
             / count(*))                                               AS pct_mapped
FROM job_skill_mentions;

\echo ''
\echo '== phrases common enough to be worth reviewing (>= 10 ads) =='
SELECT count(*) AS phrases_in_10_ads_or_more
FROM (SELECT lower(skill) FROM job_skill_mentions
      GROUP BY 1 HAVING count(DISTINCT job_id) >= 10) t;
