# Power BI Build Guide: Singapore Healthcare Analytics (Stage 5A)

This guide documents how the Power BI dashboard was built manually in Power BI Desktop (via Parallels on a Mac), and serves as the reference for rebuilding or auditing it. The finished `.pbix` file is published at `dashboard/Singapore_Healthcare_Analytics.pbix`; everything below (data model, DAX, page layouts) reflects what was actually built, and remains copy-paste-ready for reproducing it from scratch.

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

### 1.6 Why the Year table matters for one specific chart

Most charts in this dashboard use a single fact table's own `year` column directly (simpler, and that's fine). The **one place the Year table is actually required** is Page 2's "Admissions vs. Bed Capacity" chart, which plots a measure from **Monthly Utilisation** and a measure from **Facilities Annual** on the *same* axis. Power BI needs a common field both measures can be filtered by: that's `Year[Year]`. Use `Year[Year]` as the axis for that one chart (details in Part 2).

---

## Part 2: Dashboard Design

Two report pages. Rename them (double-click the page tab at the bottom):
- Page 1 → **Healthcare Service Demand**
- Page 2 → **Hospital Capacity & Regional Distribution**

### Guardrail used throughout this design

Every 2025 KPI card uses a **fixed-year measure** (a DAX measure that locks `year = 2025` inside `CALCULATE`, with `REMOVEFILTERS('Year')` first clearing any filter that might otherwise arrive from the Year dimension table). This means a KPI card can never accidentally collapse or distort itself if a Year-table slicer is added later; it always shows 2025, by construction, not by relying on "no slicer happens to be touching it." Trend-line charts, separately, always use the full 2015–2025 (or 2020–2025) range, both because no page-wide Year-table slicer is used (see §2.3) and, where relevant (Chart 2, §2.2), because the index measures themselves also use `REMOVEFILTERS('Year')` to re-fetch their 2015 baseline unconditionally.

---

### 2.1 PAGE 1: Healthcare Service Demand

**KPI cards (top row, 4 cards, each visual type = Card)**

| Card title | Measure | Expected 2025 value |
|---|---|---|
| Total Hospital Admissions (2025) | `[Total Admissions 2025]` | 699,606 |
| Public Acute Admissions (2025) | `[Public Acute Admissions 2025]` | 548,517 |
| Specialist Outpatient Attendances (2025) | `[Specialist Outpatient Attendances 2025]` | 5,728,143 |
| Public Admission Share, Acute (2025) | `[Public Admission Share 2025]` (filtered `service_category = "Acute Hospitals"`) | 83.3% |

Format: Card visual, format "Total Hospital Admissions (2025)" etc. as the card title, use thousands-separator number formatting (and % formatting for the share card). No filters needed beyond what's built into the measures themselves.

**Chart 1: "Hospital Admissions Trend by Type, 2015–2025"**
- Visual type: **Line chart**
- X-axis: `Monthly Utilisation[year]`
- Legend: `Monthly Utilisation[service_category]`
- Values: `[Total Admissions]`
- Filters: visual-level filter `measure_type = "Hospital Admissions"` (belt-and-braces; the measure already restricts this)
- Interactions: none special
- Purpose: shows Acute/Community/Psychiatric admissions trends on one chart; it answers "how have admissions changed 2015–2025" and "which grew fastest."
- Expected result: Acute line dominates (~500k→658k), Community line grows the fastest proportionally (10.7k→30.2k), Psychiatric stays flat/low (~9k–11k).

**Chart 2: "Outpatient Attendance Trends, 2015–2025"**
- Visual type: **Line chart** (or small multiples if your Power BI Desktop version has that feature: Small multiples = `service_category`)
- X-axis: `Monthly Utilisation[year]`
- Legend: `Monthly Utilisation[service_category]`
- Values: `[Outpatient Attendances]`
- Filters: visual-level filter `measure_type = "Outpatient Attendances"`
- Purpose: shows Specialist Outpatient Clinics, A&E, Polyclinics and Dental Clinics on different scales; use small multiples if available, since Polyclinics (~7.4M) dwarfs Dental Clinics (~1.0M).
- Expected result: visible 2020 dip across all four, sharpest for Dental Clinics.

**Chart 3: "Public vs Non-Public Admission Share, Acute & Community Hospitals"**
- Visual type: **Line chart**
- X-axis: `Monthly Utilisation[year]`
- Legend: `Monthly Utilisation[service_category]`
- Values: `[Public Admission Share]`
- Filters: visual-level filter `service_category` IN `{Acute Hospitals, Community Hospitals}`
- Purpose: directly shows the very different sector-mix shift between the two hospital types.
- Expected result: Acute line rises gently (76.0%→83.3%); Community line rises steeply (20.5%→66.5%). **Note in the visual's subtitle/tooltip**: this describes admission activity, not bed ownership.

**Chart 4: "Year-over-Year Growth, Key Services"**
- Visual type: **Clustered column chart**
- X-axis: `Monthly Utilisation[year]`
- Legend: `Monthly Utilisation[service_category]`
- Values: `[YoY % Change]`
- Filters: visual-level filter `service_category` IN `{Acute Hospitals, Specialist Outpatient Clinics, Polyclinics, Dental Clinics, Day Surgeries}`
- Purpose: recreates Stage 3's Figure 3 as an interactive visual, highlighting the 2020 contraction / 2021 rebound pattern for these five services specifically (not all services; see `STAGE3_EDA_FINDINGS.md`).
- Expected result: every series dips in 2020 (Dental Clinics steepest, ≈-34%), most rebound in 2021.

No Year slicer on this page; every chart is meant to always show the full 2015–2025 trend.

---

### 2.2 PAGE 2: Hospital Capacity & Regional Distribution

**KPI cards (top row, 4 cards)**

| Card title | Measure | Expected 2025 value |
|---|---|---|
| Total Hospital Beds (2025) | `[Total Hospital Beds 2025]` | 17,296 |
| Public Acute Hospital Beds (2025) | `[Public Acute Hospital Beds 2025]` | 10,784 |
| Public Acute Admissions Index (2025, 2015=100) | `[Admissions Index (2015=100)]` filtered `year = 2025` | 144.4 |
| Public Acute Beds Index (2025, 2015=100) | `[Bed Capacity Index (2015=100)]` filtered `year = 2025` | 132.7 |

(Optional 5th card if you have room: "Central Region Bed Share (2025)" = `[Regional Bed Share]` filtered `planning_region = "Central Region"`, `year = 2025` → 52.5%.)

**Chart 1: "Hospital Bed Capacity by Facility Type and Sector, 2015–2025"**
- Visual type: **Stacked column chart**, with **Small multiples = `facility_type`** if available (otherwise build two side-by-side charts, one filtered to Acute Hospitals, one to Community Hospitals; Psychiatric is flat/Public-only and optional)
- X-axis: `Facilities Annual[year]`
- Legend: `Facilities Annual[sector]`
- Values: `[Total Hospital Beds]`
- Filters: visual-level filter `institution_type = "Hospital"` (already in the measure, but keep for clarity); if not using small multiples, add `facility_type = "Acute Hospitals"` (and a second chart for Community Hospitals)
- Purpose: shows how bed capacity composition by ownership sector changed, excluding Residential Long-Term Care throughout.
- Expected result: Public beds dominate and grew the most for both Acute and Community Hospitals.

**Chart 2: "Public Acute Hospitals: Admissions vs. Bed Capacity (Indexed, 2015=100)"**
- Visual type: **Line chart**
- X-axis: **`Year[Year]`** (from the Year dimension table, required here; see §1.6)
- Values: `[Admissions Index (2015=100)]` and `[Bed Capacity Index (2015=100)]` (two line series)
- Filters: none
- Purpose: compares growth *rates* of Public Acute admissions vs. Public Acute beds on one indexed scale.
- Expected result: both start at 100 (2015), admissions line pulls ahead, reaching 144.4 vs. 132.7 by 2025.
- **Label the baseline clearly**: add a text box or chart subtitle reading "Baseline: 2015 = 100". **Do not** label this chart "occupancy" or "utilisation rate" anywhere; it is a growth-rate comparison only.

**Chart 3: "Hospital Beds by Planning Region and Facility Type"**
- Visual type: **Matrix** with **Conditional formatting → Background color** applied to the values (this gives a heatmap effect using only built-in Power BI features)
- Rows: `Regional Beds Annual[planning_region]`
- Columns: `Regional Beds Annual[facility_type]`
- Values: `[Regional Beds]`
- Filters: default year = 2025 (via a visual-level filter as the starting state); from then on, controlled by the Page 2 Year slicer, with **slicer interaction = Filter** (see §2.3)
- Purpose: shows where capacity is concentrated by region and facility type.
- Expected result (2025): Central Region / Acute Hospitals is the largest single cell (8,326); Psychiatric Hospitals is blank everywhere except North-East Region (1,950).

**Chart 4: "Regional Bed Growth, 2020 vs. 2025"**
- Visual type: **Clustered column chart**
- X-axis: `Regional Beds Annual[planning_region]`
- Legend: `Regional Beds Annual[year]`
- Values: `[Regional Beds]`
- Filters: visual-level filter `year` IN `{2020, 2025}`, with **slicer interaction = None**, so this chart always shows exactly the 2020-vs-2025 comparison regardless of what single year the Page 2 Year slicer is set to (if the slicer were allowed to filter this chart, selecting e.g. 2023 would leave it empty, since 2023 is outside the `{2020, 2025}` visual filter)
- Purpose: shows absolute regional growth side by side.
- Expected result: Central Region tallest in both years; every region grows from 2020 to 2025.
- **Add a source note text box near this chart and Chart 3**: *"2021 Public Community Hospital beds: national dataset reports 1,180; regional dataset reports 1,112 (difference: 68). Both values are genuine and unreconciled; see STAGE2_CLEANING_NOTES.md."* This note is relevant here because any 2021-inclusive regional total for Community Hospitals is affected by the discrepancy (2020 and 2025 themselves are unaffected, but readers comparing across all regional-dataset years should see this caveat).

### 2.3 Slicer and interaction configuration (Page 2 only)

Add **one slicer** to Page 2: a **Year slicer** built from **`Regional Beds Annual[year]`** (not from the Year dimension table): a List or Dropdown slicer, default showing 2025 selected (or all of 2020–2025 available to pick from).

**Why this exact field matters:** `Regional Beds Annual` has no relationship to `Monthly Utilisation` or `Facilities Annual`; only the Year dimension table connects to all three. By building the slicer directly from `Regional Beds Annual[year]` instead of from `Year[Year]`, the slicer can only ever filter visuals built from `Regional Beds Annual`. It has **no path** to reach any Monthly Utilisation- or Facilities Annual-based visual, so it is structurally impossible for this slicer to collapse the Chart 2 index trend down to one year. This is the specific guardrail requested in Task 3/4: a Year slicer must never accidentally turn a historical trend into a single-year chart.

Even though the table choice already protects Chart 1 and Chart 2, **explicitly set every visual's interaction with this slicer** (select the slicer → **Format → Edit interactions**) rather than relying on the table choice alone: Chart 4 in particular both *is* built from `Regional Beds Annual` and would otherwise be reachable by the slicer, so its interaction must be turned off deliberately:

| Visual | Interaction with the Page 2 Year slicer |
|---|---|
| All KPI cards (both pages) | **None** (already immune by construction; each uses a fixed-2025 measure with `REMOVEFILTERS('Year')`) |
| Chart 1: Hospital Bed Capacity by Facility Type and Sector | **None** (always shows the full 2015–2025 trend) |
| Chart 2: Admissions vs. Bed Capacity (Indexed) | **None** (always shows the full 2015–2025 trend; also structurally unreachable, since it's built from `Monthly Utilisation`/`Facilities Annual` via `Year[Year]`, not `Regional Beds Annual[year]`) |
| Chart 3: Hospital Beds by Planning Region and Facility Type | **Filter** (this is the one visual meant to respond to the slicer, letting you explore any single year 2020–2025) |
| Chart 4: Regional Bed Growth, 2020 vs. 2025 | **None** (this chart's own visual-level filter already fixes it to exactly 2020 and 2025; letting the slicer also filter it could leave it empty if a different single year were selected) |

To set each one: click the slicer once to select it, open **Format → Edit interactions**, then click the "no interaction" (circle-slash) icon on every visual except Chart 3, where you click the filter-funnel icon instead.

No slicer is used on Page 1 (see §2.1).

---

## Part 3: DAX Measures

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
Year-over-year percentage change for whatever `service_category` is in context (via chart Legend). Uses `MAX(year)` so it correctly reads "the year of this chart row" rather than being confused by a wider filter range. Expected value for `service_category = "Dental Clinics"`, year = 2020: **≈-34.4%**.

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
8. **Create all 20 DAX measures** from Part 3 (right-click each table → New measure → paste the formula → Enter). Format each one (number/percentage, decimal places, thousands separator) via the **Measure tools → Formatting** ribbon.
9. **Build Page 1** visual by visual, following §2.1: 4 KPI cards, then Chart 1 → Chart 2 → Chart 3 → Chart 4, in that order (so you can check each chart's numbers as you go rather than debugging four charts at once).
10. **Build Page 2** visual by visual, following §2.2: 4 (or 5) KPI cards, then Chart 1 → Chart 2 → Chart 3 → Chart 4.
11. **Add the Page 2 slicer** following §2.3 (built from `Regional Beds Annual[year]`, not from `Year[Year]`), and verify its Edit Interactions as described.
12. **Format both pages**: consistent font (e.g. Segoe UI, the Power BI default, is fine), a single accent colour for Public-sector series and a second for Non-Public/Private/Not-for-Profit (keep the same two colours on every chart that shows sector), page titles, and axis titles with units (e.g. "Admissions per Year", "Beds", "Index (2015=100)"). Add the two source-note text boxes specified in §2.2 (Chart 2's baseline label, Chart 3/4's 2021 discrepancy note).
13. **Check numerical values** against Part 5 below.
14. **Save the file**: **File → Save As**, save as `Singapore_Healthcare_Dashboard.pbix` inside the project's `data/` sibling folder of your choice (recommended: a new top-level `powerbi/` folder in the project, e.g. `02_Singapore_Healthcare_Analytics/powerbi/Singapore_Healthcare_Dashboard.pbix`; create that folder first if it doesn't exist).
15. **Export screenshots**: **File → Export → Export to PDF** (captures both pages at once), or use **File → Export → Save as image** per visual, or simply use macOS screenshot (Cmd+Shift+4) within the Parallels window for each page. Save screenshots alongside the `.pbix` file.

---

## Part 5: Validation Checklist

Work through this after building, before considering the dashboard done:

- [ ] **Row counts after import**: Monthly Utilisation = 1,452 rows; Facilities Annual = 165 rows; Regional Beds Annual = 102 rows (check via Model view → click each table → row count shown, or a temporary Card visual with `COUNTROWS(TableName)`).
- [ ] **Relationships**: exactly 3 relationships exist, all `Year[Year]` → a fact table's `year`, all **One to many**, all **Single** direction. No relationship exists directly between any two fact tables.
- [ ] **Measure outputs match the reference table** in Part 2 (Total Admissions 2025 = 699,606; Public Acute Admissions 2025 = 548,517; Specialist Outpatient Attendances 2025 = 5,728,143; Total Hospital Beds 2025 = 17,296; Public Acute Hospital Beds 2025 = 10,784; Admissions Index 2025 = 144.4; Beds Index 2025 = 132.7; Central Region Bed Share 2025 ≈ 52.5%).
- [ ] **No double-counting**: `[Total Admissions]` never includes Outpatient Attendances or Day Surgeries rows; `[Total Hospital Beds]` never includes Residential Long-Term Care rows; Chart 1 (Page 1) legend categories sum to the same total as `[Total Admissions]` for any given year.
- [ ] **Correct filter interactions**: the Page 2 Year slicer changes Chart 3 only (set to **Filter**); Chart 1, Chart 2, Chart 4, and all KPI cards on both pages are set to **None** and stay fixed/full-range no matter how the slicer is set (verify in **Format → Edit interactions** with the slicer selected).
- [ ] **No misleading mixed-unit KPIs**: no card or chart divides admissions by beds, and nothing is labelled "occupancy" or "utilisation rate" anywhere on either page.
- [ ] **Correct region comparisons**: Chart 4 (Page 2) regional totals for 2020 and 2025 match `results/sql/05_regional_bed_growth.csv`'s `beds_2020`/`beds_2025` columns.
- [ ] **Source-discrepancy disclaimer** is visible on Page 2 near the regional charts (the 1,180 vs. 1,112 / 68-bed note).
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
