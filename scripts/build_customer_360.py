
"""Build the Customer 360 dataset and generate auditable lineage."""

import sys
import json
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.transformation.customer_360 import build_customer_360
from src.monitoring.lineage import (
    build_row_level_lineage,
    generate_customer_lineage,
)


DATASETS = [
    "customers",
    "accounts",
    "orders",
    "interactions",
]


def load_csv(path: Path) -> pd.DataFrame:
    """Load a CSV and provide a clear error if it is missing."""

    if not path.exists():
        raise FileNotFoundError(f"Required pipeline file not found: {path}")

    return pd.read_csv(path)


def main():
    data_dir = PROJECT_ROOT / "data"
    processed_dir = data_dir / "processed"
    quarantine_dir = data_dir / "quarantine"
    outputs_dir = PROJECT_ROOT / "outputs"

    quarantine_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    print("Loading validated datasets...")

    customers = load_csv(
        processed_dir / "customers_resolved.csv"
    )

    accounts = load_csv(
        processed_dir / "accounts_valid.csv"
    )

    orders = load_csv(
        processed_dir / "orders_valid.csv"
    )

    interactions = load_csv(
        processed_dir / "interactions_valid.csv"
    )

    raw_customers = load_csv(
        data_dir / "sample" / "customers.csv"
    )

    raw_customer_ids = set(
        raw_customers["customer_source_id"]
        .dropna()
        .astype(str)
    )

    print("Building Customer 360 view...")

    customer_360, matched, quarantine = build_customer_360(
        resolved_customers=customers,
        accounts=accounts,
        orders=orders,
        interactions=interactions,
        raw_customer_ids=raw_customer_ids,
    )

    # Save the unified Customer 360 dataset.
    output_path = processed_dir / "customer_360.csv"

    customer_360.to_csv(
        output_path,
        index=False,
    )

    # Save linked child datasets.
    for dataset_name, dataframe in matched.items():
        dataframe.to_csv(
            processed_dir / f"{dataset_name}_linked.csv",
            index=False,
        )

    # Save relationship-quarantined records.
    quarantine_counts = {}

    for dataset_name, dataframe in quarantine.items():
        quarantine_path = (
            quarantine_dir
            / f"{dataset_name}_relationship_quarantine.csv"
        )

        dataframe.to_csv(
            quarantine_path,
            index=False,
        )

        quarantine_counts[dataset_name] = {
            "quarantined_rows": int(len(dataframe)),
            "reasons": (
                dataframe["quarantine_reason"]
                .value_counts()
                .to_dict()
                if "quarantine_reason" in dataframe.columns
                else {}
            ),
        }

    # Load validation-quarantined records for all four source datasets.
    print("Loading validation-quarantined records...")

    validation_quarantine = {
        dataset_name: load_csv(
            quarantine_dir / f"{dataset_name}_quarantine.csv"
        )
        for dataset_name in DATASETS
    }

    # Prepare source dataset details for lineage reporting.
    dataset_details = {
        "customers": {
            "resolved_customer_records": int(len(customers)),
            "golden_customers": int(len(customer_360)),
            "validation_quarantined_rows": int(
                len(validation_quarantine["customers"])
            ),
        },
        "accounts": {
            "validated_input_rows": int(len(accounts)),
            "linked_rows": int(len(matched["accounts"])),
            "relationship_quarantined_rows": int(
                len(quarantine["accounts"])
            ),
            "validation_quarantined_rows": int(
                len(validation_quarantine["accounts"])
            ),
        },
        "orders": {
            "validated_input_rows": int(len(orders)),
            "linked_rows": int(len(matched["orders"])),
            "relationship_quarantined_rows": int(
                len(quarantine["orders"])
            ),
            "validation_quarantined_rows": int(
                len(validation_quarantine["orders"])
            ),
        },
        "interactions": {
            "validated_input_rows": int(len(interactions)),
            "linked_rows": int(len(matched["interactions"])),
            "relationship_quarantined_rows": int(
                len(quarantine["interactions"])
            ),
            "validation_quarantined_rows": int(
                len(validation_quarantine["interactions"])
            ),
        },
    }

    # Build row-level lineage using the original source-record IDs.
    print("\nGenerating row-level lineage...")

    row_lineage = build_row_level_lineage(
        resolved_customers=customers,
        matched=matched,
        relationship_quarantine=quarantine,
        validation_quarantine=validation_quarantine,
    )

    # Generate customer-level and row-level lineage files and report.
    print("Generating customer-level lineage and reconciliation report...")

    lineage, lineage_report = generate_customer_lineage(
        project_root=PROJECT_ROOT,
        customer_360=customer_360,
        dataset_details=dataset_details,
        row_lineage=row_lineage,
    )

    # Prepare Customer 360 build metrics.
    row_lineage_metrics = {}

    for output_name, dataframe in row_lineage.items():
        row_lineage_metrics[output_name] = {
            "row_count": int(len(dataframe)),
            "unique_source_record_ids": int(
                dataframe["source_record_id"].nunique()
            ),
        }

    metrics = {
        "golden_customers": int(len(customer_360)),
        "account_rows_linked": int(len(matched["accounts"])),
        "order_rows_linked": int(len(matched["orders"])),
        "interaction_rows_linked": int(
            len(matched["interactions"])
        ),
        "relationship_quarantine": quarantine_counts,
        "validation_quarantine": {
            dataset_name: int(len(dataframe))
            for dataset_name, dataframe in validation_quarantine.items()
        },
        "lineage": {
            "customer_lineage_records": int(len(lineage)),
            "unique_golden_customers": int(
                lineage["golden_customer_id"].nunique()
            ),
            "review_required_customers": int(
                lineage["identity_review_required"].sum()
            ),
            "row_level_outputs": row_lineage_metrics,
            "total_row_level_lineage_records": int(
                sum(
                    len(dataframe)
                    for name, dataframe in row_lineage.items()
                    if name != "quarantine_lineage"
                )
            ),
            "quarantine_lineage_records": int(
                len(row_lineage["quarantine_lineage"])
            ),
        },
    }

    metrics_path = outputs_dir / "customer_360_metrics.json"

    with open(
        metrics_path,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            metrics,
            file,
            indent=4,
            default=str,
        )

    # Display execution results.
    print("\nCUSTOMER 360 BUILD RESULTS")
    print("=" * 50)

    print("Golden customers:", f"{len(customer_360):,}")

    for dataset_name, dataframe in matched.items():
        print(
            f"{dataset_name} linked rows: {len(dataframe):,}"
        )

    for dataset_name, dataframe in quarantine.items():
        print(
            f"{dataset_name} relationship-quarantined rows: "
            f"{len(dataframe):,}"
        )

    print("\nVALIDATION QUARANTINE")
    print("=" * 50)

    for dataset_name, dataframe in validation_quarantine.items():
        print(
            f"{dataset_name}: {len(dataframe):,} records"
        )

    print("\nCUSTOMER-LEVEL LINEAGE")
    print("=" * 50)

    print("Lineage records:", f"{len(lineage):,}")
    print(
        "Unique golden customers:",
        f"{lineage['golden_customer_id'].nunique():,}",
    )
    print(
        "Review-required customers:",
        f"{int(lineage['identity_review_required'].sum()):,}",
    )

    print("\nROW-LEVEL LINEAGE")
    print("=" * 50)

    for output_name, dataframe in row_lineage.items():
        print(
            f"{output_name}: {len(dataframe):,} rows"
        )

    print("\nOUTPUT FILES")
    print("=" * 50)

    print("Customer 360:", output_path)
    print("Metrics:", metrics_path)
    print(
        "Customer-level lineage:",
        outputs_dir / "customer_360_lineage.csv",
    )

    for output_name in row_lineage:
        print(
            f"{output_name}:",
            outputs_dir / f"{output_name}.csv",
        )

    print(
        "Lineage report:",
        outputs_dir / "lineage_report.json",
    )


if __name__ == "__main__":
    main()
