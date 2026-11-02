
import json
import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.transformation.identity_resolution import (
    resolve_customer_identities,
    build_identity_summary,
)


def main():
    input_path = PROJECT_ROOT / "data/processed/customers_valid.csv"
    output_path = PROJECT_ROOT / "data/processed/customers_resolved.csv"
    report_path = PROJECT_ROOT / "outputs/identity_resolution_report.json"

    customers = pd.read_csv(input_path)

    resolved = resolve_customer_identities(customers)
    summary = build_identity_summary(resolved)

    resolved.to_csv(output_path, index=False)

    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=4)

    print("\nCUSTOMER IDENTITY RESOLUTION")
    print("=" * 45)

    for metric, value in summary.items():
        print(f"{metric}: {value}")

    print("\nMATCH STATUS BREAKDOWN")
    print(resolved["match_status"].value_counts().to_string())

    print(f"\nResolved data saved to: {output_path}")
    print(f"Summary saved to: {report_path}")


if __name__ == "__main__":
    main()
