# AI Development Prompt Log

## 1. Purpose

This document records the AI-assisted development activities performed during the development of the Customer 360 Data Engineering Pipeline.

ChatGPT was used as a development assistant for project understanding, architecture planning, implementation guidance, debugging, testing, and documentation.

The entries below are reconstructed summaries of the development prompts and activities. They are not presented as verbatim historical messages where the original wording could not be recovered.

## 2. Prompt Record Format

Each entry includes:

- **AI Tool:** ChatGPT
- **Development Area:** The relevant project module or activity.
- **Prompt:** A reconstructed summary of the development request.
- **Purpose:** The intended development objective.
- **Verification:** How the resulting implementation was checked.

## 3. AI Development Prompt History

### 3.1 Project Understanding and Architecture

**AI Tool:** ChatGPT

**Development Area:** Project Architecture

**Prompt:**

[Reconstructed summary] Analyze the Customer 360 Data Engineering Pipeline assignment requirements. Help break the project into implementation stages, recommend a suitable technology stack, and design a modular Python project structure for processing customer, account, order, and interaction datasets.

**Purpose:**

Understand the assignment requirements and establish an implementation plan before developing the pipeline.

**Verification:**

Reviewed the project structure and confirmed that the implementation covered the major pipeline stages.

### 3.2 Synthetic Data Generation

**AI Tool:** ChatGPT

**Development Area:** Data Generation

**Prompt:**

[Reconstructed summary] Help implement a configurable synthetic data generator using Python and Faker to generate customer, account, order, and interaction datasets. Include duplicate records, missing values, inconsistent formatting, invalid values, and orphan references. Support different dataset sizes for performance testing.

**Purpose:**

Generate representative datasets for developing and testing the Customer 360 pipeline without using real customer information.

**Verification:**

Executed the data generation script and inspected the generated datasets, record counts, and sample records.

### 3.3 Data Validation and Quarantine

**AI Tool:** ChatGPT

**Development Area:** Data Validation

**Prompt:**

[Reconstructed summary] Help implement reusable validation rules for customer, account, order, and interaction datasets. Detect missing required values, duplicate identifiers, invalid email and phone formats, invalid dates, and invalid numeric values. Separate rejected records into quarantine outputs and generate validation reports.

**Purpose:**

Establish data quality controls and prevent invalid records from silently entering downstream processing.

**Verification:**

Executed the validation stage, inspected valid and quarantined records, reviewed validation reports, and ran the automated tests.

### 3.4 Customer Identity Resolution

**AI Tool:** ChatGPT

**Development Area:** Identity Resolution

**Prompt:**

[Reconstructed summary] Help implement deterministic customer identity resolution using normalized customer attributes, including email, name, and date of birth. Generate stable golden customer identifiers, automatically match sufficiently consistent records, and keep uncertain matches separate for review.

**Purpose:**

Identify duplicate customer records across source systems while avoiding unsafe automatic merges.

**Verification:**

Executed the identity-resolution module and checked golden customer identifiers, match statuses, identity summaries, and relevant pytest cases.

### 3.5 Customer 360 Integration

**AI Tool:** ChatGPT

**Development Area:** Customer 360 Transformation

**Prompt:**

[Reconstructed summary] Help build a unified Customer 360 dataset by linking customer accounts, orders, and interactions to resolved golden customer records. Aggregate account balances, order amounts, quantities, and interaction information. Quarantine records with unresolved customer references.

**Purpose:**

Create a consolidated customer-level view containing information from the different source datasets.

**Verification:**

Executed the transformation stage and inspected customer-level aggregates, linked records, relationship quarantines, and generated output datasets.

### 3.6 Data Provenance and Lineage

**AI Tool:** ChatGPT

**Development Area:** Data Lineage

**Prompt:**

[Reconstructed summary] Help implement source-file provenance and deterministic row-level identifiers. Generate customer-level and record-level lineage information that tracks source records, linked customer identifiers, match statuses, and quarantine reasons.

**Purpose:**

Improve data traceability and make it possible to understand where processed records originated.

**Verification:**

Reviewed the generated lineage datasets and reports. Executed provenance and lineage tests and checked source-to-lineage record reconciliation.

### 3.7 Data Publishing

**AI Tool:** ChatGPT

**Development Area:** Data Publishing

**Prompt:**

[Reconstructed summary] Help publish the processed Customer 360 datasets and lineage outputs in Parquet format and store the analytical datasets in DuckDB. Generate publishing reports and verify that the published datasets are readable and consistent.

**Purpose:**

Provide efficient columnar storage and an analytical database for accessing the processed data.

**Verification:**

Executed the publishing stage, verified all expected Parquet datasets, and reconciled DuckDB and Parquet row counts.

### 3.8 Pipeline Orchestration and Monitoring

**AI Tool:** ChatGPT

**Development Area:** Monitoring and Orchestration

**Prompt:**

[Reconstructed summary] Help implement a Python pipeline orchestrator that executes the project stages in sequence. Add pipeline run identifiers, execution logs, stage timings, retry handling, failure reporting, and persistent run history.

**Purpose:**

Make pipeline execution manageable, observable, and more resilient to stage failures.

**Verification:**

Executed the complete pipeline and reviewed stage statuses, execution timings, logs, run history, and retry-related tests.

### 3.9 Automated Testing and Debugging

**AI Tool:** ChatGPT

**Development Area:** Testing and Debugging

**Prompt:**

[Reconstructed summary] Help develop pytest coverage for data validation, identity resolution, Customer 360 transformations, provenance, lineage, and pipeline retry handling. Investigate identified implementation defects and suggest targeted corrections without unnecessarily changing working functionality.

**Purpose:**

Improve implementation reliability and verify that individual modules behave as expected.

**Verification:**

Compiled the Python modules, executed the complete pytest suite, and verified the pipeline through local execution.

**Latest verification result:** 33 tests passed.

### 3.10 Documentation and Final Verification

**AI Tool:** ChatGPT

**Development Area:** Documentation and Verification

**Prompt:**

[Reconstructed summary] Help prepare project documentation, including the README, architecture documentation, data dictionary, design decisions, setup instructions, execution instructions, testing instructions, and final verification procedures.

**Purpose:**

Make the project understandable, reproducible, and suitable for technical review and submission.

**Verification:**

Reviewed the documentation and executed the database reconciliation, Parquet verification, and data-quality validation scripts.

**Latest verification results:**

- DuckDB and Parquet reconciliation: 11 of 11 datasets passed.
- Parquet dataset verification: 11 of 11 datasets passed.
- Data-quality checks: 18 passed, 0 failures.

## 4. AI Usage and Human Verification

ChatGPT was used as a development assistant throughout the project for technical planning, code guidance, debugging, testing suggestions, and documentation support.

AI-generated suggestions were not treated as proof of correctness. The implementation was executed and checked locally.

The developer reviewed the code, executed the pipeline, inspected generated datasets and reports, and ran automated tests and verification scripts.

The final implementation and its limitations should be understood and explained by the developer during technical evaluation.

## 5. Development Tools and Technologies

| Tool / Technology | Purpose |
|---|---|
| ChatGPT | AI-assisted development and debugging |
| Python | Pipeline implementation |
| Visual Studio Code | Development environment |
| pandas | Data processing and transformation |
| Faker | Synthetic data generation |
| DuckDB | Analytical database |
| Parquet | Columnar data storage |
| PyArrow | Parquet support |
| pytest | Automated testing |
| Git and GitHub | Version control and project submission |

## 6. Verification Evidence

The following results were observed during local project verification:

| Verification | Result |
|---|---:|
| Automated tests | 33 passed |
| DuckDB–Parquet reconciliation | 11/11 passed |
| Parquet verification | 11/11 passed |
| Data-quality checks | 18 passed |
| Data-quality failures | 0 |

These results describe the verified project run and should not be interpreted as a guarantee for every possible input dataset or execution environment.

## 7. Limitations and Transparency

- The prompt entries in this document are reconstructed summaries, not a complete verbatim transcript.
- AI responses are not reproduced in full.
- AI assistance supported development, but local execution and verification were used to assess implementation behavior.
- Verification results apply to the datasets and environment used during the recorded project runs.
- The project limitations and future improvements are documented separately in the design decisions and README files.

## 8. Supporting Documentation

Related project documentation:

- `README.md` — Project overview, setup, execution, and verification instructions.
- `docs/architecture.md` — Pipeline architecture and component descriptions.
- `docs/data_dictionary.md` — Dataset fields and data definitions.
- `docs/design_decisions.md` — Design choices, trade-offs, and limitations.
- `ai_prompts/README.md` — Summary of AI-assisted development activities.

---

**Document status:** AI-assisted development activity log  
**Project:** Customer 360 Data Engineering Pipeline