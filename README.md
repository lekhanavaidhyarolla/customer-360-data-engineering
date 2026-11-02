# Customer 360 Data Engineering Pipeline

A Python-based end-to-end data engineering pipeline that integrates customer, account, order, and interaction datasets into a unified Customer 360 view.

The project demonstrates synthetic data generation, data validation, deterministic identity resolution, relationship-level quarantine, source-record provenance, customer-level and row-level lineage, analytical transformations, and publishing to Parquet and DuckDB.

It also includes pipeline monitoring, execution history, configurable retries, automated tests, and data-quality reconciliation checks.

## Project Objectives

- Generate realistic synthetic datasets containing inconsistent and imperfect records.
- Validate incoming data using schema and data-quality rules.
- Quarantine invalid records instead of silently discarding them.
- Resolve customer identities across multiple source systems.
- Generate deterministic golden customer identifiers.
- Flag uncertain identity matches for manual review.
- Link accounts, orders, and interactions to golden customer identifiers.
- Build a consolidated Customer 360 dataset.
- Maintain source-record provenance and row-level lineage.
- Generate customer-level lineage and lineage reports.
- Publish analytical datasets in Parquet and DuckDB.
- Record pipeline execution metrics, logs, and run history.
- Support configurable stage retries and automated tests.
- Reconcile published datasets and verify data-quality rules.

## Architecture

```text
             Synthetic Data Generator
                       |
                       v
                Raw CSV Datasets
                       |
                       v
                Data Validation
                  /         \
                 v           v
          Valid Records   Validation
                            Quarantine
                 |
                 v
         Source Provenance
                 |
                 v
       Customer Identity Resolution
                 |
                 v
       Deterministic Golden IDs
                 |
                 v
         Customer 360 Transformation
            /       |        \
           v        v         v
        Accounts  Orders  Interactions
            \       |        /
             \      |       /
              v     v      v
          Relationship Validation
                  |
                  v
          Customer 360 Dataset
                  |
                  v
             Data Lineage
          /                 \
         v                   v
 Customer-Level          Row-Level
   Lineage                 Lineage
         \                   /
          \                 /
                   v
              Data Publishing
                /         \
               v           v
            Parquet      DuckDB
                \         /
                 v       v
           Quality Checks
                   |
                   v
          Monitoring and Logs
```

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Pipeline implementation and orchestration |
| Pandas | Data ingestion and transformation |
| DuckDB | Analytical database and SQL queries |
| PyArrow | Parquet data support |
| Faker | Synthetic data generation |
| Pytest | Automated testing |

## Input Datasets

The generator creates four CSV datasets.

| Dataset | Description |
|---|---|
| `customers.csv` | Customer identity and demographic information |
| `accounts.csv` | Customer account information |
| `orders.csv` | Customer orders and transaction information |
| `interactions.csv` | Customer support and communication interactions |

The synthetic data includes deliberately introduced data-quality issues, such as:

- Duplicate customer records.
- Inconsistent text casing and formatting.
- Missing email addresses and other attributes.
- Invalid phone numbers.
- Missing required customer attributes.
- Orphan customer references in child datasets.

The generator supports reproducible dataset creation using a configurable customer count and random seed.

## Main Pipeline Stages

### 1. Synthetic Data Generation

Generates reproducible customer, account, order, and interaction datasets using Faker.

The number of base customers and random seed can be configured through command-line arguments.

### 2. Data Validation

Validates incoming datasets using rules covering:

- Required columns and required values.
- Primary-key uniqueness.
- Email format.
- Phone number format.
- Numeric constraints.
- Date parsing and validation.
- Permitted categorical values.

Invalid records are separated into quarantine outputs with validation reasons.

Source provenance metadata includes source record identifiers, source row numbers, source file information, and SHA-256 file hashes.

### 3. Customer Identity Resolution

Normalizes customer attributes and uses email as a candidate matching key.

Automatic matching requires consistent and sufficiently complete name and date-of-birth information.

Identity outcomes include:

- `SINGLE_RECORD`
- `MATCHED_EMAIL_NAME_DOB`
- `REVIEW_REQUIRED`
- `NO_EMAIL_SINGLE`

Ambiguous records are not automatically merged. Records without email remain separate rather than being combined using uncertain evidence.

Golden customer identifiers are generated deterministically from source record keys.

### 4. Customer 360 Transformation

Builds one consolidated record per golden customer.

The transformation:

- Selects customer attributes using source-system priority.
- Aggregates account counts and balances.
- Aggregates order counts, amounts, quantities, and latest order dates.
- Aggregates interaction counts and latest interaction dates.
- Links child records to validated golden customer identifiers.
- Quarantines unresolved or invalid customer relationships.

Relationship quarantine reasons distinguish orphan customer references from references to customers that did not pass validation.

### 5. Data Lineage

The pipeline produces two complementary lineage levels.

**Customer-level lineage**

Records the contributing customer source identifiers, source systems, identity-resolution status, and source-record counts for each golden customer.

**Row-level lineage**

Tracks individual source records, including:

- Dataset name.
- Source record identifier.
- Source row number.
- Source file and SHA-256 hash.
- Ingestion timestamp.
- Source primary key.
- Golden customer identifier, when available.
- Lineage status.
- Identity match status.
- Quarantine reason, when applicable.

A consolidated quarantine lineage dataset brings together validation and relationship quarantine records.

### 6. Data Publishing

Publishes 11 datasets in two analytical formats:

- Parquet files for columnar storage.
- DuckDB tables for SQL-based analysis.

The published datasets include the Customer 360 view, resolved customers, linked child datasets, customer-level lineage, four row-level lineage datasets, and consolidated quarantine lineage.

### 7. Monitoring and Reliability

The pipeline records:

- Unique pipeline run identifiers.
- Stage execution statuses.
- UTC start and completion timestamps.
- Stage durations.
- Pipeline execution duration.
- Business metrics.
- Errors and retry attempts.
- Historical execution records.

Failed stages support configurable retries. Permanent failures are recorded for investigation.

## Project Structure

```text
Customer 360 Data Engineering Project/
|
|-- data/
|   |-- raw/
|   |-- processed/
|   |-- quarantine/
|   `-- sample/
|
|-- src/
|   |-- ingestion/
|   |-- validation/
|   |-- transformation/
|   |-- publishing/
|   `-- monitoring/
|
|-- scripts/
|   |-- generate_data.py
|   |-- validate_data.py
|   |-- resolve_identities.py
|   |-- build_customer_360.py
|   |-- publish_data.py
|   |-- verify_database.py
|   |-- verify_parquet.py
|   `-- run_quality_checks.py
|
|-- tests/
|-- docs/
|-- outputs/
|-- ai_prompts/
|
|-- run_pipeline.py
|-- requirements.txt
|-- .gitignore
`-- README.md
```

## Setup and Installation

### Prerequisites

- Python 3.10 or newer.
- Git.
- Windows, Linux, or macOS.

### 1. Clone the repository

```bash
git clone https://github.com/lekhanavaidhyarolla/customer-360-data-engineering.git
cd customer-360-data-engineering
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install -r requirements.txt
```

## Running the Pipeline

Run with the default dataset size:

```powershell
python .\run_pipeline.py
```

Generate data for 1,000 requested base customers:

```powershell
python .\run_pipeline.py --customers 1000 --seed 42
```

Generate data for 10,000 requested base customers:

```powershell
python .\run_pipeline.py --customers 10000 --seed 42
```

Generate data for 100,000 requested base customers:

```powershell
python .\run_pipeline.py --customers 100000 --seed 42
```

Configure retry behavior:

```powershell
python .\run_pipeline.py --customers 1000 --seed 42 --retries 2 --retry-delay 2
```

The retry count represents additional attempts after the initial attempt.

## Running Automated Tests

Run the complete test suite:

```powershell
python -m pytest -v
```

The current automated test suite contains **33 tests** covering:

- Customer 360 construction and aggregation.
- Relationship quarantine.
- Customer identity resolution.
- Deterministic identity generation.
- Customer-level lineage.
- Pipeline stage retries and failure handling.
- Source-record provenance.
- Input validation and invalid-record quarantine.

Latest verified result:

**33 passed in 4.02 seconds.**

## Data Quality and Publishing Verification

Run the DuckDB and Parquet reconciliation:

```powershell
python .\scripts\verify_database.py
```

This verifies that all 11 DuckDB tables have the same row counts as their corresponding Parquet files.

Verify that the Parquet datasets exist and are readable:

```powershell
python .\scripts\verify_parquet.py
```

Run data-quality and lineage checks:

```powershell
python .\scripts\run_quality_checks.py
```

The quality checks cover:

- Golden customer identifier uniqueness.
- Source-record identifier uniqueness and completeness.
- Valid golden customer identifiers on linked records.
- Quarantine reason completeness.
- Source-to-lineage reconciliation.
- Combined quarantine reconciliation.

The expected counts are derived from the current published data rather than hard-coded to one dataset size.

Latest verified results:

| Verification | Result |
|---|---:|
| DuckDB-to-Parquet table reconciliation | 11/11 passed |
| Parquet existence and readability | 11/11 passed |
| Data-quality and lineage checks | 18/18 passed |
| Automated tests | 33/33 passed |

## Main Outputs

| Output | Description |
|---|---|
| `data/processed/customer_360.csv` | Consolidated Customer 360 view |
| `data/processed/customers_resolved.csv` | Customer identity-resolution results |
| `data/processed/accounts_linked.csv` | Accounts linked to golden customers |
| `data/processed/orders_linked.csv` | Orders linked to golden customers |
| `data/processed/interactions_linked.csv` | Interactions linked to golden customers |
| `data/processed/parquet/` | Published Parquet datasets |
| `data/processed/customer360.duckdb` | DuckDB analytical database |
| `data/quarantine/` | Validation and relationship quarantine outputs |
| `outputs/validation_report.json` | Data validation metrics |
| `outputs/identity_resolution_report.json` | Identity-resolution metrics |
| `outputs/customer_360_lineage.csv` | Customer-level lineage |
| `outputs/lineage_report.json` | Lineage summary |
| `outputs/pipeline_run_history.json` | Historical pipeline execution records |
| `logs/pipeline.log` | Pipeline execution log |

The DuckDB database and Parquet directory contain the published Customer 360, resolved customer, linked dataset, lineage, and quarantine outputs.

## Verified Development Benchmarks

The following benchmarks were recorded using seed `42`.

These are observed execution times from the development environment, not hardware-independent performance guarantees.

### 1,000 requested base customers

| Metric | Result |
|---|---:|
| Requested base customers | 1,000 |
| Total generated rows across datasets | 9,846 |
| Validated rows | 9,769 |
| Validation-quarantined rows | 77 |
| Overall validation success rate | 99.22% |
| Customer records entering identity resolution | 1,095 |
| Golden customers | 954 |
| Automatically matched records | 282 |
| Review-required records | 7 |
| Published datasets | 11 |
| Observed pipeline runtime | 13.52 seconds |

### 10,000 requested base customers

| Metric | Result |
|---|---:|
| Requested base customers | 10,000 |
| Total generated rows across datasets | 98,556 |
| Validated rows | 97,748 |
| Validation-quarantined rows | 808 |
| Overall validation success rate | 99.18% |
| Customer records entering identity resolution | 10,969 |
| Golden customers | 9,594 |
| Automatically matched records | 2,750 |
| Review-required records | 414 |
| Published datasets | 11 |
| Observed pipeline runtime | 58.092 seconds |

### 100,000 requested base customers

| Metric | Result |
|---|---:|
| Requested base customers | 100,000 |
| Total generated rows across datasets | 979,734 |
| Validated rows | 971,776 |
| Validation-quarantined rows | 7,958 |
| Overall validation success rate | 99.19% |
| Customer records entering identity resolution | 109,103 |
| Golden customers | 98,457 |
| Automatically matched records | 21,292 |
| Review-required records | 24,440 |
| Published datasets | 11 |
| Observed pipeline runtime | 131.982 seconds |

The latest 100K integrated run completed all five pipeline stages successfully on their first attempts.

### Benchmark comparison

| Requested base customers | Total generated rows | Observed runtime |
|---:|---:|---:|
| 1,000 | 9,846 | 13.52 sec |
| 10,000 | 98,556 | 58.092 sec |
| 100,000 | 979,734 | 131.982 sec |

Execution times may vary with hardware, system load, storage performance, and environment configuration.

## Design Decisions

- **Conservative identity resolution:** Email identifies candidate matches, while name and date-of-birth consistency are required for automatic merging.
- **Deterministic identifiers:** Golden customer IDs are generated from stable source identifiers.
- **Source provenance:** Each source row receives a deterministic provenance identifier tied to its source file and row position.
- **Quarantine instead of silent deletion:** Invalid data and unresolved relationships are retained with reasons.
- **Separate identity and relationship processing:** Customer identity resolution occurs before linking child datasets.
- **Multiple lineage levels:** Customer-level lineage provides a consolidated view, while row-level lineage tracks individual source records.
- **Analytical publishing:** Parquet provides columnar storage, while DuckDB supports SQL-based analysis.
- **Execution monitoring:** Each pipeline run has a unique identifier and recorded stage results.
- **Dynamic reconciliation:** Verification scripts compare current outputs rather than relying on fixed benchmark row counts.

## Current Limitations

- Identity resolution uses deterministic rules rather than probabilistic or machine-learning entity resolution.
- Ambiguous identity matches require manual review; a manual review interface is not included.
- Provenance identifiers are deterministic for an unchanged source file and row ordering; they are not a persistent identity mechanism for arbitrary reordered incremental data.
- Column-level lineage is not implemented.
- Synthetic datasets are used; production source-system integrations are not included.
- Retry handling retries failed stages, but permanent errors still require investigation.
- Benchmark timings are environment-dependent.

## Future Improvements

- Add probabilistic identity matching and configurable confidence scores.
- Add a manual review workflow for ambiguous customer matches.
- Extend lineage to column-level transformations.
- Add incremental processing and change-data capture.
- Add persistent record identity across reordered source extracts.
- Add production database and source-system integrations.
- Add pipeline dashboards and performance visualizations.
- Extend performance benchmarking to larger datasets.

## Project Status

The current implementation includes:

- Synthetic data generation.
- Data validation and quarantine.
- Deterministic customer identity resolution.
- Customer 360 transformation.
- Source-record provenance.
- Customer-level and row-level lineage.
- Parquet and DuckDB publishing.
- Pipeline monitoring and retry handling.
- Automated tests and dynamic data-quality checks.

The latest integrated 100K run completed successfully, with all 11 datasets published. The 10K publishing reconciliation, all 18 data-quality checks, and all 33 automated tests have also passed.

This project uses synthetic data and demonstrates end-to-end data engineering concepts.