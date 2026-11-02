
"""Run dynamic data-quality and lineage reconciliation checks."""

from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATABASE_PATH = PROJECT_ROOT / "data" / "processed" / "customer360.duckdb"

CHECKS = [
    (
        "Customer 360 golden IDs are unique and non-null",
        """
        SELECT COUNT(*) = COUNT(DISTINCT golden_customer_id)
               AND COUNT(golden_customer_id) = COUNT(*)
        FROM customer_360
        """,
    ),
    (
        "Customer source-record IDs are unique and non-null",
        """
        SELECT COUNT(*) = COUNT(DISTINCT source_record_id)
               AND COUNT(source_record_id) = COUNT(*)
        FROM customer_record_lineage
        """,
    ),
    (
        "Account source-record IDs are unique and non-null",
        """
        SELECT COUNT(*) = COUNT(DISTINCT source_record_id)
               AND COUNT(source_record_id) = COUNT(*)
        FROM accounts_record_lineage
        """,
    ),
    (
        "Order source-record IDs are unique and non-null",
        """
        SELECT COUNT(*) = COUNT(DISTINCT source_record_id)
               AND COUNT(source_record_id) = COUNT(*)
        FROM orders_record_lineage
        """,
    ),
    (
        "Interaction source-record IDs are unique and non-null",
        """
        SELECT COUNT(*) = COUNT(DISTINCT source_record_id)
               AND COUNT(source_record_id) = COUNT(*)
        FROM interactions_record_lineage
        """,
    ),
    (
        "Quarantine source-record IDs are unique and non-null",
        """
        SELECT COUNT(*) = COUNT(DISTINCT source_record_id)
               AND COUNT(source_record_id) = COUNT(*)
        FROM quarantine_lineage
        """,
    ),
    (
        "Linked accounts have golden customer IDs",
        """
        SELECT COUNT(*) = 0
        FROM accounts_linked
        WHERE golden_customer_id IS NULL
        """,
    ),
    (
        "Linked orders have golden customer IDs",
        """
        SELECT COUNT(*) = 0
        FROM orders_linked
        WHERE golden_customer_id IS NULL
        """,
    ),
    (
        "Linked interactions have golden customer IDs",
        """
        SELECT COUNT(*) = 0
        FROM interactions_linked
        WHERE golden_customer_id IS NULL
        """,
    ),
    (
        "Account relationship quarantines have reasons",
        """
        SELECT COUNT(*) = 0
        FROM accounts_record_lineage
        WHERE lineage_status = 'RELATIONSHIP_QUARANTINED'
          AND (
              quarantine_reason IS NULL
              OR TRIM(CAST(quarantine_reason AS VARCHAR)) = ''
          )
        """,
    ),
    (
        "Order relationship quarantines have reasons",
        """
        SELECT COUNT(*) = 0
        FROM orders_record_lineage
        WHERE lineage_status = 'RELATIONSHIP_QUARANTINED'
          AND (
              quarantine_reason IS NULL
              OR TRIM(CAST(quarantine_reason AS VARCHAR)) = ''
          )
        """,
    ),
    (
        "Interaction relationship quarantines have reasons",
        """
        SELECT COUNT(*) = 0
        FROM interactions_record_lineage
        WHERE lineage_status = 'RELATIONSHIP_QUARANTINED'
          AND (
              quarantine_reason IS NULL
              OR TRIM(CAST(quarantine_reason AS VARCHAR)) = ''
          )
        """,
    ),
    (
        "Consolidated quarantine records have reasons",
        """
        SELECT COUNT(*) = 0
        FROM quarantine_lineage
        WHERE quarantine_reason IS NULL
           OR TRIM(CAST(quarantine_reason AS VARCHAR)) = ''
        """,
    ),
]

# Each lineage dataset is reconciled against its corresponding published
# dataset. Child lineage also includes relationship-quarantined records,
# so its expected count is linked records plus relationship quarantines.
RECONCILIATION = [
    (
        "Customers",
        """
        SELECT
            (SELECT COUNT(*) FROM customer_record_lineage)
            =
            (SELECT COUNT(*) FROM customers_resolved)
        """,
        """
        SELECT COUNT(*) FROM customer_record_lineage
        """,
        """
        SELECT COUNT(*) FROM customers_resolved
        """,
    ),
    (
        "Accounts",
        """
        SELECT
            (SELECT COUNT(*) FROM accounts_record_lineage)
            =
            (
                (SELECT COUNT(*) FROM accounts_linked)
                +
                (
                    SELECT COUNT(*)
                    FROM accounts_record_lineage
                    WHERE lineage_status = 'RELATIONSHIP_QUARANTINED'
                )
            )
        """,
        """
        SELECT COUNT(*) FROM accounts_record_lineage
        """,
        """
        SELECT
            (SELECT COUNT(*) FROM accounts_linked)
            +
            (
                SELECT COUNT(*)
                FROM accounts_record_lineage
                WHERE lineage_status = 'RELATIONSHIP_QUARANTINED'
            )
        """,
    ),
    (
        "Orders",
        """
        SELECT
            (SELECT COUNT(*) FROM orders_record_lineage)
            =
            (
                (SELECT COUNT(*) FROM orders_linked)
                +
                (
                    SELECT COUNT(*)
                    FROM orders_record_lineage
                    WHERE lineage_status = 'RELATIONSHIP_QUARANTINED'
                )
            )
        """,
        """
        SELECT COUNT(*) FROM orders_record_lineage
        """,
        """
        SELECT
            (SELECT COUNT(*) FROM orders_linked)
            +
            (
                SELECT COUNT(*)
                FROM orders_record_lineage
                WHERE lineage_status = 'RELATIONSHIP_QUARANTINED'
            )
        """,
    ),
    (
        "Interactions",
        """
        SELECT
            (SELECT COUNT(*) FROM interactions_record_lineage)
            =
            (
                (SELECT COUNT(*) FROM interactions_linked)
                +
                (
                    SELECT COUNT(*)
                    FROM interactions_record_lineage
                    WHERE lineage_status = 'RELATIONSHIP_QUARANTINED'
                )
            )
        """,
        """
        SELECT COUNT(*) FROM interactions_record_lineage
        """,
        """
        SELECT
            (SELECT COUNT(*) FROM interactions_linked)
            +
            (
                SELECT COUNT(*)
                FROM interactions_record_lineage
                WHERE lineage_status = 'RELATIONSHIP_QUARANTINED'
            )
        """,
    ),
]


def get_count(connection, query):
    """Return the integer result of a COUNT query."""
    return connection.execute(query).fetchone()[0]


def main():
    if not DATABASE_PATH.is_file():
        raise FileNotFoundError(
            f"DuckDB database not found: {DATABASE_PATH}"
        )

    connection = duckdb.connect(str(DATABASE_PATH), read_only=True)
    failures = []
    checks_executed = 0

    try:
        print("CUSTOMER 360 DATA QUALITY CHECKS")
        print("=" * 78)

        for description, query in CHECKS:
            result = connection.execute(query).fetchone()[0]
            passed = bool(result)
            checks_executed += 1

            print(f"{'PASS' if passed else 'FAIL':6} | {description}")

            if not passed:
                failures.append(description)

        print("\nSOURCE-TO-LINEAGE RECONCILIATION")
        print("=" * 78)

        for name, check_query, actual_query, expected_query in RECONCILIATION:
            passed = bool(connection.execute(check_query).fetchone()[0])
            actual = get_count(connection, actual_query)
            expected = get_count(connection, expected_query)
            checks_executed += 1

            print(
                f"{'PASS' if passed else 'FAIL':6} | "
                f"{name:16} | expected={expected:,} | actual={actual:,}"
            )

            if not passed:
                failures.append(f"{name} lineage row count")

        # The consolidated quarantine contains:
        # 1. Customer validation quarantines.
        # 2. Account relationship quarantines.
        # 3. Order relationship quarantines.
        # 4. Interaction relationship quarantines.
        #
        # Calculate the expected count from the current data rather
        # than relying on counts from a previous pipeline run.
        expected_quarantine = get_count(
            connection,
            """
            SELECT
                (
                    SELECT COUNT(*)
                    FROM quarantine_lineage
                    WHERE lineage_status = 'VALIDATION_QUARANTINED'
                )
                +
                (
                    SELECT COUNT(*)
                    FROM accounts_record_lineage
                    WHERE lineage_status = 'RELATIONSHIP_QUARANTINED'
                )
                +
                (
                    SELECT COUNT(*)
                    FROM orders_record_lineage
                    WHERE lineage_status = 'RELATIONSHIP_QUARANTINED'
                )
                +
                (
                    SELECT COUNT(*)
                    FROM interactions_record_lineage
                    WHERE lineage_status = 'RELATIONSHIP_QUARANTINED'
                )
            """,
        )

        actual_quarantine = get_count(
            connection,
            "SELECT COUNT(*) FROM quarantine_lineage",
        )

        quarantine_passed = actual_quarantine == expected_quarantine
        checks_executed += 1

        print(
            f"{'PASS' if quarantine_passed else 'FAIL':6} | "
            f"Combined quarantine | expected={expected_quarantine:,} | "
            f"actual={actual_quarantine:,}"
        )

        if not quarantine_passed:
            failures.append("Combined quarantine reconciliation")

        print("\nSUMMARY")
        print("=" * 78)
        print("Checks executed:", checks_executed)
        print("Failures:", len(failures))

        if failures:
            print("\nFailed checks:")
            for failure in failures:
                print("-", failure)

            raise SystemExit(1)

        print("\nSUCCESS: All data-quality checks passed.")

    finally:
        connection.close()


if __name__ == "__main__":
    main()
