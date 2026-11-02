
# Customer 360 Pipeline Architecture

## 1. Overview

The Customer 360 Data Engineering Pipeline integrates four related datasets into a unified customer view.

The pipeline is organized into sequential stages. Each stage consumes the outputs of the previous stage and produces data or reports for downstream processing.

## 2. High-Level Architecture

```text
                 Synthetic Data Generator
                           |
                           v
                    Four CSV Datasets
              /          |          \
         Customers    Accounts     Orders
                              \       /
                            Interactions
                           |
                           v
                    Data Validation
                     /          \
                    v            v
              Valid Records   Quarantine
                    |
                    v
             Identity Resolution
                    |
                    v
              Golden Customer IDs
                    |
                    v
             Customer 360 Builder
               /      |       \
              v       v        v
           Accounts Orders Interactions
                    |
                    v
              Lineage Generator
                    |
                    v
               Data Publisher
                /          \
               v            v
            Parquet       DuckDB
                    |
                    v
             Pipeline Monitoring
```

## 3. Processing Stages

### Stage 1: Synthetic Data Generation

**Input:** Customer count and random seed.

**Process:**
- Generate customer demographic records.
- Generate associated account records.
- Generate order records.
- Generate customer interaction records.
- Introduce controlled data-quality issues.

**Output:** Four CSV files under `data/sample/`.

### Stage 2: Data Validation

**Input:** Generated CSV datasets.

**Process:**
- Check required columns and values.
- Validate primary-key uniqueness.
- Validate email and phone formats.
- Check numeric and date constraints.
- Check permitted categorical values.

**Output:**
- Validated records in `data/processed/`.
- Invalid records in `data/quarantine/`.
- Validation metrics in `outputs/validation_report.json`.

### Stage 3: Customer Identity Resolution

**Input:** Validated customer records.

**Process:**
- Normalize customer attributes.
- Group candidate records using normalized email.
- Compare first name, last name, and date of birth.
- Generate deterministic golden customer IDs.
- Mark uncertain matches as `REVIEW_REQUIRED`.
- Keep records without email separate.

**Output:**
- `data/processed/customers_resolved.csv`
- `outputs/identity_resolution_report.json`

### Stage 4: Customer 360 Transformation

**Input:** Resolved customers and validated child datasets.

**Process:**
- Construct one customer dimension record per golden customer.
- Prefer CRM attributes when available, with ERP fallback.
- Link accounts, orders, and interactions using source customer identifiers.
- Aggregate account balances and counts.
- Aggregate order amounts, quantities, and dates.
- Aggregate interaction counts and latest dates.
- Quarantine unresolved child relationships.

**Output:**
- `data/processed/customer_360.csv`
- Linked child datasets.
- Relationship quarantine datasets.
- `outputs/customer_360_metrics.json`

### Stage 5: Lineage Generation

**Input:** Consolidated Customer 360 records.

**Process:**
- Record contributing source systems.
- Record contributing source customer identifiers.
- Record source record counts.
- Record identity match status and review flags.
- Record associated account, order, and interaction counts.

**Output:**
- `outputs/customer_360_lineage.csv`
- `outputs/lineage_report.json`

**Scope:** This implementation provides customer-level summary lineage. It does not claim complete transaction-level or column-level lineage.

### Stage 6: Data Publishing

**Input:** Customer 360 and linked datasets.

**Process:**
- Write datasets in Parquet format.
- Create corresponding DuckDB tables.
- Generate publishing metrics.

**Output:**
- `data/processed/parquet/`
- `data/processed/customer360.duckdb`
- `outputs/publishing_report.json`

### Stage 7: Monitoring

**Process:**
- Assign a unique ID to each pipeline run.
- Track stage start and completion.
- Record durations and failures.
- Retry failed stages according to configuration.
- Collect business metrics.
- Append execution records to historical run data.

**Output:**
- `logs/pipeline.log`
- `outputs/pipeline_run_history.json`

## 4. Technology Choices

| Technology | Architectural Role |
|---|---|
| Python | Pipeline orchestration and processing |
| Pandas | CSV ingestion and transformations |
| Faker | Synthetic data generation |
| DuckDB | Analytical SQL database |
| PyArrow | Parquet support |
| Pytest | Automated testing |

## 5. Data Flow and Storage

| Directory | Purpose |
|---|---|
| `data/sample/` | Generated input datasets |
| `data/raw/` | Raw ingestion storage |
| `data/processed/` | Validated and transformed outputs |
| `data/quarantine/` | Invalid records and unresolved relationships |
| `outputs/` | Reports, lineage, and run history |
| `logs/` | Pipeline execution logs |

## 6. Reliability Considerations

- Deterministic identifiers support repeatable identity resolution.
- Fixed random seeds support reproducible synthetic datasets.
- Invalid records are preserved in quarantine.
- Retry handling allows transient stage failures to be retried.
- Run history provides an execution audit trail.
- Automated tests verify key transformation and failure-handling behavior.
