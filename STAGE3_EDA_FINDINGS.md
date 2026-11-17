# Stage 3: EDA Findings

Supporting notebook: `notebooks/01_healthcare_eda.ipynb`. Supporting charts: `figures/fig01`–`fig07`.

## Findings

**1. Acute Hospital admissions remain Public-sector dominated and the largest single volume category, growing 31.7% over 2015–2025.**
Public + Non-Public Acute Hospital admissions rose from 499,889 (2015) to 658,221 (2025). Public admissions account for the large majority of this volume in every year (e.g. 548,517 of 658,221 in 2025). *Business relevance:* Acute Hospitals remain the dominant driver of total hospital admission volume and the primary focus for capacity planning. *Caveat:* this is admissions count, not patient count or severity-adjusted volume.

**2. Community Hospital admissions grew far faster in relative terms than Acute or Psychiatric admissions: +183.3% over 2015–2025 (10,670 → 30,231).**
This is the fastest-growing of the three admission categories by a wide margin, off a much smaller base than Acute Hospitals. One year (2023) shows an unexplained -9.0% dip against an otherwise consistent upward trend. *Business relevance:* signals a structural shift toward step-down/intermediate care that may be relevant to future capacity planning, independent of Acute Hospital trends. *Caveat:* the 2023 dip is observed, not explained. No cause is asserted.

**3. The five services selected for Figure 3 (Acute Admissions, Specialist Outpatient Clinics, Polyclinics, Dental Clinics, Day Surgeries) contracted in 2020 and rebounded in 2021, with Dental Clinics showing the largest swing (-34.4% then +31.9%), but this pattern was not universal across all service categories.**
2020 YoY changes: Dental Clinics -34.4%, A&E -16.9%, Day Surgeries -16.7%, Specialist Outpatient Clinics -15.3%, Polyclinics -10.4%, Acute Admissions -10.0%. However, **Community Hospital admissions grew in 2020 (+4.0%)** rather than contracting, and **Psychiatric Hospital admissions declined in *both* 2020 and 2021 (-8.8%, -2.4%)** rather than rebounding; A&E also continued to decline slightly in 2021 (-0.9%), only rebounding in 2022 (+14.9%). By 2023–2025, growth rates for all series had returned to pre-2020 ranges. *Business relevance:* confirms 2020–2022 was an unusual period, but its shape (direction, magnitude, timing of recovery) varied meaningfully by service; a single "pandemic-era dip" narrative does not fit every category. *Caveat:* this is a descriptive observation of timing and magnitude only. No causal mechanism (e.g. pandemic policy, care-seeking behaviour) is tested or claimed.

**4. Public Acute Hospital admissions grew faster than Public Acute Hospital bed capacity over 2015–2025 (index 2015=100: admissions reached ≈144.4 by 2025, beds reached ≈132.7).**
Both series are indexed to their own 2015 baseline so the *relative* growth rate can be compared despite different units. Admissions and beds tracked closely from 2020–2022, with admissions growth pulling further ahead from 2023 onward. *Business relevance:* a widening gap between admissions growth and bed-capacity growth is relevant to future capacity-planning discussions. *Caveat:* this is **not** an occupancy or utilisation-rate calculation. Admissions (a 12-month flow) and beds (a point-in-time stock) are not combined into a ratio anywhere in this project.

**5. Hospital bed capacity is heavily concentrated in the Central Region (≈52.5% of all hospital beds in 2025) and the North-East Region (≈21.0%); the remaining three regions each hold a broadly similar, smaller share (East ≈9.0%, North ≈10.0%, West ≈7.5%). Psychiatric Hospital beds are located exclusively in the North-East Region.**
All five planning regions grew in absolute bed count between 2020 and 2025 (e.g. Central Region 8,466 → 9,083; North Region 1,003 → 1,726, the largest relative increase). *Business relevance:* informs the physical geography of acute and community hospital capacity in Singapore. *Caveat:* this describes facility location only; it is **not** evidence that any region is over- or under-served, which would require population, catchment-area or demand data not present in this project.

## Known Source-Data Discrepancy: 2021 Public Community Hospital Beds

- National facilities dataset: **1,180** beds.
- Regional dataset (summed across regions): **1,112** beds.
- **Difference: 68 beds**, unresolved.
- Both values are preserved unmodified in their respective processed CSVs. No average, correction, or reconciliation has been applied at any stage. Any analysis of 2021 Community Hospital capacity, in this project or downstream, should state which of the two source values it is using.

## Promising Questions for SQL Analysis (Stage 4)

1. Which specific months/years account for the largest absolute (not just percentage) swings in each service, and do Acute/Community/Psychiatric admissions move together or independently month-to-month?
2. How does the Public-vs-Non-Public admissions split trend over time for Acute and Community Hospitals specifically: is Non-Public share growing, shrinking, or flat?
3. Which sector (Public or Non-Public) contributed most, numerically, to the 2022-2023 decline in Community Hospital admissions? (A decomposition question: this dataset cannot establish a causal explanation for *why* the decline occurred.)
4. At a facility-type + sector + year grain, where else (besides 2021 Community/Public) might the national and regional bed datasets diverge, even by smaller margins?
5. How does bed-count growth by region (2020–2025) compare to each region's facility-type mix: is growth concentrated in Acute or Community beds?

## Limitations Carried Forward

- No common join key across the three datasets; comparisons use shared dimensions (year, facility type, sector) only.
- Non-Public admissions are not assumed equivalent to Private/Not-for-Profit beds without further source-definition confirmation.
- No occupancy/utilisation-rate, forecasting, or statistical-significance analysis was performed anywhere in this project.
- Regional bed data covers 2020–2025 only; it cannot be extended back to match the longer monthly/national coverage.
- Seasonality findings (notebook Section 4) are descriptive month-of-year averages, not a statistically validated seasonal decomposition.
