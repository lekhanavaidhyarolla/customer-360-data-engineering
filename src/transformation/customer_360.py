
"""Build a unified Customer 360 view from validated source datasets."""

import pandas as pd


CUSTOMER_ATTRIBUTES = [
    "first_name",
    "last_name",
    "email",
    "phone",
    "date_of_birth",
    "address",
]


def build_customer_dimension(resolved_customers):
    """
    Create one customer dimension row per golden_customer_id.

    CRM is preferred for display attributes. ERP is used as a fallback
    when the preferred source has a missing value.
    """
    required = {
        "golden_customer_id",
        "source_system",
        "customer_source_id",
        *CUSTOMER_ATTRIBUTES,
        "match_status",
    }

    missing = required - set(resolved_customers.columns)

    if missing:
        raise ValueError(
            f"Missing customer columns: {sorted(missing)}"
        )

    customers = resolved_customers.copy()

    if customers["golden_customer_id"].isna().any():
        raise ValueError("A customer has no golden_customer_id.")

    # CRM has priority over ERP. Other systems come last.
    customers["_source_priority"] = (
        customers["source_system"]
        .astype(str)
        .str.upper()
        .map({"CRM": 0, "ERP": 1})
        .fillna(2)
    )

    # Sort before grouping so the first non-null attribute is
    # selected from the highest-priority source.
    customers = customers.sort_values(
        [
            "_source_priority",
            "source_system",
            "customer_source_id",
        ]
    )

    grouped = customers.groupby(
        "golden_customer_id",
        sort=True,
        observed=True,
    )

    # Select the first non-null attribute in source-priority order.
    dimension = grouped[CUSTOMER_ATTRIBUTES].first()

    # Preserve all contributing source systems and source IDs.
    dimension["source_systems"] = grouped["source_system"].agg(
        lambda values: "|".join(
            sorted(values.dropna().astype(str).unique())
        )
    )

    dimension["source_customer_ids"] = grouped[
        "customer_source_id"
    ].agg(
        lambda values: "|".join(
            sorted(values.dropna().astype(str).unique())
        )
    )

    dimension["source_record_count"] = grouped.size()

    dimension["identity_match_status"] = grouped[
        "match_status"
    ].agg(
        lambda values: "|".join(
            sorted(values.dropna().astype(str).unique())
        )
    )

    dimension["identity_review_required"] = grouped[
        "match_status"
    ].agg(
        lambda values: values.eq("REVIEW_REQUIRED").any()
    )

    dimension = dimension.reset_index()

    if dimension["golden_customer_id"].duplicated().any():
        raise ValueError(
            "Customer dimension contains duplicate golden IDs."
        )

    return dimension


def attach_golden_customer_ids(
    child_records,
    customer_lookup,
    dataset_name,
    raw_customer_ids,
):
    """
    Attach golden customer IDs to accounts, orders or interactions.

    customer_source_id identifies the referenced customer.

    The child dataset's source_system identifies the system that owns
    the child record. It is not used to identify the customer.

    Unmatched references are classified as:
    - ORPHAN_CUSTOMER_REFERENCE
    - CUSTOMER_NOT_VALIDATED
    """
    required = {"customer_source_id"}

    missing = required - set(child_records.columns)

    if missing:
        raise ValueError(
            f"{dataset_name}: missing columns {sorted(missing)}"
        )

    if customer_lookup["customer_source_id"].duplicated().any():
        raise ValueError(
            "Customer lookup contains duplicate source IDs."
        )

    # Work with copies so original inputs remain unchanged.
    child_records = child_records.copy()
    customer_lookup = customer_lookup.copy()

    # Normalize reference IDs to strings for consistent matching.
    child_records["customer_source_id"] = (
        child_records["customer_source_id"].astype(str)
    )

    customer_lookup["customer_source_id"] = (
        customer_lookup["customer_source_id"].astype(str)
    )

    raw_customer_ids = {
        str(value) for value in raw_customer_ids
    }

    enriched = child_records.merge(
        customer_lookup[
            [
                "customer_source_id",
                "golden_customer_id",
            ]
        ],
        on="customer_source_id",
        how="left",
        validate="many_to_one",
        indicator=True,
    )

    matched = enriched[
        enriched["_merge"] == "both"
    ].copy()

    unmatched = enriched[
        enriched["_merge"] == "left_only"
    ].copy()

    # Classify unmatched records without a Python row-by-row loop.
    is_orphan = ~unmatched["customer_source_id"].isin(
        raw_customer_ids
    )

    unmatched["quarantine_reason"] = "CUSTOMER_NOT_VALIDATED"
    unmatched.loc[
        is_orphan,
        "quarantine_reason",
    ] = "ORPHAN_CUSTOMER_REFERENCE"

    matched = matched.drop(columns=["_merge"])
    unmatched = unmatched.drop(columns=["_merge"])

    return matched, unmatched


def aggregate_accounts(accounts):
    """Aggregate account metrics by golden customer ID."""

    if accounts.empty:
        return pd.DataFrame(
            columns=[
                "golden_customer_id",
                "account_count",
                "total_account_balance",
            ]
        )

    accounts = accounts.copy()

    accounts["balance"] = pd.to_numeric(
        accounts["balance"],
        errors="coerce",
    )

    return (
        accounts.groupby("golden_customer_id")
        .agg(
            account_count=(
                "account_id",
                "nunique",
            ),
            total_account_balance=(
                "balance",
                lambda values: values.sum(min_count=1),
            ),
        )
        .reset_index()
    )


def aggregate_orders(orders):
    """Aggregate order metrics by golden customer ID."""

    if orders.empty:
        return pd.DataFrame(
            columns=[
                "golden_customer_id",
                "order_count",
                "total_order_amount",
                "total_quantity",
                "latest_order_date",
            ]
        )

    orders = orders.copy()

    orders["amount"] = pd.to_numeric(
        orders["amount"],
        errors="coerce",
    )

    orders["quantity"] = pd.to_numeric(
        orders["quantity"],
        errors="coerce",
    )

    orders["order_date"] = pd.to_datetime(
        orders["order_date"],
        errors="coerce",
    )

    return (
        orders.groupby("golden_customer_id")
        .agg(
            order_count=(
                "order_id",
                "nunique",
            ),
            total_order_amount=(
                "amount",
                lambda values: values.sum(min_count=1),
            ),
            total_quantity=(
                "quantity",
                "sum",
            ),
            latest_order_date=(
                "order_date",
                "max",
            ),
        )
        .reset_index()
    )


def aggregate_interactions(interactions):
    """Aggregate interaction metrics by golden customer ID."""

    if interactions.empty:
        return pd.DataFrame(
            columns=[
                "golden_customer_id",
                "interaction_count",
                "latest_interaction_date",
            ]
        )

    interactions = interactions.copy()

    interactions["interaction_date"] = pd.to_datetime(
        interactions["interaction_date"],
        errors="coerce",
    )

    return (
        interactions.groupby("golden_customer_id")
        .agg(
            interaction_count=(
                "interaction_id",
                "nunique",
            ),
            latest_interaction_date=(
                "interaction_date",
                "max",
            ),
        )
        .reset_index()
    )


def build_customer_360(
    resolved_customers,
    accounts,
    orders,
    interactions,
    raw_customer_ids,
):
    """
    Build the unified Customer 360 view.

    Returns:
        customer_360: One row per golden customer.
        matched: Linked account, order and interaction records.
        quarantine: Unmatched child records with quarantine reasons.
    """

    # 1. Build one customer dimension row per golden ID.
    dimension = build_customer_dimension(
        resolved_customers
    )

    # 2. Build source-customer-ID to golden-ID lookup.
    customer_lookup = resolved_customers[
        [
            "customer_source_id",
            "golden_customer_id",
        ]
    ].copy()

    raw_ids = {
        str(value) for value in raw_customer_ids
    }

    # 3. Link accounts to golden customers.
    matched_accounts, quarantined_accounts = (
        attach_golden_customer_ids(
            accounts,
            customer_lookup,
            "accounts",
            raw_ids,
        )
    )

    # 4. Link orders to golden customers.
    matched_orders, quarantined_orders = (
        attach_golden_customer_ids(
            orders,
            customer_lookup,
            "orders",
            raw_ids,
        )
    )

    # 5. Link interactions to golden customers.
    matched_interactions, quarantined_interactions = (
        attach_golden_customer_ids(
            interactions,
            customer_lookup,
            "interactions",
            raw_ids,
        )
    )

    # 6. Aggregate linked child records.
    account_summary = aggregate_accounts(
        matched_accounts
    )

    order_summary = aggregate_orders(
        matched_orders
    )

    interaction_summary = aggregate_interactions(
        matched_interactions
    )

    # 7. Combine everything into the Customer 360 view.
    customer_360 = (
        dimension
        .merge(
            account_summary,
            on="golden_customer_id",
            how="left",
            validate="one_to_one",
        )
        .merge(
            order_summary,
            on="golden_customer_id",
            how="left",
            validate="one_to_one",
        )
        .merge(
            interaction_summary,
            on="golden_customer_id",
            how="left",
            validate="one_to_one",
        )
    )

    # Customers without child records receive zero counts.
    count_columns = [
        "account_count",
        "order_count",
        "total_quantity",
        "interaction_count",
    ]

    for column in count_columns:
        customer_360[column] = (
            customer_360[column]
            .fillna(0)
            .astype("int64")
        )

    # No linked account/order amount is represented as zero.
    customer_360["total_account_balance"] = (
        customer_360["total_account_balance"]
        .fillna(0)
    )

    customer_360["total_order_amount"] = (
        customer_360["total_order_amount"]
        .fillna(0)
    )

    # 8. Enforce one row per golden customer.
    if customer_360["golden_customer_id"].duplicated().any():
        raise ValueError(
            "Customer 360 contains duplicate golden IDs."
        )

    # 9. Return linked records and quarantined records separately.
    matched = {
        "accounts": matched_accounts,
        "orders": matched_orders,
        "interactions": matched_interactions,
    }

    quarantine = {
        "accounts": quarantined_accounts,
        "orders": quarantined_orders,
        "interactions": quarantined_interactions,
    }

    return customer_360, matched, quarantine
