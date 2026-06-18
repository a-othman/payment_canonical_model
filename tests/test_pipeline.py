import pytest
from pipeline import run_pipeline


# Test 3
def test_pipeline_catches_bad_rows_in_dlq_without_crashing():
    """Full pipeline run must produce valid records AND catch intentional errors in the DLQ.

    The raw CSVs contain 2 injected errors each (type errors, enum errors,
    negative amounts, missing IDs). None of them should crash the pipeline —
    all must land in the dead-letter queue.
    """
    valid, dlq = run_pipeline(generate_data_flag=False)

    assert len(valid) > 0, "Pipeline produced no valid records"
    assert len(dlq) > 0, "No DLQ entries — intentional bad rows were not caught"

    error_types = {entry["error_type"] for entry in dlq}
    assert error_types <= {"SchemaValidationError", "AdapterMappingError"}, (
        f"Unexpected error types in DLQ: {error_types}"
    )
