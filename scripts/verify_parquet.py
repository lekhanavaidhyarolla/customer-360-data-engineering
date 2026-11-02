
"""Verify that all expected Parquet datasets exist and are readable."""

from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
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
    if not PARQUET_DIR.is_dir():
        raise FileNotFoundError(f"Parquet directory not found: {PARQUET_DIR}")

    connection = duckdb.connect(":memory:")
    failures = []

    try:
        print("PARQUET DATASET VERIFICATION")
        print("=" * 85)

        for dataset_name in EXPECTED_DATASETS:
            parquet_path = PARQUET_DIR / f"{dataset_name}.parquet"

            if not parquet_path.is_file():
                print(f"MISSING | {dataset_name}")
                failures.append(dataset_name)
                continue

            try:
                actual_count = connection.execute(
                    "SELECT COUNT(*) FROM read_parquet(?)",
                    [str(parquet_path)],
                ).fetchone()[0]

                print(
                    f"PASS   | {dataset_name:32} | "
                    f"rows={actual_count:>10,} | "
                    f"size={parquet_path.stat().st_size:,} bytes"
                )

            except Exception as error:
                print(f"FAIL   | {dataset_name:32} | {error}")
                failures.append(dataset_name)

        print("\nExpected Parquet files:", len(EXPECTED_DATASETS))

        if failures:
            print("FAILED DATASETS:", failures)
            raise SystemExit(1)

        print("\nSUCCESS: All expected Parquet files exist and are readable.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
