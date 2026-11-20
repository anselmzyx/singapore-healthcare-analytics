# Power BI Build Guide: Singapore Healthcare Analytics (Stage 5A)

This guide documents how the Power BI dashboard was built manually in Power BI Desktop (via Parallels on a Mac), and serves as the reference for rebuilding or auditing it. The finished `.pbix` file is published at `dashboard/Singapore_Healthcare_Analytics.pbix`.

## Status of this guide (updated 20 November 2026)

This guide mixes the **original Stage 5A build plan** with the **final as-built dashboard**. Where they differ, the as-built description wins. Each kind of content is labelled:

| Content | Status |
|---|---|
| Part 1 (data model), Part 4 (build steps) | Original plan, still accurate for the model; step 8 is updated for the final measures |
| Part 2 (page layouts, interactions) | As-built, corrected against screenshots and the saved report definition |
| **Part 3A (final as-built measures)** | **Five final-dashboard measures, supplied by the owner from Power BI Desktop** |
| Part 3 (the 20 Stage 5A measures) | **Historical.** Kept unedited as the original build reference |

How each statement was established:
- **Verified independently (static, read-only):** field bindings, visual-level filters and interaction settings in the saved report definition (the `Report/definition/` JSON inside the `.pbix`); the dashboard values in both screenshots against the processed CSVs and `results/sql/`.
- **Owner-supplied, manually checked:** the five formulas in Part 3A, copied from Power BI Desktop, and the manual slicer tests recorded in §2.3. They were *not* extracted from the PBIX's compressed data model and have not been independently re-run.
- **Not verified:** the formulas of any other final measure; the no-data title correction (owner-reported, not retested); anything that needs Power BI Desktop to run. The compressed `DataModel` can't be read outside Power BI Desktop.

**Source files** (all already exist, all unchanged by this stage):
- `data/processed/healthcare_utilisation_monthly.csv`
- `data/processed/healthcare_facilities_annual.csv`
- `data/processed/hospital_beds_region_annual.csv`

---

## Part 1: Data Model

### 1.1 Load the three CSVs

1. Open **Power BI Desktop**.
2. **Home → Get Data → Text/CSV**.
3. Navigate to the project's `data/processed/` folder (via Parallels, your Mac drive is usually visible under `This PC` or a mapped network drive; look for a drive showing your Mac username, then browse to `Desktop/Data Analyst Portfolio/02_Singapore_Healthcare_Analytics/data/processed/`).
4. Select `healthcare_utilisation_monthly.csv` → **Load** (or **Transform Data** if you want to rename before loading; either works).
5. Repeat **Get Data → Text/CSV** for `healthcare_facilities_annual.csv` and `hospital_beds_region_annual.csv`.
6. You should now have three tables in the **Fields** pane, named after their CSV filenames.

### 1.2 Rename tables clearly

In the **Fields** pane, right-click each table → **Rename**:

| CSV file | Rename table to |
|---|---|
| `healthcare_utilisation_monthly.csv` | **Monthly Utilisation** |
| `healthcare_facilities_annual.csv` | **Facilities Annual** |
| `hospital_beds_region_annual.csv` | **Regional Beds Annual** |

(This guide uses these three names everywhere below. Your DAX and field references must match exactly.)

### 1.3 Verify data types

Open **Transform Data** (Power Query Editor) and check each table's column types (shown as a small icon in each column header). Power BI usually detects these correctly from CSV, but confirm:

**Monthly Utilisation**: `date` = Date, `year` = Whole Number, `month` = Whole Number, `measure_type` = Text, `service_category` = Text, `sector` = Text, `count` = Whole Number

**Facilities Annual**: `year` = Whole Number, `institution_type` = Text, `facility_type` = Text, `sector` = Text, `no_of_facilities` = Whole Number, `no_beds` = Whole Number

**Regional Beds Annual**: `year` = Whole Number, `facility_type` = Text, `sector` = Text, `planning_region` = Text, `no_beds` = Whole Number

To fix a type: click the column, then the type icon → select the correct type → **Home → Close & Apply**.

### 1.4 Create a Year dimension table

The three fact tables have **different grains** (Monthly Utilisation = one row per date+category+sector; Facilities Annual = one row per year+facility+sector, national; Regional Beds Annual = one row per year+facility+sector+region). None of them share a row-level key, so **do not** relate them directly to each other: a direct year-to-year relationship between two fact tables would be many-to-many and would silently multiply totals.

Instead, create a small **Year** dimension table and connect it to each fact table one-to-many. This lets a single Year-based control filter all three tables in a coordinated way; it does **not** make the underlying fact rows directly joinable to each other.

1. **Home → Enter Data**.
2. Create one column named `Year`, type Whole Number, with 11 rows: `2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025`.
3. Name the table **Year** → **Load**.

### 1.5 Define relationships

Go to **Model view** (left-hand icon stack). Drag to create these three relationships:

| From | To | Cardinality | Cross-filter direction |
|---|---|---|---|
| `Year[Year]` | `Monthly Utilisation[year]` | One to many (1:*) | Single (Year → Monthly Utilisation) |
| `Year[Year]` | `Facilities Annual[year]` | One to many (1:*) | Single (Year → Facilities Annual) |
| `Year[Year]` | `Regional Beds Annual[year]` | One to many (1:*) | Single (Year → Regional Beds Annual) |

For each relationship: double-click it → confirm **Cardinality = One to many**, **Cross filter direction = Single**. Single direction means Year can filter the fact tables, but a fact table can never filter Year (or, through Year, another fact table); this is what keeps the model simple and avoids ambiguous filter paths.

**Do not** create any relationship directly between Monthly Utilisation, Facilities Annual, and Regional Beds Annual. They are deliberately left unconnected to each other; they only share the Year table as a common filtering bridge, never a row-level join.

### 1.6 Why the Year table matters

`Year[Year]` serves two distinct purposes in the final dashboard, not just one:

1. **The shared axis for Page 2's "Admissions vs. Bed Capacity" chart**, which plots a measure from **Monthly Utilisation** and a measure from **Facilities Annual** on the *same* axis. Power BI needs a common field both measures can be filtered by; that's `Year[Year]`.
2. **Both pages' Year Range slicers** are themselves built from `Year[Year]` (confirmed in the published dashboard's report definition), which is how a single slicer on each page can reach visuals built from any of the three fact tables at once, since each has its own relationship back to `Year`.

Use `Year[Year]` as the axis for the indexed chart, and as the field for each page's Year Range slicer (details in Part 2).

---

## Part 2: Dashboard Design

**Historical note:** this Part originally documented the Stage 5A plan before the dashboard was built. The dashboard has since been built and redesigned, and published at `dashboard/Singapore_Healthcare_Analytics.pbix`. The content below was corrected against the two current screenshots (`dashboard/screenshots/01_healhcare_service_demand_and_utilisation.png`, `dashboard/screenshots/02_hospital_capacity_and_regional_distribution.png`) and against a read-only inspection of the PBIX's report definition (the human-readable `Report/definition/...` JSON inside the `.pbix` zip, which records each visual's field bindings and interaction settings). The PBIX's compiled data model (`DataModel`) is a binary VertiPaq part with no readable DAX text, so measure *formulas* could not be inspected this way; only measure *names* and *field roles* could be confirmed from the report definition. The formulas of the final-dashboard measures that are not in Part 3 were later supplied by the owner and are documented in Part 3A.

Two report pages, both **2560 × 1440 (QHD)**, sharing a navy-and-teal colour theme and a common "Singapore Healthcare Analytics" title. Rename the page tabs:
- Page 1 → **01 Service Demand & Utilization** (on-report subtitle: "Healthcare Service Demand & Utilization | 2015-2025")
- Page 2 → **02 Hospital Capacity & Regions** (on-report subtitle: "Hospital Capacity & Regional Distribution | 2015-2025")

### Guardrail used throughout this design

Both pages now carry a **Year Range slicer** bound to `Year[Year]` (confirmed by inspecting both slicer visuals' field bindings), not to a single fact table's own `year` column. Because `Year[Year]` has an active one-to-many relationship to all three fact tables (§1.5), this slicer can, by default, filter *any* visual built from any of the three tables. Two separate mechanisms keep the KPI cards fixed at 2025 despite that:
1. Each fixed-2025 measure (Part 3) still uses `REMOVEFILTERS('Year')` inside `CALCULATE`, so the measure returns 2025 regardless of filter context.
2. As confirmed directly in the report definition, every KPI card visual also has an explicit **NoFilter** interaction set against the slicer (and, on Page 2, against the two bed-capacity column charts as well), so the slicer cannot even attempt to filter them.

This is belt-and-braces: either mechanism alone would keep the cards fixed; the published report uses both. The historical trend charts, by contrast, are **not** given a NoFilter override against the slicer, so they do respond to the selected year range, consistent with "historical visuals responding to the selected period where applicable." The one exception is the regional matrix on Page 2 (§2.2), which does not simply filter by range: see its own entry below.

---

### 2.1 PAGE 1: Service Demand & Utilisation

**KPI cards (top row, 4 cards, each visual type = Card), fixed to 2025**

| Card title | Measure | Expected 2025 value |
|---|---|---|
| Total Admissions 2025 | `[Total Admissions 2025]` | 699,606 |
| Public Acute Admissions 2025 | `[Public Acute Admissions 2025]` | 548,517 |
| Specialist Outpatient Attendances 2025 | `[Specialist Outpatient Attendances 2025]` | 5,728,143 |
| Public Acute Admission Share (2025) | `[Public Admission Share 2025]` (filtered `service_category = "Acute Hospitals"`) | 83.3% |

Confirmed directly from the report definition: all four cards are bound to exactly these four measures from Part 3, unchanged.

**Chart 1: "Hospital Admissions by Type"**
- Visual type: **Line chart with small multiples** (one panel each for Acute, Community and Psychiatric Hospitals)
- Values: `[Total Admissions]`, broken out per panel by `service_category`
- Responds to the Year Range slicer (confirmed: no NoFilter override against this chart)
- Purpose: shows admissions trends by hospital type on three separately-scaled panels, since Acute (~500K-658K) dwarfs Community (~11K-30K) and Psychiatric (~8K-11K).

**Chart 2: "Outpatient Attendances by Service"**
- Visual type: **Line chart with small multiples**, 2×2 layout (Accident & Emergency Departments, Dental Clinics, Polyclinics, Specialist Outpatient Clinics)
- Values: `[Outpatient Attendances]`, broken out per panel by `service_category`
- Responds to the Year Range slicer
- Purpose: shows the four outpatient services on separately-scaled panels, each visibly dipping around 2020.

**Chart 3: "Public Share of Hospital Admissions"**
- Visual type: **Line chart**, two series (Acute Hospitals, Community Hospitals)
- Values: `[Public Admission Share]`
- Responds to the Year Range slicer
- Purpose: shows the different pace of the Public-sector admission-share shift between the two hospital types. **This measures admission activity, not bed ownership.**

**Chart 4: "Annual Healthcare Activity Growth (2019-2022)"**
- Visual type: **Clustered column chart**, legend = `service_category` (Acute Hospitals, Community Hospitals, Dental Clinics, Specialist Outpatient Clinics)
- Final field configuration (report bindings confirmed independently; formula supplied by the owner, see Part 3A): X-axis `Year[Year]`, Y-axis **`[Service YoY %]`**, legend `Monthly Utilisation[service_category]`. The Part 3 measure `[YoY % Change]` is the original plan's measure and is **not** the measure used by the final chart.
- Filters: a visual-level filter on `Year[Year]` (2019 to 2022) and one restricting `service_category` to the four services shown
- Confirmed **NoFilter** against the Year Range slicer: this chart keeps its own fixed 2019-2022 window regardless of the slicer's range, the same logic previously used to protect the old "2020 vs. 2025" comparison chart.
- Purpose: year-over-year growth for four services around the 2020-2022 period, descriptive only; no causal claim.

---

### 2.2 PAGE 2: Hospital Capacity & Regions

**KPI cards (top row, 4 cards, each visual type = Card), fixed to 2025**

| Card title | Measure | Expected 2025 value |
|---|---|---|
| Total Hospital Beds 2025 | `[Total Hospital Beds 2025]` | 17,296 |
| Public Acute Hospital Beds 2025 | `[Public Acute Hospital Beds 2025]` | 10,784 |
| Admissions Index 2025 (2015=100) | `[Admissions Index (2015=100)]` filtered `year = 2025` | 144.4 |
| Bed Capacity Index 2025 (2015=100) | `[Bed Capacity Index (2015=100)]` filtered `year = 2025` | 132.7 |

Confirmed directly from the report definition: the published cards use measures named **"Admissions Index (2015 BASE 100)"** and **"Bed Capacity Index (2015 Base 100)"**, a cosmetic naming variant of the `[Admissions Index (2015=100)]` / `[Bed Capacity Index (2015=100)]` measures documented in Part 3. The Part 3 code blocks are kept exactly as originally written (they are the historical Stage 5A reference and must not be edited); if you are rebuilding from scratch, naming your measures either way is equivalent, as long as the underlying logic matches Part 3.

**Chart 1: "Hospital Bed Capacity by Sector"**
- Visual type: **Stacked column chart**
- X-axis: `Year[Year]`, Legend: `Facilities Annual[sector]`
- Values: `[Total Hospital Beds]`
- Responds to the Year Range slicer; confirmed **NoFilter** set so that clicking a bar does not cross-filter the KPI cards
- Purpose: bed capacity composition by ownership sector, 2015-2025, excluding Residential Long-Term Care throughout.

**Chart 2: "Hospital Bed Capacity by Type"**
- Visual type: **Stacked column chart**
- X-axis: `Year[Year]`, Legend: `Facilities Annual[facility_type]`
- Values: `[Total Hospital Beds]`
- Responds to the Year Range slicer; confirmed **NoFilter** against the KPI cards, same as Chart 1
- Purpose: bed capacity composition by Acute/Community/Psychiatric, 2015-2025.

**Chart 3: "Hospital Beds by Region & Type"**
- Visual type: **Matrix**, rows = `Regional Beds Annual[planning_region]`, columns = `Regional Beds Annual[facility_type]`, with conditional-formatting background colour on the values
- Values and title: bound to two measures confirmed by name in the report definition, **`Regional Beds (Selected Year)`** (values) and **`Regional Beds Matrix Title`** (title), both shown in the report bindings under the `Facilities Annual` table. They build on **`Regional Hospital Beds`**. None of the three is among the original 20 Stage 5A measures in Part 3. Their formulas are documented in **Part 3A** (owner-supplied, not independently extracted).
- Behaviour: the matrix shows the **latest available year within the currently selected slicer range**, not a sum across the range, and the title shows that year. Moving the range's end year from 2021 to 2025 changes the total from 15,665 to 17,296 (one year each, never a multi-year sum). If you rebuild this, pick the single latest year in range rather than letting the matrix use a plain `SUM` across however many years the slicer spans.
- Regional coverage begins in **2020**. If the selected range ends before 2020 (for example 2015-2019) there are no regional rows, the matrix is empty, and the title reads **"Hospital Beds by Region & Type (No Data)"** rather than showing empty parentheses. This no-data title is the final version of the title measure (Part 3A, Measure 5; owner-reported, not retested here).
- Expected result at the 2025 end of the range: Central Region / Acute Hospitals is the largest single cell (8,326); Psychiatric Hospitals is blank everywhere except North-East Region (1,950); grand total 17,296.

**Chart 4: "Public Acute Admissions vs Bed Capacity (2015=100)"**
- Visual type: **Line chart**, two series
- X-axis: `Year[Year]` (required so one axis can carry a measure from `Monthly Utilisation` and a measure from `Facilities Annual`; see §1.6)
- Values: the two index measures from the KPI table above
- Confirmed **no NoFilter override** against the Year Range slicer on this chart, but the index measures' own `REMOVEFILTERS('Year')` (Part 3) re-fetches the fixed 2015 baseline regardless of the slicer's range, so the indexed line retains its original 2015 = 100 baseline even if the visible range is narrowed.
- **Label the baseline clearly** (the published report's subtitle states the coverage period). **Do not** label this chart "occupancy" or "utilisation rate" anywhere; it is a growth-rate comparison only, never a ratio of admissions to beds.

**Source note (confirmed present on the published Page 2 footer):** *"Source: Singapore MOH / data.gov.sg. Regional beds reflect facility locations, not patient demand. The 2021 public community hospital bed counts differ between national (1,180) and regional (1,112) datasets. Admissions and bed-capacity indices do not measure occupancy."*

### 2.3 Slicer and interaction summary (both pages)

Both pages use a single **Year Range slicer** (a between-style slicer bound to `Year[Year]`) rather than the Page-2-only, single-select slicer originally planned in Stage 5A. Confirmed interaction behaviour, read directly from each page's report definition:

| Visual | Interaction with the Year Range slicer |
|---|---|
| All 4 KPI cards (both pages) | **None** (protected by `REMOVEFILTERS('Year')` in the measure and an explicit NoFilter interaction) |
| Page 1, Charts 1-3 (admissions/outpatient/share trends) | Responds to the slicer (no override found) |
| Page 1, Chart 4 (Annual Healthcare Activity Growth) | **None** (its own visual-level filter fixes it to 2019-2022) |
| Page 2, Charts 1-2 (bed capacity by sector/type) | Responds to the slicer; also set to NoFilter *against the KPI cards* so clicking a bar doesn't cross-filter them |
| Page 2, Chart 3 (regional matrix) | Reachable by the slicer, but its own measure logic shows only the latest year in range rather than summing |
| Page 2, Chart 4 (indexed line chart) | Reachable by the slicer for its visible range, but the 2015 baseline itself is pinned by `REMOVEFILTERS('Year')` regardless |

To configure this yourself: build one slicer per page from `Year[Year]` as a **Between** (range) slicer, then for each KPI card and for Page 1's Chart 4, select the slicer → **Format → Edit interactions** → click the "no interaction" (circle-slash) icon against that visual.

**Manual tests (owner-reported, Power BI Desktop, 20 November 2026).** These are the only interactive tests this guide records. They were run by the project owner and have not been independently re-run; the static report-definition checks above are consistent with them.

| Page | Slicer set to | Observed |
|---|---|---|
| 1 | 2023-2025 (from 2015-2025) | All four KPI cards stayed at their 2025 values. Hospital Admissions by Type, Outpatient Attendances by Service and Public Share of Hospital Admissions showed 2023-2025 only. Annual Healthcare Activity Growth stayed fixed at 2019-2022. |
| 2 | 2020-2021 | Four KPI cards stayed at 2025 values. Both bed-capacity charts and the indexed chart followed the range. The regional matrix showed 2021 only, grand total **15,665**. |
| 2 | 2023-2025 | The regional matrix showed 2025, grand total **17,296**, title "Hospital Beds by Region & Type (2025)". |
| 2 | 2015-2019 | No regional figures (correct: regional data starts in 2020). The title previously showed empty parentheses; the title measure was then updated to show "(No Data)". The updated title was not retested by the author of this guide. |

The two regional totals match `data/processed/hospital_beds_region_annual.csv` (2021: 15,665; 2025: 17,296), which was checked independently. Not tested: other slicer ranges, cross-filtering by clicking visuals, or reopening the saved file on another machine.

**Before saving or sharing the `.pbix`, reset each Year Range slicer to the full 2015-2025 range.** A slicer selection is saved inside the file, and a leftover test range (for example "up to 2020") makes the report open on a narrowed period that doesn't match the screenshots.

---

## Part 3A: Final as-built measures (owner-supplied)

These five measures are used by the final dashboard but are **not** among the 20 historical Stage 5A measures in Part 3. The project owner copied their formulas from Power BI Desktop on 20 November 2026. They are documented here exactly as supplied. They were **not** extracted from the PBIX's compressed data model, and they have not been independently re-run. Which visual uses each measure was confirmed independently from the report definition.

| # | Measure | Used by | Replaces / relates to |
|---|---|---|---|
| 1 | `Service Activity` | Base measure for `Service YoY %` | New helper |
| 2 | `Service YoY %` | Page 1 chart "Annual Healthcare Activity Growth (2019-2022)" | **Replaces** the Part 3 measure `YoY % Change`, which the final chart does not use |
| 3 | `Regional Hospital Beds` | Base measure for the regional matrix | New helper (Part 3 has a similar `Regional Beds`) |
| 4 | `Regional Beds (Selected Year)` | Page 2 regional matrix values | New |
| 5 | `Regional Beds Matrix Title` | Page 2 regional matrix title | New; the original version is superseded (below) |

### 1. Service Activity
```dax
Service Activity =
SUM('Monthly Utilisation'[count])
```
A plain sum of `count` in the current filter context. It has no `measure_type` filter, so it is only safe where `service_category` is already in context. On the Page 1 growth chart `service_category` is the legend, so each series isolates one service (Public and Non-Public rows are added together; the parent total rows were dropped in cleaning, so nothing is counted twice).

### 2. Service YoY %
```dax
Service YoY % =
VAR CurrentYear = SELECTEDVALUE('Year'[Year])
VAR CurrentCount = [Service Activity]
VAR PreviousCount =
    CALCULATE(
        [Service Activity],
        REMOVEFILTERS('Year'),
        'Monthly Utilisation'[year] = CurrentYear - 1
    )
RETURN
    IF(
        ISBLANK(CurrentYear),
        BLANK(),
        DIVIDE(CurrentCount - PreviousCount, PreviousCount)
    )
```
Year-over-year change for the year on the chart's axis. `SELECTEDVALUE` returns a year only when exactly one year is in context, otherwise the measure is blank. `REMOVEFILTERS('Year')` lets the prior-year lookup ignore the Year filter, so 2019's growth can read 2018 even though 2018 isn't on the axis. `DIVIDE` returns blank if there is no prior-year value.

Final field configuration: X-axis `Year[Year]`, Y-axis `[Service YoY %]`, legend `Monthly Utilisation[service_category]`. The chart is fixed at 2019-2022 when the Year Range slicer changes (NoFilter interaction plus a visual-level year filter, both confirmed independently in the report definition). For reference, the processed data gives 2020 growth of Dental Clinics -34.4% and Community Hospitals +4.0%, matching the screenshot.

### 3. Regional Hospital Beds
```dax
Regional Hospital Beds =
SUM('Regional Beds Annual'[no_beds])
```
A plain sum of regional beds in the current filter context.

### 4. Regional Beds (Selected Year)
```dax
Regional Beds (Selected Year) =
VAR SelectedYear =
    MAX('Regional Beds Annual'[year])
RETURN
    CALCULATE(
        [Regional Hospital Beds],
        KEEPFILTERS('Regional Beds Annual'[year] = SelectedYear)
    )
```
Shows the latest year available within the selected range instead of adding years together. Each matrix cell finds the latest regional year in its own filter context and sums beds for that year only. `KEEPFILTERS` keeps the existing filter on the year column instead of replacing it. This gives the range's latest year in every cell because all 11 region-and-facility-type combinations have rows in every year from 2020 to 2025 (checked in `hospital_beds_region_annual.csv`). If a combination were missing its latest year, its cell would silently show an earlier year. Where no regional rows exist (a range before 2020), the measure is blank.

### 5. Regional Beds Matrix Title (final version)
```dax
Regional Beds Matrix Title =
VAR SelectedYear =
    MAX('Regional Beds Annual'[year])
RETURN
    IF(
        ISBLANK(SelectedYear),
        "Hospital Beds by Region & Type (No Data)",
        "Hospital Beds by Region & Type (" &
        FORMAT(SelectedYear, "0") & ")"
    )
```
Dynamic title. For a range with regional data it reads "... (2025)" and so on; for a range before 2020 it reads "(No Data)". The no-data branch is the owner's correction, reported but not retested here.

**Historical version (superseded):**
```dax
Regional Beds Matrix Title =
"Hospital Beds by Region & Type (" &
FORMAT(MAX('Regional Beds Annual'[year]), "0") &
")"
```
With no regional data this produced empty parentheses ("Hospital Beds by Region & Type ()").

---

## Part 3: DAX Measures (historical Stage 5A reference)

**Historical.** The 20 measures below are the original Stage 5A formulas and are kept exactly as first written. They have not been edited. Field-binding inspection of the published report definition confirms all four Page 1 KPI cards and both Page 2 stacked-column charts still use these exact measure names. The two index measures are also still in use on Page 2 Chart 4, under cosmetic name variants (`Admissions Index (2015 BASE 100)`, `Bed Capacity Index (2015 Base 100)`) noted in §2.2. The final dashboard also uses the five measures in Part 3A, and `YoY % Change` below is **not** the measure behind the Page 1 growth chart (that is `Service YoY %`). Do not assume the final PBIX contains exactly 20 measures, or that every final formula is documented: only the Part 3 formulas (original build) and the Part 3A formulas (owner-supplied) are.

Create each measure in the table listed (right-click the table → **New measure**). Format numbers with thousands separators; format `%` measures as Percentage with 1 decimal place.

### In `Monthly Utilisation`

```dax
Total Admissions =
CALCULATE(
    SUM('Monthly Utilisation'[count]),
    'Monthly Utilisation'[measure_type] = "Hospital Admissions"
)
```
Calculates total hospital admissions (Acute + Community + Psychiatric, Public + Non-Public combined) for whatever year/filter context is active. Does **not** include Outpatient Attendances or Day Surgeries. Used in trend/legend charts. Expected 2025 value (no other filters): **699,606**.

```dax
Total Admissions 2025 =
CALCULATE(
    [Total Admissions],
    REMOVEFILTERS('Year'),
    'Monthly Utilisation'[year] = 2025
)
```
Same as above, but hardcoded to 2025. `REMOVEFILTERS('Year')` first clears any filter coming from the Year dimension table (e.g. if a Year-table slicer is ever added to this page later), then the explicit `'Monthly Utilisation'[year] = 2025` filter pins the year directly on the fact table itself. Used only in the Page 1 KPI card; it always shows 2025 regardless of what else is on the report. Expected value: **699,606**.

```dax
Public Acute Admissions =
CALCULATE(
    SUM('Monthly Utilisation'[count]),
    'Monthly Utilisation'[measure_type] = "Hospital Admissions",
    'Monthly Utilisation'[service_category] = "Acute Hospitals",
    'Monthly Utilisation'[sector] = "Public"
)
```
Public-sector Acute Hospital admissions only. Expected 2025 value: **548,517**.

```dax
Public Acute Admissions 2025 =
CALCULATE(
    [Public Acute Admissions],
    REMOVEFILTERS('Year'),
    'Monthly Utilisation'[year] = 2025
)
```
Fixed-2025 KPI-card version; `REMOVEFILTERS('Year')` keeps it fixed at 2025 even if a Year-table filter is ever active. Expected value: **548,517**.

```dax
Public Community Admissions =
CALCULATE(
    SUM('Monthly Utilisation'[count]),
    'Monthly Utilisation'[measure_type] = "Hospital Admissions",
    'Monthly Utilisation'[service_category] = "Community Hospitals",
    'Monthly Utilisation'[sector] = "Public"
)
```
Public-sector Community Hospital admissions only. Expected 2025 value: **20,107**.

```dax
Public Community Admissions 2025 =
CALCULATE(
    [Public Community Admissions],
    REMOVEFILTERS('Year'),
    'Monthly Utilisation'[year] = 2025
)
```
Fixed-2025 KPI-card version; `REMOVEFILTERS('Year')` keeps it fixed at 2025 even if a Year-table filter is ever active. Expected value: **20,107**.

```dax
Specialist Outpatient Attendances =
CALCULATE(
    SUM('Monthly Utilisation'[count]),
    'Monthly Utilisation'[measure_type] = "Outpatient Attendances",
    'Monthly Utilisation'[service_category] = "Specialist Outpatient Clinics"
)
```
Specialist Outpatient Clinics attendances only (not A&E/Polyclinics/Dental). Expected 2025 value: **5,728,143**.

```dax
Specialist Outpatient Attendances 2025 =
CALCULATE(
    [Specialist Outpatient Attendances],
    REMOVEFILTERS('Year'),
    'Monthly Utilisation'[year] = 2025
)
```
Fixed-2025 KPI-card version; `REMOVEFILTERS('Year')` keeps it fixed at 2025 even if a Year-table filter is ever active. Expected value: **5,728,143**.

```dax
Outpatient Attendances =
CALCULATE(
    SUM('Monthly Utilisation'[count]),
    'Monthly Utilisation'[measure_type] = "Outpatient Attendances"
)
```
All four outpatient categories combined (used with `service_category` on Legend in Chart 2, Page 1, so each legend line isolates its own category automatically). Never combine this with `[Total Admissions]` into one number.

```dax
Public Admission Share =
DIVIDE(
    CALCULATE(
        SUM('Monthly Utilisation'[count]),
        'Monthly Utilisation'[measure_type] = "Hospital Admissions",
        'Monthly Utilisation'[sector] = "Public"
    ),
    CALCULATE(
        SUM('Monthly Utilisation'[count]),
        'Monthly Utilisation'[measure_type] = "Hospital Admissions",
        'Monthly Utilisation'[sector] IN {"Public", "Non-Public"}
    )
)
```
Public admissions as a share of (Public + Non-Public) admissions, within whatever `service_category` is in context (e.g. from a chart's Legend). `DIVIDE` returns blank instead of an error if the denominator is ever zero. Expected 2025 values: Acute Hospitals **83.3%**, Community Hospitals **66.5%**, matching `results/sql/02_sector_share_admissions.csv` exactly. **This measures admission activity, not bed ownership**; label accordingly.

```dax
Public Admission Share 2025 =
CALCULATE(
    [Public Admission Share],
    REMOVEFILTERS('Year'),
    'Monthly Utilisation'[year] = 2025
)
```
Fixed-2025 KPI-card version (use with a `service_category` filter on the card, e.g. "Acute Hospitals", to get 83.3%); `REMOVEFILTERS('Year')` keeps it fixed at 2025 even if a Year-table filter is ever active. The existing `service_category`/sector logic inside `[Public Admission Share]` is unchanged.

```dax
Admissions Index (2015=100) =
VAR Baseline =
    CALCULATE(
        [Public Acute Admissions],
        REMOVEFILTERS('Year'),
        'Monthly Utilisation'[year] = 2015
    )
RETURN
    DIVIDE([Public Acute Admissions], Baseline) * 100
```
Indexes Public Acute Hospital admissions to their own 2015 value = 100. **This measure is plotted on a chart whose axis is `Year[Year]` (see Chart 2, §2.2), not `Monthly Utilisation[year]` directly**, so the ambient filter context comes from the Year dimension table, propagating through the relationship to Monthly Utilisation. `REMOVEFILTERS('Year')` explicitly clears that Year-table filter before the explicit `'Monthly Utilisation'[year] = 2015` filter is applied, guaranteeing `Baseline` always re-fetches the genuine 2015 value no matter which year is selected on the axis. Designed to be plotted with `Year[Year]` on the axis, producing a rising index line. Expected 2025 value: **144.4**.

```dax
YoY % Change =
VAR CurrentYear = MAX('Monthly Utilisation'[year])
VAR CurrentVal = CALCULATE(SUM('Monthly Utilisation'[count]), 'Monthly Utilisation'[year] = CurrentYear)
VAR PriorVal = CALCULATE(SUM('Monthly Utilisation'[count]), 'Monthly Utilisation'[year] = CurrentYear - 1)
RETURN
    DIVIDE(CurrentVal - PriorVal, PriorVal)
```
Year-over-year percentage change for whatever `service_category` is in context (via chart Legend). Uses `MAX(year)` so it correctly reads "the year of this chart row" rather than being confused by a wider filter range. Expected value for `service_category = "Dental Clinics"`, year = 2020: **≈-34.4%**. *Historical: the final Page 1 chart uses `Service YoY %` (Part 3A, Measure 2) instead.*

### In `Facilities Annual`

```dax
Total Hospital Beds =
CALCULATE(
    SUM('Facilities Annual'[no_beds]),
    'Facilities Annual'[institution_type] = "Hospital"
)
```
Total Acute + Community + Psychiatric Hospital beds, **excluding** Residential Long-Term Care (Nursing Homes, Inpatient Hospices). Expected 2025 value: **17,296**, which independently matches the Regional Beds Annual 2025 total exactly, a useful cross-check.

```dax
Total Hospital Beds 2025 =
CALCULATE(
    [Total Hospital Beds],
    REMOVEFILTERS('Year'),
    'Facilities Annual'[year] = 2025
)
```
Fixed-2025 KPI-card version; `REMOVEFILTERS('Year')` keeps it fixed at 2025 even if a Year-table filter is ever active. Expected value: **17,296**.

```dax
Public Acute Hospital Beds =
CALCULATE(
    SUM('Facilities Annual'[no_beds]),
    'Facilities Annual'[institution_type] = "Hospital",
    'Facilities Annual'[facility_type] = "Acute Hospitals",
    'Facilities Annual'[sector] = "Public"
)
```
Public-sector Acute Hospital beds only. Expected 2025 value: **10,784**.

```dax
Public Acute Hospital Beds 2025 =
CALCULATE(
    [Public Acute Hospital Beds],
    REMOVEFILTERS('Year'),
    'Facilities Annual'[year] = 2025
)
```
Fixed-2025 KPI-card version; `REMOVEFILTERS('Year')` keeps it fixed at 2025 even if a Year-table filter is ever active. Expected value: **10,784**.

```dax
Bed Capacity Index (2015=100) =
VAR Baseline =
    CALCULATE(
        [Public Acute Hospital Beds],
        REMOVEFILTERS('Year'),
        'Facilities Annual'[year] = 2015
    )
RETURN
    DIVIDE([Public Acute Hospital Beds], Baseline) * 100
```
Same indexing pattern as `[Admissions Index (2015=100)]`, applied to Public Acute Hospital beds, and for the same reason: this measure is plotted with `Year[Year]` as the axis (Chart 2, §2.2), so `REMOVEFILTERS('Year')` clears the Year-table filter before pinning `Facilities Annual[year] = 2015` for the baseline. Expected 2025 value: **132.7**. **Never** combine this with the admissions index into a ratio; they are plotted side by side as two lines, never divided by each other.

### In `Regional Beds Annual`

```dax
Regional Beds =
SUM('Regional Beds Annual'[no_beds])
```
Plain sum of regional hospital beds, respecting whatever `planning_region` / `facility_type` / `year` filters are active (from axis, legend, slicer, or visual-level filters). Expected 2025 value (no filters): **17,296**.

```dax
Regional Bed Share =
DIVIDE(
    SUM('Regional Beds Annual'[no_beds]),
    CALCULATE(
        SUM('Regional Beds Annual'[no_beds]),
        ALL('Regional Beds Annual'[planning_region])
    )
)
```
Share of the current `planning_region` within the total across **all** regions, for whatever year/facility_type context is otherwise active (only the `planning_region` filter is removed for the denominator, via `ALL`). Expected value for `planning_region = "Central Region"`, `year = 2025`, no facility_type filter: **52.5%**. *Caveat:* if a visual also breaks this down by `facility_type` (e.g. as a Legend), the denominator will be the all-regions total **within that facility type**, not the grand total; fine for most uses here, but worth knowing.

---

## Part 4: Build Steps (numbered, in order)

1. **Open Power BI Desktop** in your Windows VM (via Parallels Desktop → launch Windows → open Power BI Desktop from the Start menu or desktop shortcut).
2. **Locate the CSV files**: your Mac's files are normally reachable from Windows File Explorer under a shared drive (commonly labelled with your Mac username, or `Z:\` / `\\Mac\Home` depending on your Parallels sharing settings). Navigate to `Desktop/Data Analyst Portfolio/02_Singapore_Healthcare_Analytics/data/processed/`. If you don't see your Mac files, open Parallels Desktop → **Actions → Configure... → Sharing** and confirm "Share Mac" / "Home folder" is enabled, then retry.
3. **Import the three datasets** following §1.1 above (Get Data → Text/CSV, three times).
4. **Rename the three tables** following §1.2.
5. **Set/verify data types** following §1.3 (Transform Data → check each column's type icon).
6. **Create the Year table** following §1.4 (Enter Data, 11 rows, 2015–2025).
7. **Build the three relationships** following §1.5 (Model view, drag Year[Year] to each fact table's year column, confirm 1:* and Single direction on each).
8. **Create the 20 documented DAX measures** from Part 3 (right-click each table → New measure → paste the formula → Enter). Format each one (number/percentage, decimal places, thousands separator) via the **Measure tools → Formatting** ribbon. Then add the five final-dashboard measures from **Part 3A** (`Service Activity`, `Service YoY %`, `Regional Hospital Beds`, `Regional Beds (Selected Year)`, and the final `Regional Beds Matrix Title`). The Page 1 growth chart uses `Service YoY %`, not Part 3's `YoY % Change`.
9. **Build Page 1** visual by visual, following §2.1: 4 KPI cards, then Chart 1 → Chart 2 → Chart 3 → Chart 4, in that order (so you can check each chart's numbers as you go rather than debugging four charts at once).
10. **Build Page 2** visual by visual, following §2.2: 4 KPI cards, then Chart 1 → Chart 2 → Chart 3 → Chart 4.
11. **Add the Year Range slicer to both pages** following §2.3 (a Between slicer built from `Year[Year]` on each page), and set each KPI card's, and Page 1 Chart 4's, interaction with it to **None** as described.
12. **Format both pages**: consistent font (e.g. Segoe UI, the Power BI default, is fine), a single accent colour for Public-sector series and a second for Non-Public/Private/Not-for-Profit (keep the same two colours on every chart that shows sector), page titles, and axis titles with units (e.g. "Admissions per Year", "Beds", "Index (2015=100)"). Add the baseline label on Page 2 Chart 4 and confirm the 2021-discrepancy footer note from §2.2 is present on Page 2.
13. **Check numerical values** against Part 5 below.
14. **Save the file**: **File → Save As**, save as `Singapore_Healthcare_Analytics.pbix` inside this project's `dashboard/` folder (the published copy already lives at `dashboard/Singapore_Healthcare_Analytics.pbix`; if you are rebuilding separately, save to the same location so the README's dashboard links continue to resolve).
15. **Export screenshots**: **File → Export → Export to PDF** (captures both pages at once), or use **File → Export → Save as image** per visual, or simply use macOS screenshot (Cmd+Shift+4) within the Parallels window for each page. Save screenshots into `dashboard/screenshots/`.

---

## Part 5: Validation Checklist

Work through this after building, before considering the dashboard done:

- [ ] **Row counts after import**: Monthly Utilisation = 1,452 rows; Facilities Annual = 165 rows; Regional Beds Annual = 102 rows (check via Model view → click each table → row count shown, or a temporary Card visual with `COUNTROWS(TableName)`).
- [ ] **Relationships**: exactly 3 relationships exist, all `Year[Year]` → a fact table's `year`, all **One to many**, all **Single** direction. No relationship exists directly between any two fact tables.
- [ ] **Measure outputs match the reference table** in Part 2 (Total Admissions 2025 = 699,606; Public Acute Admissions 2025 = 548,517; Specialist Outpatient Attendances 2025 = 5,728,143; Public Acute Admission Share 2025 = 83.3%; Total Hospital Beds 2025 = 17,296; Public Acute Hospital Beds 2025 = 10,784; Admissions Index 2025 = 144.4; Bed Capacity Index 2025 = 132.7).
- [ ] **No double-counting**: `[Total Admissions]` never includes Outpatient Attendances or Day Surgeries rows; `[Total Hospital Beds]` never includes Residential Long-Term Care rows; Page 1 Chart 1's small-multiple panels sum to the same total as `[Total Admissions]` for any given year; the Page 2 regional matrix shows one year's figures, never a sum across multiple years.
- [ ] **Correct filter interactions**: on both pages, all 4 KPI cards and Page 1 Chart 4 are set to **None** against the Year Range slicer and stay fixed/unaffected no matter how the slicer is set; Page 1 Charts 1-3 and Page 2 Charts 1-2 do respond to the slicer's range; the Page 2 matrix and indexed line chart behave as described in §2.2 (verify in **Format → Edit interactions** with the slicer selected).
- [ ] **No misleading mixed-unit KPIs**: no card or chart divides admissions by beds, and nothing is labelled "occupancy" or "utilisation rate" anywhere on either page.
- [ ] **Correct regional matrix behaviour**: moving the Year Range slicer's end year changes the matrix's title and totals to that single year, never to a sum of multiple years; at the 2025 end of the range the grand total is 17,296, matching `data/processed/hospital_beds_region_annual.csv`; with the slicer ending in 2021 the grand total is 15,665; with a range before 2020 the matrix is empty and the title reads "(No Data)".
- [ ] **Source-discrepancy disclaimer** is visible on Page 2 (the 1,180 vs. 1,112 / 68-bed note).
- [ ] **Dashboard readability**: consistent colour per sector across every chart that uses one, legible axis labels and titles, no overlapping text, KPI cards show units (admissions, beds, %, index points).
- [ ] **Successful `.pbix` save**: file saved, reopens without errors, and recalculates the same figures as this checklist on reopen.

---

## Reference Figures (verified against processed CSVs before use in this guide)

| Metric | 2025 value | Verified against |
|---|---|---|
| Acute Hospital admissions | 658,221 | `healthcare_utilisation_monthly.csv` |
| Community Hospital admissions | 30,231 | `healthcare_utilisation_monthly.csv` |
| Public Acute admissions | 548,517 | `healthcare_utilisation_monthly.csv` |
| Public Acute Hospital beds | 10,784 | `healthcare_facilities_annual.csv` |
| Public Acute admissions index (2015=100) | 144.4 | recomputed from above |
| Public Acute beds index (2015=100) | 132.7 | recomputed from above |
| Regional hospital beds, total | 17,296 | `hospital_beds_region_annual.csv` |
| Central Region share | 52.5% | recomputed from above |

**Known, unresolved source discrepancy** (carried forward from Stage 2-4, unchanged): 2021 Public Community Hospital beds: national dataset = 1,180, regional dataset = 1,112, difference = 68. Both values remain genuine and preserved; this dashboard must not average or silently reconcile them. Display the disclaimer specified in §2.2.

Reminders baked into this design: admissions are 12-month activity counts, beds are point-in-time capacity counts: the indexed comparison chart is a growth-rate comparison, not an occupancy measure; and the regional charts describe facility *location*, not patient residence or demand. No "under-served region" claim is made or should be added.
