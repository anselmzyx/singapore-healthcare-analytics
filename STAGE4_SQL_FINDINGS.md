# Stage 4: SQL Analysis & Business Insights

SQL files: `sql/01`–`sql/07`. Results: `results/sql/*.csv`. Runner: `scripts/run_sql_analysis.py` (DuckDB, in-memory, reads the three Stage 2 processed CSVs only).

## Business Question 1: Which services experienced the largest absolute changes?

**Answer:** `sql/01_annual_activity_yoy.sql` outputs 88 category-year rows across all 8 services, 2015-2025. Of these, 8 are 2015 baseline rows with no prior year to compare against (no YoY value, excluded from the ranking), leaving **80 valid year-over-year observations covering 2016-2025** that are actually ranked. Across that 80-observation set, Specialist Outpatient Clinics had both the single largest absolute drop (2020: **-807,320**, -15.3%) and the largest absolute rebound (2021: **+739,878**, +16.5%) of any service-year in the dataset. Polyclinics (2020: -698,619) and Dental Clinics (2020: -368,884) follow. **Percentage and absolute rankings diverge substantially**: Dental Clinics' 2020 contraction is the single largest *percentage* move across the full 80-observation ranking (-34.45%, pct_change_rank 1) but only the 8th-largest *absolute* move; conversely, Polyclinics' 2020 drop ranks 3rd by absolute size but only 18th by percentage. Small-base categories (Community Hospitals, Dental Clinics) repeatedly rank high on percentage change but low on absolute change, and vice versa for the largest-volume services (Polyclinics, Specialist Outpatient Clinics): a volume-based priority list and a growth-rate-based priority list would surface different services first, and this holds across the whole 2016-2025 period, not only in 2020.

*2019-2022 focus:* every one of the ten largest absolute moves in this window belongs to an outpatient/day-surgery service, not an admissions category; the largest admissions-category move in the window is Acute Hospitals 2020 (-61,625, -10.0%), ranked only 26th by absolute size.

## Business Question 2: How have Public and Non-Public admission shares changed?

**Answer:** Both Acute and Community Hospitals became markedly more Public-sector-weighted between 2015 and 2025, but by very different magnitudes:
- **Acute Hospitals:** Public share rose from 76.0% (2015) to 83.3% (2025), **+7.3 percentage points**.
- **Community Hospitals:** Public share rose from 20.5% (2015) to 66.5% (2025), **+46.0 percentage points**, a far larger structural shift in sector mix.

*Caveat:* these shares describe **admission activity** (how many patients were admitted under each sector), not the ownership distribution of available beds. "Non-Public" is Dataset 1's own category and is not assumed to map one-to-one onto the "Private"/"Not-for-Profit" bed sectors used in Datasets 2-3; no such equivalence is tested or used here. A rising Public share of *admissions* does not by itself imply the Public share of *bed capacity* moved by the same amount; Dataset 2 (`healthcare_facilities_annual.csv`) is the separate, correct source for bed-ownership distribution.

## Business Question 3: What drove the numerical decline in Community Hospital admissions in 2023?

**Answer:** The Public sector drove the entire 2022→2023 net decline. Public admissions fell by **-2,219** (14,747 → 12,528) while Non-Public admissions actually *rose* slightly by **+80** (8,931 → 9,011), partially offsetting the Public decline. Public accounts for **103.7%** of the net -2,139 change (Non-Public: -3.7%, i.e. moved in the opposite direction). By 2024, both sectors grew again (Public +4,716, Non-Public +544), and total admissions recovered to 26,799. **This is a numerical decomposition only. No cause for the Public-sector decline is identified or implied.**

## Business Question 4: How did hospital admissions grow relative to bed capacity?

**Answer:** Indexed to 2015=100, Public Acute Hospital admissions reached **144.4** by 2025 while Public Acute Hospital beds reached **132.7**: admissions grew faster than bed capacity over the decade, with the two tracking closely in 2020-2021 and the gap widening again from 2022 onward (index-point gap: +11.7 in 2025). This matches the Stage 3 EDA finding exactly (independently re-derived in SQL). **Admissions (a 12-month activity count) and beds (a point-in-time capacity figure) are never divided into a ratio anywhere in this analysis**; this is a comparison of two growth rates, not an occupancy or utilisation measure.

## Business Question 5: Where has regional hospital bed capacity grown?

**Answer:** In absolute terms, **North Region Acute Hospitals grew the most** (+619 beds, +77.9%, 2020→2025), followed by **Central Region Community Hospitals** (+412 beds, +119.4%, the fastest proportional growth of any sizeable category) and **Central Region Acute Hospitals** (+205 beds, +2.5%, slow in relative terms but still the single largest capacity block, 48.1% of the 2025 total on its own). One combination *declined*: **North-East Region Community Hospitals** (-42 beds, -5.4%). Regional shares of the 2025 total: Central 52.5%, North-East 21.0%, North 10.0%, East 9.0%, West 7.5%, consistent with Stage 3. *Reminder:* this describes facility location only; it is not evidence of regional need or under-service.

## Source Reconciliation Check (Task 7)

Independently re-derived in SQL (no hardcoded values): comparing the national facilities dataset against the regional dataset summed by year + facility_type + sector, 2020-2025 (54 combinations):
- **35 combinations match exactly.**
- **18 combinations exist only in the national dataset, all with a national value of 0**; the regional source omits zero-bed rows rather than listing them, correctly identified as not a real mismatch.
- **1 genuine mismatch: 2021 Community Hospitals, Public sector: national = 1,180, regional = 1,112, difference = 68.** This matches the figure identified in Stage 2/3 exactly, confirming the discrepancy is a genuine, reproducible feature of the source data rather than a Stage 2 processing artefact. Both values remain unmodified; no reconciliation was forced.

## How SQL Adds to / Refines the Stage 3 EDA

- Stage 3 identified *that* admissions grew faster than beds and *that* capacity is concentrated in Central Region; Stage 4's SQL independently re-derives the same index values (144.4 / 132.7) and regional shares (52.5% / 21.0% / 10.0% / 9.0% / 7.5%) from scratch in a different tool, cross-validating the Stage 3 notebook results rather than just repeating them.
- SQL adds two analyses Stage 3 did not perform: a **sector-level decomposition** of the 2023 Community Hospital decline (Question 3) and an explicit **absolute-vs-percentage ranking comparison** (Question 1); both are naturally expressed with window functions (`LAG`, `RANK`, `FIRST_VALUE`) rather than ad hoc pandas code.
- The reconciliation check (Task 7) independently reproduces the Stage 2 Python-based discrepancy finding using SQL only, closing the loop on whether the 68-bed gap was a processing artefact (it is not).

## Healthcare-Management Considerations (descriptive, not recommendations)

1. The widening gap between Public Acute admissions growth (+44% since 2015) and Public Acute bed growth (+33%) is a capacity-planning signal worth monitoring, though it is not an occupancy measure and says nothing about whether current capacity is adequate.
2. Community Hospitals underwent the largest sector-mix shift in the dataset (Public share of *admissions* +46 points since 2015), a structural change in who is providing this care that may be relevant to future Public/Non-Public capacity planning conversations. This describes admission activity only, not a confirmed equivalent shift in bed ownership.
3. Regional capacity growth was uneven and not simply proportional to existing size. North Region grew fastest proportionally (+77.9% Acute beds) while North-East Community Hospital beds declined, which is worth further investigation before drawing conclusions about regional strategy.
4. The 2023 Community Hospital admissions decline was concentrated entirely in the Public sector; any operational review of that year should focus there rather than treating it as a sector-wide trend.
5. The unresolved 68-bed 2021 discrepancy means any report quoting 2021 Community Hospital bed capacity should state which source (national or regional) it draws from, as the two are not interchangeable for that specific year.

## Limitations and Unanswered Questions

- No causal mechanism is tested or implied anywhere in this project (Stage 1-4). All "drove"/"contributed" language refers to numerical decomposition, not explanation.
- Non-Public admissions (Dataset 1) are not confirmed equivalent to Private/Not-for-Profit beds (Datasets 2-3).
- No occupancy, utilisation-rate, or efficiency ratio was calculated at any stage.
- The regional dataset covers only 2020-2025; earlier regional trends cannot be assessed.
- Why the 2023 Community Hospital Public-sector decline occurred, and why North-East Region Community Hospital beds declined 2020-2025, remain open questions this dataset cannot answer.

## Known Source-Data Discrepancy (carried forward)

2021 Public Community Hospital beds: national dataset = **1,180**, regional dataset (summed) = **1,112**, difference = **68 beds**. Independently reconfirmed via SQL in this stage (`sql/06_source_reconciliation_check.sql`). Both values remain preserved and unmodified across every stage of this project.
