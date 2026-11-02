
import pandas as pd
import pytest

from src.ingestion.provenance import add_source_provenance


def test_provenance_ids_are_deterministic(tmp_path):
    source_file = tmp_path / "customers.csv"
    source_file.write_text(
        "customer_source_id,first_name\nCRM-001,Ana\nCRM-002,Bob\n",
        encoding="utf-8",
    )

    dataframe = pd.DataFrame({
        "customer_source_id": ["CRM-001", "CRM-002"],
        "first_name": ["Ana", "Bob"],
    })

    first = add_source_provenance(
        dataframe, "customers", source_file
    )
    second = add_source_provenance(
        dataframe, "customers", source_file
    )

    assert first["source_record_id"].tolist() == (
        second["source_record_id"].tolist()
    )


def test_duplicate_business_keys_get_distinct_record_ids(tmp_path):
    source_file = tmp_path / "customers.csv"
    source_file.write_text(
        "customer_source_id,first_name\nCRM-001,Ana\nCRM-001,Ana\n",
        encoding="utf-8",
    )

    dataframe = pd.DataFrame({
        "customer_source_id": ["CRM-001", "CRM-001"],
        "first_name": ["Ana", "Ana"],
    })

    result = add_source_provenance(
        dataframe, "customers", source_file
    )

    assert result["source_record_id"].nunique() == 2
    assert result["source_row_number"].tolist() == [1, 2]


def test_provenance_ids_change_when_source_file_changes(tmp_path):
    source_file = tmp_path / "customers.csv"

    dataframe = pd.DataFrame({
        "customer_source_id": ["CRM-001"],
        "first_name": ["Ana"],
    })

    source_file.write_text(
        "customer_source_id,first_name\nCRM-001,Ana\n",
        encoding="utf-8",
    )

    first = add_source_provenance(
        dataframe, "customers", source_file
    )

    source_file.write_text(
        "customer_source_id,first_name\nCRM-001,Anita\n",
        encoding="utf-8",
    )

    second = add_source_provenance(
        dataframe, "customers", source_file
    )

    assert (
        first.loc[0, "source_record_id"]
        != second.loc[0, "source_record_id"]
    )


def test_missing_source_file_raises_error(tmp_path):
    dataframe = pd.DataFrame({"id": [1]})

    with pytest.raises(FileNotFoundError):
        add_source_provenance(
            dataframe,
            "customers",
            tmp_path / "missing.csv",
        )


def test_input_dataframe_is_not_modified(tmp_path):
    source_file = tmp_path / "customers.csv"
    source_file.write_text(
        "customer_source_id\nCRM-001\n",
        encoding="utf-8",
    )

    dataframe = pd.DataFrame({
        "customer_source_id": ["CRM-001"],
    })
    original_columns = dataframe.columns.tolist()

    add_source_provenance(
        dataframe, "customers", source_file
    )

    assert dataframe.columns.tolist() == original_columns
