-- Market-state segmentation: inventory, stockout pressure and agreement.
SELECT
    city,
    product_id,
    ROUND(AVG(inventory_level), 1) AS avg_inventory,
    ROUND(AVG(stockout_risk), 4) AS avg_stockout_risk,
    ROUND(AVG(agreed) * 100, 2) AS agreement_rate_pct,
    ROUND(AVG(CASE WHEN agreed = 1 THEN price END), 2) AS mean_price
FROM negotiations
GROUP BY city, product_id
HAVING COUNT(*) >= 6
ORDER BY avg_stockout_risk DESC, agreement_rate_pct ASC;
