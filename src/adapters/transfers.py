from datetime import datetime


def map_transfer_v1(row: dict) -> dict:
    # Convert MM/DD/YYYY to ISO 8601
    dt_str = row.get("cleared_date")
    iso_date = datetime.strptime(dt_str, "%m/%d/%Y").isoformat() + "Z" if dt_str else None

    return {
        "payment_id": row.get("transfer_id"),
        "amount_cents": int(float(row["value"]) * 100) if row.get("value") else None,
        "currency": "USD", # Implicit in source
        "status": str(row.get("state")).upper(),
        "payment_method": "TRANSFER",
        "transaction_timestamp": iso_date,
        "source_metadata": {
            "type": row.get("type"),
            "sender_routing": row.get("sender_routing"),
            "sender_acct": row.get("sender_acct"),
            "version": "v1"
        }
    }

def map_transfer_v2(row: dict) -> dict:
    return {
        "payment_id": row.get("trx_ref"),
        "amount_cents": int(row["amount_cents"]),
        "currency": "USD", 
        "status": str(row.get("status")).upper(),
        "payment_method": "TRANSFER",
        "transaction_timestamp": row["cleared_at"], # Now ISO 8601 in source
        "source_metadata": {
            "payment_method": row.get("payment_method"),
            "sender_iban": row.get("sender_iban"),
            "version": "v2"
        }
    }