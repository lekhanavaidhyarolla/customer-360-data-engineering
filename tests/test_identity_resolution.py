
import pandas as pd
import pytest

from src.transformation.identity_resolution import (
    resolve_customer_identities,
    build_identity_summary,
)


def make_customer(
    source_system,
    source_id,
    first_name="Ananya",
    last_name="Rao",
    email="ananya@example.com",
    dob="2002-05-10",
):
    return {
        "source_system": source_system,
        "customer_source_id": source_id,
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "date_of_birth": dob,
    }


def test_matching_crm_and_erp_records():
    df = pd.DataFrame([
        make_customer("CRM", "CRM-001"),
        make_customer("ERP", "ERP-001", email=" ANANYA@EXAMPLE.COM "),
    ])

    result = resolve_customer_identities(df)

    assert result["golden_customer_id"].nunique() == 1
    assert set(result["match_status"]) == {"MATCHED_EMAIL_NAME_DOB"}


def test_conflicting_dob_requires_review():
    df = pd.DataFrame([
        make_customer("CRM", "CRM-001"),
        make_customer("ERP", "ERP-001", dob="2001-01-01"),
    ])

    result = resolve_customer_identities(df)

    assert result["golden_customer_id"].nunique() == 2
    assert set(result["match_status"]) == {"REVIEW_REQUIRED"}


def test_missing_email_records_remain_separate():
    df = pd.DataFrame([
        make_customer("CRM", "CRM-001", email=None),
        make_customer("ERP", "ERP-001", email=""),
    ])

    result = resolve_customer_identities(df)

    assert result["golden_customer_id"].nunique() == 2
    assert set(result["match_status"]) == {"NO_EMAIL_SINGLE"}


def test_single_customer_gets_stable_id():
    df = pd.DataFrame([
        make_customer("CRM", "CRM-001"),
    ])

    first = resolve_customer_identities(df)
    second = resolve_customer_identities(df)

    assert (
        first.loc[0, "golden_customer_id"]
        == second.loc[0, "golden_customer_id"]
    )
    assert first.loc[0, "match_status"] == "SINGLE_RECORD"


def test_result_is_independent_of_input_order():
    df = pd.DataFrame([
        make_customer("CRM", "CRM-001"),
        make_customer("ERP", "ERP-001"),
        make_customer(
            "CRM",
            "CRM-002",
            first_name="Rahul",
            last_name="Kumar",
            email="rahul@example.com",
        ),
    ])

    first = resolve_customer_identities(df)
    second = resolve_customer_identities(df.iloc[::-1].reset_index(drop=True))

    first_ids = dict(zip(
        first["customer_source_id"],
        first["golden_customer_id"],
    ))
    second_ids = dict(zip(
        second["customer_source_id"],
        second["golden_customer_id"],
    ))

    assert first_ids == second_ids


def test_duplicate_source_keys_are_rejected():
    df = pd.DataFrame([
        make_customer("CRM", "CRM-001"),
        make_customer("CRM", "CRM-001"),
    ])

    with pytest.raises(ValueError, match="Duplicate"):
        resolve_customer_identities(df)


def test_identity_summary_counts_records():
    df = pd.DataFrame([
        make_customer("CRM", "CRM-001"),
        make_customer("ERP", "ERP-001"),
        make_customer(
            "CRM",
            "CRM-002",
            first_name="Rahul",
            last_name="Kumar",
            email="rahul@example.com",
        ),
    ])

    result = resolve_customer_identities(df)
    summary = build_identity_summary(result)

    assert summary["input_customer_records"] == 3
    assert summary["golden_customers"] == 2
    assert summary["automatically_matched_records"] == 2
    assert summary["single_records"] == 1
