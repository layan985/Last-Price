-- Buyer-policy KPI table with conditional price and extensive-margin reliability together.
SELECT
    buyer_model,
    COUNT(*) AS negotiations,
    ROUND(AVG(agreed) * 100, 2) AS agreement_rate_pct,
    ROUND(AVG(CASE WHEN agreed = 1 THEN price END), 2) AS mean_completed_price,
    ROUND(AVG(buyer_surplus), 2) AS mean_buyer_surplus,
    ROUND(AVG(rounds), 2) AS mean_rounds
FROM negotiations
GROUP BY buyer_model
ORDER BY agreement_rate_pct DESC;
