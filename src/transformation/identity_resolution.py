
"""Deterministic customer identity resolution for the Customer 360 pipeline."""

import hashlib
import re

import pandas as pd


REQUIRED_COLUMNS = {
    "source_system",
    "customer_source_id",
    "first_name",
    "last_name",
    "email",
    "date_of_birth",
}


def normalize_text(value):
    """Normalize text for reliable comparison."""
    if pd.isna(value):
        return ""

    return re.sub(r"\s+", " ", str(value).strip().lower())


def stable_id(prefix, values):
    """Create a deterministic ID from sorted identity values."""
    canonical = "|".join(sorted(str(value) for value in values))
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest.upper()}"


def resolve_customer_identities(customers):
    """
    Resolve customers conservatively using normalized email, full name,
    and date of birth.

    Exact matches are grouped into one golden customer.
    Ambiguous shared-email groups are flagged for manual review.
    Records without email remain separate.
    """

    missing_columns = REQUIRED_COLUMNS - set(customers.columns)
    if missing_columns:
        raise ValueError(
            f"Missing required columns: {sorted(missing_columns)}"
        )

    result = customers.copy().reset_index(drop=True)

    # Normalize matching fields without changing the original source values.
    result["_normalized_email"] = (
        result["email"].apply(normalize_text)
    )
    result["_normalized_first_name"] = (
        result["first_name"].apply(normalize_text)
    )
    result["_normalized_last_name"] = (
        result["last_name"].apply(normalize_text)
    )
    result["_normalized_dob"] = (
        result["date_of_birth"]
        .apply(normalize_text)
    )

    result["golden_customer_id"] = None
    result["match_status"] = None
    result["match_group_id"] = None

    # A source record must have a unique identity key.
    source_keys = list(
        zip(
            result["source_system"].astype(str),
            result["customer_source_id"].astype(str),
        )
    )

    if len(source_keys) != len(set(source_keys)):
        raise ValueError(
            "Duplicate (source_system, customer_source_id) records "
            "must be resolved before identity matching."
        )

    # Records without email cannot be safely matched using this rule.
    no_email_indices = result.index[
        result["_normalized_email"] == ""
    ]

    for index in no_email_indices:
        source_key = (
            f"{result.at[index, 'source_system']}|"
            f"{result.at[index, 'customer_source_id']}"
        )

        result.at[index, "golden_customer_id"] = stable_id(
            "GC", [source_key]
        )
        result.at[index, "match_status"] = "NO_EMAIL_SINGLE"
        result.at[index, "match_group_id"] = stable_id(
            "MG", [source_key]
        )

    # Process records with email, one email group at a time.
    email_indices = result.index[
        result["_normalized_email"] != ""
    ]

    for email, group in result.loc[email_indices].groupby(
        "_normalized_email",
        sort=True,
    ):
        indices = list(group.index)

        source_keys = [
            (
                f"{result.at[i, 'source_system']}|"
                f"{result.at[i, 'customer_source_id']}"
            )
            for i in indices
        ]

        if len(indices) == 1:
            index = indices[0]

            result.at[index, "golden_customer_id"] = stable_id(
                "GC", source_keys
            )
            result.at[index, "match_status"] = "SINGLE_RECORD"
            result.at[index, "match_group_id"] = stable_id(
                "MG", source_keys
            )
            continue

        # All records must have complete and consistent identity fields.
        first_names = {
            result.at[i, "_normalized_first_name"] for i in indices
        }
        last_names = {
            result.at[i, "_normalized_last_name"] for i in indices
        }
        dates_of_birth = {
            result.at[i, "_normalized_dob"] for i in indices
        }

        complete_identity = (
            all(first_names)
            and all(last_names)
            and all(dates_of_birth)
        )

        consistent_identity = (
            len(first_names) == 1
            and len(last_names) == 1
            and len(dates_of_birth) == 1
        )

        review_group_id = stable_id("MG", source_keys)

        if complete_identity and consistent_identity:
            golden_id = stable_id("GC", source_keys)

            for index in indices:
                result.at[index, "golden_customer_id"] = golden_id
                result.at[index, "match_status"] = (
                    "MATCHED_EMAIL_NAME_DOB"
                )
                result.at[index, "match_group_id"] = review_group_id

        else:
            # Never automatically merge ambiguous records.
            for index, source_key in zip(indices, source_keys):
                result.at[index, "golden_customer_id"] = stable_id(
                    "GC", [source_key]
                )
                result.at[index, "match_status"] = (
                    "REVIEW_REQUIRED"
                )
                result.at[index, "match_group_id"] = review_group_id

    # Remove internal normalization columns from the published result.
    internal_columns = [
        "_normalized_email",
        "_normalized_first_name",
        "_normalized_last_name",
        "_normalized_dob",
    ]

    return result.drop(columns=internal_columns)


def build_identity_summary(resolved_customers):
    """Return useful identity-resolution metrics."""

    return {
        "input_customer_records": int(len(resolved_customers)),
        "golden_customers": int(
            resolved_customers["golden_customer_id"].nunique()
        ),
        "automatically_matched_records": int(
            (
                resolved_customers["match_status"]
                == "MATCHED_EMAIL_NAME_DOB"
            ).sum()
        ),
        "review_required_records": int(
            (
                resolved_customers["match_status"]
                == "REVIEW_REQUIRED"
            ).sum()
        ),
        "records_without_email": int(
            (
                resolved_customers["match_status"]
                == "NO_EMAIL_SINGLE"
            ).sum()
        ),
        "single_records": int(
            (
                resolved_customers["match_status"]
                == "SINGLE_RECORD"
            ).sum()
        ),
    }
