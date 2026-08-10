-- Rolling price benchmark within product.
WITH daily AS (
    SELECT
        product_id,
        DATE(timestamp) AS day,
        AVG(CASE WHEN agreed = 1 THEN price END) AS avg_price,
        AVG(agreed) AS agreement_rate
    FROM negotiations
    GROUP BY product_id, DATE(timestamp)
)
SELECT
    product_id,
    day,
    avg_price,
    agreement_rate,
    AVG(avg_price) OVER (
        PARTITION BY product_id
        ORDER BY day
        ROWS BETWEEN 7 PRECEDING AND 1 PRECEDING
    ) AS trailing_7_observation_price,
    RANK() OVER (
        PARTITION BY day
        ORDER BY agreement_rate DESC
    ) AS agreement_rank_that_day
FROM daily
ORDER BY product_id, day;
