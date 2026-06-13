import pytest
from fastapi.testclient import TestClient

from app.main import app
from app import models
from tests.conftest import TestingSessionLocal

client = TestClient(app)


@pytest.fixture
def release():
    response = client.post(
        "/api/releases/",
        json={"version": "v1.0.0", "name": "阻塞计数测试发布"},
    )
    assert response.status_code == 201
    return response.json()


def _get_actual_blocker_count(release_id: int) -> int:
    db = TestingSessionLocal()
    try:
        count = (
            db.query(models.CheckItem)
            .filter(
                models.CheckItem.release_id == release_id,
                models.CheckItem.is_blocking == True,
                models.CheckItem.status.notin_([
                    models.CheckItemStatus.PASSED,
                    models.CheckItemStatus.SKIPPED,
                ]),
            )
            .count()
        )
        return count
    finally:
        db.close()


def _get_release_blocker_count(release_id: int) -> int:
    response = client.get(f"/api/releases/{release_id}")
    assert response.status_code == 200
    return response.json()["blocker_count"]


def _assert_count_consistent(release_id: int):
    persisted = _get_release_blocker_count(release_id)
    actual = _get_actual_blocker_count(release_id)
    assert persisted == actual, (
        f"blocker_count inconsistent: persisted={persisted}, actual={actual}"
    )


class TestBlockerCountIncrement:
    def test_create_blocking_pending_increments_count(self, release):
        release_id = release["id"]
        assert release["blocker_count"] == 0

        response = client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "代码审查", "category": "code", "is_blocking": True, "status": "pending"},
        )
        assert response.status_code == 201

        assert _get_release_blocker_count(release_id) == 1
        _assert_count_consistent(release_id)

    def test_create_blocking_failed_increments_count(self, release):
        release_id = release["id"]

        client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "单元测试", "category": "test", "is_blocking": True, "status": "failed"},
        )

        assert _get_release_blocker_count(release_id) == 1
        _assert_count_consistent(release_id)

    def test_create_non_blocking_does_not_increment(self, release):
        release_id = release["id"]

        client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "文档更新", "category": "documentation", "is_blocking": False, "status": "pending"},
        )

        assert _get_release_blocker_count(release_id) == 0
        _assert_count_consistent(release_id)

    def test_create_blocking_passed_does_not_increment(self, release):
        release_id = release["id"]

        client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "安全扫描", "category": "security", "is_blocking": True, "status": "passed"},
        )

        assert _get_release_blocker_count(release_id) == 0
        _assert_count_consistent(release_id)

    def test_create_multiple_blockers_accumulates(self, release):
        release_id = release["id"]

        client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "项1", "category": "code", "is_blocking": True, "status": "pending"},
        )
        client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "项2", "category": "test", "is_blocking": True, "status": "failed"},
        )
        client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "项3", "category": "build", "is_blocking": True, "status": "pending"},
        )

        assert _get_release_blocker_count(release_id) == 3
        _assert_count_consistent(release_id)


class TestBlockerCountDecrement:
    def test_resolve_from_pending_to_passed_decrements(self, release):
        release_id = release["id"]

        resp = client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "代码审查", "category": "code", "is_blocking": True, "status": "pending"},
        )
        item_id = resp.json()["id"]
        assert _get_release_blocker_count(release_id) == 1

        client.put(
            f"/api/releases/{release_id}/check-items/{item_id}",
            json={"status": "passed"},
        )

        assert _get_release_blocker_count(release_id) == 0
        _assert_count_consistent(release_id)

    def test_resolve_from_failed_to_passed_decrements(self, release):
        release_id = release["id"]

        resp = client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "单元测试", "category": "test", "is_blocking": True, "status": "failed"},
        )
        item_id = resp.json()["id"]
        assert _get_release_blocker_count(release_id) == 1

        client.put(
            f"/api/releases/{release_id}/check-items/{item_id}",
            json={"status": "passed"},
        )

        assert _get_release_blocker_count(release_id) == 0
        _assert_count_consistent(release_id)

    def test_resolve_from_pending_to_skipped_decrements(self, release):
        release_id = release["id"]

        resp = client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "构建检查", "category": "build", "is_blocking": True, "status": "pending"},
        )
        item_id = resp.json()["id"]
        assert _get_release_blocker_count(release_id) == 1

        client.put(
            f"/api/releases/{release_id}/check-items/{item_id}",
            json={"status": "skipped"},
        )

        assert _get_release_blocker_count(release_id) == 0
        _assert_count_consistent(release_id)

    def test_delete_blocking_item_decrements(self, release):
        release_id = release["id"]

        resp = client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "安全扫描", "category": "security", "is_blocking": True, "status": "pending"},
        )
        item_id = resp.json()["id"]
        assert _get_release_blocker_count(release_id) == 1

        client.delete(f"/api/releases/{release_id}/check-items/{item_id}")

        assert _get_release_blocker_count(release_id) == 0
        _assert_count_consistent(release_id)

    def test_partial_resolve_with_mixed_items(self, release):
        release_id = release["id"]

        r1 = client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "阻塞1", "category": "code", "is_blocking": True, "status": "pending"},
        )
        client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "阻塞2", "category": "test", "is_blocking": True, "status": "failed"},
        )
        client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "非阻塞", "category": "documentation", "is_blocking": False, "status": "pending"},
        )
        assert _get_release_blocker_count(release_id) == 2

        client.put(
            f"/api/releases/{release_id}/check-items/{r1.json()['id']}",
            json={"status": "passed"},
        )

        assert _get_release_blocker_count(release_id) == 1
        _assert_count_consistent(release_id)


class TestRecountBlockers:
    def test_recount_fixes_inflated_count(self, release):
        release_id = release["id"]

        client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "阻塞项", "category": "code", "is_blocking": True, "status": "pending"},
        )
        assert _get_release_blocker_count(release_id) == 1

        db = TestingSessionLocal()
        try:
            db_release = db.query(models.Release).filter(models.Release.id == release_id).first()
            db_release.blocker_count = 5
            db.commit()
        finally:
            db.close()

        assert _get_release_blocker_count(release_id) == 5
        assert _get_actual_blocker_count(release_id) == 1

        response = client.get(f"/api/releases/{release_id}/recount-blockers")
        assert response.status_code == 200

        assert _get_release_blocker_count(release_id) == 1
        _assert_count_consistent(release_id)

    def test_recount_fixes_deflated_count(self, release):
        release_id = release["id"]

        client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "阻塞1", "category": "code", "is_blocking": True, "status": "pending"},
        )
        client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "阻塞2", "category": "test", "is_blocking": True, "status": "failed"},
        )
        assert _get_release_blocker_count(release_id) == 2

        db = TestingSessionLocal()
        try:
            db_release = db.query(models.Release).filter(models.Release.id == release_id).first()
            db_release.blocker_count = 0
            db.commit()
        finally:
            db.close()

        assert _get_release_blocker_count(release_id) == 0
        assert _get_actual_blocker_count(release_id) == 2

        response = client.get(f"/api/releases/{release_id}/recount-blockers")
        assert response.status_code == 200

        assert _get_release_blocker_count(release_id) == 2
        _assert_count_consistent(release_id)

    def test_recount_on_clean_state_is_noop(self, release):
        release_id = release["id"]

        client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "阻塞项", "category": "code", "is_blocking": True, "status": "pending"},
        )
        assert _get_release_blocker_count(release_id) == 1

        response = client.get(f"/api/releases/{release_id}/recount-blockers")
        assert response.status_code == 200
        assert response.json()["blocker_count"] == 1

        _assert_count_consistent(release_id)

    def test_recount_nonexistent_release_returns_404(self):
        response = client.get("/api/releases/9999/recount-blockers")
        assert response.status_code == 404

    def test_recount_after_manual_db_status_change(self, release):
        release_id = release["id"]

        r1 = client.post(
            f"/api/releases/{release_id}/check-items/",
            json={"title": "阻塞项", "category": "code", "is_blocking": True, "status": "pending"},
        )
        item_id = r1.json()["id"]
        assert _get_release_blocker_count(release_id) == 1

        db = TestingSessionLocal()
        try:
            item = db.query(models.CheckItem).filter(models.CheckItem.id == item_id).first()
            item.status = models.CheckItemStatus.PASSED
            db.commit()
        finally:
            db.close()

        assert _get_release_blocker_count(release_id) == 1
        assert _get_actual_blocker_count(release_id) == 0

        response = client.get(f"/api/releases/{release_id}/recount-blockers")
        assert response.status_code == 200
        assert response.json()["blocker_count"] == 0

        _assert_count_consistent(release_id)
