
import pandas as pd
from pandas.testing import assert_frame_equal

from src.transformation.customer_360 import build_customer_360


def sample_data():
    customers = pd.DataFrame([
        {
            "golden_customer_id": "GC001",
            "source_system": "CRM",
            "customer_source_id": "CRM-001",
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "phone": "9876543210",
            "date_of_birth": "1995-01-10",
            "address": "Address from CRM",
            "match_status": "MATCHED_EMAIL_NAME_DOB",
            "identity_review_required": False,
        },
        {
            "golden_customer_id": "GC001",
            "source_system": "ERP",
            "customer_source_id": "ERP-001",
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@example.com",
            "phone": "9876543210",
            "date_of_birth": "1995-01-10",
            "address": "Address from ERP",
            "match_status": "MATCHED_EMAIL_NAME_DOB",
            "identity_review_required": False,
        },
        {
            "golden_customer_id": "GC002",
            "source_system": "CRM",
            "customer_source_id": "CRM-002",
            "first_name": "Bob",
            "last_name": "Jones",
            "email": "bob@example.com",
            "phone": "9123456780",
            "date_of_birth": "1990-05-20",
            "address": "Bob's address",
            "match_status": "REVIEW_REQUIRED",
            "identity_review_required": True,
        },
    ])

    accounts = pd.DataFrame([
        {
            "account_id": "A001",
            "customer_source_id": "CRM-001",
            "balance": 1000.0,
        },
        {
            "account_id": "A002",
            "customer_source_id": "ERP-001",
            "balance": 500.0,
        },
        {
            "account_id": "A003",
            "customer_source_id": "UNKNOWN-001",
            "balance": 200.0,
        },
    ])

    orders = pd.DataFrame([
        {
            "order_id": "O001",
            "customer_source_id": "CRM-001",
            "order_date": "2026-01-10",
            "amount": 250.0,
            "quantity": 2,
        },
        {
            "order_id": "O002",
            "customer_source_id": "ERP-001",
            "order_date": "2026-02-10",
            "amount": 150.0,
            "quantity": 1,
        },
    ])

    interactions = pd.DataFrame([
        {
            "interaction_id": "I001",
            "customer_source_id": "CRM-001",
            "interaction_date": "2026-03-01",
        },
    ])

    raw_customer_ids = {
        "CRM-001",
        "ERP-001",
        "CRM-002",
    }

    return customers, accounts, orders, interactions, raw_customer_ids


def run_build():
    customers, accounts, orders, interactions, raw_ids = sample_data()

    return build_customer_360(
        resolved_customers=customers,
        accounts=accounts,
        orders=orders,
        interactions=interactions,
        raw_customer_ids=raw_ids,
    )


def test_one_row_per_golden_customer():
    customer_360, _, _ = run_build()

    assert len(customer_360) == 2
    assert customer_360["golden_customer_id"].nunique() == 2
    assert not customer_360["golden_customer_id"].duplicated().any()


def test_account_aggregation():
    customer_360, _, _ = run_build()

    alice = customer_360[
        customer_360["golden_customer_id"] == "GC001"
    ].iloc[0]

    assert alice["account_count"] == 2
    assert alice["total_account_balance"] == 1500.0


def test_order_aggregation():
    customer_360, _, _ = run_build()

    alice = customer_360[
        customer_360["golden_customer_id"] == "GC001"
    ].iloc[0]

    assert alice["order_count"] == 2
    assert alice["total_order_amount"] == 400.0
    assert alice["total_quantity"] == 3
    assert str(alice["latest_order_date"])[:10] == "2026-02-10"


def test_interaction_aggregation():
    customer_360, _, _ = run_build()

    alice = customer_360[
        customer_360["golden_customer_id"] == "GC001"
    ].iloc[0]

    assert alice["interaction_count"] == 1
    assert str(alice["latest_interaction_date"])[:10] == "2026-03-01"


def test_orphan_reference_is_quarantined():
    _, matched, quarantine = run_build()

    assert len(matched["accounts"]) == 2
    assert len(quarantine["accounts"]) == 1

    reason = quarantine["accounts"].iloc[0]["quarantine_reason"]
    assert reason == "ORPHAN_CUSTOMER_REFERENCE"


def test_customer_not_validated_is_quarantined():
    customers, accounts, orders, interactions, raw_ids = sample_data()

    accounts.loc[len(accounts)] = {
        "account_id": "A004",
        "customer_source_id": "CRM-BLOCKED",
        "balance": 300.0,
    }

    raw_ids.add("CRM-BLOCKED")

    _, _, quarantine = build_customer_360(
        resolved_customers=customers,
        accounts=accounts,
        orders=orders,
        interactions=interactions,
        raw_customer_ids=raw_ids,
    )

    blocked = quarantine["accounts"]
    assert len(blocked) == 2
    assert "CUSTOMER_NOT_VALIDATED" in blocked["quarantine_reason"].values


def test_build_is_repeatable():
    first, _, _ = run_build()
    second, _, _ = run_build()

    first = first.sort_values("golden_customer_id").reset_index(drop=True)
    second = second.sort_values("golden_customer_id").reset_index(drop=True)

    assert_frame_equal(first, second)
