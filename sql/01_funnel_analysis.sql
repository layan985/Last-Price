-- Conversion/reliability funnel by buyer and seller policy.
SELECT
    buyer_model,
    seller_model,
    COUNT(*) AS negotiations,
    SUM(agreed) AS completed,
    ROUND(AVG(agreed) * 100, 2) AS agreement_rate_pct,
    ROUND(AVG(CASE WHEN agreed = 1 THEN rounds END), 2) AS avg_rounds_if_completed
FROM negotiations
GROUP BY buyer_model, seller_model
ORDER BY agreement_rate_pct DESC;
