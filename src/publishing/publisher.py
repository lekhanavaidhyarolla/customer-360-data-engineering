
import json
from pathlib import Path

import duckdb
import pandas as pd


def publish_datasets(
    project_root: Path,
    datasets: dict[str, pd.DataFrame],
) -> dict:
    processed_dir = project_root / "data" / "processed"
    published_dir = processed_dir / "parquet"
    outputs_dir = project_root / "outputs"

    published_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir.mkdir(parents=True, exist_ok=True)

    database_path = processed_dir / "customer360.duckdb"

    report = {
        "database": str(database_path.relative_to(project_root)),
        "datasets": {},
    }

    for dataset_name, dataframe in datasets.items():

        if not dataset_name.replace("_", "").isalnum():
            raise ValueError(
                f"Invalid dataset name: {dataset_name}"
            )

        parquet_path = published_dir / f"{dataset_name}.parquet"

        # Publish the Parquet file.
        dataframe.to_parquet(
            parquet_path,
            index=False,
            engine="pyarrow",
        )

        # Use an isolated connection for each dataset.
        connection = duckdb.connect(str(database_path))

        try:
            connection.register("incoming_dataframe", dataframe)

            connection.execute(
                f"""
                CREATE OR REPLACE TABLE "{dataset_name}" AS
                SELECT * FROM incoming_dataframe
                """
            ).fetchall()

            row_count = connection.execute(
                f'SELECT COUNT(*) FROM "{dataset_name}"'
            ).fetchone()[0]

        finally:
            # Closing releases the DataFrame registration.
            connection.close()

        report["datasets"][dataset_name] = {
            "row_count": int(row_count),
            "columns": list(dataframe.columns),
            "parquet_file": str(
                parquet_path.relative_to(project_root)
            ),
        }

        print(
            f"Published {dataset_name}: {row_count:,} rows"
        )

    report_path = outputs_dir / "publishing_report.json"

    with open(report_path, "w", encoding="utf-8") as file:
        json.dump(report, file, indent=4)

    print("\nPublishing completed.")
    print("DuckDB database:", database_path)
    print("Publishing report:", report_path)

    return report
