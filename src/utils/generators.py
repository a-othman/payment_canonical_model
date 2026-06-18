import pandas as pd
import random
import uuid
from datetime import datetime, timedelta
from pathlib import Path
import os 

def random_date(start, end):
    delta = end - start
    int_delta = (delta.days * 24 * 60 * 60) + delta.seconds
    return start + timedelta(seconds=random.randrange(int_delta))

start_date = datetime(2026, 1, 1)
end_date = datetime(2026, 6, 17)

# --- V1 FUNCTIONS (Standard Data with mixed-in errors) ---

def generate_card_v1(num_records=50, filename='card_v1.csv'):
    data = []
    for i in range(num_records):
        rec = {
            'txn_ref': f"ch_{uuid.uuid4().hex[:10]}",
            'txn_amount': round(random.uniform(5.0, 500.0), 2),
            'currency': 'USD',
            'card_network': random.choice(['VISA', 'MASTERCARD', 'AMEX']),
            'status': random.choice(['succeeded', 'failed', 'pending']),
            'datetime': random_date(start_date, end_date).strftime('%Y-%m-%dT%H:%M:%SZ')
        }
        # Inject 2 intentional errors
        if i == 5: rec['txn_amount'] = "N/A"             # Type error
        if i == 12: rec['status'] = "UNKNOWN_STATE"      # Enum error
        data.append(rec)
    pd.DataFrame(data).to_csv(filename, index=False)
    print(f"Generated {filename}")

def generate_transfer_v1(num_records=50, filename='transfer_v1.csv'):
    data = []
    for i in range(num_records):
        rec = {
            'transfer_id': f"TRX-{random.randint(100000, 999999)}",
            'value': round(random.uniform(100.0, 10000.0), 2),
            'sender_routing': f"S_{random.randint(100000000, 999999999)}",
            'sender_acct': f"S_{random.randint(10000000, 99999999)}",
            'receiver_routing': f"R_{random.randint(100000000, 999999999)}",
            'receiver_acct': f"R_{random.randint(10000000, 99999999)}",
            'type': random.choice(['ACH', 'WIRE']),
            'cleared_date': random_date(start_date, end_date).strftime('%m/%d/%Y'),
            'state': random.choice(['COMPLETED', 'PENDING', 'FAILED'])
        }
        # Inject 2 intentional errors
        if i == 8: rec['transfer_id'] = None             # Missing required ID
        if i == 15: rec['value'] = -500.0                # Logical error (negative transfer)
        data.append(rec)
    pd.DataFrame(data).to_csv(filename, index=False)
    print(f"Generated {filename}")

def generate_bill_v1(num_records=50, filename='bill_v1.csv'):
    data = []
    billers = [('City Water', 'WTR_001'), ('National Electric', 'ELE_044')]
    for i in range(num_records):
        b = random.choice(billers)
        rec = {
            'payment_id': f"BP_{random.randint(1000, 9999)}",
            'biller_name': b[0],
            'biller_id': b[1],
            'customer_account_no': f"ACCT-{random.randint(100, 999)}",
            'amount_paid': round(random.uniform(20.0, 300.0), 2),
            'payment_date': random_date(start_date, end_date).strftime('%Y-%m-%d'),
            'confirmation_number': f"CONF-{random.randint(100000, 999999)}",
            'status': 'COMPLETED',
        }
        # Inject 2 intentional errors
        if i == 3: rec['payment_date'] = "06-15-2026"    # Format error (not YYYY-MM-DD)
        if i == 10: rec['amount_paid'] = "FREE"          # Type error
        data.append(rec)
    pd.DataFrame(data).to_csv(filename, index=False)
    print(f"Generated {filename}")


def generate_card_v2(num_records=50, filename='card_v2.csv'):
    data = []
    for _ in range(num_records):
        dt = random_date(start_date, end_date)
        amt = round(random.uniform(5.0, 500.0), 2)
        data.append({
            'charge_id': f"ch_v2_{uuid.uuid4().hex[:12]}",   # Renamed
            'amount_cents': int(amt * 100),                  # Float -> Int
            'currency': 'USD',
            'network': random.choice(['VISA', 'MASTERCARD', 'AMEX']), # Renamed
            'state': random.choice(['SUCCESS', 'FAILED']),   # Enum change
            'created_at_ts': int(dt.timestamp())             # ISO -> UNIX Int
        })
    pd.DataFrame(data).to_csv(filename, index=False)
    print(f"Generated {filename}")

def generate_transfer_v2(num_records=50, filename='transfer_v2.csv'):
    data = []
    for _ in range(num_records):
        dt = random_date(start_date, end_date)
        amt = round(random.uniform(100.0, 10000.0), 2)
        data.append({
            'trx_ref': f"TRX-V2-{random.randint(100000, 999999)}",   # Renamed
            'amount_cents': int(amt * 100),                          # Float -> Int
            'sender_iban': f"US{random.randint(10,99)}BOFA{random.randint(1000000,9999999)}",     # Routing/Acct merged
            'receiver_iban': f"US{random.randint(10,99)}CHAS{random.randint(1000000,9999999)}",   # Routing/Acct merged
            'payment_method': random.choice(['ACH', 'WIRE']),        # Renamed
            'cleared_at': dt.strftime('%Y-%m-%dT%H:%M:%SZ'),         # MM/DD/YYYY -> ISO 8601
            'status': random.choice(['COMPLETED', 'PENDING'])        # Renamed
        })
    pd.DataFrame(data).to_csv(filename, index=False)
    print(f"Generated {filename}")

def generate_bill_v2(num_records=50, filename='bill_v2.csv'):
    data = []
    billers = [('City Water', 'WTR_001'), ('National Electric', 'ELE_044')]
    for _ in range(num_records):
        b = random.choice(billers)
        dt = random_date(start_date, end_date)
        amt = round(random.uniform(20.0, 300.0), 2)
        data.append({
            'bill_ref': f"INV_{random.randint(10000, 99999)}",   # Renamed
            'biller_code': b[1],                                 # Dropped Biller Name (Normalization)
            'account_number': f"ACCT-{random.randint(100, 999)}",# Renamed
            'total_cents': int(amt * 100),                       # Float -> Int
            'paid_at_ts': int(dt.timestamp()),                   # Date -> UNIX Int
            'status': random.choice(['COMPLETED', 'PENDING', 'FAILED']),
        })
    pd.DataFrame(data).to_csv(filename, index=False)
    print(f"Generated {filename}")


def generate_data():
    base_path = Path(__file__).parent.parent.parent / "data/raw"
    os.makedirs(base_path, exist_ok=True)
    generate_card_v1(filename=f'{base_path}/card_v1.csv')
    generate_transfer_v1(filename=f'{base_path}/transfer_v1.csv')
    generate_bill_v1(filename= f'{base_path}/bill_v1.csv')
    generate_card_v2(filename= f'{base_path}/card_v2.csv')
    generate_transfer_v2(filename= f'{base_path}/transfer_v2.csv')
    generate_bill_v2(filename= f'{base_path}/bill_v2.csv')
