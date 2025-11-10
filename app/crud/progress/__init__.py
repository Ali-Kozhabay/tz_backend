from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Lesson
from app.models.progress import LessonProgress


async def count_completed_for_course(
    db: AsyncSession,
    *,
    course_id: int,
    user_id: int,
) -> int:
    stmt = (
        select(func.count())
        .select_from(LessonProgress)
        .join(Lesson, Lesson.id == LessonProgress.lesson_id)
        .where(
            Lesson.course_id == course_id,
            LessonProgress.user_id == user_id,
            LessonProgress.status == "done",
        )
    )
    return await db.scalar(stmt) or 0


async def upsert_progress(
    db: AsyncSession,
    *,
    user_id: int,
    lesson_id: int,
    status: str,
    percent: int,
) -> LessonProgress:
    stmt = select(LessonProgress).where(
        LessonProgress.user_id == user_id,
        LessonProgress.lesson_id == lesson_id,
    )
    record = await db.scalar(stmt)
    if record:
        record.status = status
        record.percent = percent
    else:
        record = LessonProgress(
            user_id=user_id,
            lesson_id=lesson_id,
            status=status,
            percent=percent,
        )
    db.add(record)
    await db.commit()
    return record
