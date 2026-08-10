-- Join model predictions back to observed outcomes for post-deployment monitoring.
SELECT
    p.run_id,
    p.target,
    COUNT(*) AS observations,
    AVG(ABS(p.prediction - p.observed)) AS mean_absolute_error
FROM model_predictions p
WHERE p.observed IS NOT NULL
GROUP BY p.run_id, p.target
ORDER BY p.run_id DESC, p.target;
