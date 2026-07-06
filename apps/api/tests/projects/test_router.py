from io import BytesIO

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from app.projects.files import UploadStore
from app.projects.repository import ProjectRepository
from app.projects.router import get_project_service, router
from app.projects.service import ProjectService, ProjectUploadService


class FakeGraphWriter:
    def delete_project(self, project_id: str) -> None:
        return None


def make_client(tmp_path) -> tuple[TestClient, ProjectRepository]:
    repository = ProjectRepository(
        create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    )
    uploads = UploadStore(tmp_path)
    repository.ensure_builtin_project("xiaoao", "笑傲江湖")
    ProjectUploadService(repository, uploads).create(
        title="测试小说", filename="book.txt", stream=BytesIO(b"text")
    )
    service = ProjectService(repository, uploads, FakeGraphWriter())
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_project_service] = lambda: service
    return TestClient(app), repository


def test_list_and_get_projects(tmp_path):
    client, repository = make_client(tmp_path)
    response = client.get("/api/projects")
    assert response.status_code == 200
    assert {item["title"] for item in response.json()} == {"笑傲江湖", "测试小说"}
    user_project = next(item for item in repository.list_projects() if not item.is_builtin)
    assert client.get(f"/api/projects/{user_project.id}").json()["title"] == "测试小说"


def test_delete_is_idempotent_and_builtin_is_forbidden(tmp_path):
    client, repository = make_client(tmp_path)
    user_project = next(item for item in repository.list_projects() if not item.is_builtin)
    assert client.delete(f"/api/projects/{user_project.id}").status_code == 204
    assert client.delete(f"/api/projects/{user_project.id}").status_code == 204
    response = client.delete("/api/projects/xiaoao")
    assert response.status_code == 403
    assert response.json()["detail"]["code"] == "BUILTIN_PROJECT_READ_ONLY"
