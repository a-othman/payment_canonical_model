from datetime import datetime
from schema.source_models import BillSourceV1, BillSourceV2


def map_bill_v1(raw_row: dict) -> dict:
    src = BillSourceV1(**raw_row)
    iso_date = datetime.strptime(src.payment_date, "%Y-%m-%d %H:%M:%S").isoformat() + "Z"
    return {
        "payment_id": src.payment_id,
        "amount_cents": int(src.amount_paid * 100),
        "currency": "USD",
        "status": "COMPLETED",
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
        "status": "COMPLETED",
        "payment_method": "BILL_PAY",
        "transaction_timestamp": datetime.fromtimestamp(src.paid_at_ts).isoformat() + "Z",
        "source_metadata": {
            "biller_code": src.biller_code,
            "account_number": src.account_number,
            "version": "v2",
        },
    }
