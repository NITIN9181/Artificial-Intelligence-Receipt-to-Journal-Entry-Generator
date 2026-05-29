from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric

from app.database import Base
from app.models.receipt import GUID


class UsageSnapshot(Base):
    __tablename__ = "usage_snapshots"

    id = Column(GUID, primary_key=True, default=uuid4)
    checked_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    postgres_mb = Column(Numeric(10, 2))
    storage_mb = Column(Numeric(10, 2))
    request_count_today = Column(Integer)
    threshold_hit = Column(Boolean, nullable=False, default=False)
    alert_logged = Column(Boolean, nullable=False, default=False)
