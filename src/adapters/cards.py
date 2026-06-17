from datetime import datetime

def map_card_v1(row: dict) -> dict:
    return {
        "payment_id": row["txn_ref"],
        "amount_cents": int(float(row["txn_amount"]) * 100) if row.get("txn_amount") else None,
        "currency": row.get("currency", "USD"),
        "status": str(row.get("status")).upper(),
        "payment_method": "CARD",
        "transaction_timestamp": row["datetime"], # Already ISO 8601
        "source_metadata": {
            "network": row.get("card_network"),
            "version": "v1"
        }
    }


def map_card_v2(row: dict) -> dict:
    return {
        "payment_id": row["charge_id"],
        "amount_cents": int(row["amount_cents"]), # Already in cents
        "currency": row.get("currency", "USD"),
        "status": str(row.get("state")).upper(),
        "payment_method": "CARD",
        "transaction_timestamp": datetime.fromtimestamp(int(row["created_at_ts"])).isoformat() + "Z",
        "source_metadata": {
            "network": row.get("network"),
            "version": "v2"
        }
    }
