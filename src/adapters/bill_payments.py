from datetime import datetime



def map_bill_v1(row: dict) -> dict:
    # Convert YYYY-MM-DD to ISO 8601
    dt_str = row.get("payment_date")
    iso_date = datetime.strptime(dt_str, "%Y-%m-%d").isoformat() + "Z" if dt_str else None

    return {
        "payment_id": row.get("payment_id"),
        "amount_cents": int(float(row["amount_paid"]) * 100) if row.get("amount_paid") else None,
        "currency": "USD", 
        "status": "COMPLETED", # Bills only export on success
        "payment_method": "BILL_PAY",
        "transaction_timestamp": iso_date,
        "source_metadata": {
            "biller_code": row.get("biller_id"),
            "customer_account_no": row.get("customer_account_no"),
            "version": "v1"
        }
    }


def map_bill_v2(row: dict) -> dict:
    return {
        "payment_id": row.get("bill_ref"),
        "amount_cents": int(row["total_cents"]),
        "currency": "USD", 
        "status": "COMPLETED", 
        "payment_method": "BILL_PAY",
        "transaction_timestamp": datetime.fromtimestamp(int(row["paid_at_ts"])).isoformat() + "Z",
        "source_metadata": {
            "biller_code": row.get("biller_code"),
            "account_number": row.get("account_number"),
            "version": "v2"
        }
    }