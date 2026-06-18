from pydantic import BaseModel, Field
from typing import Literal, Optional


class BaseCardSource(BaseModel):
    currency: Optional[str] = "USD"
    customer_id: Optional[str] = None  # nullable at ingestion; resolved via identity job


class BaseTransferSource(BaseModel):
    customer_id: Optional[str] = None


class BaseBillSource(BaseModel):
    customer_id: Optional[str] = None


# --- V1 SOURCE CONTRACTS ---

class CardSourceV1(BaseCardSource):
    txn_ref: str
    txn_amount: float
    card_network: str
    status: Literal["succeeded", "failed", "pending"]
    datetime: str


class TransferSourceV1(BaseTransferSource):
    transfer_id: str
    value: float
    sender_routing: str
    sender_acct: str
    receiver_routing: str
    receiver_acct: str
    transfer_type: str = Field(validation_alias="type")  # renamed — 'type' shadows Python built-in
    cleared_date: str
    state: Literal["COMPLETED", "PENDING", "FAILED"]


class BillSourceV1(BaseBillSource):
    payment_id: str
    biller_name: str
    biller_id: str
    customer_account_no: str
    amount_paid: float
    payment_date: str
    confirmation_number: str
    # status absent in v1 CSV — adapter hardcodes COMPLETED; needs CSV regen to use real status


# --- V2 SOURCE CONTRACTS ---

class CardSourceV2(BaseCardSource):
    charge_id: str
    amount_cents: int
    network: str
    state: Literal["SUCCESS", "FAILED"]
    created_at_ts: int


class TransferSourceV2(BaseTransferSource):
    trx_ref: str
    amount_cents: int
    sender_iban: str
    receiver_iban: str
    payment_method: Literal["ACH", "WIRE"]
    cleared_at: str
    status: Literal["COMPLETED", "PENDING"]


class BillSourceV2(BaseBillSource):
    bill_ref: str
    biller_code: str
    account_number: str
    total_cents: int
    paid_at_ts: int
    # status absent in v2 CSV — adapter hardcodes COMPLETED; needs CSV regen to use real status
