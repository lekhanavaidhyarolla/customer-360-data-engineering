
from __future__ import annotations

from dataclasses import dataclass
import re

import pandas as pd


@dataclass
class ValidationResult:
    valid_records: pd.DataFrame
    quarantined_records: pd.DataFrame
    total_records: int

    @property
    def valid_count(self) -> int:
        return len(self.valid_records)

    @property
    def quarantined_count(self) -> int:
        return len(self.quarantined_records)

    @property
    def success_rate(self) -> float:
        if self.total_records == 0:
            return 100.0
        return round(self.valid_count / self.total_records * 100, 2)


SCHEMAS = {
    "customers": {
        "required_columns": [
            "customer_source_id",
            "source_system",
            "first_name",
            "last_name",
            "email",
            "phone",
            "date_of_birth",
            "updated_at",
        ],
        "required_values": [
            "customer_source_id",
            "source_system",
            "first_name",
            "last_name",
        ],
        "primary_key": ["source_system", "customer_source_id"],
        "date_columns": ["date_of_birth", "updated_at"],
    },
    "accounts": {
        "required_columns": [
            "account_id",
            "customer_source_id",
            "source_system",
            "account_type",
            "account_status",
            "balance",
            "opened_at",
        ],
        "required_values": [
            "account_id",
            "customer_source_id",
            "source_system",
            "account_type",
            "account_status",
            "balance",
            "opened_at",
        ],
        "primary_key": ["account_id"],
        "date_columns": ["opened_at"],
    },
    "orders": {
        "required_columns": [
            "order_id",
            "customer_source_id",
            "source_system",
            "order_date",
            "product",
            "quantity",
            "amount",
            "order_status",
        ],
        "required_values": [
            "order_id",
            "customer_source_id",
            "source_system",
            "order_date",
            "product",
            "quantity",
            "amount",
            "order_status",
        ],
        "primary_key": ["order_id"],
        "date_columns": ["order_date"],
    },
    "interactions": {
        "required_columns": [
            "interaction_id",
            "customer_source_id",
            "source_system",
            "interaction_type",
            "channel",
            "interaction_date",
            "description",
            "resolution_status",
        ],
        "required_values": [
            "interaction_id",
            "customer_source_id",
            "source_system",
            "interaction_type",
            "channel",
            "interaction_date",
            "resolution_status",
        ],
        "primary_key": ["interaction_id"],
        "date_columns": ["interaction_date"],
    },
}


def _is_empty(value) -> bool:
    return pd.isna(value) or str(value).strip() == ""


def validate_dataset(
    dataframe: pd.DataFrame,
    dataset_name: str,
) -> ValidationResult:
    """
    Validate one source dataset.

    Invalid rows are retained in quarantine with validation reasons.
    The input DataFrame is not modified.
    """

    if dataset_name not in SCHEMAS:
        raise ValueError(
            f"Unsupported dataset: {dataset_name}. "
            f"Expected one of: {list(SCHEMAS)}"
        )

    config = SCHEMAS[dataset_name]
    df = dataframe.copy().reset_index(drop=True)

    # 1. Required-column checks.
    missing_columns = [
        column
        for column in config["required_columns"]
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"{dataset_name}: missing required columns: "
            f"{missing_columns}"
        )

    errors = [[] for _ in range(len(df))]

    # 2. Required-value checks.
    for column in config["required_values"]:
        for index, value in enumerate(df[column]):
            if _is_empty(value):
                errors[index].append(f"missing_{column}")

    # 3. Duplicate primary-key checks.
    key_columns = config["primary_key"]

    duplicate_mask = df.duplicated(
        subset=key_columns,
        keep=False,
    )

    for index in df.index[duplicate_mask]:
        errors[index].append("duplicate_primary_key")

    # 4. Email and phone validation.
    if dataset_name == "customers":

        email_pattern = re.compile(
            r"^[A-Z0-9.!#$%&'*+/=?^_`{|}~-]+@"
            r"[A-Z0-9](?:[A-Z0-9-]*[A-Z0-9])?"
            r"(?:\.[A-Z0-9](?:[A-Z0-9-]*[A-Z0-9])?)+$",
            re.IGNORECASE,
        )

        for index, value in enumerate(df["email"]):
            if not _is_empty(value):
                if not email_pattern.fullmatch(str(value).strip()):
                    errors[index].append("invalid_email")

        # Missing phone numbers are allowed.
        # Non-empty phone numbers must contain exactly
        # 10 digits and only permitted formatting characters.
        for index, value in enumerate(df["phone"]):
            if not _is_empty(value):
                phone = str(value).strip()

                if not re.fullmatch(r"[0-9+\s().-]+", phone):
                    errors[index].append("invalid_phone")
                    continue

                digits = re.sub(r"\D", "", phone)

                if len(digits) != 10:
                    errors[index].append("invalid_phone")

    # 5. Numeric checks.
    numeric_rules = {}

    if dataset_name == "accounts":
        numeric_rules = {
            "balance": "non_negative",
        }

    elif dataset_name == "orders":
        numeric_rules = {
            "quantity": "positive",
            "amount": "non_negative",
        }

    for column, rule in numeric_rules.items():
        numeric_values = pd.to_numeric(
            df[column],
            errors="coerce",
        )

        for index, value in enumerate(numeric_values):
            if pd.isna(value):
                if not _is_empty(df.at[index, column]):
                    errors[index].append(
                        f"invalid_numeric_{column}"
                    )
                continue

            if rule == "non_negative" and value < 0:
                errors[index].append(
                    f"negative_{column}"
                )

            if rule == "positive" and value <= 0:
                errors[index].append(
                    f"non_positive_{column}"
                )

    # 6. Date checks.
    for column in config["date_columns"]:
        parsed_dates = pd.to_datetime(
            df[column],
            errors="coerce",
        )

        for index, parsed_date in enumerate(parsed_dates):
            if not _is_empty(df.at[index, column]):
                if pd.isna(parsed_date):
                    errors[index].append(
                        f"invalid_date_{column}"
                    )

    # 7. Allowed-value checks.
    allowed_values = {
        "account_type": {
            "SAVINGS",
            "CURRENT",
            "CREDIT",
        },
        "account_status": {
            "ACTIVE",
            "CLOSED",
            "SUSPENDED",
        },
        "order_status": {
            "PLACED",
            "SHIPPED",
            "DELIVERED",
            "CANCELLED",
            "RETURNED",
        },
        "interaction_type": {
            "COMPLAINT",
            "QUERY",
            "FEEDBACK",
            "PURCHASE_ENQUIRY",
            "SUPPORT_REQUEST",
        },
        "channel": {
            "EMAIL",
            "PHONE",
            "CHAT",
            "WEB",
        },
        "resolution_status": {
            "OPEN",
            "IN_PROGRESS",
            "RESOLVED",
        },
    }

    for column, allowed in allowed_values.items():
        if column not in df.columns:
            continue

        for index, value in enumerate(df[column]):
            if not _is_empty(value):
                normalized = str(value).strip().upper()

                if normalized not in allowed:
                    errors[index].append(
                        f"invalid_{column}"
                    )

    # 8. Separate valid and quarantined records.
    df["_validation_errors"] = [
        ";".join(row_errors)
        for row_errors in errors
    ]

    invalid_mask = df["_validation_errors"] != ""

    valid_records = df.loc[~invalid_mask].copy()
    quarantined_records = df.loc[invalid_mask].copy()

    return ValidationResult(
        valid_records=valid_records,
        quarantined_records=quarantined_records,
        total_records=len(df),
    )
