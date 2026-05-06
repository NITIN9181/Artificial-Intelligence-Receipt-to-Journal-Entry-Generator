import enum
from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    String,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    full_name = Column(String)
    company_name = Column(String)
    is_admin = Column(Boolean, nullable=False, server_default='false')
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()")
    )
