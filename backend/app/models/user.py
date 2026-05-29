import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum as SQLEnum, String

from app.database import Base
from app.models.receipt import GUID


class UserRole(str, enum.Enum):
    PREPARER = "PREPARER"
    REVIEWER = "REVIEWER"
    ADMIN = "ADMIN"


class User(Base):
    __tablename__ = "users"

    id = Column(GUID, primary_key=True, default=uuid4)
    full_name = Column(String)
    company_name = Column(String)
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.PREPARER)
    created_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
