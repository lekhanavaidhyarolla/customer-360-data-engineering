
"""Verify DuckDB tables against their corresponding Parquet files."""

from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "processed" / "customer360.duckdb"
PARQUET_DIR = PROJECT_ROOT / "data" / "processed" / "parquet"

EXPECTED_DATASETS = [
    "customer_360",
    "customers_resolved",
    "accounts_linked",
    "orders_linked",
    "interactions_linked",
    "customer_360_lineage",
    "customer_record_lineage",
    "accounts_record_lineage",
    "orders_record_lineage",
    "interactions_record_lineage",
    "quarantine_lineage",
]


def main():
    if not DATABASE_PATH.is_file():
        raise FileNotFoundError(f"DuckDB database not found: {DATABASE_PATH}")

    connection = duckdb.connect(str(DATABASE_PATH), read_only=True)
    failures = []

    try:
        existing_tables = {
            row[0]
            for row in connection.execute("SHOW TABLES").fetchall()
        }

        print("DUCKDB TABLE RECONCILIATION")
        print("=" * 85)

        for dataset_name in EXPECTED_DATASETS:
            if dataset_name not in existing_tables:
                print(f"MISSING TABLE | {dataset_name}")
                failures.append(dataset_name)
                continue

            parquet_path = PARQUET_DIR / f"{dataset_name}.parquet"

            if not parquet_path.is_file():
                print(f"MISSING PARQUET | {dataset_name}")
                failures.append(dataset_name)
                continue

            table_count = connection.execute(
                f'SELECT COUNT(*) FROM "{dataset_name}"'
            ).fetchone()[0]

            parquet_count = connection.execute(
                "SELECT COUNT(*) FROM read_parquet(?)",
                [str(parquet_path)],
            ).fetchone()[0]

            passed = table_count == parquet_count
            status = "PASS" if passed else "FAIL"

            print(
                f"{status:6} | {dataset_name:32} | "
                f"DuckDB={table_count:>10,} | "
                f"Parquet={parquet_count:>10,}"
            )

            if not passed:
                failures.append(dataset_name)

        unexpected_tables = existing_tables - set(EXPECTED_DATASETS)

        print("\nDuckDB tables found:", len(existing_tables))
        print("Expected datasets:", len(EXPECTED_DATASETS))

        if unexpected_tables:
            print("Additional tables:", sorted(unexpected_tables))

        if failures:
            print("\nFAILED DATASETS:", failures)
            raise SystemExit(1)

        print("\nSUCCESS: All DuckDB tables match their Parquet row counts.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
