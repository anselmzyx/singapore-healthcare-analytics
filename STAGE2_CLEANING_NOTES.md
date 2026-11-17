# Stage 2: Data Cleaning and Preparation Notes

Produced by `scripts/clean_data.py` (rerunnable; reads `data/raw/`, writes `data/processed/`, never modifies raw files). Execution time: ~0.7 seconds.

## Outputs

| File | Rows | Coverage |
|---|---|---|
| `data/processed/healthcare_utilisation_monthly.csv` | 1,452 | Jan 2015 – Dec 2025, monthly |
| `data/processed/healthcare_facilities_annual.csv` | 165 | 2015 – 2025, annual |
| `data/processed/hospital_beds_region_annual.csv` | 102 | 2020 – 2025, annual |

## Transformations

**Monthly utilisation (Dataset 1)**
- Read as strings with `keep_default_na=False` to preserve leading-space indentation in `DataSeries` and the literal `"na"` placeholder.
- Parsed row hierarchy by indentation: level-0 rows are either an admissions category (Acute/Psychiatric/Community Hospitals, each with Public/Non-Public children) or a self-contained service with no sector split.
- Melted wide → long; parsed `YYYYMon` column headers (e.g. `2026Jul`) into real dates. Source columns are **not** chronological (they run Dec-2005→Jan-1987, then jump to Jul-2026→Jan-2006); output is sorted by the parsed date, not source column order.
- Converted literal `"na"` to missing *before* the date filter, then filtered to Jan 2015–Dec 2025.
- Added `measure_type` (Hospital Admissions / Outpatient Attendances / Day Surgeries) and `sector` (Public / Non-Public / All) columns.
- Reconciled every admissions category-month: source parent Total vs. Public+Non-Public children, comparing only category-months where both the parent and both children are genuinely reported. Across the full history (3 admissions categories × 475 months = 1,425 category-months): **741 genuinely reported and compared (0 mismatches), 684 historically unavailable** (pre-2006, where Total/Public/Non-Public are all `"na"`) and correctly excluded from the comparison rather than treated as a match. Parent Total rows were then dropped from the final table (child rows retained) to prevent double counting; non-split services keep sector = `All`.
- Hospital-category labels (`Acute/Psychiatric/Community Hospitals Admissions`) renamed to `Acute/Psychiatric/Community Hospitals` to match the facility-type naming in Datasets 2–3.

**Facilities and beds, national (Dataset 2)**
- Filtered to 2015–2025; renamed `facility_type_a`→`facility_type`, `public_private`→`sector`; relabelled `Acute`→`Acute Hospitals` and `Not-for-Profit` casing standardised (canonical form used everywhere).
- Cast `year`, `no_of_facilities`, `no_beds` to integer. 0 missing values, 0 duplicate keys (`year`+`institution_type`+`facility_type`+`sector`), 0 negative counts.
- **5 rows retained unchanged** where `no_of_facilities == 0` but `no_beds > 0`: Public Inpatient Hospices, 2015–2019 (beds 40, 24, 24, 24, 24). Kept exactly as published: not a parsing error, no correction applied.

**Regional hospital beds (Dataset 3)**
- Parsed the 3-level indentation hierarchy (facility type → sector → planning region); melted year columns into long format; relabelled `Not-For-Profit`→`Not-for-Profit` to match Dataset 2.
- Reconciled region rows against sector subtotals (36 combos) and sector rows against facility-type totals (18 combos): **0 mismatches** at either level.
- Final table keeps **region-level leaf rows only**; facility-type and sector subtotal rows were excluded to prevent double counting.

## Validation Results (Task 5)

- No missing or negative values in any of the three processed files.
- No duplicate business keys in any file.
- Monthly admissions Total vs. Public+Non-Public: 741 of 1,425 category-months were genuinely reported and reconciled (0 mismatches); the remaining 684 are historically unavailable (pre-2006 `"na"` periods) and are excluded from the comparison rather than counted as a match.
- Regional beds vs. sector/facility-type source totals: reconciled for all 54 combos.
- Regional sum vs. national facilities figure, compared at `year + facility_type + sector` (2020–2025, Hospital rows only, 54 combos): **1 genuine mismatch**, 18 combos exist only in the national table (all with `national_value == 0`; the regional source omits zero-bed rows rather than listing them, not a numeric discrepancy).

## Unresolved Discrepancy: 2021 Public Community Hospital Beds

- National facilities dataset (Dataset 2): **1,180** beds.
- Sum of regional dataset (Dataset 3): **1,112** beds.
- **Difference: 68 beds.**
- Both original values are preserved unchanged in their respective processed files. No correction, averaging, or reconciliation was applied. This is a source-data discrepancy, not a cleaning error, and is flagged here for ChatGPT/analyst review before any downstream use of 2021 Community Hospital figures.

## Analytical Limitations Carried Forward

- Monthly **Non-Public** admissions (Dataset 1) are not assumed equivalent to **Private** or **Not-for-Profit** beds (Datasets 2–3); the source does not confirm this mapping, so no such comparison is made.
- No bed-occupancy or utilisation-rate metrics were calculated from admissions and bed-capacity figures combined.
- Dataset 1 remains monthly; Datasets 2–3 remain annual; no monthly-to-annual aggregation performed in this stage.
- Common coverage across all three datasets is still only 2020–2025.
- Residential Long-Term Care (Nursing Homes, Inpatient Hospices) has no regional breakdown and is absent from Dataset 3.

## Status
**Stage 2 (Data Cleaning and Preparation): Complete.** No EDA, charts, SQL, or modelling performed.
