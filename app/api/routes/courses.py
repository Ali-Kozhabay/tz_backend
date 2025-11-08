from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_optional_user, require_role
from app.models.course import Course, CourseVisibility, Lesson
from app.models.progress import LessonProgress
from app.models.user import User, UserRole
from app.schemas.course import (
    CourseCreate,
    CourseDetail,
    CourseRead,
    LessonCreate,
    LessonRead,
    ProgressRead,
)
from app.schemas.progress import ProgressMarkRequest, ProgressResponse

router = APIRouter(prefix="", tags=["courses"])


@router.get("/courses", response_model=dict)
async def list_courses(
    visibility: Optional[str] = Query(default=None),
    limit: int = Query(default=10, le=50),
    cursor: Optional[int] = None,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    stmt = (
        select(Course, func.count(Lesson.id).label("lessons_count"))
        .join(Lesson, Lesson.course_id == Course.id, isouter=True)
        .group_by(Course.id)
        .order_by(Course.id)
        .limit(limit)
    )
    if cursor:
        stmt = stmt.where(Course.id > cursor)

    allowed_visibilities = [CourseVisibility.PUBLIC.value]
    if user and user.role in (UserRole.MEMBER, UserRole.ADMIN):
        allowed_visibilities.append(CourseVisibility.MEMBER.value)

    if visibility:
        stmt = stmt.where(Course.visibility == visibility)
    else:
        stmt = stmt.where(Course.visibility.in_(allowed_visibilities))

    result = (await db.execute(stmt)).all()
    items = [
        CourseRead(
            id=course.id,
            title=course.title,
            slug=course.slug,
            visibility=course.visibility,
            cover_url=course.cover_url,
            lessons_count=count,
        )
        for course, count in result
    ]
    next_cursor = items[-1].id if items else None
    return {"items": items, "next_cursor": next_cursor}


@router.get("/courses/{slug}", response_model=CourseDetail)
async def get_course(
    slug: str,
    db: AsyncSession = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    stmt = select(Course).where(Course.slug == slug)
    course = await db.scalar(stmt)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if course.visibility == CourseVisibility.MEMBER.value and (
        not user or user.role not in (UserRole.MEMBER, UserRole.ADMIN)
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    lessons_stmt = (
        select(Lesson).where(Lesson.course_id == course.id, Lesson.published.is_(True)).order_by(Lesson.index)
    )
    lessons = (await db.scalars(lessons_stmt)).all()

    progress_percent = None
    if user:
        total = len(lessons)
        if total:
            completed_stmt = (
                select(func.count())
                .select_from(LessonProgress)
                .join(Lesson, Lesson.id == LessonProgress.lesson_id)
                .where(
                    Lesson.course_id == course.id,
                    LessonProgress.user_id == user.id,
                    LessonProgress.status == "done",
                )
            )
            completed = await db.scalar(completed_stmt)
            progress_percent = int((completed / total) * 100)

    response = CourseDetail(
        course=CourseRead(
            id=course.id,
            title=course.title,
            slug=course.slug,
            visibility=course.visibility,
            cover_url=course.cover_url,
            lessons_count=len(lessons),
        ),
        lessons=[LessonRead.model_validate(lesson) for lesson in lessons],
        progress=ProgressRead(percent=progress_percent or 0) if progress_percent is not None else None,
    )
    return response


@router.post("/admin/courses", response_model=CourseRead, status_code=status.HTTP_201_CREATED)
async def create_course(
    payload: CourseCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    course = Course(
        title=payload.title,
        slug=payload.slug,
        visibility=payload.visibility,
        cover_url=payload.cover_url,
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return CourseRead(
        id=course.id,
        title=course.title,
        slug=course.slug,
        visibility=course.visibility,
        cover_url=course.cover_url,
        lessons_count=0,
    )


@router.post("/admin/lessons", response_model=LessonRead, status_code=status.HTTP_201_CREATED)
async def create_lesson(
    payload: LessonCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    lesson = Lesson(
        course_id=payload.course_id,
        index=payload.index,
        title=payload.title,
        content_url=payload.content_url,
        duration_sec=payload.duration_sec,
        published=payload.published,
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return LessonRead.model_validate(lesson)


@router.post("/progress/mark", response_model=ProgressResponse)
async def mark_progress(
    payload: ProgressMarkRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.USER)),
):
    stmt = select(LessonProgress).where(
        LessonProgress.user_id == user.id, LessonProgress.lesson_id == payload.lesson_id
    )
    record = await db.scalar(stmt)
    if record:
        record.status = payload.status
        record.percent = payload.percent
    else:
        record = LessonProgress(
            user_id=user.id,
            lesson_id=payload.lesson_id,
            status=payload.status,
            percent=payload.percent,
        )
        db.add(record)
    await db.commit()
    return ProgressResponse()
