-- Business Question 4: How did hospital admissions grow relative to bed
-- capacity?
--
-- Compares Public Acute Hospital admissions (a 12-month flow, from the
-- monthly table) against Public Acute Hospital beds (a point-in-time stock,
-- from the facilities table), both indexed to their own 2015 value = 100 so
-- relative growth rates are comparable despite different units.
-- This is NOT an occupancy, utilisation, or admissions-per-bed ratio - no
-- such ratio is calculated anywhere in this query.

WITH admissions AS (
    SELECT year, SUM("count") AS public_acute_admissions
    FROM monthly
    WHERE measure_type = 'Hospital Admissions'
      AND service_category = 'Acute Hospitals'
      AND sector = 'Public'
    GROUP BY year
),
beds AS (
    SELECT year, SUM(no_beds) AS public_acute_beds
    FROM facilities
    WHERE institution_type = 'Hospital'
      AND facility_type = 'Acute Hospitals'
      AND sector = 'Public'
    GROUP BY year
),
baseline AS (
    SELECT
        (SELECT public_acute_admissions FROM admissions WHERE year = 2015) AS admissions_baseline,
        (SELECT public_acute_beds FROM beds WHERE year = 2015) AS beds_baseline
)
SELECT
    a.year,
    a.public_acute_admissions,
    b.public_acute_beds,
    ROUND(100.0 * a.public_acute_admissions / baseline.admissions_baseline, 1) AS admissions_index_2015_100,
    ROUND(100.0 * b.public_acute_beds / baseline.beds_baseline, 1) AS beds_index_2015_100,
    ROUND(100.0 * a.public_acute_admissions / baseline.admissions_baseline, 1)
        - ROUND(100.0 * b.public_acute_beds / baseline.beds_baseline, 1) AS index_point_gap_admissions_minus_beds
FROM admissions a
JOIN beds b ON a.year = b.year
CROSS JOIN baseline
ORDER BY a.year;
