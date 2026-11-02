
"""Generate deterministic row-level source provenance metadata."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pandas as pd


def calculate_file_sha256(file_path: Path) -> str:
    """Calculate a SHA-256 checksum for a source file."""

    digest = hashlib.sha256()

    with Path(file_path).open("rb") as source_file:
        for chunk in iter(lambda: source_file.read(1024 * 1024), b""):
            digest.update(chunk)

    return digest.hexdigest()


def add_source_provenance(
    dataframe: pd.DataFrame,
    dataset_name: str,
    source_file: Path,
) -> pd.DataFrame:
    """
    Attach deterministic provenance identifiers to every source row.

    Row numbers are one-based data-record positions, excluding the
    CSV header. The file checksum makes identifiers specific to the
    exact source-file version.
    """

    if not dataset_name or not dataset_name.strip():
        raise ValueError("dataset_name must not be empty")

    source_file = Path(source_file)

    if not source_file.is_file():
        raise FileNotFoundError(source_file)

    result = dataframe.copy().reset_index(drop=True)

    file_checksum = calculate_file_sha256(source_file)
    row_numbers = range(1, len(result) + 1)

    record_ids = []

    for row_number in row_numbers:
        identifier_input = (
            f"{dataset_name}|"
            f"{source_file.name}|"
            f"{file_checksum}|"
            f"{row_number}"
        )

        record_hash = hashlib.sha256(
            identifier_input.encode("utf-8")
        ).hexdigest()[:24].upper()

        record_ids.append(f"SR_{record_hash}")

    result["source_record_id"] = record_ids
    result["source_row_number"] = list(row_numbers)
    result["source_file"] = source_file.name
    result["source_file_sha256"] = file_checksum

    return result
