from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    Numeric,
    text,
)
from sqlalchemy.dialects.postgresql import UUID

from app.database import Base


class UsageSnapshot(Base):
    __tablename__ = "usage_snapshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    checked_at = Column(
        DateTime(timezone=True), nullable=False, server_default=text("NOW()"), index=True
    )
    postgres_mb = Column(Numeric(10, 2))
    storage_mb = Column(Numeric(10, 2))
    request_count_today = Column(Integer)
    threshold_hit = Column(Boolean, nullable=False, default=False)
    alert_logged = Column(Boolean, nullable=False, default=False)
