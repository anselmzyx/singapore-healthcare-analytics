# Resume Bullets: Singapore Healthcare Analytics Project

- Built a reproducible Python (pandas) pipeline to clean three Singapore government healthcare datasets, reshaping hierarchical wide-format source files and reconciling 741 admissions category-months against source totals; identified and preserved a genuine 68-bed discrepancy between national and regional capacity datasets rather than silently correcting it.

- Used DuckDB SQL (CTEs, window functions) to analyze the cleaned data, finding that Community Hospital admissions grew 183.3% versus 31.7% for Acute Hospitals, and that Public Acute Hospital admissions grew faster than bed capacity (44.4% versus 32.7%, indexed to 2015) over the same decade.

- Built a two-page Power BI dashboard, importing the cleaned CSVs and adding DAX measures and an interactive year-range filter to visualize admissions, outpatient activity, and regional bed capacity (52.5% concentrated in the Central region) across 2015 to 2025.
