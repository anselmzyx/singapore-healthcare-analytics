"""
Stage 2 — Data Cleaning and Preparation
Singapore Healthcare Utilisation & Capacity Analysis (2015-2025)

Reads the three original raw CSVs (unmodified), reshapes and standardises
them, writes three analysis-ready CSVs to data/processed/, and prints a
data-quality / validation summary. Re-runnable without touching data/raw/.
"""

import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (project-relative; script lives in scripts/, project root is parent)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"
PROCESSED.mkdir(parents=True, exist_ok=True)

MONTHLY_RAW = RAW / "d_b1ac3356e23ecad918854bbfa3627952_HospitalAdmissionsOutpatientAttendances_Monthly.csv"
FACILITIES_RAW = RAW / "d_852ebeb1165d0ec4cdc89fa7742959d1_HealthFacilitiesAndInpatientBeds.csv"
REGIONAL_RAW = RAW / "d_0ed27481bde3ad8abac12be380a441bb_HospitalBedsByFacilityTypeAndPlanningRegion_Annual.csv"

MONTHLY_START, MONTHLY_END = "2015-01-01", "2025-12-01"
ANNUAL_START, ANNUAL_END = 2015, 2025
REGIONAL_START, REGIONAL_END = 2020, 2025

# Canonical sector / facility-type labels used across both bed datasets,
# so Dataset 2 and Dataset 3 can be compared on identical category names.
SECTOR_RENAME = {"Not-For-Profit": "Not-for-Profit"}          # Dataset 3 casing -> Dataset 2 casing
FACILITY_RENAME_DS2 = {"Acute": "Acute Hospitals"}             # Dataset 2's own inconsistent label fixed

report_lines = []  # collected for the printed data-quality summary


def log(msg):
    print(msg)
    report_lines.append(msg)


# ===========================================================================
# TASK 2 — Monthly healthcare utilisation
# ===========================================================================
def clean_monthly():
    log("\n=== TASK 2: Monthly healthcare utilisation ===")

    # Read everything as string, with pandas' automatic NA detection switched
    # off, so leading spaces in DataSeries (used for row hierarchy) and the
    # literal 'na' placeholder are preserved exactly as published.
    raw = pd.read_csv(MONTHLY_RAW, dtype=str, keep_default_na=False)
    month_cols = [c for c in raw.columns if c != "DataSeries"]
    log(f"Raw shape: {raw.shape[0]} rows x {raw.shape[1]} columns "
        f"(source columns run Dec-2005->Jan-1987 then Jul-2026->Jan-2006).")

    # --- Classify each row into category / sector using indentation -------
    # Level-0 (no leading spaces) rows are either an admissions category with
    # Public/Non-Public children, or a self-contained service with no split.
    ADMISSIONS_CATEGORIES = {
        "Acute Hospitals Admissions",
        "Psychiatric Hospitals Admissions",
        "Community Hospitals Admissions",
    }
    MEASURE_TYPE = {
        "Acute Hospitals Admissions": "Hospital Admissions",
        "Psychiatric Hospitals Admissions": "Hospital Admissions",
        "Community Hospitals Admissions": "Hospital Admissions",
        "Specialist Outpatient Clinics": "Outpatient Attendances",
        "Accident & Emergency Departments": "Outpatient Attendances",
        "Polyclinics": "Outpatient Attendances",
        "Dental Clinics": "Outpatient Attendances",
        "Day Surgeries": "Day Surgeries",
    }
    # Strip the "Admissions" suffix so hospital category names match the
    # facility_type naming used in Datasets 2 and 3 (Acute/Psychiatric/Community Hospitals).
    SERVICE_CATEGORY_RENAME = {
        "Acute Hospitals Admissions": "Acute Hospitals",
        "Psychiatric Hospitals Admissions": "Psychiatric Hospitals",
        "Community Hospitals Admissions": "Community Hospitals",
    }

    rows = []
    parent_label = None
    for raw_label in raw["DataSeries"]:
        indent = len(raw_label) - len(raw_label.lstrip(" "))
        label = raw_label.strip()
        if indent == 0:
            parent_label = label
            sector = "Total" if label in ADMISSIONS_CATEGORIES else "All"
        else:
            sector = label  # 'Public' or 'Non-Public'
        rows.append({
            "raw_label": raw_label,
            "service_category": SERVICE_CATEGORY_RENAME.get(parent_label, parent_label),
            "measure_type": MEASURE_TYPE[parent_label],
            "sector": sector,
        })
    meta = pd.DataFrame(rows)
    wide = pd.concat([meta, raw[month_cols].reset_index(drop=True)], axis=1)

    # --- Reshape wide -> long ----------------------------------------------
    long = wide.melt(
        id_vars=["raw_label", "service_category", "measure_type", "sector"],
        value_vars=month_cols,
        var_name="period_raw",
        value_name="value_raw",
    )

    # Parse 'YYYYMon' headers (e.g. '2005Dec', '2026Jul') into real dates.
    long["date"] = pd.to_datetime(long["period_raw"], format="%Y%b")

    # Convert the literal 'na' placeholder to a genuine missing value BEFORE
    # the date filter, as instructed, then cast counts to a nullable integer.
    long["value_raw"] = long["value_raw"].replace("na", pd.NA)
    long["count"] = pd.to_numeric(long["value_raw"], errors="raise").astype("Int64")

    # --- Reconciliation check: Total vs Public + Non-Public ----------------
    # Run on the full available history (pre-filter) so the check is not
    # limited to the final 2015-2025 window. Pivot so Total/Public/Non-Public
    # sit side by side per category-month - this lets us see genuine missing
    # values directly, instead of a groupby().sum() that would silently turn
    # an all-missing group of children into 0 and falsely "match" a missing
    # parent total.
    # dropna=False: keep category-months where every sector is historically
    # unavailable, instead of silently discarding those rows from the pivot.
    pivot = long[long["sector"].isin(["Total", "Public", "Non-Public"])].pivot_table(
        index=["service_category", "date"], columns="sector", values="count",
        aggfunc="first", dropna=False,
    )
    total_reported = pivot["Total"].notna()
    children_reported = pivot[["Public", "Non-Public"]].notna().all(axis=1)
    is_valid = total_reported & children_reported          # both parent and children genuinely reported
    is_unavailable = ~is_valid                              # parent and/or a child is historically missing

    child_sum = pivot.loc[is_valid, ["Public", "Non-Public"]].sum(axis=1)
    diff = pivot.loc[is_valid, "Total"] - child_sum
    mismatches = diff[diff != 0]

    n_valid, n_unavailable, n_mismatch = is_valid.sum(), is_unavailable.sum(), len(mismatches)
    log(f"Reconciliation: {n_valid} category-months with genuinely reported parent and child data, "
        f"{n_unavailable} category-months unavailable in the source (not counted as a comparison), "
        f"{n_mismatch} genuine mismatches among the valid comparisons.")
    if n_mismatch:
        log(f"RECONCILIATION MISMATCH in {n_mismatch} category-months (see details below):")
        log(mismatches.to_string())

    # --- Filter to the analysis window and drop parent Total rows ---------
    long = long[(long["date"] >= MONTHLY_START) & (long["date"] <= MONTHLY_END)]
    final = long[long["sector"] != "Total"].copy()  # parent totals used only for reconciliation above

    final["year"] = final["date"].dt.year
    final["month"] = final["date"].dt.month
    final = final[["date", "year", "month", "measure_type", "service_category", "sector", "count"]]
    final = final.sort_values(["date", "measure_type", "service_category", "sector"]).reset_index(drop=True)
    final["count"] = final["count"].astype("int64")  # no missing values remain inside 2015-2025

    missing_in_window = final["count"].isna().sum()
    log(f"Final monthly table: {final.shape[0]} rows, {final['date'].min().date()} "
        f"to {final['date'].max().date()}. Missing values in window: {missing_in_window}.")

    out = PROCESSED / "healthcare_utilisation_monthly.csv"
    final.to_csv(out, index=False)
    log(f"Wrote {out.relative_to(ROOT)}")
    return final


# ===========================================================================
# TASK 3 — Healthcare facilities and beds (national, annual)
# ===========================================================================
def clean_facilities():
    log("\n=== TASK 3: Healthcare facilities and beds (national) ===")

    raw = pd.read_csv(FACILITIES_RAW)
    log(f"Raw shape: {raw.shape[0]} rows x {raw.shape[1]} columns, "
        f"years {raw['year'].min()}-{raw['year'].max()}.")

    df = raw.rename(columns={"facility_type_a": "facility_type", "public_private": "sector"})
    df["facility_type"] = df["facility_type"].replace(FACILITY_RENAME_DS2)  # 'Acute' -> 'Acute Hospitals'
    df["sector"] = df["sector"].replace(SECTOR_RENAME)

    df = df[(df["year"] >= ANNUAL_START) & (df["year"] <= ANNUAL_END)].copy()
    df["year"] = df["year"].astype("int64")
    df["no_of_facilities"] = df["no_of_facilities"].astype("int64")
    df["no_beds"] = df["no_beds"].astype("int64")

    # --- Quality checks ------------------------------------------------
    missing = df.isna().sum().sum()
    key_cols = ["year", "institution_type", "facility_type", "sector"]
    dupes = df.duplicated(subset=key_cols).sum()
    negatives = ((df["no_of_facilities"] < 0) | (df["no_beds"] < 0)).sum()
    log(f"Missing values: {missing}. Duplicate business keys ({key_cols}): {dupes}. "
        f"Negative counts: {negatives}.")

    zero_fac_positive_beds = df[(df["no_of_facilities"] == 0) & (df["no_beds"] > 0)]
    if not zero_fac_positive_beds.empty:
        log(f"NOTE: {len(zero_fac_positive_beds)} rows have no_of_facilities == 0 with "
            f"no_beds > 0 (Public Inpatient Hospices, 2015-2019) - retained as reported, "
            f"not altered. See STAGE2_CLEANING_NOTES.md.")
        log(zero_fac_positive_beds[key_cols + ["no_of_facilities", "no_beds"]].to_string(index=False))

    df = df.sort_values(["year", "institution_type", "facility_type", "sector"]).reset_index(drop=True)
    out = PROCESSED / "healthcare_facilities_annual.csv"
    df.to_csv(out, index=False)
    log(f"Final facilities table: {df.shape[0]} rows. Wrote {out.relative_to(ROOT)}")
    return df


# ===========================================================================
# TASK 4 — Regional hospital bed capacity (annual)
# ===========================================================================
def clean_regional():
    log("\n=== TASK 4: Regional hospital bed capacity ===")

    raw = pd.read_csv(REGIONAL_RAW, dtype=str, keep_default_na=False)
    year_cols = [c for c in raw.columns if c != "DataSeries"]
    log(f"Raw shape: {raw.shape[0]} rows x {raw.shape[1]} columns, years {year_cols}.")

    # --- Parse the 3-level indentation hierarchy: facility type / sector / region
    rows = []
    facility_type, sector = None, None
    for raw_label in raw["DataSeries"]:
        indent = len(raw_label) - len(raw_label.lstrip(" "))
        label = raw_label.strip()
        level = indent // 4  # 0 = facility type, 1 = sector, 2 = planning region
        if level == 0:
            facility_type, sector = label, None
        elif level == 1:
            sector = label
        rows.append({"facility_type": facility_type, "sector": sector, "level": level, "label": label})
    meta = pd.DataFrame(rows)
    meta["sector"] = meta["sector"].replace(SECTOR_RENAME)
    wide = pd.concat([meta, raw[year_cols].reset_index(drop=True)], axis=1)
    for c in year_cols:
        wide[c] = wide[c].astype("int64")

    long = wide.melt(
        id_vars=["facility_type", "sector", "level", "label"],
        value_vars=year_cols, var_name="year", value_name="no_beds",
    )
    long["year"] = long["year"].astype("int64")
    long = long[(long["year"] >= REGIONAL_START) & (long["year"] <= REGIONAL_END)]

    # --- Reconciliation: leaf (region) rows must sum to their sector total,
    #     and sector rows must sum to their facility-type total.
    region_rows = long[long["level"] == 2].rename(columns={"label": "planning_region"})
    region_rows["planning_region"] = region_rows["planning_region"].str.strip()

    sector_rows = long[long["level"] == 1]
    sector_check = (
        region_rows.groupby(["facility_type", "sector", "year"])["no_beds"].sum()
        .rename("region_sum")
        .to_frame()
        .join(sector_rows.set_index(["facility_type", "sector", "year"])["no_beds"].rename("sector_total"))
    )
    sector_check["diff"] = sector_check["sector_total"] - sector_check["region_sum"]
    sector_mismatch = sector_check[sector_check["diff"] != 0]
    if sector_mismatch.empty:
        log(f"Region-to-sector reconciliation OK across all {len(sector_check)} facility/sector/year combos.")
    else:
        log(f"REGION-TO-SECTOR MISMATCH in {len(sector_mismatch)} combos:")
        log(sector_mismatch.to_string())

    facility_rows = long[long["level"] == 0]
    facility_check = (
        sector_rows.groupby(["facility_type", "year"])["no_beds"].sum()
        .rename("sector_sum")
        .to_frame()
        .join(facility_rows.set_index(["facility_type", "year"])["no_beds"].rename("facility_total"))
    )
    facility_check["diff"] = facility_check["facility_total"] - facility_check["sector_sum"]
    facility_mismatch = facility_check[facility_check["diff"] != 0]
    if facility_mismatch.empty:
        log(f"Sector-to-facility-type reconciliation OK across all {len(facility_check)} facility/year combos.")
    else:
        log(f"SECTOR-TO-FACILITY MISMATCH in {len(facility_mismatch)} combos:")
        log(facility_check.to_string())

    # --- Final table: leaf (region) rows only, to avoid double counting ---
    final = region_rows[["year", "facility_type", "sector", "planning_region", "no_beds"]].copy()
    final["year"] = final["year"].astype("int64")
    final["no_beds"] = final["no_beds"].astype("int64")
    final = final.sort_values(["year", "facility_type", "sector", "planning_region"]).reset_index(drop=True)

    out = PROCESSED / "hospital_beds_region_annual.csv"
    final.to_csv(out, index=False)
    log(f"Final regional table: {final.shape[0]} rows, years {REGIONAL_START}-{REGIONAL_END}. "
        f"Wrote {out.relative_to(ROOT)}")
    return final


# ===========================================================================
# TASK 5 — Cross-dataset validation
# ===========================================================================
def cross_validate(monthly, facilities, regional):
    log("\n=== TASK 5: Cross-dataset validation ===")

    # Basic shape / key checks -------------------------------------------
    log(f"Monthly: years {sorted(monthly['year'].unique())[0]}-{sorted(monthly['year'].unique())[-1]}, "
        f"service_categories={sorted(monthly['service_category'].unique())}, "
        f"sectors={sorted(monthly['sector'].unique())}.")
    log(f"Facilities: years {sorted(facilities['year'].unique())[0]}-{sorted(facilities['year'].unique())[-1]}, "
        f"facility_types={sorted(facilities['facility_type'].unique())}, "
        f"sectors={sorted(facilities['sector'].unique())}.")
    log(f"Regional: years {sorted(regional['year'].unique())[0]}-{sorted(regional['year'].unique())[-1]}, "
        f"facility_types={sorted(regional['facility_type'].unique())}, "
        f"planning_regions={sorted(regional['planning_region'].unique())}.")

    for name, df, num_cols in [
        ("monthly", monthly, ["count"]),
        ("facilities", facilities, ["no_of_facilities", "no_beds"]),
        ("regional", regional, ["no_beds"]),
    ]:
        neg = (df[num_cols] < 0).sum().sum()
        miss = df[num_cols].isna().sum().sum()
        log(f"{name}: negative values={neg}, missing values={miss}.")

    key_cols = {
        "monthly": ["date", "measure_type", "service_category", "sector"],
        "facilities": ["year", "institution_type", "facility_type", "sector"],
        "regional": ["year", "facility_type", "sector", "planning_region"],
    }
    for name, df in [("monthly", monthly), ("facilities", facilities), ("regional", regional)]:
        dupes = df.duplicated(subset=key_cols[name]).sum()
        log(f"{name}: duplicate business keys on {key_cols[name]} = {dupes}.")

    # Regional aggregate (Hospital, 2020-2025) vs national facilities table ---
    regional_national_equiv = (
        regional.groupby(["year", "facility_type", "sector"])["no_beds"]
        .sum().rename("regional_sum").reset_index()
    )
    national_hospital = facilities[
        (facilities["institution_type"] == "Hospital") &
        (facilities["year"] >= REGIONAL_START) & (facilities["year"] <= REGIONAL_END)
    ][["year", "facility_type", "sector", "no_beds"]].rename(columns={"no_beds": "national_value"})

    compare = regional_national_equiv.merge(
        national_hospital, on=["year", "facility_type", "sector"], how="outer", indicator=True
    )
    log(f"\nRegional-vs-national comparison: {len(compare)} year/facility_type/sector combos checked.")

    # The regional source omits rows entirely for sector combos with zero beds
    # (rather than listing them as 0), so a missing regional row with a
    # national value of 0 is a representation difference, not a discrepancy.
    omitted_zero_rows = compare[(compare["_merge"] == "right_only") & (compare["national_value"] == 0)]
    if not omitted_zero_rows.empty:
        log(f"{len(omitted_zero_rows)} combos exist only in the national facilities dataset, all with "
            f"national_value == 0 beds (regional source simply omits zero-bed rows rather than listing "
            f"them as 0). Not treated as a discrepancy.")

    # Genuine numeric mismatches: combo present in both, with different values.
    both = compare[compare["_merge"] == "both"].copy()
    both["diff"] = both["national_value"] - both["regional_sum"]
    numeric_mismatches = both[both["diff"] != 0]
    # Any combo present in only one source with a non-zero value on the other side.
    other_mismatches = compare[
        (compare["_merge"] != "both") & (compare[["regional_sum", "national_value"]].fillna(0).sum(axis=1) != 0)
    ]
    all_mismatches = pd.concat([numeric_mismatches, other_mismatches])

    if all_mismatches.empty:
        log("No genuine numeric mismatches - regional and national bed figures reconcile exactly "
            "for every combo where both sources report a value.")
    else:
        log(f"{len(all_mismatches)} GENUINE MISMATCH(ES) found between regional sum and national "
            f"facilities figure (reported as-is; source data NOT altered to force equality):")
        log(all_mismatches.to_string(index=False))

    # Explicit check for the known 2021 Public Community Hospitals discrepancy
    nat_val = national_hospital[
        (national_hospital["year"] == 2021) & (national_hospital["facility_type"] == "Community Hospitals") &
        (national_hospital["sector"] == "Public")
    ]["national_value"]
    reg_val = regional_national_equiv[
        (regional_national_equiv["year"] == 2021) & (regional_national_equiv["facility_type"] == "Community Hospitals") &
        (regional_national_equiv["sector"] == "Public")
    ]["regional_sum"]
    nat_val = int(nat_val.iloc[0]) if len(nat_val) else None
    reg_val = int(reg_val.iloc[0]) if len(reg_val) else None
    log(f"\n2021 Public Community Hospitals beds — national facilities dataset: {nat_val}, "
        f"sum of regional dataset: {reg_val}, difference: "
        f"{(nat_val - reg_val) if nat_val is not None and reg_val is not None else 'n/a'}. "
        f"Both original values preserved unmodified in their respective processed files; "
        f"no correction applied (see STAGE2_CLEANING_NOTES.md).")


# ===========================================================================
if __name__ == "__main__":
    monthly = clean_monthly()
    facilities = clean_facilities()
    regional = clean_regional()
    cross_validate(monthly, facilities, regional)

    log("\n=== SUMMARY ===")
    log(f"healthcare_utilisation_monthly.csv : {monthly.shape[0]} rows")
    log(f"healthcare_facilities_annual.csv   : {facilities.shape[0]} rows")
    log(f"hospital_beds_region_annual.csv    : {regional.shape[0]} rows")
    log("Stage 2 cleaning complete. Raw files in data/raw/ were not modified.")
