"""
Test fixtures for Phase 3 tests.
Provides users with different roles, receipts in various states, and tokens.

To use: either merge with existing conftest.py or import from this file.
"""

import pytest
from uuid import uuid4
from datetime import datetime, date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User, UserRole
from app.models.receipt import Receipt, ReceiptStatus, ReviewComment
from app.models.journal import JournalEntry, EntryStatus
from app.database import async_session_maker


# ============================================================================
# User Fixtures
# ============================================================================

@pytest.fixture
async def preparer_user(db: AsyncSession):
    """Create a user with PREPARER role."""
    user = User(
        id=uuid4(),
        full_name="Test Preparer",
        company_name="Test Corp",
        role=UserRole.PREPARER
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def reviewer_user(db: AsyncSession):
    """Create a user with REVIEWER role."""
    user = User(
        id=uuid4(),
        full_name="Test Reviewer",
        company_name="Test Corp",
        role=UserRole.REVIEWER
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def admin_user(db: AsyncSession):
    """Create a user with ADMIN role."""
    user = User(
        id=uuid4(),
        full_name="Test Admin",
        company_name="Test Corp",
        role=UserRole.ADMIN
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest.fixture
async def other_user(db: AsyncSession):
    """Create another preparer user (for testing cross-user access)."""
    user = User(
        id=uuid4(),
        full_name="Other User",
        company_name="Other Corp",
        role=UserRole.PREPARER
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# ============================================================================
# Token Fixtures
# ============================================================================

@pytest.fixture
def preparer_token(preparer_user):
    """Generate JWT for preparer."""
    from app.auth import create_test_token
    return f"Bearer {create_test_token(str(preparer_user.id), 'PREPARER')}"


@pytest.fixture
def reviewer_token(reviewer_user):
    """Generate JWT for reviewer."""
    from app.auth import create_test_token
    return f"Bearer {create_test_token(str(reviewer_user.id), 'REVIEWER')}"


@pytest.fixture
def admin_token(admin_user):
    """Generate JWT for admin."""
    from app.auth import create_test_token
    return f"Bearer {create_test_token(str(admin_user.id), 'ADMIN')}"


# ============================================================================
# Receipt Fixtures
# ============================================================================

@pytest.fixture
async def uploaded_receipt(db: AsyncSession, preparer_user):
    """Create a receipt in UPLOADED status."""
    receipt = Receipt(
        id=uuid4(),
        user_id=preparer_user.id,
        image_url="test/uploaded.jpg",
        status=ReceiptStatus.UPLOADED
    )
    db.add(receipt)
    await db.commit()
    await db.refresh(receipt)
    return receipt


@pytest.fixture
async def extracted_receipt(db: AsyncSession, preparer_user):
    """Create a receipt in EXTRACTED status with data."""
    receipt = Receipt(
        id=uuid4(),
        user_id=preparer_user.id,
        image_url="test/extracted.jpg",
        status=ReceiptStatus.EXTRACTED,
        extracted_data={
            "vendor_name": "Test Vendor",
            "date": "2024-01-15",
            "total_amount": 50.00,
            "currency": "USD"
        }
    )
    db.add(receipt)
    await db.commit()
    await db.refresh(receipt)
    return receipt


@pytest.fixture
async def reviewed_receipt(db: AsyncSession, preparer_user):
    """Create a receipt in REVIEWED status."""
    receipt = Receipt(
        id=uuid4(),
        user_id=preparer_user.id,
        image_url="test/reviewed.jpg",
        status=ReceiptStatus.REVIEWED,
        extracted_data={
            "vendor_name": "Test Vendor",
            "date": "2024-01-15",
            "total_amount": 50.00,
            "currency": "USD"
        }
    )
    db.add(receipt)
    await db.commit()
    await db.refresh(receipt)
    return receipt


@pytest.fixture
async def reviewed_receipt_with_data(db: AsyncSession, preparer_user):
    """Create a receipt in REVIEWED status with complete data for journalizing."""
    receipt = Receipt(
        id=uuid4(),
        user_id=preparer_user.id,
        image_url="test/reviewed_complete.jpg",
        status=ReceiptStatus.REVIEWED,
        extracted_data={
            "vendor_name": "Test Vendor",
            "date": "2024-01-15",
            "total_amount": 50.00,
            "subtotal": 45.00,
            "tax_amount": 5.00,
            "currency": "USD",
            "payment_method": "Card",
            "expense_category": "Office Supplies"
        }
    )
    db.add(receipt)
    await db.commit()
    await db.refresh(receipt)
    return receipt


@pytest.fixture
async def pending_receipt(db: AsyncSession, preparer_user):
    """Create a receipt in PENDING_REVIEW status."""
    receipt = Receipt(
        id=uuid4(),
        user_id=preparer_user.id,
        image_url="test/pending.jpg",
        status=ReceiptStatus.PENDING_REVIEW,
        extracted_data={
            "vendor_name": "Test Vendor",
            "date": "2024-01-15",
            "total_amount": 50.00,
            "currency": "USD"
        }
    )
    db.add(receipt)
    await db.commit()
    await db.refresh(receipt)
    return receipt


@pytest.fixture
async def rejected_receipt(db: AsyncSession, preparer_user, reviewer_user):
    """Create a receipt in REJECTED status with review comment."""
    receipt = Receipt(
        id=uuid4(),
        user_id=preparer_user.id,
        image_url="test/rejected.jpg",
        status=ReceiptStatus.REJECTED
    )
    db.add(receipt)
    await db.flush()
    
    # Add rejection comment
    comment = ReviewComment(
        id=uuid4(),
        receipt_id=receipt.id,
        reviewer_id=reviewer_user.id,
        comment="Receipt image is unclear",
        action="REJECTED"
    )
    db.add(comment)
    await db.commit()
    await db.refresh(receipt)
    return receipt


@pytest.fixture
async def other_user_uploaded(db: AsyncSession, other_user):
    """Create a receipt belonging to other_user in UPLOADED status."""
    receipt = Receipt(
        id=uuid4(),
        user_id=other_user.id,
        image_url="test/other_uploaded.jpg",
        status=ReceiptStatus.UPLOADED
    )
    db.add(receipt)
    await db.commit()
    await db.refresh(receipt)
    return receipt


@pytest.fixture
async def other_user_pending(db: AsyncSession, other_user):
    """Create a receipt belonging to other_user in PENDING_REVIEW status."""
    receipt = Receipt(
        id=uuid4(),
        user_id=other_user.id,
        image_url="test/other_pending.jpg",
        status=ReceiptStatus.PENDING_REVIEW,
        extracted_data={
            "vendor_name": "Other Vendor",
            "date": "2024-01-15",
            "total_amount": 75.00,
            "currency": "USD"
        }
    )
    db.add(receipt)
    await db.commit()
    await db.refresh(receipt)
    return receipt


@pytest.fixture
async def other_user_reviewed(db: AsyncSession, other_user):
    """Create a receipt belonging to other_user in REVIEWED status."""
    receipt = Receipt(
        id=uuid4(),
        user_id=other_user.id,
        image_url="test/other_reviewed.jpg",
        status=ReceiptStatus.REVIEWED
    )
    db.add(receipt)
    await db.commit()
    await db.refresh(receipt)
    return receipt


# ============================================================================
# Journal Entry Fixtures
# ============================================================================

@pytest.fixture
async def posted_entry(db: AsyncSession, preparer_user):
    """Create a journal entry in POSTED status."""
    # First create a receipt
    receipt = Receipt(
        id=uuid4(),
        user_id=preparer_user.id,
        image_url="test/posted.jpg",
        status=ReceiptStatus.POSTED
    )
    db.add(receipt)
    await db.flush()
    
    # Create journal entry
    entry = JournalEntry(
        id=uuid4(),
        receipt_id=receipt.id,
        entry_number="JE001",
        entry_date=date(2024, 1, 15),
        status=EntryStatus.POSTED,
        description="Test Entry"
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@pytest.fixture
async def draft_entry(db: AsyncSession, preparer_user):
    """Create a journal entry in DRAFT status."""
    receipt = Receipt(
        id=uuid4(),
        user_id=preparer_user.id,
        image_url="test/draft.jpg",
        status=ReceiptStatus.REVIEWED
    )
    db.add(receipt)
    await db.flush()
    
    entry = JournalEntry(
        id=uuid4(),
        receipt_id=receipt.id,
        entry_number="JE002",
        entry_date=date(2024, 1, 15),
        status=EntryStatus.DRAFT,
        description="Draft Entry"
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@pytest.fixture
async def other_user_posted(db: AsyncSession, other_user):
    """Create a journal entry belonging to other_user in POSTED status."""
    receipt = Receipt(
        id=uuid4(),
        user_id=other_user.id,
        image_url="test/other_posted.jpg",
        status=ReceiptStatus.POSTED
    )
    db.add(receipt)
    await db.flush()
    
    entry = JournalEntry(
        id=uuid4(),
        receipt_id=receipt.id,
        entry_number="JE003",
        entry_date=date(2024, 1, 15),
        status=EntryStatus.POSTED,
        description="Other User Entry"
    )
    db.add(entry)
    await db.commit()
    await db.refresh(entry)
    return entry


@pytest.fixture
async def multiple_posted_entries(db: AsyncSession, preparer_user):
    """Create multiple posted journal entries."""
    entries = []
    for i in range(3):
        receipt = Receipt(
            id=uuid4(),
            user_id=preparer_user.id,
            image_url=f"test/multi_{i}.jpg",
            status=ReceiptStatus.POSTED
        )
        db.add(receipt)
        await db.flush()
        
        entry = JournalEntry(
            id=uuid4(),
            receipt_id=receipt.id,
            entry_number=f"JE00{i+10}",
            entry_date=date(2024, 1, 15 + i),
            status=EntryStatus.POSTED,
            description=f"Multi Entry {i}"
        )
        db.add(entry)
        entries.append(entry)
    
    await db.commit()
    for entry in entries:
        await db.refresh(entry)
    return entries


# ============================================================================
# ID-only Fixtures (for tests that just need IDs)
# ============================================================================

@pytest.fixture
def preparer_user_id(preparer_user):
    return str(preparer_user.id)


@pytest.fixture
def other_user_id(other_user):
    return str(other_user.id)


@pytest.fixture
def uploaded_receipt_id(uploaded_receipt):
    return str(uploaded_receipt.id)


@pytest.fixture
def extracted_receipt_id(extracted_receipt):
    return str(extracted_receipt.id)


@pytest.fixture
def reviewed_receipt_id(reviewed_receipt):
    return str(reviewed_receipt.id)


@pytest.fixture
def reviewed_receipt_with_data_id(reviewed_receipt_with_data):
    return str(reviewed_receipt_with_data.id)


@pytest.fixture
def pending_receipt_id(pending_receipt):
    return str(pending_receipt.id)


@pytest.fixture
def rejected_receipt_id(rejected_receipt):
    return str(rejected_receipt.id)


@pytest.fixture
def other_user_uploaded_id(other_user_uploaded):
    return str(other_user_uploaded.id)


@pytest.fixture
def other_user_pending_id(other_user_pending):
    return str(other_user_pending.id)


@pytest.fixture
def other_user_reviewed_id(other_user_reviewed):
    return str(other_user_reviewed.id)


@pytest.fixture
def posted_entry_id(posted_entry):
    return str(posted_entry.id)


@pytest.fixture
def draft_entry_id(draft_entry):
    return str(draft_entry.id)


@pytest.fixture
def other_user_posted_id(other_user_posted):
    return str(other_user_posted.id)


@pytest.fixture
def multiple_posted_entry_ids(multiple_posted_entries):
    return [str(e.id) for e in multiple_posted_entries]


# ============================================================================
# Database Session Fixture
# ============================================================================

@pytest.fixture
async def db():
    """Create a test database session."""
    async with async_session_maker() as session:
        yield session
        await session.rollback()


# ============================================================================
# HTTP Client Fixture
# ============================================================================

@pytest.fixture
async def client():
    """Create an async HTTP client for testing."""
    from app.main import app
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
