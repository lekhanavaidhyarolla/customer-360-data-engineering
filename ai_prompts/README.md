# AI Prompt History

## 1. Purpose

This folder documents the AI-assisted development process used for the Customer 360 Data Engineering Pipeline.

ChatGPT was used as a development assistant for technical planning, implementation guidance, debugging, testing, documentation, and project verification.

**Note:** This document is an organized summary of the major prompt topics and development activities. It is not a verbatim transcript of every conversation message.

## 2. AI-Assisted Development Areas

### 2.1 Project Understanding and Architecture

Prompt topics:
- Analyze the Customer 360 data engineering assignment requirements.
- Break the assignment into implementation stages.
- Design a modular Python pipeline for customer, account, order, and interaction data.
- Recommend a suitable project folder structure and technology stack.

### 2.2 Synthetic Data Generation

Prompt topics:
- Implement a configurable synthetic dataset generator using Python and Faker.
- Generate customer, account, order, and interaction datasets.
- Include duplicates, missing values, inconsistent formatting, and orphan references.
- Support large-scale dataset generation for performance testing.

### 2.3 Data Validation and Quarantine

Prompt topics:
- Implement reusable validation rules for each source dataset.
- Detect missing required values, duplicate primary keys, invalid email and phone formats, invalid dates, and invalid numeric values.
- Separate invalid records into quarantine outputs.
- Generate validation reports with record counts and error details.

### 2.4 Customer Identity Resolution

Prompt topics:
- Implement deterministic customer identity resolution.
- Normalize customer attributes before matching.
- Use email, name, and date of birth as matching evidence.
- Avoid automatically merging uncertain identities.
- Generate stable golden customer identifiers.

### 2.5 Customer 360 integration

Prompt topics:
- Build a unified Customer 360 dataset.
- Link account, order, and interaction records to resolved customers.
- Aggregate account balances, order amounts, quantities, and interaction counts.
- Quarantine records with unresolved customer references.

### 2.6 Data Lineage and Publishing

Prompt topics:
- Generate customer-level lineage information.
- Publish datasets in Parquet format.
- Store analytical datasets in DuckDB.
- Verify published table counts and output consistency.

### 2.7 Orchestration, Monitoring, and Reliability

Prompt topics:
- Build a pipeline orchestrator using Python subprocesses.
- Add execution logs, run IDs, stage timings, and run history.
- Implement retry handling for failed pipeline stages.
- Collect metrics from validation, identity resolution, integration, and publishing stages.

### 2.8 Automated Testing and Debugging

Prompt topics:
- Write pytest tests for validation, identity resolution, Customer 360 integration, lineage, and pipeline retries.
- Debug implementation errors and improve processing performance.
- Verify deterministic identifiers and expected pipeline behavior.
- Run the complete automated test suite.

### 2.9 Documentation and Final Verification

Prompt topics:
- Prepare the README and project setup instructions.
- Document the system architecture and data dictionary.
- Explain important design decisions and limitations.
- Verify generated dataset schemas, record counts, and publishing outputs.

## 3. AI Usage and Human Verification

AI assistance was used to support implementation and troubleshooting. The project code was executed and tested locally.

The developer reviewed the implementation, ran the pipeline, inspected generated datasets, and executed automated tests to verify the results.

AI-generated suggestions were not treated as proof of correctness. Final implementation behavior was checked through local execution and testing.

## 4. Development Tools

- AI assistant: ChatGPT
- Programming language: Python
- Development environment: Visual Studio Code
- Testing framework: pytest
- Data processing: pandas
- Analytical database: DuckDB
- Columnar storage: Parquet

## 5. Supporting Evidence

The development conversation contains the detailed implementation guidance, debugging discussions, and iterative changes used during development.

This document provides a categorized summary of those activities rather than claiming to be a complete verbatim prompt transcript.
