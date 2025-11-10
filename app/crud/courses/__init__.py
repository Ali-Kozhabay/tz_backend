from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course, Lesson


async def list_courses(
    db: AsyncSession,
    *,
    cursor: int | None,
    limit: int,
    visibility: str | None,
    allowed_visibilities: list[str],
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
    if visibility:
        stmt = stmt.where(Course.visibility == visibility)
    else:
        stmt = stmt.where(Course.visibility.in_(allowed_visibilities))
    result = await db.execute(stmt)
    return result.all()


async def get_by_slug(db: AsyncSession, slug: str) -> Course | None:
    stmt = select(Course).where(Course.slug == slug)
    return await db.scalar(stmt)


async def list_published_lessons(db: AsyncSession, course_id: int):
    stmt = select(Lesson).where(Lesson.course_id == course_id, Lesson.published.is_(True)).order_by(Lesson.index)
    return (await db.scalars(stmt)).all()


async def create_course(
    db: AsyncSession,
    *,
    title: str,
    slug: str,
    visibility: str,
    cover_url: str | None,
) -> Course:
    course = Course(
        title=title,
        slug=slug,
        visibility=visibility,
        cover_url=cover_url,
    )
    db.add(course)
    await db.commit()
    await db.refresh(course)
    return course


async def create_lesson(
    db: AsyncSession,
    *,
    course_id: int,
    index: int,
    title: str,
    content_url: str,
    duration_sec: int | None,
    published: bool,
) -> Lesson:
    lesson = Lesson(
        course_id=course_id,
        index=index,
        title=title,
        content_url=content_url,
        duration_sec=duration_sec,
        published=published,
    )
    db.add(lesson)
    await db.commit()
    await db.refresh(lesson)
    return lesson
