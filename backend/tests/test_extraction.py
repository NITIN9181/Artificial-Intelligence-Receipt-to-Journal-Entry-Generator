"""
Tests for ReceiptExtraction Pydantic schema — 100% validator coverage required.
Tests all 5 validators: line_item_math, receipt_math, date_sanity, currency_code, amount_sign
"""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.schemas.receipt import ConfidenceScores, LineItem, ReceiptExtraction


# ─── LineItem Tests ───

class TestLineItemMath:
    """line_item_math: abs(qty × unit_price − line_total) ≤ 0.05"""

    def test_valid_line_item(self):
        item = LineItem(description="Paper", quantity=2, unit_price=12.99, line_total=25.98)
        assert item.line_total == Decimal("25.98")

    def test_valid_with_rounding_tolerance(self):
        """Within 0.05 tolerance should pass."""
        item = LineItem(description="Item", quantity=3, unit_price=3.33, line_total=10.00)
        assert item is not None  # 3 × 3.33 = 9.99, diff = 0.01 ≤ 0.05

    def test_invalid_line_item_math(self):
        """Exceeds 0.05 tolerance."""
        with pytest.raises(ValueError, match="Line item math error"):
            LineItem(description="Item", quantity=2, unit_price=10.00, line_total=25.00)

    def test_zero_quantity(self):
        item = LineItem(description="Free item", quantity=0, unit_price=5.00, line_total=0.00)
        assert item.line_total == Decimal("0")

    def test_single_quantity(self):
        item = LineItem(description="Single", quantity=1, unit_price=99.99, line_total=99.99)
        assert item.quantity == Decimal("1")


# ─── Receipt Math Tests ───

class TestReceiptMath:
    """receipt_math: abs(subtotal + tax + tip − total) ≤ 0.05"""

    def test_valid_receipt_math(self):
        extraction = ReceiptExtraction(
            subtotal=Decimal("45.00"),
            tax_amount=Decimal("3.94"),
            tip_amount=Decimal("0.00"),
            total_amount=Decimal("48.94"),
        )
        assert extraction.total_amount == Decimal("48.94")

    def test_valid_with_tip(self):
        extraction = ReceiptExtraction(
            subtotal=Decimal("20.00"),
            tax_amount=Decimal("1.60"),
            tip_amount=Decimal("4.00"),
            total_amount=Decimal("25.60"),
        )
        assert extraction.total_amount == Decimal("25.60")

    def test_valid_within_tolerance(self):
        """0.03 diff — within tolerance."""
        extraction = ReceiptExtraction(
            subtotal=Decimal("10.00"),
            tax_amount=Decimal("0.80"),
            tip_amount=Decimal("0.00"),
            total_amount=Decimal("10.83"),
        )
        assert extraction is not None

    def test_invalid_receipt_math(self):
        with pytest.raises(ValueError, match="Receipt math error"):
            ReceiptExtraction(
                subtotal=Decimal("45.00"),
                tax_amount=Decimal("3.94"),
                tip_amount=Decimal("0.00"),
                total_amount=Decimal("100.00"),
            )

    def test_null_total_skips_validation(self):
        """If total is None, skip receipt math check."""
        extraction = ReceiptExtraction(
            subtotal=Decimal("45.00"),
            tax_amount=Decimal("3.94"),
            total_amount=None,
        )
        assert extraction.total_amount is None

    def test_all_zeros(self):
        extraction = ReceiptExtraction(
            subtotal=Decimal("0"),
            tax_amount=Decimal("0"),
            tip_amount=Decimal("0"),
            total_amount=Decimal("0"),
        )
        assert extraction.total_amount == Decimal("0")


# ─── Date Sanity Tests ───

class TestDateSanity:
    """date_sanity: not future, not > 10 years ago."""

    def test_valid_today(self):
        extraction = ReceiptExtraction(date=date.today())
        assert extraction.date == date.today()

    def test_valid_yesterday(self):
        yesterday = date.today() - timedelta(days=1)
        extraction = ReceiptExtraction(date=yesterday)
        assert extraction.date == yesterday

    def test_valid_recent_past(self):
        recent = date.today() - timedelta(days=365)
        extraction = ReceiptExtraction(date=recent)
        assert extraction.date == recent

    def test_invalid_future_date(self):
        future = date.today() + timedelta(days=1)
        with pytest.raises(ValueError, match="in the future"):
            ReceiptExtraction(date=future)

    def test_invalid_too_old(self):
        old = date.today() - timedelta(days=365 * 11)
        with pytest.raises(ValueError, match="more than 10 years ago"):
            ReceiptExtraction(date=old)

    def test_null_date_passes(self):
        extraction = ReceiptExtraction(date=None)
        assert extraction.date is None

    def test_boundary_ten_years(self):
        """Exactly 10 years ago should pass."""
        boundary = date.today() - timedelta(days=365 * 10)
        extraction = ReceiptExtraction(date=boundary)
        assert extraction.date == boundary


# ─── Currency Code Tests ───

class TestCurrencyCode:
    """currency_code: valid ISO 4217."""

    def test_valid_usd(self):
        extraction = ReceiptExtraction(currency="USD")
        assert extraction.currency == "USD"

    def test_valid_eur(self):
        extraction = ReceiptExtraction(currency="EUR")
        assert extraction.currency == "EUR"

    def test_valid_lowercase(self):
        """Should auto-uppercase."""
        extraction = ReceiptExtraction(currency="gbp")
        assert extraction.currency == "GBP"

    def test_invalid_currency(self):
        with pytest.raises(ValueError, match="Invalid ISO 4217"):
            ReceiptExtraction(currency="XYZ")

    def test_default_usd(self):
        extraction = ReceiptExtraction()
        assert extraction.currency == "USD"


# ─── Amount Sign Tests ───

class TestAmountSign:
    """amount_sign: all amount fields ≥ 0."""

    def test_valid_positive_amounts(self):
        extraction = ReceiptExtraction(
            subtotal=Decimal("45.00"),
            tax_amount=Decimal("3.94"),
            tip_amount=Decimal("5.00"),
            total_amount=Decimal("53.94"),
        )
        assert extraction.subtotal == Decimal("45.00")

    def test_valid_zero_amounts(self):
        extraction = ReceiptExtraction(
            subtotal=Decimal("0"),
            tax_amount=Decimal("0"),
            tip_amount=Decimal("0"),
            total_amount=Decimal("0"),
        )
        assert extraction.subtotal == Decimal("0")

    def test_invalid_negative_subtotal(self):
        with pytest.raises(ValueError):
            ReceiptExtraction(subtotal=Decimal("-1.00"))

    def test_invalid_negative_tax(self):
        with pytest.raises(ValueError):
            ReceiptExtraction(tax_amount=Decimal("-0.50"))

    def test_invalid_negative_tip(self):
        with pytest.raises(ValueError):
            ReceiptExtraction(tip_amount=Decimal("-2.00"))

    def test_invalid_negative_total(self):
        with pytest.raises(ValueError):
            ReceiptExtraction(total_amount=Decimal("-10.00"))


# ─── Payment Method Tests ───

class TestPaymentMethod:
    """payment_method: Cash, Card, Check, Split, or null."""

    def test_valid_cash(self):
        extraction = ReceiptExtraction(payment_method="Cash")
        assert extraction.payment_method == "Cash"

    def test_valid_card(self):
        extraction = ReceiptExtraction(payment_method="Card")
        assert extraction.payment_method == "Card"

    def test_valid_check(self):
        extraction = ReceiptExtraction(payment_method="Check")
        assert extraction.payment_method == "Check"

    def test_valid_split(self):
        extraction = ReceiptExtraction(payment_method="Split")
        assert extraction.payment_method == "Split"

    def test_valid_null(self):
        extraction = ReceiptExtraction(payment_method=None)
        assert extraction.payment_method is None

    def test_invalid_payment_method(self):
        with pytest.raises(ValueError, match="Invalid payment method"):
            ReceiptExtraction(payment_method="Bitcoin")


# ─── Full Extraction Tests ───

class TestFullExtraction:
    """Integration tests with all fields."""

    def test_full_valid_extraction(self):
        extraction = ReceiptExtraction(
            vendor_name="Office Depot",
            date=date(2026, 4, 28),
            currency="USD",
            subtotal=Decimal("45.00"),
            tax_amount=Decimal("3.94"),
            tip_amount=Decimal("0.00"),
            total_amount=Decimal("48.94"),
            payment_method="Card",
            line_items=[
                LineItem(
                    description="Copy Paper Ream",
                    quantity=2,
                    unit_price=Decimal("12.99"),
                    line_total=Decimal("25.98"),
                ),
            ],
            expense_category="Office Supplies",
            confidence_scores=ConfidenceScores(
                vendor_name=0.97, date=0.99, total_amount=0.95,
                subtotal=0.90, tax_amount=0.85, line_items=0.80,
            ),
        )
        assert extraction.vendor_name == "Office Depot"
        assert len(extraction.line_items) == 1

    def test_minimal_extraction(self):
        """Only required fields."""
        extraction = ReceiptExtraction()
        assert extraction.currency == "USD"
        assert extraction.line_items == []
