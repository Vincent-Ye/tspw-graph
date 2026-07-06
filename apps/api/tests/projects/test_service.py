from io import BytesIO

import pytest
from sqlalchemy import create_engine

from app.projects.files import UploadStore
from app.projects.repository import ProjectRepository
from app.projects.service import BuiltinProjectError, ProjectService, ProjectUploadService


class FakeGraphWriter:
    def __init__(self) -> None:
        self.deleted: list[str] = []

    def delete_project(self, project_id: str) -> None:
        self.deleted.append(project_id)


def test_upload_service_creates_project(tmp_path):
    repository = ProjectRepository(create_engine("sqlite+pysqlite:///:memory:"))
    service = ProjectUploadService(repository, UploadStore(tmp_path))

    project = service.create(
        title="测试小说",
        filename="book.txt",
        stream=BytesIO("第一章\n令狐冲出现。".encode()),
    )

    assert project.title == "测试小说"
    assert project.source_path is not None and project.source_path.endswith("source.txt")


def test_delete_user_project_cleans_all_stores(tmp_path):
    repository = ProjectRepository(create_engine("sqlite+pysqlite:///:memory:"))
    uploads = UploadStore(tmp_path)
    project = ProjectUploadService(repository, uploads).create(
        title="测试小说", filename="book.txt", stream=BytesIO(b"text")
    )
    graph = FakeGraphWriter()

    ProjectService(repository, uploads, graph).delete(project.id)

    assert repository.get(project.id) is None
    assert not uploads.project_dir(project.id).exists()
    assert graph.deleted == [project.id]


def test_delete_builtin_project_is_forbidden(tmp_path):
    repository = ProjectRepository(create_engine("sqlite+pysqlite:///:memory:"))
    repository.ensure_builtin_project("xiaoao", "笑傲江湖")
    service = ProjectService(repository, UploadStore(tmp_path), FakeGraphWriter())

    with pytest.raises(BuiltinProjectError):
        service.delete("xiaoao")
