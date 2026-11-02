# Customer 360 Pipeline — Engineering Design Decisions

## 1. Purpose

This document records the major engineering decisions made while developing the Customer 360 Data Engineering Pipeline, including the reasoning, trade-offs, implementation behavior, and known limitations.

## 2. Synthetic Data Generation

**Decision:** Use Faker and a configurable random seed to generate synthetic datasets.

**Reasoning:**
- Avoid exposing real customer information.
- Reproduce data-quality scenarios consistently.
- Support small development runs and larger performance tests.
- Introduce realistic inconsistencies for validation and identity-resolution testing.

**Trade-off:** Synthetic data may not represent every complexity found in production systems.

## 3. CSV-Based Input

**Decision:** Use CSV files as the initial input format.

**Reasoning:**
- Easy to inspect and understand.
- Simple to generate and reproduce.
- Suitable for demonstrating ingestion and transformation workflows.

**Trade-off:** CSV is less suitable than streaming or database-based ingestion for high-frequency production workloads.

## 4. Data Validation and Quarantine

**Decision:** Separate valid records from invalid records and preserve rejected records with reasons.

**Reasoning:**
- Invalid records should not silently enter downstream transformations.
- Quarantine outputs support investigation and correction.
- Validation reports provide measurable data-quality information.

**Implementation:** Validation checks required fields and columns, duplicate primary keys, email and phone formats, dates, allowed values, and numeric constraints.

**Trade-off:** Quarantined records require a separate correction and reprocessing workflow, which is not currently automated.

## 5. Conservative Identity Resolution

**Decision:** Use normalized email as a candidate matching key and require consistent first name, last name, and date of birth before automatically merging multiple records.

**Reasoning:**
- Email alone may be shared or reused.
- Name and date-of-birth checks reduce the risk of incorrect merges.
- Incomplete or conflicting records should not be merged automatically.

**Implementation:** Records with uncertain identity matches receive separate golden customer IDs and are flagged with `REVIEW_REQUIRED`. Records without email are kept as separate identities.

**Trade-off:** Some genuine matches remain separate and require manual review.

## 6. Deterministic Golden Customer IDs

**Decision:** Generate golden customer identifiers deterministically using SHA-256 over stable source identity keys.

**Reasoning:**
- Repeatable identity results for the same source identities.
- No dependency on randomly generated identifiers.
- Easier comparison across repeat pipeline runs.

**Trade-off:** Changes to the underlying source identity keys can result in a different golden identifier. This approach does not provide a persistent identity registry for incremental source changes.

## 7. Missing Email Handling

**Decision:** Keep records without email as separate identities.

**Reasoning:**
- Avoid uncertain matching based on incomplete information.
- Prevent accidental merging of unrelated customers.
- Preserve records for future enrichment or manual review.

**Trade-off:** Duplicate customers without email may remain unresolved.

## 8. Source Attribute Selection

**Decision:** Prefer CRM attributes when available, with ERP fallback when constructing the consolidated customer dimension.

**Reasoning:**
- Establishes a consistent source-priority rule.
- Makes attribute selection predictable.
- Supports integration of multiple customer systems.

**Trade-off:** Source priority does not necessarily guarantee that the selected value is the most recently updated or most accurate value.

## 9. Relationship-Level Quarantine

**Decision:** Link child datasets to customers using source customer identifiers and separately quarantine unresolved relationships.

**Reasoning:**
- Customer validation and child relationship validation are distinct checks.
- Orphan references should be distinguishable from references to customers that failed validation.
- Valid customer records should not be lost because unrelated child records are invalid.

**Implementation:** Relationship failures are classified as `ORPHAN_CUSTOMER_REFERENCE` or `CUSTOMER_NOT_VALIDATED`.

**Trade-off:** Child records that cannot be linked are excluded from Customer 360 aggregates but remain represented in lineage and quarantine outputs.

## 10. Aggregated Customer 360 Model

**Decision:** Produce one consolidated row per golden customer, with aggregated account, order, and interaction metrics.

**Reasoning:**
- Provides a unified customer view.
- Avoids duplicating customer attributes for every child transaction.
- Supports downstream analytical queries.

**Trade-off:** Aggregated metrics do not replace detailed transaction-level analysis; linked child datasets are retained separately.

## 11. Data Provenance and Lineage

**Decision:** Maintain both customer-level lineage and row-level lineage.

**Reasoning:**
- Customer-level lineage explains which source customer records contribute to each golden customer.
- Row-level lineage provides traceability for individual source records.
- Source file checksums and row positions help identify the origin of ingested records.
- Quarantine lineage supports investigation of rejected records and unresolved relationships.

**Implementation:** The pipeline generates customer-level lineage and five row-level lineage outputs covering customer records, account records, order records, interaction records, and consolidated quarantine records.

The row-level provenance identifier is generated deterministically using the source file checksum and row position.

**Trade-off:** The current provenance identifier is specific to a source-file version and row position. It is not a persistent identifier across file changes or row reordering. Column-level lineage is not implemented.

## 12. Parquet and DuckDB Publishing

**Decision:** Publish analytical outputs in Parquet and DuckDB.

**Reasoning:**
- Parquet provides a columnar storage format.
- DuckDB enables local SQL-based analytical queries.
- Both formats are convenient for reproducible analytical workflows.

**Implementation:** Eleven datasets are published as Parquet files and DuckDB tables. Verification scripts compare the row counts between the two formats.

**Trade-off:** The current publishing implementation is local and does not include distributed storage or managed cloud infrastructure.

## 13. Pipeline Orchestration and Retries

**Decision:** Use a Python orchestration script with subprocess execution, stage monitoring, and configurable retries.

**Reasoning:**
- Keeps pipeline stages independently executable.
- Stops downstream processing when an upstream stage fails.
- Allows transient failures to be retried.
- Records execution status and duration.

**Implementation:** The orchestrator supports configurable retry counts and retry delays. Stage execution history records success or failure information.

**Trade-off:** Retries do not fix permanent errors. A failed stage must be safe to rerun. More advanced recovery, checkpointing, and distributed scheduling are future improvements.

## 14. Automated Testing and Data Quality

**Decision:** Use pytest and independent verification scripts to test the pipeline.

**Reasoning:**
- Protects core business rules against regressions.
- Verifies important edge cases.
- Checks reconciliation and publishing consistency.
- Makes future modifications safer.

**Current test status:** 33 automated pytest tests passed in the latest recorded test run.

**Data-quality status:** The latest recorded quality-check run passed all 18 checks. Separate DuckDB and Parquet verification scripts each passed all 11 dataset checks.

These counts describe the latest recorded successful runs and are not a measured percentage of code coverage.

## 15. Performance and Repeatability

**Decision:** Support configurable synthetic dataset sizes and seeded repeat runs.

**Reasoning:**
- Allows development with smaller datasets.
- Supports larger-volume integration testing.
- Helps compare business results across runs using the same seed and parameters.

**Recorded benchmark results:**

| Generated customer parameter | Total source rows | Pipeline duration |
|---:|---:|---:|
| 1,000 | 9,846 | 17.152 seconds |
| 10,000 | 98,556 | 58.092 seconds |
| 100,000 | 979,734 | 131.982 seconds |

The timings are observations from local development runs, not production performance guarantees.

Repeat runs with the same seed and parameters produced matching business-level record counts and identity-resolution results in the recorded tests. Runtime and ingestion timestamps naturally vary.

## 16. Known Limitations

- Identity matching is deterministic and rule-based.
- No manual identity review interface is currently implemented.
- No probabilistic entity-resolution model is included.
- No production source-system integrations are included.
- Column-level lineage is not implemented.
- Provenance identifiers depend on source file content and row position.
- Incremental processing and change-data capture are not implemented.
- The pipeline uses local file storage and a local analytical database.
- Quarantined records do not have an automated correction and replay workflow.
- Performance measurements are from a local development environment.

## 17. Future Engineering Improvements

- Introduce confidence-scored probabilistic identity matching.
- Build a manual identity review and merge workflow.
- Implement incremental ingestion and change-data capture.
- Add persistent identity and provenance registries.
- Extend lineage to column level.
- Add automated quarantine correction and reprocessing.
- Add a persistent orchestration and scheduling service.
- Benchmark on larger datasets and multiple hardware configurations.
- Add cloud-based storage and deployment options.
