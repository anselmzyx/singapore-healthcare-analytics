"""
Stage 4 — SQL Analysis Runner
Singapore Healthcare Utilisation & Capacity Analysis (2015-2025)

Loads the three Stage 2 processed CSVs into an in-memory DuckDB database
(no persistent .duckdb file is created), executes every .sql file in sql/,
and writes each result to results/sql/<same name>.csv. Re-runnable without
touching data/raw/ or data/processed/.
"""

import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parent.parent
PROCESSED = ROOT / "data" / "processed"
SQL_DIR = ROOT / "sql"
RESULTS_DIR = ROOT / "results" / "sql"
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

TABLES = {
    "monthly": PROCESSED / "healthcare_utilisation_monthly.csv",
    "facilities": PROCESSED / "healthcare_facilities_annual.csv",
    "regional": PROCESSED / "hospital_beds_region_annual.csv",
}


def main():
    start = time.time()
    con = duckdb.connect(database=":memory:")  # in-memory only - no .duckdb file written

    for name, path in TABLES.items():
        # DuckDB DDL statements can't take prepared parameters; paths are fixed,
        # local, project-relative, so direct formatting is safe here.
        con.execute(f"CREATE VIEW {name} AS SELECT * FROM read_csv_auto('{path.as_posix()}')")

    print("=== Stage 4 SQL Analysis Runner (DuckDB, in-memory) ===")
    for name, path in TABLES.items():
        n = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        print(f"Loaded view '{name}' from {path.relative_to(ROOT)} ({n} rows)")

    sql_files = sorted(SQL_DIR.glob("*.sql"))
    print(f"\nFound {len(sql_files)} SQL files in {SQL_DIR.relative_to(ROOT)}/\n")

    summary = []
    for sql_file in sql_files:
        query = sql_file.read_text()
        t0 = time.time()
        df = con.execute(query).fetchdf()
        elapsed = time.time() - t0

        out_path = RESULTS_DIR / f"{sql_file.stem}.csv"
        df.to_csv(out_path, index=False)

        print(f"{sql_file.name:40s} -> {out_path.relative_to(ROOT)}  "
              f"({df.shape[0]} rows x {df.shape[1]} cols, {elapsed*1000:.0f} ms)")
        summary.append((sql_file.name, df.shape[0], df.shape[1], elapsed))

    con.close()

    total = time.time() - start
    print("\n=== Summary ===")
    for name, rows, cols, elapsed in summary:
        print(f"  {name}: {rows} rows, {cols} cols, {elapsed*1000:.0f} ms")
    print(f"Total files executed: {len(summary)}")
    print(f"Total runtime: {total:.2f} seconds")
    print("Raw and processed data were only read, never modified.")


if __name__ == "__main__":
    main()
