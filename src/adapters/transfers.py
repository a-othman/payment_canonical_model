from datetime import datetime
from schema.source_models import TransferSourceV1, TransferSourceV2


def map_transfer_v1(raw_row: dict) -> dict:
    src = TransferSourceV1(**raw_row)
    iso_date = datetime.strptime(src.cleared_date, "%m/%d/%Y").isoformat() + "Z"
    return {
        "payment_id": src.transfer_id,
        "amount_cents": int(src.value * 100),
        "currency": "USD",
        "status": src.state,
        "payment_method": "TRANSFER",
        "transaction_timestamp": iso_date,
        "source_metadata": {
            "type": src.transfer_type,
            "sender_routing": src.sender_routing,
            "sender_acct": src.sender_acct,
            "version": "v1",
        },
    }


def map_transfer_v2(raw_row: dict) -> dict:
    src = TransferSourceV2(**raw_row)
    return {
        "payment_id": src.trx_ref,
        "amount_cents": src.amount_cents,
        "currency": "USD",
        "status": src.status,
        "payment_method": "TRANSFER",
        "transaction_timestamp": src.cleared_at,
        "source_metadata": {
            "type": src.payment_method,
            "sender_iban": src.sender_iban,
            "version": "v2",
        },
    }
