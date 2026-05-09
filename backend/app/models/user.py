import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class UserRole(str, enum.Enum):
    """User role enum for role-based access control."""
    PREPARER = "PREPARER"
    REVIEWER = "REVIEWER"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    full_name = Column(String)
    company_name = Column(String)
    role = Column(SQLEnum(UserRole), nullable=False, server_default='PREPARER')
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
