-- Validation: basic data-quality checks across all three processed tables.
-- Every *_issue_count row is expected to be 0; the *_row_count rows should
-- match the known processed CSV sizes (monthly=1452, facilities=165, regional=102).

SELECT 'monthly_duplicate_keys' AS check_name, COUNT(*) AS result FROM (
    SELECT date, measure_type, service_category, sector
    FROM monthly GROUP BY 1, 2, 3, 4 HAVING COUNT(*) > 1
)
UNION ALL
SELECT 'facilities_duplicate_keys', COUNT(*) FROM (
    SELECT year, institution_type, facility_type, sector
    FROM facilities GROUP BY 1, 2, 3, 4 HAVING COUNT(*) > 1
)
UNION ALL
SELECT 'regional_duplicate_keys', COUNT(*) FROM (
    SELECT year, facility_type, sector, planning_region
    FROM regional GROUP BY 1, 2, 3, 4 HAVING COUNT(*) > 1
)
UNION ALL
SELECT 'monthly_negative_counts', COUNT(*) FROM monthly WHERE "count" < 0
UNION ALL
SELECT 'facilities_negative_values', COUNT(*) FROM facilities WHERE no_of_facilities < 0 OR no_beds < 0
UNION ALL
SELECT 'regional_negative_beds', COUNT(*) FROM regional WHERE no_beds < 0
UNION ALL
SELECT 'monthly_missing_values', COUNT(*) FROM monthly WHERE "count" IS NULL
UNION ALL
SELECT 'facilities_missing_values', COUNT(*) FROM facilities WHERE no_of_facilities IS NULL OR no_beds IS NULL
UNION ALL
SELECT 'regional_missing_values', COUNT(*) FROM regional WHERE no_beds IS NULL
UNION ALL
SELECT 'monthly_row_count', COUNT(*) FROM monthly
UNION ALL
SELECT 'facilities_row_count', COUNT(*) FROM facilities
UNION ALL
SELECT 'regional_row_count', COUNT(*) FROM regional;
