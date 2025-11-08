from typing import List, Optional

from pydantic import BaseModel


class LessonRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    course_id: int
    index: int
    title: str
    content_url: str
    duration_sec: int | None = None
    published: bool


class LessonCreate(BaseModel):
    course_id: int
    index: int
    title: str
    content_url: str
    duration_sec: int | None = None
    published: bool = False


class CourseBase(BaseModel):
    title: str
    slug: str
    visibility: str
    cover_url: str | None = None


class CourseCreate(CourseBase):
    pass


class ProgressRead(BaseModel):
    percent: int


class CourseRead(CourseBase):
    model_config = {"from_attributes": True}

    id: int
    lessons_count: int


class CourseDetail(BaseModel):
    course: CourseRead
    lessons: List[LessonRead]
    progress: Optional[ProgressRead] = None
