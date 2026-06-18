import pytest
from datetime import datetime

from adapters.cards import map_card_v1
from adapters.transfers import map_transfer_v1


CARD_V1_ROW = {
    "txn_ref": "ch_abc123",
    "txn_amount": 10.0,
    "currency": "USD",
    "card_network": "VISA",
    "status": "succeeded",
    "datetime": "2026-01-01T00:00:00Z",
}

TRANSFER_V1_ROW = {
    "transfer_id": "TRX-123456",
    "value": 500.0,
    "sender_routing": "123456789",
    "sender_acct": "12345678",
    "receiver_routing": "987654321",
    "receiver_acct": "87654321",
    "type": "ACH",
    "cleared_date": "03/20/2026",  # date-only — squad doesn't send time, defaults to 00:00:00
    "state": "COMPLETED",
}


# Test 1
def test_card_v1_status_normalizes_succeeded_to_completed():
    """'succeeded' from the Cards squad must map to 'COMPLETED' in canonical vocabulary.

    Currently FAILS — map_card_v1 does .upper() which produces 'SUCCEEDED',
    not a valid canonical status. A STATUS_MAP is needed in the adapter.
    """
    result = map_card_v1(CARD_V1_ROW)
    assert result["status"] == "COMPLETED"


# Test 4
def test_transfer_v1_timestamp_parses_to_valid_datetime():
    """transfer_v1 cleared_date (MM/DD/YYYY, date-only) must produce a valid ISO 8601 string.

    Squad sends dates without time — adapter parses with '%m/%d/%Y' and defaults to midnight.
    """
    result = map_transfer_v1(TRANSFER_V1_ROW)
    parsed = datetime.fromisoformat(result["transaction_timestamp"].replace("Z", ""))
    assert parsed.year == 2026
    assert parsed.month == 3
    assert parsed.day == 20
    assert parsed.hour == 0    # no time in source — defaults to midnight
    assert parsed.minute == 0
