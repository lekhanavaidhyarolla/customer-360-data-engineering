
"""Create auditable customer-level and row-level source lineage."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


RECORD_LINEAGE_COLUMNS = [
    "dataset_name",
    "source_record_id",
    "source_row_number",
    "source_file",
    "source_file_sha256",
    "ingested_at",
    "source_primary_key",
    "golden_customer_id",
    "lineage_status",
    "match_status",
    "quarantine_reason",
]


PRIMARY_KEY_COLUMNS = {
    "customers": "customer_source_id",
    "accounts": "account_id",
    "orders": "order_id",
    "interactions": "interaction_id",
}


def build_customer_lineage(customer_360):
    """
    Build one lineage summary row for every golden customer.

    Each row records contributing source customer identifiers
    and the processing results for that golden customer.
    """

    required_columns = {
        "golden_customer_id",
        "source_systems",
        "source_customer_ids",
        "source_record_count",
        "identity_match_status",
        "identity_review_required",
        "account_count",
        "order_count",
        "interaction_count",
    }

    missing = required_columns - set(customer_360.columns)

    if missing:
        raise ValueError(
            f"Customer 360 is missing lineage columns: {sorted(missing)}"
        )

    lineage_columns = [
        "golden_customer_id",
        "source_systems",
        "source_customer_ids",
        "source_record_count",
        "identity_match_status",
        "identity_review_required",
        "account_count",
        "order_count",
        "interaction_count",
    ]

    lineage = customer_360[lineage_columns].copy()

    if lineage["golden_customer_id"].isna().any():
        raise ValueError(
            "Lineage contains a missing golden_customer_id."
        )

    if lineage["golden_customer_id"].duplicated().any():
        raise ValueError(
            "Lineage contains duplicate golden_customer_id values."
        )

    return lineage.sort_values(
        "golden_customer_id"
    ).reset_index(drop=True)


def _empty_record_lineage():
    """Return an empty DataFrame with the standard lineage schema."""

    return pd.DataFrame(columns=RECORD_LINEAGE_COLUMNS)


def _build_record_lineage(
    dataframe: pd.DataFrame,
    dataset_name: str,
    primary_key_column: str,
    lineage_status: str,
    quarantine_reason_column: str | None = None,
) -> pd.DataFrame:
    """Convert source records into a standardized row-level lineage table."""

    if dataframe.empty:
        return _empty_record_lineage()

    required = {
        "source_record_id",
        primary_key_column,
    }

    missing = required - set(dataframe.columns)

    if missing:
        raise ValueError(
            f"{dataset_name} lineage is missing columns: {sorted(missing)}"
        )

    result = pd.DataFrame(index=dataframe.index)

    result["dataset_name"] = dataset_name
    result["source_record_id"] = dataframe["source_record_id"]

    optional_columns = [
        "source_row_number",
        "source_file",
        "source_file_sha256",
        "ingested_at",
        "golden_customer_id",
        "match_status",
    ]

    for column in optional_columns:
        if column in dataframe.columns:
            result[column] = dataframe[column]
        else:
            result[column] = None

    result["source_primary_key"] = (
        dataframe[primary_key_column].astype("string")
    )

    result["lineage_status"] = lineage_status

    if quarantine_reason_column:
        if quarantine_reason_column in dataframe.columns:
            result["quarantine_reason"] = (
                dataframe[quarantine_reason_column].astype("string")
            )
        else:
            result["quarantine_reason"] = None
    else:
        result["quarantine_reason"] = None

    result = result[RECORD_LINEAGE_COLUMNS].reset_index(drop=True)

    if result["source_record_id"].isna().any():
        raise ValueError(
            f"{dataset_name} lineage contains missing source_record_id values."
        )

    if result["source_record_id"].duplicated().any():
        raise ValueError(
            f"{dataset_name} lineage contains duplicate source_record_id values."
        )

    return result


def build_row_level_lineage(
    resolved_customers: pd.DataFrame,
    matched: dict[str, pd.DataFrame],
    relationship_quarantine: dict[str, pd.DataFrame],
    validation_quarantine: dict[str, pd.DataFrame],
) -> dict[str, pd.DataFrame]:
    """
    Build source-record lineage for customers and child datasets.

    Records are classified as:
    - linked to a golden customer;
    - identity review required;
    - relationship quarantined; or
    - validation quarantined.
    """

    outputs = {}

    # Customer records have passed validation and identity resolution.
    customer_lineage = _build_record_lineage(
        dataframe=resolved_customers,
        dataset_name="customers",
        primary_key_column="customer_source_id",
        lineage_status="LINKED_TO_GOLDEN_CUSTOMER",
    )

    # Review-required records retain their golden ID but are flagged.
    if not customer_lineage.empty:
        review_mask = (
            customer_lineage["match_status"] == "REVIEW_REQUIRED"
        )

        customer_lineage.loc[
            review_mask,
            "lineage_status",
        ] = "IDENTITY_REVIEW_REQUIRED"

    outputs["customer_record_lineage"] = customer_lineage

    # Build lineage for linked and relationship-quarantined child records.
    for dataset_name in ("accounts", "orders", "interactions"):
        primary_key = PRIMARY_KEY_COLUMNS[dataset_name]

        linked_lineage = _build_record_lineage(
            dataframe=matched[dataset_name],
            dataset_name=dataset_name,
            primary_key_column=primary_key,
            lineage_status="LINKED_TO_GOLDEN_CUSTOMER",
        )

        relationship_lineage = _build_record_lineage(
            dataframe=relationship_quarantine[dataset_name],
            dataset_name=dataset_name,
            primary_key_column=primary_key,
            lineage_status="RELATIONSHIP_QUARANTINED",
            quarantine_reason_column="quarantine_reason",
        )

        outputs[f"{dataset_name}_record_lineage"] = pd.concat(
            [
                linked_lineage,
                relationship_lineage,
            ],
            ignore_index=True,
        )

    # Validation-quarantined records have not entered identity
    # resolution or customer linking.
    validation_parts = []

    for dataset_name in PRIMARY_KEY_COLUMNS:
        quarantined = validation_quarantine[dataset_name]

        part = _build_record_lineage(
            dataframe=quarantined,
            dataset_name=dataset_name,
            primary_key_column=PRIMARY_KEY_COLUMNS[dataset_name],
            lineage_status="VALIDATION_QUARANTINED",
            quarantine_reason_column="_validation_errors",
        )

        validation_parts.append(part)

    validation_lineage = pd.concat(
        validation_parts,
        ignore_index=True,
    )

    # Collect relationship-quarantined child records.
    relationship_parts = []

    for dataset_name in ("accounts", "orders", "interactions"):
        relationship_data = outputs[
            f"{dataset_name}_record_lineage"
        ]

        relationship_parts.append(
            relationship_data.loc[
                relationship_data["lineage_status"]
                == "RELATIONSHIP_QUARANTINED"
            ]
        )

    relationship_lineage = pd.concat(
        relationship_parts,
        ignore_index=True,
    )

    # Combined quarantine lineage includes both rejection stages.
    outputs["quarantine_lineage"] = pd.concat(
        [
            validation_lineage,
            relationship_lineage,
        ],
        ignore_index=True,
    )

    # Verify source-record uniqueness in individual dataset outputs.
    for output_name, dataframe in outputs.items():
        if dataframe.empty:
            continue

        if dataframe["source_record_id"].isna().any():
            raise ValueError(
                f"{output_name} contains missing source_record_id values."
            )

        if output_name != "quarantine_lineage":
            if dataframe["source_record_id"].duplicated().any():
                raise ValueError(
                    f"{output_name} contains duplicate source_record_id values."
                )

    return outputs


def build_lineage_report(
    project_root,
    customer_lineage,
    dataset_details,
    row_lineage=None,
):
    """Create a reconciliation report for customer and record lineage."""

    report = {
        "pipeline": "Customer 360 Data Engineering Pipeline",

        # Preserve compatibility with the original customer-only report.
        "lineage_type": (
            "CUSTOMER_AND_ROW_LEVEL"
            if row_lineage is not None
            else "CUSTOMER_LEVEL"
        ),

        "source_datasets": list(PRIMARY_KEY_COLUMNS),

        "output": {
            "dataset": "customer_360",
            "row_count": int(len(customer_lineage)),
            "unique_golden_customers": int(
                customer_lineage["golden_customer_id"].nunique()
            ),
        },

        "identity_resolution": {
            "source_record_count": int(
                customer_lineage["source_record_count"].sum()
            ),
            "golden_customer_count": int(len(customer_lineage)),
            "review_required_customers": int(
                customer_lineage[
                    "identity_review_required"
                ].sum()
            ),
        },

        "dataset_details": dataset_details,

        "lineage_file": "outputs/customer_360_lineage.csv",
    }

    if row_lineage is not None:
        row_counts = {}

        for output_name, dataframe in row_lineage.items():
            row_counts[output_name] = {
                "row_count": int(len(dataframe)),

                "unique_source_record_ids": int(
                    dataframe["source_record_id"].nunique()
                ),

                "status_breakdown": (
                    dataframe["lineage_status"]
                    .value_counts()
                    .to_dict()
                    if not dataframe.empty
                    else {}
                ),
            }

        report["row_level_lineage"] = {
            "datasets": row_counts,

            "quarantine_records": int(
                len(row_lineage["quarantine_lineage"])
            ),
        }

    return report


def generate_customer_lineage(
    project_root,
    customer_360,
    dataset_details,
    row_lineage=None,
):
    """Write customer-level and optional row-level lineage outputs."""

    project_root = Path(project_root)

    outputs_dir = project_root / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    # Generate customer-level lineage.
    lineage = build_customer_lineage(customer_360)

    lineage.to_csv(
        outputs_dir / "customer_360_lineage.csv",
        index=False,
    )

    # Generate row-level lineage files when provided.
    if row_lineage is not None:
        for output_name, dataframe in row_lineage.items():
            dataframe.to_csv(
                outputs_dir / f"{output_name}.csv",
                index=False,
            )

    # Generate the combined lineage report.
    report = build_lineage_report(
        project_root=project_root,
        customer_lineage=lineage,
        dataset_details=dataset_details,
        row_lineage=row_lineage,
    )

    report_json = outputs_dir / "lineage_report.json"

    with open(
        report_json,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            report,
            file,
            indent=4,
            default=str,
        )

    return lineage, report
