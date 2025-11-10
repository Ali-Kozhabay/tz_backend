from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db, get_optional_user, require_role
from app.crud import courses as courses_crud
from app.crud import progress as progress_crud
from app.models.course import CourseVisibility
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
    allowed_visibilities = [CourseVisibility.PUBLIC.value]
    if user and user.role in (UserRole.MEMBER, UserRole.ADMIN):
        allowed_visibilities.append(CourseVisibility.MEMBER.value)

    result = await courses_crud.list_courses(
        db,
        cursor=cursor,
        limit=limit,
        visibility=visibility,
        allowed_visibilities=allowed_visibilities,
    )
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
    course = await courses_crud.get_by_slug(db, slug)
    if course is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if course.visibility == CourseVisibility.MEMBER.value and (
        not user or user.role not in (UserRole.MEMBER, UserRole.ADMIN)
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    lessons = await courses_crud.list_published_lessons(db, course.id)

    progress_percent = None
    if user:
        total = len(lessons)
        if total:
            completed = await progress_crud.count_completed_for_course(
                db, course_id=course.id, user_id=user.id
            )
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
    course = await courses_crud.create_course(
        db,
        title=payload.title,
        slug=payload.slug,
        visibility=payload.visibility,
        cover_url=payload.cover_url,
    )
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
    lesson = await courses_crud.create_lesson(
        db,
        course_id=payload.course_id,
        index=payload.index,
        title=payload.title,
        content_url=payload.content_url,
        duration_sec=payload.duration_sec,
        published=payload.published,
    )
    return LessonRead.model_validate(lesson)


@router.post("/progress/mark", response_model=ProgressResponse)
async def mark_progress(
    payload: ProgressMarkRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_role(UserRole.USER)),
):
    await progress_crud.upsert_progress(
        db,
        user_id=user.id,
        lesson_id=payload.lesson_id,
        status=payload.status,
        percent=payload.percent,
    )
    return ProgressResponse()
