from datetime import datetime, timezone
from schema.source_models import CardSourceV1, CardSourceV2

STATUS_MAP = {
    "succeeded": "COMPLETED",
    "failed": "FAILED",
    "pending": "PENDING",
    "success": "COMPLETED",
}


def map_card_v1(raw_row: dict) -> dict:
    src = CardSourceV1(**raw_row)
    return {
        "payment_id": src.txn_ref,
        "amount_cents": round(src.txn_amount * 100),
        "currency": src.currency,
        "status": STATUS_MAP[src.status],
        "payment_method": "CARD",
        "transaction_timestamp": src.datetime,
        "source_metadata": {
            "network": src.card_network,
            "version": "v1",
        },
    }


def map_card_v2(raw_row: dict) -> dict:
    src = CardSourceV2(**raw_row)
    return {
        "payment_id": src.charge_id,
        "amount_cents": src.amount_cents,
        "currency": src.currency,
        "status": STATUS_MAP[src.state.lower()],
        "payment_method": "CARD",
        "transaction_timestamp": datetime.fromtimestamp(src.created_at_ts, tz=timezone.utc).isoformat(),
        "source_metadata": {
            "network": src.network,
            "version": "v2",
        },
    }
