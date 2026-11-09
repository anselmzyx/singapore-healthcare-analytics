-- Business Question 3: What drove the numerical decline in Community Hospital
-- admissions in 2023?
--
-- A numerical decomposition only - NOT a causal explanation. Compares 2022,
-- 2023 and 2024 Public/Non-Public admissions and attributes each year's net
-- change to the sector that moved by more, as a share of the total change.

WITH yearly AS (
    SELECT
        year,
        SUM(CASE WHEN sector = 'Public' THEN "count" ELSE 0 END) AS public_admissions,
        SUM(CASE WHEN sector = 'Non-Public' THEN "count" ELSE 0 END) AS non_public_admissions,
        SUM("count") AS total_admissions
    FROM monthly
    WHERE measure_type = 'Hospital Admissions'
      AND service_category = 'Community Hospitals'
      AND year IN (2022, 2023, 2024)
    GROUP BY year
),
changes AS (
    SELECT
        year,
        public_admissions,
        non_public_admissions,
        total_admissions,
        public_admissions - LAG(public_admissions) OVER (ORDER BY year) AS public_abs_change,
        non_public_admissions - LAG(non_public_admissions) OVER (ORDER BY year) AS non_public_abs_change,
        total_admissions - LAG(total_admissions) OVER (ORDER BY year) AS total_abs_change,
        CASE
            WHEN LAG(total_admissions) OVER (ORDER BY year) IS NULL THEN NULL
            WHEN LAG(total_admissions) OVER (ORDER BY year) = 0 THEN NULL
            ELSE ROUND(100.0 * (total_admissions - LAG(total_admissions) OVER (ORDER BY year))
                 / LAG(total_admissions) OVER (ORDER BY year), 2)
        END AS total_pct_change
    FROM yearly
)
SELECT
    year,
    public_admissions,
    non_public_admissions,
    total_admissions,
    public_abs_change,
    non_public_abs_change,
    total_abs_change,
    total_pct_change,
    -- Each sector's share of that year's net change, in percentage points of the total move.
    CASE WHEN total_abs_change IS NULL OR total_abs_change = 0 THEN NULL
         ELSE ROUND(100.0 * public_abs_change / total_abs_change, 1) END AS public_contribution_pct_of_net_change,
    CASE WHEN total_abs_change IS NULL OR total_abs_change = 0 THEN NULL
         ELSE ROUND(100.0 * non_public_abs_change / total_abs_change, 1) END AS non_public_contribution_pct_of_net_change
FROM changes
ORDER BY year;
