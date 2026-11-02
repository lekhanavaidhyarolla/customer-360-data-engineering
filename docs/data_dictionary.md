# Customer 360 Data Engineering Pipeline — Data Dictionary

## 1. Overview

This document describes the source datasets, intermediate datasets, unified Customer 360 output, row-level data lineage, validation metadata, and publishing formats used by the pipeline.

The pipeline integrates customer, account, order, and interaction data from multiple source systems into a unified customer view.

## 2. Source Datasets

### 2.1 customers.csv

| Column | Description |
|---|---|
| customer_source_id | Customer identifier from the source system. |
| source_system | Originating customer system (CRM or ERP). |
| first_name | Customer's first name. |
| last_name | Customer's last name. |
| email | Customer email address. |
| phone | Customer phone number. |
| date_of_birth | Customer date of birth. |
| address | Customer address. |
| updated_at | Source record update timestamp. |

### 2.2 accounts.csv

| Column | Description |
|---|---|
| account_id | Unique account identifier. |
| customer_source_id | Customer reference from the source system. |
| source_system | Originating account system. |
| account_type | Type of account. |
| account_status | Current account status. |
| balance | Account balance. |
| opened_at | Account opening timestamp. |

### 2.3 orders.csv

| Column | Description |
|---|---|
| order_id | Unique order identifier. |
| customer_source_id | Customer reference from the source system. |
| source_system | Originating order system. |
| order_date | Date of the order. |
| product | Ordered product. |
| quantity | Number of units ordered. |
| amount | Order amount. |
| order_status | Current order status. |

### 2.4 interactions.csv

| Column | Description |
|---|---|
| interaction_id | Unique interaction identifier. |
| customer_source_id | Customer reference from the source system. |
| source_system | Originating interaction system. |
| interaction_type | Type of customer interaction. |
| channel | Communication channel. |
| interaction_date | Date of interaction. |
| description | Interaction description. |
| resolution_status | Current resolution status. |

## 3. Validation and Quarantine

Source records are checked for:

- Required columns and mandatory values.
- Duplicate primary keys.
- Invalid email and phone formats.
- Invalid date values.
- Numeric constraints, including nonnegative balances and amounts and positive quantities.
- Dataset-specific allowed values.

Invalid records are separated into quarantine datasets with validation error details. Validation reports record input, valid, and quarantined record counts.

Missing customer email is permitted by validation. Identity resolution handles such records conservatively rather than automatically matching them using incomplete information.

## 4. Identity Resolution

The identity-resolution stage assigns a deterministic `golden_customer_id` to each resolved customer identity.

| Field | Description |
|---|---|
| golden_customer_id | Deterministic identifier for a resolved customer identity. |
| match_status | Outcome of the identity-resolution process. |
| match_group_id | Identifier associated with a candidate matching group. |

Match statuses include:

- `SINGLE_RECORD`
- `NO_EMAIL_SINGLE`
- `MATCHED_EMAIL_NAME_DOB`
- `REVIEW_REQUIRED`

Records sharing a normalized email are automatically merged only when first name, last name, and date of birth are complete and consistent across the candidate records.

Records with uncertain identity matches are kept separate and flagged for review.

## 5. Intermediate Datasets

### 5.1 customers_resolved.csv

Contains validated customer records with resolved identity information and implementation-generated metadata.

Additional fields include:

- `source_file`
- `ingested_at`
- `source_record_id`
- `source_row_number`
- `source_file_sha256`
- `golden_customer_id`
- `match_status`
- `match_group_id`

### 5.2 accounts_linked.csv

Contains validated account records successfully linked to a golden customer.

Additional fields include:

- `source_file`
- `ingested_at`
- `source_record_id`
- `source_row_number`
- `source_file_sha256`
- `golden_customer_id`

### 5.3 orders_linked.csv

Contains validated order records successfully linked to a golden customer, together with source provenance metadata.

### 5.4 interactions_linked.csv

Contains validated interaction records successfully linked to a golden customer, together with source provenance metadata.

The child datasets also retain their original source attributes and relevant validation metadata.

## 6. Customer 360 Output

The `customer_360.csv` dataset contains one row per golden customer and 20 columns.

| Column | Description |
|---|---|
| golden_customer_id | Unique resolved customer identifier. |
| first_name | Selected customer first name. |
| last_name | Selected customer last name. |
| email | Customer email. |
| phone | Customer phone number. |
| date_of_birth | Customer date of birth. |
| address | Customer address. |
| source_systems | Source systems contributing customer records. |
| source_customer_ids | Original customer identifiers represented in the golden record. |
| source_record_count | Number of source customer records represented. |
| identity_match_status | Identity-resolution status. |
| identity_review_required | Indicates whether manual identity review is needed. |
| account_count | Number of linked accounts. |
| total_account_balance | Aggregated account balance. |
| order_count | Number of linked orders. |
| total_order_amount | Aggregated order amount. |
| total_quantity | Total ordered quantity. |
| latest_order_date | Most recent linked order date. |
| interaction_count | Number of linked interactions. |
| latest_interaction_date | Most recent linked interaction date. |

Customer attributes use the pipeline's source-priority rules, with CRM preferred and ERP used as a fallback.

Account, order, and interaction metrics are aggregated from successfully linked child records.

## 7. Data Lineage and Provenance

The pipeline provides both customer-level lineage and row-level lineage.

### 7.1 Customer-level lineage

The `customer_360_lineage.csv` dataset provides one lineage summary per golden customer.

It contains:

- `golden_customer_id`
- `source_systems`
- `source_customer_ids`
- `source_record_count`
- `identity_match_status`
- `identity_review_required`
- `account_count`
- `order_count`
- `interaction_count`

This makes the contributing source customer identities and their aggregated relationships traceable.

### 7.2 Row-level lineage datasets

The pipeline generates the following row-level lineage outputs:

| Dataset | Description |
|---|---|
| `customer_record_lineage.csv` | Lineage for validated customer records after identity resolution. |
| `accounts_record_lineage.csv` | Lineage for account records, including linked and relationship-quarantined records. |
| `orders_record_lineage.csv` | Lineage for order records, including linked and relationship-quarantined records. |
| `interactions_record_lineage.csv` | Lineage for interaction records, including linked and relationship-quarantined records. |
| `quarantine_lineage.csv` | Consolidated lineage view of validation and relationship quarantine records. |

Standard lineage fields include:

| Column | Description |
|---|---|
| dataset_name | Name of the source dataset. |
| source_record_id | Deterministic identifier generated for an ingested source row. |
| source_row_number | Original row number within the source file. |
| source_file | Name of the source file. |
| source_file_sha256 | SHA-256 checksum of the source file. |
| ingested_at | Ingestion timestamp. |
| source_primary_key | Primary key of the source record. |
| golden_customer_id | Resolved customer identifier, when available. |
| lineage_status | Processing or relationship outcome. |
| match_status | Identity-resolution status, when applicable. |
| quarantine_reason | Reason for quarantine, when applicable. |

Possible lineage statuses include:

- `LINKED_TO_GOLDEN_CUSTOMER`
- `IDENTITY_REVIEW_REQUIRED`
- `RELATIONSHIP_QUARANTINED`
- `VALIDATION_QUARANTINED`

The consolidated quarantine lineage output overlaps with relationship-quarantined rows in the individual child lineage datasets. It is a combined view and should not be added to the individual source lineage counts during reconciliation.

### 7.3 Provenance identifier behavior

`source_record_id` is generated using deterministic SHA-256-based provenance from the source file checksum and row position.

It provides traceability for records within a particular source-file version. It is not a persistent business identifier across file changes, row reordering, or incremental ingestion.

## 8. Quarantine and Relationship Handling

Invalid source records are separated during validation.

Child records that cannot be linked to a validated customer are quarantined with reasons including:

- `ORPHAN_CUSTOMER_REFERENCE`: The referenced customer identifier does not exist in the raw customer dataset.
- `CUSTOMER_NOT_VALIDATED`: The referenced customer exists in the raw customer dataset but did not pass customer validation.

Relationship-quarantined records remain represented in their respective row-level lineage datasets and in the consolidated quarantine lineage output.

These records are excluded from Customer 360 aggregates.

## 9. Implementation-Generated Metadata

| Field | Description |
|---|---|
| source_file | Source file associated with an ingested record. |
| ingested_at | Timestamp when the record was ingested. |
| source_record_id | Deterministic row-level provenance identifier. |
| source_row_number | Original source-file row position. |
| source_file_sha256 | SHA-256 checksum of the source file. |
| _validation_errors | Validation error information associated with a record. |
| golden_customer_id | Resolved customer identifier assigned during identity resolution or relationship linking. |

## 10. Publishing Formats

The pipeline publishes analytical datasets in:

- **CSV:** Intermediate, final, lineage, and reporting outputs.
- **Parquet:** Columnar storage for analytical workloads.
- **DuckDB:** Queryable analytical tables stored in `customer360.duckdb`.

The current publishing stage creates 11 datasets:

1. `customer_360`
2. `customers_resolved`
3. `accounts_linked`
4. `orders_linked`
5. `interactions_linked`
6. `customer_360_lineage`
7. `customer_record_lineage`
8. `accounts_record_lineage`
9. `orders_record_lineage`
10. `interactions_record_lineage`
11. `quarantine_lineage`

Each published dataset is available as a Parquet file and a DuckDB table.

## 11. Reports and Monitoring

The pipeline produces reports for:

- Data validation and quarantine metrics.
- Identity-resolution outcomes.
- Customer 360 aggregation and relationship metrics.
- Customer-level and row-level lineage.
- Publishing results.
- Pipeline execution history, stage status, duration, and retry information.

These reports support operational monitoring, reconciliation, and troubleshooting.