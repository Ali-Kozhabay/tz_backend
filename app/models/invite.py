from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String

from app.db.base import Base


class Invite(Base):
    __tablename__ = "invites"

    code = Column(String(64), primary_key=True)
    role_to_grant = Column(String(32), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
