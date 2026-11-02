
"""Validate source datasets and preserve row-level source provenance."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# Add the project root to Python's module search path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion.provenance import add_source_provenance
from src.validation.validators import validate_dataset


INPUT_DIR = PROJECT_ROOT / "data" / "sample"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
QUARANTINE_DIR = PROJECT_ROOT / "data" / "quarantine"
OUTPUT_DIR = PROJECT_ROOT / "outputs"

DATASETS = [
    "customers",
    "accounts",
    "orders",
    "interactions",
]


def read_source_dataset(
    input_file: Path,
    dataset_name: str,
) -> pd.DataFrame:
    """
    Read a source CSV while preserving identifier-like columns.

    Phone numbers are strings, not numeric values. Reading them as
    strings prevents decimal formatting and preserves leading zeros.
    """

    dtype_mapping = {}

    if dataset_name == "customers":
        dtype_mapping["phone"] = "string"

    return pd.read_csv(
        input_file,
        dtype=dtype_mapping,
        keep_default_na=True,
    )


def run_validation() -> None:
    """Validate all configured datasets and write reports."""

    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    QUARANTINE_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    run_id = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%SZ"
    )

    report = {
        "run_id": run_id,
        "started_at": datetime.now(timezone.utc).isoformat(),
        "datasets": {},
    }

    total_input = 0
    total_valid = 0
    total_quarantined = 0

    print("\nCUSTOMER 360 DATA VALIDATION")
    print("=" * 55)

    for dataset_name in DATASETS:
        input_file = INPUT_DIR / f"{dataset_name}.csv"

        if not input_file.exists():
            raise FileNotFoundError(
                f"Input dataset not found: {input_file}"
            )

        print(f"\nValidating: {dataset_name}.csv")

        # Read source data with explicit phone-number typing.
        dataframe = read_source_dataset(
            input_file,
            dataset_name,
        )

        # Add deterministic row-level provenance before validation.
        # IDs are unique for each row in this exact source-file version.
        dataframe = add_source_provenance(
            dataframe=dataframe,
            dataset_name=dataset_name,
            source_file=input_file,
        )

        # Record when this pipeline run ingested the source records.
        dataframe["ingested_at"] = datetime.now(
            timezone.utc
        ).isoformat()

        # Validate records while retaining provenance columns.
        result = validate_dataset(
            dataframe,
            dataset_name,
        )

        valid_file = (
            PROCESSED_DIR / f"{dataset_name}_valid.csv"
        )

        quarantine_file = (
            QUARANTINE_DIR / f"{dataset_name}_quarantine.csv"
        )

        # Write valid records.
        result.valid_records.to_csv(
            valid_file,
            index=False,
        )

        # Write rejected records with their provenance intact.
        result.quarantined_records.to_csv(
            quarantine_file,
            index=False,
        )

        # Verify provenance uniqueness within this source dataset.
        all_record_ids = dataframe["source_record_id"]

        if all_record_ids.isna().any():
            raise ValueError(
                f"{dataset_name}: source_record_id contains null values"
            )

        if all_record_ids.duplicated().any():
            raise ValueError(
                f"{dataset_name}: duplicate source_record_id values detected"
            )

        report["datasets"][dataset_name] = {
            "input_rows": result.total_records,
            "valid_rows": result.valid_count,
            "quarantined_rows": result.quarantined_count,
            "success_rate_percent": result.success_rate,
            "unique_source_record_ids": int(
                all_record_ids.nunique()
            ),
            "source_file_sha256": (
                dataframe["source_file_sha256"].iloc[0]
                if not dataframe.empty
                else None
            ),
            "valid_file": str(
                valid_file.relative_to(PROJECT_ROOT)
            ),
            "quarantine_file": str(
                quarantine_file.relative_to(PROJECT_ROOT)
            ),
        }

        total_input += result.total_records
        total_valid += result.valid_count
        total_quarantined += result.quarantined_count

        print(f"  Input records:      {result.total_records:,}")
        print(f"  Valid records:      {result.valid_count:,}")
        print(f"  Quarantined:        {result.quarantined_count:,}")
        print(f"  Success rate:       {result.success_rate}%")
        print(
            f"  Unique source IDs:  "
            f"{all_record_ids.nunique():,}"
        )

    overall_success_rate = (
        round(total_valid / total_input * 100, 2)
        if total_input
        else 100.0
    )

    report["summary"] = {
        "total_input_rows": total_input,
        "total_valid_rows": total_valid,
        "total_quarantined_rows": total_quarantined,
        "overall_success_rate_percent": overall_success_rate,
    }

    report["completed_at"] = datetime.now(
        timezone.utc
    ).isoformat()

    report_file = OUTPUT_DIR / "validation_report.json"

    with report_file.open("w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\n" + "=" * 55)
    print("VALIDATION COMPLETED")
    print("=" * 55)
    print(f"Total input:       {total_input:,}")
    print(f"Total valid:       {total_valid:,}")
    print(f"Total quarantined: {total_quarantined:,}")
    print(f"Overall success:   {overall_success_rate}%")
    print(f"\nReport saved: {report_file}")


if __name__ == "__main__":
    run_validation()
