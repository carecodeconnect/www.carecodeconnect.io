\pset pager off
\echo '== DS ads where Haiku names NO ML/DL/neural phrase: do they name ML tools or methods? =='
WITH ds AS (SELECT job_id FROM job_insights WHERE role_family='data_scientist'),
noml AS (
  SELECT ds.job_id FROM ds
  WHERE NOT EXISTS (SELECT 1 FROM job_skill_mentions m WHERE m.job_id=ds.job_id
    AND (m.skill ILIKE '%machine learning%' OR lower(m.skill)='ml'
      OR m.skill ILIKE '%deep learning%' OR m.skill ILIKE '%neural%'))
)
SELECT
 (SELECT count(*) FROM noml) AS ds_ads_never_saying_ml,
 count(DISTINCT m.job_id)    AS of_those_naming_an_ml_tool_or_method
FROM job_skill_mentions m JOIN noml ON noml.job_id=m.job_id
WHERE m.skill ILIKE ANY (ARRAY['%scikit%','%sklearn%','%pytorch%','%tensorflow%','%xgboost%',
  '%lightgbm%','%keras%','%random forest%','%gradient boost%','%clustering%','%classification%',
  '%regression%','%predictive model%','%supervised%','%unsupervised%','%feature engineering%',
  '%model training%','%model development%','%mlflow%','%hugging face%','%transformer%']);

\echo ''
\echo '== which phrases, exactly (top 20) =='
WITH ds AS (SELECT job_id FROM job_insights WHERE role_family='data_scientist'),
noml AS (
  SELECT ds.job_id FROM ds
  WHERE NOT EXISTS (SELECT 1 FROM job_skill_mentions m WHERE m.job_id=ds.job_id
    AND (m.skill ILIKE '%machine learning%' OR lower(m.skill)='ml'
      OR m.skill ILIKE '%deep learning%' OR m.skill ILIKE '%neural%'))
)
SELECT lower(m.skill) AS phrase, count(*) AS n, round(100.0*avg(m.required::int),0) AS pct_req
FROM job_skill_mentions m JOIN noml ON noml.job_id=m.job_id
WHERE m.skill ILIKE ANY (ARRAY['%scikit%','%sklearn%','%pytorch%','%tensorflow%','%xgboost%',
  '%lightgbm%','%keras%','%random forest%','%gradient boost%','%clustering%','%classification%',
  '%regression%','%predictive model%','%supervised%','%unsupervised%','%feature engineering%',
  '%model training%','%model development%','%mlflow%','%hugging face%','%transformer%'])
GROUP BY 1 ORDER BY n DESC LIMIT 20;

\echo ''
\echo '== what DO those ads ask for? top Haiku phrases overall =='
WITH ds AS (SELECT job_id FROM job_insights WHERE role_family='data_scientist'),
noml AS (
  SELECT ds.job_id FROM ds
  WHERE NOT EXISTS (SELECT 1 FROM job_skill_mentions m WHERE m.job_id=ds.job_id
    AND (m.skill ILIKE '%machine learning%' OR lower(m.skill)='ml'
      OR m.skill ILIKE '%deep learning%' OR m.skill ILIKE '%neural%'))
)
SELECT lower(m.skill) AS phrase, count(*) AS n
FROM job_skill_mentions m JOIN noml ON noml.job_id=m.job_id
GROUP BY 1 ORDER BY n DESC LIMIT 18;
\pset pager off
\echo '== Data Scientist ads: the full ladder for ML skills =='
WITH ds AS (SELECT job_id FROM job_insights WHERE role_family = 'data_scientist')
SELECT s.skill, count(*) AS n,
  round(100.0*avg((s.status='required')::int),0)   AS required,
  round(100.0*avg((s.status='nice')::int),0)       AS nice,
  round(100.0*avg((s.status='incidental')::int),0) AS incidental,
  round(100.0*avg((s.status='absent')::int),0)     AS absent,
  round(100.0*avg((s.status IN ('required','nice'))::int),0) AS req_or_nice,
  round(100.0*avg((s.status<>'absent')::int),0)    AS mentioned
FROM job_skills s JOIN ds ON ds.job_id = s.job_id
WHERE s.skill IN ('classical_ml','deep_learning','statistics','llm_apps','agents')
GROUP BY s.skill ORDER BY required DESC;

\echo ''
\echo '== either ML skill, by threshold (Data Scientist) =='
WITH ds AS (SELECT job_id FROM job_insights WHERE role_family='data_scientist'),
p AS (SELECT ds.job_id,
        max(CASE WHEN s.skill IN ('classical_ml','deep_learning') AND s.status='required' THEN 1 ELSE 0 END) AS req,
        max(CASE WHEN s.skill IN ('classical_ml','deep_learning') AND s.status IN ('required','nice') THEN 1 ELSE 0 END) AS req_nice,
        max(CASE WHEN s.skill IN ('classical_ml','deep_learning') AND s.status<>'absent' THEN 1 ELSE 0 END) AS any_mention
      FROM ds JOIN job_skills s ON s.job_id=ds.job_id GROUP BY ds.job_id)
SELECT count(*) AS ds_ads,
       round(100.0*avg(req),0) AS pct_required,
       round(100.0*avg(req_nice),0) AS pct_required_or_nice,
       round(100.0*avg(any_mention),0) AS pct_mentioned_at_all
FROM p;

\echo ''
\echo '== literal open-vocabulary evidence: do DS ads say machine learning? =='
WITH ds AS (SELECT job_id FROM job_insights WHERE role_family='data_scientist')
SELECT count(DISTINCT m.job_id) AS ds_ads_naming_ml,
       (SELECT count(*) FROM ds) AS ds_ads_total
FROM job_skill_mentions m JOIN ds ON ds.job_id=m.job_id
WHERE m.skill ILIKE '%machine learning%' OR m.skill ILIKE 'ml' OR m.skill ILIKE '%deep learning%';
\pset pager off
\echo '== (a) Haiku: which ML/DL phrases appear in Data Scientist ads =='
WITH ds AS (SELECT job_id FROM job_insights WHERE role_family='data_scientist')
SELECT lower(m.skill) AS phrase, count(*) AS n,
       round(100.0*avg(m.required::int),0) AS pct_required
FROM job_skill_mentions m JOIN ds ON ds.job_id=m.job_id
WHERE m.skill ILIKE '%machine learning%' OR lower(m.skill)='ml'
   OR m.skill ILIKE '%deep learning%' OR m.skill ILIKE '%neural%'
GROUP BY 1 ORDER BY n DESC LIMIT 15;

\echo ''
\echo '== (b) Haiku coverage of DS ads, required vs nice =='
WITH ds AS (SELECT job_id FROM job_insights WHERE role_family='data_scientist'),
h AS (SELECT ds.job_id,
        max(CASE WHEN (m.skill ILIKE '%machine learning%' OR lower(m.skill)='ml'
                    OR m.skill ILIKE '%deep learning%' OR m.skill ILIKE '%neural%') THEN 1 ELSE 0 END) AS named,
        max(CASE WHEN (m.skill ILIKE '%machine learning%' OR lower(m.skill)='ml'
                    OR m.skill ILIKE '%deep learning%' OR m.skill ILIKE '%neural%') AND m.required THEN 1 ELSE 0 END) AS named_req
      FROM ds LEFT JOIN job_skill_mentions m ON m.job_id=ds.job_id GROUP BY ds.job_id)
SELECT count(*) AS ds_ads,
       round(100.0*avg(named),0)     AS pct_haiku_names_ml,
       round(100.0*avg(named_req),0) AS pct_haiku_says_required
FROM h;

\echo ''
\echo '== (c) agreement: Jev required vs Haiku named (DS ads) =='
WITH ds AS (SELECT job_id FROM job_insights WHERE role_family='data_scientist'),
j AS (SELECT ds.job_id,
        max(CASE WHEN s.skill IN ('classical_ml','deep_learning') AND s.status='required' THEN 1 ELSE 0 END) AS jev_req,
        max(CASE WHEN s.skill IN ('classical_ml','deep_learning') AND s.status<>'absent' THEN 1 ELSE 0 END) AS jev_any
      FROM ds JOIN job_skills s ON s.job_id=ds.job_id GROUP BY ds.job_id),
h AS (SELECT ds.job_id,
        max(CASE WHEN (m.skill ILIKE '%machine learning%' OR lower(m.skill)='ml'
                    OR m.skill ILIKE '%deep learning%' OR m.skill ILIKE '%neural%') THEN 1 ELSE 0 END) AS hk,
        max(CASE WHEN (m.skill ILIKE '%machine learning%' OR lower(m.skill)='ml'
                    OR m.skill ILIKE '%deep learning%' OR m.skill ILIKE '%neural%') AND m.required THEN 1 ELSE 0 END) AS hk_req
      FROM ds LEFT JOIN job_skill_mentions m ON m.job_id=ds.job_id GROUP BY ds.job_id)
SELECT j.jev_req, h.hk AS haiku_named, h.hk_req AS haiku_required, count(*) AS n
FROM j JOIN h USING (job_id) GROUP BY 1,2,3 ORDER BY 1 DESC,2 DESC,3 DESC;
