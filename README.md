# Unified Payment Pipeline

A local prototype for a Unified Payment Data Pipeline. It ingests disparate CSV data from three independent product squads (Cards, Transfers, Bill Payments), validates it against strict Pydantic data contracts, and unifies everything into a single canonical Parquet schema for downstream analytics.

---

## Architecture: Two-Layer Validation

Every row passes through two validation layers before it reaches the canonical model:

```
Raw CSV row
    │
    ▼
Source Model (e.g. CardSourceV1)     ← Layer 1: is this valid squad data?
    │                                   catches type errors, enum violations,
    │                                   missing required fields
    ▼
Adapter (e.g. map_card_v1)           ← translation layer: squad vocab → canonical vocab
    │                                   STATUS_MAP, timestamp normalization, unit conversion
    ▼
CanonicalPayment                     ← Layer 2: does this meet internal business rules?
    │                                   positive amount_cents, valid status/payment_method enums
    ▼
Parquet output / Dead Letter Queue
```

---

## Canonical Schema

All three payment sources write into one `CanonicalPayment` model (`src/schema/canonical_model.py`):

| Field | Type | Notes |
|---|---|---|
| `payment_id` | `str` | Unified ID — maps from `txn_ref`, `transfer_id`, `payment_id`, etc. |
| `internal_customer_id` | `str \| None` | Always `None` at ingestion. Populated by a downstream identity-resolution job — not all payment providers supply a customer identifier |
| `amount_cents` | `int` | Integer cents — eliminates floating-point rounding errors |
| `currency` | `str` | 3-letter ISO-4217 code, defaults to `USD` |
| `status` | `Literal['COMPLETED', 'PENDING', 'FAILED']` | Canonical internal vocabulary |
| `payment_method` | `Literal['CARD', 'TRANSFER', 'BILL_PAY']` | Source squad |
| `transaction_timestamp` | `datetime` | Standardized UTC timestamp |
| `source_metadata` | `dict` | Flexible JSON envelope for squad-specific fields (routing numbers, card networks, biller IDs, IBANs) |

---

## Source Contracts

Each squad's raw format is modelled in `src/schema/source_models.py` as a typed Pydantic model. Status/state fields use `Literal` types to enforce each squad's exact vocabulary at the boundary — before any transformation runs.

| Source Model | Status vocabulary |
|---|---|
| `CardSourceV1` | `"succeeded" \| "failed" \| "pending"` |
| `CardSourceV2` | `"SUCCESS" \| "FAILED"` |
| `TransferSourceV1` | `"COMPLETED" \| "PENDING" \| "FAILED"` |
| `TransferSourceV2` | `"COMPLETED" \| "PENDING"` |

The adapter's `STATUS_MAP` then translates squad vocabulary into the canonical `COMPLETED / PENDING / FAILED` set.

---

## Project Structure

```
mal/
├── src/
│   ├── pipeline.py             # Entry point — runs the full ETL
│   ├── adapters/
│   │   ├── cards.py            # map_card_v1, map_card_v2 (includes STATUS_MAP)
│   │   ├── transfers.py        # map_transfer_v1, map_transfer_v2
│   │   └── bill_payments.py    # map_bill_v1, map_bill_v2
│   ├── schema/
│   │   ├── canonical_model.py  # CanonicalPayment Pydantic model + validators
│   │   └── source_models.py    # Typed source contracts per squad and version
│   └── utils/
│       └── generators.py       # Synthetic data generator (6 CSV files)
├── sql/
│   └── queries.py              # DuckDB analytics queries against Parquet output
├── tests/
│   ├── test_schema.py          # CanonicalPayment and source model validation rules
│   ├── test_adapters.py        # Adapter mapping and status/timestamp normalization
│   └── test_pipeline.py        # End-to-end pipeline integration
├── data/
│   ├── raw/                    # Generated input CSVs (written by generators)
│   └── output/                 # Pipeline outputs (Parquet, CSV, DLQ JSON)
├── conftest.py                 # Root pytest config — adds src/ to Python path
└── requirements.txt
```

---

## Prerequisites & Setup

Python 3.13 required.

```bash
# 1. Clone and enter the project
git clone <repo-url>
cd mal

# 2. Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate       # macOS / Linux
# .venv\Scripts\activate        # Windows

# 3. Install dependencies
pip install -r requirements.txt
```

---

## Running the Pipeline

```bash
python src/pipeline.py
```

This single command does everything in sequence:

1. **Generates synthetic data** — writes 6 CSV files (50 rows each) to `data/raw/`
2. **Routes each file** to the correct versioned adapter via filename (`card_v1.csv` → `map_card_v1`, etc.)
3. **Validates each row** through the source contract model, then `CanonicalPayment`
4. **Writes valid records** to `data/output/canonical_payments.parquet`
5. **Writes failed records** to `data/output/dead_letter_queue.json`

**Run without regenerating data** (use existing CSVs):

```bash
cd src
python -c "from pipeline import run_pipeline; run_pipeline(generate_data_flag=False)"
```

---

## Running Analytics

After the pipeline has produced `data/output/canonical_payments.parquet`:

```bash
python sql/queries.py
```

This runs four DuckDB queries directly against the Parquet file:

| Query | What it shows |
|---|---|
| **Query 0** | Total transaction count across all sources |
| **Query 1** | Total settled revenue (USD) grouped by payment method — only `COMPLETED` records |
| **Query 2** | Card network extraction from `source_metadata` JSON envelope using DuckDB's `->>'key'` operator |
| **Query 3** | DLQ failure breakdown — failure count by source file and error type |

Example output for Query 1:

```
┌────────────────┬────────────────────┬───────────────────┐
│ payment_method │ total_transactions │ total_revenue_usd │
│    BILL_PAY    │        48          │      8241.32      │
│    TRANSFER    │        44          │    189302.11      │
│      CARD      │        41          │      9823.55      │
└────────────────┴────────────────────┴───────────────────┘
```

---

## Running Tests

```bash
python -m pytest tests/ -v
```

Five tests covering the critical pipeline guarantees:

| Test | File | What it verifies |
|---|---|---|
| `test_canonical_rejects_negative_amount` | `test_schema.py` | `CanonicalPayment` raises `ValidationError` for `amount_cents < 0` — catches the intentional `value = -500` in `transfer_v1.csv` |
| `test_source_schema_rejects_non_numeric_amount` | `test_schema.py` | `CardSourceV1` rejects `txn_amount = "N/A"` at the source boundary before any mapping runs |
| `test_pipeline_catches_bad_rows_in_dlq_without_crashing` | `test_pipeline.py` | Full pipeline run produces valid records AND DLQ entries — intentional bad rows are caught, not swallowed silently |
| `test_card_v1_status_normalizes_succeeded_to_completed` | `test_adapters.py` | `"succeeded"` from the Cards squad maps to `"COMPLETED"` in canonical vocabulary via `STATUS_MAP` |
| `test_transfer_v1_timestamp_parses_to_valid_datetime` | `test_adapters.py` | `transfer_v1` `cleared_date` (`MM/DD/YYYY`, date-only) parses to a valid ISO 8601 datetime — time defaults to `00:00:00` |

Expected output:

```
tests/test_adapters.py::test_card_v1_status_normalizes_succeeded_to_completed PASSED
tests/test_adapters.py::test_transfer_v1_timestamp_parses_to_valid_datetime   PASSED
tests/test_pipeline.py::test_pipeline_catches_bad_rows_in_dlq_without_crashing PASSED
tests/test_schema.py::test_canonical_rejects_negative_amount                   PASSED
tests/test_schema.py::test_source_schema_rejects_non_numeric_amount            PASSED
5 passed in 0.56s
```

---

## Data Generation

The generator (`src/utils/generators.py`) produces 6 CSV files with **intentional errors injected** to demonstrate the Dead Letter Queue:

| File | Squad | Injected errors |
|---|---|---|
| `card_v1.csv` | Cards v1 | Row 5: `txn_amount = "N/A"` (type error); Row 12: `status = "UNKNOWN_STATE"` (enum violation) |
| `transfer_v1.csv` | Transfers v1 | Row 8: `transfer_id = None` (missing required ID); Row 15: `value = -500.0` (negative amount) |
| `bill_v1.csv` | Bill Payments v1 | Row 3: `payment_date = "06-15-2026"` (wrong date format); Row 10: `amount_paid = "FREE"` (type error) |
| `card_v2.csv` | Cards v2 | Clean — no injected errors |
| `transfer_v2.csv` | Transfers v2 | Clean — no injected errors |
| `bill_v2.csv` | Bill Payments v2 | Clean — no injected errors |

> Bill payment status is hardcoded to `COMPLETED` in the adapter — this models a real-world scenario where bill payments are processed as nightly batch jobs and only settled transactions are exported.

---

## Schema Versioning: v1 → v2

Each squad independently evolved their schema. The pipeline handles both versions simultaneously. The **version router** in `pipeline.py` inspects the filename and dispatches to the correct adapter:

```
card_v1.csv   →  map_card_v1()   →  CardSourceV1   →  CanonicalPayment
card_v2.csv   →  map_card_v2()   →  CardSourceV2   →  CanonicalPayment
```

Key v1 → v2 differences handled by each adapter:

| Change | v1 | v2 |
|---|---|---|
| Field rename (Cards) | `txn_ref`, `card_network` | `charge_id`, `network` |
| Amount type (Cards) | `txn_amount: float` → multiply × 100 | `amount_cents: int` → use directly |
| Timestamp format (Cards) | ISO 8601 string | UNIX integer → `datetime.fromtimestamp()` |
| Routing (Transfers) | Separate `sender_routing` + `sender_acct` | Merged `sender_iban` |
| Date format (Transfers) | `MM/DD/YYYY` (date-only) → `strptime`, time defaults to midnight | ISO 8601 string → use directly |
| Field rename (Bills) | `payment_id`, `biller_id`, `amount_paid` | `bill_ref`, `biller_code`, `total_cents` |
| Timestamp format (Bills) | `YYYY-MM-DD` (date-only) → `strptime`, time defaults to midnight | UNIX integer → `datetime.fromtimestamp()` |

---

## Validation & Dead Letter Queue

Failures at either validation layer are written to `data/output/dead_letter_queue.json` without stopping the pipeline:

```json
{
    "file": "transfer_v1.csv",
    "row_index": 15,
    "error_type": "SchemaValidationError",
    "error_details": "...",
    "raw_data": { "transfer_id": "TRX-123", "value": -500.0, ... }
}
```

Two error types are captured:

| Error type | Cause |
|---|---|
| `SchemaValidationError` | Pydantic validation failure — bad enum value, negative amount, wrong type at source or canonical model |
| `AdapterMappingError` | Crash inside the adapter — e.g. unparseable timestamp, null required field |

---

## Output Files

| Path | Format | Contents |
|---|---|---|
| `data/raw/*.csv` | CSV | 6 generated input files, 50 rows each |
| `data/output/canonical_payments.parquet` | Parquet | Validated, unified canonical records |
| `data/output/dead_letter_queue.json` | JSON | All rows that failed validation, with full error details and original raw data |
