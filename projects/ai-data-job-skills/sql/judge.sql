-- Which judge produced the scores, and how far it has got. Feeds
-- data/judge.json, which build_stats.py turns into page variables so the
-- Method section's model version is not typed by hand.
--
-- One row means one instrument across the whole pool, which is what the
-- page's cross-title comparisons rest on. More than one row means the pool
-- is mixed (e.g. the Haiku fallback filled a gap while TypeSafe was out of
-- credits) and the Method section must say so before the page is published.
\pset pager off
SELECT model, questions_version, count(*) AS ads_judged, max(judged_at)::date AS judged_through
FROM job_insights
GROUP BY 1, 2
ORDER BY 3 DESC;
