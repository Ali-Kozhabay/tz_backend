from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, JSON, String

from app.db.base import Base


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    actor_id = Column(Integer, nullable=False)
    action = Column(String(255), nullable=False)
    entity = Column(String(255), nullable=False)
    entity_id = Column(String(255), nullable=False)
    meta = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
