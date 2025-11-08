from enum import Enum

from sqlalchemy import Boolean, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base


class CourseVisibility(str, Enum):
    PUBLIC = "public"
    MEMBER = "member"


class Course(Base):
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False, unique=True, index=True)
    visibility = Column(String(20), default=CourseVisibility.PUBLIC.value, nullable=False)
    cover_url = Column(String(512), nullable=True)

    lessons = relationship("Lesson", back_populates="course", cascade="all, delete")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True)
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False)
    index = Column(Integer, nullable=False)
    title = Column(String(255), nullable=False)
    content_url = Column(String(512), nullable=False)
    duration_sec = Column(Integer, nullable=True)
    published = Column(Boolean, default=False, nullable=False)

    course = relationship("Course", back_populates="lessons")
