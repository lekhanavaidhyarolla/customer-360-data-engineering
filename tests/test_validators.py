
import pandas as pd
import pytest

from src.validation.validators import validate_dataset


def test_valid_customer_is_accepted():
    data = pd.DataFrame([{
        "customer_source_id": "CRM-001",
        "source_system": "CRM",
        "first_name": "John",
        "last_name": "Smith",
        "email": "john@example.com",
        "phone": "9876543210",
        "date_of_birth": "1995-01-10",
        "address": "Example Street",
        "updated_at": "2025-01-01",
    }])

    result = validate_dataset(data, "customers")

    assert result.valid_count == 1
    assert result.quarantined_count == 0


def test_missing_customer_name_is_quarantined():
    data = pd.DataFrame([{
        "customer_source_id": "CRM-002",
        "source_system": "CRM",
        "first_name": "",
        "last_name": "Smith",
        "email": "john@example.com",
        "phone": "9876543210",
        "date_of_birth": "1995-01-10",
        "address": "Example Street",
        "updated_at": "2025-01-01",
    }])

    result = validate_dataset(data, "customers")

    assert result.valid_count == 0
    assert result.quarantined_count == 1
    assert "missing_first_name" in (
        result.quarantined_records.iloc[0]["_validation_errors"]
    )


def test_duplicate_customer_source_key_is_quarantined():
    row = {
        "customer_source_id": "CRM-003",
        "source_system": "CRM",
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "jane@example.com",
        "phone": "9876543210",
        "date_of_birth": "1995-01-10",
        "address": "Example Street",
        "updated_at": "2025-01-01",
    }

    data = pd.DataFrame([row, row.copy()])

    result = validate_dataset(data, "customers")

    assert result.valid_count == 0
    assert result.quarantined_count == 2


def test_invalid_email_is_quarantined():
    data = pd.DataFrame([{
        "customer_source_id": "CRM-004",
        "source_system": "CRM",
        "first_name": "Jane",
        "last_name": "Smith",
        "email": "not-an-email",
        "phone": "9876543210",
        "date_of_birth": "1995-01-10",
        "address": "Example Street",
        "updated_at": "2025-01-01",
    }])

    result = validate_dataset(data, "customers")

    assert result.quarantined_count == 1
    assert "invalid_email" in (
        result.quarantined_records.iloc[0]["_validation_errors"]
    )


def test_invalid_dataset_name_raises_error():
    with pytest.raises(ValueError):
        validate_dataset(pd.DataFrame(), "unknown")


def test_missing_required_column_raises_error():
    data = pd.DataFrame([{
        "customer_source_id": "CRM-005",
        "source_system": "CRM",
    }])

    with pytest.raises(ValueError, match="missing required columns"):
        validate_dataset(data, "customers")
