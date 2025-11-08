import pytest

from app.core.security import create_access_token
from app.models.user import UserRole


@pytest.mark.asyncio
async def test_course_lifecycle(client, user_factory):
    admin = await user_factory("coach@example.com", "password123", role=UserRole.ADMIN)
    learner = await user_factory("learner@example.com", "password123", role=UserRole.MEMBER)
    admin_token = create_access_token(str(admin.id))
    learner_token = create_access_token(str(learner.id))

    course_payload = {
        "title": "Onboarding",
        "slug": "onboarding",
        "visibility": "member",
        "cover_url": None,
    }
    res = await client.post(
        "/admin/courses",
        json=course_payload,
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 201
    course_id = res.json()["id"]

    lesson_ids = []
    for idx in range(2):
        res = await client.post(
            "/admin/lessons",
            json={
                "course_id": course_id,
                "index": idx,
                "title": f"Lesson {idx}",
                "content_url": f"https://cdn/{idx}",
                "duration_sec": 60,
                "published": True,
            },
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        assert res.status_code == 201
        lesson_ids.append(res.json()["id"])

    res = await client.get("/courses")
    assert res.status_code == 200
    assert res.json()["items"] == []  # guest cannot see member course

    res = await client.get(
        "/courses",
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert len(res.json()["items"]) == 1

    res = await client.get(
        "/courses/onboarding",
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert res.status_code == 200
    assert len(res.json()["lessons"]) == 2

    progress_body = {"lesson_id": lesson_ids[0], "status": "done", "percent": 100}
    res = await client.post(
        "/progress/mark",
        json=progress_body,
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert res.status_code == 200

    # idempotent update
    progress_body["percent"] = 90
    res = await client.post(
        "/progress/mark",
        json=progress_body,
        headers={"Authorization": f"Bearer {learner_token}"},
    )
    assert res.status_code == 200
