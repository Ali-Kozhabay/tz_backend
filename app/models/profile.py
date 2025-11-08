from sqlalchemy import Column, ForeignKey, Integer, JSON, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class Profile(Base):
    __tablename__ = "profiles"

    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    name = Column(String(255), nullable=True)
    avatar_url = Column(String(512), nullable=True)
    locale = Column(String(10), default="en", nullable=False)
    settings = Column(JSON, default=dict)

    user = relationship("User", back_populates="profile")
