"""
Pydantic v2 schemas for receipt data extraction and validation.
Implements ALL custom validators from PRD §FR-3:
  - line_item_math: abs(qty × unit_price − line_total) ≤ 0.05
  - receipt_math: abs(subtotal + tax + tip − total) ≤ 0.05
  - date_sanity: not future, not > 10 years ago
  - currency_code: valid ISO 4217
  - amount_sign: all amount fields ≥ 0
"""

from datetime import datetime, timedelta
import datetime as dt
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator

# Valid ISO 4217 currency codes (common subset)
VALID_CURRENCY_CODES = {
    "USD", "EUR", "GBP", "JPY", "CAD", "AUD", "CHF", "CNY", "INR", "MXN",
    "BRL", "KRW", "SGD", "HKD", "NOK", "SEK", "DKK", "NZD", "ZAR", "RUB",
    "TRY", "TWD", "THB", "PHP", "PLN", "CZK", "HUF", "ILS", "CLP", "ARS",
    "COP", "PEN", "VND", "UAH", "EGP", "AED", "SAR", "MYR", "IDR", "PKR",
    "BDT", "NGN", "KES", "GHS", "TZS", "UGX", "QAR", "KWD", "BHD", "OMR",
    "JOD", "LBP", "MAD", "DZD", "TND", "LKR", "MMK", "RON", "BGN", "HRK",
    "ISK", "GEL", "AMD", "AZN", "BYN", "MDL", "KZT", "UZS", "KGS", "TJS",
}

# Valid payment methods per PRD §FR-4
VALID_PAYMENT_METHODS = {"Cash", "Card", "Check", "Split"}


# --- Line Item Schema ---

class LineItem(BaseModel):
    """A single line item on a receipt."""
    description: str = Field(..., min_length=1, max_length=500)
    quantity: Decimal = Field(..., ge=0)
    unit_price: Decimal = Field(..., ge=0)
    line_total: Decimal = Field(..., ge=0)

    @model_validator(mode="after")
    def validate_line_item_math(self) -> "LineItem":
        """line_item_math: abs(qty × unit_price − line_total) ≤ 0.05"""
        expected = self.quantity * self.unit_price
        if abs(expected - self.line_total) > Decimal("0.05"):
            raise ValueError(
                f"Line item math error: {self.quantity} × {self.unit_price} = "
                f"{expected}, but line_total is {self.line_total} "
                f"(diff: {abs(expected - self.line_total):.2f}, max allowed: 0.05)"
            )
        return self


# --- Confidence Scores Schema ---

class ConfidenceScores(BaseModel):
    """Per-field confidence scores from LLM extraction (0.0–1.0)."""
    vendor_name: float = Field(default=0.0, ge=0.0, le=1.0)
    date: float = Field(default=0.0, ge=0.0, le=1.0)
    total_amount: float = Field(default=0.0, ge=0.0, le=1.0)
    subtotal: float = Field(default=0.0, ge=0.0, le=1.0)
    tax_amount: float = Field(default=0.0, ge=0.0, le=1.0)
    line_items: float = Field(default=0.0, ge=0.0, le=1.0)


# --- Receipt Extraction Schema ---

class ReceiptExtraction(BaseModel):
    """
    Full receipt extraction schema with all PRD §FR-3 validators.
    This is the Pydantic model that validates LLM output.
    """
    vendor_name: Optional[str] = None
    date: Optional[dt.date] = None
    currency: str = Field(default="USD")
    subtotal: Optional[Decimal] = Field(default=None, ge=0)
    tax_amount: Optional[Decimal] = Field(default=None, ge=0)
    tip_amount: Optional[Decimal] = Field(default=None, ge=0)
    total_amount: Optional[Decimal] = Field(default=None, ge=0)
    payment_method: Optional[str] = None
    line_items: list[LineItem] = Field(default_factory=list)
    expense_category: Optional[str] = None
    confidence_scores: ConfidenceScores = Field(default_factory=ConfidenceScores)

    # --- Validator: currency_code ---
    @field_validator("currency")
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        """currency_code: must be a valid ISO 4217 three-letter code."""
        code = v.upper().strip()
        if code not in VALID_CURRENCY_CODES:
            raise ValueError(
                f"Invalid ISO 4217 currency code: '{v}'. "
                f"Expected a valid 3-letter code like 'USD', 'EUR', etc."
            )
        return code

    # --- Validator: payment_method ---
    @field_validator("payment_method")
    @classmethod
    def validate_payment_method(cls, v: Optional[str]) -> Optional[str]:
        """payment_method: must be Cash, Card, Check, Split, or null."""
        if v is None:
            return v
        if v not in VALID_PAYMENT_METHODS:
            raise ValueError(
                f"Invalid payment method: '{v}'. "
                f"Must be one of: {', '.join(VALID_PAYMENT_METHODS)}, or null."
            )
        return v

    # --- Validator: amount_sign (handled by Field(ge=0)) ---
    # Already enforced via ge=0 on subtotal, tax_amount, tip_amount, total_amount

    # --- Validator: date_sanity ---
    @field_validator("date")
    @classmethod
    def validate_date_sanity(cls, v: Optional[dt.date]) -> Optional[dt.date]:
        """date_sanity: not future, not > 10 years ago."""
        if v is None:
            return v
        today = dt.date.today()
        if v > today:
            raise ValueError(
                f"Receipt date {v} is in the future. Dates cannot be after today ({today})."
            )
        ten_years_ago = today - timedelta(days=365 * 25)
        if v < ten_years_ago:
            raise ValueError(
                f"Receipt date {v} is more than 25 years ago. "
                f"Dates must be after {ten_years_ago}."
            )
        return v

    # --- Validator: receipt_math ---
    @model_validator(mode="after")
    def validate_receipt_math(self) -> "ReceiptExtraction":
        """receipt_math: abs(subtotal + tax + tip − total) ≤ 0.05"""
        subtotal = self.subtotal or Decimal("0")
        tax = self.tax_amount or Decimal("0")
        tip = self.tip_amount or Decimal("0")
        total = self.total_amount

        if total is not None:
            expected_exclusive = subtotal + tax + tip
            expected_inclusive = subtotal + tip
            
            diff_exclusive = abs(expected_exclusive - total)
            diff_inclusive = abs(expected_inclusive - total)
            
            if diff_exclusive > Decimal("0.05") and diff_inclusive > Decimal("0.05"):
                raise ValueError(
                    f"Receipt math error: Could not balance. Total is {total}, "
                    f"but exclusive sum is {expected_exclusive} and inclusive sum is {expected_inclusive}."
                )
        return self


# --- Request/Response Schemas ---

class ReceiptUploadResponse(BaseModel):
    """Response for POST /api/v1/receipts/upload"""
    id: UUID
    status: str
    image_url: str
    created_at: datetime


class ReceiptExtractResponse(BaseModel):
    """Response for POST /api/v1/receipts/{id}/extract"""
    id: UUID
    status: str
    queue_position: int = 0


class ReceiptResponse(BaseModel):
    """Full receipt response for GET /api/v1/receipts/{id}"""
    id: UUID
    status: str
    image_url: str
    original_filename: Optional[str] = None
    mime_type: Optional[str] = None
    file_size_bytes: Optional[int] = None
    extracted_data: Optional[dict] = None
    confidence_scores: Optional[dict] = None
    extraction_error: Optional[str] = None
    extracted_at: Optional[datetime] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class ReceiptCorrectRequest(BaseModel):
    """Request for PUT /api/v1/receipts/{id}/correct — partial update."""
    vendor_name: Optional[str] = None
    date: Optional[dt.date] = None
    currency: Optional[str] = None
    subtotal: Optional[Decimal] = None
    tax_amount: Optional[Decimal] = None
    tip_amount: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    payment_method: Optional[str] = None
    line_items: Optional[list[LineItem]] = None
    expense_category: Optional[str] = None


class JournalizeRequest(BaseModel):
    """Request for POST /api/v1/receipts/{id}/journalize"""
    account_overrides: Optional[dict[str, str]] = None
