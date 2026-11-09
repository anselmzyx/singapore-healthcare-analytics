-- Task 7: Source reconciliation check.
--
-- Independently compares the national facilities dataset against the
-- regional dataset (summed across regions), at year + facility_type +
-- sector granularity, 2020-2025. Nothing is hardcoded - the 2021 Public
-- Community Hospital gap (expected: national 1180, regional 1112, diff 68)
-- should simply fall out of this query as a 'GENUINE MISMATCH' row.
-- Mismatches are reported as-is; neither source is adjusted to force equality.

WITH regional_agg AS (
    SELECT year, facility_type, sector, SUM(no_beds) AS regional_beds
    FROM regional
    WHERE year BETWEEN 2020 AND 2025
    GROUP BY year, facility_type, sector
),
national AS (
    SELECT year, facility_type, sector, SUM(no_beds) AS national_beds
    FROM facilities
    WHERE institution_type = 'Hospital'
      AND year BETWEEN 2020 AND 2025
    GROUP BY year, facility_type, sector
)
SELECT
    COALESCE(n.year, r.year) AS year,
    COALESCE(n.facility_type, r.facility_type) AS facility_type,
    COALESCE(n.sector, r.sector) AS sector,
    n.national_beds,
    r.regional_beds,
    n.national_beds - r.regional_beds AS difference,
    CASE
        WHEN r.regional_beds IS NULL AND n.national_beds = 0 THEN 'regional omits zero-bed rows (not a mismatch)'
        WHEN r.regional_beds IS NULL AND n.national_beds <> 0 THEN 'MISSING IN REGIONAL - review'
        WHEN n.national_beds IS NULL THEN 'MISSING IN NATIONAL - review'
        WHEN n.national_beds <> r.regional_beds THEN 'GENUINE MISMATCH'
        ELSE 'match'
    END AS status
FROM national n
FULL OUTER JOIN regional_agg r
    ON n.year = r.year AND n.facility_type = r.facility_type AND n.sector = r.sector
ORDER BY
    CASE status WHEN 'GENUINE MISMATCH' THEN 0
                WHEN 'MISSING IN REGIONAL - review' THEN 1
                WHEN 'MISSING IN NATIONAL - review' THEN 2
                ELSE 3 END,
    year, facility_type, sector;
