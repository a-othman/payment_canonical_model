import pytest
from datetime import datetime
from pydantic import ValidationError

from schema.canonical_model import CanonicalPayment
from schema.source_models import CardSourceV1


def _valid_canonical(**overrides) -> dict:
    base = {
        "payment_id": "test_001",
        "amount_cents": 1000,
        "currency": "USD",
        "status": "COMPLETED",
        "payment_method": "CARD",
        "transaction_timestamp": datetime(2026, 1, 1, 12, 0, 0),
    }
    return {**base, **overrides}


# Test 2
def test_canonical_rejects_negative_amount():
    """CanonicalPayment must reject amounts below zero — catches the transfer_v1 row 15 bug."""
    with pytest.raises(ValidationError) as exc_info:
        CanonicalPayment(**_valid_canonical(amount_cents=-500))
    assert "greater than zero" in str(exc_info.value)


# Test 5
def test_source_schema_rejects_non_numeric_amount():
    """CardSourceV1 must fail at the boundary when txn_amount is not a float — catches card_v1 row 5."""
    with pytest.raises(ValidationError):
        CardSourceV1(
            txn_ref="ch_abc123",
            txn_amount="N/A",
            card_network="VISA",
            status="succeeded",
            datetime="2026-01-01T00:00:00Z",
        )
