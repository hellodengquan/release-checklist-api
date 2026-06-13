import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app import models

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def create_test_release(version="v1.0.0", name="测试发布"):
    response = client.post(
        "/api/releases/",
        json={"version": version, "name": name, "description": "测试用发布"},
    )
    return response.json()


def create_check_item(release_id, title, category="code", is_blocking=False, status="pending"):
    response = client.post(
        f"/api/releases/{release_id}/check-items/",
        json={
            "title": title,
            "category": category,
            "is_blocking": is_blocking,
            "status": status,
        },
    )
    return response.json()


class TestReleaseBlockers:
    def test_mixed_status_check_items_returns_correct_blockers(self):
        release = create_test_release()
        release_id = release["id"]

        create_check_item(release_id, "阻塞项1-待处理", is_blocking=True, status="pending")
        create_check_item(release_id, "阻塞项2-失败", is_blocking=True, status="failed")
        create_check_item(release_id, "阻塞项3-已通过", is_blocking=True, status="passed")
        create_check_item(release_id, "非阻塞项-待处理", is_blocking=False, status="pending")
        create_check_item(release_id, "非阻塞项-失败", is_blocking=False, status="failed")
        create_check_item(release_id, "阻塞项4-已跳过", is_blocking=True, status="skipped")

        response = client.get(f"/api/releases/{release_id}/blockers")
        assert response.status_code == 200
        data = response.json()

        assert data["release_id"] == release_id
        assert data["total_blocker_count"] == 2

        blocker_titles = [item["title"] for item in data["blocking_check_items"]]
        assert "阻塞项1-待处理" in blocker_titles
        assert "阻塞项2-失败" in blocker_titles
        assert "阻塞项3-已通过" not in blocker_titles
        assert "阻塞项4-已跳过" not in blocker_titles
        assert "非阻塞项-待处理" not in blocker_titles
        assert "非阻塞项-失败" not in blocker_titles

    def test_empty_blockers_returns_empty_array(self):
        release = create_test_release(version="v2.0.0", name="无阻塞发布")
        release_id = release["id"]

        create_check_item(release_id, "已通过-非阻塞", is_blocking=False, status="passed")
        create_check_item(release_id, "已通过-阻塞", is_blocking=True, status="passed")
        create_check_item(release_id, "已跳过-阻塞", is_blocking=True, status="skipped")

        response = client.get(f"/api/releases/{release_id}/blockers")
        assert response.status_code == 200
        data = response.json()

        assert data["total_blocker_count"] == 0
        assert data["blocking_check_items"] == []

    def test_nonexistent_release_returns_404(self):
        response = client.get("/api/releases/999/blockers")
        assert response.status_code == 404
        assert response.json()["detail"] == "Release not found"

    def test_release_has_total_blocker_count_field(self):
        release = create_test_release(version="v3.0.0", name="计数测试")
        release_id = release["id"]

        create_check_item(release_id, "阻塞项A", is_blocking=True, status="pending")
        create_check_item(release_id, "阻塞项B", is_blocking=True, status="failed")

        response = client.get(f"/api/releases/{release_id}")
        assert response.status_code == 200
        data = response.json()
        assert "total_blocker_count" in data
        assert data["total_blocker_count"] == 2

        list_response = client.get("/api/releases/")
        assert list_response.status_code == 200
        list_data = list_response.json()
        assert len(list_data) > 0
        assert "total_blocker_count" in list_data[0]

    def test_blockers_include_pending_approvals(self):
        release = create_test_release(version="v4.0.0", name="审批测试")
        release_id = release["id"]

        client.post(
            f"/api/releases/{release_id}/approvals/",
            json={"approver_role": "技术负责人", "approver_name": "张三"},
        )
        client.post(
            f"/api/releases/{release_id}/approvals/",
            json={"approver_role": "产品负责人", "approver_name": "李四", "status": "approved"},
        )

        response = client.get(f"/api/releases/{release_id}/blockers")
        assert response.status_code == 200
        data = response.json()

        assert len(data["pending_approvals"]) == 1
        assert data["pending_approvals"][0]["approver_role"] == "技术负责人"

    def test_blockers_has_last_status_change(self):
        release = create_test_release(version="v5.0.0", name="状态时间测试")
        release_id = release["id"]

        create_check_item(release_id, "测试检查项", is_blocking=True, status="pending")

        response = client.get(f"/api/releases/{release_id}/blockers")
        assert response.status_code == 200
        data = response.json()
        assert data["last_status_change"] is not None
