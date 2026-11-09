-- Business Question 2: How have Public and Non-Public admission shares changed?
--
-- Restricted to Acute and Community Hospital admissions (the two categories
-- with a Public/Non-Public split). Uses conditional (CASE-based) aggregation
-- to pivot sector into columns, then a window function to track each year's
-- Public share against that service's own 2015 starting share.
-- NOTE: "Non-Public" here is Dataset 1's own category - it is NOT assumed to
-- correspond exactly to the "Private" or "Not-for-Profit" bed sectors used
-- in Datasets 2-3 (different source, no confirmed shared definition).

WITH shares AS (
    SELECT
        year,
        service_category,
        SUM(CASE WHEN sector = 'Public' THEN "count" ELSE 0 END) AS public_admissions,
        SUM(CASE WHEN sector = 'Non-Public' THEN "count" ELSE 0 END) AS non_public_admissions,
        SUM("count") AS total_admissions,
        ROUND(100.0 * SUM(CASE WHEN sector = 'Public' THEN "count" ELSE 0 END)
              / NULLIF(SUM("count"), 0), 2) AS public_share_pct,
        ROUND(100.0 * SUM(CASE WHEN sector = 'Non-Public' THEN "count" ELSE 0 END)
              / NULLIF(SUM("count"), 0), 2) AS non_public_share_pct
    FROM monthly
    WHERE measure_type = 'Hospital Admissions'
      AND service_category IN ('Acute Hospitals', 'Community Hospitals')
    GROUP BY year, service_category
)
SELECT
    year,
    service_category,
    public_admissions,
    non_public_admissions,
    total_admissions,
    public_share_pct,
    non_public_share_pct,
    ROUND(public_share_pct - FIRST_VALUE(public_share_pct) OVER (
        PARTITION BY service_category ORDER BY year
    ), 2) AS public_share_change_pts_since_2015
FROM shares
ORDER BY service_category, year;
