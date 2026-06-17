from pydantic import BaseModel, Field, field_validator
from typing import Literal, Dict, Any, Optional
from datetime import datetime

class CanonicalPayment(BaseModel):
    # 1. Identity
    payment_id: str = Field(
        ..., 
        description="Unified ID. Maps to txn_ref, transfer_id, or payment_id"
    )
    internal_customer_id: Optional[str] = Field(
        default=None, 
        description="Nullable at ingestion. Resolved later via Identity job."
    )

    # 2. Financials
    amount_cents: int = Field(
        ..., 
        description="Stored in integer cents to prevent floating point errors."
    )
    currency: str = Field(
        default="USD", 
        min_length=3, 
        max_length=3
    )

    # 3. Lifecycle & Method
    status: Literal['COMPLETED', 'PENDING', 'FAILED'] = Field(
        ..., 
        description="Strict internal vocabulary for payment state."
    )
    payment_method: Literal['CARD', 'TRANSFER', 'BILL_PAY'] = Field(
        ..., 
        description="The source squad generating the event."
    )
    transaction_timestamp: datetime = Field(
        ..., 
        description="Standardized UTC timestamp of the event."
    )

    # 4. The Extensibility Envelope
    source_metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="JSON block containing routing numbers, card networks, biller IDs, etc."
    )

    # --- CUSTOM VALIDATION LOGIC ---
    
    @field_validator('amount_cents')
    @classmethod
    def amount_must_be_positive(cls, v):
        """Catches the intentional negative amount error in the Transfer v1 data."""
        if v < 0:
            raise ValueError('Payment amount must be greater than zero.')
        return v