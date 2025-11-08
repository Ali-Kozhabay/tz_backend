from fastapi.concurrency import run_in_threadpool
from rq import Queue

from app.services.notifications import send_email
from app.services.redis import get_redis

_queue: Queue | None = None


def get_queue() -> Queue:
    global _queue
    if _queue is None:
        redis_conn = get_redis()
        _queue = Queue("emails", connection=redis_conn)
    return _queue


async def enqueue_email(to_email: str, subject: str, body: str) -> None:
    queue = get_queue()
    await run_in_threadpool(queue.enqueue, send_email, to_email, subject, body)
