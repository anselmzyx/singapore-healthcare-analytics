-- Business Question 5: Where has regional hospital bed capacity grown?
--
-- Bed counts, 2020-2025 absolute and percentage growth (guarded against
-- division by zero), and each region/facility-type combo's share of the
-- 2025 total, by planning region and facility type.
-- Regional data describes WHERE facilities are located, not patient
-- residence or demand - no claim about under-served regions is made here.

WITH by_region_type AS (
    SELECT year, planning_region, facility_type, SUM(no_beds) AS beds
    FROM regional
    WHERE year IN (2020, 2025)
    GROUP BY year, planning_region, facility_type
),
pivoted AS (
    SELECT
        planning_region,
        facility_type,
        MAX(CASE WHEN year = 2020 THEN beds END) AS beds_2020,
        MAX(CASE WHEN year = 2025 THEN beds END) AS beds_2025
    FROM by_region_type
    GROUP BY planning_region, facility_type
)
SELECT
    planning_region,
    facility_type,
    COALESCE(beds_2020, 0) AS beds_2020,
    COALESCE(beds_2025, 0) AS beds_2025,
    COALESCE(beds_2025, 0) - COALESCE(beds_2020, 0) AS absolute_growth,
    CASE
        WHEN COALESCE(beds_2020, 0) = 0 THEN NULL  -- guard: no 2020 base to grow from
        ELSE ROUND(100.0 * (COALESCE(beds_2025, 0) - beds_2020) / beds_2020, 1)
    END AS pct_growth,
    ROUND(100.0 * COALESCE(beds_2025, 0) / SUM(COALESCE(beds_2025, 0)) OVER (), 2) AS share_of_2025_total_pct
FROM pivoted
ORDER BY absolute_growth DESC;
