"""
Basic Phase 3 tests to verify role system and approval workflow.
Run with: pytest tests/test_phase3_basic.py -v
"""

import pytest
from uuid import uuid4
from sqlalchemy import select

from app.models.user import User, UserRole
from app.models.receipt import Receipt, ReceiptStatus, ReviewComment
from app.models.gnucash import GnuCashMapping


@pytest.mark.asyncio
class TestUserRoles:
    """Test user role system (Migration 010)."""
    
    async def test_create_user_with_role(self, db_session):
        """Test creating users with different roles."""
        # Create preparer
        preparer = User(
            id=uuid4(),
            full_name="Test Preparer",
            company_name="Test Corp",
            role=UserRole.PREPARER
        )
        db_session.add(preparer)
        
        # Create reviewer
        reviewer = User(
            id=uuid4(),
            full_name="Test Reviewer",
            company_name="Test Corp",
            role=UserRole.REVIEWER
        )
        db_session.add(reviewer)
        
        # Create admin
        admin = User(
            id=uuid4(),
            full_name="Test Admin",
            company_name="Test Corp",
            role=UserRole.ADMIN
        )
        db_session.add(admin)
        
        await db_session.commit()
        
        # Verify
        result = await db_session.execute(select(User))
        users = result.scalars().all()
        
        assert len(users) >= 3
        assert any(u.role == UserRole.PREPARER for u in users)
        assert any(u.role == UserRole.REVIEWER for u in users)
        assert any(u.role == UserRole.ADMIN for u in users)
    
    async def test_default_role_is_preparer(self, db_session):
        """Test that new users default to PREPARER role."""
        user = User(
            id=uuid4(),
            full_name="New User",
            company_name="Test Corp"
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        assert user.role == UserRole.PREPARER


@pytest.mark.asyncio
class TestPendingReviewStatus:
    """Test PENDING_REVIEW status (Migration 011)."""
    
    async def test_create_receipt_with_pending_review(self, db_session, test_user):
        """Test creating receipt with PENDING_REVIEW status."""
        receipt = Receipt(
            id=uuid4(),
            user_id=test_user.id,
            image_url="test/path.jpg",
            status=ReceiptStatus.PENDING_REVIEW
        )
        db_session.add(receipt)
        await db_session.commit()
        await db_session.refresh(receipt)
        
        assert receipt.status == ReceiptStatus.PENDING_REVIEW
    
    async def test_valid_transitions_to_pending_review(self):
        """Test that REVIEWED can transition to PENDING_REVIEW."""
        from app.models.receipt import validate_status_transition
        
        # Valid: REVIEWED → PENDING_REVIEW
        assert validate_status_transition(
            ReceiptStatus.REVIEWED,
            ReceiptStatus.PENDING_REVIEW
        ) is True
        
        # Invalid: UPLOADED → PENDING_REVIEW
        assert validate_status_transition(
            ReceiptStatus.UPLOADED,
            ReceiptStatus.PENDING_REVIEW
        ) is False
    
    async def test_valid_transitions_from_pending_review(self):
        """Test transitions from PENDING_REVIEW."""
        from app.models.receipt import validate_status_transition
        
        # Valid: PENDING_REVIEW → REVIEWED (approved)
        assert validate_status_transition(
            ReceiptStatus.PENDING_REVIEW,
            ReceiptStatus.REVIEWED
        ) is True
        
        # Valid: PENDING_REVIEW → REJECTED
        assert validate_status_transition(
            ReceiptStatus.PENDING_REVIEW,
            ReceiptStatus.REJECTED
        ) is True
        
        # Invalid: PENDING_REVIEW → POSTED (must go through REVIEWED first)
        assert validate_status_transition(
            ReceiptStatus.PENDING_REVIEW,
            ReceiptStatus.POSTED
        ) is False


@pytest.mark.asyncio
class TestGnuCashMappings:
    """Test GnuCash mappings (Migration 012)."""
    
    async def test_create_mapping(self, db_session, test_user):
        """Test creating a GnuCash account mapping."""
        mapping = GnuCashMapping(
            id=uuid4(),
            user_id=test_user.id,
            internal_account_code="EXPENSE_OFFICE",
            gnucash_account_path="Expenses:Office Supplies"
        )
        db_session.add(mapping)
        await db_session.commit()
        await db_session.refresh(mapping)
        
        assert mapping.internal_account_code == "EXPENSE_OFFICE"
        assert mapping.gnucash_account_path == "Expenses:Office Supplies"
    
    async def test_unique_constraint(self, db_session, test_user):
        """Test that (user_id, internal_account_code) is unique."""
        mapping1 = GnuCashMapping(
            id=uuid4(),
            user_id=test_user.id,
            internal_account_code="EXPENSE_OFFICE",
            gnucash_account_path="Expenses:Office Supplies"
        )
        db_session.add(mapping1)
        await db_session.commit()
        
        # Try to create duplicate
        mapping2 = GnuCashMapping(
            id=uuid4(),
            user_id=test_user.id,
            internal_account_code="EXPENSE_OFFICE",
            gnucash_account_path="Expenses:Office"
        )
        db_session.add(mapping2)
        
        with pytest.raises(Exception):  # Should raise IntegrityError
            await db_session.commit()


@pytest.mark.asyncio
class TestReviewComments:
    """Test review comments (Migration 013)."""
    
    async def test_create_review_comment(self, db_session, test_user, test_receipt):
        """Test creating a review comment."""
        comment = ReviewComment(
            id=uuid4(),
            receipt_id=test_receipt.id,
            reviewer_id=test_user.id,
            comment="Please fix the date",
            action="RETURNED"
        )
        db_session.add(comment)
        await db_session.commit()
        await db_session.refresh(comment)
        
        assert comment.comment == "Please fix the date"
        assert comment.action == "RETURNED"
    
    async def test_review_comment_actions(self, db_session, test_user, test_receipt):
        """Test all valid review comment actions."""
        actions = ["APPROVED", "REJECTED", "RETURNED"]
        
        for action in actions:
            comment = ReviewComment(
                id=uuid4(),
                receipt_id=test_receipt.id,
                reviewer_id=test_user.id,
                comment=f"Test {action}",
                action=action
            )
            db_session.add(comment)
        
        await db_session.commit()
        
        # Verify all created
        result = await db_session.execute(
            select(ReviewComment).where(ReviewComment.receipt_id == test_receipt.id)
        )
        comments = result.scalars().all()
        
        assert len(comments) == 3
        assert set(c.action for c in comments) == set(actions)


# Fixtures

@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
    user = User(
        id=uuid4(),
        full_name="Test User",
        company_name="Test Corp",
        role=UserRole.PREPARER
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_receipt(db_session, test_user):
    """Create a test receipt."""
    receipt = Receipt(
        id=uuid4(),
        user_id=test_user.id,
        image_url="test/path.jpg",
        status=ReceiptStatus.REVIEWED
    )
    db_session.add(receipt)
    await db_session.commit()
    await db_session.refresh(receipt)
    return receipt


@pytest.fixture
async def db_session():
    """Create a test database session."""
    from app.database import async_session_maker
    
    async with async_session_maker() as session:
        yield session
        await session.rollback()
