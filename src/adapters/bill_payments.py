from datetime import datetime, timezone
from schema.source_models import BillSourceV1, BillSourceV2


def map_bill_v1(raw_row: dict) -> dict:
    src = BillSourceV1(**raw_row)
    iso_date = datetime.strptime(src.payment_date, "%Y-%m-%d").replace(tzinfo=timezone.utc).isoformat()
    return {
        "payment_id": src.payment_id,
        "amount_cents": round(src.amount_paid * 100),
        "currency": "USD",
        "status": src.status,
        "payment_method": "BILL_PAY",
        "transaction_timestamp": iso_date,
        "source_metadata": {
            "biller_code": src.biller_id,
            "customer_account_no": src.customer_account_no,
            "version": "v1",
        },
    }


def map_bill_v2(raw_row: dict) -> dict:
    src = BillSourceV2(**raw_row)
    return {
        "payment_id": src.bill_ref,
        "amount_cents": src.total_cents,
        "currency": "USD",
        "status": src.status,
        "payment_method": "BILL_PAY",
        "transaction_timestamp": datetime.fromtimestamp(src.paid_at_ts, tz=timezone.utc).isoformat(),
        "source_metadata": {
            "biller_code": src.biller_code,
            "account_number": src.account_number,
            "version": "v2",
        },
    }
