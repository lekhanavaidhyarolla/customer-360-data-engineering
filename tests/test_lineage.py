
import json

import pandas as pd
import pytest

from src.monitoring.lineage import (
    build_customer_lineage,
    generate_customer_lineage,
)


@pytest.fixture
def sample_customer_360():
    return pd.DataFrame(
        [
            {
                "golden_customer_id": "GOLDEN_002",
                "source_systems": "CRM,ERP",
                "source_customer_ids": "CRM-002,ERP-002",
                "source_record_count": 2,
                "identity_match_status": "MATCHED_EMAIL_NAME_DOB",
                "identity_review_required": False,
                "account_count": 2,
                "order_count": 3,
                "interaction_count": 1,
            },
            {
                "golden_customer_id": "GOLDEN_001",
                "source_systems": "CRM",
                "source_customer_ids": "CRM-001",
                "source_record_count": 1,
                "identity_match_status": "SINGLE_RECORD",
                "identity_review_required": False,
                "account_count": 1,
                "order_count": 2,
                "interaction_count": 4,
            },
        ]
    )


def test_build_customer_lineage_returns_one_row_per_customer(
    sample_customer_360,
):
    lineage = build_customer_lineage(sample_customer_360)

    assert len(lineage) == 2
    assert lineage["golden_customer_id"].nunique() == 2
    assert list(lineage["golden_customer_id"]) == [
        "GOLDEN_001",
        "GOLDEN_002",
    ]


def test_build_customer_lineage_rejects_missing_columns():
    invalid_data = pd.DataFrame(
        {
            "golden_customer_id": ["GOLDEN_001"],
            "source_systems": ["CRM"],
        }
    )

    with pytest.raises(
        ValueError,
        match="missing lineage columns",
    ):
        build_customer_lineage(invalid_data)


def test_build_customer_lineage_rejects_missing_golden_id(
    sample_customer_360,
):
    invalid_data = sample_customer_360.copy()

    invalid_data.loc[0, "golden_customer_id"] = None

    with pytest.raises(
        ValueError,
        match="missing golden_customer_id",
    ):
        build_customer_lineage(invalid_data)


def test_build_customer_lineage_rejects_duplicate_golden_ids(
    sample_customer_360,
):
    invalid_data = sample_customer_360.copy()

    invalid_data.loc[1, "golden_customer_id"] = "GOLDEN_002"

    with pytest.raises(
        ValueError,
        match="duplicate golden_customer_id",
    ):
        build_customer_lineage(invalid_data)


def test_generate_customer_lineage_creates_output_files(
    tmp_path,
    sample_customer_360,
):
    dataset_details = {
        "customers": {
            "resolved_customer_records": 2,
            "golden_customers": 2,
        },
        "accounts": {
            "validated_input_rows": 3,
            "linked_rows": 3,
            "relationship_quarantined_rows": 0,
        },
    }

    lineage, report = generate_customer_lineage(
        project_root=tmp_path,
        customer_360=sample_customer_360,
        dataset_details=dataset_details,
    )

    lineage_path = (
        tmp_path / "outputs" / "customer_360_lineage.csv"
    )

    report_path = (
        tmp_path / "outputs" / "lineage_report.json"
    )

    assert lineage_path.exists()
    assert report_path.exists()

    saved_lineage = pd.read_csv(lineage_path)

    assert len(saved_lineage) == 2
    assert saved_lineage["golden_customer_id"].nunique() == 2

    with open(report_path, "r", encoding="utf-8") as file:
        saved_report = json.load(file)

    assert saved_report["output"]["row_count"] == 2
    assert saved_report["output"]["unique_golden_customers"] == 2
    assert saved_report["identity_resolution"]["source_record_count"] == 3
    assert report["lineage_type"] == "CUSTOMER_LEVEL"
