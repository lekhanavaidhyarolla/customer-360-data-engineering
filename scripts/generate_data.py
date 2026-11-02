
from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path
from datetime import date, timedelta

from faker import Faker


PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "data" / "sample"

fake = Faker("en_US")


def random_date(rng: random.Random, start_year: int = 2021) -> str:
    start = date(start_year, 1, 1)
    end = date(2026, 10, 31)
    days = (end - start).days
    return (start + timedelta(days=rng.randint(0, days))).isoformat()


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Created {path.name}: {len(rows):,} rows")


def generate_data(customer_count: int, seed: int) -> None:
    rng = random.Random(seed)
    Faker.seed(seed)
    fake.seed_instance(seed)

    customers = []
    accounts = []
    orders = []
    interactions = []

    customer_references = []

    # --------------------------------------------------
    # 1. CUSTOMER DATA
    # --------------------------------------------------
    for number in range(1, customer_count + 1):
        first_name = fake.first_name()
        last_name = fake.last_name()
        email = fake.email().lower()
        phone = fake.numerify(text="##########")
        birth_date = fake.date_of_birth(
            minimum_age=18, maximum_age=85
        ).isoformat()

        address = fake.address().replace("\n", ", ")

        primary_id = f"CRM-{number:07d}"

        customer = {
            "customer_source_id": primary_id,
            "source_system": "CRM",
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "phone": phone,
            "date_of_birth": birth_date,
            "address": address,
            "updated_at": random_date(rng),
        }

        customers.append(customer)
        customer_references.append(primary_id)

        # Introduce cross-system duplicate identities.
        if rng.random() < 0.15:
            duplicate_id = f"ERP-{number:07d}"

            duplicate = customer.copy()
            duplicate.update({
                "customer_source_id": duplicate_id,
                "source_system": "ERP",
                "email": email.upper() if rng.random() < 0.5 else email,
                "phone": phone if rng.random() < 0.7 else "",
                "updated_at": random_date(rng),
            })

            customers.append(duplicate)
            customer_references.append(duplicate_id)

        # Introduce missing and invalid customer attributes.
        if rng.random() < 0.03:
            customer["email"] = ""

        if rng.random() < 0.02:
            customer["phone"] = "INVALID-PHONE"

        if rng.random() < 0.02:
            customer["first_name"] = ""

        # Introduce exact duplicate source records.
        if rng.random() < 0.02:
            customers.append(customer.copy())

    # --------------------------------------------------
    # 2. ACCOUNT DATA
    # --------------------------------------------------
    account_number = 1

    for customer_id in customer_references:
        for _ in range(rng.randint(1, 2)):
            accounts.append({
                "account_id": f"ACC-{account_number:09d}",
                "customer_source_id": customer_id,
                "source_system": "CORE_BANKING",
                "account_type": rng.choice([
                    "SAVINGS", "CURRENT", "CREDIT"
                ]),
                "account_status": rng.choice([
                    "ACTIVE", "ACTIVE", "CLOSED", "SUSPENDED"
                ]),
                "balance": round(rng.uniform(100, 100000), 2),
                "opened_at": random_date(rng, 2018),
            })

            account_number += 1

    # --------------------------------------------------
    # 3. ORDER DATA
    # --------------------------------------------------
    order_number = 1

    products = [
        "Laptop",
        "Mobile Phone",
        "Headphones",
        "Smart Watch",
        "Tablet",
        "Keyboard",
        "Monitor",
    ]

    for customer_id in customer_references:
        for _ in range(rng.randint(2, 5)):
            orders.append({
                "order_id": f"ORD-{order_number:09d}",
                "customer_source_id": customer_id,
                "source_system": "E_COMMERCE",
                "order_date": random_date(rng),
                "product": rng.choice(products),
                "quantity": rng.randint(1, 5),
                "amount": round(rng.uniform(250, 150000), 2),
                "order_status": rng.choice([
                    "PLACED", "SHIPPED", "DELIVERED",
                    "CANCELLED", "RETURNED"
                ]),
            })

            order_number += 1

    # --------------------------------------------------
    # 4. CUSTOMER INTERACTION DATA
    # --------------------------------------------------
    interaction_number = 1

    for customer_id in customer_references:
        for _ in range(rng.randint(1, 4)):
            interactions.append({
                "interaction_id": f"INT-{interaction_number:09d}",
                "customer_source_id": customer_id,
                "source_system": "SUPPORT_CRM",
                "interaction_type": rng.choice([
                    "COMPLAINT", "QUERY", "FEEDBACK",
                    "PURCHASE_ENQUIRY", "SUPPORT_REQUEST"
                ]),
                "channel": rng.choice([
                    "EMAIL", "PHONE", "CHAT", "WEB"
                ]),
                "interaction_date": random_date(rng),
                "description": fake.sentence(nb_words=8),
                "resolution_status": rng.choice([
                    "OPEN", "IN_PROGRESS", "RESOLVED"
                ]),
            })

            interaction_number += 1

    # --------------------------------------------------
    # 5. INVALID REFERENCES FOR QUALITY TESTING
    # --------------------------------------------------
    if customer_references:
        accounts.append({
            "account_id": "ACC-ORPHAN-001",
            "customer_source_id": "UNKNOWN-CUSTOMER-001",
            "source_system": "CORE_BANKING",
            "account_type": "SAVINGS",
            "account_status": "ACTIVE",
            "balance": 5000.00,
            "opened_at": random_date(rng),
        })

        orders.append({
            "order_id": "ORD-ORPHAN-001",
            "customer_source_id": "UNKNOWN-CUSTOMER-002",
            "source_system": "E_COMMERCE",
            "order_date": random_date(rng),
            "product": "Laptop",
            "quantity": 1,
            "amount": 50000.00,
            "order_status": "PLACED",
        })

        interactions.append({
            "interaction_id": "INT-ORPHAN-001",
            "customer_source_id": "UNKNOWN-CUSTOMER-003",
            "source_system": "SUPPORT_CRM",
            "interaction_type": "COMPLAINT",
            "channel": "EMAIL",
            "interaction_date": random_date(rng),
            "description": "Reference to unknown customer",
            "resolution_status": "OPEN",
        })

    # --------------------------------------------------
    # 6. WRITE DATASETS
    # --------------------------------------------------
    write_csv(
        OUTPUT_DIR / "customers.csv",
        customers,
        [
            "customer_source_id", "source_system",
            "first_name", "last_name", "email", "phone",
            "date_of_birth", "address", "updated_at",
        ],
    )

    write_csv(
        OUTPUT_DIR / "accounts.csv",
        accounts,
        [
            "account_id", "customer_source_id", "source_system",
            "account_type", "account_status", "balance",
            "opened_at",
        ],
    )

    write_csv(
        OUTPUT_DIR / "orders.csv",
        orders,
        [
            "order_id", "customer_source_id", "source_system",
            "order_date", "product", "quantity", "amount",
            "order_status",
        ],
    )

    write_csv(
        OUTPUT_DIR / "interactions.csv",
        interactions,
        [
            "interaction_id", "customer_source_id", "source_system",
            "interaction_type", "channel", "interaction_date",
            "description", "resolution_status",
        ],
    )

    total_rows = (
        len(customers)
        + len(accounts)
        + len(orders)
        + len(interactions)
    )

    print("\nDATA GENERATION COMPLETED")
    print(f"Requested base customers: {customer_count:,}")
    print(f"Total rows across all datasets: {total_rows:,}")
    print(f"Output directory: {OUTPUT_DIR}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate synthetic Customer 360 source datasets."
    )

    parser.add_argument(
        "--customers",
        type=int,
        default=1000,
        help="Number of base customers to generate (default: 1000).",
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible data (default: 42).",
    )

    args = parser.parse_args()

    if args.customers < 1:
        parser.error("--customers must be at least 1")

    generate_data(args.customers, args.seed)


if __name__ == "__main__":
    main()
