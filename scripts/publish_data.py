
"""Publish Customer 360 datasets and lineage to Parquet and DuckDB."""

import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.publishing.publisher import publish_datasets


def load_csv(path: Path) -> pd.DataFrame:
    """Load a CSV file and report a clear error if it is missing."""

    if not path.exists():
        raise FileNotFoundError(
            f"Required publishing input not found: {path}"
        )

    return pd.read_csv(path)


def main():
    processed_dir = PROJECT_ROOT / "data" / "processed"
    outputs_dir = PROJECT_ROOT / "outputs"

    print("Loading Customer 360 datasets and lineage...")

    datasets = {
        # Main Customer 360 outputs
        "customer_360": load_csv(
            processed_dir / "customer_360.csv"
        ),
        "customers_resolved": load_csv(
            processed_dir / "customers_resolved.csv"
        ),
        "accounts_linked": load_csv(
            processed_dir / "accounts_linked.csv"
        ),
        "orders_linked": load_csv(
            processed_dir / "orders_linked.csv"
        ),
        "interactions_linked": load_csv(
            processed_dir / "interactions_linked.csv"
        ),

        # Customer-level lineage
        "customer_360_lineage": load_csv(
            outputs_dir / "customer_360_lineage.csv"
        ),

        # Row-level source lineage
        "customer_record_lineage": load_csv(
            outputs_dir / "customer_record_lineage.csv"
        ),
        "accounts_record_lineage": load_csv(
            outputs_dir / "accounts_record_lineage.csv"
        ),
        "orders_record_lineage": load_csv(
            outputs_dir / "orders_record_lineage.csv"
        ),
        "interactions_record_lineage": load_csv(
            outputs_dir / "interactions_record_lineage.csv"
        ),
        "quarantine_lineage": load_csv(
            outputs_dir / "quarantine_lineage.csv"
        ),
    }

    print("\nDatasets ready for publishing:")

    for name, dataframe in datasets.items():
        print(f"{name}: {len(dataframe):,} rows")

    print("\nPublishing datasets to Parquet and DuckDB...")

    report = publish_datasets(
        project_root=PROJECT_ROOT,
        datasets=datasets,
    )

    print("\nPUBLISHING COMPLETED")
    print("=" * 50)

    for name, dataframe in datasets.items():
        print(f"{name}: {len(dataframe):,} rows published")

    print("\nDuckDB database:")
    print(processed_dir / "customer360.duckdb")

    print("\nParquet directory:")
    print(processed_dir / "parquet")

    print("\nPublishing report:")
    print(outputs_dir / "publishing_report.json")


if __name__ == "__main__":
    main()
