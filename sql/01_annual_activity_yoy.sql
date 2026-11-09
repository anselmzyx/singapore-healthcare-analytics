-- Business Question 1: Which services experienced the largest absolute changes?
--
-- Builds annual totals per service (admissions categories are summed across
-- Public + Non-Public; outpatient/day-surgery series have a single 'All'
-- sector already), then uses LAG() to compute year-over-year absolute and
-- percentage change, and ranks both so the two rankings can be compared.
-- Different service types (admissions / attendances / day surgeries) are
-- kept as separate rows - never summed into one combined KPI.

WITH annual_totals AS (
    SELECT
        year,
        measure_type,
        service_category,
        SUM("count") AS annual_total
    FROM monthly
    GROUP BY year, measure_type, service_category
),
yoy AS (
    SELECT
        year,
        measure_type,
        service_category,
        annual_total,
        annual_total - LAG(annual_total) OVER (
            PARTITION BY measure_type, service_category ORDER BY year
        ) AS yoy_absolute_change,
        CASE
            WHEN LAG(annual_total) OVER (PARTITION BY measure_type, service_category ORDER BY year) IS NULL THEN NULL
            WHEN LAG(annual_total) OVER (PARTITION BY measure_type, service_category ORDER BY year) = 0 THEN NULL
            ELSE ROUND(
                100.0 * (annual_total - LAG(annual_total) OVER (PARTITION BY measure_type, service_category ORDER BY year))
                / LAG(annual_total) OVER (PARTITION BY measure_type, service_category ORDER BY year), 2)
        END AS yoy_pct_change
    FROM annual_totals
)
SELECT
    year,
    measure_type,
    service_category,
    annual_total,
    yoy_absolute_change,
    yoy_pct_change,
    (year BETWEEN 2019 AND 2022) AS in_2019_2022_window,
    -- Rank by magnitude of change (largest swings first), abs and pct separately,
    -- so the two rankings can be compared row by row.
    RANK() OVER (ORDER BY ABS(yoy_absolute_change) DESC NULLS LAST) AS abs_change_rank,
    RANK() OVER (ORDER BY ABS(yoy_pct_change) DESC NULLS LAST) AS pct_change_rank
FROM yoy
ORDER BY year, measure_type, service_category;
