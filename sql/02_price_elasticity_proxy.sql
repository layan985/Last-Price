-- Relationship between relative quote level and agreement.
-- This is descriptive on synthetic data, not a causal elasticity estimate.
WITH quoted AS (
    SELECT
        treatment_id,
        buyer_model,
        market_segment,
        reference_price / NULLIF(buyer_value, 0) AS quote_to_value,
        agreed
    FROM negotiations
)
SELECT
    buyer_model,
    market_segment,
    CASE
        WHEN quote_to_value < 0.70 THEN '<70%'
        WHEN quote_to_value < 0.80 THEN '70-80%'
        WHEN quote_to_value < 0.90 THEN '80-90%'
        ELSE '90%+'
    END AS quote_bucket,
    COUNT(*) AS n,
    ROUND(AVG(agreed) * 100, 2) AS agreement_rate_pct
FROM quoted
GROUP BY buyer_model, market_segment, quote_bucket
ORDER BY buyer_model, market_segment, quote_bucket;
